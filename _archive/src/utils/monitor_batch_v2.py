#!/usr/bin/env python3
"""
Moniteur en temps réel du batch loader v2
"""
import os
import json
from datetime import datetime

NEWS_DATA_DIR = '/data/files/companies'

tickers = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'AMD', 'INTC', 
           'AVGO', 'CRM', 'ORCL', 'ADBE', 'SNOW', 'PLTR', 'NOW']

print(f"\n{'='*80}")
print(f"📊 MONITORING BATCH LOADER V2 - {datetime.now().strftime('%H:%M:%S')}")
print(f"{'='*80}\n")

print(f"{'Ticker':<10} {'Articles':<10} {'Modifié':<20}")
print("-"*80)

for ticker in tickers:
    news_file = os.path.join(NEWS_DATA_DIR, f'{ticker}_news.json')
    
    if os.path.exists(news_file):
        try:
            # Lire le fichier
            with open(news_file, 'r') as f:
                data = json.load(f)
            
            # Compter articles
            articles = data.get('articles', []) if isinstance(data, dict) else data
            count = len(articles)
            
            # Date de modification
            mtime = os.path.getmtime(news_file)
            modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{ticker:<10} {count:<10} {modified:<20}")
        except Exception as e:
            print(f"{ticker:<10} ERROR: {str(e)[:30]}")
    else:
        print(f"{ticker:<10} {'N/A':<10} {'Fichier absent':<20}")

print("-"*80)
