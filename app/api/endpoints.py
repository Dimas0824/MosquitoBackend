import os
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.auth import get_current_device
from app.models.device import Device
from app.models.image import Image
from app.models.inference import InferenceResult
from app.schemas.schemas import UploadResponse, DeviceResponse
from app.services.roboflow_service import roboflow_service
from app.services.blynk_service import blynk_service
from app.services.decision_engine import decision_engine
from app.utils.image_utils import (
    save_image, 
    preprocess_image, 
    generate_image_filename
)
from app.config import settings, get_current_time

router = APIRouter()


async def process_inference_background(
    original_image_id: str,
    preprocessed_image_path: str,
    device_id: str,
    device_code: str,
    db: Session
):
    """
    Background task untuk processing inference
    Sesuai flow di rancangan.md - async processing
    """
    try:
        # Inference dengan Roboflow
        raw_prediction = await roboflow_service.infer(preprocessed_image_path)
        
        # Parse hasil prediksi
        parsed_result = roboflow_service.parse_prediction(raw_prediction)
        
        # Simpan inference result
        inference_result = InferenceResult(
            image_id=original_image_id,
            device_id=device_id,
            device_code=device_code,
            raw_prediction=raw_prediction,
            total_objects=parsed_result['total_objects'],
            total_jentik=parsed_result['total_jentik'],
            total_non_jentik=parsed_result['total_non_jentik'],
            avg_confidence=parsed_result['avg_confidence'],
            parsing_version="1.0",
            status="success"
        )
        db.add(inference_result)
        db.commit()
        
        # Decision Engine
        status = decision_engine.determine_status(parsed_result['total_jentik'])
        action = decision_engine.determine_action(status)
        
        # Handle alerts
        if decision_engine.should_create_alert(
            device_code, 
            parsed_result['total_jentik'], 
            db
        ):
            decision_engine.create_alert(
                device_id,
                device_code,
                parsed_result['total_jentik'],
                db
            )
        
        # Resolve alerts jika aman
        decision_engine.resolve_alerts_if_safe(
            device_code,
            parsed_result['total_jentik'],
            db
        )
        
        # Update Blynk
        await blynk_service.update_all(
            device_code,
            status,
            parsed_result['total_jentik']
        )
        
        print(f"✓ Inference completed for {device_code}: {status} ({parsed_result['total_jentik']} jentik)")
        
    except Exception as e:
        # Simpan error ke database
        inference_result = InferenceResult(
            image_id=original_image_id,
            device_id=device_id,
            device_code=device_code,
            status="failed",
            error_message=str(e)
        )
        db.add(inference_result)
        db.commit()
        
        # Update Blynk dengan status error
        await blynk_service.update_status(device_code, "INFERENCE ERROR")
        
        print(f"✗ Inference failed for {device_code}: {str(e)}")


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    captured_at: Optional[str] = Form(None),
    current_device: Device = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    """
    Upload image endpoint
    Flow sesuai rancangan.md:
    1. Auth device
    2. Save original image
    3. Preprocess image
    4. Response cepat ke ESP32
    5. Inference dijalankan di background
    """
    try:
        # Parse captured_at
        captured_datetime = None
        if captured_at:
            try:
                captured_datetime = datetime.fromisoformat(captured_at.replace('Z', '+00:00'))
            except:
                captured_datetime = get_current_time()
        else:
            captured_datetime = get_current_time()
        
        # Read image data
        image_data = await image.read()
        
        # Generate filenames
        original_filename = generate_image_filename(current_device.device_code, "original")
        preprocessed_filename = generate_image_filename(current_device.device_code, "preprocessed")
        
        # Paths
        original_path = os.path.join(settings.IMAGE_ORIGINAL_PATH, original_filename)
        preprocessed_path = os.path.join(settings.IMAGE_PREPROCESSED_PATH, preprocessed_filename)
        
        # Save original image
        width, height, checksum = save_image(image_data, original_path)
        
        # Insert original image to database
        original_image = Image(
            device_id=current_device.id,
            device_code=current_device.device_code,
            image_type="original",
            image_path=original_path,
            width=width,
            height=height,
            checksum=checksum,
            captured_at=captured_datetime
        )
        db.add(original_image)
        db.commit()
        db.refresh(original_image)
        
        # Preprocess image
        prep_width, prep_height, prep_checksum = preprocess_image(
            original_path, 
            preprocessed_path
        )
        
        # Insert preprocessed image to database
        preprocessed_image = Image(
            device_id=current_device.id,
            device_code=current_device.device_code,
            image_type="preprocessed",
            image_path=preprocessed_path,
            width=prep_width,
            height=prep_height,
            checksum=prep_checksum,
            captured_at=captured_datetime
        )
        db.add(preprocessed_image)
        db.commit()
        
        # Add background task untuk inference
        background_tasks.add_task(
            process_inference_background,
            original_image.id,
            preprocessed_path,
            current_device.id,
            current_device.device_code,
            db
        )
        
        # Response cepat - default SLEEP
        # ESP32 akan sleep, nanti action berikutnya disesuaikan berdasarkan hasil inference
        return UploadResponse(
            success=True,
            message="Image uploaded successfully, processing in background",
            action="SLEEP",
            status="PROCESSING",
            device_code=current_device.device_code,
            total_jentik=0,
            total_objects=0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/device/info", response_model=DeviceResponse)
async def get_device_info(
    current_device: Device = Depends(get_current_device)
):
    """Get device information"""
    return current_device


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": get_current_time().isoformat()
    }
