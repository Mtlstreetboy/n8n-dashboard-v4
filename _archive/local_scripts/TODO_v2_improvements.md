# TODO: Améliorations Système de Sentiment v2.0

**Date:** 2025-12-07  
**Statut:** ANALYSE - Pas urgent pour dataset actuel (1645 articles, 19 compagnies)

---

## 🔍 Analyse de votre système de scoring actuel

D'après votre code, voici **exactement** comment fonctionne votre système de sentiment :

### 📊 Le Mécanisme de Comparaison

```python
# Dans votre fonction analyze_article_full
def analyze_article_full(article, articles, ticker, company_name):
    """
    article: L'article à analyser
    articles: TOUS les articles de la même compagnie  ← C'est la clé !
    ticker: NVDA, GOOGL, etc.
    company_name: NVIDIA, Google, etc.
    """
```

**OUI, les articles sont comparés uniquement avec ceux de la MÊME compagnie !**

### 🎯 Comment ça fonctionne (basé sur votre code)

#### 1️⃣ **Sentiment RAW** (absolu)
Le LLM analyse l'article individuellement et donne un score de -100 à +100.

```python
# Exemple pour NVIDIA
Article: "NVIDIA annonce des revenus records"
→ sentiment_raw: +75  (très positif en absolu)

Article: "NVIDIA fait face à des problèmes de supply chain"
→ sentiment_raw: -40  (négatif en absolu)
```

#### 2️⃣ **Sentiment ADJUSTED** (relatif au contexte de la compagnie)

Le LLM reçoit le **contexte des autres articles** de la même compagnie et ajuste le score.

```python
# Contexte pour NVIDIA (passé dans articles)
articles = [
  {"title": "NVIDIA bat les attentes Q1", "sentiment_raw": +65},
  {"title": "NVIDIA investit 10B$ en R&D", "sentiment_raw": +55},
  {"title": "NVIDIA perd un client majeur", "sentiment_raw": -30},
  {"title": "NVIDIA supply chain issues", "sentiment_raw": -40},  # ← Celui qu'on analyse
  ...
]

# Le LLM ajuste en fonction du contexte:
# "Dans le contexte de NVIDIA où les nouvelles sont généralement très positives,
#  cet article sur la supply chain est moins grave que si c'était une startup"

sentiment_adjusted: -25  (au lieu de -40)
# Ajustement: -40 → -25 (+15 points)
```

---

## 🧪 Exemple Concret : NVIDIA vs Startup

### Même article, deux contextes différents

**Article identique :**
> "L'entreprise fait face à des retards de livraison de puces"

**Contexte NVIDIA (grande compagnie établie) :**
```python
articles_nvidia = [
  # Historique très positif
  {"title": "Record revenue Q3", "sentiment": +80},
  {"title": "New AI chip breakthrough", "sentiment": +70},
  {"title": "Partnership with Microsoft", "sentiment": +65},
  # ... 100 articles, moyenne: +55
]

# Analyse
sentiment_raw: -40  (négatif en soi)
sentiment_adjusted: -25  (ajusté à la hausse)

# Raison: "NVIDIA a les ressources pour régler ça rapidement,
#          et leur historique montre une excellente exécution"
```

**Contexte STARTUP (petite compagnie fragile) :**
```python
articles_startup = [
  # Historique mixte/négatif
  {"title": "Funding round delayed", "sentiment": -20},
  {"title": "CEO departure rumors", "sentiment": -35},
  {"title": "Product launch postponed", "sentiment": -15},
  # ... 20 articles, moyenne: -10
]

# Analyse
sentiment_raw: -40  (même article!)
sentiment_adjusted: -55  (ajusté à la BAISSE)

# Raison: "Cette startup est déjà fragile, ce problème
#          pourrait être fatal pour eux"
```

---

## 🔄 Le Flow Complet

```python
# 1. Chargement des données par compagnie
filepath = f"{ticker}_news.json"  # NVDA_news.json
data = json.load(f)
articles = data['articles']  # TOUS les articles NVIDIA

# 2. Pour chaque article à analyser
for article in to_analyze:
    result = analyze_article_full(
        article,      # L'article à scorer
        articles,     # ← Contexte: TOUS les autres articles NVIDIA
        "NVDA",
        "NVIDIA"
    )
    
    # Le LLM voit:
    # - L'article actuel
    # - Les 50-100 derniers articles NVIDIA
    # - Les tendances récentes NVIDIA
    
    article['sentiment_raw'] = result['sentiment_raw']        # -40
    article['sentiment_adjusted'] = result['sentiment_adjusted']  # -25
```

