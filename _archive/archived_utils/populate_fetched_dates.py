#!/usr/bin/env python3
"""
Script pour historiser toutes les dates déjà collectées
Évite de refetch inutilement les 160 jours déjà tentés
"""
import json
import os
from datetime import datetime, timedelta

NEWS_DATA_DIR = '/data/files/companies'

def populate_fetched_dates():
    """Populate fetched_dates pour toutes les compagnies"""
    
    files = [f for f in os.listdir(NEWS_DATA_DIR) if f.endswith('_news.json') and 'backup' not in f]
    
    print("📊 Analyse et historisation des dates collectées\n")
    print(f"{'Ticker':<12} | Articles | Dates | Plage")
    print("=" * 70)
    
    for filename in sorted(files):
        filepath = os.path.join(NEWS_DATA_DIR, filename)
        ticker = filename.replace('_news.json', '')
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extraire toutes les dates des articles
        article_dates = set()
        for article in data.get('articles', []):
            pub = article.get('published_at', '')
            if pub and len(pub) >= 10:
                article_dates.add(pub[:10])
        
        if article_dates:
            min_date = min(article_dates)
            max_date = max(article_dates)
            
            # Générer toutes les dates entre min et max (160 jours depuis max)
            max_date_obj = datetime.strptime(max_date, '%Y-%m-%d')
            fetched_dates = []
            
            for i in range(160):
                date_obj = max_date_obj - timedelta(days=i)
                fetched_dates.append(date_obj.strftime('%Y-%m-%d'))
            
            # Sauvegarder
            data['fetched_dates'] = sorted(fetched_dates)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"{ticker:<12} | {len(data['articles']):8} | {len(article_dates):5} | {min_date} → {max_date} ✅")
        else:
            print(f"{ticker:<12} | {len(data.get('articles', [])):8} | {'0':>5} | Aucune date")
    
    print("\n✅ Historisation terminée - Delta mode prêt!")

if __name__ == '__main__':
    populate_fetched_dates()
