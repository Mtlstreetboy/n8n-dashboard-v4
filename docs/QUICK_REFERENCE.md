# 📌 QUICK REFERENCE - Audit prod/ en 5 minutes

**🎯 L'ESSENTIEL A RETENIR**

---

## 1️⃣ Architecture Actuelle

```
DAILY AUTOMATION (daily_automation.py)
    ↓
    ├─ Collect News (scripts/ dans container)
    ├─ Collect Options (collect_options.py) → CSV + JSON
    ├─ Analyze (advanced_sentiment_engine_v4.py) → _latest_v4.json
    └─ Generate Dashboard (generate_dashboard_3levels.py) → HTML SPA
    
Output: dashboard_v4_3levels.html (dans prod/dashboard/)
```

## 2️⃣ Les 4 Fichiers CRITIQUES (Ne jamais perdre)

| Fichier | Rôle | Dépendances |
|---------|------|------------|
| `config/companies_config.py` | Config master (15 tickers) | Aucune |
| `analysis/advanced_sentiment_engine_v4.py` | Dual-brain LLM engine | Ollama, FinBERT |
| `automation/daily_automation.py` | Orchestrator | Tous les autres |
| `dashboard/generate_dashboard_3levels.py` | Dashboard generator | Données locales |

## 3️⃣ Data Locations (Docker vs Local)

### 🐳 Docker Container
```
/data/sentiment_analysis/    ← Sentiment outputs
/data/options_data/          ← Options CSVs
/data/files/companies/       ← News JSON
```

### 💻 Windows Local
```
local_files/sentiment_analysis/
local_files/options_data/
local_files/companies/
```

## 4️⃣ File Status Summary

| Catégorie | Count | Status |
|-----------|-------|--------|
| Active (Production) | 25 | ✅ En utilisation |
| Supporting | 10 | ✅ Nécessaire |
| Historical Archive | 15 | ⚠️ À isoler |
| Generated/Cache | 7 | 🔄 Auto-nettoyable |

## 5️⃣ Top 10 Files to Know

### Production Tier 1 (Ne jamais supprimer)
1. `config/companies_config.py` - Master config
2. `analysis/advanced_sentiment_engine_v4.py` - Core AI engine
3. `automation/daily_automation.py` - Orchestrator
4. `collection/collect_options.py` - Data source (options)
5. `dashboard/generate_dashboard_3levels.py` - Dashboard builder

### Supporting
6. `analysis/finbert_analyzer.py` - Fallback sentiment
7. `analysis/analyst_insights_integration.py` - Analyst scores
8. `collection/batch_loader_v2.py` - Batch processing
9. `dashboard/dashboard_options.py` - Streamlit UI
10. `utils/sentiment_server.py` - HTTP API

## 6️⃣ Problèmes Identifiés

❌ **Archive mélangée** → Solution: déplacer `_archive/cleanup_2025/` vers `/archive/`  
❌ **Structure plate** → Solution: créer `pipelines/`, `dashboards/`, `services/`  
❌ **Imports compliqués** → Solution: consolider dans `utils/`  
❌ **Générateurs vieux** → Solution: supprimer les versions obsolètes  
❌ **Paths hardcodés** → Solution: centraliser path resolution  

## 7️⃣ Solutions Rapides (Si temps limité)

### Top 1 (5 min)
```powershell
mkdir archive
mv prod/_archive/cleanup_2025/* archive/
```
→ Archive immédiatement isolée ✅

### Top 2 (30 min)
```powershell
mkdir prod/pipelines
mkdir prod/dashboards/generators
# Créer la structure (sans mover les fichiers)
```
→ Structure préparée, prêt pour migration ✅

### Top 3 (1h)
```python
# Créer prod/utils/path_utils.py
def get_data_root():
    if Path('/data/scripts').exists():
        return Path('/data')
    return Path(__file__).parent.parent.parent / 'local_files'
```
→ DRY principle appliqué ✅

## 8️⃣ Testing Checklist

```powershell
# Test 1: Config loads
python -c "from config.companies_config import get_all_companies; print(len(get_all_companies()))"
# Expected: 15

# Test 2: V4 Engine imports
python -c "from analysis.advanced_sentiment_engine_v4 import AdvancedSentimentEngineV4; print('OK')"

# Test 3: Dashboard generates
cd prod/dashboard && python generate_dashboard_3levels.py
# Expected: dashboard_v4_3levels.html created

# Test 4: One ticker analysis
python prod/analysis/advanced_sentiment_engine_v4.py NVDA
# Expected: local_files/sentiment_analysis/NVDA_latest_v4.json
```

## 9️⃣ Path Resolution Logic (Important!)

Tous les scripts DOIVENT supporter Docker ET local:

```python
# Pattern standard dans tout le code:
if os.path.exists('/data/scripts'):
    # DOCKER
    DATA_DIR = '/data'
else:
    # LOCAL
    DATA_DIR = Path(__file__).parent.parent.parent / 'local_files'
```

## 🔟 When to Use What

| Besoin | Fichier |
|--------|---------|
| Ajouter un ticker | `config/companies_config.py` |
| Améliorer sentiment | `analysis/advanced_sentiment_engine_v4.py` |
| Changer job quotidien | `automation/daily_automation.py` |
| Ajouter métrique options | `collection/collect_options.py` |
| Modifier dashboard | `dashboard/generate_dashboard_3levels.py` |
| Debugger en local | Copier data depuis Docker avec `docker cp` |

---

## 📚 Documentation Complète

1. **AUDIT_PROD_COMPLET.json** (280 KB)
   - Inventaire détaillé de TOUS les fichiers
   - Analyse de dépendances complète
   - Structure proposée en détail

2. **AUDIT_PROD_ANALYSIS.md**
   - Vue d'ensemble lisible
   - Diagrams textuels
   - Checklist validation

3. **ARCHITECTURE_DIAGRAMS.md**
   - Diagrammes ASCII détaillés
   - Data flow complet
   - Dépendances visuelles

4. **IMPLEMENTATION_GUIDE.md**
   - Plan phase-by-phase
   - Scripts d'exécution
   - Validation tests

5. **QUICK_REFERENCE.md** ← Vous êtes ici
   - Synthèse rapide
   - Points clés
   - Quick links

---

## 🎯 Prochaines Étapes

### Si vous avez 5 min
→ Lire cette page (QUICK_REFERENCE)

### Si vous avez 30 min
→ Lire AUDIT_PROD_ANALYSIS.md + ARCHITECTURE_DIAGRAMS.md

### Si vous avez 2 heures
→ Lire tous les documents + commencer Phase 1 (archive isolation)

### Si vous avez 1-2 semaines
→ Exécuter plan complet (IMPLEMENTATION_GUIDE.md)

---

**Generated:** 2025-12-30  
**Scope:** Production directory analysis & recommendations  
**Status:** ✅ Complete & ready for implementation

Pour questions détaillées → Voir document JSON complet
