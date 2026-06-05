from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class RatingDistribution:
    """Distribuzione dei rating per un pattern rilevato"""
    stars_5: int = 0
    stars_4: int = 0
    stars_3: int = 0
    stars_2: int = 0
    stars_1: int = 0
    
    def total(self) -> int:
        return self.stars_5 + self.stars_4 + self.stars_3 + self.stars_2 + self.stars_1
    
    def get_extreme_concentration(self) -> float:
        """Percentuale di concentrazione su rating estremi (5★ o 1-2★)"""
        total = self.total()
        if total == 0:
            return 0
        extreme = self.stars_5 + self.stars_1 + self.stars_2
        return extreme / total
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "5★": self.stars_5,
            "4★": self.stars_4,
            "3★": self.stars_3,
            "2★": self.stars_2,
            "1★": self.stars_1
        }


@dataclass
class DetectedPattern:
    """Un pattern rilevato come potenzialmente anomalo"""
    pattern: str
    pattern_type: str
    occurrences: int
    percentage_in_window: float
    anomaly_ratio: float
    rating_distribution: RatingDistribution
    temporal_concentration_days: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern,
            "tipo": self.pattern_type,
            "occorrenze": self.occurrences,
            "percentuale_recensioni": round(self.percentage_in_window * 100, 1),
            "anomaly_ratio": round(self.anomaly_ratio, 1),
            "rating_distribution": self.rating_distribution.to_dict(),
            "concentrazione_temporale_giorni": round(self.temporal_concentration_days, 1)
        }


@dataclass
class DetectedTemplate:
    """Un template pattern con slot variabili"""
    template: str
    slot_fillers: Dict[str, List[str]]
    entropy: float
    occurrences: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template": self.template,
            "slot_filler": self.slot_fillers,
            "entropia": round(self.entropy, 2),
            "occorrenze": self.occurrences
        }


@dataclass
class TimeWindow:
    """Finestra temporale identificata"""
    start_date: str
    end_date: str
    total_reviews: int
    density_zscore: float
    review_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_reviews": self.total_reviews,
            "density_zscore": round(self.density_zscore, 2)
        }


@dataclass
class SemanticReport:
    """Report completo di analisi semantica per una finestra temporale"""
    window: TimeWindow
    patterns: List[DetectedPattern] = field(default_factory=list)
    templates: List[DetectedTemplate] = field(default_factory=list)
    anomaly_score: float = 0.0
    interpretation: str = ""
    recommendation: str = ""
    
    score_components: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        interpretation_map = {
            (0, 40): "pattern normale",
            (40, 70): "zona grigia, possibile campagna modesta",
            (70, 100): "forte indicatore di fake review campaign"
        }
        
        interp = "pattern anomalo"
        for (low, high), desc in interpretation_map.items():
            if low <= self.anomaly_score < high:
                interp = desc
                break
        
        return {
            "finestra_analizzata": self.window.to_dict(),
            "pattern_rilevati": [p.to_dict() for p in self.patterns],
            "template_individuati": [t.to_dict() for t in self.templates],
            "punteggio_anomalia": round(self.anomaly_score, 1),
            "interpretazione": interp,
            "raccomandazione": self.recommendation,
            "score_breakdown": {k: round(v, 2) for k, v in self.score_components.items()}
        }
