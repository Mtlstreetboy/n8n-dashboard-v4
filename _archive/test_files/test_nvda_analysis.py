#!/usr/bin/env python3
"""
Analyze NVDA test articles with LLM
Single company test before running all
"""

import sys
sys.path.append('/data/scripts')

from analyze_llm_companies import analyze_company_llm

if __name__ == "__main__":
    print("Testing LLM analysis on NVDA...")
    print("This will analyze all 200 NVDA articles")
    print("="*70)
    
    result = analyze_company_llm('NVDA', max_workers=5)
    
    if result:
        print("\n" + "="*70)
        print("TEST COMPLETE!")
        print(f"Company: {result.get('name')}")
        print(f"Articles analyzed: {result.get('new_analyzed')}")
        print(f"Avg sentiment raw: {result.get('avg_sentiment_raw', 0):+.1f}")
        print(f"Avg sentiment adjusted: {result.get('avg_sentiment_adjusted', 0):+.1f}")
        print(f"Trend: {result.get('trend_data', {}).get('direction', 'unknown')}")
        print("="*70)
