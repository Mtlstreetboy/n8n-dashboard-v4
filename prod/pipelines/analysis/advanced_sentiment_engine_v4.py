#!/usr/bin/env python3
"""
⚠️⚠️⚠️ MOTEUR DE SENTIMENT MULTI-DIMENSIONNEL V4 - DUAL BRAIN AGENTIC
--------------------------------------------------------------------
Version V4 avec ARCHITECTURE AGENTIQUE:
- 🧠 System 2 (Logique): Qwen 2.5 7B pour la configuration et les maths
- 🗣️ System 1 (Narrative): Llama 3.1 8B pour l'interprétation et le storytelling
- 🎯 Analyst Insights intégré
- 🌪️ Détection de régime de volatilité
- 🔍 Détection automatique de catalyseurs
- 🚨 Système d'alertes intelligentes

Basé sur V3, optimisé pour hardware local (RTX 2070 Ti)
"""
import sys
import os

# Environment Detection & Path Setup
if os.path.exists('/data/scripts'):
    # Docker
    sys.path.insert(0, '/data/scripts')
    DATA_DIR = '/data'
    NEWS_DATA_DIR = '/data/files/companies'
    OPTIONS_DATA_DIR = '/data/options_data'
    FINANCIALS_DATA_DIR = '/data/files/financials'
    OUTPUT_DIR = '/data/sentiment_analysis'
else:
    # Local Windows
    current_dir = os.path.dirname(os.path.abspath(__file__)) # .../prod/pipelines/analysis
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) # analysis -> pipelines -> prod -> root
    
    # Add prod to path for imports
    prod_dir = os.path.dirname(os.path.dirname(current_dir)) # analysis -> pipelines -> prod
    sys.path.append(prod_dir)
    
    DATA_DIR = os.path.join(project_root, 'local_files')
    NEWS_DATA_DIR = os.path.join(DATA_DIR, 'companies') 
    OPTIONS_DATA_DIR = os.path.join(DATA_DIR, 'options_data')
    FINANCIALS_DATA_DIR = os.path.join(DATA_DIR, 'financials')
    OUTPUT_DIR = os.path.join(DATA_DIR, 'sentiment_analysis')

# Force UTF-8 for Windows Console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# DUAL BRAIN CONFIGURATION
MODEL_LOGIC = "qwen2.5:7b"      # Pour structures, JSON, maths
MODEL_NARRATIVE = "llama3.1:8b" # Pour texte, nuance, synthèse

import json
import yfinance as yf
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import math
import re
import requests

# Local relative imports
try:
    from .finbert_analyzer import FinBERTAnalyzer
except ImportError:
    try:
        from finbert_analyzer import FinBERTAnalyzer
    except Exception:
        FinBERTAnalyzer = None

# Import module analyst insights
try:
    from .analyst_insights_integration import AnalystInsightsIntegration, AnalystSignal
except ImportError:
    try:
        from analyst_insights_integration import AnalystInsightsIntegration, AnalystSignal
    except ImportError:
        print("⚠️ Module analyst_insights_integration non trouvé. Fonctionnalité analyst insights désactivée.")
        AnalystInsightsIntegration = None
        AnalystSignal = None

# Configuration
# Constants are now set dynamically above
# NEWS_DATA_DIR ...
# OPTIONS_DATA_DIR ...
# OUTPUT_DIR ...
def _get_ollama_api_urls() -> List[str]:
    """Return a prioritized list of Ollama endpoints.

    In Docker, `localhost` points to the container; `host.docker.internal` usually
    points to the host on Docker Desktop.
    """
    configured = (os.getenv('OLLAMA_API_URL') or '').strip()
    urls: List[str] = []
    if configured:
        urls.append(configured)
    # Docker Desktop (Windows/macOS) host gateway
    urls.append('http://host.docker.internal:11434/api/generate')
    # Ollama running inside the same container
    urls.append('http://localhost:11434/api/generate')
    # de-dup
    deduped: List[str] = []
    for u in urls:
        if u and u not in deduped:
            deduped.append(u)
    return deduped


def _ollama_generate(model: str, prompt: str, temperature: float, timeout: int = 30) -> str:
    """Call Ollama `/api/generate` with fallback across candidate URLs."""
    last_err: Exception | None = None
    for url in _get_ollama_api_urls():
        try:
            response = requests.post(
                url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                },
                timeout=timeout,
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")

            return response.json().get('response', '')
        except Exception as e:
            last_err = e
            continue

    raise Exception(f"Ollama unavailable on any endpoint: {last_err}")

@dataclass
class SentimentSignal:
    """Signal de sentiment avec métadonnées"""
    timestamp: str
    source: str  # 'news', 'options', 'combined'
    score: float  # -1 à +1
    confidence: float  # 0 à 1
    volume: int  # nombre d'articles ou contrats
    metadata: dict

