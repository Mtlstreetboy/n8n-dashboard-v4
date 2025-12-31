# 📁 Structure du Projet - n8n-local-stack

**Dernière mise à jour:** 31 Décembre 2025  
**État:** Réorganisé et optimisé ✅

---

## 🎯 Vue d'ensemble

Après nettoyage complet, le projet est désormais organisé et facile à naviguer.

**Avant:** 36 fichiers à la racine 😱  
**Après:** 5 fichiers essentiels à la racine 😍

---

## 📂 Structure Complète

```
c:\n8n-local-stack/
│
├── 📄 CONFIG & CORE
│   ├── .env                          ← Secrets & config locale
│   ├── .gitignore                    ← Git exclusions
│   ├── .github/                      ← GitHub workflows
│   ├── .venv/                        ← Python venv
│   ├── .vscode/                      ← VS Code config
│   ├── docker-compose.yml            ← Docker (SEUL)
│   ├── Dockerfile                    ← Image Docker
│   └── README.md                     ← Doc principale
│
├── 📚 docs/                          ← DOCUMENTATION
│   ├── README.md                     ← Start guide
│   ├── PROJECT_STRUCTURE.md          ← Ce fichier
│   ├── WELCOME.md
│   ├── QUICK_START_TOMORROW.md
│   ├── QUICK_REFERENCE.md
│   ├── CHECKLIST_TOMORROW.md
│   ├── STATUS_FINAL.md
│   ├── POLITICAL_TRADES_PLAN.md      ← Political data plan
│   ├── README_DOCUMENTATION.md       ← Vieux docs
│   ├── IMPLEMENTATION_GUIDE.md
│   │
│   ├── guides/                       ← GUIDES DÉTAILLÉS
│   │   ├── smart-money.md
│   │   ├── SMART_MONEY_PLAN.md
│   │   ├── SMART_MONEY_README.md
│   │   └── SMART_MONEY_SESSION_LOG.md
│   │
│   └── diagrams/                     ← DIAGRAMMES
│       ├── ARCHITECTURE_DIAGRAM.md
│       ├── ARCHITECTURE_DIAGRAMS.md
│       └── PIPELINE_DIAGRAM.mmd
│
├── 🏭 prod/                          ← CODE EN PRODUCTION ⚠️
│   ├── __init__.py
│   ├── dashboard_options.py
│   ├── dashboard_sentiment.py
│   ├── dashboard_timeline.py
│   ├── collect_news.py
│   ├── collect_options.py
│   ├── analysis/                     ← NEW - Analyseurs
│   │   ├── edgar_smart_money_analyzer.py
│   │   └── smart_money_analyzer.py
│   ├── config/                       ← NEW - Configuration
│   │   └── smart_money_config.py
│   └── ...
│
├── 🔧 services/                      ← LIBRARIES & SERVICES
│   ├── quiverquant/                  ← NEW - API Integration
│   │   ├── __init__.py
│   │   ├── config.py                 ← Credentials
│   │   ├── quiverquant_client.py    ← Client API
│   │   ├── collect_political_trades.py  ← Collector
│   │   ├── test_quiver_connection.py
│   │   └── README.md
│   └── ...
│
├── 📜 scripts/                       ← SCRIPTS D'EXÉCUTION
│   ├── tests/                        ← TESTS
│   │   ├── test_edgartools_connection.py
│   │   ├── test_real_apis.py
│   │   ├── test_political_apis.py
│   │   ├── test_political_sources.py
│   │   └── debug_form4_structure.py
│   ├── setup/                        ← SETUP & VALIDATION
│   │   └── validate_smart_money_setup.py
│   ├── daily_automation.py           ← Cron job
│   ├── collect_news.py
│   ├── collect_options.py
│   └── ...
│
├── 📊 data/                          ← DONNÉES CONTENEUR
│   ├── options_data/
│   ├── sentiment_analysis/
│   ├── smart_money/
│   └── ...
│
├── 📁 local_files/                   ← CACHE LOCAL
│   ├── smart_money/
│   │   └── political_trades_*.csv    ← QuiverQuant output
│   ├── collected_articles_100days.json
│   ├── companies_sentiment_summary.json
│   └── ...
│
├── 📔 notebooks/                     ← JUPYTER NOTEBOOKS
│   └── smart_money_testing.ipynb
│
├── 🗑️ _archive/                      ← FICHIERS ANCIENS
│   ├── docker-old/                   ← Vieilles versions Docker
│   │   ├── docker-compose.finbert.yml
│   │   └── docker-compose.finbert.gpu.yml
│   ├── analysis/                     ← Vieilles analyses
│   │   ├── PRODUCTION_ANALYSIS_DETAILED.md
│   │   └── PRODUCTION_ANALYSIS_SUMMARY.md
│   ├── AUDIT_*.md                    ← Vieux audits
│   ├── logs/
│   ├── scripts/
│   └── ... (ancien contenu)
│
└── workflows/                        ← N8N WORKFLOWS
    └── ...
```

