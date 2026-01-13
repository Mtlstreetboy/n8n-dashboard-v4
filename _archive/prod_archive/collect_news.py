#!/usr/bin/env python3
"""
???? COLLECTEUR OPTIMIS?? AVEC BATCH ET RATE LIMITING
--------------------------------------------------------------------
Strat??gie intelligente:
- Batch de 7 jours au lieu de 1 jour = divise requ??tes par 7
- Limite ?? 90 requ??tes/jour pour NewsAPI gratuit
- GNews pour compl??ter les donn??es r??centes

Usage: python3 collect_news.py [jours] [workers]
Exemple: python3 collect_news.py 100 1
"""
import sys
sys.path.insert(0, '/data/scripts')

from collect_companies import save_articles, load_existing_articles
from companies_config import get_all_companies
from newsapi import NewsApiClient
from gnews import GNews
from datetime import datetime, timedelta
import time
from threading import Lock
import random

# Lock pour ??viter les conflits d'??criture
write_lock = Lock()

# Configuration
NEWSAPI_KEY = '1aa909b97e814a108887c7af7f9ed5b1'
MAX_REQUESTS_PER_DAY = 90  # Limite pour NewsAPI gratuit (100 - marge)
BATCH_SIZE = 7  # Jours par requ??te (divise par 7 le nombre de requ??tes)

# Compteur global de requ??tes
requests_counter = {'count': 0}

