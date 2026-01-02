from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import update
from app.models.alert import Alert
from app.config import get_current_time


class DecisionEngine:
    """
    Decision engine untuk menentukan status dan action
    Sesuai flow di rancangan.md
    """
    
    @staticmethod
    def determine_status(total_jentik: int) -> str:
        """
        Tentukan status berdasarkan jumlah jentik
        Returns: "AMAN" atau "BAHAYA"
        """
        if total_jentik > 0:
            return "BAHAYA"
        return "AMAN"
    
    @staticmethod
    def determine_action(status: str) -> str:
        """
        Tentukan action untuk ESP32 berdasarkan status
        Returns: "ACTIVATE" atau "SLEEP"
        """
        if status == "BAHAYA":
            return "ACTIVATE"
        return "SLEEP"
    
    @staticmethod
    def should_create_alert(
        device_code: str,
        total_jentik: int,
        db: Session
    ) -> bool:
        """
        Tentukan apakah perlu membuat alert baru
        Alert hanya dibuat jika:
        - total_jentik > 0
        - DAN belum ada alert yang belum resolved untuk device ini
        """
        if total_jentik == 0:
            return False
        
        # Cek apakah ada alert yang belum resolved
        unresolved_alert = db.query(Alert).filter(
            Alert.device_code == device_code,
            Alert.resolved_at.is_(None)
        ).first()
        
        # Jika sudah ada alert yang belum resolved, jangan buat baru
        if unresolved_alert:
            return False
        
        return True
    
    @staticmethod
    def resolve_alerts_if_safe(
        device_code: str,
        total_jentik: int,
        db: Session
    ):
        """
        Resolve semua alert yang belum resolved jika kondisi sudah aman
        """
        if total_jentik == 0:
            # Update semua alert yang belum resolved
            db.query(Alert).filter(
                Alert.device_code == device_code,
                Alert.resolved_at.is_(None)
            ).update({
                "resolved_at": get_current_time()
            })
            db.commit()
    
    @staticmethod
    def create_alert(
        device_id: str,
        device_code: str,
        total_jentik: int,
        db: Session
    ) -> Alert:
        """
        Buat alert baru
        """
        alert = Alert(
            device_id=device_id,
            device_code=device_code,
            alert_type="LARVA_DETECTED",
            alert_message=f"Terdeteksi {total_jentik} jentik nyamuk",
            alert_level="critical"
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert


decision_engine = DecisionEngine()
