<!-- Copilot / AI agent instructions for contributors and automated agents -->
# Copilot Instructions

**Purpose**: Guidance for AI assistants working on this n8n-based AI data pipeline & sentiment analysis system. Preserve production behavior unless explicitly approved.

## 🎯 System Overview

This is a **Docker-containerized n8n automation stack** for AI-powered financial sentiment analysis with local LLM processing (Ollama). The system collects multi-source data (news, options, Reddit WSB), analyzes it using dual-brain LLM architecture, and generates interactive dashboards.

**Core Stack**: n8n + Ollama (Qwen 2.5 7B + Llama 3.1 8B) + Python data pipelines + Streamlit dashboards

## 🔐 Key Principles

- **Preserve Production**: Never modify `prod/` files without approval. Production dashboards & collectors are actively deployed.
- **Test First**: Run `pytest prod/tests/` or task-specific tests before changes to analysis/dashboard logic.
- **Encoding Safety**: NEVER use PowerShell piping (`Get-Content | docker exec`) - it corrupts UTF-8 emojis (→ `??`). Always use `docker cp`.
- **Path Resolution**: Use `prod/utils/path_utils.py` for Docker/local path handling - never hardcode paths.

## 📁 Architecture & Project Structure

```
prod/                           # Production code (modular structure)
├── pipelines/                  # Data processing workflows
│   ├── collection/             # News, options, financials collectors
│   ├── analysis/               # Sentiment engines (V4 dual-brain LLM)
│   └── automation/             # Orchestration (daily_automation.py)
├── dashboards/                 # Visualization layers
│   └── generators/             # Streamlit apps + HTML generators
├── collectors/                 # Specialized scrapers (WSB, Reddit)
├── config/                     # companies_config.py (15 AI tickers)
├── utils/                      # path_utils.py, shared utilities
└── tests/                      # unit/ + integration/ test suites

local_files/                    # Local dev data (maps to /data/ in container)
├── sentiment_analysis/         # LLM analysis outputs (*_latest_v4.json)
├── options_data/               # Options CSVs + sentiment JSONs
├── companies/                  # News JSONs (30-day rolling)
└── wsb_data/                   # Reddit WSB scrapes & analysis

docker-compose.yml              # n8n + Ollama stack definition
Dockerfile                      # Custom n8n image with Python + ML libs
```

## 🔑 Critical Files (Do NOT Delete/Break)

| File | Role | Dependencies |
|------|------|--------------|
| `prod/config/companies_config.py` | Master config (15 tickers: NVDA, PLTR, etc.) | None |
| `prod/pipelines/analysis/advanced_sentiment_engine_v4.py` | **Core AI Engine** - Dual-brain LLM (1500 LOC) | Ollama, FinBERT |
| `prod/pipelines/automation/daily_automation.py` | Orchestrator - runs full pipeline | All collectors + analyzers |
| `prod/collectors/wsb_sentiment_collector.py` | Reddit WSB scraper (multi-source fallback) | Pushshift/RSS APIs |

## 🐳 Docker vs Local Environments

**Path Resolution Pattern** (used everywhere):
```python
# ✅ CORRECT - Use path_utils.py
from prod.utils.path_utils import get_data_root, resolve_data_path
data_root = get_data_root()  # Returns /data/ in Docker, ./local_files/ locally
sentiment_file = resolve_data_path('sentiment_analysis/NVDA_latest_v4.json')

# ❌ WRONG - Hardcoded paths
DATA_DIR = '/data/sentiment_analysis'  # Breaks in local dev
```

**Container Paths**:
- Scripts: `/data/scripts` → mounts `./prod/`
- Data files: `/data/` → mounts `./local_files/`
- Ollama API: `http://host.docker.internal:11434` (from n8n container)

