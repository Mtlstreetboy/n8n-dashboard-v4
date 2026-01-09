
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def test_rss_history(ticker, days_ago=30):
    date = datetime.now() - timedelta(days=days_ago)
    date_str = date.strftime('%Y-%m-%d')
    next_date_str = (date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    query = f'{ticker} stock after:{date_str} before:{next_date_str}'
    url = f'https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en'
    
    print(f"Testing RSS for {ticker} on {date_str}...")
    print(f"URL: {url}")
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            items = root.findall('.//item')
            print(f"✅ Found {len(items)} articles.")
            for i, item in enumerate(items[:3]):
                title = item.find('title').text
                pub = item.find('pubDate').text
                print(f"   {i+1}. [{pub[:16]}] {title}")
        else:
            print(f"❌ Failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_rss_history("NVDA", 45)
