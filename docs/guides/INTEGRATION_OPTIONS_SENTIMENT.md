# 🔗 INTÉGRATION - Options Dashboard + Sentiment Dashboard

## 🎯 Objectif

Fusionner les insights des **options** avec le **sentiment des news** pour créer un **Super Score** de sentiment composite.

---

## 📊 Architecture Actuelle

```
prod/
├── dashboard_sentiment.py       # Sentiment des news (port 8501)
├── dashboard_options.py         # Analyse des options (port 8502)
├── dashboard_companies.py       # Vue par compagnie
└── dashboard_timeline.py        # Évolution temporelle
```

**Problème:** Les dashboards sont séparés, pas de vue unifiée.

---

## 🚀 Plan d'Intégration

### Phase 1: Ajouter un onglet Options au Dashboard Sentiment

**Fichier:** `dashboard_sentiment.py`

**Modifications:**
1. Ajouter un nouvel onglet "📊 Options Analysis"
2. Importer les fonctions de `dashboard_options.py`
3. Afficher les 5 visualisations dans le dashboard principal

```python
# Dans dashboard_sentiment.py

# Importer les fonctions d'options
from dashboard_options import (
    load_options_data,
    get_current_stock_price,
    calculate_composite_score,
    create_volatility_smile,
    create_option_heatmap,
    create_open_interest_ladder,
    create_money_flow_analysis,
    create_price_volume_3d
)

# Ajouter un nouvel onglet
tab_options = st.tabs(["Vue Globale", "Composantes", "Divergences", "Details", "📊 Options"])[4]

with tab_options:
    st.subheader("📊 Analyse des Options")
    
    # Charger données options
    calls_df, puts_df = load_options_data(selected_ticker)
    
    if calls_df is not None and puts_df is not None:
        current_price = get_current_stock_price(selected_ticker)
        scores = calculate_composite_score(calls_df, puts_df, current_price)
        
        # Afficher les 5 vues...
    else:
        st.warning("Aucune donnée d'options disponible")
```

---

### Phase 2: Créer un Score Composite Final

**Formule proposée:**

```python
Final_Sentiment = (
    News_Sentiment × 0.30 +        # Sentiment des articles
    Options_Score × 0.50 +         # Score des options (poids fort!)
    Momentum × 0.10 +              # Momentum technique
    Fear_Greed × 0.10              # Indices de marché
)
```

**Pourquoi ce poids?**
- **Options (50%)**: Argent réel en jeu, révèle les vraies convictions
- **News (30%)**: Narratif important mais peut être du bruit
- **Momentum (10%)**: Contexte technique
- **Fear/Greed (10%)**: Sentiment global du marché

**Implémentation:**

```python
def calculate_final_sentiment(ticker, news_sentiment, options_score, momentum, fear_greed):
    """
    Calcule le sentiment final en combinant toutes les sources
    """
    # Normaliser les scores entre -1 et 1
    news_norm = news_sentiment  # Déjà normalisé
    options_norm = np.clip(options_score, -1, 1)
    momentum_norm = np.clip(momentum, -1, 1)
    fear_greed_norm = (fear_greed - 50) / 50  # Convertir 0-100 en -1 à 1
    
    # Score composite
    final_score = (
        news_norm * 0.30 +
        options_norm * 0.50 +
        momentum_norm * 0.10 +
        fear_greed_norm * 0.10
    )
    
    # Confidence (basé sur la cohérence des signaux)
    signals = [news_norm, options_norm, momentum_norm, fear_greed_norm]
    std_dev = np.std(signals)
    confidence = 1 - (std_dev / 2)  # Plus les signaux sont cohérents, plus la confidence est haute
    
    return {
        'final_score': final_score,
        'confidence': confidence,
        'components': {
            'news': news_norm * 0.30,
            'options': options_norm * 0.50,
            'momentum': momentum_norm * 0.10,
            'fear_greed': fear_greed_norm * 0.10
        }
    }
```

---

### Phase 3: Créer une Vue "Super Score"

**Affichage visuel:**

