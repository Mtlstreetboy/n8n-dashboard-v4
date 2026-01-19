#!/usr/bin/env python3
"""
WSB Market Sentiment Collector - Version Pushshift (SANS AUTHENTIFICATION)
Utilise l'API Pushshift pour contourner les limitations Reddit

Usage:
    python wsb_sentiment_collector.py [--hours 24] [--limit 100] [--output /data/wsb_data]
"""

import re
import json
import time
import os
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration centralisée"""
    
    # Chemins (compatible container et local)
    DATA_DIR = os.environ.get('WSB_DATA_DIR', './wsb_data')
    CACHE_FILE = os.path.join(DATA_DIR, 'ticker_cache.json')
    HISTORY_FILE = os.path.join(DATA_DIR, 'wsb_history.json')
    
    # APIs (SANS AUTHENTIFICATION)
    PUSHSHIFT_BASE = "https://api.pullpush.io/reddit/search/submission"
    REDDIT_RSS = "https://www.reddit.com/r/wallstreetbets/.rss"
    
    # User Agent
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    REQUEST_DELAY = 1.0
    
    # Analyse
    MAX_POSTS = 100
    MIN_MENTIONS = 1  # Réduit pour RSS avec moins de posts
    TICKER_MIN_LEN = 2
    TICKER_MAX_LEN = 5
    CACHE_HOURS = 24  # Durée cache validation tickers
    
    # Sentiment keywords (WSB specific)
    BULLISH_WORDS = {
        'moon', 'mooning', 'calls', 'bullish', 'buy', 'long', 'rocket',
        'tendies', 'gain', 'gains', 'profit', 'profits', 'printing',
        'diamond', 'hands', 'hold', 'holding', 'rally', 'breakout',
        'squeeze', 'gamma', 'yolo', 'lfg', 'send', 'sending', 'rip',
        'green', 'pump', 'pumping', 'undervalued', 'cheap', 'dip', 'btfd'
    }
    
    BEARISH_WORDS = {
        'dump', 'dumping', 'puts', 'bearish', 'sell', 'selling', 'short',
        'crash', 'crashing', 'loss', 'losses', 'bag', 'bagholder', 'bagholding',
        'rekt', 'wrecked', 'rug', 'rugged', 'tank', 'tanking', 'bleeding',
        'dead', 'plunge', 'plunging', 'red', 'drill', 'drilling', 'fade',
        'overvalued', 'expensive', 'trap', 'scam'
    }
    
    # Blacklist étendue (mots courants qui ressemblent à des tickers)
    BLACKLIST = {
        # Acronymes WSB
        'DD', 'YOLO', 'FOMO', 'ATH', 'ATL', 'MOASS', 'FUD', 'HODL', 'BTFD',
        'DRS', 'NFT', 'CEO', 'CFO', 'CTO', 'COO', 'IPO', 'SEC', 'FED', 'GDP',
        # Options
        'OTM', 'ITM', 'ATM', 'DTE', 'IV', 'OI', 'PM', 'AH',
        # Reddit/Internet
        'OP', 'OC', 'TL', 'DR', 'PSA', 'AMA', 'TIL', 'TLDR', 'IMO', 'IMHO',
        'IRL', 'LOL', 'LMAO', 'ROFL', 'WTF', 'OMG', 'FYI', 'ASAP', 'FAQ',
        # ETFs courants (à exclure car trop génériques)
        'SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI', 'TQQQ', 'SQQQ', 'UVXY',
        # Mots anglais courts
        'A', 'I', 'AM', 'PM', 'TV', 'AI', 'IT', 'OR', 'AN', 'AS', 'AT',
        'BE', 'BY', 'DO', 'GO', 'IF', 'IN', 'IS', 'ME', 'MY', 'NO', 'OF',
        'ON', 'SO', 'TO', 'UP', 'US', 'WE', 'ALL', 'AND', 'ARE', 'BUT',
        'FOR', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOT',
        'NOW', 'OLD', 'ONE', 'OUR', 'OUT', 'OWN', 'SAY', 'THE', 'TOO',
        'TWO', 'WAY', 'WHO', 'WHY', 'YET', 'YOU', 'BUY', 'SELL', 'HOLD',
        # Géographie
        'USA', 'NYC', 'LA', 'UK', 'EU', 'NY', 'CA', 'TX', 'FL',
        # Autres
        'PR', 'HR', 'EV', 'PE', 'EPS', 'ROI', 'YOY', 'MOM', 'QOQ',
        'APE', 'APES', 'BEAR', 'BULL', 'PUTS', 'CALLS', 'CALL', 'PUT'
    }
    
    # Tickers populaires connus (pour boost de confiance)
    KNOWN_TICKERS = {
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA',
        'AMD', 'INTC', 'NFLX', 'DIS', 'PYPL', 'SQ', 'COIN', 'HOOD',
        'GME', 'AMC', 'BB', 'BBBY', 'PLTR', 'SOFI', 'RIVN', 'LCID',
        'NIO', 'BABA', 'JD', 'PDD', 'WISH', 'CLOV', 'SPCE', 'DKNG',
        'ROKU', 'SNAP', 'UBER', 'LYFT', 'ABNB', 'RBLX', 'U', 'CRWD',
        'ZM', 'DOCU', 'OKTA', 'NET', 'SNOW', 'MDB', 'DDOG', 'PATH'
    }


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RedditPost:
    """Post Reddit avec métadonnées"""
    id: str
    title: str
    content: str
    score: int
    created_utc: float
    url: str
    author: str = "unknown"
    flair: str = ""
    source: str = "pushshift"  # pushshift, rss, or reddit
    
    @property
    def full_text(self) -> str:
        return f"{self.title} {self.content}"
    
    @property
    def created_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.created_utc)
    
    @property
    def age_hours(self) -> float:
        return (datetime.now() - self.created_datetime).total_seconds() / 3600


@dataclass
class TickerAnalysis:
    """Analyse complète d'un ticker"""
    ticker: str
    mentions: int
    unique_posts: int
    total_score: int
    avg_post_score: float
    sentiment_score: float
    sentiment_label: str
    confidence: float
    is_validated: bool
    sample_contexts: List[str] = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# PUSHSHIFT SCRAPER (PRINCIPALE - SANS AUTH)
