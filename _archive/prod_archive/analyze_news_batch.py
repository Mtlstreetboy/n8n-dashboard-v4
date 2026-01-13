#!/usr/bin/env python3
"""
???? ANALYSE BATCH LLM - TOUTES LES COMPAGNIES
Lance l'analyse Llama3 sur tous les articles collect??s
"""
import sys
sys.path.insert(0, '/data/scripts')

from companies_config import get_all_companies
import subprocess
import json
import os

def analyze_all_news():
    """Lance l'analyse LLM pour toutes les compagnies avec donn??es news"""
    
    companies = get_all_companies()
    news_dir = '/data/files/companies'
    
    # Trouver les compagnies avec fichiers news JSON
    companies_with_news = []
    for company in companies:
        ticker = company['ticker']
        news_file = os.path.join(news_dir, f'{ticker}_news.json')
        if os.path.exists(news_file):
            # Compter articles
            try:
                with open(news_file, 'r') as f:
                    data = json.load(f)
                    article_count = len(data) if isinstance(data, list) else len(data.get('articles', []))
                    if article_count > 0:
                        companies_with_news.append((ticker, article_count, company['name']))
            except:
                continue
    
    print("="*80)
    print("ANALYSE BATCH LLM (LLAMA3) - SENTIMENT DES ARTICLES")
    print(f"Compagnies avec donn??es: {len(companies_with_news)}")
    print("="*80)
    
    for i, (ticker, count, name) in enumerate(companies_with_news, 1):
        print(f"\n[{i}/{len(companies_with_news)}] {ticker} - {name}")
        print(f"    Articles ?? analyser: {count}")
        
        try:
            # Lancer analyze_news.py
            result = subprocess.run(
                ['python3', '/data/scripts/analyze_news.py', ticker],
                capture_output=True,
                text=True,
                timeout=300  # 5 min max
            )
            
            # Afficher progression
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'Analyse' in line or 'articles' in line or 'COMPLETE' in line:
                    print(f"    {line.strip()}")
            
            if result.returncode == 0:
                print(f"    ??? SUCCES")
            else:
                print(f"    ??? ERREUR: {result.stderr[:200]}")
                
        except subprocess.TimeoutExpired:
            print(f"    ??? TIMEOUT (>5min)")
        except Exception as e:
            print(f"    ??? EXCEPTION: {str(e)}")
    
    print("\n" + "="*80)
    print("ANALYSE BATCH TERMINEE")
    print("="*80)

if __name__ == "__main__":
    analyze_all_news()