**Host Paths** (Windows):
- Repository: `c:\n8n-local-stack`
- Data: `c:\n8n-local-stack\local_files\`

## 🚀 Essential Commands & Workflows

### Starting the Stack
```powershell
docker-compose up -d              # Start n8n + Ollama
docker logs -f n8n_data_architect # Watch logs
docker exec -it n8n_data_architect sh  # Enter container shell
```

**Access Points**:
- n8n: http://localhost:5678 (admin / supersecurepassword)
- Streamlit dashboards: ports 8501-8503
- Ollama API: http://localhost:11434

### Running the Pipeline

**Via VS Code Tasks** (preferred):
- `🚀 Automation Quotidienne Complète` - Full daily pipeline
- `📰 Collecter Options Data` - Options only
- `📈 Analyser Toutes les Compagnies` - Sentiment analysis only
- `📊 Dashboard Sentiment Multi-Dimensionnel` - Launch Streamlit on 8502

**Manual Execution** (in container):
```bash
docker exec n8n_data_architect python3 /data/scripts/pipelines/automation/daily_automation.py
```

### Data Management

**Copy data from container** (encoding-safe):
```powershell
docker cp n8n_data_architect:/data/options_data ./local_files/options_data
docker cp n8n_data_architect:/data/sentiment_analysis ./local_files/sentiment_analysis
```

**NEVER use PowerShell piping** (corrupts UTF-8):
```powershell
# ❌ WRONG - Breaks emojis
Get-Content file.json | docker exec -i n8n_data_architect sh -c "cat > /data/file.json"

# ✅ CORRECT - Use docker cp
docker cp file.json n8n_data_architect:/data/file.json
```

### Local Streamlit Development

```powershell
python -m venv .venv_dashboard
.\.venv_dashboard\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONUTF8='1'; chcp 65001 | Out-Null  # Force UTF-8 encoding
streamlit run prod\dashboards\generators\dashboard_benchmark_v2.py --server.port 8503
```

## 🧠 Dual-Brain LLM Architecture (V4 Engine)

**Core Pattern** (`advanced_sentiment_engine_v4.py`):
```python
MODEL_LOGIC = "qwen2.5:7b"      # System 2: JSON, math, structured reasoning
MODEL_NARRATIVE = "llama3.1:8b" # System 1: Text interpretation, nuance