```python
# Métriques principales
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🎯 Super Score",
        f"{final_score:.2f}",
        delta=f"Confidence: {confidence:.0%}"
    )

with col2:
    sentiment_label = "🚀 Bullish" if final_score > 0.15 else "📉 Bearish" if final_score < -0.15 else "⏸️ Neutral"
    st.metric("Signal", sentiment_label)

with col3:
    # Force du signal
    signal_strength = abs(final_score)
    strength_label = "💪 Fort" if signal_strength > 0.3 else "👌 Moyen" if signal_strength > 0.15 else "🤏 Faible"
    st.metric("Force", strength_label)

# Graphique de décomposition
fig = go.Figure()

fig.add_trace(go.Bar(
    x=['News', 'Options', 'Momentum', 'Fear/Greed'],
    y=[
        components['news'],
        components['options'],
        components['momentum'],
        components['fear_greed']
    ],
    marker_color=['#2196F3', '#4CAF50', '#FF9800', '#F44336'],
    text=[
        f"{components['news']:.2f}",
        f"{components['options']:.2f}",
        f"{components['momentum']:.2f}",
        f"{components['fear_greed']:.2f}"
    ],
    textposition='outside'
))

fig.update_layout(
    title="Décomposition du Super Score",
    yaxis_title="Contribution au Score Final",
    height=400
)

st.plotly_chart(fig, use_container_width=True)
```

---

### Phase 4: Alertes Intelligentes

**Détecter les divergences:**

```python
def detect_divergences(news_sentiment, options_score):
    """
    Détecte les divergences entre news et options
    """
    divergences = []
    
    # Divergence bullish: News négatives mais options positives
    if news_sentiment < -0.2 and options_score > 0.2:
        divergences.append({
            'type': '🚀 DIVERGENCE BULLISH',
            'signal': 'News négatives mais options bullish',
            'interpretation': 'Smart money achète pendant que les news sont mauvaises',
            'action': 'OPPORTUNITÉ D\'ACHAT potentielle',
            'confidence': 'Élevée'
        })
    
    # Divergence bearish: News positives mais options négatives
    if news_sentiment > 0.2 and options_score < -0.2:
        divergences.append({
            'type': '📉 DIVERGENCE BEARISH',
            'signal': 'News positives mais options bearish',
            'interpretation': 'Smart money se protège malgré les bonnes news',
            'action': 'PRUDENCE - Possibilité de baisse',
            'confidence': 'Élevée'
        })
    
    # Cohérence bullish: Tous les signaux alignés
    if news_sentiment > 0.2 and options_score > 0.2:
        divergences.append({
            'type': '💪 CONVICTION BULLISH',
            'signal': 'Tous les signaux alignés positivement',
            'interpretation': 'Consensus fort sur la hausse',
            'action': 'SIGNAL D\'ACHAT fort',
            'confidence': 'Très élevée'
        })
    
    # Cohérence bearish
    if news_sentiment < -0.2 and options_score < -0.2:
        divergences.append({
            'type': '⚠️ CONVICTION BEARISH',
            'signal': 'Tous les signaux alignés négativement',
            'interpretation': 'Consensus fort sur la baisse',
            'action': 'SIGNAL DE VENTE fort',
            'confidence': 'Très élevée'
        })
    
    return divergences

# Affichage
divergences = detect_divergences(news_sentiment, options_score)

if divergences:
    st.subheader("🔔 Alertes Détectées")
    for div in divergences:
        with st.expander(f"{div['type']} - Confidence: {div['confidence']}"):
            st.markdown(f"**Signal:** {div['signal']}")
            st.markdown(f"**Interprétation:** {div['interpretation']}")
            st.info(f"**Action suggérée:** {div['action']}")
```

---

## 📊 Exemple de Vue Intégrée

### Cas 1: NVDA - Cohérence Bullish

