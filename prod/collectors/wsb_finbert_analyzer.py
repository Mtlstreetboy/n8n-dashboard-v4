#!/usr/bin/env python3
"""
🤖 WSB FinBERT Sentiment Analyzer - Étape 2/2
==============================================
Analyse les posts collectés avec FinBERT (Docker ou local)

Usage:
    # Avec Docker FinBERT API (recommandé)
    docker-compose -f docker-compose.finbert.yml up -d
    python wsb_finbert_analyzer.py --input ./wsb_data/wsb_raw_posts.json
    
    # Ou en mode local (télécharge le modèle ~500MB)
    python wsb_finbert_analyzer.py --input ./wsb_data/wsb_raw_posts.json --local

Prérequis Docker:
    docker-compose -f docker-compose.finbert.yml up -d
    # Attend que le service soit prêt sur http://localhost:8088
"""

import json
import os
import time
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
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
    """Configuration"""
    DATA_DIR = os.environ.get('WSB_DATA_DIR', './wsb_data')
    RAW_FILE = os.path.join(DATA_DIR, 'wsb_raw_posts.json')
    ANALYSIS_FILE = os.path.join(DATA_DIR, 'wsb_finbert_analysis.json')
    
    # FinBERT API (Docker)
    FINBERT_API_URL = os.environ.get('FINBERT_API_URL', 'http://localhost:8088')
    
    # Ticker detection
    KNOWN_TICKERS = {
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA',
        'AMD', 'INTC', 'NFLX', 'DIS', 'PYPL', 'SQ', 'COIN', 'HOOD',
        'GME', 'AMC', 'BB', 'PLTR', 'SOFI', 'RIVN', 'LCID',
        'NIO', 'BABA', 'JD', 'DKNG', 'ROKU', 'SNAP', 'UBER', 'LYFT',
        'ABNB', 'RBLX', 'CRWD', 'ZM', 'NET', 'SNOW', 'DDOG'
    }
    
    BLACKLIST = {
        'DD', 'YOLO', 'FOMO', 'ATH', 'MOASS', 'FUD', 'HODL', 'SEC', 'FED',
        'CEO', 'CFO', 'IPO', 'ETF', 'OTM', 'ITM', 'DTE', 'OP', 'PSA',
        'USA', 'UK', 'EU', 'AI', 'EV', 'PE', 'EPS', 'ROI',
        'THE', 'AND', 'FOR', 'ALL', 'NOW', 'BUY', 'SELL', 'HOLD'
    }


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PostAnalysis:
    """Analyse FinBERT d'un post"""
    post_id: str
    title: str
    author: str
    created_datetime: str
    url: str
    score: int
    
    # FinBERT results
    sentiment_label: str  # positive, negative, neutral
    sentiment_score: float  # -1 to +1
    confidence: float  # 0 to 1
    
    # Detected tickers
    tickers: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass 
class TickerSentiment:
    """Sentiment agrégé pour un ticker"""
    ticker: str
    mentions: int
    avg_sentiment: float
    sentiment_label: str
    positive_posts: int
    negative_posts: int
    neutral_posts: int
    confidence: float
    sample_posts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# FINBERT CLIENT
# ============================================================================

