# 📊 AI Finance News Sentiment Analyzer - Guide Complet

## 🎯 Objectif du Système

Analyser 30 nouvelles IA par jour sur les 100 derniers jours pour détecter les bulles spéculatives via l'analyse de sentiment automatisée.

---

## 📐 Architecture du Pipeline

Voir `ai-sentiment-pipeline.mmd` pour le diagramme visuel complet.

### Phases du Pipeline

1. **Collection** : Agrégation de sources multiples (NewsAPI, RSS, Reddit, HackerNews)
2. **Enrichissement** : Dédoublonnage, filtrage, extraction de contenu
3. **Analyse IA** : Scoring de sentiment par Ollama (-10 à +10)
4. **Stockage** : CSV quotidiens + JSON historique
5. **Agrégation** : Moyennes mobiles (7j, 30j, 90j) + volatilité
6. **Visualisation** : Dashboard + alertes bulle

---

## 🔧 Scripts Python Créés

### 1. `sentiment_analyzer.py`

**Rôle :** Analyse le sentiment d'articles via Ollama.

**Input (stdin JSON):**
```json
{
  "articles": [
    {
      "title": "GPT-5 Release Announced",
      "content": "OpenAI announced...",
      "url": "https://...",
      "published_at": "2025-11-30T10:00:00Z"
    }
  ]
}
```

**Output (stdout JSON):**
```json
[
  {
    "title": "GPT-5 Release Announced",
    "url": "https://...",
    "published_at": "2025-11-30T10:00:00Z",
    "sentiment_score": 8,
    "justification": "Percée majeure augmentant valuation marché",
    "keywords": ["GPT-5", "OpenAI", "breakthrough"],
    "category": "product",
    "analyzed_at": "2025-11-30T16:30:00"
  }
]
```

**Échelle de Scoring:**
- `-10` : Catastrophique (crash, scandale majeur)
- `-5` : Très négatif (échecs, régulations sévères)
- `0` : Neutre (purement informatif)
- `+5` : Très positif (innovation, adoption)
- `+10` : Révolutionnaire (percée historique)

---

### 2. `aggregate_sentiment.py`

**Rôle :** Agrège les scores, calcule moyennes mobiles, détecte les bulles.

**Input (stdin JSON):**
```json
{
  "articles": [
    {"title": "...", "sentiment_score": 8, "published_at": "2025-11-28", ...},
    {"title": "...", "sentiment_score": 6, "published_at": "2025-11-29", ...}
  ]
}
```

**Output (stdout JSON):**
```json
{
  "statistics": {
    "period_start": "2025-08-22",
    "period_end": "2025-11-30",
    "total_days": 100,
    "total_articles": 3000,
    "overall_avg_score": 5.2,
    "latest_ma_7d": 7.1,
    "latest_ma_30d": 6.3,
    "latest_ma_90d": 5.8,
    "latest_volatility_7d": 1.2,
    "bubble_risk_level": "HIGH",
    "bubble_indicators": [
      "EXTREME_OPTIMISM: Score quotidien > 7",
      "DIVERGENCE: MA7d dépasse MA90d de 3.5 points"
    ]
  },
  "daily_data": [
    {"date": "2025-11-30", "daily_avg_score": 7.8, "ma_7d": 7.1, ...}
  ]
}
```

**Signaux de Bulle Détectés:**

1. **EXTREME_OPTIMISM** : Score quotidien > 7 (euphorie)
2. **DIVERGENCE** : MA 7j dépasse MA 90j de plus de 3 points (déconnexion tendance longue)
3. **COMPLACENCY** : Faible volatilité + optimisme élevé (complaisance)
4. **SUSTAINED_RALLY** : Hausse continue sur 14+ jours (momentum insoutenable)

**Niveaux de Risque:**
- `LOW` : Aucun signal
- `MEDIUM` : 1-2 signaux
- `HIGH` : 3+ signaux ou EXTREME_OPTIMISM

---

## 🗂️ Structure de Données Recommandée

### Stockage Quotidien (CSV)
```
local_files/sentiment/
├── 2025-11-30_articles.csv
├── 2025-11-29_articles.csv
└── ...
```

**Colonnes CSV:**
- `title`, `url`, `published_at`, `source`
- `sentiment_score`, `justification`, `keywords`, `category`
- `analyzed_at`

### Stockage Historique (JSON)
```
local_files/sentiment_historical.json
```

Contient l'array complet de tous les articles pour faciliter l'agrégation.

---

## 🔄 Workflow n8n Recommandé

### Workflow 1 : Collection + Analyse (Quotidien)

