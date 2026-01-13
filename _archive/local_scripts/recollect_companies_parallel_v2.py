#!/usr/bin/env python3
"""
???? COLLECTEUR HYBRIDE COMPAGNIES - NewsAPI (30j) + GNews (fra??ches)
--------------------------------------------------------------------
Strat??gie optimale pour chaque compagnie:
- NewsAPI: 30 derniers jours (historique fiable)
- GNews: Nouvelles fra??ches des derni??res 24h (temps r??el)

Usage: docker exec -it n8n_data_architect python3 /data/scripts/recollect_companies_parallel_v2.py 30 10
"""
import sys
sys.path.insert(0, '/data/scripts')

from collect_companies import save_articles, load_existing_articles
from companies_config import get_all_companies
from newsapi import NewsApiClient
from gnews import GNews
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import random

# Lock pour ??viter les conflits d'??criture
write_lock = Lock()

# NewsAPI Key
NEWSAPI_KEY = '1aa909b97e814a108887c7af7f9ed5b1'

def collect_company_hybrid(company, days=30, newsapi=None):
    """
    Collecte hybride pour une compagnie: NewsAPI (historique) + GNews (temps r??el)
    """
    ticker = company['ticker']
    company_name = company['name']
    
    print(f"\n{'='*60}")
    print(f"???? {ticker} - {company_name}")
    print(f"{'='*60}")
    
    # Charger les articles existants
    existing_articles = load_existing_articles(ticker)
    existing_urls = {article['url'] for article in existing_articles if 'url' in article}
    
    print(f"???? Articles existants: {len(existing_articles)}")
    
    new_articles = []
    errors = 0
    
    # Phase 1: NewsAPI (historique)
    print(f"\n???? PHASE 1: NewsAPI (historique {days} jours)")
    
    search_terms = " OR ".join([f'"{term}"' for term in company.get('search_terms', [ticker])])
    
    for day_offset in range(1, days + 1):
        date_target = datetime.now() - timedelta(days=day_offset)
        date_str = date_target.strftime("%Y-%m-%d")
        
        try:
            response = newsapi.get_everything(
                q=search_terms,
                from_param=date_str,
                to=date_str,
                language='en',
                page_size=100,
                sort_by='publishedAt'
            )
            
            for item in response.get('articles', [])[:20]:
                url = item.get('url', '')
                
                if url and url not in existing_urls:
                    article = {
                        'title': item.get('title', ''),
                        'url': url,
                        'published_at': item.get('publishedAt', date_str),
                        'content': item.get('description', ''),
                        'source': item.get('source', {}).get('name', 'Unknown'),
                        'ticker': ticker,
                        'company_name': company_name,
                        'sector': company.get('sector', 'Unknown'),
                        'collected_at': datetime.now().isoformat(),
                        'validated': False,
                        'method': 'newsapi'
                    }
                    new_articles.append(article)
                    existing_urls.add(url)
            
            if day_offset % 10 == 0:
                print(f"  [{day_offset}/{days}] +{len(new_articles)} articles")
            
            time.sleep(random.uniform(0.1, 0.3))
            
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  ?????? Erreur jour {date_str}: {str(e)[:50]}")
    
    print(f"??? Phase 1: +{len(new_articles)} articles (NewsAPI)")
    
    # Phase 2: GNews (nouvelles fra??ches)
    print(f"\n???? PHASE 2: GNews (temps r??el)")
    
    gnews_count = 0
    try:
        google_news = GNews(language='en', country='US', max_results=100)
        news_items = google_news.get_news(search_terms)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        for item in news_items:
            url = item.get('url', '')
            
            if url and url not in existing_urls:
                article = {
                    'title': item.get('title', ''),
                    'url': url,
                    'published_at': today,
                    'content': item.get('description', ''),
                    'source': item.get('publisher', {}).get('title', 'Unknown'),
                    'ticker': ticker,
                    'company_name': company_name,
                    'sector': company.get('sector', 'Unknown'),
                    'collected_at': datetime.now().isoformat(),
                    'validated': False,
                    'method': 'gnews'
                }
                new_articles.append(article)
                existing_urls.add(url)
                gnews_count += 1
        
        print(f"??? Phase 2: +{gnews_count} articles (GNews)")
        
    except Exception as e:
        print(f"??? GNews erreur: {str(e)[:50]}")
    
    # Fusion et sauvegarde
    all_articles = existing_articles + new_articles
    
    with write_lock:
        save_articles(ticker, company_name, all_articles)
    
    newsapi_count = len(new_articles) - gnews_count
    
    print(f"\n??? {ticker} TERMIN??:")
    print(f"   ???? NewsAPI: {newsapi_count} articles")
    print(f"   ???? GNews: {gnews_count} articles")
    print(f"   ???? Total nouveau: {len(new_articles)}")
    print(f"   ???? Total final: {len(all_articles)}")
    
    return {
        'ticker': ticker,
        'status': 'success',
        'existing': len(existing_articles),
        'new': len(new_articles),
        'newsapi': newsapi_count,
        'gnews': gnews_count,
        'errors': errors
    }

def recollect_all_hybrid(days=30, max_workers=10):
    """
    Collecte hybride pour toutes les compagnies en parall??le
    """
    companies = get_all_companies()
    newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
    
    print("="*80)
    print("???? COLLECTEUR HYBRIDE - TOUTES LES COMPAGNIES")
    print(f"???? NewsAPI ({days}j historique) + GNews (temps r??el)")
    print(f"???? Compagnies: {len(companies)} | Workers: {max_workers}")
    print("="*80)
    
    start_time = time.time()
    results = []
    
    # Ex??cution parall??le
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(collect_company_hybrid, company, days, newsapi): company 
            for company in companies
        }
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            
            print(f"\n[{completed}/{len(companies)}] ??? {result['ticker']} termin??")
    
    # Rapport final
    elapsed = (time.time() - start_time) / 60
    
    total_existing = sum(r['existing'] for r in results)
    total_new = sum(r['new'] for r in results)
    total_newsapi = sum(r['newsapi'] for r in results)
    total_gnews = sum(r['gnews'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    
    print("\n" + "="*80)
    print("??? COLLECTE HYBRIDE TERMIN??E")
    print("="*80)
    print(f"???? Articles existants: {total_existing}")
    print(f"???? Nouveaux articles: {total_new}")
    print(f"   ???? NewsAPI: {total_newsapi}")
    print(f"   ???? GNews: {total_gnews}")
    print(f"???? Total final: {total_existing + total_new}")
    print(f"?????? Dur??e: {elapsed:.1f} minutes")
    print(f"??? Vitesse: {total_new/elapsed:.0f} articles/min" if elapsed > 0 else "")
    print(f"?????? Erreurs: {total_errors}")
    print("="*80)
    
    # D??tails par compagnie
    print("\n???? D??TAIL PAR COMPAGNIE:")
    print("-"*80)
    print(f"{'Ticker':<10} {'Existant':<10} {'NewsAPI':<10} {'GNews':<10} {'Total':<10}")
    print("-"*80)
    
    for r in sorted(results, key=lambda x: x['new'], reverse=True):
        total = r['existing'] + r['new']
        print(f"{r['ticker']:<10} {r['existing']:<10} {r['newsapi']:<10} {r['gnews']:<10} {total:<10}")
    
    print("-"*80)

if __name__ == "__main__":
    days = 30
    workers = 10
    
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        try:
            workers = int(sys.argv[2])
        except:
            pass
    
    recollect_all_hybrid(days=days, max_workers=workers)