---

## 🚀 Quick Start

### 1. Démarrer le stack
```bash
docker-compose up -d
```

### 2. Entrer dans le conteneur
```bash
docker exec -it n8n_data_architect bash
```

### 3. Exécuter scripts
```bash
# Collecter données politiques
python services/quiverquant/collect_political_trades.py

# Tester connexion API
python services/quiverquant/test_quiver_connection.py

# Exécuter tests
python scripts/tests/test_real_apis.py
```

---

## 📖 Documentation Clés

| Document | Chemin | Contenu |
|----------|--------|---------|
| **Quick Start** | [docs/QUICK_START_TOMORROW.md](QUICK_START_TOMORROW.md) | Démarrage rapide |
| **Smart Money** | [docs/guides/SMART_MONEY_README.md](guides/SMART_MONEY_README.md) | Smart Money Tracker |
| **Political Trades** | [docs/POLITICAL_TRADES_PLAN.md](POLITICAL_TRADES_PLAN.md) | Plan intégration political data |
| **API Reference** | [docs/QUIVERQUANT_API_REFERENCE.md](QUIVERQUANT_API_REFERENCE.md) | QuiverQuant API docs |
| **Architecture** | [docs/diagrams/ARCHITECTURE_DIAGRAM.md](diagrams/ARCHITECTURE_DIAGRAM.md) | Architecture système |

---

## 🔑 Credentials & Config

```
.env                        ← Token QuiverQuant, DB config, etc.
services/quiverquant/config.py  ← API credentials
prod/config/smart_money_config.py   ← Smart Money parameters
```

**Important:** Ne JAMAIS commit `.env` ou credentials!

---

## 📦 Composants Principaux

### Production (`prod/`)
- **Dashboards:** Options, Sentiment, Timeline
- **Collectors:** News, Options, Politique
- **Analyzers:** Smart Money (NEW)

### Services (`services/`)
- **QuiverQuant** (NEW): Alternative data API
  - Congressional trading
  - Insider trades
  - Institutional holdings (13F)

### Scripts (`scripts/`)
- **Tests:** API connections, data validation
- **Setup:** Environment validation
- **Automation:** Daily cron jobs

---

## 🧹 Nettoyage Effectué

**Supprimé:**
- ❌ AUDIT_PROD_ANALYSIS.md (ancien audit)
- ❌ AUDIT_PROD_COMPLET.json
- ❌ CLEANUP_PLAN.md
- ❌ DOCUMENTS_INDEX.md

**Archivé dans `_archive/`:**
- 📦 docker-compose.finbert.yml
- 📦 docker-compose.finbert.gpu.yml
- 📦 Vieux analyses

**Réorganisé:**
- 📚 17 fichiers docs → `docs/`
- 🧪 5 scripts tests → `scripts/tests/`
- 📖 3 guides → `docs/guides/`
- 📊 1 notebook → `notebooks/`

**Résultat:** 
- 36 → 5 fichiers à la racine ✅
- Structure claire et maintenable ✅
- Tous les fichiers tracés par git ✅

---

## 🎯 Prochaines Étapes

1. **Test QuiverQuant**
   ```bash
   python services/quiverquant/test_quiver_connection.py
   ```

2. **Collector Political Trades**
   ```bash
   python services/quiverquant/collect_political_trades.py
   ```

3. **Intégration Smart Money**
   - Mettre à jour `prod/analysis/edgar_smart_money_analyzer.py`
   - Ajouter données QuiverQuant aux signaux
   - Tester avec données réelles

4. **Validation Complète**
   ```bash
   python scripts/setup/validate_smart_money_setup.py
   ```

---

## 📞 Support

**Documentation:** Voir [docs/](.)  
**Scripts de test:** Voir [scripts/tests/](../scripts/tests/)  
**API Integration:** Voir [services/quiverquant/](../services/quiverquant/)

---

*Structure finalisée le 31 Décembre 2025*  
*Tous les changements sont versionnés dans git ✅*
