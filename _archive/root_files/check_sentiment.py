import json

data = json.load(open('/data/files/companies/NVDA_news.json'))
articles = data.get('articles', [])

with_sentiment = [a for a in articles if a.get('sentiment')]
print(f"Articles avec sentiment: {len(with_sentiment)} / {len(articles)}")

if with_sentiment:
    print("\nExemple 1:")
    print(f"  Titre: {with_sentiment[0].get('title','')[:80]}...")
    print(f"  Sentiment: {with_sentiment[0].get('sentiment')}")
