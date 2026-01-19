#!/usr/bin/env python3
"""
📥 WSB Raw Post Collector - Étape 1/2
=====================================
Collecte TOUS les posts r/wallstreetbets des dernières 24h
Sauvegarde en JSON brut pour analyse ultérieure avec FinBERT

Usage:
    python wsb_raw_collector.py --hours 24
    python wsb_raw_collector.py --hours 48 --output ./data/wsb_posts.json
"""

import json
import time
import os
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import requests
import re

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration"""
    DATA_DIR = os.environ.get('WSB_DATA_DIR', './wsb_data')
    RAW_FILE = os.path.join(DATA_DIR, 'wsb_raw_posts.json')
    
    # APIs
    PUSHSHIFT_BASE = "https://api.pullpush.io/reddit/search/submission"
    REDDIT_RSS = "https://www.reddit.com/r/wallstreetbets/.rss"
    
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


# ============================================================================
# DATA CLASS
# ============================================================================

@dataclass
class RawPost:
    """Post Reddit brut"""
    id: str
    title: str
    content: str
    author: str
    score: int
    num_comments: int
    created_utc: float
    url: str
    flair: str
    source: str  # pushshift, rss
    
    @property
    def created_datetime(self) -> str:
        return datetime.fromtimestamp(self.created_utc).isoformat()
    
    @property
    def full_text(self) -> str:
        """Texte complet pour analyse"""
        return f"{self.title}. {self.content}" if self.content else self.title
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['created_datetime'] = self.created_datetime
        d['full_text'] = self.full_text
        return d


# ============================================================================
# PUSHSHIFT SCRAPER
# ============================================================================

class PushshiftScraper:
    """Collecte via Pushshift (archive Reddit publique)"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': Config.USER_AGENT})
    
    def fetch_posts(self, hours_back: int = 24, limit: int = 500) -> List[RawPost]:
        """Récupère les posts via Pushshift"""
        logger.info(f"📡 Pushshift: Fetching posts from last {hours_back}h...")
        
        after = int((datetime.now() - timedelta(hours=hours_back)).timestamp())
        posts = []
        
        # Pushshift peut paginer, on fait plusieurs requêtes si nécessaire
        page_size = min(100, limit)
        last_utc = None
        
        while len(posts) < limit:
            params = {
                'subreddit': 'wallstreetbets',
                'size': page_size,
                'after': after,
                'sort': 'desc',
                'sort_type': 'created_utc'
            }
            
            if last_utc:
                params['before'] = last_utc
            
            try:
                response = self.session.get(
                    Config.PUSHSHIFT_BASE,
                    params=params,
                    timeout=30
                )
                
                if response.status_code != 200:
                    logger.warning(f"⚠️ Pushshift returned {response.status_code}")
                    break
                
                data = response.json()
                raw_posts = data.get('data', [])
                
                if not raw_posts:
                    break
                
                for post in raw_posts:
                    posts.append(RawPost(
                        id=post.get('id', ''),
                        title=post.get('title', ''),
                        content=post.get('selftext', '') or '',
                        author=post.get('author', 'unknown'),
                        score=post.get('score', 0),
                        num_comments=post.get('num_comments', 0),
                        created_utc=post.get('created_utc', time.time()),
                        url=f"https://reddit.com{post.get('permalink', '')}",
                        flair=post.get('link_flair_text', '') or '',
                        source='pushshift'
                    ))
                
                last_utc = raw_posts[-1].get('created_utc')
                logger.info(f"   Retrieved {len(posts)} posts so far...")
                
                time.sleep(1)  # Rate limit
                
            except Exception as e:
                logger.error(f"❌ Pushshift error: {e}")
                break
        
        logger.info(f"✅ Pushshift: Retrieved {len(posts)} total posts")
        return posts[:limit]


# ============================================================================
# RSS FALLBACK
# ============================================================================

