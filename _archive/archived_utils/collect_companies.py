# -*- coding: utf-8 -*-
"""
Collecteur de Nouvelles par Compagnie AI
Collection parallele optimisee pour analyse de sentiment par ticker
"""

from gnews import GNews
from datetime import datetime, timedelta
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import sys

# Importer la config des compagnies (fix after move)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.companies_config import get_all_companies, get_search_query

DATA_DIR = "/data/files"
if sys.platform == 'win32':
    # Windows Local environment override
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    DATA_DIR = os.path.join(project_root, 'local_files')

COMPANIES_DIR = os.path.join(DATA_DIR, "companies")

# Lock pour ecriture thread-safe
write_lock = Lock()

def ensure_companies_dir():
    """Cree le dossier companies s'il n'existe pas"""
    if not os.path.exists(COMPANIES_DIR):
        os.makedirs(COMPANIES_DIR)
        print(f"Created directory: {COMPANIES_DIR}")

def get_output_file(ticker):
    """Retourne le chemin du fichier JSON pour une compagnie"""
    return os.path.join(COMPANIES_DIR, f"{ticker}_news.json")

def load_existing_articles(ticker):
    """Charge les articles existants pour une compagnie"""
    filepath = get_output_file(ticker)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('articles', [])
        except Exception as e:
            print(f"Warning: Could not load {filepath}: {e}")
    return []

def get_last_collected_date(ticker):
    """Trouve la derniere date collectee pour une compagnie"""
    articles = load_existing_articles(ticker)
    if articles:
        dates = []
        for article in articles:
            pub_date = article.get('published_at', '')
            if pub_date:
                try:
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    dates.append(dt)
                except:
                    pass
        if dates:
            return max(dates)
    return None

def save_articles(ticker, company_name, articles):
    """Sauvegarde les articles d'une compagnie"""
    filepath = get_output_file(ticker)
    with write_lock:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "ticker": ticker,
                "company_name": company_name,
                "total_articles": len(articles),
                "last_update": datetime.now().isoformat(),
                "articles": articles
            }, f, indent=2, ensure_ascii=False)

def collect_company_day(company, day_offset, existing_urls):
    """
    Collecte les nouvelles d'une compagnie pour un jour donne
    """
    ticker = company['ticker']
    company_name = company['name']
    
    date_target = datetime.now() - timedelta(days=day_offset)
    date_str = date_target.strftime("%Y-%m-%d")
    
    # Configuration GNews
    google_news = GNews(language='en', country='US', max_results=20)
    
    start_date = date_target - timedelta(days=1)
    google_news.start_date = (start_date.year, start_date.month, start_date.day)
    google_news.end_date = (date_target.year, date_target.month, date_target.day)
    
    try:
        # Construire requete de recherche
        search_query = get_search_query(company)
        
        # Recherche avec retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                news_items = google_news.get_news(search_query)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        
        day_articles = []
        for item in news_items:
            url = item.get('url', '')
            
            # Skip si deja collecte
            if url in existing_urls:
                continue
            
            # Extraire contenu complet
            try:
                full_article = google_news.get_full_article(url)
                if full_article and hasattr(full_article, 'text'):
                    content = full_article.text
                else:
                    content = item.get('description', '')
            except:
                content = item.get('description', '')
            
            article_data = {
                'title': item.get('title', ''),
                'url': url,
                'published_at': item.get('published date', date_str),
                'content': content,
                'source': item.get('publisher', {}).get('title', 'Unknown'),
                'ticker': ticker,
                'company_name': company_name,
                'sector': company.get('sector', 'Unknown'),
                'collected_at': datetime.now().isoformat(),
                'validated': False  # Sera valide par LLM plus tard
            }
            
            day_articles.append(article_data)
            existing_urls.add(url)
        
        return {
            'success': True,
            'ticker': ticker,
            'date': date_str,
            'articles': day_articles,
            'count': len(day_articles)
        }
        
    except Exception as e:
        return {
            'success': False,
            'ticker': ticker,
            'date': date_str,
            'error': str(e),
            'count': 0
        }

