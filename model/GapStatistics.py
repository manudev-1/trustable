from dataclasses import dataclass, asdict
from typing import Dict

@dataclass
class GapStatistics:
    """Statistiche sui gap temporali tra recensioni"""
    avg_gap_days: float
    median_gap_days: float
    std_gap_days: float
    min_gap: float
    max_gap: float
    
    def to_dict(self) -> Dict:
        return asdict(self)