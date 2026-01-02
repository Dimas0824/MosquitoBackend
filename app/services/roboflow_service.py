import httpx
from typing import Dict, Any, Optional
from app.config import settings

# Try to import inference_sdk, fallback to httpx
try:
    from inference_sdk import InferenceHTTPClient
    HAS_INFERENCE_SDK = True
except ImportError:
    HAS_INFERENCE_SDK = False


class RoboflowService:
    """Service untuk komunikasi dengan Roboflow API"""
    
    def __init__(self):
        self.api_key = settings.ROBOFLOW_API_KEY
        self.workspace = settings.ROBOFLOW_WORKSPACE
        self.workflow_id = settings.ROBOFLOW_WORKFLOW_ID
        # Legacy support
        self.model_id = settings.ROBOFLOW_MODEL_ID
        self.version = settings.ROBOFLOW_VERSION or 1
        
        # Debug logging
        print(f"🔧 Roboflow Service Init:")
        print(f"   API Key: {'✓' if self.api_key else '✗'}")
        print(f"   Workspace: {self.workspace or '✗'}")
        print(f"   Workflow ID: {self.workflow_id or '✗'}")
        print(f"   Model ID: {self.model_id or '✗'}")
        print(f"   inference_sdk installed: {'✓' if HAS_INFERENCE_SDK else '✗'}")
        
        # Initialize client for workflows
        if self.workspace and self.workflow_id:
            if HAS_INFERENCE_SDK:
                self.client = InferenceHTTPClient(
                    api_url="https://serverless.roboflow.com",
                    api_key=self.api_key
                )
                print(f"   Mode: Workflow (inference_sdk) ✓")
            else:
                self.client = None
                print(f"   Mode: Workflow (httpx) ✓")
            self.api_type = "workflow"
            self.base_url = "https://serverless.roboflow.com"
        elif self.model_id:
            self.client = None
            self.api_type = "detection"
            self.base_url = "https://detect.roboflow.com"
            print(f"   Mode: Detection ✓")
        else:
            self.client = None
            self.api_type = None
            print(f"   Mode: ✗ NOT CONFIGURED")
            print(f"   ⚠️  Need either (workspace + workflow_id) OR model_id")
    
    async def infer(self, image_path: str) -> Any:
        """
        Kirim image ke Roboflow untuk inference
        Returns: Raw prediction result dari Roboflow (bisa list atau dict)
        """
        if not self.api_key:
            raise Exception("Roboflow API key not configured")
        
        print(f"📸 Starting inference for: {image_path}")
        print(f"   API Type: {self.api_type}")
        
        if self.api_type == "workflow":
            return await self._infer_workflow(image_path)
        elif self.api_type == "detection":
            return await self._infer_detection(image_path)
        else:
            error_msg = (
                "Roboflow not properly configured. "
                f"API Key: {'✓' if self.api_key else '✗'}, "
                f"Workspace: {self.workspace or '✗'}, "
                f"Workflow ID: {self.workflow_id or '✗'}, "
                f"Model ID: {self.model_id or '✗'}, "
                f"inference_sdk: {'✓' if HAS_INFERENCE_SDK else '✗ (run: pip install inference-sdk)'}"
            )
            raise Exception(error_msg)
    
    async def _infer_workflow(self, image_path: str) -> Any:
        """Inference menggunakan Roboflow Workflows (returns list atau dict)"""
        if not self.workspace or not self.workflow_id:
            raise Exception("Roboflow workspace or workflow_id not configured")
        
        # Try with inference_sdk first if available
        if HAS_INFERENCE_SDK and self.client:
            return await self._infer_workflow_sdk(image_path)
        else:
            return await self._infer_workflow_httpx(image_path)
    
    async def _infer_workflow_sdk(self, image_path: str) -> Any:
        """Inference using inference_sdk (returns list atau dict)"""
        if not self.client:
            raise Exception("Workflow client not initialized")
        
        try:
            print(f"   🔄 Running workflow (SDK): {self.workspace}/{self.workflow_id}")
            import asyncio
            result = await asyncio.to_thread(
                self.client.run_workflow,
                workspace_name=self.workspace,
                workflow_id=self.workflow_id,
                images={"image": image_path},
                use_cache=False
            )
            print(f"   ✓ Workflow completed successfully")
            
            # Return full result (list atau dict) tanpa parsing
            # Biar raw_prediction tersimpan lengkap di database
            return result
                
        except Exception as e:
            print(f"   ✗ Workflow error: {str(e)}")
            raise Exception(f"Roboflow Workflow error: {str(e)}")
    
    async def _infer_workflow_httpx(self, image_path: str) -> Any:
        """Inference using httpx directly (returns list atau dict)"""
        url = f"{self.base_url}/{self.workspace}/{self.workflow_id}"
        
        try:
            print(f"   🔄 Running workflow (httpx): {self.workspace}/{self.workflow_id}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(image_path, 'rb') as image_file:
                    files = {
                        'image': ('image.jpg', image_file, 'image/jpeg')
                    }
                    params = {
                        'api_key': self.api_key
                    }
                    response = await client.post(url, files=files, params=params)
                    response.raise_for_status()
                    result = response.json()
                    
            print(f"   ✓ Workflow completed successfully")
            return result
            
        except httpx.HTTPError as e:
            print(f"   ✗ Workflow HTTP error: {str(e)}")
            raise Exception(f"Roboflow Workflow API error: {str(e)}")
        except Exception as e:
            print(f"   ✗ Workflow error: {str(e)}")
            raise Exception(f"Workflow inference error: {str(e)}")
    
    async def _infer_detection(self, image_path: str) -> Dict[str, Any]:
        """Inference menggunakan Roboflow Detection API (legacy)"""
        if not self.model_id:
            raise Exception("Roboflow model ID not configured")
        
        url = f"{self.base_url}/{self.model_id}/{self.version}"
        
        params = {
            "api_key": self.api_key,
            "confidence": 40,
            "overlap": 30
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(image_path, 'rb') as image_file:
                    files = {'file': image_file}
                    response = await client.post(url, params=params, files=files)
                    response.raise_for_status()
                    return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Roboflow API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Inference error: {str(e)}")
    
    def parse_prediction(self, raw_prediction: Any) -> Dict[str, Any]:
        """
        Parse hasil prediksi dari Roboflow Workflow
        Raw prediction structure: [{"dynamic_crop": [...], "detection_predictions": {...}}]
        Returns: {
            'total_objects': int,
            'total_jentik': int,
            'total_non_jentik': int,
            'avg_confidence': float
        }
        """
        try:
            # Workflow API returns: result[0]["detection_predictions"]["predictions"]
            predictions = []
            if isinstance(raw_prediction, list) and len(raw_prediction) > 0:
                # Extract detection_predictions dari workflow result
                first_result = raw_prediction[0]
                if isinstance(first_result, dict):
                    detection_data = first_result.get("detection_predictions", {})
                    predictions = detection_data.get("predictions", [])
                
                print(f"   📊 Parsing workflow result: {len(predictions)} predictions found")
            elif isinstance(raw_prediction, dict):
                # Fallback untuk detection API (legacy)
                predictions = raw_prediction.get('predictions', [])
                print(f"   📊 Parsing detection API result: {len(predictions)} predictions found")
            
            # Hitung jumlah jentik dan non-jentik berdasarkan class
            jumlah_jentik = 0
            jumlah_non_jentik = 0
            confidences = []
            
            for pred in predictions:
                class_name = pred.get('class', '').lower()
                confidence = pred.get('confidence', 0)
                confidences.append(confidence)
                
                # Check class: jentik atau non-jentik
                if 'jentik' in class_name or 'larva' in class_name or 'larvae' in class_name:
                    jumlah_jentik += 1
                else:
                    jumlah_non_jentik += 1
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            result = {
                'total_objects': len(predictions),
                'total_jentik': jumlah_jentik,
                'total_non_jentik': jumlah_non_jentik,
                'avg_confidence': round(avg_confidence, 4)
            }
            
            print(f"   ✓ Parsed: {jumlah_jentik} jentik, {jumlah_non_jentik} non-jentik")
            return result
            
        except Exception as e:
            print(f"   ✗ Parse error: {str(e)}")
            return {
                'total_objects': 0,
                'total_jentik': 0,
                'total_non_jentik': 0,
                'avg_confidence': 0.0
            }


roboflow_service = RoboflowService()
