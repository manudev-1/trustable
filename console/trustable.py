import os
import argparse
import json
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

from scraper.GMRS import GoogleMapsReviewsScraper
from analytic.ReviewPlotter import ReviewPlotter
from model.Review import Review
from analytic.SemanticAnalyzer import SemanticAnalyzer
from analytic.TemporalAnalyzer import TemporalAnalyzer
from analytic.ReportGenerator import ReportGenerator

def analyze_place_reviews(place_data: Dict[str, Any], tok_path: str = "./analytic/data/wikipedia-it.tok") -> Dict[str, Any]:
    """
    Esegue analisi completa (temporale + semantica) su review di un luogo.
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
    
    os.makedirs("./log/files", exist_ok=True)
    
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
    semantic_analyzer = SemanticAnalyzer(tok_path=tok_path, reviews=reviews)
    semantic_reports = semantic_analyzer.analyze(reviews)
    
    semantic_result = {
        "anomalous_windows": len(semantic_reports),
        "reports": [r.to_dict() for r in semantic_reports]
    }

    return {
        "place_id": place_data.get("place_id"),
        "place_name": place_data.get("place_name"),
        "analysis_date": datetime.now().strftime('%Y-%m-%d'),
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
        scores_list = [
            r.get("punteggio_anomalia", 0) if isinstance(r, dict) else getattr(r, "punteggio_anomalia", 0)
            for r in semantic["reports"]
        ]
        if scores_list:
            max_score = max(scores_list)
            if max_score >= 70:
                scores.append(f"⚠ Semantic anomaly: HIGH risk (score: {max_score:.0f})")
            elif max_score >= 40:
                scores.append(f"⚠ Semantic anomaly: MODERATE risk (score: {max_score:.0f})")
    
    if not scores:
        return "✓ No significant anomalies detected. Appears trustworthy."
    
    return " | ".join(scores)

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Scrape Google Maps reviews using Apify."
    )
    
    parser.add_argument(
        '-t', '--token', 
        type=str, 
        default=os.getenv("APIFY_TOKEN"),
        help="Apify API Token (defaults to APIFY_TOKEN env variable)"
    )
    
    parser.add_argument(
        '-u', '--url', 
        type=str, 
        required=True, 
        help="Specific Google Maps URL to scrape"
    )
    
    parser.add_argument(
        '-n', '--num', 
        type=int, 
        required=False,
        default=100,
        help="Number of reviews to scrape"
    )
    
    parser.add_argument(
        '-tok', '--tokenizer', 
        type=str, 
        required=False,
        default="./analytic/data/wikipedia-it.tok",
        help="Path to the tokenizer file"
    )
    
    parser.add_argument(
        '--plot',
        action='store_true',
        help="Show timeline plot after analysis"
    )

    parser.add_argument(
        '--hist',
        action='store_true',
        help="Show monthly histogram plot after analysis (requires --plot)"
    )
    
    args = parser.parse_args()
    
    if not args.token:
        parser.error("Apify token is required. Provide it via .env file or use the --token flag.")
    
    print(f"Initializing scraper with token: {args.token[:5]}...")
    scraper = GoogleMapsReviewsScraper(args.token)
    
    print(f"Scraping reviews from target URL...")
    reviews = scraper.get_reviews(args.url, args.num)
    
    if not reviews:
        print("No reviews found. Please check the URL and try again.")
        return
    
    print(f"Successfully retrieved {len(reviews)} reviews.")
    
    place_data = {
        "place_id": args.url.split("?")[0],
        "place_name": "Scraped Location",
        "reviews": reviews
    }
    
    result = analyze_place_reviews(place_data, tok_path=args.tokenizer)
    
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
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"./log/files/log_analisi_{timestamp}.json"
    
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Full results saved to: {log_filename}")

    if args.plot:
        plotter = ReviewPlotter(reviews)
        plotter.show_timeline()
        
        if args.hist:
            plotter.show_monthly_histogram()
    

if __name__ == '__main__':
    main()