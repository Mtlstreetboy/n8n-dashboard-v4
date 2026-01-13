#!/usr/bin/env python3
"""
🎯 NEWS ANALYZER V1 - Analyse de sentiment des articles collectés
--------------------------------------------------------------------
Partie 2 du pipeline: Analyse UNIQUEMENT (articles déjà collectés)
Utilise FinBERT pour l'analyse contextuelle par ticker

Prérequis:
    - Articles collectés via news_collector.py
    - FinBERT Docker en cours: docker-compose -f docker-compose.finbert.gpu.yml up -d

Usage:
    python news_analyzer.py              # Analyser tous les articles sans sentiment
    python news_analyzer.py --force      # Ré-analyser tous les articles
    python news_analyzer.py NVDA AMD     # Analyser seulement ces tickers
"""
import sys
import os

# Environment Detection
if os.path.exists('/data/scripts'):
    sys.path.insert(0, '/data/scripts')
    DATA_FILES_DIR = '/data/files'
else:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Go up 2 levels: collection -> pipelines -> prod
    PIPELINES_DIR = os.path.dirname(CURRENT_DIR)
    PROD_ROOT = os.path.dirname(PIPELINES_DIR)
    PROJECT_ROOT = os.path.dirname(PROD_ROOT) # C:\n8n-local-stack
    
    # We need PROD_ROOT in sys.path to import from 'config'
    sys.path.insert(0, PROD_ROOT)
    # We ALSO need PIPELINES_DIR in sys.path to import from 'analysis' (which is in pipelines/analysis)
    sys.path.insert(0, PIPELINES_DIR)
    DATA_FILES_DIR = os.path.join(PROJECT_ROOT, 'local_files')

import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

# Rich pour affichage
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from tqdm import tqdm
    RICH_AVAILABLE = True
except ImportError:
    print("📦 Installation de rich et tqdm...")
    os.system("pip install rich tqdm -q")
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from tqdm import tqdm
    RICH_AVAILABLE = True

# Analyseur contextuel FinBERT
from analysis.contextual_sentiment_analyzer import (
    analyze_contextual_sentiment,
    format_sentiment_for_storage,
    check_finbert_health
)

# Config
from config.companies_config import get_all_companies

console = Console()

# Configuration
NEWS_DATA_DIR = os.path.join(DATA_FILES_DIR, 'companies')
MAX_PARALLEL_ANALYSIS = 4  # Limité car FinBERT est GPU-intensive


