# 📊 Production Scripts - AI Stocks Sentiment Analysis

## 🚀 Quick Start - Dashboard Sentiment Multi-Dimensionnel

```bash
# 1. Lancer le dashboard principal (port 8502)
docker exec n8n_data_architect sh -c "nohup python3 -m streamlit run /data/scripts/dashboard_sentiment.py --server.port=8502 --server.address=0.0.0.0 > /tmp/dashboard_sentiment.log 2>&1 &"

# Accéder: http://localhost:8502

# 2. Analyser toutes les compagnies
docker exec n8n_data_architect python3 /data/scripts/analyze_all_sentiment.py

# 3. Collecter nouvelles données
docker exec n8n_data_architect python3 /data/scripts/collect_options.py
```

---

## 🎯 Architecture du Système

### 📊 **Moteur de Sentiment Multi-Dimensionnel** (Nouveau!)

**`advanced_sentiment_engine.py`** - Analyse révolutionnaire combinant 5 dimensions:
1. 📰 Sentiment News (LLM Llama3)
2. 📊 Sentiment Options (Put/Call Ratio)
3. ⚡ Narrative Momentum
4. 💪 Conviction Score
5. 🔍 Divergence Detection

**`analyze_all_sentiment.py`** - Batch analysis pour toutes les compagnies
- Génère rapports individuels + consolidé
- Exports CSV + JSON
- Détection automatique des divergences

**`dashboard_sentiment.py`** - Dashboard interactif (port 8502)
- Vue globale (15 compagnies)
- Graphiques Plotly
- Analyse détaillée par ticker
- Export CSV

### 1️⃣ **Collecte de Données**
- **`collect_news.py`** - Collecte hybride NewsAPI + GNews
  - Batch de 7 jours (optimisé pour quota)
  - Usage: `python3 collect_news.py`

- **`collect_options.py`** - Collecte options Yahoo Finance
  - Calls, Puts, PCR, IV
  - Usage: `python3 collect_options.py`

- **`collect_companies.py`** - Module utilitaire
  - Fonctions: `save_articles()`, `load_existing_articles()`

### 2️⃣ **Analyse de Sentiment**
- **`analyze_sentiment.py`** - Analyse LLM avec Ollama (Llama3)
  - Analyse tous les articles collectés
  - Checkpointing automatique tous les 10 articles
  - Gestion gracieuse des interruptions (SIGTERM/SIGINT)
  - Usage: `python3 analyze_sentiment.py`

- **`sentiment_llm_relative.py`** - Moteur d'analyse LLM
  - Sentiment brut + ajustement contextuel
  - Détection d'impact financier

### 3️⃣ **Visualisation**
- **`dashboard_timeline.py`** - Dashboard d'évolution temporelle
  - Graphiques de sentiment dans le temps
  - Détection automatique d'événements (spikes/drops)
  - Moyennes mobiles
  - Port: 8501
  - Usage: `streamlit run dashboard_timeline.py --server.port 8501 --server.address 0.0.0.0`

- **`dashboard_companies.py`** - Dashboard comparatif
  - Vue d'ensemble du marché
  - Comparaison entre entreprises
  - Filtres par secteur et tendance

### 4️⃣ **Monitoring & Agrégation**
- **`monitor_analysis.py`** - Script CLI de monitoring
  - Affiche la progression de l'analyse
  - Statistiques par entreprise
  - Usage: `python3 monitor_analysis.py`

- **`aggregate_companies.py`** - Agrégation des données
  - Génère `companies_sentiment_summary.json`
  - Statistiques globales

### 5️⃣ **Détection de Tendances**
- **`trend_detection.py`** - Algorithmes de détection de tendances
  - Calcul des coefficients de tendance
  - Classification: improving/stable/declining

### 6️⃣ **Configuration**
- **`companies_config.py`** - Configuration des entreprises à suivre
  - Liste des tickers
  - Termes de recherche
  - Secteurs

## 🚀 Pipeline Complet

```bash
# 1. Collecter 100 jours de nouvelles
docker exec n8n_data_architect python3 /data/scripts/collect_news.py 100 10

# 2. Analyser le sentiment avec LLM
docker exec n8n_data_architect python3 /data/scripts/analyze_sentiment.py

# 3. Monitorer la progression
docker exec n8n_data_architect python3 /data/scripts/monitor_analysis.py

# 4. Agréger les résultats
docker exec n8n_data_architect python3 /data/scripts/aggregate_companies.py

# 5. Lancer le dashboard
docker exec -d n8n_data_architect sh -c "cd /data/scripts && streamlit run dashboard_timeline.py --server.port 8501 --server.address 0.0.0.0"
```

## 📁 Structure des Données

```
/data/files/
├── companies/
│   ├── NVDA_news.json
│   ├── MSFT_news.json
│   └── ...
└── companies_sentiment_summary.json
```

## ⚙️ Configuration Docker

Volumes mappés:
- `./prod:/data/scripts` - Scripts de production
- `./local_files:/data/files` - Données et résultats

Ports exposés:
- `8501` - Dashboard Streamlit
- `5678` - n8n
- `11434` - Ollama

## 🔄 Maintenance

- Les scripts supportent les exécutions incrémentales
- Checkpointing automatique pour les longues analyses
- Déduplication des articles par URL
