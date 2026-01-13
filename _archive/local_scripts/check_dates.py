#!/usr/bin/env python3
"""Check date range of collected articles"""
import json
import os
from datetime import datetime
from email.utils import parsedate_to_datetime

COMPANIES_DIR = "/data/files/companies"

all_dates = []
files = [f for f in os.listdir(COMPANIES_DIR) if f.endswith('_news.json')]

for filename in files:
    filepath = os.path.join(COMPANIES_DIR, filename)
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    for article in data['articles']:
        if 'published_at' not in article:
            continue
        
        pub_date_str = article['published_at']
        try:
            if 'GMT' in pub_date_str or ',' in pub_date_str:
                pub_date = parsedate_to_datetime(pub_date_str)
            else:
                pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
            
            # Remove timezone for comparison
            if pub_date.tzinfo is not None:
                pub_date = pub_date.replace(tzinfo=None)
            
            all_dates.append(pub_date)
        except:
            pass

if all_dates:
    print(f"Total articles: {len(all_dates)}")
    print(f"Oldest: {min(all_dates).date()}")
    print(f"Newest: {max(all_dates).date()}")
    print(f"Days covered: {(max(all_dates) - min(all_dates)).days} days")
else:
    print("No dates found!")