class AdvancedSentimentEngineV4:
    def __init__(self, ticker: str, use_llm_config: bool = True):
        self.ticker = ticker
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Configuration adaptative par LLM ou défaut
        if use_llm_config:
            llm_config = self.generate_ticker_config_with_llm(ticker)
            self.params = {
                'temporal_decay_halflife': llm_config['temporal_decay_halflife'],
                'momentum_window': llm_config['momentum_window'],
                'volatility_penalty': llm_config['volatility_penalty'],
                'volume_weight_exp': 0.5,
                'divergence_threshold': llm_config['divergence_threshold'],
                'institutional_premium': llm_config['institutional_premium'],
            }
            self.config_rationale = llm_config.get('rationale', '')
        else:
            self.params = self._get_default_config()
            self.config_rationale = 'Configuration par défaut'
    
    def _get_default_config(self) -> Dict:
        """Configuration par défaut si LLM fail"""
        return {
            'temporal_decay_halflife': 3,
            'momentum_window': 7,
            'volatility_penalty': 0.3,
            'volume_weight_exp': 0.5,
            'divergence_threshold': 0.4,
            'institutional_premium': 0.2,
            'rationale': 'Configuration par défaut (modérée)'
        }
    
    def load_news_sentiment(self, days=100) -> List[SentimentSignal]:
        """Charge et analyse le sentiment des nouvelles avec analyse LLM existante"""
        news_file = os.path.join(NEWS_DATA_DIR, f'{self.ticker}_news.json')
        
        if not os.path.exists(news_file):
            print(f"⚠️⚠️⚠️  Aucune donnée de nouvelles pour {self.ticker}")
            return []
        
        with open(news_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'articles' in data:
            articles = data['articles']
        elif isinstance(data, list):
            articles = data
        else:
            print(f"⚠️⚠️⚠️  Format de données inconnu pour {self.ticker}")
            return []
        
        print(f"📄 Analyse de {len(articles)} articles...")
        
        signals = []
        cutoff = datetime.now() - timedelta(days=days)
        
        for article in articles:
            pub_date_str = article.get('published_at', '')
            try:
                pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                if pub_date.tzinfo is None:
                    from datetime import timezone
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
            except:
                continue
            
            from datetime import timezone
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
            
            if pub_date < cutoff:
                continue
            
            # PRIORITY 1: Cached Sentiment (New Format)
            cached_sent = article.get('sentiment')
            llm_data = article.get('llm_sentiment', {})
            
            if cached_sent and isinstance(cached_sent, dict) and 'compound' in cached_sent:
                # Use cached FinBERT/Contextual sentiment
                sentiment_score = cached_sent.get('compound', 0.0)
                # Confidence is roughly proportional to how non-neutral it is + relevance
                relevance = cached_sent.get('relevance', 0.5)
                confidence = 0.5 + (relevance * 0.5)
                method = cached_sent.get('method', 'cached')
                
            elif llm_data and 'sentiment_score' in llm_data:
                # Use LLM sentiment (Old Format)
                raw_score = llm_data.get('sentiment_score', 0)
                sentiment_score = np.clip(raw_score / 100.0, -1, 1)
                confidence = llm_data.get('confidence', 0.7)
                method = 'llm'
                
            else:
                # FALLBACK: Try FinBERT first if available (local or API), fallback to keywords
                text_for_sent = (article.get('title') or '') + ' ' + (article.get('content') or '')
                if FinBERTAnalyzer is not None:
                    try:
                        analyzer = FinBERTAnalyzer()
                        s = analyzer.polarity_scores(text_for_sent)
                        sentiment_score = float(np.clip(s.get('compound', 0.0), -1, 1))
                        # Confidence proxy: max of pos/neg magnitude
                        confidence = float(np.clip(max(s.get('pos', 0.0), s.get('neg', 0.0)), 0, 1))
                        method = 'finbert_live'
                    except Exception:
                        sentiment_score, confidence = self._simple_sentiment_analysis(article)
                        method = 'keyword_fallback'
                else:
                    sentiment_score, confidence = self._simple_sentiment_analysis(article)
                    method = 'keyword_fallback'
            
            # Defensive: ensure content is never None
            content_text = article.get('content') or ''
            title_text = article.get('title') or ''
            
            signal = SentimentSignal(
                timestamp=pub_date.isoformat(),
                source='news_llm',
                score=sentiment_score,
                confidence=confidence,
                volume=1,
                metadata={
                    'title': title_text,
                    'source': article.get('source', 'Unknown'),
                    'content': content_text[:200],
                    'method': 'llm' if 'sentiment_score' in llm_data else ('finbert' if FinBERTAnalyzer is not None else 'keyword')
                }
            )
            signals.append(signal)
        
        print(f"📄 {len(signals)} articles avec sentiment détecté")
        return signals
    
    def _simple_sentiment_analysis(self, article: dict) -> Tuple[float, float]:
        """Fallback: utilise FinBERT si disponible, sinon mots-clés"""
        title = article.get('title') or ''
        content = article.get('content') or ''
        text = (title + ' ' + content).strip()
        
        if not text:
            return 0.0, 0.0
        
        # Essayer FinBERT d'abord
        try:
            from finbert_analyzer import FinBERTAnalyzer
            analyzer = FinBERTAnalyzer()
            if analyzer.is_available:
                scores = analyzer.analyze(text)
                return scores['compound'], min(1 - scores['neutral'], 1.0)
        except ImportError:
            pass
        
        # Fallback: analyse par mots-clés financiers
        text_lower = text.lower()
        
        positive_words = {
            'surge': 3, 'soar': 3, 'breakthrough': 3, 'revolutionary': 3,
            'record': 2.5, 'boom': 2.5, 'stellar': 2.5, 'exceptional': 2.5,
            'growth': 2, 'profit': 2, 'gain': 2, 'success': 2, 'innovation': 2,
            'beat': 2, 'outperform': 2, 'upgrade': 2, 'bullish': 2,
            'positive': 1, 'improve': 1, 'strong': 1, 'rise': 1, 'increase': 1
        }
        
        negative_words = {
            'crash': -3, 'collapse': -3, 'scandal': -3, 'fraud': -3,
            'plunge': -2.5, 'crisis': -2.5, 'disaster': -2.5, 'catastrophic': -2.5,
            'loss': -2, 'decline': -2, 'fall': -2, 'miss': -2, 'concern': -2,
            'downgrade': -2, 'bearish': -2, 'lawsuit': -2, 'investigation': -2,
            'negative': -1, 'weak': -1, 'drop': -1, 'decrease': -1, 'risk': -1
        }
        
        sentiment_score = 0
        word_count = 0
        
        for word, weight in positive_words.items():
            count = text_lower.count(word)
            sentiment_score += count * weight
            word_count += count
        
        for word, weight in negative_words.items():
            count = text_lower.count(word)
            sentiment_score += count * weight
            word_count += count
        
        if word_count > 0:
            normalized_score = np.tanh(sentiment_score / 10)
            confidence = min(word_count / 5, 1.0)
            return normalized_score, confidence
        
        return 0.0, 0.0
    
    def load_analyst_insights(self):
        """🎯 NOUVELLE DIMENSION V3: Charge et analyse le consensus des analystes professionnels"""
        if AnalystInsightsIntegration is None:
            # Fallback silencieux si module manquant
            return None
        
        try:
            analyst_integration = AnalystInsightsIntegration(self.ticker)
            analyst_signal = analyst_integration.load_analyst_insights()
            return analyst_signal
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement analyst insights: {e}")
            return None

    def load_financial_sentiment(self) -> SentimentSignal:
        """💰 NOUVELLE DIMENSION V5 (Financials): Analyse Valuations & Targets"""
        fin_file = os.path.join(FINANCIALS_DATA_DIR, f'{self.ticker}_financials.json')
        
        if not os.path.exists(fin_file):
            print(f"⚠️ Aucune donnée financière pour {self.ticker}")
            return None
            
        try:
            with open(fin_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metrics = data.get('metrics', {})
            
            # 1. Upside Score
            upside = metrics.get('analyst_upside_potential', 0) or 0
            if upside > 0.15:
                upside_score = min((upside - 0.15) / 0.2, 1.0) # >35% upside = max score
            elif upside < 0:
                upside_score = max(upside / 0.2, -1.0)
            else:
                upside_score = 0.1 # Légèrement positif si positif
                
            # 2. Recommendation Score (1=Strong Buy, 5=Sell)
            rec_mean = metrics.get('recommendationMean')
            rec_score = 0
            if rec_mean:
                if rec_mean < 2.0: # Strong Buy
                    rec_score = (2.5 - rec_mean) / 1.5 
                elif rec_mean > 3.0: # Sell
                    rec_score = -(rec_mean - 2.5) / 2.5
            
            # 3. P/E Score (Sommaire)
            pe_score = 0
            # Trailing vs Forward PE improvement
            trailing = metrics.get('trailingPE')
            forward = metrics.get('forwardPE')
            
            if trailing and forward and forward < trailing:
                pe_score = 0.2 # Improving earnings expected
            
            # Mix final
            final_score = (upside_score * 0.5) + (rec_score * 0.3) + (pe_score * 0.2)
            final_score = np.clip(final_score, -1, 1)
            
            # Confiance basée sur nb analystes
            nb_analysts = metrics.get('numberOfAnalystOpinions', 0) or 0
            confidence = min(nb_analysts / 20, 1.0)
            if confidence == 0: confidence = 0.5 # Default confidence if no analyst data but other data exists
            
            print(f"💰 Sentiment Financier: {final_score:.3f} (Confiance: {confidence:.2f})")
            
            return SentimentSignal(
                timestamp=data.get('collected_at', datetime.now().isoformat()),
                source='financials',
                score=final_score,
                confidence=confidence,
                volume=nb_analysts,
                metadata={
                    'upside': upside,
                    'rec_mean': rec_mean,
                    'pe_forward': forward,
                    'pe_trailing': trailing
                }
            )
            
        except Exception as e:
            print(f"⚠️ Erreur chargement financials {self.ticker}: {e}")
            return None
    
    def load_options_sentiment(self) -> SentimentSignal:
        """Charge et analyse le sentiment des options avec métriques avancées"""
        sentiment_file = os.path.join(OPTIONS_DATA_DIR, f'{self.ticker}_latest_sentiment.json')
        
        if not os.path.exists(sentiment_file):
            print(f"⚠️⚠️⚠️  Aucune donnée d'options pour {self.ticker}")
            return None
        
        with open(sentiment_file, 'r', encoding='utf-8') as f:
            metrics = json.load(f)
        
        print(f"📊 Analyse des options...")
        
        pcr_volume = metrics.get('put_call_ratio_volume', 1.0)
        pcr_oi = metrics.get('put_call_ratio_oi', 1.0)
        call_iv = metrics.get('call_implied_volatility', 0)
        put_iv = metrics.get('put_implied_volatility', 0)
        total_volume = metrics.get('total_contracts', 0)
        call_volume = metrics.get('call_volume', 0)
        put_volume = metrics.get('put_volume', 0)
        
        if pcr_volume < 0.7:
            base_sentiment = (0.7 - pcr_volume) / 0.7
        elif pcr_volume > 1.3:
            base_sentiment = -(pcr_volume - 1.3) / 1.3
        else:
            base_sentiment = -(pcr_volume - 0.7) / 0.6
        
        avg_iv = (call_iv + put_iv) / 2
        iv_factor = 1 - (avg_iv * self.params['volatility_penalty'])
        iv_factor = max(0.5, min(1.0, iv_factor))
        
        iv_skew = (put_iv - call_iv) / max(call_iv, 0.01)
        skew_adjustment = -np.tanh(iv_skew * 2) * 0.2
        
        oi_volume_ratio = pcr_oi / max(pcr_volume, 0.01)
        if oi_volume_ratio > 1.2:
            smart_money_factor = (oi_volume_ratio - 1) * self.params['institutional_premium']
            smart_money_factor = min(smart_money_factor, 0.15)
        else:
            smart_money_factor = 0
        
        sentiment_score = base_sentiment * iv_factor + skew_adjustment
        sentiment_score = np.clip(sentiment_score, -1, 1)
        
        volume_confidence = min(np.log1p(total_volume) / 15, 1.0)
        
        if smart_money_factor > 0:
            volume_confidence = min(volume_confidence * 1.2, 1.0)
        
        signal = SentimentSignal(
            timestamp=metrics.get('timestamp', datetime.now().isoformat()),
            source='options',
            score=sentiment_score,
            confidence=volume_confidence,
            volume=total_volume,
            metadata={
                'pcr_volume': pcr_volume,
                'pcr_oi': pcr_oi,
                'call_iv': call_iv,
                'put_iv': put_iv,
                'iv_factor': iv_factor,
                'iv_skew': iv_skew,
                'smart_money_factor': smart_money_factor,
                'call_volume': call_volume,
                'put_volume': put_volume
            }
        )
        
        print(f"📊 Sentiment options: {sentiment_score:.3f} (confiance: {volume_confidence:.2%})")
        return signal
    
    def calculate_temporal_decay(self, signals: List[SentimentSignal]) -> List[float]:
        """Applique un decay exponentiel: nouvelles récentes pèsent plus lourd"""
        now = datetime.now()
        weights = []
        
        for signal in signals:
            try:
                signal_time = datetime.fromisoformat(signal.timestamp.replace('Z', '+00:00'))
                days_ago = (now - signal_time).total_seconds() / 86400
                
                decay = 0.5 ** (days_ago / self.params['temporal_decay_halflife'])
                weights.append(decay)
            except:
                weights.append(0.1)
        
        return weights
    
    def calculate_price_momentum(self, window_days: int = 10) -> float:
        """📊 Price Momentum: Traditional price change over N days"""
        try:
            ticker_data = yf.Ticker(self.ticker)
            hist = ticker_data.history(period='1mo', interval='1d')
            
            if len(hist) < window_days:
                return 0.0
            
            current_price = hist['Close'].iloc[-1]
            old_price = hist['Close'].iloc[-window_days]
            
            if old_price == 0:
                return 0.0
            
            # Normalize to -1 to +1 range (±20% price change = ±1.0)
            price_change_pct = (current_price - old_price) / old_price
            momentum = np.clip(price_change_pct * 5, -1, 1)
            
            return momentum
        except Exception as e:
            print(f"⚠️ Price momentum calculation failed for {self.ticker}: {e}")
            return 0.0
    
    def calculate_volume_momentum(self, window_days: int = 10) -> float:
        """📈 Volume Momentum: Recent volume vs average"""
        try:
            ticker_data = yf.Ticker(self.ticker)
            hist = ticker_data.history(period='1mo', interval='1d')
            
            if len(hist) < window_days:
                return 0.0
            
            recent_volume = hist['Volume'].iloc[-3:].mean()  # Last 3 days average
            avg_volume = hist['Volume'].iloc[-window_days:].mean()
            
            if avg_volume == 0:
                return 0.0
            
            # Normalize to -1 to +1 range (2x volume = +1.0, 0.5x = -1.0)
            volume_ratio = recent_volume / avg_volume
            momentum = np.clip((volume_ratio - 1) * 2, -1, 1)
            
            return momentum
        except Exception as e:
            print(f"⚠️ Volume momentum calculation failed for {self.ticker}: {e}")
            return 0.0
    
    def calculate_news_momentum(self, signals: List[SentimentSignal]) -> float:
        """📰 News Momentum: Velocity of sentiment change (original narrative momentum)"""
        if len(signals) < 2:
            return 0.0
        
        sorted_signals = sorted(signals, key=lambda x: x.timestamp)
        
        window = self.params['momentum_window']
        now = datetime.now()
        
        recent = []
        older = []
        
        for signal in sorted_signals:
            try:
                signal_time = datetime.fromisoformat(signal.timestamp.replace('Z', '+00:00'))
                days_ago = (now - signal_time).total_seconds() / 86400
                
                if days_ago <= window:
                    recent.append(signal)
                elif days_ago <= window * 2:
                    older.append(signal)
            except:
                continue
        
        if not recent or not older:
            return 0.0
        
        recent_sentiment = np.mean([s.score * s.confidence for s in recent])
        older_sentiment = np.mean([s.score * s.confidence for s in older])
        
        momentum = (recent_sentiment - older_sentiment) * 2
        momentum = np.clip(momentum, -1, 1)
        
        return momentum
    
    def calculate_smart_momentum(self, signals: List[SentimentSignal]) -> Dict:
        """🚀 SMART MOMENTUM MULTI-DIMENSIONNEL
        
        Combines 3 momentum indicators:
        - Price Momentum (50%): Traditional 10-day price change
        - News Momentum (30%): Sentiment velocity from articles
        - Volume Momentum (20%): Trading volume acceleration
        
        Returns comprehensive momentum analysis with divergence detection
        """
        # Calculate individual components
        price_mom = self.calculate_price_momentum(window_days=10)
        news_mom = self.calculate_news_momentum(signals)
        volume_mom = self.calculate_volume_momentum(window_days=10)
        
        # Weighted combination
        smart_momentum = (price_mom * 0.5) + (news_mom * 0.3) + (volume_mom * 0.2)
        smart_momentum = np.clip(smart_momentum, -1, 1)
        
        # Divergence detection: Price vs News
        divergence_detected = False
        divergence_type = None
        divergence_magnitude = abs(price_mom - news_mom)
        
        if divergence_magnitude > 0.5:  # Significant divergence
            divergence_detected = True
            if price_mom > 0.3 and news_mom < -0.3:
                divergence_type = "🐂 BULLISH DIVERGENCE: Price rising despite negative news (Smart Money buying)"
            elif price_mom < -0.3 and news_mom > 0.3:
                divergence_type = "🐻 BEARISH DIVERGENCE: Price falling despite positive news (Smart Money selling)"
        
        # Actionable interpretation
        if smart_momentum > 0.5:
            signal = "🚀 STRONG BUY MOMENTUM"
            interpretation = "All indicators converging upward - high confidence trend"
        elif smart_momentum > 0.2:
            signal = "📈 Building Momentum"
            interpretation = "Positive trend developing - watch for continuation"
        elif smart_momentum > -0.2:
            signal = "➡️ Consolidation"
            interpretation = "Sideways movement - awaiting catalyst"
        elif smart_momentum > -0.5:
            signal = "📉 Weakening"
            interpretation = "Negative momentum building - consider risk management"
        else:
            signal = "💥 STRONG SELL MOMENTUM"
            interpretation = "All indicators converging downward - high risk"
        
        return {
            'smart_momentum': round(smart_momentum, 4),
            'components': {
                'price_momentum': round(price_mom, 4),
                'news_momentum': round(news_mom, 4),
                'volume_momentum': round(volume_mom, 4)
            },
            'signal': signal,
            'interpretation': interpretation,
            'divergence_detected': divergence_detected,
            'divergence_type': divergence_type,
            'divergence_magnitude': round(divergence_magnitude, 4) if divergence_detected else 0
        }
    
    def detect_divergence(self, news_signal: float, options_signal: float) -> Dict:
        """🔍 INNOVATION: Détecte les divergences entre ce que les gens DISENT et FONT"""
        divergence_magnitude = abs(news_signal - options_signal)
        
        if divergence_magnitude < self.params['divergence_threshold']:
            divergence_type = 'aligned'
            opportunity_score = 0
        elif news_signal > 0 and options_signal < 0:
            divergence_type = 'bearish_divergence'
            opportunity_score = divergence_magnitude * 0.8
        elif news_signal < 0 and options_signal > 0:
            divergence_type = 'bullish_divergence'
            opportunity_score = divergence_magnitude * 1.2
        else:
            divergence_type = 'weak_divergence'
            opportunity_score = divergence_magnitude * 0.3
        
        return {
            'type': divergence_type,
            'magnitude': divergence_magnitude,
            'opportunity_score': opportunity_score,
            'interpretation': self._interpret_divergence(divergence_type, divergence_magnitude)
        }
    
    def _interpret_divergence(self, div_type: str, magnitude: float) -> str:
        """Interprétation humaine de la divergence"""
        interpretations = {
            'aligned': "🤝 Consensus - Nouvelles et marchés s'accordent",
            'bearish_divergence': f"🐻 BEARISH DIVERGENCE (force: {magnitude:.2f}) - Le marché ignore les bonnes nouvelles. Possible correction à venir ou les nouvelles sont 'priced in'.",
            'bullish_divergence': f"🐂 BULLISH DIVERGENCE (force: {magnitude:.2f}) - Le marché achète malgré les mauvaises nouvelles. Smart money voit une opportunité. Signal d'achat potentiel.",
            'weak_divergence': f"⚠️ Divergence faible (force: {magnitude:.2f}) - Incertitude, attendre confirmation."
        }
        return interpretations.get(div_type, "")
    
    def calculate_conviction_score(self, news_signals: List[SentimentSignal], 
                                   options_signal: SentimentSignal) -> float:
        """🧮 INNOVATION: Score de conviction - mesure la FORCE de l'alignement"""
        if not news_signals or not options_signal:
            return 0.5
        
        news_scores = [s.score * s.confidence for s in news_signals]
        news_sentiment = np.mean(news_scores) if news_scores else 0
        
        options_sentiment = options_signal.score
        
        if (news_sentiment > 0 and options_sentiment > 0) or \
           (news_sentiment < 0 and options_sentiment < 0):
            conviction = (abs(news_sentiment) + abs(options_sentiment)) / 2
            conviction *= 1.2
        else:
            conviction = 0.3
        
        volume_factor = min(np.log1p(options_signal.volume) / 12, 1.0)
        conviction *= (0.7 + 0.3 * volume_factor)
        
        return np.clip(conviction, 0, 1)
    
    def calculate_fear_greed_asymmetry(self, signals: List[SentimentSignal]) -> float:
        """😨🤑 INNOVATION: Les marchés réagissent plus aux mauvaises nouvelles qu'aux bonnes"""
        if not signals:
            return 0
        
        positive_signals = [s for s in signals if s.score > 0]
        negative_signals = [s for s in signals if s.score < 0]
        
        if not positive_signals and not negative_signals:
            return 0
        
        avg_positive = np.mean([s.score for s in positive_signals]) if positive_signals else 0
        avg_negative = np.mean([abs(s.score) for s in negative_signals]) if negative_signals else 0
        
        if avg_negative > avg_positive * 1.3:
            return -0.15
        elif avg_positive > avg_negative * 1.3:
            return 0.10
        
        return 0
    
    # ============================================================================
    # 3. VOLATILITY REGIME DETECTION
    # ============================================================================
    
    def detect_market_regime(self, options_signal: SentimentSignal) -> Dict:
        """🌪️ Détecte le régime de volatilité et ajuste l'interprétation"""
        if not options_signal or not options_signal.metadata:
            return {
                'regime': 'UNKNOWN',
                'confidence': 0.0,
                'implications': 'Données insuffisantes pour déterminer le régime'
            }
        
        call_iv = options_signal.metadata.get('call_iv', 0)
        put_iv = options_signal.metadata.get('put_iv', 0)
        avg_iv = (call_iv + put_iv) / 2
        iv_skew = options_signal.metadata.get('iv_skew', 0)
        pcr_volume = options_signal.metadata.get('pcr_volume', 1.0)
        
        regime_data = {
            'avg_iv': avg_iv,
            'iv_skew': iv_skew,
            'pcr_volume': pcr_volume
        }
        
        if avg_iv > 0.5:
            regime = 'HIGH_VOLATILITY'
            confidence = min((avg_iv - 0.5) / 0.5, 1.0)
            
            if pcr_volume > 1.2:
                sub_regime = 'PANIC'
                implications = "🚨 PANIQUE - Les traders se couvrent agressivement. Opportunité contrarian possible mais risquée."
                signal_adjustment = -0.2
            else:
                sub_regime = 'EUPHORIA'
                implications = "🎢 EUPHORIE - Volatilité élevée avec optimisme. Attention aux corrections."
                signal_adjustment = -0.15
        
        elif avg_iv < 0.2:
            regime = 'LOW_VOLATILITY'
            confidence = min((0.2 - avg_iv) / 0.2, 1.0)
            sub_regime = 'COMPLACENT'
            implications = "😴 COMPLACENCE - Marché trop calme. Risque de mouvement brusque imminent. Augmenter vigilance."
            signal_adjustment = -0.1
        
        elif 0.3 <= avg_iv <= 0.4:
            regime = 'NORMAL_VOLATILITY'
            confidence = 1.0 - abs(avg_iv - 0.35) / 0.05
            sub_regime = 'HEALTHY'
            implications = "✅ NORMAL - Volatilité saine. Signaux de sentiment plus fiables."
            signal_adjustment = 0.0
        
        else:
            regime = 'MODERATE_VOLATILITY'
            confidence = 0.7
            
            if avg_iv > 0.35:
                sub_regime = 'RISING'
                implications = "📈 TENSION MONTANTE - Nervosité croissante. Surveiller pour escalade."
            else:
                sub_regime = 'FALLING'
                implications = "📉 DÉTENTE - Volatilité en baisse. Retour à la normale possible."
            
            signal_adjustment = -0.05
        
        skew_analysis = ""
        if abs(iv_skew) > 0.3:
            if iv_skew > 0:
                skew_analysis = " | ⚠️ Put skew élevé - Protection tail risk demandée"
            else:
                skew_analysis = " | 📞 Call skew élevé - Spéculation haussière agressive"
        
        return {
            'regime': regime,
            'sub_regime': sub_regime,
            'confidence': round(confidence, 3),
            'metrics': regime_data,
            'implications': implications + skew_analysis,
            'signal_adjustment': signal_adjustment,
            'recommendation': self._get_regime_recommendation(regime, sub_regime)
        }
    
    def _get_regime_recommendation(self, regime: str, sub_regime: str) -> str:
        """Recommandations tactiques selon le régime"""
        recommendations = {
            ('HIGH_VOLATILITY', 'PANIC'): "Attendre stabilisation. Si conviction forte, petites positions avec stops serrés.",
            ('HIGH_VOLATILITY', 'EUPHORIA'): "Prendre profits partiels. Réduire exposition. Volatilité = risque bidirectionnel.",
            ('LOW_VOLATILITY', 'COMPLACENT'): "Surveiller catalyseurs. Préparer scenarios. Volatilité reviendra.",
            ('NORMAL_VOLATILITY', 'HEALTHY'): "Conditions idéales pour trading selon signaux. Suivre plan normal.",
            ('MODERATE_VOLATILITY', 'RISING'): "Augmenter prudence. Réduire taille positions. Surveiller évolution.",
            ('MODERATE_VOLATILITY', 'FALLING'): "Environnement s'améliore. Opportunité de repositionnement graduel."
        }
        
        return recommendations.get((regime, sub_regime), "Surveiller et ajuster selon évolution.")
    
    # ============================================================================
    # 4. DÉTECTION DE CATALYSEURS
    # ============================================================================
    
    def detect_catalysts(self, news_signals: List[SentimentSignal]) -> Dict:
        """🔍 Identifie les événements/catalyseurs majeurs qui impactent le sentiment"""
        if not news_signals:
            return {
                'catalysts_detected': [],
                'count': 0,
                'most_recent': None,
                'impact_assessment': 'NO_DATA',
                'recommendation': 'Pas de données articles disponibles pour détecter des catalyseurs.',
                'categories_present': []
            }
        
        catalyst_patterns = {
            'earnings': {
                'keywords': ['earnings', 'quarter', 'q1', 'q2', 'q3', 'q4', 
                            'revenue', 'eps', 'profit', 'guidance', 'beat', 'miss'],
                'impact_weight': 0.9,
                'category': 'FINANCIAL'
            },
            'fda_regulatory': {
                'keywords': ['fda', 'approval', 'clinical trial', 'phase', 
                            'drug', 'medication', 'regulatory', 'clearance'],
                'impact_weight': 0.95,
                'category': 'REGULATORY'
            },
            'merger_acquisition': {
                'keywords': ['merger', 'acquisition', 'buyout', 'takeover', 
                            'acquire', 'deal', 'bid', 'offer'],
                'impact_weight': 1.0,
                'category': 'CORPORATE_ACTION'
            },
            'product_launch': {
                'keywords': ['launch', 'release', 'announce', 'unveil', 
                            'introduce', 'debut', 'new product'],
                'impact_weight': 0.7,
                'category': 'PRODUCT'
            },
            'legal_issues': {
                'keywords': ['lawsuit', 'investigation', 'probe', 'fraud', 
                            'violation', 'fine', 'penalty', 'settlement'],
                'impact_weight': 0.85,
                'category': 'LEGAL'
            },
            'executive_changes': {
                'keywords': ['ceo', 'cfo', 'resign', 'appoint', 'departure', 
                            'hire', 'executive', 'management change'],
                'impact_weight': 0.6,
                'category': 'MANAGEMENT'
            },
            'analyst_action': {
                'keywords': ['upgrade', 'downgrade', 'rating', 'price target', 
                            'analyst', 'initiate coverage'],
                'impact_weight': 0.5,
                'category': 'ANALYST'
            }
        }
        
        detected_catalysts = []
        recent_signals = sorted(news_signals, key=lambda x: x.timestamp, reverse=True)[:20]
        
        for signal in recent_signals:
            title = (signal.metadata.get('title') or '').lower()
            content_preview = (signal.metadata.get('content') or '')[:200].lower()
            text = title + ' ' + content_preview
            
            for catalyst_type, config in catalyst_patterns.items():
                matches = sum(1 for kw in config['keywords'] if kw in text)
                
                if matches >= 1:
                    confidence = min(matches / 3, 1.0)
                    catalyst_sentiment = signal.score
                    impact_score = config['impact_weight'] * confidence * abs(catalyst_sentiment)
                    
                    detected_catalysts.append({
                        'type': catalyst_type,
                        'category': config['category'],
                        'timestamp': signal.timestamp,
                        'confidence': round(confidence, 3),
                        'sentiment': round(catalyst_sentiment, 3),
                        'impact_score': round(impact_score, 3),
                        'title': signal.metadata.get('title', 'N/A'),
                        'matches': matches
                    })
        
        unique_catalysts = {}
        for cat in detected_catalysts:
            key = cat['type']
            if key not in unique_catalysts or cat['impact_score'] > unique_catalysts[key]['impact_score']:
                unique_catalysts[key] = cat
        
        final_catalysts = list(unique_catalysts.values())
        final_catalysts.sort(key=lambda x: x['impact_score'], reverse=True)
        
        if not final_catalysts:
            impact_assessment = 'NO_CATALYSTS'
            recommendation = "Pas de catalyseurs majeurs détectés. Trading technique/sentiment standard."
        else:
            max_impact = max(c['impact_score'] for c in final_catalysts)
            avg_sentiment = np.mean([c['sentiment'] for c in final_catalysts])
            
            if max_impact > 0.7:
                impact_assessment = 'HIGH_IMPACT'
                recommendation = f"⚡ CATALYSEUR MAJEUR détecté. Attendre clarification post-événement. Volatilité élevée attendue."
            elif max_impact > 0.4:
                impact_assessment = 'MODERATE_IMPACT'
                recommendation = f"📊 Catalyseurs modérés en jeu. Ajuster positions selon développements."
            else:
                impact_assessment = 'LOW_IMPACT'
                recommendation = f"✓ Catalyseurs mineurs. Impact limité sur tendance globale."
            
            if avg_sentiment > 0.3:
                recommendation += " | Biais POSITIF des catalyseurs."
            elif avg_sentiment < -0.3:
                recommendation += " | Biais NÉGATIF des catalyseurs."
        
        most_recent = final_catalysts[0] if final_catalysts else None
        
        return {
            'catalysts_detected': final_catalysts,
            'count': len(final_catalysts),
            'most_recent': most_recent,
            'impact_assessment': impact_assessment,
            'recommendation': recommendation,
            'categories_present': list(set(c['category'] for c in final_catalysts))
        }
    
    # ============================================================================
    # 7. ALERTES INTELLIGENTES
    # ============================================================================
    
    def generate_alerts(self, report: Dict, regime: Dict, catalysts: Dict) -> List[Dict]:
        """🚨 Génère des alertes actionnables basées sur patterns et anomalies"""
        alerts = []
        
        # ALERTE 1: Divergence majeure
        div = report['divergence_analysis']
        if div['opportunity_score'] > 0.5:
            alerts.append({
                'priority': 'HIGH',
                'type': 'DIVERGENCE',
                'icon': '🚨',
                'title': 'DIVERGENCE MAJEURE DÉTECTÉE',
                'message': div['interpretation'],
                'action': self._get_divergence_action(div['type']),
                'urgency': 'IMMEDIATE'
            })
        elif div['opportunity_score'] > 0.3:
            alerts.append({
                'priority': 'MEDIUM',
                'type': 'DIVERGENCE',
                'icon': '⚠️',
                'title': 'Divergence Notable',
                'message': div['interpretation'],
                'action': 'Surveiller évolution dans les 24-48h',
                'urgency': 'MONITOR'
            })
        
        # ALERTE 2: Momentum accéléré
        momentum = report['components']['narrative_momentum']
        if abs(momentum) > 0.5:
            direction = "HAUSSIER ⬆️" if momentum > 0 else "BAISSIER ⬇️"
            alerts.append({
                'priority': 'HIGH',
                'type': 'MOMENTUM',
                'icon': '⚡',
                'title': f'MOMENTUM {direction} ACCÉLÉRÉ',
                'message': f"Changement de sentiment rapide détecté ({momentum:+.3f}). Mouvement en cours.",
                'action': 'Position dans le sens du momentum avec stop-loss serré' if abs(momentum) > 0.7 else 'Attendre confirmation avant entrée',
                'urgency': 'IMMEDIATE' if abs(momentum) > 0.7 else 'SOON'
            })
        
        # ALERTE 3: Smart Money Activity
        smart_money_factor = report.get('smart_money_factor', 0)
        if smart_money_factor > 0.1:
            alerts.append({
                'priority': 'HIGH',
                'type': 'SMART_MONEY',
                'icon': '💰',
                'title': 'SMART MONEY ACTIF',
                'message': f"Détection d'activité institutionnelle (score: {smart_money_factor:.3f}). Open Interest suggère positionnement de gros joueurs.",
                'action': 'Analyser leurs positions. Ils ont souvent raison à moyen terme.',
                'urgency': 'MONITOR'
            })
        
        # ALERTE 4: Régime de volatilité extrême
        if regime['regime'] in ['HIGH_VOLATILITY', 'LOW_VOLATILITY']:
            if regime['regime'] == 'HIGH_VOLATILITY':
                alerts.append({
                    'priority': 'HIGH',
                    'type': 'VOLATILITY',
                    'icon': '🌪️',
                    'title': 'RÉGIME DE HAUTE VOLATILITÉ',
                    'message': regime['implications'],
                    'action': regime['recommendation'],
                    'urgency': 'IMMEDIATE'
                })
            else:
                alerts.append({
                    'priority': 'MEDIUM',
                    'type': 'VOLATILITY',
                    'icon': '😴',
                    'title': 'Complacence du Marché',
                    'message': regime['implications'],
                    'action': regime['recommendation'],
                    'urgency': 'MONITOR'
                })
        
        # ALERTE 5: Catalyseur majeur
        if catalysts['impact_assessment'] in ['HIGH_IMPACT', 'MODERATE_IMPACT']:
            most_recent = catalysts['most_recent']
            if most_recent:
                priority = 'HIGH' if catalysts['impact_assessment'] == 'HIGH_IMPACT' else 'MEDIUM'
                alerts.append({
                    'priority': priority,
                    'type': 'CATALYST',
                    'icon': '🎯',
                    'title': f"Catalyseur: {most_recent['type'].replace('_', ' ').title()}",
                    'message': f"{most_recent['title'][:80]}... (Impact: {most_recent['impact_score']:.2f})",
                    'action': catalysts['recommendation'],
                    'urgency': 'IMMEDIATE' if priority == 'HIGH' else 'SOON'
                })
        
        # ALERTE 6: Conviction extrême
        conviction = report['conviction_score']
        final_score = report['final_sentiment_score']
        
        if conviction > 0.8 and abs(final_score) > 0.5:
            direction = "ACHAT 🟢" if final_score > 0 else "VENTE 🔴"
            alerts.append({
                'priority': 'HIGH',
                'type': 'CONVICTION',
                'icon': '💪',
                'title': f'CONVICTION ÉLEVÉE - Signal {direction}',
                'message': f"Alignement fort entre nouvelles et options (conviction: {conviction:.1%}). Signal {report['classification']}.",
                'action': f"Setup de haute qualité. Considérer position selon plan de trading.",
                'urgency': 'IMMEDIATE'
            })
        
        # ALERTE 7: Asymétrie Peur/Greed notable
        fear_greed = report['components']['fear_greed_asymmetry']
        if abs(fear_greed) > 0.1:
            if fear_greed < -0.1:
                alerts.append({
                    'priority': 'MEDIUM',
                    'type': 'PSYCHOLOGY',
                    'icon': '😨',
                    'title': 'Asymétrie de Peur Détectée',
                    'message': 'Marché surréagit aux mauvaises nouvelles. Possible capitulation ou opportunité contrarian.',
                    'action': 'Opportunité d\'achat si fondamentaux solides. Attendre stabilisation.',
                    'urgency': 'MONITOR'
                })
            else:
                alerts.append({
                    'priority': 'MEDIUM',
                    'type': 'PSYCHOLOGY',
                    'icon': '🤑',
                    'title': 'Euphorie Détectée',
                    'message': 'Marché surréagit positivement. Possibles attentes trop optimistes.',
                    'action': 'Prudence. Prendre profits partiels si en position.',
                    'urgency': 'MONITOR'
                })
        
        # ALERTE 8: Données de faible qualité
        if report['metadata']['analysis_depth'] == 'SHALLOW':
            alerts.append({
                'priority': 'LOW',
                'type': 'DATA_QUALITY',
                'icon': '⚠️',
                'title': 'Données Limitées',
                'message': f"Seulement {report['metadata']['news_articles_count']} articles analysés. Confiance réduite.",
                'action': 'Attendre plus de données ou croiser avec autres sources.',
                'urgency': 'INFO'
            })
        
        # Trier par priorité
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        alerts.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return alerts
    
    def _get_divergence_action(self, div_type: str) -> str:
        """Actions spécifiques selon type de divergence"""
        actions = {
            'bearish_divergence': "❌ NE PAS ACHETER malgré bonnes nouvelles. Attendre correction ou confirmation par price action.",
            'bullish_divergence': "✅ OPPORTUNITÉ D'ACHAT potentielle. Smart money accumule malgré sentiment négatif. Entrer graduellement.",
            'weak_divergence': "⏸️ Signal mixte. Attendre clarification. Pas d'action pour le moment.",
            'aligned': "✓ Pas d'action spéciale. Suivre analyse sentiment standard."
        }
        return actions.get(div_type, "Surveiller évolution.")
    
    # ============================================================================
    # 8. CONFIGURATION PAR TICKER AVEC LLM
    # ============================================================================
    
    def generate_ticker_config_with_llm(self, ticker: str) -> Dict:
        """🤖 Utilise Llama3 via Ollama pour analyser le ticker et proposer une config optimale"""
        
        prompt = f"""Analyse le ticker {ticker} et propose une configuration optimale pour un moteur de sentiment.

Considère:
- La volatilité typique du secteur/compagnie
- La fréquence des nouvelles (tech vs utilities)
- Le volume de trading d'options typique
- Les caractéristiques de sentiment (meme stock vs value)
- La réactivité du prix aux nouvelles

Réponds UNIQUEMENT avec un JSON valide dans ce format exact:
{{
  "temporal_decay_halflife": <nombre entre 1-7 jours>,
  "momentum_window": <nombre entre 3-14 jours>,
  "volatility_penalty": <nombre entre 0.1-0.5>,
  "divergence_threshold": <nombre entre 0.2-0.7>,
  "institutional_premium": <nombre entre 0.1-0.3>,
  "rationale": "<explication courte de 2-3 phrases>"
}}

Exemples de profils:
- TSLA: decay rapide (1-2j), threshold élevé (0.6), très volatile
- KO: decay lent (5-7j), threshold bas (0.3), stable
- NVDA: decay moyen (3j), threshold moyen (0.4), tech volatile"""

        try:
            print(f"🧠 System 2 ({MODEL_LOGIC}) analyse la configuration optimale pour {ticker}...")
            response_text = _ollama_generate(model=MODEL_LOGIC, prompt=prompt, temperature=0.1, timeout=45)
            
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                config = json.loads(json_match.group())
            else:
                config = json.loads(response_text)
            
            config['temporal_decay_halflife'] = np.clip(config.get('temporal_decay_halflife', 3), 1, 7)
            config['momentum_window'] = np.clip(config.get('momentum_window', 7), 3, 14)
            config['volatility_penalty'] = np.clip(config.get('volatility_penalty', 0.3), 0.1, 0.5)
            config['divergence_threshold'] = np.clip(config.get('divergence_threshold', 0.4), 0.2, 0.7)
            config['institutional_premium'] = np.clip(config.get('institutional_premium', 0.2), 0.1, 0.3)
            
            print(f"\n🤖 Configuration LLM pour {ticker}:")
            print(f"   Rationale: {config.get('rationale', 'N/A')}\n")
            
            return config
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la génération de config LLM: {e}")
            print(f"   Utilisation de la configuration par défaut")
            return self._get_default_config()
    
    # ============================================================================
    # 📊 MÉTRIQUES AVANCÉES AVEC LLM
    # ============================================================================
    
    def calculate_advanced_metrics_with_llm(self, news_signals: List[SentimentSignal], 
                                            report: Dict) -> Dict:
        """📈 Calcule des métriques avancées et utilise LLM pour interprétation contextuelle"""
        
        # 1. Sharpe Ratio du Sentiment
        if len(news_signals) > 5:
            sentiment_scores = [s.score * s.confidence for s in news_signals]
            sharpe_ratio = np.mean(sentiment_scores) / (np.std(sentiment_scores) + 1e-6)
        else:
            sharpe_ratio = 0
        
        # 2. Volatilité du Sentiment
        if len(news_signals) > 1:
            sentiment_volatility = np.std([s.score for s in news_signals])
        else:
            sentiment_volatility = 0
        
        # 3. Momentum Acceleration
        momentum_current = report['components'].get('narrative_momentum', 0)
        if len(news_signals) > 10:
            older_signals = news_signals[-10:]
            older_momentum = self.calculate_news_momentum(older_signals)
            momentum_acceleration = momentum_current - older_momentum
        else:
            momentum_acceleration = 0
        
        # 4. Contrarian Opportunity Score
        final_sentiment = report['final_sentiment_score']
        conviction = report['conviction_score']
        
        if abs(final_sentiment) > 0.6 and conviction < 0.5:
            contrarian_score = abs(final_sentiment) * (1 - conviction)
        else:
            contrarian_score = 0
        
        # 5. Sentiment Consistency
        if len(news_signals) > 3:
            recent_scores = [s.score for s in news_signals[-10:]]
            consistency = 1 - (np.std(recent_scores) / (abs(np.mean(recent_scores)) + 1e-6))
            consistency = np.clip(consistency, 0, 1)
        else:
            consistency = 0.5
        
        metrics = {
            'sharpe_ratio': round(sharpe_ratio, 3),
            'sentiment_volatility': round(sentiment_volatility, 3),
            'momentum_acceleration': round(momentum_acceleration, 3),
            'contrarian_score': round(contrarian_score, 3),
            'sentiment_consistency': round(consistency, 3)
        }
        
        interpretation = self._get_llm_metrics_interpretation(metrics, report)
        metrics['llm_interpretation'] = interpretation
        
        return metrics
    
    def generate_strategic_outlook(self, report: Dict) -> str:
        """🔮 Génère une perspective stratégique 'Antigravity' pour les prochains mois"""
        
        prompt = f"""Tu es l'Agent Google Antigravity, un stratège de marché d'élite.
Basé sur l'analyse multi-dimensionnelle suivante pour {self.ticker}, rédige une perspective pour les 3-6 prochains mois.

DONNÉES:
- Sentiment Global: {report['final_sentiment_score']:.2f} ({report['classification']})
- Conviction: {report['conviction_score']:.1%}
- Régime: {report.get('volatility_regime', {}).get('regime', 'N/A')}
- Options P/C Ratio: {report['components']['options_sentiment']:.2f}
- Analyst Consensus: {report['components']['analyst_sentiment']:.2f}

TA MISSION:
1. Donne une prévision claire pour les 3-6 prochains mois (Hausse/Baisse/Action Range).
2. Identifie 1 ou 2 niveaux clés ou catalyseurs à surveiller (Tech ou Fonda).
3. Sois direct, professionnel mais avec une touche "Insiders".

Format: Paragraphe court (3-4 phrases max). Commence par "🔮 **Perspective Antigravity** :"."""
        
        try:
            print(f"🔮 System 2 ({MODEL_LOGIC}) génère la perspective stratégique...")
            outlook = _ollama_generate(model=MODEL_LOGIC, prompt=prompt, temperature=0.7, timeout=60).strip()
            return outlook
        except Exception as e:
            return f"⚠️ Perspective indisponible: {e}"
    
    def _get_llm_metrics_interpretation(self, metrics: Dict, report: Dict) -> str:
        """Utilise Llama3 via Ollama pour interpréter les métriques avancées dans le contexte"""
        
        prompt = f"""Tu es un analyste quantitatif expert. Analyse ces métriques de sentiment pour {self.ticker}:

MÉTRIQUES:
- Sharpe Ratio: {metrics['sharpe_ratio']} (risk-adjusted sentiment)
- Volatilité Sentiment: {metrics['sentiment_volatility']} (0=stable, 1=chaotique)
- Accélération Momentum: {metrics['momentum_acceleration']} (changement de vitesse)
- Score Contrarian: {metrics['contrarian_score']} (0=pas d'opportunité, 1=forte)
- Consistance: {metrics['sentiment_consistency']} (0=incohérent, 1=uniforme)

CONTEXTE:
- Sentiment Final: {report['final_sentiment_score']}
- Classification: {report['classification']}
- Conviction: {report['conviction_score']}

En 2-3 phrases courtes et actionnables, que révèlent ces métriques? Quelle est l'implication pour un trader?

Format: <emoji> <insight clé> | <action recommandée>"""

        try:
            print(f"🗣️ System 1 ({MODEL_NARRATIVE}) rédige l'interprétation...")
            interpretation = _ollama_generate(model=MODEL_NARRATIVE, prompt=prompt, temperature=0.6, timeout=45).strip()
            return interpretation
            
        except Exception as e:
            print(f"⚠️ Erreur LLM pour interprétation métriques: {e}")
            return self._fallback_metrics_interpretation(metrics)
    
    def _fallback_metrics_interpretation(self, metrics: Dict) -> str:
        """Interprétation simple si LLM fail"""
        interpretations = []
        
        if metrics['sharpe_ratio'] > 1.5:
            interpretations.append("📈 Excellent risk/reward")
        elif metrics['sharpe_ratio'] < 0:
            interpretations.append("📉 Sentiment erratique, risque élevé")
        
        if metrics['sentiment_volatility'] > 0.5:
            interpretations.append("⚠️ Forte incertitude")
        
        if metrics['contrarian_score'] > 0.5:
            interpretations.append("🔄 Opportunité contrarian potentielle")
        
        if metrics['sentiment_consistency'] > 0.7:
            interpretations.append("✅ Signal cohérent")
        
        return " | ".join(interpretations) if interpretations else "Métriques standards, pas de signal particulier."
    
    # ============================================================================
    # GÉNÉRATION DU RAPPORT MASTER
    # ============================================================================
    
    def generate_master_sentiment(self) -> Dict:
        """🧠 MOTEUR PRINCIPAL V4: Combine 6 DIMENSIONS pour un score de sentiment ultime"""
        print(f"\n{'='*60}")
        print(f"🔍 ANALYSE MULTI-DIMENSIONNELLE V4 (Dual Brain): {self.ticker}")
        print(f"{'='*60}\n")
        
        # 1. Charger les données (4 dimensions principales)
        news_signals = self.load_news_sentiment(days=100)
        options_signal = self.load_options_sentiment()
        analyst_signal = self.load_analyst_insights()
        financial_signal = self.load_financial_sentiment() # ⬅️ NOUVEAU V5
        
        if not news_signals and not options_signal and not analyst_signal and not financial_signal:
            return {'error': 'Aucune donnée disponible'}
        
        # 2. Calculer les composantes de base
        if news_signals:
            decay_weights = self.calculate_temporal_decay(news_signals)
            weighted_news = [s.score * s.confidence * w 
                           for s, w in zip(news_signals, decay_weights)]
            news_sentiment = np.mean(weighted_news) if weighted_news else 0
            news_confidence = np.mean([s.confidence for s in news_signals])
        else:
            news_sentiment = 0
            news_confidence = 0
        
        options_sentiment = options_signal.score if options_signal else 0
        options_confidence = options_signal.confidence if options_signal else 0
        
        analyst_sentiment = analyst_signal.score if analyst_signal else 0
        analyst_confidence = analyst_signal.confidence if analyst_signal else 0
        
        # ⬅️ NOUVEAU V5: Financials
        financial_sentiment = financial_signal.score if financial_signal else 0
        financial_confidence = financial_signal.confidence if financial_signal else 0
        
        # 🚀 SMART MOMENTUM V6: Multi-dimensional momentum analysis
        momentum_analysis = self.calculate_smart_momentum(news_signals)
        momentum = momentum_analysis['smart_momentum']
        
        divergence = self.detect_divergence(news_sentiment, options_sentiment)
        conviction = self.calculate_conviction_score(news_signals, options_signal)
        fear_greed_factor = self.calculate_fear_greed_asymmetry(news_signals)
        
        # 3. Score final V5 (news 30%, options 30%, analyst 20%, financials 20%)
        news_weight = news_confidence * 0.30
        options_weight = options_confidence * 0.30  # ⬇️ Réduit pour laisser place aux financials
        analyst_weight = analyst_confidence * 0.20
        financial_weight = financial_confidence * 0.20 # ⬅️ NOUVEAU V5
        
        total_weight = news_weight + options_weight + analyst_weight + financial_weight
        if total_weight > 0:
            news_weight /= total_weight
            options_weight /= total_weight
            analyst_weight /= total_weight
            financial_weight /= total_weight
        else:
            # Fallback
            news_weight = 0.30
            options_weight = 0.30
            analyst_weight = 0.20
            financial_weight = 0.20
        
        base_sentiment = (news_sentiment * news_weight + 
                         options_sentiment * options_weight +
                         analyst_sentiment * analyst_weight + 
                         financial_sentiment * financial_weight)
        
        momentum_boost = momentum * 0.15
        divergence_penalty = -divergence['opportunity_score'] * 0.1
        
        final_sentiment = base_sentiment + momentum_boost + divergence_penalty + fear_greed_factor
        final_sentiment = np.clip(final_sentiment, -1, 1)
        
        # 4. Classification
        if final_sentiment > 0.5 and conviction > 0.7:
            classification = 'STRONG_BUY'
            confidence_level = 'HIGH'
        elif final_sentiment > 0.2 and conviction > 0.5:
            classification = 'BUY'
            confidence_level = 'MEDIUM'
        elif final_sentiment < -0.5 and conviction > 0.7:
            classification = 'STRONG_SELL'
            confidence_level = 'HIGH'
        elif final_sentiment < -0.2 and conviction > 0.5:
            classification = 'SELL'
            confidence_level = 'MEDIUM'
        else:
            classification = 'HOLD'
            confidence_level = 'LOW' if conviction < 0.3 else 'MEDIUM'
        
        # 5. Rapport de base
        smart_money_factor = options_signal.metadata.get('smart_money_factor', 0) if options_signal else 0
        
        report = {
            'ticker': self.ticker,
            'timestamp': datetime.now().isoformat(),
            'final_sentiment_score': round(final_sentiment, 4),
            'classification': classification,
            'confidence_level': confidence_level,
            'conviction_score': round(conviction, 4),
            'smart_money_factor': round(smart_money_factor, 4),
            
            'components': {
                'news_sentiment': round(news_sentiment, 4),
                'news_confidence': round(news_confidence, 4),
                'news_weight': round(news_weight, 4),
                'options_sentiment': round(options_sentiment, 4),
                'options_confidence': round(options_confidence, 4),
                'options_weight': round(options_weight, 4),
                'analyst_sentiment': round(analyst_sentiment, 4),
                'analyst_confidence': round(analyst_confidence, 4),
                'analyst_weight': round(analyst_weight, 4),
                'financial_sentiment': round(financial_sentiment, 4), # ⬅️ NOUVEAU V5
                'financial_confidence': round(financial_confidence, 4),
                'financial_weight': round(financial_weight, 4),
                'strategic_bias': 'BULLISH' if base_sentiment > 0 else 'BEARISH',
                'narrative_momentum': round(momentum, 4),
                'smart_momentum': momentum_analysis,  # 🚀 V6: Full breakdown
                'fear_greed_asymmetry': round(fear_greed_factor, 4)
            },
            
            'divergence_analysis': {
                'type': divergence['type'],
                'magnitude': round(divergence['magnitude'], 4),
                'opportunity_score': round(divergence['opportunity_score'], 4),
                'interpretation': divergence['interpretation']
            },
            
            'metadata': {
                'news_articles_count': len(news_signals),
                'options_volume': options_signal.volume if options_signal else 0,
                'analysis_depth': 'DEEP' if len(news_signals) > 50 else 'SHALLOW',
                'config_rationale': self.config_rationale,
                'version': 'V4 - Dual Brain'  # ⬅️ V4
            }
        }
        
        # ⬅️ NOUVEAU V3: Ajouter métadonnées analyst insights
        if analyst_signal:
            report['analyst_insights'] = analyst_signal.metadata
            
        # ⬅️ NOUVEAU V5 (Fix Dashboard): Ajouter options detail
        if options_signal:
            report['options_detail'] = options_signal.metadata
        
        # 6. NOUVELLES ANALYSES V3
        print("\n🆕 ANALYSES AVANCÉES V3:\n")
        
        # ⬅️ NOUVEAU V3: Afficher analyst insights
        if analyst_signal:
            print(f"🎯 Analyst Insights:")
            meta = analyst_signal.metadata
            print(f"   {meta.get('recommendation_summary', 'N/A')}")
            if meta.get('upside_potential'):
                print(f"   Price Target Upside: {meta['upside_potential']:+.1%}")
            print(f"   Upgrades 30d: {meta.get('upgrades_30d', 0)} | Downgrades: {meta.get('downgrades_30d', 0)}")
            print(f"   Score: {analyst_sentiment:+.3f} (confiance: {analyst_confidence:.1%})\n")
        
        # Régime de volatilité
        regime = self.detect_market_regime(options_signal)
        report['volatility_regime'] = regime
        if 'sub_regime' in regime:
            print(f"🌪️ Régime: {regime['regime']} ({regime['sub_regime']})")
        else:
            print(f"🌪️ Régime: {regime['regime']}")
        print(f"   {regime['implications']}")
        print(f"   → {regime.get('recommendation', 'N/A')}\n")
        
        # Catalyseurs
        catalysts = self.detect_catalysts(news_signals)
        report['catalysts'] = catalysts
        print(f"🎯 Catalyseurs: {catalysts['count']} détectés ({catalysts['impact_assessment']})")
        if catalysts['most_recent']:
            print(f"   Plus récent: {catalysts['most_recent']['type']} (impact: {catalysts['most_recent']['impact_score']:.2f})")
        print(f"   → {catalysts['recommendation']}\n")
        
        # Métriques avancées avec LLM
        advanced_metrics = self.calculate_advanced_metrics_with_llm(news_signals, report)
        report['advanced_metrics'] = advanced_metrics
        print(f"📊 Métriques Avancées:")
        print(f"   Sharpe: {advanced_metrics['sharpe_ratio']:.2f} | Volatilité: {advanced_metrics['sentiment_volatility']:.2f}")
        print(f"   Consistance: {advanced_metrics['sentiment_consistency']:.1%} | Contrarian: {advanced_metrics['contrarian_score']:.2f}")
        print(f"   💡 {advanced_metrics['llm_interpretation']}\n")
        
        # Alertes
        alerts = self.generate_alerts(report, regime, catalysts)
        report['alerts'] = alerts
        print(f"🚨 ALERTES: {len(alerts)} générées\n")
        for alert in alerts[:3]:  # Top 3
            print(f"   {alert['icon']} [{alert['priority']}] {alert['title']}")
            print(f"      → {alert['action']}\n")
        
        # 7. Afficher le résumé
        self._print_report(report)
        
        # 8. Sauvegarder
        self._save_report(report)
        
        return report
    
    def _print_report(self, report: Dict):
        """Affiche un rapport visuel du sentiment"""
        print(f"\n{'='*60}")
        print(f"📊 RAPPORT DE SENTIMENT V4: {self.ticker}")
        print(f"{'='*60}\n")
        
        score = report['final_sentiment_score']
        classification = report['classification']
        confidence = report['confidence_level']
        
        bar_length = 40
        position = int((score + 1) / 2 * bar_length)
        bar = '█' * position + '░' * (bar_length - position)
        
        print(f"🎯 SCORE FINAL: {score:+.4f}")
        print(f"   Bearish {bar} Bullish")
        print(f"   -1.00                  0.00                  +1.00\n")
        
        print(f"📈 CLASSIFICATION: {classification}")
        print(f"🔒 CONFIANCE: {confidence}")
        print(f"💪 CONVICTION: {report['conviction_score']:.2%}\n")
        
        print(f"🔍 COMPOSANTES:")
        comp = report['components']
        print(f"   📰 Nouvelles: {comp['news_sentiment']:+.3f} (poids: {comp['news_weight']:.2%})")
        print(f"   📊 Options:   {comp['options_sentiment']:+.3f} (poids: {comp['options_weight']:.2%})")
        print(f"   🎯 Analysts:  {comp['analyst_sentiment']:+.3f} (poids: {comp['analyst_weight']:.2%})")
        print(f"   💰 Financials:{comp['financial_sentiment']:+.3f} (poids: {comp['financial_weight']:.2%}) ⬅️ V5")
        print(f"   🚀 Momentum:  {comp['narrative_momentum']:+.3f}")
        print(f"   😨 Peur/Greed: {comp['fear_greed_asymmetry']:+.3f}\n")
        
        div = report['divergence_analysis']
        print(f"⚠️ DIVERGENCE:")
        print(f"   Type: {div['type']}")
        print(f"   {div['interpretation']}\n")
        
        print(f"{'='*60}\n")
    
    def _save_report(self, report: Dict):
        """Sauvegarde le rapport"""
        # Create at most one timestamped snapshot per 7-day window.
        max_age_seconds = 7 * 24 * 3600
        now_ts = datetime.now().timestamp()

        # Find existing timestamped snapshots for this ticker (V4)
        import glob
        pattern = os.path.join(OUTPUT_DIR, f"{self.ticker}_sentiment_v4_*.json")
        existing = sorted(glob.glob(pattern))

        create_new_snapshot = True
        if existing:
            # Use filesystem mtime of the newest snapshot
            latest_existing = max(existing, key=os.path.getmtime)
            latest_mtime = os.path.getmtime(latest_existing)
            age = now_ts - latest_mtime
            if age < max_age_seconds:
                create_new_snapshot = False

        if create_new_snapshot:
            filename = f"{self.ticker}_sentiment_v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"💾 Rapport V4 sauvegardé: {filepath}")
        else:
            print(f"ℹ️ Snapshot existant récent trouvé ({os.path.basename(latest_existing)}); pas de nouveau snapshot horodaté créé.")

        # Always update the latest_v4.json pointer
        latest_path = os.path.join(OUTPUT_DIR, f"{self.ticker}_latest_v4.json")
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"💾 Latest V3 mis à jour: {latest_path}")


def main():
    """Analyse de sentiment V3 pour une compagnie (avec Analyst Insights)"""
    if len(sys.argv) < 2:
        print("Usage: python3 advanced_sentiment_engine_v4.py TICKER [--no-llm]")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    use_llm = '--no-llm' not in sys.argv
    
    engine = AdvancedSentimentEngineV4(ticker, use_llm_config=use_llm)
    report = engine.generate_master_sentiment()


if __name__ == "__main__":
    main()
