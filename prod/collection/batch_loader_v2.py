#!/usr/bin/env python3
"""
🚀 BATCH LOADER V2.1 - Parallélisation + Monitoring Visuel
--------------------------------------------------------------------
Ajouts V2.1:
- Barres de progression live avec tqdm
- Affichage riche avec rich (tableau temps réel)
- Métriques de rate limiting
- ETA précis
"""
import sys
import os

# Environment Detection
if os.path.exists('/data/scripts'):
    sys.path.insert(0, '/data/scripts')
    DATA_FILES_DIR = '/data/files'
else:
    # Local Windows
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, CURRENT_DIR)
    PROD_DIR = os.path.dirname(CURRENT_DIR)
    PROJECT_ROOT = os.path.dirname(PROD_DIR)
    sys.path.append(PROD_DIR) # Add prod to path for config import
    DATA_FILES_DIR = os.path.join(PROJECT_ROOT, 'local_files')
import json
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import traceback

from gnews import GNews
from config.companies_config import get_all_companies

# STRICT: Analyseur de sentiment contextualisé par ticker (OBLIGATOIRE)
# Si l'import échoue, le script crashera intentionnellement
from analysis.contextual_sentiment_analyzer import analyze_contextual_sentiment, format_sentiment_for_storage
print("🎯 Analyse contextuelle par ticker activée (MODE STRICT)")

# Imports pour monitoring visuel
try:
    from tqdm import tqdm
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
    RICH_AVAILABLE = True
except ImportError:
    print("📦 Installation de tqdm et rich pour monitoring visuel...")
    os.system("pip install tqdm rich -q")
    from tqdm import tqdm
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
    RICH_AVAILABLE = True

console = Console()

# Configuration
NEWS_DATA_DIR = os.path.join(DATA_FILES_DIR, 'companies')
MAX_PARALLEL_TICKERS = 6
MAX_WORKERS_PER_TICKER = 16
DAYS_TO_SCRAPE = 160
RATE_LIMIT_GOOGLE = 0.5
RATE_LIMIT_YAHOO = 0.2

class GlobalRateLimiter:
    """Rate limiter thread-safe avec métriques"""
    
    def __init__(self):
        self.locks = {
            'google': Lock(),
            'yahoo': Lock()
        }
        self.last_request = {
            'google': 0,
            'yahoo': 0
        }
        self.wait_count = {
            'google': 0,
            'yahoo': 0
        }
        self.total_wait_time = {
            'google': 0,
            'yahoo': 0
        }
    
    def wait_if_needed(self, source='google'):
        """Attend si nécessaire avec tracking des métriques"""
        with self.locks[source]:
            elapsed = time.time() - self.last_request[source]
            delay = RATE_LIMIT_GOOGLE if source == 'google' else RATE_LIMIT_YAHOO
            
            if elapsed < delay:
                wait_time = delay - elapsed
                time.sleep(wait_time)
                self.wait_count[source] += 1
                self.total_wait_time[source] += wait_time
            
            self.last_request[source] = time.time()
    
    def get_stats(self):
        """Retourne les stats de rate limiting"""
        return {
            'google_waits': self.wait_count['google'],
            'google_wait_time': self.total_wait_time['google'],
            'yahoo_waits': self.wait_count['yahoo'],
            'yahoo_wait_time': self.total_wait_time['yahoo']
        }

rate_limiter = GlobalRateLimiter()

