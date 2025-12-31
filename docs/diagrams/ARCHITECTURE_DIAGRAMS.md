# 🏗️ Architecture Diagram - prod/ Complete System

## 1. Data Flow - From Collection to Dashboard

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    DAILY AUTOMATION ORCHESTRATION                        │
│              (prod/automation/daily_automation.py)                       │
│                                                                          │
│  Runs daily schedule or on-demand from n8n workflows                    │
└──────────┬──────────────────┬──────────────────┬──────────────────┬─────┘
           │                  │                  │                  │
        STEP 1             STEP 2             STEP 3             STEP 4
        NEWS               OPTIONS           SENTIMENT          DASHBOARD
        COLLECT            COLLECT           ANALYSIS           GENERATE
           │                  │                  │                  │
           ▼                  ▼                  ▼                  ▼

╔════════════════════╗ ╔════════════════════╗ ╔════════════════════╗ ╔════════════╗
║ collect_news.py    ║ ║collect_options.py  ║ ║ analyze_all_       ║ ║generate_   ║
║ (Docker only)      ║ ║                    ║ ║ sentiment.py       ║ ║dashboard_  ║
║ + NewsAPI          ║ ║ + yfinance         ║ ║ (launcher)         ║ ║3levels.py  ║
║                    ║ ║ + Alpha Vantage    ║ ║                    ║ ║            ║
║ → News JSON        ║ ║ → CSV files        ║ ║ For each ticker:   ║ ║ Aggregates ║
║                    ║ ║ → JSON metrics     ║ ║   launch V4 engine ║ ║ all data   ║
╚────────────────────╚ ╚────────────────────╚ ╚────────────────────╚ ╚────────────╚
           │                  │                  │                  │
           │                  │                  │                  │
           └──────────────────┴──────────────────┴──────────────────┘
                              │
                              ▼
      ┌───────────────────────────────────────────────────────────┐
      │         DATA AGGREGATION LAYER                            │
      │                                                           │
      │  local_files/ (or /data/ in Docker)                     │
      │  ├─ sentiment_analysis/                                  │
      │  │  ├─ NVDA_latest_v4.json    [~50-100 KB each]         │
      │  │  ├─ MSFT_latest_v4.json                              │
      │  │  ├─ GOOGL_latest_v4.json                             │
      │  │  └─ ... (15 tickers total)                           │
      │  │                                                       │
      │  ├─ options_data/                                        │
      │  │  ├─ NVDA_latest_sentiment.json                       │
      │  │  ├─ NVDA_calls_2025-12-30.csv      [Greeks, IV]      │
      │  │  ├─ NVDA_puts_2025-12-30.csv                         │
      │  │  └─ ... (15 tickers × 2 files = 30 CSVs)            │
      │  │                                                       │
      │  └─ companies/                                           │
      │     ├─ NVDA_news.json         [30-day rolling window]   │
      │     ├─ MSFT_news.json                                    │
      │     └─ ... (15 tickers total)                           │
      │                                                           │
      └───────────────────────────┬────────────────────────────┘
                                  │
                                  ▼
      ┌───────────────────────────────────────────────────────────┐
      │  DASHBOARD v4_3levels.html (SPA - Single Page App)       │
      │  Location: prod/dashboard/dashboard_v4_3levels.html      │
      │                                                           │
      │  🔹 Level 1: Grid View (All 15 tickers)                  │
      │     - Sentiment score + color coding                     │
      │     - Put/call ratio                                      │
      │     - IV (implied volatility)                            │
      │     - Quick stats                                         │
      │                                                           │
      │  🔹 Level 2: Ticker Detail (Click to drill-down)        │
      │     - Time-series sentiment chart (30 days)              │
      │     - News articles list (with sentiment)                │
      │     - Options summary (volume, OI)                       │
      │     - Composite score breakdown                          │
      │                                                           │
      │  🔹 Level 3: Options Deep Dive (Advanced Analysis)       │
      │     - Volatility Smile chart                             │
      │     - Volume heatmap                                      │
      │     - Open Interest ladder                               │
      │     - Money flow analysis                                │
      │     - 3D price-volatility surface                        │
      │                                                           │
      │  Architecture: Pure React-like JS (no external APIs)     │
      │  Data: ALL embedded in <script> JSON block (~2-5MB)     │
      │  Status: GENERATED FILE (not manually edited)            │
      │                                                           │
      └───────────────────────────┬────────────────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
                ▼                 ▼                 ▼
        ┌────────────────┐ ┌─────────────────┐ ┌──────────────┐
        │ STREAMLIT APPS │ │   STATIC HTML   │ │ HTTP SERVER  │
        │  (Interactive) │ │ (for archival)  │ │ (API access) │
        │                │ │                 │ │              │
        │ Port 8501-8502 │ │ Can be emailed  │ │ Port 8000    │
        │                │ │ or archived     │ │              │
        │ - Options      │ │                 │ │ - /api/data/ │
        │ - Companies    │ │ Portable        │ │ - /dashboard │
        │ - Timeline     │ │                 │ │              │
        └────────────────┘ └─────────────────┘ └──────────────┘
