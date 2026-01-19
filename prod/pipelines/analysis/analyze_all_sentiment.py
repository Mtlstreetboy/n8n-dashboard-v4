#!/usr/bin/env python3
"""
[BATCH] ANALYSE DE SENTIMENT - TOUTES LES COMPAGNIES
Genere un rapport consolide lisible
"""
import sys
sys.path.insert(0, '/data/scripts')
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configure FinBERT API URL for microservice mode
import os
os.environ['FINBERT_API_URL'] = 'http://localhost:8089'

import sys
# Add parent dir to path for config import
# Go up 3 levels: analysis -> pipelines -> prod
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.companies_config import get_all_companies

import subprocess
import json
import glob
from datetime import datetime

# Output dir setup
# Output dir setup
if sys.platform != 'win32' and os.path.exists('/data/sentiment_analysis'):
    OUTPUT_DIR = '/data/sentiment_analysis'
else:
    # Windows Local environment - Force path relative to project root based on SCRIPT location
    # Script is in prod/analysis/analyze_all_sentiment.py -> Root is ../../../..
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    OUTPUT_DIR = os.path.join(project_root, 'local_files', 'sentiment_analysis')

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
            # Détection de l'environnement pour les chemins
            if os.path.exists('/data/scripts'):
                # Docker environment
                cmd = ['python3', '/data/scripts/advanced_sentiment_engine_v4.py', ticker]
                cwd = '/data/scripts'
            else:
                # Windows Local environment - use absolute path
                script_dir = os.path.dirname(os.path.abspath(__file__))
                engine_path = os.path.join(script_dir, 'advanced_sentiment_engine_v4.py')
                cmd = [sys.executable, engine_path, ticker]
                
                # Pass --no-llm if present in parent args
                if '--no-llm' in sys.argv:
                    cmd.append('--no-llm')
                
                cwd = os.getcwd()

            # SMART CACHE CHECK (User request: skip < 7 days)
            should_run = True
            latest_file = os.path.join(OUTPUT_DIR, f"{ticker}_latest_v4.json")
            
            if os.path.exists(latest_file) and '--force' not in sys.argv:
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                        ts_str = cached_data.get('timestamp')
                        if ts_str:
                            last_run = datetime.fromisoformat(ts_str) if 'T' in ts_str else datetime.now()
                            age_days = (datetime.now() - last_run).days
                            
                            if age_days < 7:
                                print(f"  ⚡ [CACHE] Skip analyse (Données récentes: {age_days} jours < 7. Use --force to override)")
                                should_run = False
                                
                                # Add to results for potential consolidated report
                                results.append(cached_data) 
                except Exception:
                    pass # Force analysis on error

            if should_run:
                # Lancer l'analyse avec sortie en temps réel (V4 DUEL BRAIN)
                result = subprocess.run(
                    cmd,
                    capture_output=False,
                    timeout=300, # Augmenté pour V4 (chargement modèles)
                    env=os.environ.copy(), # Hériter de l'environnement actuel
                    cwd=cwd
                )
                
                if result.returncode != 0:
                    print(f"  [!] Erreur execution (code {result.returncode})")
                    continue
            else:
                # If skipped, ensure we consider it a success for the loop's continuation
                pass
            
            # Charger le fichier _latest_v4.json cr???? par advanced_sentiment_engine_v4.py
            latest_file = os.path.join(OUTPUT_DIR, f"{ticker}_latest_v4.json")
            
            if os.path.exists(latest_file):
                with open(latest_file, 'r', encoding='utf-8') as f:
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

    # [NEW] Export specific for Dashboard V4 (Dict format, prod/dashboard)
    # Format expected by dashboard: { "TICKER": { ... }, ... }
    dashboard_data = {r['ticker']: r for r in results}
    
    # Determine dashboard path (assuming standard structure)
    # script is in prod/analysis, dashboard is in prod/dashboards/generators
    # We want: .../prod/dashboards/generators
    prod_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dashboard_dir = os.path.join(prod_dir, 'dashboards', 'generators')
    
    if os.path.exists(dashboard_dir):
        dashboard_file = os.path.join(dashboard_dir, 'consolidated_sentiment_data.json')
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2)
        print(f"[EXPORT] DASHBOARD DATA: {dashboard_file}")
    else:
        print(f"[!] Dashboard directory not found: {dashboard_dir}")

    print("="*80 + "\n")

if __name__ == "__main__":
    analyze_all_companies()
