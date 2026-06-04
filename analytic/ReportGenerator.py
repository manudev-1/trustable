from typing import List, Dict, Any
from datetime import datetime
import json

from model.Review import Review
from analytic.TemporalAnalyzer import TemporalAnalyzer
from analytic.FakeScoreCalculator import FakeScoreCalculator
from model.MonthlyMetrics import MonthlyMetrics

class ReportGenerator:
    """Genera report strutturati in vari formati"""
    
    def __init__(self, reviews: List[Review]):
        self.reviews = reviews
        self.analyzer = TemporalAnalyzer(reviews)
    
    def generate_full_report(self) -> Dict[str, Any]:
        """
        Genera un report completo con tutte le metriche calcolate
        """
        density = self.analyzer.get_monthly_density()
        normalized = self.analyzer.get_normalized_density(density)
        stats = self.analyzer.get_gap_statistics()
        burst = self.analyzer.analyze_burst()
        features = self.analyzer.extract_features()
        
        score_calc = FakeScoreCalculator(features, burst, self.analyzer.gaps)
        fake_score = score_calc.calculate()
        score_breakdown = score_calc.get_score_breakdown()
        
        monthly_metrics = MonthlyMetrics(
            density_per_month=density,
            normalized_density=normalized,
            total_months=len(density),
            active_months=sum(1 for v in density.values() if v > 0),
            gini_index=features.gini_index,
            top_3_months_ratio=features.top_3_ratio,
            max_reviews_in_month=max(density.values()) if density else 0
        )
        
        return {
            "metadata": {
                "total_reviews": len(self.reviews),
                "timestamp_analisi": datetime.now().isoformat(),
                "analysis_type": "temporal_only"
            },
            "metriche_mensili": monthly_metrics.to_dict(),
            "analisi_gap_temporali": {
                "statistiche": stats.to_dict(),
                "lista_gap_giorni": [round(g, 2) for g in self.analyzer.gaps]
            },
            "analisi_burst": burst.to_dict(),
            "entropia_e_regolarita": {
                "spacing_entropy": round(features.spacing_entropy, 4),
                "interpretazione": "Vicino a 1: pattern umano/casuale. Vicino a 0: pattern meccanico/regolare."
            },
            "feature_temporali": features.to_dict(),
            "score_anomalia": {
                "punteggio_totale": fake_score,
                "soglia_attenzione": 60,
                "soglia_allerta": 80,
                "interpretazione": self._interpret_score(fake_score),
                "dettaglio_punteggi": score_breakdown
            }
        }
    
    def _interpret_score(self, score: float) -> str:
        """Interpreta il punteggio ottenuto"""
        if score < 30:
            return "Pattern temporale normale. Recensioni distribuite naturalmente."
        elif score < 60:
            return "Lieve anomalia temporale. Possibile concentrazione occasionale."
        elif score < 80:
            return "ANOMALIA SIGNIFICATIVA. Pattern temporali sospetti rilevati."
        else:
            return "ALTA PROBABILITÀ DI FAKE REVIEWS. Pattern temporali molto anomali."
    
    def save_report(self, filepath: str) -> None:
        """Salva il report in formato JSON"""
        report = self.generate_full_report()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        print(f"Report salvato in: {filepath}")
    
    def print_summary(self) -> None:
        """Stampa un riassunto leggibile del report"""
        report = self.generate_full_report()
        
        print("\n" + "="*60)
        print("ANALISI TEMPORALE RECENSIONI")
        print("="*60)
        
        print(f"\n📊 METADATI")
        print(f"   Totale recensioni: {report['metadata']['total_reviews']}")
        
        print(f"\n📅 DISTRIBUZIONE MENSILE")
        m_metrics = report['metriche_mensili']
        print(f"   Mesi totali: {m_metrics['total_months']}")
        print(f"   Mesi con recensioni: {m_metrics['active_months']}")
        print(f"   Massimo recensioni in un mese: {m_metrics['max_reviews_in_month']}")
        print(f"   Indice di Gini: {m_metrics['gini_index']} (0=uniforme, 1=concentrata)")
        print(f"   Top 3 mesi: {m_metrics['top_3_months_ratio']*100:.1f}% del totale")
        
        print(f"\n⏱️ GAP TEMPORALI")
        gaps = report['analisi_gap_temporali']['statistiche']
        print(f"   Gap medio: {gaps['avg_gap_days']:.1f} giorni")
        print(f"   Gap mediano: {gaps['median_gap_days']:.1f} giorni")
        print(f"   Deviazione std: {gaps['std_gap_days']:.1f} giorni")
        
        print(f"\n💥 ANALISI BURST")
        burst = report['analisi_burst']
        print(f"   Tipo: {burst['burst_type']}")
        print(f"   Ratio gap stesso giorno: {burst['same_day_gaps_ratio']*100:.1f}%")
        print(f"   Ratio gap brevi (1-2gg): {burst['short_gaps_ratio']*100:.1f}%")
        
        print(f"\n🎯 SCORE FINALE")
        score_info = report['score_anomalia']
        score = score_info['punteggio_totale']
        
        if score < 30:
            emoji = "🟢"
        elif score < 60:
            emoji = "🟡"
        elif score < 80:
            emoji = "🟠"
        else:
            emoji = "🔴"
        
        print(f"   {emoji} Punteggio anomalia: {score}%")
        print(f"   {score_info['interpretazione']}")
        
        print("\n" + "="*60 + "\n")