class HistoricalEngine:
    """Moteur de collecte historique avec progress tracking"""
    
    def __init__(self, ticker, company_name, search_terms):
        self.ticker = ticker
        self.company_name = company_name
        self.search_terms = search_terms if isinstance(search_terms, list) else [ticker]
        self.cache_file = os.path.join(NEWS_DATA_DIR, f'{ticker}_news.json')
        self.cache = self._load_cache()
        
        # STRICT: Analyseur de sentiment contextualisé uniquement
        self.sentiment_analyzer = None  # Pas besoin d'objet, fonction directe
        self.sentiment_model = 'finbert_contextual'
        self.use_contextual = True
    
    def _load_cache(self):
        """Charge le cache existant avec gestion d'erreur"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'articles' in data:
                    # Assurer que fetched_dates existe
                    if 'fetched_dates' not in data:
                        data['fetched_dates'] = []
                    return data
                elif isinstance(data, list):
                    return {'ticker': self.ticker, 'articles': data, 'fetched_dates': []}
            except Exception as e:
                backup_file = self.cache_file.replace('.json', '_backup.json')
                if os.path.exists(self.cache_file):
                    import shutil
                    shutil.copy(self.cache_file, backup_file)
        
        return {'ticker': self.ticker, 'articles': [], 'fetched_dates': []}
    
    def _save_cache(self):
        """Sauvegarde le cache avec backup automatique"""
        os.makedirs(NEWS_DATA_DIR, exist_ok=True)
        
        if os.path.exists(self.cache_file):
            backup_file = self.cache_file.replace('.json', '_backup.json')
            import shutil
            shutil.copy(self.cache_file, backup_file)
        
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def _fetch_single_day(self, date_obj):
        """Fetch articles pour un jour spécifique"""
        try:
            rate_limiter.wait_if_needed('google')
            
            gnews = GNews(
                language='en',
                country='US',
                max_results=20,
                period=None
            )
            
            articles = []
            for term in self.search_terms:
                try:
                    results = gnews.get_news(term)
                    
                    for item in results:
                        try:
                            pub_date_str = item.get('published date', '')
                            pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                            if pub_date.tzinfo is None:
                                pub_date = pub_date.replace(tzinfo=timezone.utc)
                            
                            days_diff = abs((pub_date.date() - date_obj.date()).days)
                            if days_diff <= 1:
                                title = item.get('title', '')
                                description = item.get('description', '')
                                
                                # STRICT: Analyse de sentiment CONTEXTUELLE par ticker (OBLIGATOIRE)
                                contextual_result = analyze_contextual_sentiment(
                                    title=title,
                                    description=description,
                                    target_ticker=self.ticker
                                )
                                
                                if contextual_result:
                                    sentiment_data = format_sentiment_for_storage(contextual_result)
                                else:
                                    # Si l'analyse échoue, on skip cet article (pas de fallback)
                                    continue
                                
                                article = {
                                    'title': title,
                                    'url': item.get('url', ''),
                                    'published_at': pub_date.isoformat(),
                                    'description': description,
                                    'content': description,  # Garder les deux pour compatibilité
                                    'source': item.get('publisher', {}).get('title', 'Unknown'),
                                    'ticker': self.ticker,
                                    'company_name': self.company_name,
                                    'collected_at': datetime.now(timezone.utc).isoformat(),
                                    'sentiment': sentiment_data
                                }
                                articles.append(article)
                        except Exception as e:
                            continue
                
                except Exception as e:
                    continue
            
            return {
                'date': date_obj.strftime('%Y-%m-%d'),
                'articles': articles,
                'success': True
            }
        
        except Exception as e:
            return {
                'date': date_obj.strftime('%Y-%m-%d'),
                'articles': [],
                'success': False,
                'error': str(e)
            }
    
    def run_time_machine(self, days=160, progress_bar=None):
        """Collecte historique avec progress bar - MODE DELTA (saute les dates déjà tentées)"""
        existing_urls = {a['url'] for a in self.cache['articles'] if 'url' in a}
        
        # MODE DELTA AMÉLIORÉ: vérifier les dates déjà tentées (avec ou sans résultats)
        fetched_dates_set = set(self.cache.get('fetched_dates', []))
        
        # Aussi ajouter les dates où on a trouvé des articles
        for article in self.cache.get('articles', []):
            pub = article.get('published_at', '')
            if pub and isinstance(pub, str) and len(pub) >= 10:
                fetched_dates_set.add(pub[:10])
        
        # Générer liste des dates à fetcher, en sautant celles déjà tentées
        dates_to_fetch = []
        skipped_dates = 0
        for i in range(days):
            date_obj = datetime.now(timezone.utc) - timedelta(days=i)
            date_str = date_obj.strftime('%Y-%m-%d')
            
            if date_str in fetched_dates_set:
                skipped_dates += 1
            else:
                dates_to_fetch.append(date_obj)
        
        # Log delta info
        console.print(f"   ⏭️  [yellow]Delta mode:[/yellow] {skipped_dates}/{days} jours déjà tentés, {len(dates_to_fetch)} à fetcher")
        
        new_articles = []
        errors = 0
        newly_fetched_dates = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS_PER_TICKER) as executor:
            futures = {executor.submit(self._fetch_single_day, date): date for date in dates_to_fetch}
            
            for future in as_completed(futures):
                date = futures[future]
                date_str = date.strftime('%Y-%m-%d')
                
                try:
                    result = future.result()
                    
                    # Historiser cette date (même si 0 articles trouvés)
                    newly_fetched_dates.append(date_str)
                    
                    if result['success']:
                        for article in result['articles']:
                            if article['url'] not in existing_urls:
                                new_articles.append(article)
                                existing_urls.add(article['url'])
                    else:
                        errors += 1
                    
                    if progress_bar:
                        progress_bar.update(1)
                
                except Exception as e:
                    # Historiser même en cas d'erreur
                    newly_fetched_dates.append(date_str)
                    errors += 1
                    if progress_bar:
                        progress_bar.update(1)
        
        # Merge avec cache et sauvegarder les dates tentées
        self.cache['articles'].extend(new_articles)
        
        # Ajouter les nouvelles dates fetchées à l'historique
        existing_fetched = set(self.cache.get('fetched_dates', []))
        existing_fetched.update(newly_fetched_dates)
        self.cache['fetched_dates'] = sorted(list(existing_fetched))
        
        # Dédupliquer
        seen_urls = set()
        unique_articles = []
        for article in self.cache['articles']:
            url = article.get('url', '')
            if url and url not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(url)
        
        self.cache['articles'] = unique_articles
        self._save_cache()
        
        # Métriques
        total_articles = len(self.cache['articles'])
        fetched_days = len(dates_to_fetch) if dates_to_fetch else 1
        coverage = len([a for a in new_articles if a]) / max(fetched_days, 1) * 100
        avg_per_day = total_articles / max(days, 1)
        
        return {
            'ticker': self.ticker,
            'success': True,
            'existing': total_articles - len(new_articles),
            'new': len(new_articles),
            'total': total_articles,
            'errors': errors,
            'coverage': coverage,
            'avg_articles_per_day': avg_per_day,
            'confidence_score': min((coverage + avg_per_day * 10) / 2, 100),
            'skipped_dates': skipped_dates,
            'fetched_dates': len(dates_to_fetch)
        }

def process_single_ticker(company, days=160, ticker_progress=None):
    """Traite un ticker avec progress tracking"""
    ticker = company['ticker']
    company_name = company['name']
    search_terms = company.get('search_terms', [ticker])
    
    start_time = time.time()
    
    try:
        # Progress bar pour les jours
        with tqdm(
            total=days,
            desc=f"📰 {ticker}",
            unit="jours",
            leave=False,
            ncols=100,
            bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
        ) as pbar:
            
            engine = HistoricalEngine(ticker, company_name, search_terms)
            result = engine.run_time_machine(days, progress_bar=pbar)
        
        elapsed = time.time() - start_time
        result['duration'] = elapsed
        
        if ticker_progress:
            ticker_progress.update(1)
        
        return result
    
    except Exception as e:
        elapsed = time.time() - start_time
        
        if ticker_progress:
            ticker_progress.update(1)
        
        return {
            'ticker': ticker,
            'success': False,
            'error': str(e),
            'duration': elapsed
        }

def batch_load_parallel(days=160):
    """Charge tous les tickers avec monitoring visuel complet"""
    companies = get_all_companies()
    
    console.print("\n" + "="*80, style="bold cyan")
    console.print("🚀 BATCH LOADER V2.1 - MONITORING VISUEL", style="bold cyan", justify="center")
    console.print("="*80 + "\n", style="bold cyan")
    
    # Panneau de config
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Param", style="cyan")
    config_table.add_column("Value", style="green bold")
    config_table.add_row("📊 Tickers", str(len(companies)))
    config_table.add_row("📅 Historique", f"{days} jours")
    config_table.add_row("⚡ Tickers simultanés", str(MAX_PARALLEL_TICKERS))
    config_table.add_row("🔧 Workers/ticker", str(MAX_WORKERS_PER_TICKER))
    config_table.add_row("⏱️ Durée estimée", f"~{len(companies) * 60 / MAX_PARALLEL_TICKERS / 60:.0f} minutes")
    
    console.print(Panel(config_table, title="Configuration", border_style="cyan"))
    console.print()
    
    start_time = time.time()
    results = []
    
    # Progress bar globale
    with tqdm(
        total=len(companies),
        desc="🎯 Tickers complétés",
        unit="ticker",
        ncols=100,
        colour='green',
        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
    ) as ticker_pbar:
        
        # Parallélisation
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_TICKERS) as executor:
            futures = {executor.submit(process_single_ticker, company, days, ticker_pbar): company for company in companies}
            
            for future in as_completed(futures):
                company = futures[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Mini rapport par ticker
                    if result.get('success'):
                        console.print(
                            f"✅ [green]{result['ticker']}[/green] "
                            f"| 🆕 {result['new']} nouveaux "
                            f"| 📚 {result['total']} total "
                            f"| 📊 {result['confidence_score']:.0f}/100 "
                            f"| ⏱️ {result['duration']:.1f}s"
                        )
                    else:
                        console.print(f"❌ [red]{result['ticker']}[/red] | Erreur: {result.get('error', 'Unknown')}")
                
                except Exception as e:
                    console.print(f"❌ [red]{company['ticker']}[/red] | Exception: {str(e)}")
                    results.append({
                        'ticker': company['ticker'],
                        'success': False,
                        'error': str(e)
                    })
    
    # Rapport final
    elapsed = (time.time() - start_time) / 60
    
    successes = [r for r in results if r.get('success')]
    failures = [r for r in results if not r.get('success')]
    
    total_new = sum(r.get('new', 0) for r in successes)
    total_articles = sum(r.get('total', 0) for r in successes)
    total_skipped = sum(r.get('skipped_dates', 0) for r in successes)
    avg_quality = sum(r.get('confidence_score', 0) for r in successes) / max(len(successes), 1)
    
    # Rate limiting stats
    rl_stats = rate_limiter.get_stats()
    
    console.print("\n" + "="*80, style="bold green")
    console.print("🎉 BATCH LOADER TERMINÉ (MODE DELTA)", style="bold green", justify="center")
    console.print("="*80, style="bold green")
    
    # Tableau de résultats
    results_table = Table(show_header=False, box=None)
    results_table.add_column("Métrique", style="cyan")
    results_table.add_column("Valeur", style="green bold")
    results_table.add_row("✅ Succès", f"{len(successes)}/{len(companies)}")
    results_table.add_row("❌ Échecs", str(len(failures)))
    results_table.add_row("🆕 Nouveaux articles", f"{total_new:,}")
    results_table.add_row("📚 Total articles", f"{total_articles:,}")
    results_table.add_row("⏭️ Jours sautés (delta)", f"{total_skipped:,}")
    results_table.add_row("📊 Qualité moyenne", f"{avg_quality:.1f}/100")
    results_table.add_row("⏱️ Durée totale", f"{elapsed:.1f} minutes")
    results_table.add_row("⚡ Speedup", f"~{len(companies) * 3 / max(elapsed, 0.1):.1f}x vs séquentiel")
    results_table.add_row("🚦 Rate limit waits", f"{rl_stats['google_waits']} ({rl_stats['google_wait_time']:.1f}s)")
    
    console.print(Panel(results_table, title="Résultats Globaux", border_style="green"))
    
    # Tableau détaillé
    console.print("\n📊 DÉTAIL PAR TICKER:\n", style="bold yellow")
    
    detail_table = Table(show_header=True, header_style="bold cyan")
    detail_table.add_column("Ticker", style="cyan")
    detail_table.add_column("Status", justify="center")
    detail_table.add_column("Nouveaux", justify="right")
    detail_table.add_column("Total", justify="right")
    detail_table.add_column("Sautés", justify="right")
    detail_table.add_column("Qualité", justify="right")
    detail_table.add_column("Durée", justify="right")
    
    for r in sorted(results, key=lambda x: x.get('new', 0), reverse=True):
        status = '✅' if r.get('success') else '❌'
        status_style = 'green' if r.get('success') else 'red'
        new = r.get('new', 0)
        total = r.get('total', 0)
        skipped = r.get('skipped_dates', 0)
        quality = f"{r.get('confidence_score', 0):.0f}/100" if r.get('success') else 'N/A'
        duration = f"{r.get('duration', 0):.1f}s" if 'duration' in r else 'N/A'
        
        detail_table.add_row(
            r['ticker'],
            f"[{status_style}]{status}[/{status_style}]",
            f"{new:,}",
            f"{total:,}",
            f"{skipped}",
            quality,
            duration
        )
    
    console.print(detail_table)
    
    if failures:
        console.print("\n❌ ÉCHECS DÉTAILLÉS:\n", style="bold red")
        for r in failures:
            console.print(f"   • {r['ticker']}: {r.get('error', 'Unknown error')}", style="red")

if __name__ == "__main__":
    days = DAYS_TO_SCRAPE
    
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass
    
    # Installation des dépendances
    try:
        import gnews
        import vaderSentiment
    except ImportError:
        console.print("📦 Installation des dépendances...", style="yellow")
        os.system("pip install gnews vaderSentiment -q")
    
    batch_load_parallel(days=days)
