# 🎯 Political Trading Analysis Pipeline

## Vue d'ensemble

Ce pipeline automatisé complètement intégré récupère les tickers des traders politiques (60 derniers jours) et exécute le processus d'analyse **complet** jusqu'à la création de la vue finale.

```mermaid
flowchart LR
    QQ["🌐 QuiverQuant<br/>API"] -->|"60 derniers jours"| EXTRACT["1️⃣ EXTRACT<br/>Tickers politiques"]
    EXTRACT -->|"30 tickers top"| CONFIG["2️⃣ CONFIG<br/>political_companies_config.py"]
    CONFIG -->|"Liste des tickers"| COLLECT["3️⃣ COLLECT<br/>News + Options"]
    COLLECT -->|"Données brutes"| ANALYZE["4️⃣ ANALYZE<br/>Sentiment + Insights"]
    ANALYZE -->|"Résultats"| VIEW["5️⃣ VIEW<br/>Dashboard + Synthèse"]
    VIEW -->|"Prêt pour viz"| DONE["✅ Terminé"]
    
    style QQ fill:#1e3a8a,color:#fff
    style EXTRACT fill:#065f46,color:#fff
    style CONFIG fill:#7c2d12,color:#fff
    style COLLECT fill:#4c1d95,color:#fff
    style ANALYZE fill:#831843,color:#fff
    style VIEW fill:#115e59,color:#fff
    style DONE fill:#166534,color:#fff
```

## 🚀 Démarrage rapide

### Option 1: Pipeline complet (RECOMMANDÉ)

```bash
cd c:\project\n8n-dashboard-v4
python prod/automation/run_political_pipeline.py --mode full
```

Cela va:
- ✅ Extraire les tickers politiques des 60 derniers jours
- ✅ Générer `political_companies_config.py`
- ✅ Collecter les nouvelles et options
- ✅ Analyser les sentiments
- ✅ Générer la synthèse et vue

### Option 2: Exécution notebook (développement)

```bash
# Lancer le notebook d'exploration
jupyter notebook notebooks/quiverquant_data_exploration.ipynb
```

## 📁 Fichiers générés

Après exécution du pipeline:

```
prod/
├── config/
│   └── political_companies_config.py  ← GÉNÉRÉ (30 tickers politiques)
└── automation/
    ├── run_political_pipeline.py       ← Orchestrateur principal
    └── political_trading_pipeline.py   ← Version longue (détails)

local_files/
├── political_trades/
│   ├── synthesis.json                  ← Synthèse avec stats
│   └── README.md                       ← Infos du run

data/
├── political_trades_TIMESTAMP.csv      ← Données brutes
├── congressional_cache.parquet         ← Cache (évite limite 1000)
├── news/                               ← Nouvelles collectées
└── options/                            ← Options collectées
```

## 🔧 Configuration

### Tokens requis

Le token QuiverQuant doit être défini dans `services/quiverquant/config.py`:

```python
QUIVERQUANT_TOKEN = "bibep"  # Votre token ici
```

### Ajuster les paramètres

Dans `run_political_pipeline.py`:

```python
# Nombre de tickers à analyser
tickers[:30]  # Changer la limite

# Fenêtre temporelle
cutoff_date = datetime.now() - timedelta(days=60)  # Changer à 30, 90, etc
```

## 📊 Exemple de résultat

```
PHASE 1: EXTRACTION DES TICKERS POLITIQUES
✅ 1250 trades extraits
✅ 87 tickers uniques
✅ Top 10 tickers identifiés

PHASE 2: GÉNÉRATION DE LA CONFIGURATION
✅ Config générée: 30 compagnies
  - TSLA: 145 trades
  - NVDA: 128 trades
  - META: 112 trades
  - MSFT: 98 trades
  - AMZN: 87 trades

PHASE 3: COLLECTE DES DONNÉES
✅ 15/15 tickers - nouvelles collectées
✅ 10/10 tickers - options collectées

PHASE 4: ANALYSE
✅ 10 tickers analysés

PHASE 5: GÉNÉRATION DE LA VUE
✅ Synthèse générée
✅ README créé
```

## 🔌 Intégration avec le système existant

### Utiliser le config manager

```python
from config.config_manager import use_political_mode

# Switcher au mode politique
manager = use_political_mode()

# Récupérer les compagnies
companies = manager.get_companies()
tickers = manager.get_tickers()

# Rechercher une compagnie
company = manager.get_company_by_ticker("TSLA")
print(company['political_trades_60d'])  # Nombre de trades politiques
```

### Changer de mode dynamiquement

