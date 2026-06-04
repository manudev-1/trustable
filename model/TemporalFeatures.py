from dataclasses import dataclass
from typing import Dict

@dataclass
class TemporalFeatures:
    """Feature temporali estratte per il calcolo dello score"""
    gini_index: float
    burst_ratio_value: float
    top_3_ratio: float
    spacing_entropy: float
    avg_gap_days: float
    std_gap_days: float
    
    def to_dict(self) -> Dict:
        return {
            "gini_index": round(self.gini_index, 4),
            "burst_ratio": round(self.burst_ratio_value, 4),
            "top_3_ratio": round(self.top_3_ratio, 4),
            "spacing_entropy": round(self.spacing_entropy, 4),
            "avg_gap_days": round(self.avg_gap_days, 2),
            "std_gap_days": round(self.std_gap_days, 2)
        }