#!/usr/bin/env python3
"""
???? AUTOMATISATION QUOTIDIENNE - SENTIMENT ANALYSIS
Lance la collecte, l'analyse et la g??n??ration de rapports
"""
import sys
sys.path.insert(0, '/data/scripts')

import subprocess
import time
import json
import os
from datetime import datetime

LOG_DIR = '/tmp'
DATA_DIR = '/data/sentiment_analysis'

def log(message):
    """Log avec timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    
    # Sauvegarder dans fichier log
    log_file = os.path.join(LOG_DIR, 'daily_automation.log')
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def run_command(command, description, timeout=300):
    """Ex??cute une commande avec gestion d'erreur"""
    log(f"???? {description}...")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd='/data/scripts'
        )
        
        if result.returncode == 0:
            log(f"??? {description} - SUCCESS")
            return True
        else:
            log(f"??? {description} - FAILED (code {result.returncode})")
            if result.stderr:
                log(f"   Erreur: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"?????? {description} - TIMEOUT (>{timeout}s)")
        return False
    except Exception as e:
        log(f"???? {description} - EXCEPTION: {str(e)}")
        return False

def check_quota_status():
    """V??rifie si on peut lancer la collecte news"""
    # Checker le dernier run de collect_news
    news_files = []
    for ticker in ['NVDA', 'MSFT', 'GOOGL']:
        file_path = f'/data/files/companies/{ticker}_news.json'
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            news_files.append(mtime)
    
    if news_files:
        last_update = max(news_files)
        hours_since = (time.time() - last_update) / 3600
        
        if hours_since < 12:
            log(f"?????? News collect??es il y a {hours_since:.1f}h - SKIP collection news")
            return False
        else:
            log(f"??? News collect??es il y a {hours_since:.1f}h - OK pour collecter")
            return True
    
    return True

def main():
    """Pipeline quotidien"""
    log("="*80)
    log("???? AUTOMATISATION QUOTIDIENNE - DEBUT")
    log("="*80)
    
    start_time = time.time()
    success_count = 0
    total_steps = 4
    
    # ETAPE 1: Collecter les options (rapide, pas de quota)
    if run_command(
        ['python3', '/data/scripts/collect_options.py'],
        "Collecte donn??es options (Yahoo Finance)",
        timeout=180
    ):
        success_count += 1
    
    # ETAPE 2: Collecter les news (Batch Loader V2 - Incremental)
    # On lance sur 2 jours pour couvrir la journ??e et la veille
    if run_command(
        ['python3', '/data/scripts/batch_loader_v2.py', '2'],
        "Collecte articles news (Batch V2 - Incremental)",
        timeout=600
    ):
        success_count += 1
    
    # ETAPE 3: Analyser le sentiment (multi-dimensionnel)
    if run_command(
        ['python3', '/data/scripts/analyze_all_sentiment.py'],
        "Analyse sentiment multi-dimensionnelle (15 compagnies)",
        timeout=600
    ):
        success_count += 1
    
    # ETAPE 4: G??n??rer les statistiques
    try:
        consolidated_file = os.path.join(DATA_DIR, 'consolidated_sentiment_report.json')
        if os.path.exists(consolidated_file):
            with open(consolidated_file, 'r') as f:
                data = json.load(f)
            
            stats = data['statistics']
            log(f"???? STATISTIQUES:")
            log(f"   Total compagnies: {data['total_companies']}")
            log(f"   Score moyen: {stats['average_score']:+.4f}")
            log(f"   Bullish: {stats['bullish_count']} | Neutral: {stats['neutral_count']} | Bearish: {stats['bearish_count']}")
            
            # Top 3
            top3 = sorted(data['companies'], key=lambda x: x['final_sentiment_score'], reverse=True)[:3]
            top3_str = ', '.join([f"{c['ticker']} ({c['final_sentiment_score']:+.3f})" for c in top3])
            log(f"   Top 3: {top3_str}")
            
            success_count += 1
        else:
            log("?????? Fichier consolid?? non trouv??")
            
    except Exception as e:
        log(f"??? Erreur lecture stats: {str(e)}")
    
    # RESUME
    elapsed = time.time() - start_time
    log("="*80)
    log(f"???? AUTOMATISATION QUOTIDIENNE - FIN")
    log(f"   Succ??s: {success_count}/{total_steps} ??tapes")
    log(f"   Dur??e: {elapsed:.1f}s ({elapsed/60:.1f}min)")
    log("="*80)
    
    # Code de sortie
    if success_count >= total_steps - 1:  # Au moins 3/4 OK
        log("??? AUTOMATION SUCCESS")
        return 0
    else:
        log("??? AUTOMATION FAILED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
