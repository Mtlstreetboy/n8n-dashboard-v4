#!/usr/bin/env python3
"""
[BATCH] ANALYSE DE SENTIMENT - TOUTES LES COMPAGNIES
Genere un rapport consolide lisible
"""
import sys
sys.path.insert(0, '/data/scripts')

from companies_config import get_all_companies
import subprocess
import json
import os
import glob
from datetime import datetime

OUTPUT_DIR = '/data/sentiment_analysis'

def analyze_all_companies():
    """Analyse toutes les compagnies avec options"""
    companies = get_all_companies()
    
    # Filtrer les compagnies publiques (avec options)
    public_companies = [c for c in companies 
                       if c['ticker'] not in ['OPENAI', 'ANTHROPIC', 'COHERE', 'MISTRAL']]
    
    print("="*80)
    print("[BATCH] ANALYSE SENTIMENT MULTI-DIMENSIONNEL")
    print(f"Compagnies a analyser: {len(public_companies)}")
    print("="*80)
    
    results = []
    
    for i, company in enumerate(public_companies, 1):
        ticker = company['ticker']
        print(f"\n[{i}/{len(public_companies)}] Analyse de {ticker}...")
        
        try:
            # Lancer l'analyse avec sortie en temps r??el
            result = subprocess.run(
                ['python3', '/data/scripts/advanced_sentiment_engine_v2.py', ticker],
                capture_output=False,
                timeout=120,
                env={
                    'PYTHONIOENCODING': 'utf-8',
                    'LANG': 'en_US.UTF-8',
                    'LC_ALL': 'en_US.UTF-8',
                    'PATH': os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin'),
                    'PYTHONPATH': '/data/scripts'
                },
                cwd='/data/scripts'
            )
            
            if result.returncode != 0:
                print(f"  [!] Erreur execution (code {result.returncode})")
                continue
            
            # Charger le fichier _latest.json cr???? par advanced_sentiment_engine.py
            latest_file = os.path.join(OUTPUT_DIR, f"{ticker}_latest.json")
            
            if os.path.exists(latest_file):
                with open(latest_file, 'r') as f:
                    report = json.load(f)
                
                results.append(report)
                score = report.get('final_sentiment_score', 0)
                classification = report.get('classification', 'UNKNOWN')
                conviction = report.get('conviction_score', 0)
                print(f"\n  [OK] {ticker}: {score:+.4f} | {classification} | Conviction: {conviction:.2%}\n")
            else:
                print(f"  [!] ECHEC - Fichier non trouve: {latest_file}")
                
        except subprocess.TimeoutExpired:
            print(f"  [!] TIMEOUT - Analyse trop longue (>90s)")
            continue
        except Exception as e:
            print(f"  [!] ERREUR: {str(e)}")
            continue
    
    # G??n??rer rapport consolid??
    generate_consolidated_report(results)
    
    return results

def generate_consolidated_report(results):
    """G??n??re un rapport consolid?? CSV et JSON"""
    
    # Trier par score
    sorted_results = sorted(results, key=lambda x: x['final_sentiment_score'], reverse=True)
    
    print("\n" + "="*80)
    print("[RAPPORT CONSOLIDE] CLASSEMENT PAR SENTIMENT")
    print("="*80)
    print(f"{'Ticker':<8} {'Score':<10} {'Class.':<15} {'Conviction':<12} {'Divergence':<20}")
    print("-"*80)
    
    for r in sorted_results:
        ticker = r['ticker']
        score = r['final_sentiment_score']
        classification = r['classification']
        conviction = r['conviction_score']
        div_type = r['divergence_analysis']['type']
        
        print(f"{ticker:<8} {score:+.4f}     {classification:<15} {conviction:<11.2%} {div_type:<20}")
    
    print("-"*80)
    
    if not results:
        print("\n[!] Aucun resultat a consolider")
        return
    
    # Stats globales
    avg_score = sum(r['final_sentiment_score'] for r in results) / len(results)
    bullish_count = sum(1 for r in results if r['final_sentiment_score'] > 0.2)
    bearish_count = sum(1 for r in results if r['final_sentiment_score'] < -0.2)
    neutral_count = len(results) - bullish_count - bearish_count
    
    print(f"\n[STATISTIQUES GLOBALES]")
    print(f"  Score moyen:  {avg_score:+.4f}")
    print(f"  Distribution: Bullish={bullish_count} | Neutral={neutral_count} | Bearish={bearish_count}")
    
    # Sauvegarder CSV
    import csv
    csv_file = os.path.join(OUTPUT_DIR, 'consolidated_sentiment_report.csv')
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'ticker', 'score', 'classification', 'confidence_level', 'conviction',
            'news_sentiment', 'options_sentiment', 'momentum', 'divergence_type',
            'news_articles', 'options_volume'
        ])
        writer.writeheader()
        
        for r in sorted_results:
            writer.writerow({
                'ticker': r['ticker'],
                'score': round(r['final_sentiment_score'], 4),
                'classification': r['classification'],
                'confidence_level': r['confidence_level'],
                'conviction': round(r['conviction_score'], 4),
                'news_sentiment': round(r['components']['news_sentiment'], 4),
                'options_sentiment': round(r['components']['options_sentiment'], 4),
                'momentum': round(r['components']['narrative_momentum'], 4),
                'divergence_type': r['divergence_analysis']['type'],
                'news_articles': r['metadata']['news_articles_count'],
                'options_volume': r['metadata']['options_volume']
            })
    
    print(f"\n[EXPORT] CSV: {csv_file}")
    
    # Sauvegarder JSON consolide
    json_file = os.path.join(OUTPUT_DIR, 'consolidated_sentiment_report.json')
    consolidated = {
        'generated_at': datetime.now().isoformat(),
        'total_companies': len(results),
        'statistics': {
            'average_score': round(avg_score, 4),
            'bullish_count': bullish_count,
            'neutral_count': neutral_count,
            'bearish_count': bearish_count
        },
        'companies': sorted_results
    }
    
    with open(json_file, 'w') as f:
        json.dump(consolidated, f, indent=2)
    
    print(f"[EXPORT] JSON: {json_file}")
    print("="*80 + "\n")

if __name__ == "__main__":
    analyze_all_companies()