def collect_company_optimized(company, days=100, newsapi=None):
    """
    Collecte optimis??e avec batch et rate limiting
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
    
    # Phase 1: NewsAPI par batch de 7 jours
    search_terms = " OR ".join([f'"{term}"' for term in company.get('search_terms', [ticker])])
    total_batches = (days + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"\n???? PHASE 1: NewsAPI ({total_batches} batchs de {BATCH_SIZE}j)")
    
    for batch_num in range(total_batches):
        # V??rifier limite de requ??tes
        if requests_counter['count'] >= MAX_REQUESTS_PER_DAY:
            print(f"??????  Limite quotidienne atteinte ({MAX_REQUESTS_PER_DAY} req)")
            print(f"   Trait?? {batch_num}/{total_batches} batchs pour {ticker}")
            break
        
        # Calculer p??riode du batch (du plus r??cent au plus ancien)
        start_offset = batch_num * BATCH_SIZE
        end_offset = min(start_offset + BATCH_SIZE, days)
        
        from_date = (datetime.now() - timedelta(days=end_offset)).strftime("%Y-%m-%d")
        to_date = (datetime.now() - timedelta(days=start_offset + 1)).strftime("%Y-%m-%d")
        
        try:
            response = newsapi.get_everything(
                q=search_terms,
                from_param=from_date,
                to=to_date,
                language='en',
                page_size=100,
                sort_by='relevancy'
            )
            
            requests_counter['count'] += 1
            
            added_in_batch = 0
            for item in response.get('articles', [])[:30]:  # Max 30 par batch
                url = item.get('url', '')
                
                if url and url not in existing_urls:
                    article = {
                        'title': item.get('title', ''),
                        'url': url,
                        'published_at': item.get('publishedAt', ''),
                        'content': item.get('description', ''),
                        'source': item.get('source', {}).get('name', 'Unknown'),
                        'ticker': ticker,
                        'company_name': company_name,
                        'sector': company.get('sector', 'Unknown'),
                        'collected_at': datetime.now().isoformat(),
                        'validated': False,
                        'method': 'newsapi_batch'
                    }
                    new_articles.append(article)
                    existing_urls.add(url)
                    added_in_batch += 1
            
            print(f"  [{batch_num+1}/{total_batches}] {from_date}???{to_date}: +{added_in_batch} (req: {requests_counter['count']}/{MAX_REQUESTS_PER_DAY})")
            
            # Sauvegarde interm??diaire tous les 3 batchs
            if (batch_num + 1) % 3 == 0:
                all_articles = existing_articles + new_articles
                with write_lock:
                    save_articles(ticker, company_name, all_articles)
                print(f"  ???? Sauvegarde: {len(all_articles)} articles")
            
            time.sleep(random.uniform(0.3, 0.7))
            
        except Exception as e:
            errors += 1
            error_msg = str(e)
            if 'rate' in error_msg.lower() or '429' in error_msg:
                print(f"  ??????  Rate limit atteint - arr??t NewsAPI pour {ticker}")
                break
            elif errors <= 3:
                print(f"  ??? Erreur batch {batch_num}: {error_msg[:50]}")
    
    newsapi_count = len(new_articles)
    print(f"??? Phase 1: +{newsapi_count} articles (NewsAPI)")
    
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
    
    # Sauvegarde finale
    all_articles = existing_articles + new_articles
    
    with write_lock:
        save_articles(ticker, company_name, all_articles)
    
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
        'errors': errors,
        'requests_used': requests_counter['count']
    }

def collect_all_optimized(days=100, sequential=True):
    """
    Collecte optimis??e avec gestion du rate limiting
    Sequential=True recommand?? pour respecter les quotas NewsAPI
    """
    companies = get_all_companies()
    newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
    
    # Calcul th??orique des requ??tes
    batches_per_company = (days + BATCH_SIZE - 1) // BATCH_SIZE
    total_requests_needed = len(companies) * batches_per_company
    companies_per_day = MAX_REQUESTS_PER_DAY // batches_per_company
    
    print("="*80)
    print("???? COLLECTEUR OPTIMIS?? - RATE LIMITING INTELLIGENT")
    print(f"???? NewsAPI (batch {BATCH_SIZE}j) + GNews (temps r??el)")
    print(f"???? Compagnies: {len(companies)}")
    print(f"???? Requ??tes/entreprise: ~{batches_per_company}")
    print(f"??? Limite quotidienne: {MAX_REQUESTS_PER_DAY} requ??tes")
    print(f"???? Capacit??: ~{companies_per_day} entreprises/jour")
    print(f"???? Dur??e estim??e: {(len(companies) + companies_per_day - 1) // companies_per_day} jours")
    print("="*80)
    
    start_time = time.time()
    results = []
    
    # Ex??cution s??quentielle (respecte rate limit)
    for i, company in enumerate(companies, 1):
        if requests_counter['count'] >= MAX_REQUESTS_PER_DAY:
            print(f"\n??????  Quota quotidien atteint apr??s {i-1}/{len(companies)} entreprises")
            print(f"???? {len(companies) - i + 1} entreprises restantes - relancer demain")
            break
        
        print(f"\n[{i}/{len(companies)}] Traitement de {company['ticker']}...")
        
        result = collect_company_optimized(company, days, newsapi)
        results.append(result)
        
        print(f"[{i}/{len(companies)}] ??? {result['ticker']} termin??")
    
    # Rapport final
    elapsed = (time.time() - start_time) / 60
    
    total_existing = sum(r['existing'] for r in results)
    total_new = sum(r['new'] for r in results)
    total_newsapi = sum(r['newsapi'] for r in results)
    total_gnews = sum(r['gnews'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    
    print("\n" + "="*80)
    print("??? COLLECTE OPTIMIS??E TERMIN??E")
    print("="*80)
    print(f"???? Entreprises trait??es: {len(results)}/{len(companies)}")
    print(f"???? Articles existants: {total_existing}")
    print(f"???? Nouveaux articles: {total_new}")
    print(f"   ???? NewsAPI: {total_newsapi}")
    print(f"   ???? GNews: {total_gnews}")
    print(f"???? Total final: {total_existing + total_new}")
    print(f"??????  Dur??e: {elapsed:.1f} minutes")
    print(f"???? Vitesse: {total_new/elapsed:.0f} articles/min" if elapsed > 0 else "")
    print(f"???? Requ??tes utilis??es: {requests_counter['count']}/{MAX_REQUESTS_PER_DAY}")
    print(f"??? Erreurs: {total_errors}")
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
    
    if len(results) < len(companies):
        remaining = len(companies) - len(results)
        print(f"\n???? {remaining} entreprises restantes - relancer demain pour continuer")

if __name__ == "__main__":
    days = 100
    
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass
    
    collect_all_optimized(days=days, sequential=True)
