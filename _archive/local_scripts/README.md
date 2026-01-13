# Scripts AI Finance News Sentiment Analyzer

## 📁 Structure

### Core Scripts (Production)
```
sentiment_weighted.py      # Module d'analyse avec pondération financière
analyze_weighted.py        # Script principal d'analyse complète  
collect_parallel.py        # Collection parallèle de nouvelles (GNews)
aggregate_sentiment.py     # Agrégation et détection de bulles
```

### Tests
```
test_gnews.py             # Validation de l'API GNews
test_weighted.py          # Test du système de pondération
```

---

## 🚀 Utilisation

### 1. Collecter les articles (100 jours)
```bash
docker exec -it n8n_data_architect python3 /data/scripts/collect_parallel.py
```
**Output:** `/data/files/collected_articles_100days.json` (1937 articles)

---

### 2. Analyser le sentiment (avec pondération financière)
```bash
docker exec -it n8n_data_architect python3 /data/scripts/analyze_weighted.py
```

**Features:**
- ✅ Pondération basée sur mots-clés financiers critiques
- ✅ Contexte historique (tendance des 30 derniers jours)
- ✅ Échelle -10 à +10 avec distribution complète
- ✅ Parallélisation (10 workers)
- ✅ Checkpoints tous les 200 articles

**Output:** `/data/files/sentiment_weighted.json`

**Temps:** ~10-15 minutes pour 1937 articles

---

### 3. Agréger et détecter les bulles
```bash
docker exec -it n8n_data_architect python3 /data/scripts/aggregate_sentiment.py
```

**Features:**
- ✅ Moyennes mobiles (7j, 30j, 90j)
- ✅ Détection de 4 signaux de bulle:
  - EXTREME_OPTIMISM (score > 7)
  - DIVERGENCE (écart > 3 points)
  - COMPLACENCY (faible volatilité)
  - SUSTAINED_RALLY (14 jours consécutifs positifs)

**Output:** `/data/files/bubble_analysis.json`

---

## 🧪 Tests

### Tester GNews
```bash
docker exec -it n8n_data_architect python3 /data/scripts/test_gnews.py
```
Valide : connexion API, recherche par date, parsing d'articles

### Tester la pondération
```bash
docker exec -it n8n_data_architect python3 /data/scripts/test_weighted.py
```
Valide : échelle -10 à +10, mots-clés financiers, variation des scores

---

## 📊 Système de Pondération

### Mots-clés EXTRÊMEMENT POSITIFS (+7 à +10)
- `breakthrough`, `revolutionary`, `game-changer`, `unprecedented`
- `explosive growth`, `trillion dollar`, `market dominance`
- `AGI achieved`, `superintelligence`, `transformative`

### Mots-clés TRÈS POSITIFS (+4 à +6)
- `partnership`, `acquisition`, `funding round`, `IPO`
- `innovation`, `adoption`, `expansion`, `record revenue`
- `outperforms`, `beats expectations`, `market leader`

### Mots-clés NÉGATIFS (-3 à -1)
- `concerns`, `criticism`, `challenges`, `risks`
- `slower adoption`, `disappointing results`, `regulatory scrutiny`

### Mots-clés TRÈS NÉGATIFS (-6 à -4)
- `data breach`, `scandal`, `lawsuit`, `ban`
- `massive layoffs`, `project cancelled`, `stock crash`

### Mots-clés CATASTROPHIQUES (-10 à -7)
- `systemic failure`, `criminal charges`, `existential threat`
- `industry collapse`, `regulation shutdown`, `total ban`

---

## 📈 Workflow Complet

```
1. collect_parallel.py
   ↓
   collected_articles_100days.json (1937 articles)
   ↓
2. analyze_weighted.py
   ↓
   sentiment_weighted.json (articles + scores)
   ↓
3. aggregate_sentiment.py
   ↓
   bubble_analysis.json (détection finale)
```

---

## 🔧 Configuration

### Ollama Model
- **Model:** llama3 (8B parameters)
- **Temperature:** 0.2 (déterministe)
- **Port:** http://ollama:11434

### Parallelization
- **Workers:** 10 threads
- **Timeout:** 60s par requête
- **Checkpoint:** tous les 200 articles

### GNews
- **Source:** Google News RSS
- **Langue:** Français + Anglais
- **Période:** 100 jours (configuré dans collect_parallel.py)

---

## 📂 Data Files

```
/data/files/
├── collected_articles_100days.json    # Articles bruts (GNews)
├── sentiment_weighted.json             # Articles + scores
└── bubble_analysis.json                # Détection de bulle
```

---

## 🎯 Objectif Final

Détecter si le marché de l'IA est dans une **bulle spéculative** basé sur :
1. Sentiment moyen sur 100 jours
2. Volatilité des scores
3. Signaux d'optimisme extrême
4. Divergence entre attentes et réalité