```python
from config.config_manager import get_config_manager

manager = get_config_manager()

# Mode AI (défaut)
manager.switch_mode("ai")
print(manager.get_companies())  # ← AI_COMPANIES

# Mode politique
manager.switch_mode("political")
print(manager.get_companies())  # ← POLITICAL_COMPANIES

# Mode hybride
manager.switch_mode("hybrid")
print(manager.get_companies())  # ← AI + POLITICAL (déduplicé)
```

## 📈 Flux de données détaillé

### 1️⃣ EXTRACT (Phase 1)

**Input:** Token QuiverQuant  
**Process:**
- Appeler `congress_trading()`
- Appeler `senate_trading()`
- Appeler `house_trading()`
- Combiner et filtrer 60 jours
- Compter les tickers

**Output:** Liste de tickers, DataFrame avec dates

```python
tickers = ["TSLA", "NVDA", "META", ...]  # Triés par activité
df_60days = pd.DataFrame(1250 rows)
```

### 2️⃣ CONFIG (Phase 2)

**Input:** Tickers + Counts  
**Process:**
- Récupérer les noms d'entreprises
- Créer les search_terms
- Ajouter les counts politiques

**Output:** `political_companies_config.py`

```python
POLITICAL_COMPANIES = [
    {
        "ticker": "TSLA",
        "name": "Tesla Inc",
        "political_trades_60d": 145,
        "search_terms": ["TSLA", "Tesla Inc", "TSLA stock", ...]
    },
    ...
]
```

### 3️⃣ COLLECT (Phase 3)

**Input:** Tickers  
**Process:**
- Boucler sur chaque ticker
- Collecter les news (Google News, etc)
- Collecter les options (chain data)
- Sauvegarder les données

**Output:** Fichiers CSV/JSON dans `/data`

### 4️⃣ ANALYZE (Phase 4)

**Input:** Données collectées  
**Process:**
- Calculer sentiment (FinBERT)
- Extraire insights analysts
- Scorer les signaux

**Output:** Résultats d'analyse

### 5️⃣ VIEW (Phase 5)

**Input:** Tous les résultats précédents  
**Process:**
- Créer `synthesis.json`
- Générer `README.md`
- Préparer les données pour le dashboard

**Output:** Fichiers prêts pour Streamlit

## 🔄 Automatisation quotidienne

Pour exécuter automatiquement chaque jour:

```python
# Dans prod/automation/daily_automation.py

from automation.run_political_pipeline import run_full_pipeline
import schedule
import time

def job():
    print("📅 Exécution quotidienne du pipeline politique...")
    run_full_pipeline()

# Planifier pour 08:00 chaque jour
schedule.every().day.at("08:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

Ou avec cron (Linux/Mac):

```bash
0 8 * * * cd /path/to/project && python prod/automation/run_political_pipeline.py --mode full
```

## 🐛 Troubleshooting

### QuiverQuant token non valide

```
❌ Error: Invalid token
```

**Solution:** Vérifier `services/quiverquant/config.py` et remplacer le token

### Module non trouvé

```
⚠️ Modules de collecte non trouvés
```

**Solution:** Vérifier que les chemins sys.path sont corrects dans le script

### Limit 1000 atteint (Phase 1)

Le script retourne seulement 1000 résultats récents. C'est normal, c'est l'API QuiverQuant qui a cette limite.

**Solution:** Exécuter quotidiennement pour accumuler l'historique dans le cache

## 📚 Fichiers connexes

- `notebooks/quiverquant_data_exploration.ipynb` - Exploration interactive des données
- `docs/diagrams/political_trades_flow.md` - Diagramme Mermaid du flux
- `docs/QUIVERQUANT_API_REFERENCE.md` - Référence API complète
- `prod/config/companies_config.py` - Config AI (pour comparaison)

## 💡 Cas d'usage

### Cas 1: Découvrir les stocks que les politiciens achètent

```bash
python prod/automation/run_political_pipeline.py --mode full
# Vérifier political_companies_config.py pour voir le top 30
```

### Cas 2: Analyser un ticker spécifique

```python
from config.political_companies_config import POLITICAL_COMPANIES

# Trouver TSLA
for company in POLITICAL_COMPANIES:
    if company['ticker'] == 'TSLA':
        print(f"Trades politiques (60j): {company['political_trades_60d']}")
        break
```

### Cas 3: Combiner AI + Political trading

```python
from config.config_manager import use_hybrid_mode

manager = use_hybrid_mode()
all_companies = manager.get_companies()
# Maintenant vous avez AI_COMPANIES + POLITICAL_COMPANIES
```

## 📞 Support

Pour des questions:
1. Vérifier les logs dans `political_pipeline.log`
2. Consulter les erreurs de synthèse dans `local_files/political_trades/synthesis.json`
3. Réexécuter avec `--debug` (futur)

---

**Version:** 2.0  
**Dernière mise à jour:** 2026-01-02  
**Status:** ✅ Production Ready
