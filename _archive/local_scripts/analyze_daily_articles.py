#!/usr/bin/env python3
"""
Analyse la distribution quotidienne des articles par compagnie
"""
import json
import os
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from collections import defaultdict

DATA_DIR = '/data/files/companies'

def analyze_daily_distribution():
    """Analyse combien d'articles par jour pour chaque compagnie"""
    
    cutoff = datetime(2025, 8, 30, tzinfo=timezone.utc)
    companies_daily = {}
    
    # Charge tous les articles
    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith('_news.json'):
            continue
        
        ticker = filename.replace('_news.json', '')
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('articles', [])
        daily_count = defaultdict(int)
        
        for article in articles:
            try:
                pub_date = parsedate_to_datetime(article.get('published_at', ''))
                if pub_date >= cutoff:
                    daily_count[pub_date.date()] += 1
            except:
                continue
        
        if daily_count:
            companies_daily[ticker] = daily_count
    
    # Analyse et affichage
    print("=" * 100)
    print("ANALYSE QUOTIDIENNE DES ARTICLES (100 derniers jours)")
    print("=" * 100)
    
    results = []
    for ticker, daily_count in companies_daily.items():
        if not daily_count:
            continue
        
        total = sum(daily_count.values())
        num_days = len(daily_count)
        avg_per_day = total / num_days if num_days > 0 else 0
        max_day = max(daily_count.values())
        min_day = min(daily_count.values())
        
        results.append({
            'ticker': ticker,
            'total': total,
            'days_with_articles': num_days,
            'avg_per_day': avg_per_day,
            'max_day': max_day,
            'min_day': min_day,
            'missing_to_180': max(0, 180 - total)
        })
    
    # Trie par moyenne croissante
    results.sort(key=lambda x: x['avg_per_day'])
    
    print("\nCompagnies necessitant plus d'articles (< 1.5/jour):")
    print("-" * 100)
    print(f"{'Ticker':<12} {'Total':<7} {'Jours':<7} {'Moy/j':<8} {'Min':<6} {'Max':<6} {'Manque 180':<12}")
    print("-" * 100)
    
    for r in results:
        if r['avg_per_day'] < 1.5:
            print(f"{r['ticker']:<12} {r['total']:<7} {r['days_with_articles']:<7} {r['avg_per_day']:<8.2f} "
                  f"{r['min_day']:<6} {r['max_day']:<6} {r['missing_to_180']:<12}")
    
    print("\n" + "=" * 100)
    print("Compagnies avec bonne couverture (>= 1.5/jour):")
    print("-" * 100)
    
    for r in results:
        if r['avg_per_day'] >= 1.5:
            print(f"{r['ticker']:<12} {r['total']:<7} {r['days_with_articles']:<7} {r['avg_per_day']:<8.2f} "
                  f"{r['min_day']:<6} {r['max_day']:<6} {r['missing_to_180']:<12}")
    
    print("\n" + "=" * 100)
    print("RECOMMANDATION:")
    print("=" * 100)
    
    weak_companies = [r for r in results if r['avg_per_day'] < 1.5]
    if weak_companies:
        print(f"\n{len(weak_companies)} compagnies necessitent plus d'articles.")
        print("\nAction recommandee:")
        print("1. Relancer la collecte avec max_results=20 (actuellement 15)")
        print("2. Etendre la periode de recherche (actuellement 1 jour par requete)")
        print("3. Ajouter plus de search terms dans companies_config.py")
        print("\nCompagnies prioritaires (< 1.0/jour):")
        for r in weak_companies:
            if r['avg_per_day'] < 1.0:
                print(f"  - {r['ticker']}: {r['avg_per_day']:.2f}/jour (manque {r['missing_to_180']} articles)")

if __name__ == '__main__':
    analyze_daily_distribution()
