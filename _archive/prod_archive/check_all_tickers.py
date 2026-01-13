#!/usr/bin/env python3
"""
Vérifier toutes les compagnies pour comprendre le problème
"""
import sys
sys.path.insert(0, '/data/scripts')

import json
import os
from datetime import datetime, timedelta, timezone
import numpy as np

NEWS_DATA_DIR = '/data/files/companies'
TICKERS = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'AMD']

print(f"\n{'='*100}")
print(f"🔍 ANALYSE COMPARATIVE - TOUTES LES COMPAGNIES")
print(f"{'='*100}\n")

results = []

for ticker in TICKERS:
    news_file = os.path.join(NEWS_DATA_DIR, f'{ticker}_news.json')
    
    if not os.path.exists(news_file):
        print(f"⚠️ {ticker}: fichier non trouvé")
        continue
    
    with open(news_file, 'r') as f:
        data = json.load(f)
    
    articles = data.get('articles', []) if isinstance(data, dict) else data
    
    # Analyser les dates
    cutoff = datetime.now() - timedelta(days=100)
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    
    recent_articles = []
    buckets = {'0-7d': 0, '7-14d': 0, '14-30d': 0, '30-60d': 0, '60-100d': 0}
    
    for article in articles:
        pub_date_str = article.get('published_at', '')
        try:
            pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            
            if pub_date >= cutoff:
                days_ago = (datetime.now(timezone.utc) - pub_date).total_seconds() / 86400
                
                llm_data = article.get('llm_sentiment', {})
                if llm_data and 'sentiment_score' in llm_data:
                    raw_score = llm_data.get('sentiment_score', 0)
                    sentiment_score = np.clip(raw_score / 100.0, -1, 1)
                    
                    recent_articles.append({
                        'days_ago': days_ago,
                        'score': sentiment_score
                    })
                    
                    # Bucketing
                    if days_ago <= 7:
                        buckets['0-7d'] += 1
                    elif days_ago <= 14:
                        buckets['7-14d'] += 1
                    elif days_ago <= 30:
                        buckets['14-30d'] += 1
                    elif days_ago <= 60:
                        buckets['30-60d'] += 1
                    else:
                        buckets['60-100d'] += 1
        except:
            continue
    
    # Calculer momentum
    recent_7d = [a for a in recent_articles if a['days_ago'] <= 7]
    older_7_14d = [a for a in recent_articles if 7 < a['days_ago'] <= 14]
    
    if recent_7d and older_7_14d:
        recent_sentiment = np.mean([a['score'] for a in recent_7d])
        older_sentiment = np.mean([a['score'] for a in older_7_14d])
        momentum = (recent_sentiment - older_sentiment) * 2
        momentum = np.clip(momentum, -1, 1)
    else:
        momentum = 0
    
    # Calculer fear/greed
    positive = [a for a in recent_articles if a['score'] > 0]
    negative = [a for a in recent_articles if a['score'] < 0]
    
    if positive and negative:
        avg_pos = np.mean([a['score'] for a in positive])
        avg_neg = np.mean([abs(a['score']) for a in negative])
        
        if avg_neg > avg_pos * 1.3:
            fear_greed = -0.15
        elif avg_pos > avg_neg * 1.3:
            fear_greed = 0.10
        else:
            fear_greed = 0
    else:
        fear_greed = 0
    
    results.append({
        'ticker': ticker,
        'total': len(articles),
        'recent': len(recent_articles),
        'buckets': buckets,
        'momentum': momentum,
        'fear_greed': fear_greed,
        'pos_count': len(positive),
        'neg_count': len(negative)
    })

# Afficher le tableau
print(f"{'Ticker':<8} {'Total':<8} {'Recent':<8} {'0-7d':<8} {'7-14d':<8} {'14-30d':<8} {'30+d':<8} {'Momentum':<12} {'Fear/Greed':<12}")
print(f"{'-'*100}")

for r in results:
    b = r['buckets']
    print(f"{r['ticker']:<8} {r['total']:<8} {r['recent']:<8} {b['0-7d']:<8} {b['7-14d']:<8} {b['14-30d']:<8} {b['30-60d']+b['60-100d']:<8} {r['momentum']:+.4f}      {r['fear_greed']:+.4f}")

print(f"\n{'='*100}")
print("DIAGNOSTIC")
print(f"{'='*100}\n")

# Vérifier si le pattern est identique partout
all_zero_14_30d = all(r['buckets']['14-30d'] == 0 for r in results)
all_zero_30plus = all(r['buckets']['30-60d'] + r['buckets']['60-100d'] == 0 for r in results)

if all_zero_14_30d and all_zero_30plus:
    print("❌ PROBLÈME DÉTECTÉ: TOUTES les compagnies ont 0 articles entre 14-100 jours")
    print("   Cela signifie que:")
    print("   1. Le collecteur de nouvelles a été lancé il y a ~14 jours seulement")
    print("   2. OU les anciennes nouvelles ont été supprimées")
    print("   3. OU il y a un bug dans le filtrage temporel")
    
    # Vérifier la première hypothèse
    earliest_dates = []
    for r in results:
        ticker = r['ticker']
        news_file = os.path.join(NEWS_DATA_DIR, f'{ticker}_news.json')
        with open(news_file, 'r') as f:
            data = json.load(f)
        articles = data.get('articles', []) if isinstance(data, dict) else data
        
        dates = []
        for article in articles:
            pub_date_str = article.get('published_at', '')
            try:
                pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                dates.append(pub_date)
            except:
                pass
        
        if dates:
            oldest = min(dates)
            days_since_oldest = (datetime.now(timezone.utc) - oldest).days
            earliest_dates.append({'ticker': ticker, 'oldest_date': oldest, 'days': days_since_oldest})
    
    print(f"\n📅 DATES DES ARTICLES LES PLUS ANCIENS:")
    for item in sorted(earliest_dates, key=lambda x: x['days'], reverse=True):
        print(f"   {item['ticker']:<8}: {item['oldest_date'].strftime('%Y-%m-%d')} ({item['days']} jours)")
    
    avg_oldest = sum(item['days'] for item in earliest_dates) / len(earliest_dates)
    print(f"\n   📊 Moyenne: {avg_oldest:.1f} jours")
    
    if avg_oldest < 20:
        print(f"\n✅ CONFIRMATION: Le collecteur a été lancé il y a environ {avg_oldest:.0f} jours")
        print("   C'est NORMAL que momentum et fear/greed soient faibles/nuls.")
        print("   Solution: Attendre que plus de données historiques s'accumulent.")
    else:
        print(f"\n⚠️ Les articles remontent à {avg_oldest:.0f} jours mais sont tous dans la fenêtre 0-14j")
        print("   Il y a probablement un problème de collecte ou de filtrage.")

else:
    print("✅ La distribution temporelle varie entre les compagnies (NORMAL)")

print(f"\n{'='*100}\n")