```

## 2. Core Processing Engine - Advanced Sentiment Engine V4

```
┌─────────────────────────────────────────────────────────────────────────┐
│         ADVANCED SENTIMENT ENGINE V4 - DUAL BRAIN ARCHITECTURE          │
│     (prod/analysis/advanced_sentiment_engine_v4.py - 1380 lines)        │
│                                                                          │
│  Input per ticker:                                                      │
│  ├─ News articles (from local_files/companies/{TICKER}_news.json)      │
│  ├─ Options data (from local_files/options_data/)                      │
│  └─ Historical sentiment (for trend analysis)                          │
│                                                                          │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    ┌────────┐      ┌────────┐      ┌─────────┐
    │ SYSTEM │      │ SYSTEM │      │FALLBACK │
    │   2    │      │   1    │      │         │
    │(LOGIC) │      │(NARRATIVE) │  │FinBERT │
    └────────┘      └────────┘      └─────────┘
    Qwen 2.5 7B     Llama 3.1 8B    Transformer
        │                │              │
        │ JSON struct    │ Nuance       │ Sentiment
        │ Math           │ Story        │ confidence
        │ Config         │ Catalhysts   │ score
        │                │              │
        │                │              │
        └────────────────┼──────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │  MULTI-DIMENSIONAL ANALYSIS         │
        │                                     │
        │  1. NEWS SENTIMENT                  │
        │     - Article sentiment scores      │
        │     - Catalyst detection            │
        │     - Trend analysis                │
        │     - Confidence scoring            │
        │                                     │
        │  2. OPTIONS SENTIMENT               │
        │     - Put/call ratio trend          │
        │     - IV (implied volatility) rise  │
        │     - Open Interest changes         │
        │     - Greek dynamics (delta, gamma) │
        │                                     │
        │  3. ANALYST INSIGHTS                │
        │     - Price target changes          │
        │     - Recommendations               │
        │     - Consensus shifts              │
        │                                     │
        │  4. VOLATILITY REGIME DETECTION     │
        │     - Calm (normal market)          │
        │     - Rising (fear)                 │
        │     - Crash (panic)                 │
        │     - Euphoria (greed)              │
        │                                     │
        │  5. COMPOSITE SCORING               │
        │     - Weighted average of signals   │
        │     - Confidence aggregation        │
        │     - Alert generation             │
        │                                     │
        └────────────────┬────────────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │  OUTPUT: {TICKER}_latest_v4.json    │
        │                                     │
        │  {                                  │
        │    "ticker": "NVDA",                │
        │    "timestamp": "2025-12-30T14:30", │
        │    "sentiment": {                   │
        │      "score": 0.72,                 │
        │      "confidence": 0.89,            │
        │      "components": {                │
        │        "news_sentiment": 0.68,      │
        │        "options_sentiment": 0.76,   │
        │        "analyst_sentiment": 0.71    │
        │      },                             │
        │      "volatility_regime": "rising", │
        │      "catalysts": [...],            │
        │      "alerts": [...]                │
        │    }                                │
        │  }                                  │
        │                                     │
        └─────────────────────────────────────┘
