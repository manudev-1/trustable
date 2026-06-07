import sys
from typing import Dict, Any
import json
from datetime import datetime

from analytic.ReviewPlotter import ReviewPlotter
from model.Review import Review
from analytic.SemanticAnalyzer import SemanticAnalyzer
from analytic.TemporalAnalyzer import TemporalAnalyzer
from analytic.ReportGenerator import ReportGenerator

def analyze_place_reviews(
    place_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Esegue analisi completa (temporale + semantica) su review di un luogo.
    
    Args:
        place_data: {
            "place_id": "...",
            "place_name": "...",
            "reviews": [list of Apify review objects]
        }
    
    Returns:
        Risultati combinati di analisi temporale e semantica
    """
    
    if not place_data.get("reviews"):
        return {
            "place_id": place_data.get("place_id"),
            "place_name": place_data.get("place_name"),
            "error": "No reviews found",
            "temporal_analysis": None,
            "semantic_analysis": None
        }
        
    
    reviews = place_data.get("reviews", [])
    print(f"[Temporal] Analyzing {len(reviews)} reviews...")
    report_gen = ReportGenerator(reviews)
    report_gen.print_summary()
    
    filename = f"./log/files/log_analisi_math_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_gen.save_report(filename)
    
    temporal_analyzer = TemporalAnalyzer(reviews)
    temporal_features = temporal_analyzer.extract_features()
    burst_analysis = temporal_analyzer.analyze_burst()
    
    temporal_result = {
        "total_reviews": len(reviews),
        "gini_index": temporal_features.gini_index,
        "burst_ratio": temporal_features.burst_ratio_value,
        "burst_type": burst_analysis.burst_type,
        "spacing_entropy": temporal_features.spacing_entropy,
        "avg_gap_days": temporal_features.avg_gap_days,
        "std_gap_days": temporal_features.std_gap_days
    }
    
    print(f"[Semantic] Analyzing patterns and templates...")
    semantic_analyzer = SemanticAnalyzer(tok_path="./analytic/data/wikipedia-it.tok", reviews=reviews)
    semantic_reports = semantic_analyzer.analyze(reviews)
    
    semantic_result = {
        "anomalous_windows": len(semantic_reports),
        "reports": [r.to_dict() for r in semantic_reports]
    }

    return {
        "place_id": place_data.get("place_id"),
        "place_name": place_data.get("place_name"),
        "analysis_date": "2026-06-05",
        "temporal_analysis": temporal_result,
        "semantic_analysis": semantic_result,
        "summary": _generate_summary(temporal_result, semantic_result)
    }

def _generate_summary(temporal: Dict, semantic: Dict) -> str:
    """
    Genera un riassunto della trust score della location.
    """
    scores = []
    
    if temporal["burst_type"] == "same_day_burst":
        scores.append("⚠ Temporal anomaly: same-day burst detected")
    elif temporal["burst_type"] == "short_burst":
        scores.append("⚠ Temporal anomaly: short-term burst detected")
    
    if temporal["gini_index"] > 0.6:
        scores.append("⚠ Temporal anomaly: high concentration (Gini > 0.6)")

    if semantic["anomalous_windows"] > 0:
        max_score = max([r["punteggio_anomalia"] for r in semantic["reports"]])
        if max_score >= 70:
            scores.append(f"⚠ Semantic anomaly: HIGH risk (score: {max_score:.0f})")
        elif max_score >= 40:
            scores.append(f"⚠ Semantic anomaly: MODERATE risk (score: {max_score:.0f})")
    
    if not scores:
        return "✓ No significant anomalies detected. Appears trustworthy."
    
    return " | ".join(scores)

def main():
    reviews = set([])
    
    if not reviews:
        print("Nessuna recensione da analizzare.")
        return
    
    place_data = {
        "place_id": "clinica_computer",
        "place_name": "Clinica Computer",
        "reviews": reviews
    }
    
    result = analyze_place_reviews(place_data)
    
    print(f"Analisi di {len(reviews)} recensioni...")
    
    print("\n" + "="*80)
    print(f"Analysis Results for: {result['place_name']}")
    print("="*80)
    print(f"\nSummary: {result['summary']}\n")
    
    print("Temporal Analysis:")
    print(f"  Total reviews: {result['temporal_analysis']['total_reviews']}")
    print(f"  Burst type: {result['temporal_analysis']['burst_type']}")
    print(f"  Gini index: {result['temporal_analysis']['gini_index']:.2f}")
    
    print(f"\nSemantic Analysis:")
    print(f"  Anomalous windows: {result['semantic_analysis']['anomalous_windows']}")
    
    if result['semantic_analysis']['reports']:
        for i, report in enumerate(result['semantic_analysis']['reports'], 1):
            print(f"\n  Window {i}:")
            print(f"    Period: {report['finestra_analizzata']['start_date']} to {report['finestra_analizzata']['end_date']}")
            print(f"    Anomaly score: {report['punteggio_anomalia']:.0f}/100")
            print(f"    Patterns found: {len(report['pattern_rilevati'])}")
            print(f"    Templates found: {len(report['template_individuati'])}")
    
    with open(f"./log/files/log_analisi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Full results saved to: ./log/files/log_analisi_semantica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    if "--plot" in sys.argv:
        plotter = ReviewPlotter(reviews)
        plotter.show_timeline()
        
        if "--hist" in sys.argv:
            plotter.show_monthly_histogram()

if __name__ == '__main__':
    main()