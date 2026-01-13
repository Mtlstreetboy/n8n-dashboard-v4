#!/usr/bin/env python3
"""Check real article sentiment"""

import json
import sys
sys.path.append('/data/scripts')

from sentiment_financial import analyze_financial_sentiment_vector

# Load AMZN articles
with open('/data/files/companies/AMZN_news.json') as f:
    data = json.load(f)

articles = data['articles']

# Find first analyzed article
analyzed = [a for a in articles if a.get('sentiment_analyzed')]
if not analyzed:
    print("No analyzed articles found!")
    exit(1)

article = analyzed[0]

print(f"Title: {article['title']}")
print(f"Description: {article.get('description', 'N/A')}")
print()
print(f"Sentiment index (stored): {article.get('financial_sentiment_index')}")
print(f"Category (stored): {article.get('financial_sentiment_category')}")
print(f"Sim positive (stored): {article.get('similarity_positive')}")
print(f"Sim negative (stored): {article.get('similarity_negative')}")
print()

# Recalculate
print("Recalculating...")
result = analyze_financial_sentiment_vector(
    article['title'],
    article.get('description', '')
)

print(f"Sentiment index (new): {result['sentiment_index']:.3f}")
print(f"Category (new): {result['category']}")
print(f"Sim positive (new): {result['similarity_positive']:.3f}")
print(f"Sim negative (new): {result['similarity_negative']:.3f}")
