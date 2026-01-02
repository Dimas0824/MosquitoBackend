"""
Script untuk registrasi device baru
Sesuai flow di rancangan.md - dilakukan sekali oleh admin
"""
from sqlalchemy.orm import Session
from typing import Optional
from app.database import SessionLocal, init_db
from app.models.device import Device, DeviceAuth
from app.auth import hash_password
import sys


def register_device(
    device_code: str,
    password: str,
    location: Optional[str] = None,
    description: Optional[str] = None
):
    """
    Register device baru ke database
    
    Args:
        device_code: Kode device (misal: ESP32_TOREN_01)
        password: Password device
        location: Lokasi device (optional)
        description: Deskripsi device (optional)
    """
    db: Session = SessionLocal()
    
    try:
        # Cek apakah device_code sudah ada
        existing = db.query(Device).filter(Device.device_code == device_code).first()
        if existing:
            print(f"✗ Device {device_code} sudah terdaftar!")
            return False
        
        # Create device
        device = Device(
            device_code=device_code,
            location=location,
            description=description,
            is_active=True
        )
        db.add(device)
        db.flush()  # Flush untuk mendapatkan device.id
        
        # Create device auth
        device_auth = DeviceAuth(
            device_id=device.id,
            device_code=device_code,
            password_hash=hash_password(password)
        )
        db.add(device_auth)
        
        db.commit()
        
        print(f"✓ Device berhasil didaftarkan!")
        print(f"  Device Code: {device_code}")
        print(f"  Device ID: {device.id}")
        print(f"  Location: {location or '-'}")
        print(f"  Description: {description or '-'}")
        print(f"\n⚠️ Simpan credentials berikut untuk ESP32:")
        print(f"  Username: {device_code}")
        print(f"  Password: {password}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # Initialize database
    init_db()
    
    print("=" * 60)
    print("REGISTRASI DEVICE BARU")
    print("=" * 60)
    
    if len(sys.argv) >= 3:
        # CLI mode
        device_code = sys.argv[1]
        password = sys.argv[2]
        location = sys.argv[3] if len(sys.argv) > 3 else None
        description = sys.argv[4] if len(sys.argv) > 4 else None
    else:
        # Interactive mode
        device_code = input("Device Code (e.g., ESP32_TOREN_01): ").strip()
        password = input("Password: ").strip()
        location = input("Location (optional): ").strip() or None
        description = input("Description (optional): ").strip() or None
    
    print()
    register_device(device_code, password, location, description)
