# 📋 PLAN DE NETTOYAGE prod/ - À CONSERVER

## ✅ CONSERVER (Pipeline Split)

### 📁 `prod/analysis/` - MOTEUR SENTIMENT
- **advanced_sentiment_engine_v4.py** ✅ ESSENTIEL (1380 lignes - cœur de l'analyse 6D)
- **analyze_all_sentiment.py** ✅ ESSENTIEL (orchestrateur - lance l'analyse pour 15 tickers)
- **finbert_analyzer.py** ✅ CONSERVER (module FinBERT utilisé par v4)
- **analyst_insights_integration.py** ✅ CONSERVER (6ème dimension)
- **contextual_sentiment_analyzer.py** ✅ CONSERVER (évite contamination cross-ticker)
- **__init__.py** ✅ CONSERVER (imports)

### 📁 `prod/collection/` - COLLECTE DONNÉES
- **batch_loader_v2.py** ✅ ESSENTIEL (collecte news Google News API)
- **collect_options.py** ✅ ESSENTIEL (collecte options Yahoo Finance)
- **collect_companies.py** ❌ ARCHIVER (non utilisé par pipeline)
- **collect_options_worker.py** ❌ ARCHIVER (non appelé)
- **__init__.py** ✅ CONSERVER

### 📁 `prod/automation/` - ORCHESTRATION
- **daily_automation.py** ✅ CONSERVER (daily_automation.py - lance le pipeline 4 étapes)
- **__init__.py** ✅ CONSERVER

### 📁 `prod/config/` - CONFIGURATION
- **companies_config.py** ✅ CONSERVER (liste des 15 tickers)
- **__init__.py** ✅ CONSERVER

### 📁 `prod/dashboard/` - DASHBOARD
- ❌ **dashboard_companies.py** - ARCHIVER (legacy)
- ❌ **dashboard_options.py** - ARCHIVER (legacy)
- ❌ **dashboard_timeline.py** - ARCHIVER (legacy)
- **__init__.py** ✅ CONSERVER

### 📁 `prod/` (root)
- **dashboard_v4_split.html** ✅ ESSENTIEL (le dashboard final)

---

## ❌ À ARCHIVER

### Alternatives/Legacy d'analyzers
- sentiment_analysis_v*.py (toutes versions < v4)
- comparative_sentiment_analysis.py
- aggregate_companies.py
- sentiment_trend_tracker.py

### Dashboards alternatifs
- dashboard_v4_buttons.html
- dashboard_v4_3levels.html
- dashboard_v4_tabs.html

### Utilitaires non-essentiels
- Tous les `monitor_*.py` (monitoring legacy)
- `sentiment_server.py` (serveur legacy?)
- `populate_fetched_dates.py` (data prep legacy?)
- `check_llm_status.py` (debug)

### Scripts de collecte legacy
- `collect_companies.py` (si pas utilisé par v4)
- `collect_options_worker.py` (si duplicate de collect_options.py)

### Dashboard legacy
- `dashboard_companies.py`
- `dashboard_options.py`
- `dashboard_timeline.py`

---

---

## 📊 RÉSUMÉ FINAL - À CONSERVER vs À ARCHIVER

### ✅ À CONSERVER (15 fichiers essentiels)

```
prod/
├── dashboard_v4_split.html                          [ESSENTIEL]
├── analysis/
│   ├── __init__.py
│   ├── advanced_sentiment_engine_v4.py              [ESSENTIEL]
│   ├── analyze_all_sentiment.py                     [ESSENTIEL]
│   ├── finbert_analyzer.py
│   ├── analyst_insights_integration.py
│   └── contextual_sentiment_analyzer.py
├── collection/
│   ├── __init__.py
│   ├── batch_loader_v2.py                           [ESSENTIEL]
│   └── collect_options.py                           [ESSENTIEL]
├── automation/
│   ├── __init__.py
│   └── daily_automation.py
└── config/
    ├── __init__.py
    └── companies_config.py
```

### ❌ À ARCHIVER (11+ fichiers)

**Collection (legacy):**
- collect_companies.py
- collect_options_worker.py

**Dashboard (legacy):**
- dashboard_companies.py
- dashboard_options.py
- dashboard_timeline.py

**Utils (all legacy):**
- sentiment_server.py
- monitor_batch_v2.py
- populate_fetched_dates.py
- check_llm_status.py

**Empty/Unused:**
- prod/_archive/ (dossier vide)
- prod/logs/ (logs vides)

---

## 🎯 PIPELINE RÉEL (Daily Automation)

```
collect_options.py ──────┐
                         ├──► advanced_sentiment_engine_v4.py ─┐
batch_loader_v2.py ──────┤                                     ├──► analyze_all_sentiment.py
                         └──► companies_config.py ─────────────┘
                                    │
                                    └──► {TICKER}_latest_v4.json
                                             │
                                             └──► EMBEDDED_DATA in split.html
                                                   │
                                                   └──► dashboard_v4_split.html ✅
```

---

## ❓ QUESTIONS RÉSOLUES

✅ **collect_companies.py** - NON UTILISÉ - ARCHIVER  
✅ **collect_options_worker.py** - NON UTILISÉ - ARCHIVER  
✅ **Dashboard scripts** - LEGACY - ARCHIVER  
✅ **Utils scripts** - LEGACY - ARCHIVER  

**AUCUNE AMBIGUÏTÉ - PRÊT À NETTOYER !**

