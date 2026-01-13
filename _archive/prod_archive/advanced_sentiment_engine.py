#!/usr/bin/env python3
"""
⚠️⚠️⚠️ MOTEUR DE SENTIMENT MULTI-DIMENSIONNEL INNOVATEUR
--------------------------------------------------------------------
Approche révolutionnaire combinant 5 dimensions avec détection d'anomalies:

1. 📰 Sentiment Textuel (NLP) - Ce que les gens DISENT
2. 📈 Sentiment Options (PCR) - Ce que les traders FONT
3. 🚀 Momentum Narratif - VITESSE du changement de sentiment
4. 💪 Conviction Score - FORCE de l'alignement signal/action
5. ⚠️ Détection d'Anomalies - Divergences & opportunités cachées

Innovations clés:
- Temporal Decay: nouvelles récentes pèsent plus lourd
- Volatility-Adjusted Conviction: ajuste selon la nervosité du marché
- Narrative Momentum: détecte les changements de sentiment avant le marché
- Smart Money Divergence: repère quand institutionnels font le contraire du retail
- Fear/Greed Asymmetry: réaction asymétrique aux bonnes/mauvaises nouvelles

Usage: python3 advanced_sentiment_engine.py AAPL
"""
import sys
sys.path.insert(0, '/data/scripts')

import json
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import math

# Configuration
NEWS_DATA_DIR = '/data/files/companies'
OPTIONS_DATA_DIR = '/data/options_data'
OUTPUT_DIR = '/data/sentiment_analysis'

@dataclass
class SentimentSignal:
    """Signal de sentiment avec métadonnées"""
    timestamp: str
    source: str  # 'news', 'options', 'combined'
    score: float  # -1 à +1
    confidence: float  # 0 à 1
    volume: int  # nombre d'articles ou contrats
    metadata: dict

