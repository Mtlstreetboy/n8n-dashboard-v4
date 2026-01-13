#!/usr/bin/env python3
"""
LLM Sentiment Analysis for All Companies
Approach: 100% Llama3 with relative context and temporal trends
"""

import os
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

import sys
sys.path.append('/data/scripts')
import signal
import threading

from companies_config import AI_COMPANIES
from sentiment_llm_relative import (
    analyze_article_full,
    calculate_temporal_trend
)

COMPANIES_DIR = "/data/files/companies"

# Graceful shutdown support
STOP_EVENT = threading.Event()


def _signal_handler(signum, frame):
    print(f"Received signal {signum}, requesting graceful shutdown...")
    STOP_EVENT.set()


# Register signal handlers
signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


def analyze_company_llm(
    ticker: str,
    max_workers: int = 5
) -> Dict:
    """
    Analyze all validated articles for a company using LLM
    
    Args:
        ticker: Company ticker
        max_workers: Number of parallel workers (5-10 max for LLM)
    
    Returns:
        dict: Analysis statistics
    """
    
    filepath = os.path.join(COMPANIES_DIR, f"{ticker}_news.json")
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return None
    
    # Load data
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    company_name = data['company_name']
    articles = data['articles']
    # Checkpoint: save progress every N articles
    CHECKPOINT_EVERY = 10

    # Filter: articles not already analyzed + not too many errors
    # Removed validation requirement for direct analysis
    to_analyze = [
        a for a in articles 
        if 'llm_sentiment' not in a
        and a.get('error_count', 0) < 3  # Skip after 3 failures
    ]
    
    already_analyzed = [
        a for a in articles 
        if 'llm_sentiment' in a
    ]
    
    print(f"\n{'='*60}")
    print(f"Analyzing: {ticker} - {company_name}")
    print(f"Total articles: {len(articles)}")
    print(f"Already analyzed: {len(already_analyzed)}")
    print(f"To analyze: {len(to_analyze)}")
    print(f"{'='*60}")
    
    if len(to_analyze) == 0:
        print("Nothing to analyze!")
        
        # Recalculate trend if already have analyses
        if already_analyzed:
            trend_data = calculate_temporal_trend(articles)
            data['trend_data'] = trend_data
            data['last_sentiment_analysis'] = datetime.now().isoformat()
            
            # Save
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return {
                'ticker': ticker,
                'total': len(articles),
                'analyzed': len(already_analyzed),
                'new_analyzed': 0,
                'avg_sentiment_raw': sum(a['sentiment_raw'] for a in already_analyzed) / len(already_analyzed),
                'avg_sentiment_adjusted': sum(a['sentiment_adjusted'] for a in already_analyzed) / len(already_analyzed),
                'trend_data': trend_data
            }
        
        return {
            'ticker': ticker,
            'total': len(articles),
            'analyzed': 0,
            'new_analyzed': 0
        }
    
    # Parallel LLM analysis
    analyzed_articles = []
    errors = 0
    
    start_time = time.time()
    
    print(f"Starting LLM analysis with {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                analyze_article_full,
                article,
                articles,
                ticker,
                company_name
            ): article
            for article in to_analyze
        }
        
        for i, future in enumerate(as_completed(futures), 1):
            article = futures[future]
            
            try:
                result = future.result(timeout=60)
                
                # Validate result
                if not (-100 <= result.get('sentiment_raw', 0) <= 100):
                    raise ValueError(f"Invalid sentiment_raw: {result.get('sentiment_raw')}")
                if not (-100 <= result.get('sentiment_adjusted', 0) <= 100):
                    raise ValueError(f"Invalid sentiment_adjusted: {result.get('sentiment_adjusted')}")
                
                # Add result to article
                article.update(result)
                article['analysis_status'] = 'success'
                article['analyzed_at'] = datetime.now().isoformat()
                article['error_count'] = 0  # Reset on success
                analyzed_articles.append(article)

                # Checkpoint save: persist progress to disk periodically
                if (i % CHECKPOINT_EVERY == 0) or (i == len(to_analyze)):
                    try:
                        data['articles'] = articles
                        data['last_sentiment_analysis'] = datetime.now().isoformat()
                        tmp_path = filepath + '.tmp'
                        with open(tmp_path, 'w', encoding='utf-8') as wf:
                            json.dump(data, wf, indent=2, ensure_ascii=False)
                        os.replace(tmp_path, filepath)
                        print(f"  Checkpoint: saved progress at {i}/{len(to_analyze)}")
                    except Exception as e:
                        print(f"  Warning: failed to write checkpoint: {e}")

                # Progress
                if i % 5 == 0 or i == len(to_analyze):
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0

                    sentiment_adj = result.get('sentiment_adjusted', 0)
                    category_emoji = "[+]" if sentiment_adj > 20 else "[-]" if sentiment_adj < -20 else "[=]"

                    print(f"  Progress: {i}/{len(to_analyze)} ({rate:.1f} art/s) {category_emoji} Last: {sentiment_adj:+.1f}")

                    # Rate limiting: small delay every 5 articles to respect API limits
                    if i % 5 == 0 and i < len(to_analyze):
                        time.sleep(0.5)

                # If a shutdown was requested, break out cleanly after checkpoint
                if STOP_EVENT.is_set():
                    print("Shutdown requested — stopping company analysis and saving checkpoint.")
                    break
                
            except TimeoutError:
                article['analysis_status'] = 'timeout'
                article['error_count'] = article.get('error_count', 0) + 1
                article['last_error'] = 'LLM timeout after 60s'
                article['last_error_at'] = datetime.now().isoformat()
                print(f"  Timeout on article: {article.get('title', 'unknown')[:50]}...")
                errors += 1
                
            except Exception as e:
                article['analysis_status'] = 'error'
                article['error_count'] = article.get('error_count', 0) + 1
                article['last_error'] = str(e)
                article['last_error_at'] = datetime.now().isoformat()
                print(f"  Error analyzing article: {e}")
                errors += 1
    
    elapsed = time.time() - start_time
    
    # Calculate statistics
    sentiments_raw = [a['sentiment_raw'] for a in analyzed_articles]
    sentiments_adjusted = [a['sentiment_adjusted'] for a in analyzed_articles]
    
    avg_raw = sum(sentiments_raw) / len(sentiments_raw) if sentiments_raw else 0
    avg_adjusted = sum(sentiments_adjusted) / len(sentiments_adjusted) if sentiments_adjusted else 0
    
    # Categories
    very_positive = len([s for s in sentiments_adjusted if s > 40])
    positive = len([s for s in sentiments_adjusted if 10 < s <= 40])
    neutral = len([s for s in sentiments_adjusted if -10 <= s <= 10])
    negative = len([s for s in sentiments_adjusted if -40 <= s < -10])
    very_negative = len([s for s in sentiments_adjusted if s < -40])
    
    # Calculate global trend
    trend_data = calculate_temporal_trend(articles)
    
    # Update metadata
    data['last_sentiment_analysis'] = datetime.now().isoformat()
    data['sentiment_stats'] = {
        'total_analyzed': len(already_analyzed) + len(analyzed_articles),
        'new_analyzed': len(analyzed_articles),
        'avg_sentiment_raw': avg_raw,
        'avg_sentiment_adjusted': avg_adjusted,
        'distribution': {
            'very_positive': very_positive,
            'positive': positive,
            'neutral': neutral,
            'negative': negative,
            'very_negative': very_negative
        },
        'errors': errors
    }
    data['trend_data'] = trend_data
    
    # Save
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Count failed articles
    failed_articles = [a for a in articles if a.get('error_count', 0) >= 3]
    
    print(f"\nSentiment Analysis Summary:")
    print(f"  New analyzed: {len(analyzed_articles)} in {elapsed:.1f}s ({len(analyzed_articles)/elapsed:.2f} art/s)")
    print(f"  Avg sentiment raw: {avg_raw:+.1f}")
    print(f"  Avg sentiment adjusted: {avg_adjusted:+.1f}")
    print(f"  Distribution: [++]{very_positive} [+]{positive} [=]{neutral} [-]{negative} [--]{very_negative}")
    print(f"  Trend: {trend_data['direction']} (coef: {trend_data['trend_coefficient']:+.2f})")
    print(f"  Errors (this run): {errors}")
    print(f"  Failed articles (>= 3 errors): {len(failed_articles)}")
    print(f"  Saved to: {filepath}")
    
    return {
        'ticker': ticker,
        'name': company_name,
        'total': len(articles),
        'analyzed': len(already_analyzed) + len(analyzed_articles),
        'new_analyzed': len(analyzed_articles),
        'avg_sentiment_raw': avg_raw,
        'avg_sentiment_adjusted': avg_adjusted,
        'trend_data': trend_data,
        'errors': errors
    }


