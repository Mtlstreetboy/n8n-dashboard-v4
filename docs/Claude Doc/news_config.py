{
  "settings": {
    "days_back": 40,
    "news_per_day": 20,
    "output_file": "stock_news.json",
    "update_interval_hours": 24,
    "language": "fr",
    "country": "CA"
  },
  "tickers": [
    {
      "symbol": "NVDA",
      "name": "Nvidia",
      "enabled": true,
      "sources": ["yahoo", "google"]
    },
    {
      "symbol": "AMD",
      "name": "AMD",
      "enabled": true,
      "sources": ["yahoo", "google"]
    },
    {
      "symbol": "INTC",
      "name": "Intel",
      "enabled": true,
      "sources": ["yahoo", "google"]
    },
    {
      "symbol": "TSLA",
      "name": "Tesla",
      "enabled": false,
      "sources": ["yahoo", "google"]
    },
    {
      "symbol": "AAPL",
      "name": "Apple",
      "enabled": false,
      "sources": ["yahoo", "google"]
    },
    {
      "symbol": "MSFT",
      "name": "Microsoft",
      "enabled": false,
      "sources": ["yahoo", "google"]
    },
    {
      "symbol": "GOOGL",
      "name": "Google",
      "enabled": false,
      "sources": ["yahoo", "google"]
    },
    {
      "symbol": "AMZN",
      "name": "Amazon",
      "enabled": false,
      "sources": ["yahoo", "google"]
    },
    {
      "symbol": "META",
      "name": "Meta",
      "enabled": false,
      "sources": ["yahoo", "google"]
    }
  ],
  "sources": {
    "yahoo": {
      "enabled": true,
      "priority": 1
    },
    "google": {
      "enabled": true,
      "priority": 2
    },
    "reuters": {
      "enabled": false,
      "priority": 3
    }
  },
  "filters": {
    "min_title_length": 10,
    "exclude_keywords": ["advertisement", "sponsored"],
    "languages": ["fr", "en"]
  }
}