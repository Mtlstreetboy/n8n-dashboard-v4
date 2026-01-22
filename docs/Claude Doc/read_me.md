# 📰 Stock News Scraper

Scraper automatique de nouvelles financières depuis **Yahoo Finance** et **Google News** avec configuration flexible.

## 🚀 Installation

### 1. Cloner/Créer le projet
```bash
mkdir stock-news-scraper
cd stock-news-scraper
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

## 📁 Structure du projet

```
stock-news-scraper/
├── news_scraper.py      # Script principal
├── config.json          # Configuration
├── requirements.txt     # Dépendances Python
├── stock_news.json      # Sortie (généré)
└── README.md           # Ce fichier
```

## ⚙️ Configuration (config.json)

### Settings globaux
```json
{
  "settings": {
    "days_back": 40,              // Nombre de jours à scraper
    "news_per_day": 20,           // Limite par jour
    "output_file": "stock_news.json",
    "language": "fr",             // Langue (fr, en)
    "country": "CA"               // Pays (CA, US, FR)
  }
}
```

### Ajouter des tickers
```json
{
  "tickers": [
    {
      "symbol": "NVDA",           // Symbole ticker
      "name": "Nvidia",           // Nom compagnie
      "enabled": true,            // Activer/désactiver
      "sources": ["yahoo", "google"]  // Sources à utiliser
    }
  ]
}
```

### Sources disponibles
- `yahoo` : Yahoo Finance (via yfinance)
- `google` : Google News RSS
- `reuters` : Reuters (à implémenter)

### Filtres
```json
{
  "filters": {
    "min_title_length": 10,
    "exclude_keywords": ["advertisement", "sponsored"],
    "languages": ["fr", "en"]
  }
}
```

## 🎯 Utilisation

### Lancement simple
```bash
python news_scraper.py
```

### Exemple de sortie
```
============================================================
  📰 STOCK NEWS SCRAPER 📰
============================================================
✅ Configuration chargée depuis config.json

🚀 Démarrage du scraping pour 3 tickers...
📅 Période: 40 derniers jours

📈 Nvidia (NVDA)
  📊 Yahoo Finance: NVDA...
    ✅ 15 nouvelles récupérées
  🔍 Google News: NVDA...
    ✅ 18 nouvelles récupérées

📈 AMD (AMD)
  📊 Yahoo Finance: AMD...
    ✅ 12 nouvelles récupérées
  🔍 Google News: AMD...
    ✅ 16 nouvelles récupérées

============================================================
📊 STATISTIQUES
============================================================

📈 Nouvelles par ticker:
  NVDA: 33 nouvelles
  AMD: 28 nouvelles
  INTC: 25 nouvelles

📰 Nouvelles par source:
  Yahoo Finance: 42 nouvelles
  Google News: 44 nouvelles

📅 Couverture: 38 jours différents
📊 Moyenne: 2.3 nouvelles/jour
============================================================

💾 Données sauvegardées dans stock_news.json
📊 Total: 86 nouvelles

✅ Terminé!
```

## 📊 Format de sortie JSON

```json
{
  "metadata": {
    "generated_at": "2025-01-06 15:30:00",
    "total_news": 86,
    "tickers": ["NVDA", "AMD", "INTC"],
    "days_covered": 40
  },
  "news": [
    {
      "ticker": "NVDA",
      "company": "Nvidia",
      "title": "Nvidia annonce ses résultats Q4",
      "publisher": "Bloomberg",
      "link": "https://...",
      "publish_date": "2025-01-05",
      "publish_time": "14:30:00",
      "type": "news",
      "source": "Yahoo Finance",
      "thumbnail": "https://..."
    }
  ]
}
```

## 💡 Exemples d'utilisation

### Suivre uniquement les semi-conducteurs
```json
{
  "tickers": [
    {"symbol": "NVDA", "name": "Nvidia", "enabled": true},
    {"symbol": "AMD", "name": "AMD", "enabled": true},
    {"symbol": "INTC", "name": "Intel", "enabled": true}
  ]
}
```

### Suivre les FAANG
```json
{
  "tickers": [
    {"symbol": "META", "name": "Meta", "enabled": true},
    {"symbol": "AAPL", "name": "Apple", "enabled": true},
    {"symbol": "AMZN", "name": "Amazon", "enabled": true},
    {"symbol": "NFLX", "name": "Netflix", "enabled": true},
    {"symbol": "GOOGL", "name": "Google", "enabled": true}
  ]
}
```

### Uniquement Google News (pas Yahoo)
```json
{
  "sources": {
    "yahoo": {"enabled": false},
    "google": {"enabled": true}
  }
}
```

## 🔧 Personnalisation

### Changer la période
Modifiez `days_back` dans `config.json`:
```json
"days_back": 90  // 90 derniers jours
```

### Limiter le nombre de nouvelles
```json
"news_per_day": 10  // 10 nouvelles max par jour
```

### Automatisation (cron)
Linux/Mac - Ajoutez à crontab:
```bash
# Tous les jours à 8h
0 8 * * * cd /chemin/vers/stock-news-scraper && python news_scraper.py
```

Windows - Créez un script batch:
```batch
@echo off
cd C:\chemin\vers\stock-news-scraper
python news_scraper.py
```

## 🐛 Dépannage

### Erreur 403 (Google News)
- Ajoutez un délai entre les requêtes
- Utilisez un VPN si bloqué

### Pas de nouvelles Yahoo Finance
- Vérifiez que le ticker est valide
- Essayez un autre ticker pour tester

### Encodage des caractères
Le script utilise UTF-8 par défaut. Si problème:
```python
# Dans save_to_json()
json.dump(output_data, f, ensure_ascii=False, indent=2)
```

## 📝 Notes

- **Rate Limiting**: Un délai de 1s est ajouté entre chaque requête Google News
- **Données Yahoo**: Limitées aux ~15-20 dernières nouvelles par ticker
- **Google News**: Plus de couverture historique mais parfois moins détaillé

## 🚀 Améliorations futures

- [ ] Support Reuters API
- [ ] Support Bloomberg
- [ ] Base de données SQLite
- [ ] Dashboard web
- [ ] Alertes email
- [ ] Analyse de sentiment
- [ ] Export CSV/Excel

## 📄 Licence

Libre d'utilisation. Les données appartiennent à leurs sources respectives.

---

**Bon scraping! 📈**