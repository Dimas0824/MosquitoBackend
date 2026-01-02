import httpx
from typing import Dict, Any, Optional
from app.config import settings


class BlynkService:
    """Service untuk komunikasi dengan Blynk Cloud API"""
    
    def __init__(self):
        self.auth_token = settings.BLYNK_AUTH_TOKEN
        self.base_url = "https://blynk.cloud/external/api"
    
    async def update_status(self, device_code: str, status: str) -> bool:
        """
        Update status device ke Blynk
        status: "AMAN" atau "BAHAYA"
        Virtual Pin V0 untuk status
        """
        if not self.auth_token:
            print("⚠️  Blynk not configured, skipping update")
            return False
        
        url = f"{self.base_url}/update"
        
        params = {
            "token": self.auth_token,
            "V0": status
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Blynk update error: {str(e)}")
            return False
    
    async def update_larva_count(self, count: int) -> bool:
        """
        Update jumlah jentik ke Blynk
        Virtual Pin V1 untuk count
        """
        if not self.auth_token:
            return False
        
        url = f"{self.base_url}/update"
        
        params = {
            "token": self.auth_token,
            "V1": count
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Blynk update error: {str(e)}")
            return False
    
    async def send_notification(self, message: str) -> bool:
        """
        Kirim notifikasi ke Blynk app
        """
        if not self.auth_token:
            return False
        
        url = f"{self.base_url}/notify"
        
        params = {
            "token": self.auth_token,
            "body": message
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Blynk notification error: {str(e)}")
            return False
    
    async def update_all(self, device_code: str, status: str, larva_count: int) -> Dict[str, bool]:
        """
        Update semua data ke Blynk sekaligus
        """
        results = {
            "status_updated": await self.update_status(device_code, status),
            "count_updated": await self.update_larva_count(larva_count)
        }
        
        # Kirim notifikasi jika bahaya
        if status == "BAHAYA":
            results["notification_sent"] = await self.send_notification(
                f"⚠️ PERINGATAN: Jentik terdeteksi di {device_code}! Jumlah: {larva_count}"
            )
        
        return results


blynk_service = BlynkService()
