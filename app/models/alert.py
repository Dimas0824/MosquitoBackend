import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.config import get_current_time


def generate_uuid():
    return str(uuid.uuid4())


class Alert(Base):
    __tablename__ = "alerts"
    
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=generate_uuid)
    device_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("devices.id"), nullable=False)
    device_code: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    alert_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    alert_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alert_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # info | warning | critical
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_current_time)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="alerts")
