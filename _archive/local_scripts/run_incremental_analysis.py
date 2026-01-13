#!/usr/bin/env python3
"""
Incremental Analysis - Run daily to analyze new articles
Only processes articles not yet analyzed (idempotent)
"""

import sys
sys.path.append('/data/scripts')

from analyze_llm_companies import analyze_all_companies_llm
from monitor_analysis import print_summary

if __name__ == "__main__":
    print("\n" + "="*80)
    print("INCREMENTAL SENTIMENT ANALYSIS")
    print("This script is safe to run multiple times - only analyzes new articles")
    print("="*80 + "\n")
    
    # Show status before
    print("???? STATUS BEFORE ANALYSIS:")
    print("-"*80)
    before = print_summary()
    
    if before['pending'] == 0:
        print("\n??? Nothing to analyze - all articles already processed!")
        exit(0)
    
    input("\n??????  Press ENTER to start analysis or Ctrl+C to cancel...")
    
    # Run analysis
    print("\n???? Starting incremental analysis...\n")
    analyze_all_companies_llm(max_workers=5)
    
    # Show status after
    print("\n\n???? STATUS AFTER ANALYSIS:")
    print("-"*80)
    after = print_summary()
    
    # Summary of changes
    print("\n???? DELTA:")
    print(f"  Articles analyzed: +{after['analyzed'] - before['analyzed']}")
    print(f"  Companies completed: +{after['companies_complete'] - before['companies_complete']}")
    print(f"  Progress: {before['pct_complete']:.1f}% ??? {after['pct_complete']:.1f}%")
    print("="*80)
