
import json
import glob
import random
import os

def check_sentiment():
    files = glob.glob('local_files/companies/*_news.json')
    all_articles = []

    print(f"Loading {len(files)} files...")
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                ticker = data.get('ticker', 'UNKNOWN')
                for art in data.get('articles', []):
                    if art.get('sentiment'):
                        art['ticker'] = ticker
                        all_articles.append(art)
        except Exception as e:
            print(f"Error reading {f}: {e}")

    if not all_articles:
        print("No analyzed articles found.")
        return

    print(f"Found {len(all_articles)} analyzed articles. Sampling 10...")
    sample = random.sample(all_articles, min(10, len(all_articles)))
    
    print("-" * 100)
    print(f"{'TICKER':<6} | {'SCORE':<6} | {'TITLE'}")
    print("-" * 100)
    
    for a in sample:
        sent = a.get('sentiment', {})
        # Handle various score keys depending on version
        score = sent.get('binary_score')
        if score is None:
             score = sent.get('compound')
        if score is None:
             score = sent.get('global_compound', 0)
             
        title = a.get('title', 'No Title')
        print(f"{a['ticker']:<6} | {float(score):>6.2f} | {title[:80]}")
    print("-" * 100)

if __name__ == "__main__":
    check_sentiment()