class FinBERTClient:
    """Client pour FinBERT (API Docker ou local)"""
    
    def __init__(self, api_url: str = None, use_local: bool = False):
        self.api_url = api_url or Config.FINBERT_API_URL
        self.use_local = use_local
        self._local_analyzer = None
        
        if use_local:
            self._init_local()
        else:
            self._check_api()
    
    def _check_api(self):
        """Vérifie que l'API FinBERT est accessible"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ FinBERT API connected: {self.api_url}")
                return True
        except:
            pass
        
        logger.warning(f"⚠️ FinBERT API not available at {self.api_url}")
        logger.info("   Starting in local mode...")
        self.use_local = True
        self._init_local()
        return False
    
    def _init_local(self):
        """Initialise FinBERT en local"""
        try:
            # Import depuis le module existant
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from pipelines.analysis.finbert_analyzer import FinBERTAnalyzer
            self._local_analyzer = FinBERTAnalyzer()
            logger.info("✅ FinBERT local model loaded")
        except ImportError:
            logger.warning("⚠️ Local FinBERT not available, using simple fallback")
            self._local_analyzer = None
    
    def analyze(self, text: str) -> Tuple[str, float, float]:
        """
        Analyse un texte avec FinBERT
        Returns: (label, score, confidence)
        """
        if not text or len(text.strip()) < 10:
            return 'neutral', 0.0, 0.5
        
        # Tronquer si trop long (FinBERT max ~512 tokens)
        text = text[:1500]
        
        if self.use_local and self._local_analyzer:
            return self._analyze_local(text)
        else:
            return self._analyze_api(text)
    
    def _analyze_api(self, text: str) -> Tuple[str, float, float]:
        """Analyse via API Docker"""
        try:
            response = requests.post(
                f"{self.api_url}/analyze",
                json={'text': text},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                label = data.get('label', 'neutral')
                score = data.get('score', 0.0)
                confidence = data.get('confidence', 0.5)
                
                # Convertir score en -1 à +1
                if label == 'positive':
                    score = abs(score)
                elif label == 'negative':
                    score = -abs(score)
                else:
                    score = 0.0
                
                return label, score, confidence
        except Exception as e:
            logger.debug(f"API error: {e}")
        
        return 'neutral', 0.0, 0.5
    
    def _analyze_local(self, text: str) -> Tuple[str, float, float]:
        """Analyse en local"""
        if self._local_analyzer:
            try:
                result = self._local_analyzer.polarity_scores(text)
                
                # Déterminer le label
                if result['compound'] > 0.1:
                    label = 'positive'
                elif result['compound'] < -0.1:
                    label = 'negative'
                else:
                    label = 'neutral'
                
                confidence = max(result['pos'], result['neg'], result['neu'])
                return label, result['compound'], confidence
            except Exception as e:
                logger.debug(f"Local analysis error: {e}")
        
        # Fallback simple basé sur mots-clés
        return self._simple_sentiment(text)
    
    def _simple_sentiment(self, text: str) -> Tuple[str, float, float]:
        """Fallback simple si FinBERT non disponible"""
        text_lower = text.lower()
        
        bullish = ['moon', 'calls', 'bullish', 'buy', 'long', 'rocket', 'gain', 'profit', 'squeeze']
        bearish = ['puts', 'bearish', 'sell', 'short', 'crash', 'loss', 'dump', 'tank', 'drill']
        
        bull_count = sum(1 for w in bullish if w in text_lower)
        bear_count = sum(1 for w in bearish if w in text_lower)
        
        if bull_count > bear_count:
            score = min(1.0, bull_count * 0.2)
            return 'positive', score, 0.5
        elif bear_count > bull_count:
            score = -min(1.0, bear_count * 0.2)
            return 'negative', score, 0.5
        else:
            return 'neutral', 0.0, 0.5
    
    def batch_analyze(self, texts: List[str], batch_size: int = 10) -> List[Tuple[str, float, float]]:
        """Analyse un batch de textes"""
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            for text in batch:
                results.append(self.analyze(text))
            
            # Progress
            if (i + batch_size) % 50 == 0:
                logger.info(f"   Analyzed {min(i + batch_size, len(texts))}/{len(texts)} posts...")
            
            time.sleep(0.1)  # Rate limit
        
        return results


# ============================================================================
# TICKER EXTRACTOR
# ============================================================================

class TickerExtractor:
    """Extrait les tickers des textes"""
    
    PATTERNS = [
        r'\$([A-Z]{2,5})\b',
        r'\b([A-Z]{2,5})\s+(?:stock|shares|calls|puts|options)',
        r'(?:bought|sold|buying|selling)\s+([A-Z]{2,5})\b',
        r'(?:long|short)\s+([A-Z]{2,5})\b',
    ]
    
    def extract(self, text: str) -> List[str]:
        """Extrait les tickers d'un texte"""
        tickers = set()
        
        for pattern in self.PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                ticker = match.upper()
                if self._is_valid(ticker):
                    tickers.add(ticker)
        
        return list(tickers)
    
    def _is_valid(self, ticker: str) -> bool:
        """Valide un ticker"""
        if ticker in Config.BLACKLIST:
            return False
        if not 2 <= len(ticker) <= 5:
            return False
        if not ticker.isalpha():
            return False
        return True


