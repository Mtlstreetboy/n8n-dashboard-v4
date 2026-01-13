# 📁 Nouvelle Structure du Projet

**Date de réorganisation:** 2026-01-10  
**Basé sur:** Audit d'architecture automatisé

## 🎯 Structure Organisée

```
prod/
├── pipelines/              # 🔄 TRAITEMENT DE DONNÉES
│   ├── collection/         # Collecte (news, options, financials)
│   ├── analysis/           # Analyse sentiment (V4 engine, FinBERT)
│   └── automation/         # Orchestration (daily_automation.py)
│
├── dashboards/             # 📊 INTERFACES UTILISATEUR
│   ├── generators/         # Scripts de génération HTML
│   └── html/              # Fichiers HTML générés (non-versionnés)
│
├── services/              # 🔧 SERVICES BACKEND
│   └── (futurs services HTTP, monitoring)
│
├── config/                # ⚙️ CONFIGURATION
│   └── companies_config.py # Configuration des 15 tickers
│
├── utils/                 # 🛠️ UTILITAIRES PARTAGÉS
│   └── path_utils.py      # Résolution chemins Docker/local
│
└── tests/                 # ✅ TESTS ORGANISÉS
    ├── unit/              # Tests unitaires
    └── integration/       # Tests d'intégration
```

## 🔄 Changements Principaux

### Avant → Après

| Ancien Chemin | Nouveau Chemin |
|---------------|----------------|
| `prod/analysis/` | `prod/pipelines/analysis/` |
| `prod/collection/` | `prod/pipelines/collection/` |
| `prod/automation/` | `prod/pipelines/automation/` |
| `prod/dashboard/` | `prod/dashboards/generators/` |
| `prod/utils/` (services) | `prod/services/` |

### Nouveaux Utilitaires

- **`prod/utils/path_utils.py`** : Résolution automatique des chemins Docker vs local
- **`build/`** : Dossier pour artefacts générés
- **`archive/`** : Code historique isolé

## 🚀 Utilisation

### Imports Mis à Jour

```python
# Ancien
from analysis.advanced_sentiment_engine_v4 import AdvancedSentimentEngineV4
from collection.collect_options import collect_options

# Nouveau
from pipelines.analysis.advanced_sentiment_engine_v4 import AdvancedSentimentEngineV4
from pipelines.collection.collect_options import collect_options
```

### Résolution de Chemins

```python
# Utiliser le nouvel utilitaire
from utils.path_utils import get_data_root, resolve_data_path

# Fonctionne automatiquement en Docker ET local
data_root = get_data_root()
sentiment_file = resolve_data_path('sentiment_analysis/NVDA_latest_v4.json')
```

## 📋 Fichiers Critiques (Inchangés)

Ces fichiers restent les mêmes, juste déplacés :

1. **`pipelines/analysis/advanced_sentiment_engine_v4.py`** - Moteur dual-brain
2. **`pipelines/automation/daily_automation.py`** - Orchestrateur
3. **`pipelines/collection/collect_options.py`** - Collecteur options
4. **`config/companies_config.py`** - Configuration des 15 tickers
5. **`dashboards/generators/generate_consolidated_data.py`** - Générateur dashboard

## ✅ Bénéfices

- **Navigation claire** : Chaque module a une responsabilité définie
- **Scalabilité** : Facile d'ajouter de nouveaux modules
- **Maintenance** : Structure logique pour nouveaux développeurs
- **Compatibilité** : Fonctionne toujours en Docker ET local
- **Archive propre** : Code historique isolé

## 🔧 Prochaines Étapes

1. Tester que tous les imports fonctionnent
2. Vérifier que daily_automation.py s'exécute
3. Générer un dashboard pour valider
4. Mettre à jour la documentation si nécessaire

---

**Note:** Tous les fichiers de données (`local_files/`) et la configuration Docker restent inchangés.