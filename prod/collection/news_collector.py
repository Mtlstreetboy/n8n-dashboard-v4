#!/usr/bin/env python3
"""
📰 NEWS COLLECTOR V1 - Collecte d'articles via Yahoo Finance
--------------------------------------------------------------------
Partie 1 du pipeline: Collecte UNIQUEMENT (pas d'analyse sentiment)
Utilise yfinance (API officielle, fiable) au lieu de GNews (cassé)

Usage:
    python news_collector.py [days]
    python news_collector.py 7      # 7 derniers jours
    python news_collector.py 40     # 40 derniers jours (défaut)
"""
import sys
import os

# Environment Detection
if os.path.exists('/data/scripts'):
    sys.path.insert(0, '/data/scripts')
    DATA_FILES_DIR = '/data/files'
else:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROD_DIR = os.path.dirname(CURRENT_DIR)
    PROJECT_ROOT = os.path.dirname(PROD_DIR)
    sys.path.insert(0, PROD_DIR)
    DATA_FILES_DIR = os.path.join(PROJECT_ROOT, 'local_files')

import json
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from collections import defaultdict

# Yahoo Finance - API officielle fiable
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    print("📦 Installation de yfinance...")
    os.system("pip install yfinance -q")
    import yfinance as yf
    YFINANCE_AVAILABLE = True

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

# Config
from config.companies_config import get_all_companies, get_public_companies

console = Console()

# Configuration
NEWS_DATA_DIR = os.path.join(DATA_FILES_DIR, 'companies')
MAX_PARALLEL_TICKERS = 8
RATE_LIMIT_YAHOO = 0.3  # 300ms entre chaque requête
DAYS_DEFAULT = 40

# Rate limiter global
class RateLimiter:
    def __init__(self):
        self.lock = Lock()
        self.last_request = 0
        self.wait_count = 0
        self.total_wait = 0
    
    def wait(self, delay=RATE_LIMIT_YAHOO):
        with self.lock:
            elapsed = time.time() - self.last_request
            if elapsed < delay:
                wait_time = delay - elapsed
                time.sleep(wait_time)
                self.wait_count += 1
                self.total_wait += wait_time
            self.last_request = time.time()

rate_limiter = RateLimiter()


