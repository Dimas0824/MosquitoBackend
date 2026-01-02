import uuid
from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.config import get_current_time


def generate_uuid():
    return str(uuid.uuid4())


class InferenceResult(Base):
    __tablename__ = "inference_results"
    
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=generate_uuid)
    image_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("images.id"), nullable=False)
    device_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("devices.id"), nullable=False)
    device_code: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    inference_at: Mapped[datetime] = mapped_column(DateTime, default=get_current_time)
    raw_prediction: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    total_objects: Mapped[int] = mapped_column(Integer, default=0)
    total_jentik: Mapped[int] = mapped_column(Integer, default=0)
    total_non_jentik: Mapped[int] = mapped_column(Integer, default=0)
    avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    parsing_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # success | failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="inference_results")
    image = relationship("Image", back_populates="inference_result")
