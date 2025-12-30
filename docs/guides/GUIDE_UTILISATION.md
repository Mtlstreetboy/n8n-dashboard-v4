# 📊 Guide Complet - Dashboard d'Options

## 🎯 Objectif
Visualiser et analyser les données d'options (calls/puts) avec 5 vues innovantes pour détecter le sentiment du marché.

---

## 📋 Prérequis

### Installation
```powershell
# 1. Python 3.8+ installé
python --version

# 2. Docker Desktop en cours d'exécution
docker ps
```

---

## 🚀 Démarrage Rapide (3 étapes)

### Étape 1: Collecter les données d'options
```powershell
# Dans le container Docker
docker exec n8n_data_architect python3 /data/scripts/collect_options.py
```
**Durée:** 5-10 minutes pour tous les tickers  
**Résultat:** Fichiers CSV dans `/data/options_data/`

### Étape 2: Lancer le dashboard
```powershell
# Dashboard dans Docker
docker exec -d n8n_data_architect streamlit run /data/scripts/dashboard_options.py --server.port 8501 --server.address 0.0.0.0
```

### Étape 3: Accéder au dashboard
Ouvrir dans le navigateur:
```
http://localhost:8501
```

---

## 📊 Utilisation du Dashboard

### 1. Entrer un ticker
Dans le champ "Ticker", taper: `AAPL`, `NVDA`, `TSLA`, etc.

### 2. Cliquer "🔍 Analyser"
Le dashboard charge les données et calcule le score composite.

### 3. Explorer les 5 onglets

#### 📈 Volatility Smile
- Courbe d'IV (Implied Volatility) par strike
- Taille des points = volume
- Détecte la nervosité du marché

#### 🔥 Volume Heatmap
- Concentration calls (vert) vs puts (rouge)
- Identifie support/résistance

#### 📊 Open Interest Ladder
- Profondeur des positions
- Calcule le "Max Pain" (aimant de prix)

#### 💰 Money Flow
- Flux d'argent par zone (OTM, ATM, ITM)
- Suit le "smart money"

#### 🎯 3D Surface
- Vue tridimensionnelle (Strike × Expiration × Volume)
- Pattern recognition visuel

---

## 🔧 Configuration

### Tickers disponibles
Le script collecte automatiquement les options pour:
```
ADBE, AMD, AMZN, AVGO, CRM, GOOGL, INTC, META, 
MSFT, NOW, NVDA, ORCL, PLTR, SNOW, TSLA
```

### Ajouter un nouveau ticker
Éditer `prod/companies_config.py`:
```python
{
    'ticker': 'AAPL',
    'name': 'Apple Inc.',
    'sector': 'Technology'
}
```

Puis relancer la collecte:
```powershell
docker exec n8n_data_architect python3 /data/scripts/collect_options.py
```

---

## 🛠️ Dépannage

### Problème: "Aucune donnée d'options pour TICKER"
**Solution:**
```powershell
# Collecter manuellement ce ticker
docker exec n8n_data_architect python3 -c "import sys; sys.path.insert(0, '/data/scripts'); from collect_options import OptionsCollector; c=OptionsCollector(); c.get_options_data('AAPL')"
```

### Problème: Dashboard ne répond pas
**Solution:**
```powershell
# Vérifier que Streamlit tourne
docker exec n8n_data_architect ps aux | findstr streamlit

# Redémarrer si besoin
docker exec n8n_data_architect pkill -f streamlit
docker exec -d n8n_data_architect streamlit run /data/scripts/dashboard_options.py --server.port 8501 --server.address 0.0.0.0
```

### Problème: Port 8501 déjà utilisé
**Solution:**
```powershell
# Utiliser un autre port
docker exec -d n8n_data_architect streamlit run /data/scripts/dashboard_options.py --server.port 8505 --server.address 0.0.0.0
# Puis accéder à http://localhost:8505
```

---

## 📁 Structure des Fichiers

```
prod/
├── collect_options.py              # Collecteur de données (Yahoo Finance)
├── dashboard_options.py            # Dashboard Streamlit (5 vues)
├── test_options_dashboard.py       # Tests automatisés
└── companies_config.py             # Configuration des tickers

/data/options_data/ (dans le container)
├── AAPL_calls_20251210_025609.csv
├── AAPL_puts_20251210_025609.csv
├── AAPL_latest_sentiment.json
└── ...
```

---

## 🔄 Automatisation

### Collecte automatique toutes les heures
Éditer `prod/cron_daily_collect.sh`:
```bash
# Ajouter cette ligne
0 * * * * docker exec n8n_data_architect python3 /data/scripts/collect_options.py
```

---

## 📈 Interprétation du Score Composite

### Score Final
```
Options_Score = (
    Volatility_Skew × 25% +
    Max_Pain_Distance × 20% +
    Money_Flow_Ratio × 30% +
    Volume_Concentration × 25%
)
```

### Signaux
- **Score > 0.15** = 🚀 Bullish (calls dominants)
- **Score -0.15 à 0.15** = ⏸️ Neutral
- **Score < -0.15** = 📉 Bearish (puts dominants)

### Exemple
```
AAPL: Score = 0.28 (Bullish)
├─ Volatility Skew: 0.10 (puts légèrement chers)
├─ Max Pain Distance: -0.07 (prix au-dessus du max pain)
├─ Money Flow: 0.52 (flux vers calls)
└─ Volume Concentration: -0.02 (équilibré)

→ Interprétation: Spéculation haussière, momentum positif
```

---

## 🧪 Tests

Vérifier que tout fonctionne:
```powershell
docker exec n8n_data_architect python3 /data/scripts/test_options_dashboard.py
```

**Résultat attendu:** `5/5 tests passés (100%)`

---

## 📚 Ressources

- **Yahoo Finance API**: Source des données d'options
- **Streamlit**: Framework web pour les dashboards
- **Plotly**: Bibliothèque de visualisation interactive

---

## 💡 Conseils

1. **Actualiser les données**: Relancer `collect_options.py` avant l'analyse pour avoir des données fraîches
2. **Combiner avec News**: Utiliser `dashboard_sentiment.py` pour croiser options + actualités
3. **Volume minimum**: Ignorer les strikes avec volume < 100 (peu liquides)
4. **Expirations**: Court terme (< 30j) = momentum, Long terme = conviction

---

**Dernière mise à jour:** 2025-12-09  
**Version:** 1.0  
**Support:** Voir `test_options_dashboard.py` pour exemples d'utilisation