class RSSFallback:
    """Fallback via RSS (~25 posts)"""
    
    def fetch_posts(self) -> List[RawPost]:
        """Récupère via RSS Reddit"""
        logger.info("📡 RSS: Fetching fallback posts...")
        
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
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('.//atom:entry', ns):
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
                
                # Clean HTML from content
                content = content_elem.text if content_elem is not None else ''
                if content:
                    content = re.sub(r'<[^>]+>', ' ', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                
                posts.append(RawPost(
                    id=id_elem.text.split('/')[-1] if id_elem is not None else '',
                    title=title_elem.text if title_elem is not None else '',
                    content=content[:2000],  # Limit content length
                    author=author_elem.text if author_elem is not None else 'unknown',
                    score=0,
                    num_comments=0,
                    created_utc=created_utc,
                    url=link_elem.get('href') if link_elem is not None else '',
                    flair='',
                    source='rss'
                ))
            
            logger.info(f"✅ RSS: Retrieved {len(posts)} posts")
            return posts
            
        except Exception as e:
            logger.error(f"❌ RSS error: {e}")
            return []


# ============================================================================
# MAIN COLLECTOR
# ============================================================================

class WSBRawCollector:
    """Collecteur principal de posts WSB"""
    
    def __init__(self):
        self.pushshift = PushshiftScraper()
        self.rss = RSSFallback()
    
    def collect(self, hours_back: int = 24, limit: int = 500) -> List[RawPost]:
        """Collecte tous les posts disponibles"""
        logger.info(f"🚀 Starting WSB Raw Collection (last {hours_back}h)...")
        
        all_posts = {}
        
        # 1. Essayer Pushshift d'abord
        pushshift_posts = self.pushshift.fetch_posts(hours_back=hours_back, limit=limit)
        for post in pushshift_posts:
            if post.id:
                all_posts[post.id] = post
        
        # 2. Compléter avec RSS si pas assez
        if len(all_posts) < 10:
            logger.info("📡 Complementing with RSS...")
            rss_posts = self.rss.fetch_posts()
            for post in rss_posts:
                if post.id and post.id not in all_posts:
                    all_posts[post.id] = post
        
        posts = list(all_posts.values())
        
        # Trier par date (plus récent d'abord)
        posts.sort(key=lambda x: x.created_utc, reverse=True)
        
        logger.info(f"📊 Total collected: {len(posts)} unique posts")
        return posts
    
    def save(self, posts: List[RawPost], filename: Optional[str] = None) -> str:
        """Sauvegarde les posts en JSON"""
        if filename is None:
            os.makedirs(Config.DATA_DIR, exist_ok=True)
            filename = Config.RAW_FILE
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        data = {
            'collection_timestamp': datetime.now().isoformat(),
            'source': 'r/wallstreetbets',
            'total_posts': len(posts),
            'posts': [p.to_dict() for p in posts]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(posts)} posts to {filename}")
        return filename
    
    def print_summary(self, posts: List[RawPost]):
        """Affiche un résumé de la collecte"""
        print("\n" + "=" * 80)
        print(f"📥 WSB RAW COLLECTION - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)
        
        if not posts:
            print("No posts collected.")
            return
        
        print(f"\n📊 Total posts: {len(posts)}")
        
        # Stats par source
        sources = {}
        for p in posts:
            sources[p.source] = sources.get(p.source, 0) + 1
        print(f"📡 Sources: {sources}")
        
        # Plage de dates
        if posts:
            oldest = min(p.created_utc for p in posts)
            newest = max(p.created_utc for p in posts)
            print(f"📅 Date range: {datetime.fromtimestamp(oldest)} → {datetime.fromtimestamp(newest)}")
        
        # Aperçu des posts
        print(f"\n{'#':<4} {'Time':<20} {'Score':<8} {'Title (truncated)':<50}")
        print("-" * 80)
        
        for i, post in enumerate(posts[:15], 1):
            dt = datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M')
            title = post.title[:47] + "..." if len(post.title) > 50 else post.title
            print(f"{i:<4} {dt:<20} {post.score:<8} {title}")
        
        if len(posts) > 15:
            print(f"... and {len(posts) - 15} more posts")
        
        print("=" * 80)
        print(f"\n✅ Ready for FinBERT analysis!")
        print(f"   Next step: python wsb_finbert_analyzer.py --input {Config.RAW_FILE}")


# ============================================================================
# CLI
# ============================================================================

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WSB Raw Post Collector (Step 1/2)')
    parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')
    parser.add_argument('--limit', type=int, default=500, help='Max posts to collect')
    parser.add_argument('--output', type=str, help='Output JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    collector = WSBRawCollector()
    posts = collector.collect(hours_back=args.hours, limit=args.limit)
    
    output_file = args.output or Config.RAW_FILE
    collector.save(posts, output_file)
    
    if not args.quiet:
        collector.print_summary(posts)
    
    return posts


if __name__ == "__main__":
    main()