def collect_company_news(company, days=30, max_workers=5):
    """
    Collecte les nouvelles d'une compagnie sur N jours
    """
    ticker = company['ticker']
    company_name = company['name']
    
    print(f"\n{'='*60}")
    print(f"Collecting: {ticker} - {company_name}")
    print(f"{'='*60}")
    
    # Charger articles existants
    existing_articles = load_existing_articles(ticker)
    existing_urls = {article['url'] for article in existing_articles}
    
    # Determiner date de debut
    last_date = get_last_collected_date(ticker)
    if last_date:
        days_to_collect = (datetime.now() - last_date).days + 1
        print(f"Last collected: {last_date.date()}")
        print(f"Collecting {days_to_collect} days (delta)")
    else:
        days_to_collect = days
        print(f"First collection: {days_to_collect} days")
    
    # Collection parallele par jour
    new_articles = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(collect_company_day, company, day, existing_urls): day
            for day in range(days_to_collect)
        }
        
        for future in as_completed(futures):
            result = future.result()
            if result['success']:
                new_articles.extend(result['articles'])
                if result['count'] > 0:
                    print(f"  {result['date']}: +{result['count']} articles")
            else:
                print(f"  {result['date']}: ERROR - {result['error']}")
    
    # Fusionner et sauvegarder
    all_articles = existing_articles + new_articles
    
    # Dedupliquer par URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        url = article['url']
        if url not in seen_urls:
            unique_articles.append(article)
            seen_urls.add(url)
    
    # Trier par date
    unique_articles.sort(key=lambda x: x['published_at'], reverse=True)
    
    # Sauvegarder
    save_articles(ticker, company_name, unique_articles)
    
    print(f"\nSummary:")
    print(f"  New articles: {len(new_articles)}")
    print(f"  Total unique: {len(unique_articles)}")
    print(f"  Saved to: {get_output_file(ticker)}")
    
    return len(new_articles)

def collect_all_companies(days=30, company_workers=3, day_workers=5):
    """
    Collecte toutes les compagnies en parallele
    
    Args:
        days: Nombre de jours a collecter (ou delta depuis derniere collection)
        company_workers: Nombre de compagnies traitees en parallele
        day_workers: Nombre de jours collectes en parallele par compagnie
    """
    ensure_companies_dir()
    
    companies = get_all_companies()
    
    print("\n" + "="*70)
    print(f"COLLECTION PARALLELISEE: {len(companies)} compagnies AI")
    print(f"Max days per company: {days}")
    print(f"Company workers: {company_workers}")
    print(f"Day workers per company: {day_workers}")
    print("="*70)
    
    start_time = time.time()
    total_new = 0
    
    with ThreadPoolExecutor(max_workers=company_workers) as executor:
        futures = {
            executor.submit(collect_company_news, company, days, day_workers): company
            for company in companies
        }
        
        for future in as_completed(futures):
            company = futures[future]
            try:
                new_count = future.result()
                total_new += new_count
            except Exception as e:
                print(f"\nERROR with {company['ticker']}: {e}")
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*70)
    print(f"COLLECTION COMPLETE")
    print(f"Total new articles: {total_new}")
    print(f"Time elapsed: {elapsed:.1f}s")
    print(f"Articles per second: {total_new/elapsed:.2f}")
    print("="*70)

if __name__ == "__main__":
    import sys
    
    # Parametres par defaut
    days = 30
    company_workers = 3
    day_workers = 5
    
    # Override si arguments
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
    if len(sys.argv) > 2:
        company_workers = int(sys.argv[2])
    if len(sys.argv) > 3:
        day_workers = int(sys.argv[3])
    
    collect_all_companies(days, company_workers, day_workers)
