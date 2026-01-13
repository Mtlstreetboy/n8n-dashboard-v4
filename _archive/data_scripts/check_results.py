import json

with open('/data/files/sentiment_weighted.json') as f:
    data = json.load(f)

articles = data['articles'][:10]

print("\n=== PREMIERS 10 ARTICLES ===\n")
for i, a in enumerate(articles, 1):
    score = a.get('sentiment_score', 0)
    bubble = a.get('vector_bubble_index', 'N/A')
    sim_hype = a.get('similarity_to_hype', 'N/A')
    sim_reality = a.get('similarity_to_reality', 'N/A')
    title = a.get('title', 'No title')[:70]
    
    print(f"{i}. Score: {score:+d} | Bubble: {bubble} | Hype: {sim_hype} | Reality: {sim_reality}")
    print(f"   {title}...")
    print()
