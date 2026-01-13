#!/usr/bin/env python3
"""
Monitor sentiment analysis progress across all companies
Easy-to-read summary of what's analyzed and what remains
"""

import os
import json
from datetime import datetime
from typing import Dict, List

COMPANIES_DIR = "/data/files/companies"

def get_company_status(ticker: str) -> Dict:
    """Get analysis status for one company"""
    filepath = os.path.join(COMPANIES_DIR, f"{ticker}_news.json")
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data['articles']
    total = len(articles)
    
    analyzed = [a for a in articles if 'llm_sentiment' in a]
    pending = [a for a in articles if 'llm_sentiment' not in a and a.get('error_count', 0) < 3]
    failed = [a for a in articles if a.get('error_count', 0) >= 3]
    
    # Calculate average sentiment if available
    avg_sentiment = 0
    trend = 'unknown'
    if analyzed:
        sentiments = [a['sentiment_adjusted'] for a in analyzed]
        avg_sentiment = sum(sentiments) / len(sentiments)
        trend = data.get('trend_data', {}).get('direction', 'unknown')
    
    last_analysis = data.get('last_sentiment_analysis', 'Never')
    
    return {
        'ticker': ticker,
        'company_name': data['company_name'],
        'total': total,
        'analyzed': len(analyzed),
        'pending': len(pending),
        'failed': len(failed),
        'pct_complete': (len(analyzed) / total * 100) if total > 0 else 0,
        'avg_sentiment': avg_sentiment,
        'trend': trend,
        'last_analysis': last_analysis
    }


def print_summary():
    """Print comprehensive analysis summary"""
    
    # Get all company files
    files = [f for f in os.listdir(COMPANIES_DIR) if f.endswith('_news.json')]
    tickers = sorted([f.replace('_news.json', '') for f in files])
    
    print("="*80)
    print(f"SENTIMENT ANALYSIS STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    statuses = []
    for ticker in tickers:
        status = get_company_status(ticker)
        if status:
            statuses.append(status)
    
    # Overall stats
    total_articles = sum(s['total'] for s in statuses)
    total_analyzed = sum(s['analyzed'] for s in statuses)
    total_pending = sum(s['pending'] for s in statuses)
    total_failed = sum(s['failed'] for s in statuses)
    
    print(f"\nOVERALL PROGRESS:")
    print(f"  Total articles: {total_articles}")
    print(f"  ??? Analyzed: {total_analyzed} ({total_analyzed/total_articles*100:.1f}%)")
    print(f"  ??? Pending: {total_pending} ({total_pending/total_articles*100:.1f}%)")
    print(f"  ??? Failed: {total_failed} ({total_failed/total_articles*100:.1f}%)")
    
    # Companies needing analysis
    need_analysis = [s for s in statuses if s['pending'] > 0]
    if need_analysis:
        print(f"\n???? COMPANIES WITH PENDING ARTICLES: {len(need_analysis)}")
        for s in sorted(need_analysis, key=lambda x: x['pending'], reverse=True):
            print(f"  {s['ticker']:10} - {s['pending']:3} pending ({s['pct_complete']:5.1f}% done)")
    
    # Completed companies
    completed = [s for s in statuses if s['pending'] == 0 and s['analyzed'] > 0]
    if completed:
        print(f"\n??? COMPLETED COMPANIES: {len(completed)}")
        print(f"\n{'Ticker':<10} {'Sentiment':<12} {'Trend':<15} {'Articles':<10} {'Last Analysis'}")
        print("-"*80)
        for s in sorted(completed, key=lambda x: x['avg_sentiment'], reverse=True):
            emoji = "[+]" if s['avg_sentiment'] > 20 else "[-]" if s['avg_sentiment'] < -20 else "[=]"
            sentiment_str = f"{emoji} {s['avg_sentiment']:+6.1f}"
            last_time = s['last_analysis'][:19] if s['last_analysis'] != 'Never' else 'Never'
            print(f"{s['ticker']:<10} {sentiment_str:<12} {s['trend']:<15} {s['analyzed']:<10} {last_time}")
    
    # Failed articles summary
    companies_with_failures = [s for s in statuses if s['failed'] > 0]
    if companies_with_failures:
        print(f"\n??????  COMPANIES WITH FAILURES: {len(companies_with_failures)}")
        for s in companies_with_failures:
            print(f"  {s['ticker']:10} - {s['failed']} failed articles")
    
    # Estimate remaining time
    if total_pending > 0:
        avg_rate = 0.47  # articles per second (from NVDA test)
        est_minutes = (total_pending / avg_rate) / 60
        print(f"\n??????  ESTIMATED TIME FOR REMAINING: {est_minutes:.1f} minutes (~{est_minutes/60:.1f} hours)")
    
    print("\n" + "="*80)
    
    # Return summary for scripting
    return {
        'total_articles': total_articles,
        'analyzed': total_analyzed,
        'pending': total_pending,
        'failed': total_failed,
        'pct_complete': (total_analyzed / total_articles * 100) if total_articles > 0 else 0,
        'companies_complete': len(completed),
        'companies_pending': len(need_analysis),
        'companies_failed': len(companies_with_failures)
    }


if __name__ == "__main__":
    summary = print_summary()
    
    # Exit code based on completion
    if summary['pending'] == 0:
        print("??? All companies analyzed!")
        exit(0)
    else:
        print(f"??? {summary['pending']} articles still pending")
        exit(1)
