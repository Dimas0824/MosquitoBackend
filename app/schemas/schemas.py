from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UploadRequest(BaseModel):
    """Request schema untuk upload image"""
    captured_at: Optional[datetime] = Field(default=None, description="Waktu capture image")


class UploadResponse(BaseModel):
    """Response schema untuk upload endpoint"""
    success: bool
    message: str
    action: str  # ACTIVATE | SLEEP
    status: str  # AMAN | BAHAYA
    device_code: str
    total_jentik: int
    total_objects: int
    
    class Config:
        from_attributes = True


class DeviceResponse(BaseModel):
    """Response schema untuk device info"""
    id: str
    device_code: str
    location: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