---

## 📈 Analyse Temporelle (Trends)

Votre fonction `calculate_temporal_trend(articles)` fait aussi une analyse **intra-compagnie** :

```python
# Pour NVIDIA
articles_sorted_by_date = sorted(articles, key=lambda x: x['date'])

# Calcule la tendance au fil du temps
# Est-ce que les sentiments de NVIDIA s'améliorent ou empirent?

trend_data = {
    'direction': 'POSITIVE_TREND',  # ou NEGATIVE_TREND, STABLE
    'trend_coefficient': +0.42,     # Corrélation temps vs sentiment
    'recent_avg': +35.2,            # Sentiment moyen derniers 30 jours
    'historical_avg': +28.5         # Sentiment moyen sur 6 mois
}

# Interprétation:
# "NVIDIA montre une tendance positive (+0.42)
#  Les nouvelles récentes sont meilleures que la moyenne historique"
```

---

## ⚠️ Les Limitations de Cette Approche

### ❌ **Problème 1 : Pas de comparaison inter-compagnies**

```python
# NVDA moyenne: +55
# GOOGL moyenne: +30

# Un article GOOGL à +45 pourrait être "excellent pour Google"
# Mais un article NVDA à +45 serait "décevant pour NVIDIA"

# ⚠️ Votre système ne capture PAS cela
```

### ❌ **Problème 2 : Biais de volume**

```python
# NVIDIA: 2000 articles (beaucoup de données)
# Petite startup: 50 articles (peu de contexte)

# L'ajustement NVIDIA est plus fiable
# L'ajustement startup est moins stable
```

### ❌ **Problème 3 : Pas de normalisation sectorielle**

```python
# Toutes les compagnies AI/tech peuvent être corrélées
# Si le secteur entier baisse, tous les sentiments baissent

# Article NVDA: "Revenue down 5%"
# → sentiment: -20
# Mais si TOUT le secteur est down 15%, c'est en fait positif!

# ⚠️ Pas de benchmark sectoriel
```

---

## 🎯 Ce Que Votre Système Capture Bien

### ✅ **1. Contexte historique de la compagnie**
```python
# "Est-ce que cette nouvelle est normale pour NVIDIA?"
# "Est-ce un changement significatif par rapport à leur historique?"
```

### ✅ **2. Tendances temporelles**
```python
# "NVIDIA s'améliore ou empire au fil du temps?"
# Coefficient de tendance: -1 à +1
```

### ✅ **3. Ajustement qualitatif**
```python
# Un bug logiciel chez Google = -10 (ils ont 10K ingénieurs)
# Un bug logiciel chez startup = -40 (peut tuer la boîte)
```

---

## 🚀 Améliorations Possibles (v2.0)

### **Priorité 1: Ajouter un Sentiment INTER-COMPANIES (Score Relatif)**

```python
def calculate_relative_score(ticker, sentiment_adjusted, all_companies_data):
    """
    Compare le sentiment d'une compagnie vs toutes les autres
    """
    
    # Moyenne du secteur AI
    sector_avg = calculate_sector_average(all_companies_data)
    
    # Z-score (combien d'écarts-types par rapport à la moyenne)
    company_avg = get_company_average(ticker, all_companies_data)
    sector_std = calculate_sector_std(all_companies_data)
    
    z_score = (company_avg - sector_avg) / sector_std
    
    return {
        'sentiment_adjusted': sentiment_adjusted,  # Relatif à la compagnie
        'sentiment_sector_relative': z_score,      # Relatif au secteur
        'sector_avg': sector_avg,
        'percentile': calculate_percentile(company_avg, all_companies_data)
    }

# Résultat:
{
    'ticker': 'NVDA',
    'sentiment_adjusted': +55,        # Bon pour NVIDIA
    'sentiment_sector_relative': +2.3, # 2.3 std au-dessus de la moyenne AI
    'sector_avg': +32,
    'percentile': 95                  # Top 5% du secteur
}
```

### **Priorité 2: Normalisation Temporelle (Rolling Window)**