```
🎯 Super Score: 0.42 (Bullish)
Confidence: 85%

Décomposition:
├── 📰 News: +0.15 (30%) = +0.045
├── 📊 Options: +0.50 (50%) = +0.250    ← Poids fort!
├── 📈 Momentum: +0.30 (10%) = +0.030
└── 😱 Fear/Greed: +0.40 (10%) = +0.040
    ────────────────────────────────
    TOTAL: +0.365 → 0.42 (arrondi)

🔔 ALERTE:
💪 CONVICTION BULLISH
Tous les signaux alignés positivement
→ SIGNAL D'ACHAT fort
```

### Cas 2: TSLA - Divergence Bullish

```
🎯 Super Score: 0.08 (Neutral)
Confidence: 45%

Décomposition:
├── 📰 News: -0.25 (30%) = -0.075
├── 📊 Options: +0.35 (50%) = +0.175    ← Divergence!
├── 📈 Momentum: -0.10 (10%) = -0.010
└── 😱 Fear/Greed: +0.20 (10%) = +0.020
    ────────────────────────────────
    TOTAL: +0.11 → 0.08

🔔 ALERTE:
🚀 DIVERGENCE BULLISH
News négatives mais options bullish
Smart money achète pendant que les news sont mauvaises
→ OPPORTUNITÉ D'ACHAT potentielle
```

---

## 🛠️ Implémentation Step-by-Step

### Étape 1: Tester l'intégration localement

```bash
# 1. Créer une copie de dashboard_sentiment.py
cp prod/dashboard_sentiment.py prod/dashboard_sentiment_integrated.py

# 2. Ajouter les imports
# 3. Ajouter l'onglet Options
# 4. Ajouter le calcul du Super Score
# 5. Tester
docker exec -d n8n_data_architect streamlit run /data/scripts/dashboard_sentiment_integrated.py --server.port 8503 --server.address 0.0.0.0
```

### Étape 2: Valider les résultats

- Comparer Super Score vs réalité du marché
- Ajuster les poids si nécessaire
- Backtester sur historique

### Étape 3: Remplacer l'ancien dashboard

```bash
# Si validé, remplacer
mv prod/dashboard_sentiment_integrated.py prod/dashboard_sentiment.py
```

---

## 📈 KPIs à Suivre

1. **Accuracy du Super Score**
   - % de prédictions correctes sur 1 jour
   - % de prédictions correctes sur 7 jours

2. **Alpha des Alertes**
   - Performance moyenne après une alerte bullish
   - Performance moyenne après une alerte bearish

3. **Divergences**
   - Win rate des divergences bullish
   - Win rate des divergences bearish

---

## 🚀 Extensions Futures

### 1. Machine Learning
Entraîner un modèle pour optimiser les poids automatiquement:
```python
from sklearn.linear_model import Ridge

# Features
X = [[news, options, momentum, fear_greed], ...]

# Target: Rendement réel à J+7
y = [rendement_j7, ...]

# Trouver les poids optimaux
model = Ridge().fit(X, y)
optimal_weights = model.coef_
```

### 2. Dark Pool Activity
Ajouter les données de dark pools (transactions institutionnelles):
```python
Final_Sentiment = (
    News × 0.25 +
    Options × 0.35 +
    Dark_Pool × 0.20 +    # Nouveau!
    Momentum × 0.10 +
    Fear_Greed × 0.10
)
```

### 3. Social Sentiment
Intégrer Twitter/Reddit:
```python
Final_Sentiment = (
    News × 0.25 +
    Options × 0.35 +
    Social × 0.15 +        # Nouveau!
    Momentum × 0.15 +
    Fear_Greed × 0.10
)
```

---

## 📚 Ressources

- **Options Theory**: https://www.optionsplaybook.com/
- **Sentiment Analysis**: https://towardsdatascience.com/sentiment-analysis-concept-analysis-and-applications
- **Composite Indicators**: https://www.investopedia.com/articles/active-trading/041814/four-most-commonlyused-indicators-trend-trading.asp

---

**Status:** 🟡 En attente d'implémentation  
**Priorité:** Haute  
**Difficulté:** Moyenne  
**Impact:** ⭐⭐⭐⭐⭐ (Majeur)