class NewsAnalyzer:
    """Analyseur de sentiment pour les articles collectés"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.cache_file = os.path.join(NEWS_DATA_DIR, f'{ticker}_news.json')
        self.data = self._load_data()
        self.analyzed_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    def _load_data(self) -> dict:
        """Charge les données du fichier"""
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'articles' in data:
                return data
            elif isinstance(data, list):
                return {'ticker': self.ticker, 'articles': data}
            
        except Exception as e:
            console.print(f"  ⚠️ Erreur lecture {self.ticker}: {e}", style="yellow")
        
        return None
    
    def _save_data(self):
        """Sauvegarde les données analysées"""
        if not self.data:
            return
        
        # Backup avant sauvegarde
        if os.path.exists(self.cache_file):
            backup_file = self.cache_file.replace('.json', '_backup.json')
            import shutil
            shutil.copy(self.cache_file, backup_file)
        
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def analyze_articles(self, force: bool = False, progress_bar=None) -> dict:
        """
        Analyse le sentiment de tous les articles
        
        Args:
            force: Si True, ré-analyse même les articles déjà analysés
        """
        if not self.data:
            return {
                'ticker': self.ticker,
                'success': False,
                'error': 'No data file'
            }
        
        articles = self.data.get('articles', [])
        
        for article in articles:
            # Skip si déjà analysé (sauf si force)
            if not force and article.get('sentiment') is not None:
                # Vérifier que le sentiment est valide (pas juste None)
                sent = article.get('sentiment', {})
                if isinstance(sent, dict) and sent.get('compound') is not None:
                    self.skipped_count += 1
                    if progress_bar:
                        progress_bar.update(1)
                    continue
            
            # Analyser l'article
            try:
                title = article.get('title', '')
                description = article.get('description', '') or article.get('content', '')
                
                if not title and not description:
                    self.skipped_count += 1
                    if progress_bar:
                        progress_bar.update(1)
                    continue
                
                # Analyse contextuelle
                result = analyze_contextual_sentiment(
                    title=title,
                    description=description,
                    target_ticker=self.ticker
                )
                
                if result:
                    article['sentiment'] = format_sentiment_for_storage(result)
                    article['sentiment_analyzed_at'] = datetime.now().isoformat()
                    self.analyzed_count += 1
                else:
                    self.error_count += 1
                
            except Exception as e:
                self.error_count += 1
            
            if progress_bar:
                progress_bar.update(1)
        
        # Sauvegarder
        self._save_data()
        
        return {
            'ticker': self.ticker,
            'success': True,
            'analyzed': self.analyzed_count,
            'skipped': self.skipped_count,
            'errors': self.error_count,
            'total': len(articles)
        }


def get_articles_needing_analysis(ticker: str) -> int:
    """Compte les articles sans sentiment pour un ticker"""
    cache_file = os.path.join(NEWS_DATA_DIR, f'{ticker}_news.json')
    
    if not os.path.exists(cache_file):
        return 0
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('articles', []) if isinstance(data, dict) else data
        
        count = 0
        for article in articles:
            sent = article.get('sentiment')
            if sent is None or (isinstance(sent, dict) and sent.get('compound') is None):
                count += 1
        
        return count
    except:
        return 0


def analyze_single_ticker(ticker: str, force: bool = False) -> dict:
    """Analyse un ticker"""
    analyzer = NewsAnalyzer(ticker)
    
    total_articles = len(analyzer.data.get('articles', [])) if analyzer.data else 0
    
    with tqdm(
        total=total_articles,
        desc=f"🎯 {ticker}",
        unit="art",
        leave=False,
        ncols=80
    ) as pbar:
        return analyzer.analyze_articles(force=force, progress_bar=pbar)


def analyze_all(tickers: List[str] = None, force: bool = False):
    """Analyse tous les tickers ou une sélection"""
    
    # Vérifier FinBERT d'abord
    console.print("\n🔍 Vérification de FinBERT...", style="yellow")
    if not check_finbert_health():
        console.print("\n❌ FinBERT n'est pas accessible. Démarrez Docker:", style="bold red")
        console.print("   docker-compose -f docker-compose.finbert.gpu.yml up -d", style="yellow")
        return {'success': False, 'error': 'FinBERT not available'}
    
    # Déterminer les tickers à analyser
    if tickers:
        companies = [{'ticker': t} for t in tickers]
    else:
        companies = get_all_companies()
    
    # Filtrer ceux qui ont des articles à analyser
    tickers_to_process = []
    for company in companies:
        ticker = company['ticker']
        count = get_articles_needing_analysis(ticker) if not force else -1
        
        cache_file = os.path.join(NEWS_DATA_DIR, f'{ticker}_news.json')
        if os.path.exists(cache_file):
            if force or count > 0:
                tickers_to_process.append((ticker, count))
    
    if not tickers_to_process:
        console.print("\n✅ Tous les articles sont déjà analysés!", style="green")
        return {'success': True, 'analyzed': 0}
    
    console.print("\n" + "="*70, style="bold magenta")
    console.print("🎯 NEWS ANALYZER V1 - FinBERT Contextuel", style="bold magenta", justify="center")
    console.print("="*70 + "\n", style="bold magenta")
    
    # Info config
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Param", style="cyan")
    config_table.add_column("Value", style="green bold")
    config_table.add_row("📊 Tickers à analyser", str(len(tickers_to_process)))
    config_table.add_row("🔄 Mode", "Force (ré-analyse)" if force else "Incremental")
    console.print(Panel(config_table, title="Configuration", border_style="magenta"))
    
    # Liste des tickers
    console.print("\n📋 Tickers:", style="cyan")
    for ticker, count in tickers_to_process:
        if count >= 0:
            console.print(f"   • {ticker}: {count} articles à analyser")
        else:
            console.print(f"   • {ticker}: ré-analyse complète")
    console.print()
    
    start_time = time.time()
    results = []
    
    # Traitement séquentiel (FinBERT GPU ne supporte pas bien le parallélisme extrême)
    for ticker, _ in tickers_to_process:
        result = analyze_single_ticker(ticker, force=force)
        results.append(result)
        
        if result['success']:
            console.print(
                f"  ✅ {result['ticker']:8} | "
                f"🆕 {result['analyzed']:3} analysés | "
                f"⏭️ {result['skipped']:3} skippés | "
                f"❌ {result['errors']} erreurs"
            )
        else:
            console.print(f"  ❌ {result['ticker']:8} | {result.get('error', 'Unknown')}", style="red")
    
    # Rapport final
    elapsed = time.time() - start_time
    
    total_analyzed = sum(r.get('analyzed', 0) for r in results)
    total_skipped = sum(r.get('skipped', 0) for r in results)
    total_errors = sum(r.get('errors', 0) for r in results)
    
    console.print("\n" + "="*70, style="bold green")
    console.print("🎉 ANALYSE TERMINÉE", style="bold green", justify="center")
    console.print("="*70, style="bold green")
    
    results_table = Table(show_header=False, box=None)
    results_table.add_column("Métrique", style="cyan")
    results_table.add_column("Valeur", style="green bold")
    results_table.add_row("🆕 Articles analysés", f"{total_analyzed:,}")
    results_table.add_row("⏭️ Articles skippés", f"{total_skipped:,}")
    results_table.add_row("❌ Erreurs", str(total_errors))
    results_table.add_row("⏱️ Durée", f"{elapsed:.1f}s")
    results_table.add_row("⚡ Vitesse", f"{total_analyzed / max(elapsed, 0.1):.1f} art/s")
    
    console.print(Panel(results_table, title="Résultats", border_style="green"))
    
    return {
        'success': True,
        'analyzed': total_analyzed,
        'skipped': total_skipped,
        'errors': total_errors,
        'duration': elapsed
    }


def main():
    """Point d'entrée principal"""
    force = '--force' in sys.argv
    
    # Récupérer les tickers spécifiques (arguments sans --)
    tickers = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    tickers = tickers if tickers else None
    
    stats = analyze_all(tickers=tickers, force=force)
    
    if stats.get('success'):
        console.print("\n✅ Analyse terminée!", style="bold green")
        console.print("   Les sentiments sont maintenant dans les fichiers *_news.json", style="dim")
    
    return 0 if stats.get('success') else 1


if __name__ == "__main__":
    sys.exit(main())
