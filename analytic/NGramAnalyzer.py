import re
from typing import List
from collections import Counter

from model.Review import Review
from model.DetectedPattern import DetectedPattern, RatingDistribution
from analytic.CorpusManager import CorpusManager


class NGramAnalyzer:
    """
    FASE 2.1-2.2: Estrazione n-grammi e calcolo anomalia statistica.
    
    Per una data finestra temporale:
    1. Estrae bigrammi e trigrammi dalle recensioni
    2. Identifica quelli frequenti (>threshold% delle recensioni)
    3. Calcola anomaly_ratio vs probabilità attesa da corpus italiano
    """
    
    # Configurazione
    NGRAM_FREQUENCY_THRESHOLD = 0.10
    ANOMALY_RATIO_THRESHOLD = 10.0
    MIN_NGRAM_LENGTH = 2
    MAX_NGRAM_LENGTH = 3
    
    def __init__(self, corpus_manager: CorpusManager):
        """
        Args:
            corpus_manager: CorpusManager per le frequenze di riferimento
        """
        self.corpus = corpus_manager
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenizza un testo in parole, rimuovendo punteggiatura e stopwords comuni.
        
        Args:
            text: Testo da tokenizzare
        
        Returns:
            Lista di token
        """
        text = text.lower()
        
        text = re.sub(r"[^\w\s']", " ", text)
        
        tokens = text.split()
        
        italian_stopwords = {
            'il', 'la', 'lo', 'i', 'gli', 'le', 'a', 'di', 'da', 'per', 'con', 'su',
            'in', 'è', 'sono', 'e', 'o', 'che', 'non', 'se', 'più', 'meno', 'ho',
            'ha', 'abbiamo', 'hanno', 'ho', 'hai', 'sia', 'siamo'
        }
        
        filtered = [t for t in tokens 
                   if len(t) > 2 and t not in italian_stopwords]
        
        return filtered
    
    def _extract_ngrams(self, text: str, n: int) -> List[str]:
        """
        Estrae n-grammi da un testo.
        
        Args:
            text: Testo sorgente
            n: Lunghezza n-gramma (2 o 3)
        
        Returns:
            Lista di n-grammi
        """
        tokens = self._tokenize(text)
        ngrams = []
        
        for i in range(len(tokens) - n + 1):
            ngram = " ".join(tokens[i:i+n])
            ngrams.append(ngram)
        
        return ngrams
    
    def analyze_window(
        self,
        reviews: List[Review],
        window_review_ids: List[str]
    ) -> List[DetectedPattern]:
        """
        Analizza una finestra temporale per pattern n-gramma anomali.
        
        Args:
            reviews: Lista completa di tutte le review
            window_review_ids: ID delle review nella finestra (dal TimeWindow)
        
        Returns:
            Lista di DetectedPattern trovati
        """
        window_reviews = [r for r in reviews if r.review_id in window_review_ids]
        
        if not window_reviews:
            return []
        
        patterns = []
        

        for n in [2, 3]:
            all_ngrams = []
            for review in window_reviews:
                if review.text:
                    ngrams = self._extract_ngrams(review.text, n)
                    all_ngrams.extend(ngrams)
            
            if not all_ngrams:
                continue
            
            ngram_counts = Counter(all_ngrams)
            
            threshold_count = len(window_reviews) * self.NGRAM_FREQUENCY_THRESHOLD
            frequent_ngrams = {
                ng: count for ng, count in ngram_counts.items()
                if count >= threshold_count
            }
            
            for ngram, count in frequent_ngrams.items():
                prob_observed = count / len(window_reviews)
                
                prob_expected = self.corpus.get_ngram_frequency(ngram, n)
                
                if prob_expected < 0.000001:
                    prob_expected = self.corpus.estimate_probability_from_unigrams(ngram)

                if prob_expected > 0:
                    anomaly_ratio = prob_observed / prob_expected
                else:
                    anomaly_ratio = float('inf')
                
                if anomaly_ratio > self.ANOMALY_RATIO_THRESHOLD:
                    rating_dist = self._get_rating_distribution(
                        window_reviews, ngram
                    )
                    
                    temporal_conc = self._temporal_concentration(
                        window_reviews, ngram
                    )
                    
                    pattern = DetectedPattern(
                        pattern=ngram,
                        pattern_type=f"{'bigram' if n == 2 else 'trigram'}",
                        occurrences=count,
                        percentage_in_window=prob_observed,
                        anomaly_ratio=anomaly_ratio,
                        rating_distribution=rating_dist,
                        temporal_concentration_days=temporal_conc
                    )
                    patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p.anomaly_ratio, reverse=True)
    
    def _get_rating_distribution(
        self,
        reviews: List[Review],
        ngram: str
    ) -> RatingDistribution:
        """
        Calcola la distribuzione dei rating per le review che contengono un n-gramma.
        
        Args:
            reviews: Lista di review della finestra
            ngram: L'n-gramma in questione
        
        Returns:
            RatingDistribution
        """
        dist = RatingDistribution()
        
        for review in reviews:
            if review.text and ngram.lower() in review.text.lower():
                rating = review.rating or 3
                if rating == 5:
                    dist.stars_5 += 1
                elif rating == 4:
                    dist.stars_4 += 1
                elif rating == 3:
                    dist.stars_3 += 1
                elif rating == 2:
                    dist.stars_2 += 1
                elif rating == 1:
                    dist.stars_1 += 1
        
        return dist
    
    def _temporal_concentration(
        self,
        reviews: List[Review],
        ngram: str
    ) -> float:
        """
        Misura in quanti giorni è concentrato il pattern.
        
        Args:
            reviews: Review della finestra
            ngram: L'n-gramma
        
        Returns:
            Numero di giorni
        """
        from analytic.DataParser import DateParser
        
        dates = []
        for review in reviews:
            if review.text and ngram.lower() in review.text.lower():
                dt = DateParser.parse(review.published_at_iso or review.published_at)
                if dt:
                    dates.append(dt)
        
        if not dates:
            return 0
        
        dates = sorted(dates)
        span = (dates[-1] - dates[0]).days
        return max(span, 1)