def analyze_all_companies_llm(max_workers: int = 5):
    """
    Analyze all companies in series (LLM too heavy to parallelize companies)
    
    Args:
        max_workers: Workers per company
    """
    
    print("="*70)
    print("SENTIMENT ANALYSIS LLM: All Companies")
    print(f"Workers per company: {max_workers}")
    print("="*70)
    
    tickers = [c['ticker'] for c in AI_COMPANIES]
    print(f"\nFound {len(tickers)} companies to analyze\n")
    
    results = []
    start_time = time.time()
    
    # Process in series (LLM intensive)
    for ticker in tickers:
        result = analyze_company_llm(ticker, max_workers)
        if result:
            results.append(result)
    
    elapsed = time.time() - start_time
    
    # Global summary
    print("\n" + "="*70)
    print(f"SENTIMENT ANALYSIS COMPLETE")
    print(f"Time elapsed: {elapsed/60:.1f} min")
    print("\nPer Company:")
    
    for r in sorted(results, key=lambda x: x.get('avg_sentiment_adjusted', 0), reverse=True):
        sentiment = r.get('avg_sentiment_adjusted', 0)
        trend = r.get('trend_data', {}).get('direction', 'unknown')
        emoji = "[+]" if sentiment > 20 else "[-]" if sentiment < -20 else "[=]"
        
        print(f"  {emoji} {r['ticker']:10} - Sentiment: {sentiment:+6.1f} | "
              f"Trend: {trend:15} | {r.get('new_analyzed', 0)} new")
    
    total_analyzed = sum(r.get('new_analyzed', 0) for r in results)
    print(f"\nTotal new analyzed: {total_analyzed}")
    print(f"Average rate: {total_analyzed/elapsed:.2f} articles/sec")
    print("="*70)


if __name__ == "__main__":
    # Configuration
    MAX_WORKERS_PER_COMPANY = 5  # 5-10 workers max for LLM
    
    # Launch analysis
    analyze_all_companies_llm(MAX_WORKERS_PER_COMPANY)
