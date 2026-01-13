#!/usr/bin/env python3
"""Test du syst??me hybride"""
import sys
sys.path.insert(0, '/data/scripts')
from sentiment_weighted import analyze_sentiment_weighted

print("Test 1: Article HYPE")
test_hype = "AI will revolutionize everything! This paradigm shift represents unlimited potential for exponential growth."
result = analyze_sentiment_weighted(test_hype, "Test Hype")
print(f"Score: {result['score']}")
print(f"Bubble Index: {result.get('vector_bubble_index', 'N/A')}")
print(f"Sentiment: {result.get('sentiment', 'N/A')}")
print(f"Method: {result.get('method', 'N/A')}")
print(f"Confidence: {result.get('confidence', 'N/A')}")
print()

print("Test 2: Article REALITY")
test_reality = "Quarterly report shows GPU costs increased 15% while revenue grew only 3%. ROI projections indicate break-even in 18 months."
result2 = analyze_sentiment_weighted(test_reality, "Test Reality")
print(f"Score: {result2['score']}")
print(f"Bubble Index: {result2.get('vector_bubble_index', 'N/A')}")
print(f"Sentiment: {result2.get('sentiment', 'N/A')}")
print(f"Method: {result2.get('method', 'N/A')}")
print(f"Confidence: {result2.get('confidence', 'N/A')}")