```

## 3. Module Dependency Graph

```
┌────────────────────────────────────────────────────────────────────────┐
│              CONFIGURATION LAYER (Single Source of Truth)              │
│                                                                        │
│              ┌──────────────────────────────────────┐                │
│              │  companies_config.py                 │                │
│              │  - 15 tickers (NVDA, MSFT, etc.)    │                │
│              │  - Sectors (AI Hardware, Software)   │                │
│              │  - Search keywords                   │                │
│              │  - get_all_companies() function      │                │
│              └──────────────────────────────────────┘                │
│                          ▲                                            │
│                          │ (used by)                                  │
│        ┌─────────────────┼─────────────────┬──────────────┐          │
│        │                 │                 │              │          │
│        ▼                 ▼                 ▼              ▼          │
│    ┌────────┐    ┌─────────────┐    ┌────────┐    ┌────────┐       │
│    │COLLECT │    │   ANALYZE   │    │ DAILY  │    │AGGREGATE│       │
│    │OPTIONS │    │   SENTIMENT │    │AUTOMATION  │COMPANIES   │     │
│    │        │    │             │    │        │    │        │       │
│    │collect │    │analyze_all_ │    │daily_  │    │aggregate│       │
│    │options │    │sentiment.py │    │automation   │companies      │
│    │.py     │    │             │    │.py     │    │.py     │       │
│    └───┬────┘    └──────┬──────┘    └────┬───┘    └────┬────┘       │
│        │                │                │            │              │
│        └────────────────┼────────────────┼────────────┘              │
│                         │                │                           │
│        ┌────────────────┘                │                           │
│        │                                 │                           │
│        └─────────────────────────────────┼─────────────────┐         │
│                                          │                │         │
│                                          ▼                ▼         │
│                              ┌──────────────────────────────┐        │
│                              │ADVANCED_SENTIMENT_ENGINE_V4  │        │
│                              │                              │        │
│                              │ - Qwen 2.5 7B              │        │
│                              │ - Llama 3.1 8B             │        │
│                              │ - FinBERT fallback         │        │
│                              │ - Analyst insights         │        │
│                              │ - Catalyst detection       │        │
│                              └──────────────┬───────────────┘        │
│                                             │                        │
│                                             ▼                        │
│                              ┌──────────────────────────────┐        │
│                              │GENERATE_DASHBOARD_3LEVELS    │        │
│                              │                              │        │
│                              │ - Loads all _v4.json files │        │
│                              │ - Loads all options CSVs    │        │
│                              │ - Loads news JSON files     │        │
│                              │ - Generates SPA HTML        │        │
│                              └──────────────┬───────────────┘        │
│                                             │                        │
│                                             ▼                        │
│                              ┌──────────────────────────────┐        │
│                              │dashboard_v4_3levels.html     │        │
│                              │(Pure JavaScript SPA)         │        │
│                              └──────────────────────────────┘        │
└────────────────────────────────────────────────────────────────────────┘
```

## 4. File Dependency Tree

```
ROOT: companies_config.py (MASTER CONFIG)
  │
  ├─── collect_options.py
  │    ├─ yfinance
  │    ├─ pandas
  │    └─ outputs: {TICKER}_latest_sentiment.json, {TICKER}_calls_*.csv
  │
  ├─── analyze_all_sentiment.py (BATCH LAUNCHER)
  │    ├─ batch_loader_v2.py
  │    └─ advanced_sentiment_engine_v4.py (PER TICKER)
  │        ├─ finbert_analyzer.py
  │        ├─ analyst_insights_integration.py
  │        │  ├─ analyst_signals.py
  │        │  └─ price_target_parser.py
  │        ├─ contextual_sentiment_analyzer.py
  │        ├─ comparative_sentiment_analysis.py
  │        └─ outputs: {TICKER}_latest_v4.json
  │
  ├─── generate_dashboard_3levels.py
  │    ├─ reads: sentiment_analysis/{TICKER}_latest_v4.json
  │    ├─ reads: options_data/{TICKER}_latest_sentiment.json
  │    ├─ reads: companies/{TICKER}_news.json
  │    └─ outputs: dashboard_v4_3levels.html (FINAL ARTIFACT)
  │
  └─── daily_automation.py (ORCHESTRATOR)
       ├─ collect_options.py
       ├─ analyze_all_sentiment.py
       ├─ generate_dashboard_3levels.py
       └─ logging, error handling, quota checking