class NewsCollector:
    """Collecteur de news via Yahoo Finance"""
    
    def __init__(self, ticker: str, company_name: str, search_terms: list = None):
        self.ticker = ticker
        self.company_name = company_name
        self.search_terms = search_terms or [ticker]
        self.cache_file = os.path.join(NEWS_DATA_DIR, f'{ticker}_news.json')
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """Charge le cache existant"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'articles' in data:
                    return data
                elif isinstance(data, list):
                    return {'ticker': self.ticker, 'articles': data, 'fetched_dates': []}
            except Exception as e:
                console.print(f"  ⚠️ Erreur lecture cache {self.ticker}: {e}", style="yellow")
        
        return {'ticker': self.ticker, 'articles': [], 'fetched_dates': []}
    
    def _save_cache(self):
        """Sauvegarde le cache"""
        os.makedirs(NEWS_DATA_DIR, exist_ok=True)
        
        # Backup avant sauvegarde
        if os.path.exists(self.cache_file):
            backup_file = self.cache_file.replace('.json', '_backup.json')
            import shutil
            shutil.copy(self.cache_file, backup_file)
        
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def collect_yahoo_news(self, days_back: int = 40) -> dict:
        """Collecte les news depuis Yahoo Finance (nouvelle structure API 2025+)"""
        rate_limiter.wait()
        
        new_articles = []
        existing_urls = {a.get('url', '') for a in self.cache['articles']}
        
        try:
            ticker_obj = yf.Ticker(self.ticker)
            news = ticker_obj.news or []
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            for article in news:
                try:
                    # Nouvelle structure: données dans 'content'
                    content = article.get('content', article)  # Fallback sur article si pas de content
                    
                    # Extraire la date de publication
                    pub_date_str = content.get('pubDate', '')
                    if pub_date_str:
                        # Format ISO: "2026-01-06T21:02:22Z"
                        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                    else:
                        # Ancien format avec timestamp
                        timestamp = article.get('providerPublishTime', 0)
                        if timestamp:
                            pub_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        else:
                            continue
                    
                    # Filtrer par date
                    if pub_date < cutoff_date:
                        continue
                    
                    # Extraire l'URL (nouvelle structure)
                    url = ''
                    canonical_url = content.get('canonicalUrl', {})
                    if isinstance(canonical_url, dict):
                        url = canonical_url.get('url', '')
                    if not url:
                        click_url = content.get('clickThroughUrl', {})
                        if isinstance(click_url, dict):
                            url = click_url.get('url', '')
                    if not url:
                        url = article.get('link', '')
                    
                    # Vérifier doublon
                    if url in existing_urls:
                        continue
                    
                    # Extraire le publisher
                    provider = content.get('provider', {})
                    publisher = provider.get('displayName', 'Yahoo Finance') if isinstance(provider, dict) else 'Yahoo Finance'
                    
                    # Construire l'article
                    news_item = {
                        'title': content.get('title', '') or article.get('title', ''),
                        'url': url,
                        'published_at': pub_date.isoformat(),
                        'description': content.get('summary', '') or content.get('description', ''),
                        'content': content.get('summary', '') or content.get('description', ''),
                        'source': publisher,
                        'ticker': self.ticker,
                        'company_name': self.company_name,
                        'collected_at': datetime.now(timezone.utc).isoformat(),
                        'collection_source': 'yahoo_finance',
                        # Sentiment sera ajouté par news_analyzer.py
                        'sentiment': None
                    }
                    
                    # Filtres basiques
                    if len(news_item['title']) < 10:
                        continue
                    
                    new_articles.append(news_item)
                    existing_urls.add(url)
                    
                except Exception as e:
                    continue
            
            return {
                'success': True,
                'new_count': len(new_articles),
                'articles': new_articles
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'new_count': 0,
                'articles': []
            }
    
    def collect_rss_history(self, days_back: int = 60, max_per_day: int = 20) -> int:
        """
        Collecte historique via Google News RSS (Smart Backfill)
        - Vérifie jour par jour en remontant le temps
        - Skip si jour déjà marqué comme 'fetched'
        - Skip si on a déjà >= max_per_day articles pour ce jour
        """
        import requests
        import xml.etree.ElementTree as ET
        
        total_added = 0
        fetched_dates = set(self.cache.get('fetched_dates', []))
        
        # Indexer les articles existants par date (YYYY-MM-DD)
        articles_by_date = defaultdict(list)
        for art in self.cache.get('articles', []):
            d = art.get('published_at', '')[:10]
            if d: articles_by_date[d].append(art)
            
        console.print(f"  📚 [dim]Backfill Historique ({days_back} jours) pour {self.ticker}...[/dim]")
        
        # Iterer du plus récent au plus ancien
        for i in range(days_back):
            date_obj = datetime.now() - timedelta(days=i)
            date_str = date_obj.strftime('%Y-%m-%d')
            
            # 1. Check si déjà traité via le flag explicite
            if date_str in fetched_dates:
                continue
                
            # 2. Check quota existant
            existing_count = len(articles_by_date.get(date_str, []))
            if existing_count >= max_per_day:
                fetched_dates.add(date_str)
                continue
                
            # 3. Fetch RSS pour ce jour spécifique
            try:
                # Construire la requête: (Term1 OR Term2) after:...
                terms_str = " OR ".join(f'"{t}"' for t in self.search_terms[:2]) # Limiter à 2 termes principaux pour pas casser l'URL
                
                # Google RSS: after:YYYY-MM-DD before:YYYY-MM-DD (next day)
                next_date = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
                query = f'({terms_str}) after:{date_str} before:{next_date}'
                url = f'https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en'
                
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    items = root.findall('.//item')
                    
                    day_added = 0
                    for item in items:
                        if day_added + existing_count >= max_per_day:
                            break
                            
                        link = item.find('link').text
                        # Simple dedupe by URL
                        if any(a['url'] == link for a in self.cache['articles']):
                            continue
                            
                        # Parse date
                        pub_str = item.find('pubDate').text
                        try:
                            pub_dt = datetime.strptime(pub_str, '%a, %d %b %Y %H:%M:%S %Z')
                            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                        except:
                            pub_dt = datetime.now(timezone.utc)
                            
                        article = {
                            'title': item.find('title').text,
                            'url': link,
                            'published_at': pub_dt.isoformat(),
                            'description': item.find('description').text if item.find('description') is not None else '',
                            'content': '',
                            'source': item.find('source').text if item.find('source') is not None else 'Google RSS',
                            'ticker': self.ticker,
                            'company_name': self.company_name,
                            'collected_at': datetime.now(timezone.utc).isoformat(),
                            'collection_source': 'google_rss_backfill',
                            'sentiment': None
                        }
                        
                        self.cache['articles'].append(article)
                        articles_by_date[date_str].append(article)
                        day_added += 1
                        total_added += 1
                        
                    # Marquer le jour comme traité
                    fetched_dates.add(date_str)
                    
                    # Petit sleep pour pas spammer Google (100ms)
                    time.sleep(0.1)
                    
            except Exception:
                pass # Fail dim
        
        # Mettre à jour et sauvegarder
        self.cache['fetched_dates'] = list(fetched_dates)
        self._save_cache()
        return total_added

    def run(self, days_back: int = 40) -> dict:
        """Exécute la collecte (Yahoo Live + RSS Backfill)"""
        start_time = time.time()
        
        # 1. Yahoo Live (Delta récent et rapide)
        # On limite Yahoo à 7 jours car c'est pour l'actu chaude
        live_res = self.collect_yahoo_news(days_back=7)
        
        # 2. RSS Backfill (Historique profond et intelligent)
        # On va chercher jusqu'à 'days_back' jours
        backfill_count = self.collect_rss_history(days_back=days_back, max_per_day=20)
        
        total_new = live_res['new_count'] + backfill_count
        
        elapsed = time.time() - start_time
        
        return {
            'ticker': self.ticker,
            'success': live_res['success'],
            'new_articles': total_new,
            'total_articles': len(self.cache['articles']),
            'error': live_res.get('error'),
            'duration': elapsed
        }


def collect_single_ticker(company: dict, days: int) -> dict:
    """Collecte pour un ticker"""
    ticker = company['ticker']
    name = company['name']
    search_terms = company.get('search_terms', [])
    
    collector = NewsCollector(ticker, name, search_terms)
    return collector.run(days)


def collect_all(days: int = DAYS_DEFAULT, only_public: bool = True):
    """Collecte pour tous les tickers"""
    
    companies = get_public_companies() if only_public else get_all_companies()
    
    console.print("\n" + "="*70, style="bold cyan")
    console.print("📰 NEWS COLLECTOR V2 - Yahoo + RSS Backfill", style="bold cyan", justify="center")
    console.print("="*70 + "\n", style="bold cyan")
    
    # Info config
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Param", style="cyan")
    config_table.add_column("Value", style="green bold")
    config_table.add_row("📊 Tickers", str(len(companies)))
    config_table.add_row("📅 Période", f"{days} jours")
    config_table.add_row("📁 Output", NEWS_DATA_DIR)
    console.print(Panel(config_table, title="Configuration", border_style="cyan"))
    console.print()
    
    start_time = time.time()
    results = []
    
    # Progress bar
    with tqdm(total=len(companies), desc="🎯 Collecte", unit="ticker", ncols=100, colour='green') as pbar:
        
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_TICKERS) as executor:
            futures = {
                executor.submit(collect_single_ticker, company, days): company 
                for company in companies
            }
            
            for future in as_completed(futures):
                company = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Affichage inline
                    if result['new_articles'] > 0:
                        console.print(f"  ✅ {result['ticker']:8} | 🆕 {result['new_articles']:3} nouveaux | 📚 {result['total_articles']:4} total")
                    else:
                        console.print(f"  ⏭️  {result['ticker']:8} | Pas de nouveaux articles", style="dim")
                
                except Exception as e:
                    results.append({
                        'ticker': company['ticker'],
                        'success': False, # This 'success' key is not returned by the new run method, but kept for compatibility with the reporting logic below.
                        'error': str(e),
                        'new_articles': 0,
                        'total_articles': 0
                    })
                    console.print(f"  ❌ {company['ticker']:8} | Erreur: {e}", style="red")
                
                pbar.update(1)
    
    # Rapport final
    elapsed = time.time() - start_time
    
    successes = [r for r in results if not r.get('error')]
    failures = [r for r in results if r.get('error')]
    total_new = sum(r.get('new_articles', 0) for r in successes)
    total_articles = sum(r.get('total_articles', 0) for r in successes)
    
    console.print("\n" + "="*70, style="bold green")
    console.print("🎉 COLLECTE TERMINÉE", style="bold green", justify="center")
    console.print("="*70, style="bold green")
    
    results_table = Table(show_header=False, box=None)
    results_table.add_column("Métrique", style="cyan")
    results_table.add_column("Valeur", style="green bold")
    results_table.add_row("✅ Succès", f"{len(successes)}/{len(companies)}")
    results_table.add_row("🆕 Nouveaux articles", f"{total_new:,}")
    results_table.add_row("📚 Total articles", f"{total_articles:,}")
    results_table.add_row("⏱️ Durée", f"{elapsed:.1f}s")
    results_table.add_row("🚦 Rate limit waits", f"{rate_limiter.wait_count}")
    
    console.print(Panel(results_table, title="Résultats", border_style="green"))
    
    if failures:
        console.print("\n❌ Échecs:", style="bold red")
        for r in failures:
            console.print(f"   • {r['ticker']}: {r.get('error', 'Unknown')}", style="red")
    
    # Retourner stats pour pipeline
    return {
        'success': len(failures) == 0,
        'total_new': total_new,
        'total_articles': total_articles,
        'successes': len(successes),
        'failures': len(failures),
        'duration': elapsed
    }


def main():
    """Point d'entrée principal"""
    days = DAYS_DEFAULT
    
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass
    
    stats = collect_all(days=days)
    
    console.print("\n✅ Collecte terminée! Lancez maintenant:", style="bold green")
    console.print("   python news_analyzer.py", style="yellow")
    
    return 0 if stats['success'] else 1


if __name__ == "__main__":
    sys.exit(main())
