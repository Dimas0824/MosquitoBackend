import secrets
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.models.device import DeviceAuth, Device
from app.database import get_db
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()
docs_security = HTTPBasic()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def authenticate_device(device_code: str, password: str, db: Session) -> Device:
    """
    Authenticate device using device_code and password
    Returns Device object if authentication successful
    Raises HTTPException if authentication failed
    """
    device_auth = db.query(DeviceAuth).filter(
        DeviceAuth.device_code == device_code
    ).first()
    
    if not device_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not verify_password(password, device_auth.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    device = db.query(Device).filter(Device.id == device_auth.device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not device.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is not active"
        )
    
    return device


def get_current_device(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Device:
    """
    Dependency untuk mendapatkan device yang terautentikasi
    Menggunakan HTTP Basic Auth
    """
    return authenticate_device(credentials.username, credentials.password, db)


def verify_docs_credentials(credentials: HTTPBasicCredentials = Depends(docs_security)):
    """
    Dependency untuk autentikasi akses dokumentasi API
    Menggunakan HTTP Basic Auth dengan bcrypt hash password
    """
    # Verify username
    correct_username = secrets.compare_digest(credentials.username, settings.DOCS_USERNAME)
    
    # Verify password using bcrypt hash
    correct_password = False
    if correct_username:  # Only verify password if username is correct
        try:
            correct_password = pwd_context.verify(credentials.password, settings.DOCS_PASSWORD_HASH)
        except Exception:
            correct_password = False
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid documentation credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