# ============================================================================
# MAIN ANALYZER
# ============================================================================

class WSBFinBERTAnalyzer:
    """Analyseur principal WSB + FinBERT"""
    
    def __init__(self, api_url: str = None, use_local: bool = False):
        self.finbert = FinBERTClient(api_url=api_url, use_local=use_local)
        self.ticker_extractor = TickerExtractor()
    
    def load_posts(self, filename: str) -> List[Dict]:
        """Charge les posts depuis le fichier JSON"""
        logger.info(f"📂 Loading posts from {filename}...")
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        posts = data.get('posts', [])
        logger.info(f"   Loaded {len(posts)} posts")
        return posts
    
    def analyze(self, posts: List[Dict]) -> Tuple[List[PostAnalysis], List[TickerSentiment]]:
        """Analyse tous les posts avec FinBERT"""
        logger.info(f"🤖 Analyzing {len(posts)} posts with FinBERT...")
        
        post_analyses = []
        ticker_data = defaultdict(lambda: {
            'mentions': 0,
            'sentiments': [],
            'confidences': [],
            'labels': [],
            'posts': []
        })
        
        for i, post in enumerate(posts):
            # Extraire le texte
            text = post.get('full_text') or f"{post.get('title', '')}. {post.get('content', '')}"
            
            # Analyser avec FinBERT
            label, score, confidence = self.finbert.analyze(text)
            
            # Extraire les tickers
            tickers = self.ticker_extractor.extract(text)
            
            # Créer l'analyse du post
            analysis = PostAnalysis(
                post_id=post.get('id', ''),
                title=post.get('title', ''),
                author=post.get('author', 'unknown'),
                created_datetime=post.get('created_datetime', ''),
                url=post.get('url', ''),
                score=post.get('score', 0),
                sentiment_label=label,
                sentiment_score=score,
                confidence=confidence,
                tickers=tickers
            )
            post_analyses.append(analysis)
            
            # Agréger par ticker
            for ticker in tickers:
                data = ticker_data[ticker]
                data['mentions'] += 1
                data['sentiments'].append(score)
                data['confidences'].append(confidence)
                data['labels'].append(label)
                if len(data['posts']) < 3:
                    data['posts'].append(post.get('title', '')[:100])
            
            # Progress
            if (i + 1) % 25 == 0:
                logger.info(f"   Analyzed {i + 1}/{len(posts)} posts...")
        
        # Créer les analyses par ticker
        ticker_analyses = []
        for ticker, data in ticker_data.items():
            if data['mentions'] >= 1:
                avg_sentiment = sum(data['sentiments']) / len(data['sentiments'])
                avg_confidence = sum(data['confidences']) / len(data['confidences'])
                
                # Compter les labels
                label_counts = Counter(data['labels'])
                
                # Déterminer le label global
                if avg_sentiment > 0.1:
                    sentiment_label = '🚀 Bullish'
                elif avg_sentiment < -0.1:
                    sentiment_label = '📉 Bearish'
                else:
                    sentiment_label = '➖ Neutral'
                
                ticker_analyses.append(TickerSentiment(
                    ticker=ticker,
                    mentions=data['mentions'],
                    avg_sentiment=round(avg_sentiment, 3),
                    sentiment_label=sentiment_label,
                    positive_posts=label_counts.get('positive', 0),
                    negative_posts=label_counts.get('negative', 0),
                    neutral_posts=label_counts.get('neutral', 0),
                    confidence=round(avg_confidence, 3),
                    sample_posts=data['posts'][:3]
                ))
        
        # Trier par mentions
        ticker_analyses.sort(key=lambda x: x.mentions, reverse=True)
        
        logger.info(f"✅ Analysis complete: {len(post_analyses)} posts, {len(ticker_analyses)} tickers")
        return post_analyses, ticker_analyses
    
    def save(self, post_analyses: List[PostAnalysis], ticker_analyses: List[TickerSentiment], 
             filename: str = None) -> str:
        """Sauvegarde les résultats"""
        if filename is None:
            os.makedirs(Config.DATA_DIR, exist_ok=True)
            filename = Config.ANALYSIS_FILE
        
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'model': 'FinBERT (ProsusAI/finbert)',
            'total_posts': len(post_analyses),
            'total_tickers': len(ticker_analyses),
            'ticker_summary': [t.to_dict() for t in ticker_analyses],
            'post_analyses': [p.to_dict() for p in post_analyses]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to {filename}")
        return filename
    
    def print_report(self, post_analyses: List[PostAnalysis], ticker_analyses: List[TickerSentiment]):
        """Affiche un rapport"""
        print("\n" + "=" * 100)
        print(f"🤖 WSB FINBERT SENTIMENT ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 100)
        
        # Stats globales
        total = len(post_analyses)
        positive = sum(1 for p in post_analyses if p.sentiment_label == 'positive')
        negative = sum(1 for p in post_analyses if p.sentiment_label == 'negative')
        neutral = total - positive - negative
        
        print(f"\n📊 Overall Sentiment Distribution:")
        print(f"   🟢 Positive: {positive} ({positive/total*100:.1f}%)")
        print(f"   🔴 Negative: {negative} ({negative/total*100:.1f}%)")
        print(f"   ⚪ Neutral:  {neutral} ({neutral/total*100:.1f}%)")
        
        # Top tickers
        print(f"\n📈 TOP TICKERS BY MENTION:")
        print(f"\n{'#':<4} {'Ticker':<8} {'Mentions':<10} {'Sentiment':<12} {'Label':<16} {'Confidence'}")
        print("-" * 80)
        
        for i, ticker in enumerate(ticker_analyses[:20], 1):
            sentiment_bar = "+" * max(0, int(ticker.avg_sentiment * 5)) if ticker.avg_sentiment > 0 else \
                           "-" * max(0, int(-ticker.avg_sentiment * 5))
            print(f"{i:<4} {ticker.ticker:<8} {ticker.mentions:<10} {ticker.avg_sentiment:>+.3f}      "
                  f"{ticker.sentiment_label:<16} {ticker.confidence:.2f}")
        
        print("=" * 100)
        
        # Validés seulement (dans KNOWN_TICKERS)
        validated = [t for t in ticker_analyses if t.ticker in Config.KNOWN_TICKERS]
        print(f"\n✅ Validated tickers (known stocks): {len(validated)}")
        
        if validated:
            print(f"\n{'Ticker':<8} {'Mentions':<10} {'Sentiment':<12} {'Label'}")
            print("-" * 50)
            for t in validated[:10]:
                print(f"{t.ticker:<8} {t.mentions:<10} {t.avg_sentiment:>+.3f}      {t.sentiment_label}")
        
        print("\n" + "=" * 100)
        print("🤖 Model: FinBERT (ProsusAI/finbert) - Specialized for financial text")


# ============================================================================
# CLI
# ============================================================================

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WSB FinBERT Analyzer (Step 2/2)')
    parser.add_argument('--input', type=str, default=Config.RAW_FILE, 
                       help='Input JSON file from collector')
    parser.add_argument('--output', type=str, help='Output analysis file')
    parser.add_argument('--api', type=str, default=Config.FINBERT_API_URL,
                       help='FinBERT API URL')
    parser.add_argument('--local', action='store_true', 
                       help='Use local FinBERT model instead of API')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    # Vérifier que le fichier d'entrée existe
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        print(f"   Run first: python wsb_raw_collector.py --hours 24")
        return
    
    analyzer = WSBFinBERTAnalyzer(api_url=args.api, use_local=args.local)
    posts = analyzer.load_posts(args.input)
    post_analyses, ticker_analyses = analyzer.analyze(posts)
    
    output_file = args.output or Config.ANALYSIS_FILE
    analyzer.save(post_analyses, ticker_analyses, output_file)
    
    if not args.quiet:
        analyzer.print_report(post_analyses, ticker_analyses)


if __name__ == "__main__":
    main()
