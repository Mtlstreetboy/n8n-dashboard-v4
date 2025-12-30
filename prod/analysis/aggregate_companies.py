# -*- coding: utf-8 -*-
"""
Agregation des donnees de sentiment par compagnie
Calcule statistiques, tendances, et detecte changements significatifs
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = "/data/files"
COMPANIES_DIR = os.path.join(DATA_DIR, "companies")
OUTPUT_FILE = os.path.join(DATA_DIR, "companies_sentiment_summary.json")

def load_company_data(ticker):
    """Charge les donnees d'une compagnie"""
    filepath = os.path.join(COMPANIES_DIR, f"{ticker}_news.json")
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_company_metrics(data):
    """
    Calcule toutes les metriques pour une compagnie
    """
    ticker = data['ticker']
    company_name = data['company_name']
    articles = data['articles']
    
    # Filtrer articles avec sentiment
    analyzed_articles = [a for a in articles if 'sentiment_adjusted' in a]
    
    if not analyzed_articles:
        return None
    
    # Trier par date
    analyzed_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
    
    # Sentiment global (normalise de -100/+100 vers -1/+1)
    sentiments = [a['sentiment_adjusted'] / 100.0 for a in analyzed_articles]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
    
    # Distribution
    positive_count = sum(1 for s in sentiments if s > 0.15)
    negative_count = sum(1 for s in sentiments if s < -0.15)
    neutral_count = len(sentiments) - positive_count - negative_count
    
    # Sentiment par periode
    now = datetime.now()
    cutoff_7d = (now - timedelta(days=7)).isoformat()
    cutoff_30d = (now - timedelta(days=30)).isoformat()
    
    articles_7d = [a for a in analyzed_articles if a.get('published_at', '') >= cutoff_7d]
    articles_30d = [a for a in analyzed_articles if a.get('published_at', '') >= cutoff_30d]
    
    sentiments_7d = [a['financial_sentiment_index'] for a in articles_7d]
    sentiments_30d = [a['financial_sentiment_index'] for a in articles_30d]
    
    avg_7d = sum(sentiments_7d) / len(sentiments_7d) if sentiments_7d else avg_sentiment
    avg_30d = sum(sentiments_30d) / len(sentiments_30d) if sentiments_30d else avg_sentiment
    
    # Tendance (7d vs 30d)
    trend = avg_7d - avg_30d
    
    if trend > 0.05:
        trend_label = "improving"
    elif trend < -0.05:
        trend_label = "declining"
    else:
        trend_label = "stable"
    
    # Volatilite (std deviation)
    if len(sentiments_7d) > 1:
        mean_7d = sum(sentiments_7d) / len(sentiments_7d)
        variance = sum((s - mean_7d) ** 2 for s in sentiments_7d) / len(sentiments_7d)
        volatility = variance ** 0.5
    else:
        volatility = 0.0
    
    # Top articles positifs/negatifs
    top_positive = sorted(analyzed_articles, key=lambda x: x.get('financial_sentiment_index', 0), reverse=True)[:3]
    top_negative = sorted(analyzed_articles, key=lambda x: x.get('financial_sentiment_index', 0))[:3]
    
    # Articles recents
    recent_articles = analyzed_articles[:5]
    
    # Key themes (depuis articles avec LLM)
    all_themes = []
    for article in analyzed_articles:
        themes = article.get('key_themes', [])
        if themes:
            all_themes.extend(themes)
    
    # Compter themes
    theme_counts = {}
    for theme in all_themes:
        theme_counts[theme] = theme_counts.get(theme, 0) + 1
    
    # Top themes
    top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'ticker': ticker,
        'company_name': company_name,
        'sector': data.get('articles', [{}])[0].get('sector', 'Unknown') if data.get('articles') else 'Unknown',
        
        # Counts
        'total_articles': len(articles),
        'analyzed_articles': len(analyzed_articles),
        'articles_7d': len(articles_7d),
        'articles_30d': len(articles_30d),
        
        # Sentiment
        'avg_sentiment': round(avg_sentiment, 3),
        'avg_sentiment_7d': round(avg_7d, 3),
        'avg_sentiment_30d': round(avg_30d, 3),
        
        # Trend
        'trend_delta': round(trend, 3),
        'trend_label': trend_label,
        'volatility_7d': round(volatility, 3),
        
        # Distribution
        'positive_count': positive_count,
        'neutral_count': neutral_count,
        'negative_count': negative_count,
        'positive_pct': round(positive_count / len(sentiments) * 100, 1) if sentiments else 0.0,
        'negative_pct': round(negative_count / len(sentiments) * 100, 1) if sentiments else 0.0,
        
        # Top articles
        'top_positive_articles': [
            {
                'title': a['title'][:80],
                'sentiment': a['financial_sentiment_index'],
                'date': a.get('published_at', '')[:10],
                'url': a.get('url', '')
            }
            for a in top_positive
        ],
        'top_negative_articles': [
            {
                'title': a['title'][:80],
                'sentiment': a['financial_sentiment_index'],
                'date': a.get('published_at', '')[:10],
                'url': a.get('url', '')
            }
            for a in top_negative
        ],
        
        # Recent
        'recent_articles': [
            {
                'title': a['title'][:80],
                'sentiment': a['financial_sentiment_index'],
                'date': a.get('published_at', '')[:10]
            }
            for a in recent_articles
        ],
        
        # Themes
        'top_themes': [{'theme': theme, 'count': count} for theme, count in top_themes],
        
        # Metadata
        'last_update': data.get('last_update', ''),
        'last_sentiment_analysis': data.get('last_sentiment_analysis', '')
    }