```python
def calculate_rolling_sentiment(articles, window_days=30):
    """
    Sentiment sur fenêtre glissante pour détecter les changements
    """
    
    windows = []
    for date in date_range:
        window_articles = [
            a for a in articles 
            if date - timedelta(days=window_days) <= a['date'] <= date
        ]
        avg = mean([a['sentiment_adjusted'] for a in window_articles])
        windows.append({'date': date, 'sentiment': avg})
    
    return windows

# Permet de voir:
# "NVIDIA était à +60 en janvier, maintenant à +45 en décembre"
# Trend: -15 points sur l'année
```

### **Priorité 3: Benchmark Multi-Niveau**

```python
def calculate_multilevel_sentiment(article, ticker):
    """
    Trois niveaux de comparaison
    """
    
    return {
        # Niveau 1: Absolu (brut LLM)
        'sentiment_absolute': -40,
        
        # Niveau 2: Relatif à la compagnie (votre système actuel)
        'sentiment_company_relative': -25,
        
        # Niveau 3: Relatif au secteur
        'sentiment_sector_relative': +5,  # En fait positif vs secteur!
        
        # Niveau 4: Relatif au marché global
        'sentiment_market_relative': +15,  # Très positif vs marché baissier
        
        'interpretation': "Bien que négatif pour NVIDIA (-25), "
                         "c'est positif vs le secteur AI qui souffre (-30 avg)"
    }
```

---

## 💡 Structure de Données v2.0

Pour une **analyse de sentiment complète**, vous devriez avoir :

```python
{
    'ticker': 'NVDA',
    'article_id': '12345',
    
    # Système actuel v1.0 ✅
    'sentiment_raw': -40,              # Brut LLM
    'sentiment_adjusted': -25,          # Ajusté au contexte NVIDIA
    
    # Améliorations v2.0 🚀
    'sentiment_sector_zscore': +0.8,   # 0.8 std au-dessus des AI companies
    'sentiment_market_zscore': +1.5,   # 1.5 std au-dessus du marché
    'sector_percentile': 72,            # Top 28% des AI companies
    'trend_30d': 'IMPROVING',          # Tendance sur 30 jours
    
    'interpretation': "Article négatif pour NVIDIA (-25), mais positif "
                     "relatif au secteur AI qui est en difficulté. "
                     "NVIDIA surperforme ses pairs."
}
```

---

## 📋 Plan d'Implémentation (Quand nécessaire)

### Phase 1: Post-Processing (facile, 2-3h)
- Ajouter script `calculate_sector_metrics.py`
- Calcule z-scores et percentiles APRÈS analyse
- Pas besoin de refaire l'analyse LLM
- Ajoute les métriques inter-compagnies au JSON existant

### Phase 2: Dashboard Enrichi (2-3h)
- Ajouter graphiques comparatifs dans `dashboard_companies.py`
- Heatmap des sentiments relatifs
- Graphique rolling sentiment 30/60/90 jours
- Tableau de classement inter-compagnies

### Phase 3: Refactoring Analysis (4-6h)
- Modifier `analyze_article_full()` pour calculer multi-niveaux
- Ajouter paramètre `all_companies_context` 
- Calculer en temps réel pendant l'analyse

---

## ⚠️ Décision: QUAND Implémenter v2.0?

### ❌ **PAS MAINTENANT si:**
- Dataset < 10k articles
- 1-2 utilisateurs
- Analyse quotidienne/hebdomadaire suffit
- Pas besoin de trading automatique

### ✅ **OUI si:**
- Dataset > 50k articles
- Besoin de signaux de trading précis
- Comparaison compétitive critique
- Analyse temps réel nécessaire
- Multi-users avec dashboards personnalisés

---

## 🎯 Recommandation Actuelle

**GARDER v1.0 pour l'instant** (sentiment_raw + sentiment_adjusted)

**Ajouter Phase 1** (post-processing) SEULEMENT si vous avez besoin de:
- Comparer NVDA vs GOOGL vs AMD directement
- Identifier les "outliers" du secteur
- Détecter les mouvements collectifs du secteur AI

**Effort minimal:** ~2h de dev pour Phase 1  
**Gain:** Métriques inter-compagnies sans refaire l'analyse LLM

---

**Source:** Analyse de Claude (conversation 2025-12-07)  
**Status:** TODO - À implémenter si le besoin se présente  
**Priority:** LOW (système actuel fonctionne bien pour le use case)
