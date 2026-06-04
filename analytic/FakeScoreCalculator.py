from typing import List, Dict, Tuple
import math

from model.TemporalFeatures import TemporalFeatures
from model.BurstAnalysis import BurstAnalysis

class FakeScoreCalculator:
    """
    Calcola il punteggio di probabilità di recensioni fake
    basato esclusivamente su pattern temporali.
    """

    WEIGHTS = {
        'gini': 18,
        'burst_ratio': 18,
        'top_3': 12,
        'same_day_burst': 20,
        'short_burst': 12,
        'same_day_gaps': 20,
        'short_gaps': 8,
        'std_gap_anomaly': 10,
        'spacing': 12,
        'extra_std_bonus': 7,
        'avg_gap_bonus': 5
    }
    
    def __init__(self, features: TemporalFeatures, burst_analysis: BurstAnalysis, gaps: List[float]):
        self.features = features
        self.burst = burst_analysis
        self.gaps = gaps
    
    def _get_gap_ratios(self) -> Tuple[float, float]:
        """Calcola i ratio di gap corti e same-day"""
        if not self.gaps:
            return 0, 0
        
        gaps_floor = [math.floor(g) for g in self.gaps]
        same_day_ratio = sum(g == 0 for g in gaps_floor) / len(gaps_floor)
        short_ratio = sum(1 for g in gaps_floor if 1 <= g <= 2) / len(gaps_floor)
        return same_day_ratio, short_ratio
    
    def calculate(self) -> float:
        """
        Calcola il punteggio finale (0-100).
        Più alto = più probabile presenza di fake reviews.
        """
        if not self.gaps:
            return 0
        
        same_day_ratio, short_ratio = self._get_gap_ratios()
        score = 0.0
        
        score += self.features.gini_index * self.WEIGHTS['gini']
        score += self.features.burst_ratio_value * self.WEIGHTS['burst_ratio']
        score += self.features.top_3_ratio * self.WEIGHTS['top_3']
        
        if self.burst.burst_type == "same_day_burst":
            score += self.WEIGHTS['same_day_burst']
        elif self.burst.burst_type == "short_burst":
            score += self.WEIGHTS['short_burst']
        
        score += same_day_ratio * self.WEIGHTS['same_day_gaps']
        score += short_ratio * self.WEIGHTS['short_gaps']
        
        score += (1 - self.features.spacing_entropy) * self.WEIGHTS['spacing']
        
        if self.features.std_gap_days > self.features.avg_gap_days * 2:
            score += self.WEIGHTS['std_gap_anomaly']
        
        if 0 < self.features.avg_gap_days < 5:
            score += self.WEIGHTS['avg_gap_bonus']
        
        score += min((self.features.std_gap_days / 30) * self.WEIGHTS['extra_std_bonus'], 
                     self.WEIGHTS['extra_std_bonus'])
        
        return min(round(score, 2), 100)
    
    def get_score_breakdown(self) -> Dict[str, float]:
        """Restituisce il dettaglio del contributo di ogni metrica"""
        if not self.gaps:
            return {}
        
        same_day_ratio, short_ratio = self._get_gap_ratios()
        
        return {
            "gini_contributo": round(self.features.gini_index * self.WEIGHTS['gini'], 2),
            "burst_ratio_contributo": round(self.features.burst_ratio_value * self.WEIGHTS['burst_ratio'], 2),
            "top3_contributo": round(self.features.top_3_ratio * self.WEIGHTS['top_3'], 2),
            "burst_type_contributo": self.WEIGHTS['same_day_burst'] if self.burst.burst_type == "same_day_burst" 
                                     else (self.WEIGHTS['short_burst'] if self.burst.burst_type == "short_burst" else 0),
            "same_day_gaps_contributo": round(same_day_ratio * self.WEIGHTS['same_day_gaps'], 2),
            "short_gaps_contributo": round(short_ratio * self.WEIGHTS['short_gaps'], 2),
            "spacing_contributo": round((1 - self.features.spacing_entropy) * self.WEIGHTS['spacing'], 2),
            "std_anomaly_contributo": self.WEIGHTS['std_gap_anomaly'] if self.features.std_gap_days > self.features.avg_gap_days * 2 else 0,
            "avg_gap_bonus": self.WEIGHTS['avg_gap_bonus'] if 0 < self.features.avg_gap_days < 5 else 0
        }