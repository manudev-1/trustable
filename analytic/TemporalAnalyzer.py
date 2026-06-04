from typing import List, Dict
from datetime import datetime
from analytic.DataParser import DateParser
import statistics
from collections import defaultdict, Counter
import numpy as np
import math

from model.Review import Review
from model.GapStatistics import GapStatistics
from model.BurstAnalysis import BurstAnalysis
from model.TemporalFeatures import TemporalFeatures

class TemporalAnalyzer:
    """
    Analizzatore dei pattern temporali delle recensioni.
    Calcola metriche di distribuzione, gap e burst.
    """
    
    def __init__(self, reviews: List[Review]):
        self.reviews = reviews
        self.dates = self._extract_dates()
        self.gaps = self._compute_gaps()
    
    def _extract_dates(self) -> List[datetime]:
        """Estrae e ordina tutte le date valide"""
        dates = []
        for review in self.reviews:
            dt = DateParser.parse(review.published_at_iso or review.published_at)
            if dt:
                dates.append(dt)
        return sorted(dates)
    
    def _compute_gaps(self) -> List[float]:
        """Calcola i gap in giorni tra recensioni consecutive"""
        if len(self.dates) < 2:
            return []
        
        gaps = []
        for i in range(1, len(self.dates)):
            delta = (self.dates[i] - self.dates[i - 1]).total_seconds() / 86400
            gaps.append(delta)
        return gaps
    
    def get_gap_statistics(self) -> GapStatistics:
        """Calcola statistiche descrittive sui gap"""
        if not self.gaps:
            return GapStatistics(0, 0, 0, 0, 0)
        
        return GapStatistics(
            avg_gap_days=statistics.mean(self.gaps),
            median_gap_days=statistics.median(self.gaps),
            std_gap_days=statistics.pstdev(self.gaps),
            min_gap=min(self.gaps),
            max_gap=max(self.gaps)
        )
    
    def get_monthly_density(self) -> Dict[str, int]:
        """Calcola la densità di recensioni per mese"""
        density = defaultdict(int)
        for date in self.dates:
            month_key = DateParser.get_month_key(date)
            density[month_key] += 1
        return dict(sorted(density.items()))
    
    def get_normalized_density(self, density: Dict[str, int]) -> Dict[str, float]:
        """Normalizza la densità (somma = 1)"""
        total = sum(density.values())
        if total == 0:
            return {}
        return {k: v / total for k, v in density.items()}
    
    @staticmethod
    def calculate_gini(values: List[float]) -> float:
        """Calcola l'indice di Gini per misurare la concentrazione"""
        arr = np.array(sorted(values))
        if len(arr) == 0 or np.sum(arr) == 0:
            return 0
        n = len(arr)
        index = np.arange(1, n + 1)
        return (2 * np.sum(index * arr)) / (n * np.sum(arr)) - (n + 1) / n
    
    @staticmethod
    def calculate_burst_ratio(month_counts: Dict[str, int]) -> float:
        """Rapporto tra il mese più attivo e il totale"""
        total = sum(month_counts.values())
        if total == 0:
            return 0
        return max(month_counts.values()) / total
    
    @staticmethod
    def calculate_top_k_ratio(month_counts: Dict[str, int], k: int = 3) -> float:
        """Rapporto dei k mesi più attivi sul totale"""
        total = sum(month_counts.values())
        if total == 0:
            return 0
        top_k = sorted(month_counts.values(), reverse=True)[:k]
        return sum(top_k) / total
    
    def analyze_burst(self) -> BurstAnalysis:
        """
        Analizza il tipo di burst temporale
        - same_day: molte recensioni nello stesso giorno
        - short: recensioni concentrate in pochi giorni
        - long: burst distribuito
        """
        if len(self.dates) < 2:
            return BurstAnalysis("none", 0, 0, 0)
        
        day_groups = defaultdict(int)
        for date in self.dates:
            day_groups[date.date()] += 1
        
        max_same_day = max(day_groups.values())
        same_day_ratio = max_same_day / len(self.dates) if self.dates else 0
        
        gaps_floor = [math.floor(g) for g in self.gaps] if self.gaps else []
        same_day_gaps_ratio = sum(g == 0 for g in gaps_floor) / len(gaps_floor) if gaps_floor else 0
        short_gaps_ratio = sum(1 for g in gaps_floor if 1 <= g <= 2) / len(gaps_floor) if gaps_floor else 0
        
        if same_day_ratio > 0.3:
            burst_type = "same_day_burst"
            score = 1.0
        elif short_gaps_ratio > 0.4 or same_day_gaps_ratio > 0.2:
            burst_type = "short_burst"
            score = 0.7
        else:
            burst_type = "long_burst"
            score = 0.3
        
        return BurstAnalysis(
            burst_type=burst_type,
            score=score,
            same_day_gaps_ratio=same_day_gaps_ratio,
            short_gaps_ratio=short_gaps_ratio,
            total_short_gaps_ratio=(same_day_gaps_ratio + short_gaps_ratio)
        )
    
    @staticmethod
    def calculate_spacing_entropy(gaps: List[float]) -> float:
        """
        Calcola l'entropia degli intervalli tra recensioni.
        Valori vicini a 1 indicano casualità umana,
        valori vicini a 0 indicano regolarità meccanica.
        """
        if not gaps:
            return 0
        
        rounded_gaps = [round(g) for g in gaps]
        freq = Counter(rounded_gaps)
        total = sum(freq.values())
        
        entropy = 0.0
        for count in freq.values():
            p = count / total
            entropy -= p * math.log(p + 1e-9)
        
        n = len(freq)
        if n <= 1:
            return 0
        return entropy / math.log(n + 1e-9)
    
    def extract_features(self) -> TemporalFeatures:
        """
        Estrae tutte le feature temporali per il calcolo dello score
        """
        density = self.get_monthly_density()
        normalized = self.get_normalized_density(density)
        normalized_values = list(normalized.values()) if normalized else []
        
        stats = self.get_gap_statistics()
        spacing = self.calculate_spacing_entropy(self.gaps)
        
        return TemporalFeatures(
            gini_index=self.calculate_gini(normalized_values),
            burst_ratio_value=self.calculate_burst_ratio(density),
            top_3_ratio=self.calculate_top_k_ratio(density, 3),
            spacing_entropy=spacing,
            avg_gap_days=stats.avg_gap_days,
            std_gap_days=stats.std_gap_days
        )