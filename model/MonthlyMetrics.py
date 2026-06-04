from dataclasses import dataclass
from typing import Dict

@dataclass
class MonthlyMetrics:
    """Metriche di distribuzione mensile"""
    density_per_month: Dict[str, int]
    normalized_density: Dict[str, float]
    total_months: int
    active_months: int
    gini_index: float
    top_3_months_ratio: float
    max_reviews_in_month: int
    
    def to_dict(self) -> Dict:
        return {
            "densita_recensioni_per_mese": self.density_per_month,
            "densita_normalizzata_per_mese": self.normalized_density,
            "total_months": self.total_months,
            "active_months": self.active_months,
            "gini_index": round(self.gini_index, 4),
            "top_3_months_ratio": round(self.top_3_months_ratio, 4),
            "max_reviews_in_month": self.max_reviews_in_month
        }