```

## 5. Data Types & Structures

### News Article Structure
```json
{
  "articles": [
    {
      "title": "NVIDIA Announces New AI Chip",
      "description": "...",
      "published_at": "2025-12-30T10:30:00Z",
      "source": "Reuters",
      "url": "https://...",
      "sentiment_score": 0.75,
      "importance": "high"
    }
  ]
}
```

### Options Sentiment JSON
```json
{
  "ticker": "NVDA",
  "timestamp": "2025-12-30T16:00:00Z",
  "metrics": {
    "put_call_ratio": 0.95,
    "put_call_ratio_trend": "rising",
    "implied_volatility": 32.5,
    "iv_trend": "increasing",
    "open_interest_calls": 1250000,
    "open_interest_puts": 980000,
    "volume_calls": 850000,
    "volume_puts": 650000,
    "composite_score": 0.68
  }
}
```

### Sentiment Analysis Output (V4)
```json
{
  "ticker": "NVDA",
  "timestamp": "2025-12-30T14:30:00Z",
  "version": "v4",
  "sentiment_analysis": {
    "news_sentiment": 0.72,
    "news_confidence": 0.89,
    "options_sentiment": 0.68,
    "options_confidence": 0.82,
    "analyst_sentiment": 0.71,
    "analyst_confidence": 0.85,
    "composite_score": 0.70,
    "composite_confidence": 0.85
  },
  "components": {
    "news_summary": "...",
    "options_summary": "...",
    "volatility_regime": "rising_fear"
  },
  "catalysts": [
    {"date": "2025-12-31", "title": "Q4 Earnings", "impact": "high"}
  ],
  "alerts": [
    {"level": "warning", "message": "IV spiking above 30%"}
  ]
}
```

## 6. Environment Paths

### Docker Container
```
/data/
├── scripts/                    → ACTIVE CODE (pip installed)
│   ├── collect_news.py
│   ├── advanced_sentiment_engine_v4.py
│   └── ...
├── sentiment_analysis/         → OUTPUTS
├── options_data/              → OUTPUTS
└── files/companies/           → NEWS DATA
```

### Windows Local (Development)
```
c:\n8n-local-stack\
├── prod/                      → ACTIVE CODE
│   ├── analysis/
│   ├── collection/
│   ├── dashboard/
│   └── ...
└── local_files/              → OUTPUTS & DATA
    ├── sentiment_analysis/
    ├── options_data/
    └── companies/
```

### Path Resolution Logic (Implemented in all scripts)
```python
if os.path.exists('/data/scripts'):
    # DOCKER MODE
    DATA_DIR = '/data'
    SCRIPT_DIR = '/data/scripts'
else:
    # LOCAL MODE
    DATA_DIR = os.path.join(PROJECT_ROOT, 'local_files')
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
```

## 7. Communication Protocols

### News Collection (Daily)
```
NewsAPI (FREE tier) 
→ collect_news.py 
→ {TICKER}_news.json 
→ ✓ Stored locally
```

### Options Collection (Daily)
```
yfinance (FREE)
→ collect_options.py
→ {TICKER}_calls_*.csv, {TICKER}_puts_*.csv, {TICKER}_latest_sentiment.json
→ ✓ Stored locally
```

### Sentiment Analysis (Per ticker)
```
Local news/options files
→ advanced_sentiment_engine_v4.py
→ Ollama/LLM endpoints (Qwen + Llama)
→ {TICKER}_latest_v4.json
→ ✓ Stored locally
```

### Dashboard Generation (On-demand)
```
All {TICKER}_latest_v4.json
+ All {TICKER}_latest_sentiment.json
+ All {TICKER}_news.json
→ generate_dashboard_3levels.py
→ dashboard_v4_3levels.html
→ ✓ Generated file (not committed)
```

### Serving (Real-time)
```
dashboard_v4_3levels.html → Browser (Static)
Streamlit apps → Port 8501-8502 (Interactive)
sentiment_server.py → Port 8000 (REST API)
```

---

**Generated:** 2025-12-30 | **Scope:** Complete prod/ architecture analysis
