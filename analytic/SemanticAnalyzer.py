import logging
from typing import List, Dict, Optional

from model.Review import Review
from model.DetectedPattern import SemanticReport, TimeWindow
from analytic.TemporalWindowDetector import TemporalWindowDetector
from analytic.NGramAnalyzer import NGramAnalyzer
from analytic.TemplateDetector import TemplateDetector
from analytic.RatingDistributionAnalyzer import RatingDistributionAnalyzer
from analytic.CorpusManager import CorpusManager

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """
    ANALIZZATORE SEMANTICO PRINCIPALE
    
    Orchestr le 4 fasi di analisi per rilevare fake review campaign:
    1. Scansione temporale → identifica finestre ad alta densità
    2. Analisi pattern sequenziali → n-grammi anomali e template
    3. Verifica distribuzione rating → bias su estremi
    4. Calcolo score composito → 0-100
    """
    
    SCORE_WEIGHTS = {
        'density_anomaly': 25,
        'pattern_rigidity': 25,
        'rating_concentration': 20,
        'template_entropy': 15,
        'text_uniformity': 10,
        'template_pos_patterns': 5
    }
    
    def __init__(self, 
                corpus_path: Optional[str] = None, 
                tok_path: Optional[str] = None,
                reviews: Optional[List[Review]] = None
                ):
        """
        Inizializza l'analizzatore.
        
        Args:
            corpus_path: Path opzionale a corpus custom
        """
        self.corpus = CorpusManager(corpus_path, tok_path)
        self.window_detector = TemporalWindowDetector(reviews)
        self.ngram_analyzer = NGramAnalyzer(self.corpus)
        self.template_detector = TemplateDetector()
        self.rating_analyzer = RatingDistributionAnalyzer()
    
    def analyze(self, reviews: List[Review]) -> List[SemanticReport]:
        """
        Esegue l'analisi semantica completa su una lista di review.
        
        Args:
            reviews: Lista di Review object
        
        Returns:
            Lista di SemanticReport per ogni finestra anomala rilevata
        """
        if not reviews:
            logger.warning("No reviews provided for semantic analysis")
            return []
        
        logger.info(f"Starting semantic analysis on {len(reviews)} reviews")

        logger.debug("Phase 1: Temporal window detection")
        detector = TemporalWindowDetector(reviews)
        anomalous_windows = detector.detect_anomalous_windows()
        
        if not anomalous_windows:
            logger.info("No anomalous temporal windows detected")
            return []
        
        logger.info(f"Found {len(anomalous_windows)} anomalous windows")
        
        reports = []
        for window in anomalous_windows:
            report = self._analyze_window(reviews, window)
            reports.append(report)
        
        return sorted(reports, key=lambda r: r.anomaly_score, reverse=True)
    
    def _analyze_window(
        self,
        all_reviews: List[Review],
        window: TimeWindow
    ) -> SemanticReport:
        """
        Analizza una singola finestra temporale anomala.
        
        Args:
            all_reviews: Tutte le review
            window: TimeWindow da analizzare
        
        Returns:
            SemanticReport per questa finestra
        """
        logger.debug(f"Analyzing window {window.start_date} to {window.end_date}")
        
        patterns = self.ngram_analyzer.analyze_window(
            all_reviews,
            window.review_ids
        )
        
        templates = self.template_detector.analyze_window(
            all_reviews,
            window.review_ids
        )
        
        score_components = self._calculate_score_components(
            window,
            patterns,
            templates,
            all_reviews,
            window.review_ids
        )
        
        anomaly_score = self._compute_final_score(score_components)
        
        recommendation = self._generate_recommendation(
            window, anomaly_score, patterns, templates
        )
        
        report = SemanticReport(
            window=window,
            patterns=patterns[:10],
            templates=templates[:5],
            anomaly_score=anomaly_score,
            interpretation="",
            recommendation=recommendation,
            score_components=score_components
        )
        
        return report
    
    def _calculate_score_components(
        self,
        window: TimeWindow,
        patterns: List,
        templates: List,
        all_reviews: List[Review],
        window_review_ids: List[str]
    ) -> Dict[str, float]:
        """
        Calcola i componenti individuali dello score.
        
        Returns:
            Dict con contributi di ogni fattore
        """
        components = {}
        
        if window.density_zscore > 2.0:
            components['density_anomaly'] = min(
                (window.density_zscore - 2.0) / 3.0,
                1.0
            ) * self.SCORE_WEIGHTS['density_anomaly']
        else:
            components['density_anomaly'] = 0
        
        if patterns:
            rigid_patterns_count = sum(
                1 for p in patterns
                if p.anomaly_ratio > 10.0
            )
            components['pattern_rigidity'] = min(
                rigid_patterns_count / 5.0,
                1.0
            ) * self.SCORE_WEIGHTS['pattern_rigidity']
        else:
            components['pattern_rigidity'] = 0
        
        rating_bias_score = self.rating_analyzer.get_rating_bias_score(patterns)
        components['rating_concentration'] = (
            rating_bias_score * self.SCORE_WEIGHTS['rating_concentration']
        )
        
        if templates:
            avg_entropy = sum(t.entropy for t in templates) / len(templates)
            if avg_entropy < 1.5:
                components['template_entropy'] = (
                    (1.5 - avg_entropy) / 1.5
                ) * self.SCORE_WEIGHTS['template_entropy']
            else:
                components['template_entropy'] = 0
        else:
            components['template_entropy'] = 0
        
        window_reviews = [r for r in all_reviews if r.review_id in window_review_ids]
        text_lengths = [
            len(r.text or "") for r in window_reviews if r.text
        ]
        if text_lengths and len(text_lengths) > 1:
            import statistics
            std_length = statistics.stdev(text_lengths) if len(text_lengths) > 1 else 0
            if std_length < 10:
                components['text_uniformity'] = (
                    (10 - std_length) / 10
                ) * self.SCORE_WEIGHTS['text_uniformity']
            else:
                components['text_uniformity'] = 0
        else:
            components['text_uniformity'] = 0
        
        components['template_pos_patterns'] = 0
        
        return components
    
    def _compute_final_score(self, components: Dict[str, float]) -> float:
        """
        Calcola il punteggio finale da 0-100.
        
        Args:
            components: Dict dei contributi
        
        Returns:
            Score finale (0-100)
        """
        total = sum(components.values())
        return min(round(total, 1), 100.0)
    
    def _generate_recommendation(
        self,
        window: TimeWindow,
        score: float,
        patterns: List,
        templates: List
    ) -> str:
        """
        Genera una raccomandazione basata sul score.
        
        Args:
            window: TimeWindow
            score: Anomaly score
            patterns: Pattern rilevati
            templates: Template rilevati
        
        Returns:
            Testo raccomandazione
        """
        if score < 40:
            return "Pattern temporale entro norma. Nessun'azione richiesta."
        
        elif score < 70:
            recommendations = [
                f"Zona grigia: possibile campagna modesta nel periodo {window.start_date}/{window.end_date}."
            ]
            
            if patterns:
                top_pattern = patterns[0]
                recommendations.append(
                    f"Verificare manualmente pattern ricorrente: '{top_pattern.pattern}' "
                    f"(anomaly ratio: {top_pattern.anomaly_ratio:.0f}x)"
                )
            
            if templates:
                recommendations.append(
                    f"Rilevati {len(templates)} template pattern con bassa entropia."
                )
            
            return " ".join(recommendations)
        
        else:
            recommendations = [
                f"FORTE INDICATORE di fake review campaign nel periodo {window.start_date}/{window.end_date}.",
                f"Score anomalia: {score:.0f}/100.",
                f"Approfondire manualmente le {window.total_reviews} recensioni di questo periodo."
            ]
            
            if patterns:
                top_patterns = patterns[:3]
                pattern_strs = [
                    f"'{p.pattern}' ({p.occurrences}x, ratio {p.anomaly_ratio:.0f}x)"
                    for p in top_patterns
                ]
                recommendations.append(
                    f"Pattern anomali rilevati: {'; '.join(pattern_strs)}"
                )
            
            if templates:
                entropy_sum = sum(t.entropy for t in templates)
                avg_entropy = entropy_sum / len(templates)
                recommendations.append(
                    f"Template rigidi trovati ({len(templates)} template, "
                    f"entropia media: {avg_entropy:.2f})"
                )
            
            return " ".join(recommendations)
