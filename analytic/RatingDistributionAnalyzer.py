from typing import List
from model.DetectedPattern import DetectedPattern


class RatingDistributionAnalyzer:
    """
    FASE 2.4: Analisi della distribuzione dei rating per pattern rilevati.
    
    Verifica se i pattern sono concentrati su rating estremi (5★ o 1-2★),
    il che indica automatizzazione coordinata.
    """
    
    RATING_CONCENTRATION_THRESHOLD = 0.80
    
    def __init__(self):
        pass
    
    def analyze_pattern_rating_concentration(
        self,
        pattern: DetectedPattern
    ) -> float:
        """
        Calcola la concentrazione di un pattern su rating estremi.
        
        Args:
            pattern: DetectedPattern da analizzare
        
        Returns:
            Percentuale di concentrazione (0-1)
        """
        return pattern.rating_distribution.get_extreme_concentration()
    
    def get_rating_bias_score(
        self,
        patterns: List[DetectedPattern]
    ) -> float:
        """
        Calcola il score di bias di rating per un insieme di pattern.
        
        Se molti pattern sono concentrati su rating estremi, indica campagna coordinata.
        
        Args:
            patterns: Lista di DetectedPattern
        
        Returns:
            Score 0-1 (0=no bias, 1=massimo bias)
        """
        if not patterns:
            return 0.0
        
        biased_patterns = sum(
            1 for p in patterns
            if self.analyze_pattern_rating_concentration(p) > self.RATING_CONCENTRATION_THRESHOLD
        )
        
        return biased_patterns / len(patterns)
    
    @staticmethod
    def describe_rating_pattern(pattern: DetectedPattern) -> str:
        """
        Descrizione qualitativa del bias di rating di un pattern.
        
        Args:
            pattern: DetectedPattern
        
        Returns:
            Descrizione testuale
        """
        dist = pattern.rating_distribution
        total = dist.total()
        
        if total == 0:
            return "no data"
        
        pct_5 = dist.stars_5 / total
        pct_1_2 = (dist.stars_1 + dist.stars_2) / total
        pct_neutral = (dist.stars_3 + dist.stars_4) / total
        
        if pct_5 > 0.7:
            return f"strongly positive (5★: {pct_5*100:.0f}%)"
        elif pct_1_2 > 0.7:
            return f"strongly negative (1-2★: {pct_1_2*100:.0f}%)"
        elif pct_neutral > 0.6:
            return f"mixed/neutral (3-4★: {pct_neutral*100:.0f}%)"
        else:
            return "balanced"