class AdvancedSentimentEngine:
    def __init__(self, ticker: str):
        self.ticker = ticker
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Paramètres du modèle (optimisables)
        self.params = {
            'temporal_decay_halflife': 3,  # jours
            'momentum_window': 3,  # jours pour momentum (réduit de 7 à 3 car articles très récents)
            'volatility_penalty': 0.3,  # pénalité si IV élevée
            'volume_weight_exp': 0.5,  # exposant pour pondération volume
            'divergence_threshold': 0.4,  # seuil pour détecter divergences
            'institutional_premium': 0.2,  # bonus si options grosses positions
            'fear_greed_threshold': 1.2,  # seuil pour asymétrie (réduit de 1.3 à 1.2)
        }
    
    def load_news_sentiment(self, days=100) -> List[SentimentSignal]:
        """
        Charge et analyse le sentiment des nouvelles avec analyse LLM existante
        """
        news_file = os.path.join(NEWS_DATA_DIR, f'{self.ticker}_news.json')
        
        if not os.path.exists(news_file):
            print(f"⚠️⚠️⚠️  Aucune donnée de nouvelles pour {self.ticker}")
            return []
        
        with open(news_file, 'r') as f:
            data = json.load(f)
        
        # Extraire la liste d'articles du format {"ticker": "X", "articles": [...]}
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
                # Normaliser en offset-aware UTC
                if pub_date.tzinfo is None:
                    from datetime import timezone
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
            except:
                continue
            
            # Normaliser cutoff aussi
            from datetime import timezone
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
            
            if pub_date < cutoff:
                continue
            
            # Utiliser le sentiment LLM si disponible
            llm_data = article.get('llm_sentiment', {})
            if llm_data and 'sentiment_score' in llm_data:
                # Normaliser le score LLM (assume -100 à +100) vers -1 à +1
                raw_score = llm_data.get('sentiment_score', 0)
                sentiment_score = np.clip(raw_score / 100.0, -1, 1)
                confidence = llm_data.get('confidence', 0.7)
            else:
                # Fallback: analyse simple par mots-clés
                sentiment_score, confidence = self._simple_sentiment_analysis(article)
            
            signal = SentimentSignal(
                timestamp=pub_date.isoformat(),
                source='news_llm',
                score=sentiment_score,
                confidence=confidence,
                volume=1,
                metadata={
                    'title': article.get('title', ''),
                    'source': article.get('source', 'Unknown'),
                    'method': 'llm' if 'sentiment_score' in article else 'keyword'
                }
            )
            signals.append(signal)
        
        print(f"📄 {len(signals)} articles avec sentiment détecté")
        return signals
    
    def _simple_sentiment_analysis(self, article: dict) -> Tuple[float, float]:
        """
        Fallback: analyse simple par mots-clés si pas de LLM
        """
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
        
        text = (article.get('title', '') + ' ' + article.get('content', '')).lower()
        
        sentiment_score = 0
        word_count = 0
        
        for word, weight in positive_words.items():
            count = text.count(word)
            sentiment_score += count * weight
            word_count += count
        
        for word, weight in negative_words.items():
            count = text.count(word)
            sentiment_score += count * weight
            word_count += count
        
        if word_count > 0:
            normalized_score = np.tanh(sentiment_score / 10)
            confidence = min(word_count / 5, 1.0)
            return normalized_score, confidence
        
        return 0.0, 0.0
    
    def load_options_sentiment(self) -> SentimentSignal:
        """
        Charge et analyse le sentiment des options avec métriques avancées
        """
        sentiment_file = os.path.join(OPTIONS_DATA_DIR, f'{self.ticker}_latest_sentiment.json')
        
        if not os.path.exists(sentiment_file):
            print(f"⚠️⚠️⚠️  Aucune donnée d'options pour {self.ticker}")
            return None
        
        with open(sentiment_file, 'r') as f:
            metrics = json.load(f)
        
        print(f"📊 Analyse des options...")
        
        # Extraire les métriques clés
        pcr_volume = metrics.get('put_call_ratio_volume', 1.0)
        pcr_oi = metrics.get('put_call_ratio_oi', 1.0)
        call_iv = metrics.get('call_implied_volatility', 0)
        put_iv = metrics.get('put_implied_volatility', 0)
        total_volume = metrics.get('total_contracts', 0)
        call_volume = metrics.get('call_volume', 0)
        put_volume = metrics.get('put_volume', 0)
        
        # 🧮 CALCUL INNOVANT: Score de sentiment multi-facteurs
        
        # 1. Sentiment de base (PCR inversé et normalisé)
        if pcr_volume < 0.7:
            base_sentiment = (0.7 - pcr_volume) / 0.7  # 0 à 1
        elif pcr_volume > 1.3:
            base_sentiment = -(pcr_volume - 1.3) / 1.3  # 0 à -1
        else:
            base_sentiment = -(pcr_volume - 0.7) / 0.6  # -0.5 à 0.5
        
        # 2. Ajustement par la volatilité
        avg_iv = (call_iv + put_iv) / 2
        iv_factor = 1 - (avg_iv * self.params['volatility_penalty'])
        iv_factor = max(0.5, min(1.0, iv_factor))
        
        # 3. Put/Call Skew
        iv_skew = (put_iv - call_iv) / max(call_iv, 0.01)
        skew_adjustment = -np.tanh(iv_skew * 2) * 0.2
        
        # 4. Détection "Smart Money"
        oi_volume_ratio = pcr_oi / max(pcr_volume, 0.01)
        if oi_volume_ratio > 1.2:
            smart_money_factor = (oi_volume_ratio - 1) * self.params['institutional_premium']
            smart_money_factor = min(smart_money_factor, 0.15)
        else:
            smart_money_factor = 0
        
        # 5. Score final combiné
        sentiment_score = base_sentiment * iv_factor + skew_adjustment
        sentiment_score = np.clip(sentiment_score, -1, 1)
        
        # 6. Confiance basée sur le volume
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
        """
        Applique un decay exponentiel: nouvelles récentes pèsent plus lourd
        """
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
    
    def calculate_narrative_momentum(self, signals: List[SentimentSignal]) -> float:
        """
        🧮 INNOVATION: Détecte la VITESSE du changement de sentiment
        """
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
    
    def detect_divergence(self, news_signal: float, options_signal: float) -> Dict:
        """
        🔍 INNOVATION: Détecte les divergences entre ce que les gens DISENT et FONT
        """
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
        """
        🧮 INNOVATION: Score de conviction - mesure la FORCE de l'alignement
        """
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
        """
        😨🤑 INNOVATION: Les marchés réagissent plus aux mauvaises nouvelles qu'aux bonnes
        """
        if not signals:
            return 0
        
        positive_signals = [s for s in signals if s.score > 0]
        negative_signals = [s for s in signals if s.score < 0]
        
        if not positive_signals and not negative_signals:
            return 0
        
        avg_positive = np.mean([s.score for s in positive_signals]) if positive_signals else 0
        avg_negative = np.mean([abs(s.score) for s in negative_signals]) if negative_signals else 0
        
        threshold = self.params.get('fear_greed_threshold', 1.3)
        
        # Calcul progressif de l'asymétrie au lieu de seuils fixes
        if avg_negative > 0.01:
            ratio = avg_negative / max(avg_positive, 0.01)
            if ratio > threshold:
                # Peur domine: retourne valeur négative proportionnelle
                return -np.clip((ratio - 1) * 0.15, -0.25, -0.05)
        
        if avg_positive > 0.01:
            ratio = avg_positive / max(avg_negative, 0.01)
            if ratio > threshold:
                # Greed domine: retourne valeur positive proportionnelle
                return np.clip((ratio - 1) * 0.10, 0.05, 0.20)
        
        return 0
    
    def generate_master_sentiment(self) -> Dict:
        """
        🧠 MOTEUR PRINCIPAL: Combine tout pour un score de sentiment ultime
        """
        print(f"\n{'='*60}")
        print(f"🔍 ANALYSE MULTI-DIMENSIONNELLE: {self.ticker}")
        print(f"{'='*60}\n")
        
        # 1. Charger les données
        news_signals = self.load_news_sentiment(days=100)
        options_signal = self.load_options_sentiment()
        
        if not news_signals and not options_signal:
            return {'error': 'Aucune donnée disponible'}
        
        # 2. Calculer les composantes
        
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
        
        # 3. Momentum narratif
        momentum = self.calculate_narrative_momentum(news_signals)
        
        # 4. Détection de divergence
        divergence = self.detect_divergence(news_sentiment, options_sentiment)
        
        # 5. Score de conviction
        conviction = self.calculate_conviction_score(news_signals, options_signal)
        
        # 6. Asymétrie peur/greed
        fear_greed_factor = self.calculate_fear_greed_asymmetry(news_signals)
        
        # 7. 🧮 SCORE FINAL INNOVANT
        
        news_weight = news_confidence * 0.4
        options_weight = options_confidence * 0.6
        
        total_weight = news_weight + options_weight
        if total_weight > 0:
            news_weight /= total_weight
            options_weight /= total_weight
        else:
            news_weight = options_weight = 0.5
        
        base_sentiment = (news_sentiment * news_weight + 
                         options_sentiment * options_weight)
        
        momentum_boost = momentum * 0.15
        divergence_penalty = -divergence['opportunity_score'] * 0.1
        
        final_sentiment = base_sentiment + momentum_boost + divergence_penalty + fear_greed_factor
        final_sentiment = np.clip(final_sentiment, -1, 1)
        
        # 8. Classification intelligente
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
        
        # 9. Générer le rapport complet
        report = {
            'ticker': self.ticker,
            'timestamp': datetime.now().isoformat(),
            'final_sentiment_score': round(final_sentiment, 4),
            'classification': classification,
            'confidence_level': confidence_level,
            'conviction_score': round(conviction, 4),
            
            'components': {
                'news_sentiment': round(news_sentiment, 4),
                'news_confidence': round(news_confidence, 4),
                'news_weight': round(news_weight, 4),
                'options_sentiment': round(options_sentiment, 4),
                'options_confidence': round(options_confidence, 4),
                'options_weight': round(options_weight, 4),
                'narrative_momentum': round(momentum, 4),
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
                'analysis_depth': 'DEEP' if len(news_signals) > 50 else 'SHALLOW'
            }
        }
        
        # 10. Afficher le résumé
        self._print_report(report)
        
        # 11. Sauvegarder
        self._save_report(report)
        
        return report
    
    def _print_report(self, report: Dict):
        """Affiche un rapport visuel du sentiment"""
        print(f"\n{'='*60}")
        print(f"📊 RAPPORT DE SENTIMENT: {self.ticker}")
        print(f"{'='*60}\n")
        
        score = report['final_sentiment_score']
        classification = report['classification']
        confidence = report['confidence_level']
        
        # Barre visuelle
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
        print(f"   🚀 Momentum:  {comp['narrative_momentum']:+.3f}")
        print(f"   😨 Peur/Greed: {comp['fear_greed_asymmetry']:+.3f}\n")
        
        div = report['divergence_analysis']
        print(f"⚠️ DIVERGENCE:")
        print(f"   Type: {div['type']}")
        print(f"   {div['interpretation']}\n")
        
        print(f"{'='*60}\n")
    
    def _save_report(self, report: Dict):
        """Sauvegarde le rapport"""
        filename = f"{self.ticker}_sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        latest_path = os.path.join(OUTPUT_DIR, f"{self.ticker}_latest.json")
        with open(latest_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"💾 Rapport sauvegardé: {filepath}")


def main():
    """Analyse de sentiment pour une compagnie"""
    if len(sys.argv) < 2:
        print("Usage: python3 advanced_sentiment_engine.py TICKER")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    
    engine = AdvancedSentimentEngine(ticker)
    report = engine.generate_master_sentiment()


if __name__ == "__main__":
    main()
