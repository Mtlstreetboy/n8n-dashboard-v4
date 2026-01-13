#!/usr/bin/env python3
"""
Script de debug pour analyser momentum et fear/greed
"""
import sys
sys.path.insert(0, '/data/scripts')

import json
import os
from datetime import datetime, timedelta
import numpy as np

NEWS_DATA_DIR = '/data/files/companies'
TICKER = 'NVDA'

print(f"\n{'='*80}")
print(f"🔍 DEBUG MOMENTUM & FEAR/GREED - {TICKER}")
print(f"{'='*80}\n")

# 1. Charger les nouvelles
news_file = os.path.join(NEWS_DATA_DIR, f'{TICKER}_news.json')
with open(news_file, 'r') as f:
    data = json.load(f)

articles = data.get('articles', []) if isinstance(data, dict) else data
print(f"📰 Total articles: {len(articles)}")

# 2. Analyser les articles récents (100 derniers jours)
cutoff = datetime.now() - timedelta(days=100)
from datetime import timezone
if cutoff.tzinfo is None:
    cutoff = cutoff.replace(tzinfo=timezone.utc)

recent_articles = []
for article in articles:
    pub_date_str = article.get('published_at', '')
    try:
        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
        
        if pub_date >= cutoff:
            llm_data = article.get('llm_sentiment', {})
            if llm_data and 'sentiment_score' in llm_data:
                raw_score = llm_data.get('sentiment_score', 0)
                sentiment_score = np.clip(raw_score / 100.0, -1, 1)
                confidence = llm_data.get('confidence', 0.7)
                
                days_ago = (datetime.now(timezone.utc) - pub_date).total_seconds() / 86400
                
                recent_articles.append({
                    'date': pub_date,
                    'days_ago': days_ago,
                    'score': sentiment_score,
                    'confidence': confidence,
                    'title': article.get('title', '')[:60]
                })
    except:
        continue

recent_articles.sort(key=lambda x: x['days_ago'])

print(f"📰 Articles récents (<100 jours): {len(recent_articles)}")
print(f"\n{'='*80}")
print("ANALYSE MOMENTUM NARRATIF")
print(f"{'='*80}")

# 3. Calculer momentum (7 jours vs 7-14 jours)
momentum_window = 7
now = datetime.now(timezone.utc)

recent_7d = [a for a in recent_articles if a['days_ago'] <= momentum_window]
older_7_14d = [a for a in recent_articles if momentum_window < a['days_ago'] <= momentum_window * 2]

print(f"\n🔵 Articles derniers 7 jours: {len(recent_7d)}")
if recent_7d:
    print("   Échantillon:")
    for a in recent_7d[:5]:
        print(f"   - {a['days_ago']:.1f}j: {a['score']:+.3f} (conf: {a['confidence']:.2f}) | {a['title']}")
    recent_sentiment = np.mean([a['score'] * a['confidence'] for a in recent_7d])
    print(f"\n   📊 Sentiment moyen pondéré: {recent_sentiment:+.4f}")
else:
    print("   ⚠️ AUCUN article dans les 7 derniers jours!")
    recent_sentiment = 0

print(f"\n🟡 Articles entre 7-14 jours: {len(older_7_14d)}")
if older_7_14d:
    print("   Échantillon:")
    for a in older_7_14d[:5]:
        print(f"   - {a['days_ago']:.1f}j: {a['score']:+.3f} (conf: {a['confidence']:.2f}) | {a['title']}")
    older_sentiment = np.mean([a['score'] * a['confidence'] for a in older_7_14d])
    print(f"\n   📊 Sentiment moyen pondéré: {older_sentiment:+.4f}")
else:
    print("   ⚠️ AUCUN article entre 7-14 jours!")
    older_sentiment = 0

print(f"\n{'='*40}")
if recent_7d and older_7_14d:
    momentum = (recent_sentiment - older_sentiment) * 2
    momentum = np.clip(momentum, -1, 1)
    print(f"🚀 MOMENTUM = ({recent_sentiment:.4f} - {older_sentiment:.4f}) * 2 = {momentum:+.4f}")
else:
    momentum = 0
    print(f"🚀 MOMENTUM = 0.0 (pas assez de données dans les fenêtres)")
    if not recent_7d:
        print("   ❌ Problème: Aucun article récent dans les 7 derniers jours")
    if not older_7_14d:
        print("   ❌ Problème: Aucun article dans la fenêtre 7-14 jours")

print(f"\n{'='*80}")
print("ANALYSE FEAR/GREED ASYMMETRY")
print(f"{'='*80}")

# 4. Analyser fear/greed asymmetry
positive_articles = [a for a in recent_articles if a['score'] > 0]
negative_articles = [a for a in recent_articles if a['score'] < 0]
neutral_articles = [a for a in recent_articles if a['score'] == 0]