# Ollama API fallback chain
_get_ollama_api_urls() → [
    'http://host.docker.internal:11434/api/generate',  # Docker Desktop host
    'http://localhost:11434/api/generate'              # Container-local Ollama
]
```

**Analysis Flow**:
1. **Collect** - News (NewsAPI) + Options (yfinance) + WSB (Reddit RSS fallback)
2. **Analyze** - Dual-brain LLM generates sentiment scores (-1 to +1) + confidence (0-1)
3. **Integrate** - Combines news sentiment + options flow (put/call ratio) + analyst insights
4. **Output** - `{ticker}_latest_v4.json` with 50+ metrics

## 📊 Data Formats & Contracts

**Sentiment Output** (`*_latest_v4.json`):
```json
{
  "ticker": "NVDA",
  "timestamp": "2025-12-30T10:15:00Z",
  "sentiment_score": 0.72,        // -1 (bearish) to +1 (bullish)
  "confidence": 0.85,             // 0 to 1
  "news_sentiment": 0.68,
  "options_flow_signal": 0.15,    // Derived from put/call ratio
  "composite_score": 0.74,
  "catalyst_detected": true,
  "volatility_regime": "elevated",
  "articles_analyzed": 12,
  "llm_narrative": "Strong bullish momentum..."
}
```

**Options Data** (CSV columns):
- `strike`, `lastPrice`, `bid`, `ask`, `volume`, `openInterest`
- `impliedVolatility`, `delta`, `gamma`, `theta`, `vega` (Greeks)

## 🧪 Testing Strategy

**Before Modifying Analyzers**:
```bash
# In container
docker exec n8n_data_architect pytest prod/tests/unit/test_sentiment_engine.py -v
docker exec n8n_data_architect pytest prod/tests/integration/ -v
```

**Dashboard Testing** (use real data):
```bash
# Copy production data locally first
docker cp n8n_data_architect:/data/sentiment_analysis ./local_files/sentiment_analysis
python prod/dashboards/generators/dashboard_benchmark_v2.py  # Test locally
```

**Validation Checklist**:
1. ✅ Path resolution works (Docker + local)
2. ✅ No hardcoded `/data/` paths
3. ✅ UTF-8 encoding preserved (emojis intact)
4. ✅ LLM fallback chain handles Ollama unavailable
5. ✅ Output JSON schema matches downstream consumers

## 🐛 Common Issues & Fixes

### Issue: `FileNotFoundError: /data/options_data`
**Fix**: Use `path_utils.get_data_root()` instead of hardcoded paths.

### Issue: Emojis become `??` in logs/dashboards
**Fix**: Stop using PowerShell piping. Use `docker cp` or edit files in UTF-8 aware editor.
```powershell
# Re-encode all Python files (no logic change)
Get-ChildItem -Path .\prod -Filter *.py -Recurse | ForEach-Object {
    (Get-Content -Raw $_.FullName) | Set-Content -LiteralPath $_.FullName -Encoding UTF8
}
```

### Issue: Ollama API timeout
**Fix**: Engine already has fallback chain. Check if Ollama container is running:
```bash
docker ps | grep ollama
docker exec -it ollama_local_ai ollama list  # Check loaded models
```

### Issue: Dashboard data stale
**Fix**: Run collectors first, then regenerate dashboard:
```bash
docker exec n8n_data_architect python3 /data/scripts/pipelines/collection/collect_options.py
docker exec n8n_data_architect python3 /data/scripts/pipelines/automation/daily_automation.py
```

## 📝 Development Conventions

### Import Patterns (prod/ modules)
```python
# ✅ Relative imports (within pipelines/)
from .finbert_analyzer import FinBERTAnalyzer
from .analyst_insights_integration import AnalystInsightsIntegration

# ✅ Absolute from prod root
from prod.config.companies_config import AI_COMPANIES
from prod.utils.path_utils import resolve_data_path
```

### Adding New Tickers
1. Edit `prod/config/companies_config.py` → add to `AI_COMPANIES` list
2. Run full pipeline to generate data:
   ```bash
   docker exec n8n_data_architect python3 /data/scripts/pipelines/automation/daily_automation.py
   ```
3. Dashboard auto-detects new tickers via config

### WSB Collector Multi-Source Strategy
**Fallback chain** (`wsb_sentiment_collector.py`):
1. **Pushshift API** (primary, rate-limited)
2. **RSS Feed** (`reddit.com/r/wallstreetbets/.rss`, no auth)
3. **Thread Scraper** (for specific high-value threads)

Pattern: Always implement graceful fallback for external APIs.

## 📚 Key Documentation Files

- `QUICK_REFERENCE.md` - 5-min architecture overview ⭐ START HERE
- `ARCHITECTURE_DIAGRAMS.md` - Complete data flow diagrams
- `AUDIT_PROD_ANALYSIS.md` - Deep codebase audit (47 files analyzed)
- `prod/README_NEW_STRUCTURE.md` - Modular structure migration guide
- `docs/RUN_OPTIONS_LOCALLY.md` - Local dev setup guide

## ✅ Agent Pre-Flight Checklist

Before making code changes:
1. [ ] Does this modify production files (`prod/pipelines`, `prod/dashboards`)? → Requires approval
2. [ ] Have I tested in both Docker AND local environments?
3. [ ] Are paths resolved via `path_utils.py` (not hardcoded)?
4. [ ] Is UTF-8 encoding preserved (no PowerShell piping)?
5. [ ] Do existing tests still pass?
6. [ ] Have I documented any new conventions or breaking changes?

---

**Last Updated**: 2025-01-20  
**Reviewer**: Senior Data Architect / Repository Owner  
**Version**: 2.0 (expanded from initial version)
