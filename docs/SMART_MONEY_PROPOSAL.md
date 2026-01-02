# 💰 Smart Money & Political Trades Dashboard - Proposition d'Intégration

**Date:** 2 Janvier 2026  
**Objectif:** Intégrer les données de trading politique (Congress, Senate, House) dans l'écosystème existant avec le même pattern que les Options

---

## 📋 Vue d'Ensemble

### Architecture Cible (Inspirée du système Options)

```
QuiverQuant API
     ↓
collect_political_trades.py (similaire à collect_options.py)
     ↓
/data/political_trades/*.csv + *.json
     ↓
analyze_political_sentiment.py (similaire aux analyzers existants)
     ↓
dashboard_political_trades.py (Streamlit - 5 vues comme dashboard_options.py)
     ↓
Intégration dans dashboard_v4_split.html (nouveau niveau)
```

---

## 🗂️ Structure Proposée

### 1. Fichiers de Collection

**`prod/collection/collect_political_trades.py`**
- Collecte Congressional, Senate, House Trading via QuiverQuant
- Cache local pour accumulation progressive (résout le problème des 1000 résultats)
- Export CSV + JSON par source et par ticker
- Rotation automatique des caches (garder historique)

**Fonctionnalités:**
```python
class PoliticalTradesCollector:
    """
    Collecte et cache les trades politiques
    """
    def collect_congressional()  # Tous les politiciens
    def collect_senate()         # Sénat uniquement  
    def collect_house()          # Chambre uniquement
    def collect_by_ticker(ticker)  # Par action spécifique
    def cache_with_history()     # Accumulation progressive
    def export_signals()         # Signaux bullish/bearish
```

**Données générées:**
```
/data/political_trades/
├── congressional_all_trades.csv
├── congressional_60days.csv
├── senate_trades.csv
├── house_trades.csv
├── ticker_sentiment_60days.csv
├── AAPL_political_trades.json
├── NVDA_political_trades.json
└── cache/
    ├── congressional_cache.parquet
    ├── senate_cache.parquet
    └── house_cache.parquet
```

---

### 2. Fichiers d'Analyse

