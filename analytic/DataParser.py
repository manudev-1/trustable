from datetime import datetime
from typing import Optional

class DateParser:
    """Gestione del parsing delle date"""
    
    @staticmethod
    def parse(date_str: Optional[str]) -> Optional[datetime]:
        """Converte una stringa data in datetime object"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None
    
    @staticmethod
    def get_month_key(date: datetime) -> str:
        """Restituisce la chiave nel formato YYYY-MM"""
        return date.strftime("%Y-%m")