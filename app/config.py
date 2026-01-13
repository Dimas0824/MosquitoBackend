from pydantic_settings import BaseSettings
from typing import Optional
from datetime import datetime, timezone, timedelta
import zoneinfo


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/mosquito_db"
    
    # Roboflow
    ROBOFLOW_API_KEY: str = ""
    ROBOFLOW_WORKSPACE: Optional[str] = None
    ROBOFLOW_WORKFLOW_ID: Optional[str] = None
    # Legacy support for model-based detection
    ROBOFLOW_MODEL_ID: Optional[str] = None
    ROBOFLOW_VERSION: Optional[int] = None
    
    # Blynk
    BLYNK_AUTH_TOKEN: Optional[str] = None
    BLYNK_TEMPLATE_ID: Optional[str] = None
    BLYNK_DEVICE_NAME: str = "mosquito_detector"
    
    # Storage
    STORAGE_PATH: str = "./storage"
    IMAGE_ORIGINAL_PATH: str = "./storage/images/original"
    IMAGE_PREPROCESSED_PATH: str = "./storage/images/preprocessed"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Documentation Access (HTTP Basic Auth)
    # Username untuk akses dokumentasi
    DOCS_USERNAME: str = "admin"
    # Password hash (bcrypt) - default: "admin123"
    # Generate hash: from passlib.context import CryptContext; CryptContext(schemes=["bcrypt"]).hash("your_password")
    DOCS_PASSWORD_HASH: str = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5VO/9rJ3jrGf2"
    
    # Timezone (e.g., 'Asia/Jakarta' for WIB, 'UTC', 'America/New_York')
    TIMEZONE: str = "Asia/Jakarta"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def get_current_time() -> datetime:
    """
    Get current datetime with configured timezone (WIB/Asia Jakarta)
    Returns timezone-aware datetime object
    """
    try:
        tz = zoneinfo.ZoneInfo(settings.TIMEZONE)
    except Exception:
        # Fallback to WIB if timezone not found
        tz = zoneinfo.ZoneInfo('Asia/Jakarta')
    return datetime.now(tz)


def to_wib(dt: datetime) -> datetime:
    """
    Convert datetime to WIB timezone
    If datetime is naive (no timezone), assume it's WIB
    If datetime has timezone, convert it to WIB
    """
    wib_tz = zoneinfo.ZoneInfo(settings.TIMEZONE)
    
    if dt.tzinfo is None:
        # Naive datetime - assume it's already WIB
        return dt.replace(tzinfo=wib_tz)
    else:
        # Timezone-aware - convert to WIB
        return dt.astimezone(wib_tz)