**`prod/analysis/political_sentiment_analyzer.py`**
- Analyse le sentiment par ticker (bullish/bearish)
- Ratio achats/ventes
- Smart Money score (basé sur volume et timing)
- Détection de patterns (clusters d'achats, ventes massives)

**Métriques calculées:**
```python
{
    "ticker": "AAPL",
    "political_sentiment_score": 0.65,  # -1 à +1
    "buy_sell_ratio": 2.3,
    "total_trades_60d": 45,
    "purchases": 30,
    "sales": 15,
    "avg_trade_size": "$50K-$100K",
    "top_buyers": ["Rep. Smith", "Sen. Johnson"],
    "top_sellers": ["Rep. Lee"],
    "smart_money_factor": 0.08,
    "signal": "BULLISH",
    "confidence": "MEDIUM"
}
```

---

### 3. Dashboard Streamlit

**`prod/dashboard/dashboard_political_trades.py`**

Inspiré de `dashboard_options.py` avec **5 visualisations:**

#### 🏛️ VUE 1: Congressional Activity Heatmap
- **Axes:** Date (Y) × Ticker (X)  
- **Couleur:** Sentiment (Rouge=Vente, Vert=Achat, Intensité=Volume)
- **Signaux:** Clusters d'achats = bullish institutional signal

#### 📊 VUE 2: Buy/Sell Ratio by Ticker
- **Type:** Bar chart horizontal
- **Données:** Ratio achats/ventes par ticker (60 jours)
- **Tri:** Plus bullish → Plus bearish
- **Signaux:** Ratio > 2 = Fort signal bullish

#### 👥 VUE 3: Top Politicians Trading Activity
- **Type:** Treemap ou Bubble chart
- **Taille:** Nombre de trades
- **Couleur:** Performance historique (% de trades rentables)
- **Signaux:** Suivre les "Smart Traders" avec meilleur track record

#### 📈 VUE 4: Timeline - Political Trades vs Stock Price
- **Type:** Dual-axis line chart
- **Ligne 1:** Prix de l'action (candlestick)
- **Markers:** Achats (🟢) et Ventes (🔴) politiques
- **Signaux:** Corrélation achats politiques → mouvement prix

#### 🎯 VUE 5: Sentiment Composite Score
- **Type:** Gauge + Breakdown
- **Score:** Combinaison de:
  - Congressional sentiment: 50%
  - Senate sentiment: 30%
  - House sentiment: 20%
- **Classification:** STRONG BUY / BUY / HOLD / SELL / STRONG SELL

---

### 4. Intégration Dashboard V4

**Modification de `prod/dashboard/dashboard_v4_split.html`**

Ajouter un **3ème bouton de navigation** dans GridView:

```javascript
// Boutons existants
<button onClick={() => handleNavigate('sentiment', ticker)}>
    📊 Sentiment Analysis
</button>
<button onClick={() => handleNavigate('options', ticker)}>
    💹 Options Data
</button>

// NOUVEAU BOUTON
<button onClick={() => handleNavigate('political', ticker)}>
    💰 Political Trades
</button>
```

**Nouvelle vue `PoliticalView`:**
```javascript
const PoliticalView = ({ ticker, data, onBack }) => {
    // Afficher:
    // - Score de sentiment politique
    // - Liste des trades récents
    // - Top 5 politiciens qui tradent ce ticker
    // - Signal: BUY/SELL/HOLD
    // - Corrélation avec mouvements de prix
}
```

---

### 5. Automation Quotidienne

**Modification de `prod/automation/daily_automation.py`**

Ajouter une étape de collecte politique:

```python
def collect_political_trades():
    """Collecte les trades politiques quotidiennement"""
    log("💰 Collecte Political Trades...")
    
    success = run_command(
        ['python3', '/data/scripts/collect_political_trades.py'],
        "Collecte Political Trades",
        timeout=600
    )
    
    if success:
        # Analyser le sentiment
        run_command(
            ['python3', '/data/scripts/analyze_political_sentiment.py'],
            "Analyse Political Sentiment"
        )
    
    return success
```

**Ordre d'exécution:**
1. ✅ Collecte News (existant)
2. ✅ Collecte Options (existant)
3. 🆕 Collecte Political Trades
4. ✅ Analyse Sentiment V4 (existant)
5. 🆕 Analyse Political Sentiment
6. ✅ Génération Dashboard (existant)

---

## 📊 Données Combinées: Super Score

### Formule du Score Final Intégré

```python
FINAL_SCORE = (
    news_sentiment × 0.25 +
    options_sentiment × 0.35 +
    analyst_sentiment × 0.15 +
    political_sentiment × 0.25  # NOUVEAU
)
```

**Justification des poids:**
- **Options (35%):** Signal le plus immédiat et liquide
- **Political (25%):** Insider info, mais délai de reporting
- **News (25%):** Sentiment public/médiatique
- **Analyst (15%):** Opinions d'experts, souvent "priced in"

---

## 🔄 Flux de Données Complet

### Journée type (automatisée)

```
06:00 → Collecte News (prod/collection/collect_news.py)
06:30 → Collecte Options (prod/collection/collect_options.py)
07:00 → Collecte Political Trades (prod/collection/collect_political_trades.py) 🆕
07:30 → Analyse Sentiment V4 (tous tickers)
08:00 → Analyse Political Sentiment 🆕
08:30 → Génération Dashboard HTML
09:00 → ✅ Dashboard prêt pour la journée
```

---

## 🎨 Wireframe Dashboard Intégré

### Niveau 1: GridView (Existant + Ajout)

```
┌──────────────────────────────────────────┐
│  🧠 Sentiment Dashboard V4 - Grid View   │
├──────────────────────────────────────────┤
│  ┌────────┬────────┬────────┐           │
│  │  NVDA  │  AAPL  │  MSFT  │           │
│  │  0.65  │  0.42  │ -0.12  │           │
│  │  🟢💰🔥 │  🟢💰  │  🔴    │           │
│  └────────┴────────┴────────┘           │
│                                          │
│  Légende:                                │
│  🟢 = Sentiment positif                  │
│  💰 = Political trades bullish 🆕        │
│  🔥 = High volatility                    │
└──────────────────────────────────────────┘
```

### Niveau 2: Ticker Detail (Nouveau bouton)

```
┌──────────────────────────────────────────┐
│  Grid > NVDA                             │
├──────────────────────────────────────────┤
│  ┌─────────────┬─────────────┬──────┐   │
│  │ 📊 Sentiment│ 💹 Options  │💰NEW│   │
│  │   Analysis  │    Data     │Trades│   │
│  └─────────────┴─────────────┴──────┘   │
└──────────────────────────────────────────┘
```

### Niveau 3: Political Trades View (Nouveau)

```
┌──────────────────────────────────────────┐
│  Grid > NVDA > 💰 Political Trades       │
├──────────────────────────────────────────┤
│  🎯 SENTIMENT SCORE: 0.72 (BULLISH)      │
│                                          │
│  📊 60-DAY ACTIVITY                      │
│  Achats:  47  (62%)                      │
│  Ventes:  29  (38%)                      │
│  Ratio:   1.62  🟢                       │
│                                          │
│  👥 TOP TRADERS                          │
│  1. Rep. Johnson    +12 trades (all BUY)│
│  2. Sen. Williams   +8 trades           │
│  3. Rep. Martinez   +5 trades           │
│                                          │
│  📅 RECENT TRADES                        │
│  2025-01-01 | Rep. Smith | BUY | $50K   │
│  2024-12-28 | Sen. Lee   | BUY | $100K  │
│  2024-12-22 | Rep. Davis | SELL| $25K   │
│                                          │
│  ⚠️ ALERTS                               │
│  🔔 Cluster de 5 achats en 7 jours      │
│  💡 Signal historiquement précurseur     │
└──────────────────────────────────────────┘
```

---

## 📝 Fichiers à Créer

### Production Files

```
prod/
├── collection/
│   └── collect_political_trades.py         🆕 (300 lignes estimées)
├── analysis/
│   └── political_sentiment_analyzer.py     🆕 (250 lignes estimées)
├── dashboard/
│   └── dashboard_political_trades.py       🆕 (800 lignes, style dashboard_options.py)
├── utils/
│   └── political_trades_cache.py           🆕 (150 lignes, gestion cache/historique)
└── config/
    └── political_trades_config.py          🆕 (50 lignes, configuration)
```

### Services (API Client)

```
services/
└── quiverquant/
    ├── quiverquant_client.py               ✅ Existant
    └── config.py                           ✅ Existant
```

### Data Directory

```
/data/political_trades/  (dans container)
├── congressional_all_trades.csv
├── senate_trades.csv
├── house_trades.csv
├── purchases_60days.csv
├── sales_60days.csv
├── ticker_sentiment_60days.csv
└── cache/
    ├── congressional_cache.parquet
    ├── senate_cache.parquet
    └── house_cache.parquet
```

---

## 🧪 Tests

**`prod/tests/test_political_trades.py`** 🆕

```python
def test_collect_congressional():
    """Test collection Congressional data"""
    collector = PoliticalTradesCollector()
    df = collector.collect_congressional()
    assert len(df) > 0
    assert 'TransactionDate' in df.columns

def test_political_sentiment_score():
    """Test sentiment score calculation"""
    analyzer = PoliticalSentimentAnalyzer()
    score = analyzer.calculate_sentiment('NVDA')
    assert -1 <= score <= 1

def test_cache_accumulation():
    """Test progressive cache accumulation"""
    collector = PoliticalTradesCollector()
    collector.cache_with_history(df_new, 'congressional')
    # Verify cache grows over time
```

---

## 🚀 Plan d'Implémentation (5 jours)

### Jour 1: Collection
- [ ] Créer `collect_political_trades.py`
- [ ] Implémenter cache avec historique
- [ ] Tester collection sur 3 tickers
- [ ] Export CSV + JSON

### Jour 2: Analyse
- [ ] Créer `political_sentiment_analyzer.py`
- [ ] Calculer sentiment score
- [ ] Ratio achats/ventes
- [ ] Top traders identification

### Jour 3: Dashboard Streamlit
- [ ] Créer `dashboard_political_trades.py`
- [ ] 5 visualisations (heatmap, ratio, timeline, etc.)
- [ ] Tester localement

### Jour 4: Intégration Dashboard V4
- [ ] Modifier `dashboard_v4_split.html`
- [ ] Ajouter `PoliticalView`
- [ ] Ajouter bouton navigation
- [ ] Intégrer dans Super Score

### Jour 5: Automation + Tests
- [ ] Modifier `daily_automation.py`
- [ ] Créer tests unitaires
- [ ] Documentation
- [ ] Déploiement

---

## 💡 Avantages de Cette Approche

### ✅ Cohérence Architecture
- Même pattern que `collect_options.py` → `dashboard_options.py`
- Réutilise les mêmes outils (Streamlit, Plotly, pandas)
- S'intègre naturellement dans `dashboard_v4_split.html`

### ✅ Séparation des Préoccupations
- Collection indépendante (peut tourner seule)
- Dashboard indépendant (peut être consulté séparément)
- Intégration optionnelle dans V4

### ✅ Cache Intelligent
- Résout le problème des 1000 résultats
- Accumulation progressive sur 1 an
- Pas de perte de données historiques

### ✅ Évolutivité
- Facile d'ajouter d'autres sources (Insider Trades, WSB sentiment)
- Pattern réutilisable pour d'autres datasets
- Dashboard extensible (ajouter vues)

---

## 🎯 Résultat Final

Un **système complet** qui permet de:

1. ✅ **Collecter** les trades politiques automatiquement
2. ✅ **Analyser** le sentiment par ticker
3. ✅ **Visualiser** dans un dashboard dédié (Streamlit)
4. ✅ **Intégrer** dans le dashboard V4 principal (HTML)
5. ✅ **Combiner** avec News, Options, Analyst dans un Super Score
6. ✅ **Alerter** sur les signaux importants (clusters d'achats)

---

## 📞 Prochaines Étapes

**Validation:**
- [ ] Valider l'approche proposée
- [ ] Ajuster les poids du Super Score
- [ ] Confirmer les 5 visualisations du dashboard

**Développement:**
- [ ] Je peux commencer par créer les fichiers de base
- [ ] Implémenter la collection en premier
- [ ] Puis l'analyse et le dashboard

**Questions:**
1. Voulez-vous que je crée les fichiers maintenant?
2. Préférez-vous commencer par la collection ou le dashboard?
3. Souhaitez-vous modifier les poids du Super Score?

---

**📅 Créé:** 2 Janvier 2026  
**👤 Auteur:** GitHub Copilot  
**📊 Projet:** n8n-dashboard-v4