```
[Schedule Trigger - 8h00 chaque jour]
    ↓
[HTTP Request - NewsAPI.org]
    ↓
[HTTP Request - Google News RSS]
    ↓
[Merge Data]
    ↓
[Code Node - Déduplication]
    ↓
[Execute Command - sentiment_analyzer.py]
    ↓
[Split In Batches - 10 articles] (éviter timeout Ollama)
    ↓
[Write Binary File - CSV quotidien]
    ↓
[Read File - sentiment_historical.json]
    ↓
[Code Node - Append nouveau data]
    ↓
[Write Binary File - sentiment_historical.json]
```

### Workflow 2 : Agrégation + Alerte (Quotidien - après Workflow 1)

```
[Schedule Trigger - 20h00 chaque jour]
    ↓
[Read File - sentiment_historical.json]
    ↓
[Execute Command - aggregate_sentiment.py]
    ↓
[IF Node - bubble_risk_level == "HIGH"]
    ↓ (TRUE)
[Send Email - Alerte Bulle Détectée]
    ↓
[Write Binary File - daily_report.json]
```

---

## 🌐 Sources de Données Gratuites

### 1. NewsAPI.org
- **URL:** `https://newsapi.org/v2/everything?q=AI+OR+LLM+OR+GPT&language=en&sortBy=publishedAt`
- **Limite gratuite:** 100 requêtes/jour
- **Clé API:** Inscription requise

### 2. Google News RSS
- **URL:** `https://news.google.com/rss/search?q=artificial+intelligence+when:7d&hl=en-US&gl=US&ceid=US:en`
- **Limite:** Aucune (RSS public)

### 3. Reddit (via API)
- **Subreddits:** r/MachineLearning, r/artificial, r/OpenAI
- **Endpoint:** `https://www.reddit.com/r/MachineLearning/top.json?t=day`
- **Limite:** 60 requêtes/min sans auth

### 4. HackerNews API
- **URL:** `https://hacker-news.firebaseio.com/v0/topstories.json`
- **Puis:** `https://hacker-news.firebaseio.com/v0/item/{id}.json`
- **Limite:** Aucune

---

## 📊 Exemple de Résultat d'Analyse

### Scénario : Bulle Détectée

**Date:** 2025-11-30

**Statistiques:**
- Score moyen 100 jours : `5.2`
- Score moyen 7 derniers jours : `7.8`
- Volatilité 7j : `0.9` (très faible)
- Articles analysés : `3000`

**Signaux:**
- ⚠️ **EXTREME_OPTIMISM** : Score quotidien à 8.1
- ⚠️ **DIVERGENCE** : MA 7j dépasse MA 90j de 4.2 points
- ⚠️ **COMPLACENCY** : Volatilité < 1 avec optimisme > 7

**Verdict:** `BUBBLE RISK = HIGH`

**Interprétation :** Le marché IA est en phase d'euphorie. Les nouvelles sont systématiquement interprétées positivement, avec peu de remise en question. Historiquement, ce pattern précède des corrections de 20-40%.

---

## 🛠️ Installation des Dépendances Python

Le script `aggregate_sentiment.py` nécessite **pandas**. Ajoutez-le au Dockerfile :

```dockerfile
# Dans votre Dockerfile actuel, ligne "RUN pip install..."
RUN pip install pandas requests numpy matplotlib
```

Puis rebuild :
```powershell
docker-compose down
docker-compose up -d --build
```

---

## 🚀 Prochaines Étapes

1. **Tester le script d'analyse manuellement :**
   ```powershell
   echo '{"articles":[{"title":"Test","content":"AI breakthrough announced","url":"http://test.com","published_at":"2025-11-30"}]}' | docker exec -i n8n_data_architect python3 /data/scripts/sentiment_analyzer.py
   ```

2. **Créer le workflow n8n de collection** (je peux générer le JSON si vous voulez)

3. **Configurer les API keys** dans n8n (NewsAPI, Reddit si besoin)

4. **Créer un dashboard avec `matplotlib`** pour visualiser les graphiques (script Python additionnel)

---

## 📈 Métriques de Performance

- **Temps d'analyse par article :** ~3-5 secondes (Ollama local)
- **Throughput quotidien :** 30 articles = ~2-3 minutes
- **Stockage :** ~10 MB pour 100 jours de données

---

## 🔒 Notes de Sécurité

- Les API keys doivent être dans des **variables d'environnement** n8n (jamais hardcodées)
- Le fichier `sentiment_historical.json` peut devenir volumineux → implémenter une rotation mensuelle
- Ollama tourne en local → aucune donnée sensible envoyée à des tiers

---

**Prêt à implémenter ?** Dites-moi si vous voulez que je génère :
1. Le workflow n8n complet (JSON à importer)
2. Un script de visualisation avec graphiques
3. Un script de test unitaire pour valider le pipeline
