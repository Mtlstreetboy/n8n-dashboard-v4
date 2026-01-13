import json
import os

tickers = ['GOOGL', 'META', 'AMZN', 'AMD', 'TSLA', 'ORCL', 'CRM', 'PLTR', 'SNOW', 'AVGO', 'ADBE', 'NOW', 'INTC']
base_dir = '/data/files/companies'

print("Status des analyses LLM:")
print("-" * 50)

for ticker in tickers:
    news_file = f'{base_dir}/{ticker}_news.json'
    if not os.path.exists(news_file):
        print(f"{ticker}: Fichier absent")
        continue
    
    try:
        with open(news_file, 'r') as f:
            data = json.load(f)
        
        articles = data.get('articles', data if isinstance(data, list) else [])
        
        if not articles:
            print(f"{ticker}: Aucun article")
            continue
        
        has_llm = 'llm_sentiment' in articles[0]
        count = len(articles)
        
        print(f"{ticker}: {count} articles, LLM={has_llm}")
        
    except Exception as e:
        print(f"{ticker}: ERREUR - {str(e)}")
