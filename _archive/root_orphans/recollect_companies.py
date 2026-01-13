#!/usr/bin/env python3
"""
Relance la collecte pour toutes les compagnies (100 derniers jours)
Augmente max_results a 20 et deduplique automatiquement
"""
import sys
sys.path.insert(0, '/data/scripts')

from collect_companies import collect_company_day, save_articles, load_existing_articles
from companies_config import get_all_companies
from datetime import datetime
import time

def recollect_all_companies(days=100):
    """Relance la collecte pour les 100 derniers jours"""
    
    companies = get_all_companies()
    
    print("=" * 80)
    print(f"RECOLLECTE COMPLETE - {days} derniers jours - max_results=20")
    print("=" * 80)
    
    for company in companies:
        ticker = company['ticker']
        company_name = company['name']
        
        print(f"\n[{ticker}] Debut recollecte...")
        
        # Charge articles existants pour dedupliquer
        existing_articles = load_existing_articles(ticker)
        existing_urls = {a.get('url') for a in existing_articles}
        
        new_articles_count = 0
        
        # Collecte jour par jour
        for day_offset in range(days):
            if day_offset % 10 == 0:
                print(f"  [{ticker}] Jour {day_offset}/{days}...")
            
            try:
                result = collect_company_day(company, day_offset, existing_urls)
                
                if result['success'] and result['articles']:
                    # Ajoute les nouveaux articles
                    for article in result['articles']:
                        if article['url'] not in existing_urls:
                            existing_articles.append(article)
                            existing_urls.add(article['url'])
                            new_articles_count += 1
                
                # Rate limit Google News
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  [{ticker}] Erreur jour {day_offset}: {str(e)[:50]}")
                continue
        
        # Sauvegarde tous les articles (anciens + nouveaux)
        save_articles(ticker, company_name, existing_articles)
        
        print(f"[{ticker}] Termine: {new_articles_count} nouveaux articles | Total: {len(existing_articles)}")
        time.sleep(2)  # Pause entre compagnies
    
    print("\n" + "=" * 80)
    print("RECOLLECTE TERMINEE")
    print("=" * 80)

if __name__ == '__main__':
    recollect_all_companies(days=100)
