"""
Script simulasi untuk testing upload image
Mensimulasikan ESP32 upload image ke backend
"""
import httpx
import asyncio
from pathlib import Path
import sys


async def upload_image(
    image_path: str,
    device_code: str,
    password: str,
    api_url: str = "http://localhost:8000/api/upload"
):
    """
    Simulasi ESP32 upload image
    
    Args:
        image_path: Path ke image file
        device_code: Device code untuk auth
        password: Password device
        api_url: URL endpoint
    """
    if not Path(image_path).exists():
        print(f"✗ File tidak ditemukan: {image_path}")
        return
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Basic auth
            auth = (device_code, password)
            
            # Prepare file
            with open(image_path, 'rb') as f:
                files = {'image': f}
                
                # Upload
                print(f"📤 Uploading {image_path}...")
                response = await client.post(
                    api_url,
                    files=files,
                    auth=auth
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Upload berhasil!")
                print(f"  Action: {result['action']}")
                print(f"  Status: {result['status']}")
                print(f"  Device: {result['device_code']}")
                print(f"  Message: {result['message']}")
            else:
                print(f"✗ Upload gagal!")
                print(f"  Status Code: {response.status_code}")
                print(f"  Response: {response.text}")
                
    except Exception as e:
        print(f"✗ Error: {str(e)}")


async def simulate_multiple_devices(
    image_path: str,
    devices: list,
    api_url: str = "http://localhost:8000/api/upload"
):
    """
    Simulasi multiple devices upload bersamaan
    
    Args:
        image_path: Path ke image file
        devices: List of tuples (device_code, password)
        api_url: URL endpoint
    """
    tasks = []
    for device_code, password in devices:
        task = upload_image(image_path, device_code, password, api_url)
        tasks.append(task)
    
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    print("=" * 60)
    print("SIMULASI ESP32 UPLOAD")
    print("=" * 60)
    
    if len(sys.argv) >= 4:
        # CLI mode
        image_path = sys.argv[1]
        device_code = sys.argv[2]
        password = sys.argv[3]
        
        asyncio.run(upload_image(image_path, device_code, password))
    else:
        print("Usage: python test_upload.py <image_path> <device_code> <password>")
        print()
        print("Example:")
        print("  python test_upload.py sample.jpg ESP32_TOREN_01 password123")
        print()
        print("Multiple devices test:")
        print("  Edit script dan uncomment simulate_multiple_devices")