def aggregate_all_companies():
    """Agrege toutes les compagnies"""
    
    print("\n" + "="*70)
    print("AGGREGATING COMPANY SENTIMENT DATA")
    print("="*70 + "\n")
    
    # Lister toutes les compagnies
    json_files = [f for f in os.listdir(COMPANIES_DIR) if f.endswith('_news.json')]
    tickers = [f.replace('_news.json', '') for f in json_files]
    
    companies_summary = []
    
    for ticker in tickers:
        print(f"Processing {ticker}...")
        data = load_company_data(ticker)
        
        if data:
            metrics = calculate_company_metrics(data)
            if metrics:
                companies_summary.append(metrics)
    
    # Trier par sentiment moyen
    companies_summary.sort(key=lambda x: x['avg_sentiment'], reverse=True)
    
    # Calculer statistiques globales
    if companies_summary:
        global_stats = {
            'total_companies': len(companies_summary),
            'total_articles': sum(c['total_articles'] for c in companies_summary),
            'total_analyzed': sum(c['analyzed_articles'] for c in companies_summary),
            'avg_sentiment_all': round(sum(c['avg_sentiment'] for c in companies_summary) / len(companies_summary), 3),
            'most_positive': companies_summary[0]['ticker'] if companies_summary else None,
            'most_negative': companies_summary[-1]['ticker'] if companies_summary else None,
            'improving_count': sum(1 for c in companies_summary if c['trend_label'] == 'improving'),
            'declining_count': sum(1 for c in companies_summary if c['trend_label'] == 'declining'),
            'stable_count': sum(1 for c in companies_summary if c['trend_label'] == 'stable')
        }
    else:
        global_stats = {}
    
    # Sauvegarder
    summary_data = {
        'generated_at': datetime.now().isoformat(),
        'global_stats': global_stats,
        'companies': companies_summary
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    # Afficher resume
    print("\n" + "="*70)
    print("AGGREGATION COMPLETE")
    print("="*70)
    
    if global_stats:
        print(f"\nGlobal Statistics:")
        print(f"  Total Companies: {global_stats['total_companies']}")
        print(f"  Total Articles: {global_stats['total_articles']}")
        print(f"  Articles Analyzed: {global_stats['total_analyzed']}")
        print(f"  Average Sentiment: {global_stats['avg_sentiment_all']:+.3f}")
        print(f"  Most Positive: {global_stats['most_positive']}")
        print(f"  Most Negative: {global_stats['most_negative']}")
        print(f"  Trends - Improving: {global_stats['improving_count']}, "
              f"Stable: {global_stats['stable_count']}, "
              f"Declining: {global_stats['declining_count']}")
    
    print(f"\n\nTop 10 Companies by Sentiment:")
    for i, company in enumerate(companies_summary[:10], 1):
        emoji = "📈" if company['avg_sentiment'] > 0.15 else "📉" if company['avg_sentiment'] < -0.15 else "➖"
        trend_emoji = "⬆" if company['trend_label'] == 'improving' else "⬇" if company['trend_label'] == 'declining' else "→"
        
        print(f"  {i:2d}. {emoji} {company['ticker']:10} ({company['company_name'][:30]:30}) - "
              f"Sentiment: {company['avg_sentiment']:+.3f} {trend_emoji} "
              f"({company['analyzed_articles']} articles)")
    
    print(f"\n\nBottom 5 Companies by Sentiment:")
    for i, company in enumerate(companies_summary[-5:], 1):
        emoji = "📈" if company['avg_sentiment'] > 0.15 else "📉" if company['avg_sentiment'] < -0.15 else "➖"
        trend_emoji = "⬆" if company['trend_label'] == 'improving' else "⬇" if company['trend_label'] == 'declining' else "→"
        
        print(f"  {i}. {emoji} {company['ticker']:10} ({company['company_name'][:30]:30}) - "
              f"Sentiment: {company['avg_sentiment']:+.3f} {trend_emoji} "
              f"({company['analyzed_articles']} articles)")
    
    print(f"\n\nSaved to: {OUTPUT_FILE}")
    print("="*70)
    
    return summary_data

if __name__ == "__main__":
    aggregate_all_companies()
