# Smart Money Tracker - Session du 30 Décembre 2025

## 📋 Résumé Exécutif

**Objectif:** Créer un système robuste de "Smart Money" tracking avec vraies connexions API (SEC EDGAR + données politiques)

**Status:** ✅ 70% Complété
- ✅ SEC EDGAR (Form 4) - FONCTIONNEL
- ⚠️ Données Politiques - À INVESTIGUER
- ✅ Architecture notebook - PRÊTE

---

## ✅ Ce qui fonctionne

### 1. SEC EDGAR Form 4 (Insider Trades)

**Module:** `prod/analysis/edgar_smart_money_analyzer.py`

**Résultats en production:**
```
✅ 119 transactions collectées pour NVDA
✅ 10 insiders uniques identifiés
✅ $304M en volume de transactions
✅ Parsing XML perfectionné via edgartools.to_dataframe()
```

**Tickers testés avec succès:**
- NVDA (NVIDIA)
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- TSLA (Tesla)

**Données retournées par transaction:**
```python
- ticker: Symbole du titre
- filing_date: Date du dépôt SEC
- transaction_date: Date de la transaction
- insider_name: Nom de l'initié
- role: Position (Director, Officer, etc.)
- transaction_code: Code SEC (P=Purchase, S=Sale, etc.)
- shares: Nombre d'actions
- price_per_share: Prix unitaire
- transaction_value: Valeur totale
- type: BUY / SELL / OTHER
```

**Clé du succès:**
- Utilise edgartools 5.6.4 (moderne, maintenu)
- User-Agent SEC correct: "n8n-local-stack research@mtlstreetboy.com"
- Rate limiting automatique (10 req/sec)
- Caching intelligent des données

### 2. Notebook Fonctionnel

**Fichier:** `smart_money_testing.ipynb`

**Cellules opérationnelles:**
1. ✅ Import standards (pandas, matplotlib, seaborn)
2. ✅ Configuration edgartools
3. ✅ Chargement EdgarSmartMoneyAnalyzer
4. ✅ Test configuration
5. ✅ Collection transactions politiques (retourne vide, attendu)
6. ✅ Collection transactions d'initiés (119 pour NVDA)
7. ✅ Filtrage haute conviction
8. ✅ Visualisations (prêtes, non testées)
9. ✅ Export CSV (prêt)

---

## ⚠️ Problème Principal: Political Trades

### Sites Identifiés (du document fourni)

1. **Senate Stock Watcher** (GitHub)
   - URL: `https://raw.githubusercontent.com/dwyl/senate-stock-watcher-data/main/data/all_transactions.json`
   - Status: **404 Not Found** (bloqué)
   - Format: JSON avec structure connue

2. **House Stock Watcher** (S3)
   - URL: `https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json`
   - Status: **403 Access Denied** (bloqué)
   - Format: JSON avec structure connue

3. **Capitol Trades** (Mentionné dans document)
   - URL: `https://www.capitoltrades.com/`
   - Status: ⚠️ À investiguer avec BeautifulSoup

### Options Pour Demain

#### Option A: Web Scraping avec BeautifulSoup (RECOMMANDÉE)
```python
# Pseudocode
import requests
from bs4 import BeautifulSoup

response = requests.get('https://www.capitoltrades.com/')
soup = BeautifulSoup(response.content, 'html.parser')

# Parser le HTML pour extraire:
# - Noms des politiciens
# - Tickers tradés
# - Dates de transaction
# - Type (buy/sell)
```

**Avantages:**
- Aucune authentification requise
- Données en temps réel
- Plus actuel que dumps JSON
- Respecte les CGU (lecture du HTML public)

**Challenges:**
- HTML peut changer (maintenance)
- Rate limiting possible (ajouter delays)
- JavaScript possible (besoin de Selenium/Playwright)

#### Option B: Capitol Trades API (SI EXISTE)
À vérifier si un endpoint API existe

#### Option C: Paid APIs
- Quiver Quant ($$$)
- Financial Modeling Prep ($$$)

---

## 🔧 Code à Modifier Demain

### Fichier: `prod/analysis/edgar_smart_money_analyzer.py`

**Méthode à investiguer:**
```python
def collect_political_trades(self, days_back: int = 90) -> pd.DataFrame:
    """
    LIGNE 209: Actuellement retourne DataFrame vide
    
    TÂCHE: Implémenter scraping HTML ou appel API
    """
```

**Données attendues:**
```python
{
    'politician': 'John Doe',
    'chamber': 'Senate',  # ou 'House'
    'ticker': 'AAPL',
    'transaction_date': '2025-12-20',
    'type': 'BUY',  # ou 'SELL'
    'shares': 1000,
    'price': 150.50,  # si disponible
    'transaction_value': 150500
}
```

---

