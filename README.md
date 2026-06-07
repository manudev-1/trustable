# Trustable

**Is a Google Business Profile trustable?**

A sophisticated Python tool for analyzing Google Maps reviews to detect trustworthiness indicators and anomalies. This system uses advanced temporal and semantic analysis to identify suspicious patterns in review behavior, helping businesses and users assess the authenticity of Google Business Profiles.

## Overview

Trustable performs comprehensive analysis on Google Maps reviews through:

- **Temporal Analysis**: Detects suspicious burst patterns, abnormal review distributions, and timing anomalies
- **Semantic Analysis**: Identifies template-based reviews, linguistic patterns, and content anomalies
- **Visualization**: Generates timeline and histogram plots of review distributions
- **Reporting**: Produces detailed JSON reports with anomaly scores and risk assessments

## Installation

### Prerequisites

- Python 3.7+
- Apify API account (for Google Maps review scraping)

### Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd trustable
   ```
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Install the package:

   ```bash
   pip install -e .
   ```
4. Set up your Apify token:
   Create a `.env` file in the project root:

   ```
   APIFY_TOKEN=your_apify_token_here
   ```

## Usage

### Main Command: `trustable`

Analyze reviews from a Google Maps location:

```bash
trustable -u "https://www.google.com/maps/place/..." --num 100
```

#### Arguments:

- `-u, --url` (required): Google Maps URL of the location to analyze
- `-n, --num` (optional): Number of reviews to scrape (default: 100)
- `-t, --token` (optional): Apify API token (defaults to `APIFY_TOKEN` env variable)
- `-tok, --tokenizer` (optional): Path to tokenizer file (default: `./analytic/data/wikipedia-it.tok`)
- `--plot`: Display timeline visualization of reviews
- `--hist`: Display monthly histogram (requires `--plot`)

#### Example:

```bash
trustable -u "https://www.google.com/maps/place/example" -n 50 --plot --hist
```

### Other Commands

- `gmrs`: Google Maps Reviews Scraper (direct scraping utility)
- `reviews_time`: Temporal analysis tools

## Project Structure

```
trustable/
├── console/                    # CLI entry points
│   ├── trustable.py           # Main analysis command
│   ├── gmrs.py                # Google Maps scraper CLI
│   └── reviews_time.py        # Temporal analysis CLI
├── scraper/                    # Review scraping
│   └── GMRS.py                # Google Maps Reviews Scraper implementation
├── model/                      # Data models
│   ├── Review.py              # Review data structure
│   ├── UserProfile.py         # User profile model
│   ├── MonthlyMetrics.py      # Monthly statistics
│   ├── TemporalFeatures.py    # Temporal feature extraction
│   ├── BurstAnalysis.py       # Burst pattern detection
│   ├── GapStatistics.py       # Gap analysis between reviews
│   └── DetectedPattern.py     # Pattern detection results
├── analytic/                   # Analysis modules
│   ├── ReviewPlotter.py       # Visualization tools
│   ├── TemporalAnalyzer.py    # Time-series analysis
│   ├── SemanticAnalyzer.py    # Content & pattern analysis
│   ├── TemplateDetector.py    # Review template detection
│   ├── DataParser.py          # Review data parsing
│   ├── CorpusManager.py       # Text corpus management
│   ├── RatingDistributionAnalyzer.py  # Rating statistics
│   ├── NGramAnalyzer.py       # N-gram analysis
│   ├── FakeScoreCalculator.py # Fake review scoring
│   ├── ReportGenerator.py     # Report generation
│   └── SemanticAnalyzer.py    # NLP-based analysis
├── log/                        # Analysis logs and reports
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Analysis Features

### Temporal Analysis

Detects timing-based anomalies:

- **Burst Detection**: Identifies same-day bursts or short-term review spikes
- **Distribution Analysis**: Calculates Gini index to measure review concentration
- **Gap Statistics**: Analyzes spacing between reviews for unusual patterns
- **Entropy Calculation**: Measures randomness in review timing

**Anomaly Indicators:**

- ⚠ Same-day burst: Multiple reviews posted on same day
- ⚠ Short-term burst: Unusual spikes within short periods
- ⚠ High concentration (Gini > 0.6): Reviews clustered in specific time periods

### Semantic Analysis

Identifies suspicious content patterns:

- **Template Detection**: Finds reviews with identical or nearly identical phrasing
- **N-gram Analysis**: Extracts common linguistic patterns
- **Fake Score Calculation**: Rates probability of fake reviews based on patterns
- **Anomalous Window Detection**: Identifies time periods with suspicious content

**Anomaly Scoring:**

- Score ≥ 70: HIGH risk of fake reviews
- Score 40-70: MODERATE risk
- Score < 40: LOW risk

## Output

### JSON Report Structure

Analysis results are saved to `log/files/` with timestamps:

```json
{
  "place_id": "location_url",
  "place_name": "Location Name",
  "analysis_date": "YYYY-MM-DD",
  "temporal_analysis": {
    "total_reviews": 100,
    "gini_index": 0.45,
    "burst_ratio": 0.12,
    "burst_type": "short_burst|same_day_burst|normal",
    "spacing_entropy": 4.2,
    "avg_gap_days": 2.5,
    "std_gap_days": 1.8
  },
  "semantic_analysis": {
    "anomalous_windows": 2,
    "reports": [...]
  },
  "summary": "Assessment summary with detected issues"
}
```

## Dependencies

Key dependencies include:

- **apify_client**: Google Maps review scraping via Apify
- **matplotlib**: Data visualization
- **pydantic**: Data validation
- **typer**: CLI framework

See `requirements.txt` for complete list.

## License

Developed by Manuele Barone

## Notes

- Requires Language tokenizer file (e.g. `wikipedia-it.tok`) for semantic analysis
- Uses Italian language processing by default
- Results are sensitive to the number of reviews analyzed (recommend 50+ for reliable analysis)
- Apify token is required for review scraping
