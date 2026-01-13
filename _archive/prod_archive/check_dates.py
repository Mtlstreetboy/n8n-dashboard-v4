#!/usr/bin/env python3
import json
from datetime import datetime, timezone

tickers = ['NVDA', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'AMD']
for ticker in tickers:
    try:
        with open(f'/data/files/companies/{ticker}_news.json', 'r') as f:
            data = json.load(f)
        articles = data.get('articles', []) if isinstance(data, dict) else data
        
        dates = []
        for a in articles:
            try:
                pub_date = datetime.fromisoformat(a.get('published_at', '').replace('Z', '+00:00'))
                dates.append(pub_date)
            except:
                pass
        
        if dates:
            oldest = min(dates)
            newest = max(dates)
            now = datetime.now(timezone.utc)
            days_since_oldest = (now - oldest).days
            days_since_newest = (now - newest).days
            days_range = (newest - oldest).days
            print(f'{ticker:6s}: {len(dates):3d} articles | Ancien: {oldest.strftime("%Y-%m-%d")} ({days_since_oldest:2d}j) | Récent: {newest.strftime("%Y-%m-%d")} ({days_since_newest}j) | Plage: {days_range:2d}j')
    except Exception as e:
        print(f'{ticker}: ERROR - {e}')
