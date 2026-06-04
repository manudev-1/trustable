from dataclasses import dataclass, asdict
from typing import Dict, Literal

@dataclass
class BurstAnalysis:
    """Risultati dell'analisi dei burst temporali"""
    burst_type: Literal['same_day', 'short', 'long', 'none']
    score: float
    same_day_gaps_ratio: float
    short_gaps_ratio: float
    total_short_gaps_ratio: float
    
    def to_dict(self) -> Dict:
        return asdict(self)