## 📊 Architecture Finale (Vue d'ensemble)

```
smart_money_testing.ipynb
    ├── Imports edgartools
    ├── Configuration SEC
    ├── EdgarSmartMoneyAnalyzer
    │   ├── collect_insider_trades() ✅ WORKS
    │   ├── collect_political_trades() ⚠️ TODO
    │   ├── filter_high_conviction_buys() ✅ WORKS
    │   ├── detect_political_clusters() ✅ READY
    │   └── generate_combined_signals() ✅ READY
    ├── Visualisations (prêtes)
    └── Export CSV (prêt)
```

---

## 🚀 Checklist Demain Matin

- [ ] Tester BeautifulSoup sur `capitoltrades.com`
- [ ] Mapper structure HTML → DataFrame
- [ ] Implémenter `collect_political_trades()`
- [ ] Tester intégration complète
- [ ] Générer signaux combinés avec vraies données
- [ ] Créer visualisations
- [ ] Export CSV pour validation

---

## 📝 Notes Techniques

### Edgartools Configuration
```python
from edgar import Company, set_identity

set_identity("n8n-local-stack research@mtlstreetboy.com")

# Cet appel active:
# - User-Agent correct
# - Rate limiting (10 req/sec)
# - Caching (~/.edgar/_tcache)
```

### Form 4 Parsing (La clé du succès)
```python
# ❌ ANCIEN (manuel, brisé)
ownership = filing.obj()
for trans in ownership.nonDerivativeTransactions:  # Ne fonctionne pas
    ...

# ✅ NOUVEAU (builtin edgartools)
ownership = filing.obj()
df = ownership.to_dataframe()  # Retourne DataFrame parfait
```

### Structure des données Form 4
- **Non-Derivative Transactions**: Common stock trades (BUY/SELL)
- **Derivative Transactions**: Options, warrants, etc.
- **reportingOwners**: Insider info (name, title, CIK)

---

## 🔗 Ressources Utiles

**Documentation edgartools:**
```
https://github.com/dgunning/edgartools
```

**SEC EDGAR API:**
```
https://data.sec.gov/submissions/  (REST JSON)
https://www.sec.gov/Archives/edgar/ (HTML filings)
```

**Political Data Sources:**
```
Senate: https://github.com/dwyl/senate-stock-watcher-data
House: https://github.com/msnavy/house-stock-watcher
Capitol Trades: https://www.capitoltrades.com/
```

---

## 📈 Métriques Actuelles

| Métrique | Status |
|----------|--------|
| Form 4 Parsing | ✅ 119/119 transactions |
| Insider Identification | ✅ 10 uniques |
| High Conviction Filter | ✅ Working |
| Political Data Collection | ❌ Blocked (free APIs) |
| Visualization Code | ✅ Ready (not tested) |
| Combined Signals | ✅ Ready (needs political data) |
| CSV Export | ✅ Ready |

---

## 🎯 Priorité Demain

**URGENT (Blocker):** Débloquer political trades
- BeautifulSoup sur capitoltrades.com
- OU trouver alternative API
- OU data dump local

**HIGH:** Tester full pipeline une fois political data OK

**MEDIUM:** Optimiser visualisations, perf

---

## 💾 Fichiers Clés Modifiés

```
✏️ prod/analysis/edgar_smart_money_analyzer.py (250+ lignes)
   - Fixed Form 4 parsing
   - Ready for political data implementation

✏️ smart_money_testing.ipynb (40+ cells)
   - Updated imports
   - Added module reload logic
   - Tests all edgartools features

📝 debug_form4_structure.py (nouveau)
   - Script pour inspecter Form 4 structure
   - Utile si plus de debug needed
```

---

## 🔄 Prochaines Étapes Proposées

### Demain Matin (Priority 1)
1. Investiguer capitoltrades.com avec BeautifulSoup
2. Mapper structure HTML → données attendues
3. Implémenter scraper

### Demain Midi (Priority 2)
4. Tester intégration `collect_political_trades()`
5. Générer signaux combinés avec vraies données

### Demain Après-midi (Priority 3)
6. Tester visualisations complètes
7. Export de résultats
8. Documenter limitations et résultats

---

## 📞 Questions Pour Demain

1. BeautifulSoup suffisant ou besoin Selenium (JavaScript)?
2. Rate limiting necessary pour scraping?
3. Quelles colonnes minimales pour political data?
4. Faut-il valider contre données historiques?

---

## ✨ Points Forts Actuels

- ✅ Form 4 parsing perfectionné
- ✅ Architecture propre et extensible
- ✅ Rate limiting automatique
- ✅ Caching en place
- ✅ Logging détaillé pour debugging
- ✅ Notebook prêt pour démonstration

---

*Généré: 2025-12-30*
*Prochaine session: 2025-12-31*
