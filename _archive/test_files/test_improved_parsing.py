#!/usr/bin/env python3
"""
Test improved LLM parsing with 1000 tokens
"""
import sys
sys.path.append('/data/files')

from sentiment_llm_relative import llm_analyze_sentiment_relative

# Create test article similar to the problematic AMD one
test_article = {
    'title': 'AMD stock soars after company says its data center revenue will jump 60%',
    'description': 'Advanced Micro Devices announced strong Q4 guidance with data center revenue expected to surge 60% year-over-year, driving optimism about AI chip demand.',
    'published_at': '2025-12-07T06:22:02Z',
    'url': 'https://example.com/amd-data-center-surge',
    'content': ''
}

# Empty context (like the original problematic case)
recent_articles = []

print("=" * 70)
print("TESTING IMPROVED LLM PARSING (1000 tokens + robust JSON)")
print("=" * 70)
print(f"\nTest Article: {test_article['title']}")
print(f"Description: {test_article['description'][:100]}...")

print("\n🔄 Analyzing with improved LLM...")
result = llm_analyze_sentiment_relative(
    article=test_article,
    recent_articles=recent_articles,
    ticker='AMD',
    company_name='Advanced Micro Devices'
)

print("\n" + "=" * 70)
print("RESULTS:")
print("=" * 70)
print(f"✅ Sentiment Score: {result.get('sentiment_score')}")
print(f"✅ Category: {result.get('category')}")
print(f"✅ Confidence: {result.get('confidence')}")
print(f"✅ Error: {result.get('error', False)}")
print(f"\n📝 Reasoning:")
print(f"   {result.get('reasoning', 'N/A')}")
print(f"\n🔍 Key Factors:")
for factor in result.get('key_factors', []):
    print(f"   - {factor}")
print(f"\n📊 Comparative Context:")
print(f"   {result.get('comparative_context', 'N/A')}")

if result.get('error'):
    print(f"\n❌ RAW OUTPUT (debugging):")
    print(f"   {result.get('raw_output', 'N/A')[:300]}...")

print("\n" + "=" * 70)
print("EXPECTED: Positive sentiment (+60 to +80) for 'soars' and '60% jump'")
print("=" * 70)
