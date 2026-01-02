# 📁 QuiverQuant Documentation

Ce dossier contient toute la documentation relative à l'intégration de **QuiverQuant** dans le système d'analyse.

## 📚 Fichiers disponibles

### 🎯 Pipeline & Orchestration

- **[POLITICAL_TRADING_PIPELINE.md](POLITICAL_TRADING_PIPELINE.md)**
  - Guide complet du pipeline automatisé
  - De l'extraction à la création de la vue
  - Scripts: `run_political_pipeline.py`, `quick_start_political.py`
  - **Status:** ✅ Production Ready

### 📊 Diagrammes & Architecture

- **[political_trades_flow.md](political_trades_flow.md)**
  - Diagrammes Mermaid du flux complet (8 étapes)
  - Flux détaillé par fonction
  - Structure des données (ERD)
  - Timeline d'exécution quotidienne
  - **Visualisation:** Ouvrir dans un viewer Mermaid

### 🔌 Intégration

- **[INTEGRATION_POLITICAL_TRADES.md](INTEGRATION_POLITICAL_TRADES.md)**
  - Plan d'intégration avec le système existant
  - Connexion avec `daily_automation.py`
  - Intégration dans le dashboard V4
  - Calcul du "Super Score" combiné

### 📋 Planning & Stratégie

- **[POLITICAL_TRADES_PLAN.md](POLITICAL_TRADES_PLAN.md)**
  - Plan initial de collecte des données politiques
  - Stratégie d'extraction et analyse
  - Historique des décisions

### 📖 Référence API

- **[QUIVERQUANT_API_REFERENCE.md](QUIVERQUANT_API_REFERENCE.md)**
  - Documentation complète de l'API QuiverQuant
  - Endpoints disponibles
  - Exemples d'utilisation
  - Limites et contraintes (1000 résultats)

## 🚀 Quick Start

```bash
# Pipeline complet
cd c:\project\n8n-dashboard-v4
python prod/automation/run_political_pipeline.py --mode full

# Interface interactive
python quick_start_political.py
```

## 📂 Structure du code

```
services/quiverquant/
├── quiverquant_client.py       # Client API
├── config.py                   # Token configuration
├── collect_political_trades.py # Collecteur principal
└── README.md

prod/automation/
├── run_political_pipeline.py   # Orchestrateur principal ⭐
├── political_trading_pipeline.py
└── daily_automation.py         # Intégration future

prod/config/
├── political_companies_config.py   # Généré automatiquement
└── config_manager.py               # Gestionnaire de mode (AI/Political/Hybrid)

notebooks/
└── quiverquant_data_exploration.ipynb  # Exploration interactive
```

## 🔑 Configuration requise

### Token QuiverQuant

Fichier: `services/quiverquant/config.py`

```python
QUIVERQUANT_TOKEN = "bibep"  # Votre token ici
```

### Dépendances Python

```bash
pip install pandas numpy requests
```

## 📊 Flux de données

```
QuiverQuant API (60j)
    ↓
Extraction des tickers (Top 30-50)
    ↓
Génération political_companies_config.py
    ↓
Collecte nouvelles + options
    ↓
Analyse sentiment + insights
    ↓
Génération de la vue (Dashboard)
```

## 🎯 Outputs générés

### Fichiers de configuration

- `prod/config/political_companies_config.py` - Liste des 30 tickers politiques

### Données collectées

- `local_files/political_trades/synthesis.json` - Synthèse complète
- `local_files/political_trades/README.md` - Info du run
- `data/congressional_cache.parquet` - Cache historique
- `data/news/` - Nouvelles collectées
- `data/options/` - Options collectées

### Logs

- `political_pipeline.log` - Logs d'exécution

## 🔄 Automatisation

Le pipeline peut être exécuté quotidiennement via:

1. **Cron (Linux/Mac)**
   ```bash
   0 8 * * * cd /path/to/project && python prod/automation/run_political_pipeline.py --mode full
   ```

2. **Task Scheduler (Windows)**
   - Créer une tâche planifiée
   - Action: `python prod/automation/run_political_pipeline.py --mode full`
   - Trigger: Daily à 08:00

3. **daily_automation.py** (Intégration future)
   ```python
   from automation.run_political_pipeline import run_full_pipeline
   run_full_pipeline()
   ```

## 📈 Cas d'usage

### 1. Découvrir les stocks que les politiciens achètent

```bash
python prod/automation/run_political_pipeline.py --mode full
# Consulter: prod/config/political_companies_config.py
```

### 2. Analyser un ticker spécifique

```python
from config.political_companies_config import POLITICAL_COMPANIES

for company in POLITICAL_COMPANIES:
    if company['ticker'] == 'TSLA':
        print(f"Trades politiques (60j): {company['political_trades_60d']}")
```

### 3. Mode hybride (AI + Political)

```python
from config.config_manager import use_hybrid_mode

manager = use_hybrid_mode()
all_companies = manager.get_companies()
# Combine AI_COMPANIES + POLITICAL_COMPANIES
```

## 🐛 Troubleshooting

### Token invalide
```
❌ Error: Invalid token
```
**Solution:** Vérifier `services/quiverquant/config.py`

### Limite 1000 résultats
L'API QuiverQuant retourne max 1000 résultats récents. C'est normal.

**Solution:** Exécuter quotidiennement pour accumuler l'historique dans le cache parquet.

### Module non trouvé
```
⚠️ Modules de collecte non trouvés
```
**Solution:** Vérifier les chemins `sys.path` dans les scripts

## 📞 Support

1. Consulter les logs: `political_pipeline.log`
2. Vérifier la synthèse: `local_files/political_trades/synthesis.json`
3. Explorer dans Jupyter: `notebooks/quiverquant_data_exploration.ipynb`

## 🔗 Liens utiles

- [QuiverQuant Website](https://www.quiverquant.com/)
- [API Documentation](https://api.quiverquant.com/docs)
- Token: Fourni par QuiverQuant (plan payant)

## 📝 Notes importantes

- **Délai de reporting:** Les trades politiques sont reportés avec 5-45 jours de délai (légal)
- **Limite API:** 1000 résultats max par requête
- **Cache intelligent:** Le système accumule progressivement l'historique
- **Déduplication:** Évite les doublons automatiquement

---

**Version:** 2.0  
**Dernière mise à jour:** 2026-01-02  
**Status:** ✅ Documentation complète et système opérationnel