# ============================================================================

class PushshiftScraper:
    """Scraper utilisant Pushshift (archive Reddit publique, SANS AUTH)"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': Config.USER_AGENT})
    
    def fetch_posts(self, hours_back: int = 24, limit: int = 100) -> List[RedditPost]:
        """
        Récupère les posts via Pushshift
        hours_back: nombre d'heures dans le passé
        """
        logger.info(f"📡 Fetching posts from Pushshift (last {hours_back}h)...")
        
        after = int((datetime.now() - timedelta(hours=hours_back)).timestamp())
        
        params = {
            'subreddit': 'wallstreetbets',
            'size': min(limit, 100),
            'after': after,
            'sort': 'desc',
            'sort_type': 'created_utc'
        }
        
        posts = []
        
        try:
            response = self.session.get(
                Config.PUSHSHIFT_BASE,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                raw_posts = data.get('data', [])
                
                for post in raw_posts:
                    posts.append(RedditPost(
                        id=post.get('id', ''),
                        title=post.get('title', ''),
                        content=post.get('selftext', '') or '',
                        score=post.get('score', 0),
                        created_utc=post.get('created_utc', time.time()),
                        url=f"https://reddit.com{post.get('permalink', '')}",
                        author=post.get('author', 'unknown'),
                        flair=post.get('link_flair_text', '') or '',
                        source='pushshift'
                    ))
                
                logger.info(f"✅ Pushshift: Retrieved {len(posts)} posts")
            else:
                logger.warning(f"⚠️ Pushshift returned {response.status_code}")
        
        except requests.exceptions.Timeout:
            logger.warning("⚠️ Pushshift timeout")
        except Exception as e:
            logger.error(f"❌ Pushshift error: {e}")
        
        return posts


# ============================================================================
# RSS FALLBACK (TOUJOURS DISPONIBLE)
# ============================================================================

class RSSFallback:
    """Fallback via RSS (toujours disponible, ~25 posts max)"""
    
    def fetch_posts(self, limit: int = 25) -> List[RedditPost]:
        """Récupère via RSS Reddit (max ~25 posts)"""
        logger.info("📡 Fetching via RSS fallback...")
        
        try:
            response = requests.get(
                Config.REDDIT_RSS,
                headers={'User-Agent': Config.USER_AGENT},
                timeout=15
            )
            
            if response.status_code != 200:
                logger.warning(f"⚠️ RSS returned {response.status_code}")
                return []
            
            root = ET.fromstring(response.content)
            posts = []
            
            # Parse Atom feed
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('.//atom:entry', ns)[:limit]:
                title_elem = entry.find('atom:title', ns)
                content_elem = entry.find('atom:content', ns)
                link_elem = entry.find('atom:link', ns)
                id_elem = entry.find('atom:id', ns)
                author_elem = entry.find('.//atom:name', ns)
                updated_elem = entry.find('atom:updated', ns)
                
                # Parse timestamp
                created_utc = time.time()
                if updated_elem is not None and updated_elem.text:
                    try:
                        dt = datetime.fromisoformat(updated_elem.text.replace('Z', '+00:00'))
                        created_utc = dt.timestamp()
                    except:
                        pass
                
                posts.append(RedditPost(
                    id=id_elem.text.split('/')[-1] if id_elem is not None else '',
                    title=title_elem.text if title_elem is not None else '',
                    content=content_elem.text if content_elem is not None else '',
                    score=0,  # RSS ne donne pas le score
                    created_utc=created_utc,
                    url=link_elem.get('href') if link_elem is not None else '',
                    author=author_elem.text if author_elem is not None else 'unknown',
                    source='rss'
                ))
            
            logger.info(f"✅ RSS: Retrieved {len(posts)} posts")
            return posts
            
        except ET.ParseError as e:
            logger.error(f"❌ RSS parse error: {e}")
        except Exception as e:
            logger.error(f"❌ RSS error: {e}")
        
        return []


# ============================================================================
# MULTI-SOURCE SCRAPER
# ============================================================================

class MultiSourceScraper:
    """Combine plusieurs sources pour maximiser la couverture"""
    
    def __init__(self):
        self.pushshift = PushshiftScraper()
        self.rss = RSSFallback()
    
    def fetch_posts(self, hours_back: int = 24, limit: int = 100) -> List[RedditPost]:
        """Récupère depuis toutes les sources disponibles"""
        all_posts = {}
        
        # 1. Essayer Pushshift d'abord (meilleure source)
        pushshift_posts = self.pushshift.fetch_posts(hours_back=hours_back, limit=limit)
        for post in pushshift_posts:
            if post.id:
                all_posts[post.id] = post
        
        # 2. Compléter avec RSS si pas assez de posts
        if len(all_posts) < 20:
            logger.info("📡 Complementing with RSS...")
            rss_posts = self.rss.fetch_posts(limit=25)
            for post in rss_posts:
                if post.id and post.id not in all_posts:
                    all_posts[post.id] = post
        
        posts = list(all_posts.values())
        logger.info(f"📊 Total unique posts from all sources: {len(posts)}")
        
        return posts


# ============================================================================
# TICKER VALIDATOR
# ============================================================================

class TickerValidator:
    """Valide les tickers via Yahoo Finance avec cache persistant"""
    
    def __init__(self):
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Charge le cache depuis le disque"""
        try:
            if os.path.exists(Config.CACHE_FILE):
                with open(Config.CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")
        return {}
    
    def _save_cache(self):
        """Sauvegarde le cache sur disque"""
        try:
            os.makedirs(os.path.dirname(Config.CACHE_FILE), exist_ok=True)
            with open(Config.CACHE_FILE, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save cache: {e}")
    
    def _is_cache_valid(self, ticker: str) -> bool:
        """Vérifie si l'entrée cache est encore valide"""
        if ticker not in self.cache:
            return False
        
        cached_time = self.cache[ticker].get('timestamp', 0)
        cache_age_hours = (time.time() - cached_time) / 3600
        return cache_age_hours < Config.CACHE_HOURS
    
    def validate(self, ticker: str) -> bool:
        """Valide un ticker via Yahoo Finance"""
        # Tickers connus = validés automatiquement
        if ticker in Config.KNOWN_TICKERS:
            return True
        
        # Vérifier le cache
        if self._is_cache_valid(ticker):
            return self.cache[ticker].get('valid', False)
        
        # Validation via Yahoo Finance
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search"
            params = {'q': ticker, 'quotesCount': 5, 'newsCount': 0}
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            is_valid = False
            if 'quotes' in data:
                for quote in data['quotes']:
                    if quote.get('symbol', '').upper() == ticker.upper():
                        # Vérifier que c'est bien une action (pas crypto, etc.)
                        quote_type = quote.get('quoteType', '')
                        if quote_type in ('EQUITY', 'ETF'):
                            is_valid = True
                            break
            
            # Mettre en cache
            self.cache[ticker] = {
                'valid': is_valid,
                'timestamp': time.time()
            }
            self._save_cache()
            
            time.sleep(0.2)  # Rate limit Yahoo
            return is_valid
            
        except Exception as e:
            logger.debug(f"Validation error for {ticker}: {e}")
            return False
    
    def batch_validate(self, tickers: List[str], max_validations: int = 30) -> Dict[str, bool]:
        """Valide plusieurs tickers (limité pour éviter rate limiting)"""
        results = {}
        validated_count = 0
        
        for ticker in tickers:
            if ticker in Config.KNOWN_TICKERS:
                results[ticker] = True
            elif self._is_cache_valid(ticker):
                results[ticker] = self.cache[ticker].get('valid', False)
            elif validated_count < max_validations:
                results[ticker] = self.validate(ticker)
                validated_count += 1
            else:
                results[ticker] = False  # Non validé par manque de quota
        
        return results


# ============================================================================
# TICKER EXTRACTOR & SENTIMENT ANALYZER
# ============================================================================

class TickerExtractor:
    """Extrait et analyse les tickers depuis le texte"""
    
    # Patterns regex pour détecter les tickers
    PATTERNS = [
        r'\$([A-Z]{2,5})\b',                          # $NVDA
        r'\b([A-Z]{2,5})\s*🚀',                        # TSLA 🚀
        r'\b([A-Z]{2,5})\s+(?:stock|shares?|calls?|puts?|options?|position)',
        r'(?:bought|sold|buying|selling|holding|hold)\s+([A-Z]{2,5})\b',
        r'(?:long|short)\s+(?:on\s+)?([A-Z]{2,5})\b',
        r'\b([A-Z]{2,5})\s+(?:to the moon|moon|mooning|printing)',
        r'(?:earnings|ER)\s+(?:for\s+)?([A-Z]{2,5})\b',
    ]
    
    def extract_tickers(self, text: str) -> Set[str]:
        """Extrait les tickers potentiels d'un texte"""
        tickers = set()
        
        for pattern in self.PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                ticker = match.upper()
                if self._is_valid_format(ticker):
                    tickers.add(ticker)
        
        return tickers
    
    def _is_valid_format(self, ticker: str) -> bool:
        """Vérifie le format basique d'un ticker"""
        if ticker in Config.BLACKLIST:
            return False
        if not Config.TICKER_MIN_LEN <= len(ticker) <= Config.TICKER_MAX_LEN:
            return False
        if not ticker.isalpha():
            return False
        return True
    
    def calculate_sentiment(self, text: str, ticker: str) -> float:
        """
        Calcule un score de sentiment pour un ticker dans son contexte
        Retourne un score entre -1 (très bearish) et +1 (très bullish)
        """
        text_lower = text.lower()
        
        # Trouver toutes les positions du ticker
        ticker_positions = [
            m.start() for m in re.finditer(
                rf'\b{ticker}\b|\${ticker}\b', 
                text, 
                re.IGNORECASE
            )
        ]
        
        if not ticker_positions:
            return 0.0
        
        total_sentiment = 0
        contexts_analyzed = 0
        
        for pos in ticker_positions:
            # Extraire le contexte (100 chars avant/après)
            start = max(0, pos - 100)
            end = min(len(text_lower), pos + 100)
            context = text_lower[start:end]
            
            # Compter les mots bullish/bearish
            bullish = sum(1 for word in Config.BULLISH_WORDS if word in context)
            bearish = sum(1 for word in Config.BEARISH_WORDS if word in context)
            
            # Pondérer par la proximité (mots plus proches = plus importants)
            total_sentiment += (bullish - bearish)
            contexts_analyzed += 1
        
        if contexts_analyzed == 0:
            return 0.0
        
        # Normaliser entre -1 et +1
        raw_score = total_sentiment / contexts_analyzed
        normalized = max(-1, min(1, raw_score / 3))  # /3 pour modérer les extrêmes
        
        return round(normalized, 2)
    
    def get_sentiment_label(self, score: float) -> str:
        """Convertit un score en label"""
        if score > 0.3:
            return "🚀 Bullish"
        elif score > 0.1:
            return "📈 Slightly Bullish"
        elif score < -0.3:
            return "📉 Bearish"
        elif score < -0.1:
            return "⚠️ Slightly Bearish"
        else:
            return "➖ Neutral"
    
    def extract_context_snippet(self, text: str, ticker: str, max_length: int = 100) -> str:
        """Extrait un snippet de contexte pour un ticker"""
        match = re.search(
            rf'.{{0,50}}(?:\$?{ticker}).{{0,50}}',
            text,
            re.IGNORECASE
        )
        if match:
            snippet = match.group(0).strip()
            return snippet[:max_length] + "..." if len(snippet) > max_length else snippet
        return ""


# ============================================================================
# MAIN ANALYZER
# ============================================================================

class WSBAnalyzer:
    """Analyseur principal WSB - Version Pushshift (SANS AUTH)"""
    
    def __init__(self):
        self.scraper = MultiSourceScraper()
        self.validator = TickerValidator()
        self.extractor = TickerExtractor()
    
    def analyze(self, hours_back: int = 24, limit: int = Config.MAX_POSTS) -> List[TickerAnalysis]:
        """Lance l'analyse complète"""
        logger.info("🚀 Starting WSB Analysis (No Auth Required)...")
        
        # 1. Récupérer les posts via Pushshift/RSS
        posts = self.scraper.fetch_posts(hours_back=hours_back, limit=limit)
        
        if not posts:
            logger.error("❌ No posts retrieved from any source")
            return []
        
        # 2. Extraire et agréger les données par ticker
        ticker_data = defaultdict(lambda: {
            'mentions': 0,
            'posts': set(),
            'scores': [],
            'sentiments': [],
            'contexts': [],
            'timestamps': []
        })
        
        logger.info(f"🔍 Analyzing {len(posts)} posts for tickers...")
        
        for post in posts:
            tickers = self.extractor.extract_tickers(post.full_text)
            
            for ticker in tickers:
                data = ticker_data[ticker]
                data['mentions'] += 1
                data['posts'].add(post.id)
                data['scores'].append(post.score)
                data['sentiments'].append(
                    self.extractor.calculate_sentiment(post.full_text, ticker)
                )
                data['timestamps'].append(post.created_utc)
                
                # Garder quelques contextes d'exemple
                if len(data['contexts']) < 3:
                    ctx = self.extractor.extract_context_snippet(post.full_text, ticker)
                    if ctx:
                        data['contexts'].append(ctx)
        
        # 3. Filtrer par nombre minimum de mentions
        filtered_tickers = {
            t: d for t, d in ticker_data.items() 
            if d['mentions'] >= Config.MIN_MENTIONS
        }
        
        logger.info(f"📊 Found {len(filtered_tickers)} tickers with {Config.MIN_MENTIONS}+ mentions")
        
        # 4. Valider les top tickers
        sorted_tickers = sorted(
            filtered_tickers.keys(),
            key=lambda t: filtered_tickers[t]['mentions'],
            reverse=True
        )
        
        validation_results = self.validator.batch_validate(sorted_tickers[:50])
        
        # 5. Créer les objets d'analyse
        analyses = []
        
        for ticker in sorted_tickers:
            data = filtered_tickers[ticker]
            
            avg_sentiment = sum(data['sentiments']) / len(data['sentiments'])
            is_validated = validation_results.get(ticker, False)
            
            # Calculer la confiance
            confidence = self._calculate_confidence(
                mentions=data['mentions'],
                unique_posts=len(data['posts']),
                is_validated=is_validated
            )
            
            analyses.append(TickerAnalysis(
                ticker=ticker,
                mentions=data['mentions'],
                unique_posts=len(data['posts']),
                total_score=sum(data['scores']),
                avg_post_score=sum(data['scores']) / len(data['scores']),
                sentiment_score=round(avg_sentiment, 2),
                sentiment_label=self.extractor.get_sentiment_label(avg_sentiment),
                confidence=confidence,
                is_validated=is_validated,
                sample_contexts=data['contexts'][:3],
                first_seen=datetime.fromtimestamp(min(data['timestamps'])).isoformat(),
                last_seen=datetime.fromtimestamp(max(data['timestamps'])).isoformat()
            ))
        
        # Trier par mentions puis par confiance
        analyses.sort(key=lambda x: (x.confidence, x.mentions), reverse=True)
        
        return analyses
    
    def _calculate_confidence(self, mentions: int, unique_posts: int, is_validated: bool) -> float:
        """Calcule un score de confiance 0-1"""
        # Base: validation
        base = 0.5 if is_validated else 0.2
        
        # Bonus mentions (jusqu'à +0.3)
        mention_bonus = min(0.3, mentions / 50)
        
        # Bonus diversité posts (jusqu'à +0.2)
        diversity_bonus = min(0.2, unique_posts / 20)
        
        return round(min(1.0, base + mention_bonus + diversity_bonus), 2)
    
    def print_report(self, analyses: List[TickerAnalysis], top_n: int = 25):
        """Affiche un rapport formaté"""
        print("\n" + "=" * 100)
        print(f"📊 WSB SENTIMENT ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 100)
        
        if not analyses:
            print("No tickers detected.")
            return
        
        # Header
        print(f"\n{'#':<4} {'Ticker':<8} {'Mentions':<10} {'Posts':<7} "
              f"{'Sentiment':<18} {'Confidence':<12} {'Validated':<10}")
        print("-" * 100)
        
        for i, analysis in enumerate(analyses[:top_n], 1):
            valid_icon = "✅" if analysis.is_validated else "❓"
            conf_bar = "█" * int(analysis.confidence * 10) + "░" * (10 - int(analysis.confidence * 10))
            
            print(f"{i:<4} {analysis.ticker:<8} {analysis.mentions:<10} {analysis.unique_posts:<7} "
                  f"{analysis.sentiment_label:<18} [{conf_bar}] {analysis.confidence:<5} {valid_icon}")
        
        print("=" * 100)
        
        # Résumé
        validated_count = sum(1 for a in analyses if a.is_validated)
        bullish_count = sum(1 for a in analyses if a.sentiment_score > 0.1)
        bearish_count = sum(1 for a in analyses if a.sentiment_score < -0.1)
        
        print(f"\n📈 Summary: {len(analyses)} tickers detected | "
              f"{validated_count} validated | "
              f"{bullish_count} bullish | {bearish_count} bearish")
        
        print("\n💡 Legend: ✅ = Validated ticker | ❓ = Unverified | Confidence bar shows reliability")
        print("🔄 Data source: Pushshift Archive (public, no auth required)")
    
    def export_json(self, analyses: List[TickerAnalysis], filename: Optional[str] = None):
        """Exporte les résultats en JSON"""
        if filename is None:
            os.makedirs(Config.DATA_DIR, exist_ok=True)
            filename = os.path.join(
                Config.DATA_DIR, 
                f"wsb_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            )
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_tickers': len(analyses),
            'tickers': [a.to_dict() for a in analyses]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results exported to {filename}")
        return filename
    
    def export_for_dashboard(self, analyses: List[TickerAnalysis]) -> str:
        """Exporte dans un format compatible avec les dashboards existants"""
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        filename = os.path.join(Config.DATA_DIR, "wsb_latest.json")
        
        # Format simplifié pour dashboard
        dashboard_data = {
            'last_updated': datetime.now().isoformat(),
            'source': 'r/wallstreetbets',
            'tickers': [
                {
                    'symbol': a.ticker,
                    'mentions': a.mentions,
                    'sentiment': a.sentiment_score,
                    'sentiment_label': a.sentiment_label,
                    'confidence': a.confidence,
                    'validated': a.is_validated
                }
                for a in analyses if a.is_validated  # Only validated tickers
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2)
        
        logger.info(f"📊 Dashboard data exported to {filename}")
        return filename


# ============================================================================
# CLI
# ============================================================================

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WSB Sentiment Analyzer (No Auth Required)')
    parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')
    parser.add_argument('--limit', type=int, default=100, help='Number of posts to analyze')
    parser.add_argument('--output', type=str, help='Output directory')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    if args.output:
        Config.DATA_DIR = args.output
    
    analyzer = WSBAnalyzer()
    analyses = analyzer.analyze(hours_back=args.hours, limit=args.limit)
    
    if not args.quiet:
        analyzer.print_report(analyses)
    
    analyzer.export_json(analyses)
    analyzer.export_for_dashboard(analyses)
    
    return analyses


if __name__ == "__main__":
    main()
