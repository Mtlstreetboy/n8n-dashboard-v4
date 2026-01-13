"""
Test avec 10 articles et 1 seul worker
"""
import json
from datetime import datetime
import sys
sys.path.insert(0, '/data/scripts')
from sentiment_weighted import analyze_sentiment_weighted

print("???? TEST: 10 articles avec 1 worker\n")

# Charger les articles
with open('/data/files/collected_articles_100days.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

articles = data.get('articles', [])[:10]

print(f"???? {len(articles)} articles ?? analyser\n")

results = []
for i, article in enumerate(articles, 1):
    title = article.get('title', 'No title')
    content = article.get('content', '') or article.get('description', '')
    
    print(f"[{i}/10] Analyse: {title[:60]}...")
    
    try:
        sentiment = analyze_sentiment_weighted(content, title)
        
        print(f"  ??? Score: {sentiment['score']:+d}")
        print(f"     Bubble Index: {sentiment.get('vector_bubble_index', 'N/A')}")
        print(f"     Similarity Hype: {sentiment.get('similarity_to_hype', 'N/A')}")
        print(f"     Similarity Reality: {sentiment.get('similarity_to_reality', 'N/A')}")
        print(f"     Method: {sentiment.get('method', 'N/A')}")
        print(f"     Confidence: {sentiment.get('confidence', 'N/A')}")
        print()
        
        results.append({
            **article,
            'sentiment_score': sentiment['score'],
            **{k: v for k, v in sentiment.items() if k != 'score'}
        })
        
    except Exception as e:
        print(f"  ??? ERREUR: {e}")
        print(f"     Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print()

# Sauvegarder
output = {
    'articles': results,
    'total_analyzed': len(results),
    'test_date': datetime.now().isoformat()
}

with open('/data/files/sentiment_test_10.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n??? Test termin??: {len(results)}/{len(articles)} articles analys??s")
print(f"???? Sauvegard??: /data/files/sentiment_test_10.json")

# Stats
if results:
    scores = [r['sentiment_score'] for r in results]
    avg = sum(scores) / len(scores)
    print(f"\n???? Score moyen: {avg:.2f}")
    print(f"???? Scores: {scores}")
