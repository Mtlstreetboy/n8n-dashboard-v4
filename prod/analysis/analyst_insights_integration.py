#!/usr/bin/env python3
"""
🎯 INTÉGRATION ANALYST INSIGHTS DE YAHOO FINANCE
--------------------------------------------------
Ajoute une 6ème dimension au moteur de sentiment : le consensus des analystes professionnels

Données extraites :
1. Recommandations (Strong Buy, Buy, Hold, Sell, Strong Sell)
2. Price Targets (moyenne, médiane, high, low)
3. Changements récents (upgrades/downgrades)
4. Tendances des révisions (momentum des analystes)
5. Divergence entre consensus et prix actuel

Installation requise:
pip install yfinance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
from dataclasses import dataclass

@dataclass
class AnalystSignal:
    """Signal de sentiment des analystes avec métadonnées"""
    timestamp: str
    source: str  # 'analyst_recommendation', 'price_target', etc.
    score: float  # -1 à +1
    confidence: float  # 0 à 1
    metadata: dict

class AnalystInsightsIntegration:
    """
    Classe pour charger et analyser les Analyst Insights de Yahoo Finance
    À intégrer dans AdvancedSentimentEngineV3
    """
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.yf_ticker = yf.Ticker(ticker)
    
    def load_analyst_insights(self) -> AnalystSignal:
        """
        📊 NOUVELLE DIMENSION: Charge et analyse le consensus des analystes
        
        Returns:
            AnalystSignal avec score, confiance et métadonnées détaillées
        """
        print(f"📊 Analyse des Analyst Insights...")
        
        try:
            # 1. Récupérer les recommandations
            recommendations = self._get_recommendations()
            
            # 2. Récupérer les price targets
            price_targets = self._get_price_targets()
            
            # 3. Récupérer les révisions récentes
            upgrades_downgrades = self._get_upgrades_downgrades()
            
            # 4. Calculer le score composite
            analyst_score, confidence, metadata = self._calculate_analyst_sentiment(
                recommendations, price_targets, upgrades_downgrades
            )
            
            signal = AnalystSignal(
                timestamp=datetime.now().isoformat(),
                source='analyst_insights',
                score=analyst_score,
                confidence=confidence,
                metadata=metadata
            )
            
            print(f"📊 Sentiment analystes: {analyst_score:.3f} (confiance: {confidence:.2%})")
            print(f"   Recommandations: {metadata.get('recommendation_summary', 'N/A')}")
            upside = metadata.get('upside_potential')
            if upside is not None:
                print(f"   Price Target vs Prix: {upside:+.1%}")
            
            return signal
            
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement des analyst insights: {e}")
            return None
    
    def _get_recommendations(self) -> Dict:
        """
        Extrait les recommandations des analystes
        
        Format Yahoo Finance:
        - strongBuy: nombre d'analystes
        - buy: nombre d'analystes
        - hold: nombre d'analystes
        - sell: nombre d'analystes
        - strongSell: nombre d'analystes
        """
        try:
            info = self.yf_ticker.info
            
            recommendations = {
                'strong_buy': info.get('recommendationKey', '') == 'strong_buy' or 
                              info.get('recommendationMean', 0) <= 1.5,
                'buy': info.get('recommendationKey', '') == 'buy' or 
                       1.5 < info.get('recommendationMean', 0) <= 2.5,
                'hold': info.get('recommendationKey', '') == 'hold' or 
                        2.5 < info.get('recommendationMean', 0) <= 3.5,
                'sell': info.get('recommendationKey', '') == 'sell' or 
                        3.5 < info.get('recommendationMean', 0) <= 4.5,
                'strong_sell': info.get('recommendationKey', '') == 'strong_sell' or 
                               info.get('recommendationMean', 0) > 4.5,
                'mean': info.get('recommendationMean', None),
                'count': info.get('numberOfAnalystOpinions', 0)
            }
            
            # Récupérer l'historique des recommandations si disponible
            try:
                rec_history = self.yf_ticker.recommendations
                if rec_history is not None and not rec_history.empty:
                    # Analyser les 3 derniers mois
                    recent = rec_history[rec_history.index > datetime.now() - timedelta(days=90)]
                    
                    if not recent.empty:
                        # Compter les upgrades vs downgrades
                        if 'To Grade' in recent.columns and 'From Grade' in recent.columns:
                            recommendations['recent_changes'] = len(recent)
                            recommendations['recent_data'] = recent.tail(5).to_dict('records')
            except:
                pass
            
            return recommendations
            
        except Exception as e:
            print(f"⚠️ Erreur recommandations: {e}")
            return {'mean': None, 'count': 0}
    
    def _get_price_targets(self) -> Dict:
        """
        Extrait les price targets des analystes
        
        Returns:
            Dict avec target_mean, target_high, target_low, current_price, upside
        """
        try:
            info = self.yf_ticker.info
            
            target_mean = info.get('targetMeanPrice', None)
            target_high = info.get('targetHighPrice', None)
            target_low = info.get('targetLowPrice', None)
            target_median = info.get('targetMedianPrice', None)
            current_price = info.get('currentPrice', None) or info.get('regularMarketPrice', None)
            
            # Calculer l'upside/downside potentiel
            upside = None
            if target_mean and current_price:
                upside = (target_mean - current_price) / current_price
            
            return {
                'target_mean': target_mean,
                'target_median': target_median,
                'target_high': target_high,
                'target_low': target_low,
                'current_price': current_price,
                'upside': upside,
                'target_range': (target_high - target_low) if (target_high and target_low) else None
            }
            
        except Exception as e:
            print(f"⚠️ Erreur price targets: {e}")
            return {}
    
    def _get_upgrades_downgrades(self) -> Dict:
        """
        Analyse les upgrades/downgrades récents (30 derniers jours)
        
        Returns:
            Dict avec upgrades_count, downgrades_count, net_changes, momentum
        """
        try:
            rec_history = self.yf_ticker.recommendations
            
            if rec_history is None or rec_history.empty:
                return {'upgrades': 0, 'downgrades': 0, 'net': 0}
            
            # Filtrer les 30 derniers jours
            from datetime import timezone
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            
            # Ensure index is datetime
            if not isinstance(rec_history.index, pd.DatetimeIndex):
                # Try to find a date column
                date_cols = [c for c in rec_history.columns if 'date' in c.lower()]
                if date_cols:
                    rec_history = rec_history.set_index(date_cols[0])
                    rec_history.index = pd.to_datetime(rec_history.index, utc=True)
                else:
                    return {'upgrades': 0, 'downgrades': 0, 'net': 0} # Impossible to filter

            # Ensure index is timezone aware for comparison
            if rec_history.index.tz is None:
                rec_history.index = rec_history.index.tz_localize('UTC')
            
            recent = rec_history[rec_history.index > cutoff]
            
            if recent.empty:
                return {'upgrades': 0, 'downgrades': 0, 'net': 0}
            
            # Mapper les grades à des scores numériques
            grade_map = {
                'Strong Buy': 5, 'Buy': 4, 'Outperform': 4,
                'Hold': 3, 'Neutral': 3, 'Market Perform': 3,
                'Underperform': 2, 'Sell': 1, 'Strong Sell': 0
            }
            
            upgrades = 0
            downgrades = 0
            
            for _, row in recent.iterrows():
                from_grade = row.get('From Grade', '')
                to_grade = row.get('To Grade', '')
                
                from_score = grade_map.get(from_grade, 3)
                to_score = grade_map.get(to_grade, 3)
                
                if to_score > from_score:
                    upgrades += 1
                elif to_score < from_score:
                    downgrades += 1
            
            net_changes = upgrades - downgrades
            
            # Calculer le momentum (pondéré par récence)
            momentum = 0
            if len(recent) > 0:
                for i, (_, row) in enumerate(recent.iterrows()):
                    from_grade = row.get('From Grade', '')
                    to_grade = row.get('To Grade', '')
                    
                    from_score = grade_map.get(from_grade, 3)
                    to_score = grade_map.get(to_grade, 3)
                    
                    change = to_score - from_score
                    # Pondération exponentielle (plus récent = plus important)
                    weight = np.exp(-i / len(recent))
                    momentum += change * weight
                
                momentum = momentum / len(recent)
            
            return {
                'upgrades': upgrades,
                'downgrades': downgrades,
                'net': net_changes,
                'momentum': momentum,
                'total_changes': len(recent),
                'recent_changes': recent.tail(3).to_dict('records') if not recent.empty else []
            }
            
        except Exception as e:
            print(f"⚠️ Erreur upgrades/downgrades: {e}")
            return {'upgrades': 0, 'downgrades': 0, 'net': 0}
    
    def _calculate_analyst_sentiment(self, recommendations: Dict, 
                                    price_targets: Dict, 
                                    changes: Dict) -> Tuple[float, float, Dict]:
        """
        🧮 CALCUL INNOVANT: Score de sentiment composite des analystes
        
        Combine 3 facteurs:
        1. Recommandation moyenne (40%)
        2. Price target upside (40%)
        3. Momentum récent (20%)
        
        Returns:
            (score, confidence, metadata)
        """
        
        # ========== FACTEUR 1: Recommandation Moyenne ==========
        rec_mean = recommendations.get('mean')
        rec_count = recommendations.get('count', 0)
        
        if rec_mean is not None:
            # Convertir échelle Yahoo (1=Strong Buy, 5=Strong Sell) vers -1 à +1
            # 1.0 = +1.0 (Strong Buy)
            # 3.0 = 0.0 (Hold)
            # 5.0 = -1.0 (Strong Sell)
            rec_score = (3.0 - rec_mean) / 2.0
            rec_score = np.clip(rec_score, -1, 1)
            
            # Confiance basée sur le nombre d'analystes
            rec_confidence = min(np.log1p(rec_count) / np.log1p(30), 1.0)
        else:
            rec_score = 0
            rec_confidence = 0
        
        # ========== FACTEUR 2: Price Target Upside ==========
        upside = price_targets.get('upside')
        
        if upside is not None:
            # Convertir upside vers -1 à +1
            # +50% upside = +1.0
            # -50% downside = -1.0
            pt_score = np.tanh(upside * 2)  # tanh pour smooth saturation
            
            # Confiance basée sur la dispersion des targets
            target_range = price_targets.get('target_range')
            current_price = price_targets.get('current_price')
            
            if target_range and current_price:
                # Plus le range est étroit, plus la confiance est élevée
                dispersion = target_range / current_price
                pt_confidence = 1.0 - min(dispersion / 0.5, 1.0)  # 50% range = confiance 0
            else:
                pt_confidence = 0.5
        else:
            pt_score = 0
            pt_confidence = 0
        
        # ========== FACTEUR 3: Momentum Récent ==========
        net_changes = changes.get('net', 0)
        total_changes = changes.get('total_changes', 0)
        momentum = changes.get('momentum', 0)
        
        if total_changes > 0:
            # Score basé sur net changes et momentum
            momentum_score = np.tanh(net_changes / 3) * 0.7 + momentum * 0.3
            momentum_score = np.clip(momentum_score, -1, 1)
            
            # Confiance basée sur le nombre de changements
            momentum_confidence = min(total_changes / 5, 1.0)
        else:
            momentum_score = 0
            momentum_confidence = 0
        
        # ========== SCORE FINAL COMPOSITE ==========
        
        # Pondération adaptative selon la disponibilité des données
        weights = {
            'rec': 0.4 * rec_confidence,
            'pt': 0.4 * pt_confidence,
            'momentum': 0.2 * momentum_confidence
        }
        
        total_weight = sum(weights.values())
        
        if total_weight > 0:
            # Normaliser les poids
            for k in weights:
                weights[k] /= total_weight
            
            # Score pondéré
            final_score = (
                rec_score * weights['rec'] +
                pt_score * weights['pt'] +
                momentum_score * weights['momentum']
            )
        else:
            final_score = 0
        
        # Confiance globale
        final_confidence = (rec_confidence + pt_confidence + momentum_confidence) / 3
        
        # ========== MÉTADONNÉES ==========
        
        # Résumé textuel des recommandations
        if rec_mean:
            if rec_mean <= 1.5:
                rec_summary = f"Strong Buy consensus (Mean: {rec_mean:.1f})"
            elif rec_mean <= 2.5:
                rec_summary = f"Buy consensus (Mean: {rec_mean:.1f})"
            elif rec_mean <= 3.5:
                rec_summary = f"Hold consensus (Mean: {rec_mean:.1f})"
            elif rec_mean <= 4.5:
                rec_summary = f"Sell consensus (Mean: {rec_mean:.1f})"
            else:
                rec_summary = f"Strong Sell consensus (Mean: {rec_mean:.1f})"
        else:
            rec_summary = "Insufficient data"
        
        metadata = {
            'recommendation_mean': rec_mean,
            'recommendation_count': rec_count,
            'recommendation_summary': rec_summary,
            'recommendation_score': round(rec_score, 3),
            
            'target_mean': price_targets.get('target_mean'),
            'target_median': price_targets.get('target_median'),
            'current_price': price_targets.get('current_price'),
            'upside_potential': upside,
            'price_target_score': round(pt_score, 3),
            
            'upgrades_30d': changes.get('upgrades', 0),
            'downgrades_30d': changes.get('downgrades', 0),
            'net_changes_30d': changes.get('net', 0),
            'momentum_score': round(momentum_score, 3),
            
            'weights': {k: round(v, 3) for k, v in weights.items()},
            'component_confidences': {
                'recommendation': round(rec_confidence, 3),
                'price_target': round(pt_confidence, 3),
                'momentum': round(momentum_confidence, 3)
            }
        }
        
        return final_score, final_confidence, metadata


# ============================================================================
# EXEMPLE D'UTILISATION STANDALONE
# ============================================================================

def test_analyst_insights(ticker: str):
    """Test standalone de l'intégration Analyst Insights"""
    
    print(f"\n{'='*60}")
    print(f"🎯 TEST ANALYST INSIGHTS: {ticker}")
    print(f"{'='*60}\n")
    
    integration = AnalystInsightsIntegration(ticker)
    signal = integration.load_analyst_insights()
    
    if signal:
        print(f"\n📊 RÉSULTATS:")
        print(f"   Score: {signal.score:+.4f}")
        print(f"   Confiance: {signal.confidence:.2%}\n")
        
        print(f"📋 DÉTAILS:")
        for key, value in signal.metadata.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for k, v in value.items():
                    print(f"      {k}: {v}")
            elif value is not None:
                print(f"   {key}: {value}")
    else:
        print("❌ Impossible de charger les analyst insights")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyst_insights_integration.py TICKER")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    test_analyst_insights(ticker)