print(f"\n📈 Articles POSITIFS: {len(positive_articles)}")
print(f"📉 Articles NÉGATIFS: {len(negative_articles)}")
print(f"➖ Articles NEUTRES: {len(neutral_articles)}")

if positive_articles:
    avg_positive = np.mean([a['score'] for a in positive_articles])
    print(f"\n   📊 Sentiment positif moyen: {avg_positive:.4f}")
    print("   Top 5 articles positifs:")
    sorted_pos = sorted(positive_articles, key=lambda x: x['score'], reverse=True)
    for a in sorted_pos[:5]:
        print(f"   - {a['score']:+.3f} ({a['days_ago']:.1f}j) | {a['title']}")
else:
    avg_positive = 0
    print("   ⚠️ AUCUN article positif!")

if negative_articles:
    avg_negative = np.mean([abs(a['score']) for a in negative_articles])
    print(f"\n   📊 Sentiment négatif moyen (absolu): {avg_negative:.4f}")
    print("   Top 5 articles négatifs:")
    sorted_neg = sorted(negative_articles, key=lambda x: x['score'])
    for a in sorted_neg[:5]:
        print(f"   - {a['score']:+.3f} ({a['days_ago']:.1f}j) | {a['title']}")
else:
    avg_negative = 0
    print("   ⚠️ AUCUN article négatif!")

print(f"\n{'='*40}")
if positive_articles or negative_articles:
    if avg_negative > avg_positive * 1.3:
        fear_greed = -0.15
        print(f"😨 PEUR DOMINE: négatif ({avg_negative:.4f}) > positif ({avg_positive:.4f}) * 1.3")
        print(f"   Fear/Greed = -0.15")
    elif avg_positive > avg_negative * 1.3:
        fear_greed = 0.10
        print(f"🤑 GREED DOMINE: positif ({avg_positive:.4f}) > négatif ({avg_negative:.4f}) * 1.3")
        print(f"   Fear/Greed = +0.10")
    else:
        fear_greed = 0
        print(f"⚖️ ÉQUILIBRE: positif ({avg_positive:.4f}) vs négatif ({avg_negative:.4f})")
        print(f"   Fear/Greed = 0.0")
else:
    fear_greed = 0
    print("⚠️ AUCUNE donnée positive ou négative pour calculer l'asymétrie")

print(f"\n{'='*80}")
print("DISTRIBUTION TEMPORELLE DES ARTICLES")
print(f"{'='*80}\n")

# 5. Distribution par tranche de temps
buckets = {
    '0-7d': 0, '7-14d': 0, '14-30d': 0, '30-60d': 0, '60-100d': 0
}

for a in recent_articles:
    d = a['days_ago']
    if d <= 7:
        buckets['0-7d'] += 1
    elif d <= 14:
        buckets['7-14d'] += 1
    elif d <= 30:
        buckets['14-30d'] += 1
    elif d <= 60:
        buckets['30-60d'] += 1
    else:
        buckets['60-100d'] += 1

for period, count in buckets.items():
    bar = '█' * (count // 5) if count > 0 else ''
    print(f"{period:10s}: {count:4d} articles {bar}")

print(f"\n{'='*80}")
print("DIAGNOSTIC")
print(f"{'='*80}\n")

issues = []
if momentum == 0:
    if not recent_7d:
        issues.append("❌ MOMENTUM = 0 car AUCUN article dans les 7 derniers jours")
    elif not older_7_14d:
        issues.append("❌ MOMENTUM = 0 car AUCUN article dans la période 7-14 jours")
    else:
        issues.append("✅ MOMENTUM = 0 car sentiment identique entre les deux périodes")

if fear_greed == 0:
    if not positive_articles and not negative_articles:
        issues.append("❌ FEAR/GREED = 0 car AUCUN article positif ou négatif")
    else:
        issues.append("✅ FEAR/GREED = 0 car équilibre entre positif et négatif")

if len(recent_7d) == 0:
    issues.append("⚠️ PROBLÈME MAJEUR: Distribution temporelle déséquilibrée - aucun article récent")

for issue in issues:
    print(issue)

print(f"\n{'='*80}")
print("RECOMMANDATIONS")
print(f"{'='*80}\n")

if len(recent_7d) == 0:
    print("🔧 Le problème principal est que les articles ne sont pas assez récents.")
    print("   Solutions possibles:")
    print("   1. Augmenter la fenêtre de momentum (ex: 14 jours au lieu de 7)")
    print("   2. Vérifier que le collecteur de nouvelles fonctionne correctement")
    print("   3. Utiliser une période d'analyse plus longue (ex: 30 jours)")

print(f"\n{'='*80}\n")
