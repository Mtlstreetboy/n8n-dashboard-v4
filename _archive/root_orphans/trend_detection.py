"""
Trend Detection and Pattern Shift Analysis
===========================================

Détecte les changements de pattern dans le sentiment en utilisant :
- Régression linéaire pour établir la tendance baseline
- Variance/écart-type pour quantifier la dispersion normale
- Poids des outliers pour identifier les signaux de changement
- Détection de shift quand plusieurs articles consécutifs dévient

Usage:
    from trend_detection import TrendDetector
    
    detector = TrendDetector(articles)
    results = detector.analyze()
    
    for article in results['outliers']:
        print(f"{article['title']}: {article['outlier_weight']:.2f}σ")
"""

import json
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from dataclasses import dataclass
import pandas as pd


@dataclass
class TrendLine:
    """Représente la droite de tendance d'une compagnie"""
    slope: float  # Pente (changement de sentiment par jour)
    intercept: float  # Ordonnée à l'origine
    r_squared: float  # Coefficient de détermination (qualité du fit)
    std_dev: float  # Écart-type des résidus
    variance: float  # Variance des résidus


@dataclass
class OutlierArticle:
    """Article identifié comme outlier"""
    article: Dict
    residual: float  # Distance à la droite (valeur brute)
    std_residual: float  # Distance normalisée (en nombre d'écarts-types)
    outlier_weight: float  # Poids de l'outlier (|std_residual|)
    direction: str  # 'positive' ou 'negative' (par rapport à la tendance)
    is_recent: bool  # True si dans les 7 derniers jours


class TrendDetector:
    """
    Détecte les changements de pattern dans le sentiment
    
    Méthode :
    1. Calcule la régression linéaire : sentiment = a*t + b
    2. Calcule la variance σ² des résidus
    3. Pour chaque article, calcule le poids : w = |résidu| / σ
    4. Détecte les shifts : plusieurs outliers récents dans même direction
    """
    
    def __init__(
        self,
        articles: List[Dict],
        outlier_threshold: float = 2.0,  # Nombre d'écarts-types pour être outlier
        shift_window_days: int = 7,  # Fenêtre pour détecter un shift
        shift_min_articles: int = 3,  # Nombre min d'outliers pour confirmer shift
        lookback_days: int = 60  # Nombre de jours à analyser (depuis aujourd'hui)
    ):
        """
        Args:
            articles: Liste d'articles avec 'published_at' et 'sentiment_adjusted'
            outlier_threshold: Seuil en σ pour identifier un outlier (défaut: 2σ)
            shift_window_days: Fenêtre temporelle pour analyser les shifts
            shift_min_articles: Nombre minimum d'outliers récents pour confirmer
            lookback_days: Nombre de jours à analyser depuis aujourd'hui (défaut: 60)
        """
        self.articles = articles
        self.outlier_threshold = outlier_threshold
        self.shift_window_days = shift_window_days
        self.shift_min_articles = shift_min_articles
        self.lookback_days = lookback_days
        
        # Résultats de l'analyse
        self.trend_line = None
        self.outliers = []
        self.shift_detected = None
        
    def analyze(self) -> Dict:
        """
        Lance l'analyse complète
        
        Returns:
            Dict avec:
                - trend_line: TrendLine
                - outliers: List[OutlierArticle]
                - shift: Dict ou None (si shift détecté)
                - stats: Statistiques générales
        """
        # Filtre par date (lookback_days)
        now = pd.Timestamp.now(tz='UTC')
        cutoff_date = now - pd.Timedelta(days=self.lookback_days)
        
        recent_articles = [
            a for a in self.articles
            if pd.to_datetime(a.get('published_at')).tz_localize('UTC' if pd.to_datetime(a.get('published_at')).tz is None else None) >= cutoff_date
        ]
        
        # Filtre les articles avec sentiment valide
        valid_articles = [
            a for a in recent_articles
            if 'sentiment_adjusted' in a
            and a.get('sentiment_adjusted') is not None
            and not a.get('llm_sentiment', {}).get('error', False)
        ]
        
        if len(valid_articles) < 10:
            return {
                'error': 'Pas assez d\'articles valides (min: 10)',
                'valid_count': len(valid_articles),
                'total_count': len(self.articles)
            }
        
        # 1. Calcule la régression linéaire
        self.trend_line = self._calculate_trend_line(valid_articles)
        
        # 2. Identifie les outliers
        self.outliers = self._identify_outliers(valid_articles)
        
        # 3. Détecte les shifts
        self.shift_detected = self._detect_shift()
        
        # 4. Statistiques
        stats = self._calculate_stats(valid_articles)
        
        return {
            'trend_line': self.trend_line,
            'outliers': self.outliers,
            'shift': self.shift_detected,
            'stats': stats
        }
    
    def _calculate_trend_line(self, articles: List[Dict]) -> TrendLine:
        """
        Calcule la régression linéaire : sentiment = slope*t + intercept
        
        Retourne aussi la variance σ² des résidus
        """
        # Prépare les données
        data = []
        for article in articles:
            try:
                pub_date = pd.to_datetime(article['published_at'])
                sentiment = article['sentiment_adjusted']
                data.append((pub_date, sentiment))
            except Exception:
                continue
        
        if len(data) < 10:
            raise ValueError("Pas assez de données pour la régression")
        
        # Convertit en arrays numpy
        dates = np.array([d[0] for d in data])
        sentiments = np.array([d[1] for d in data])
        
        # Timestamp en jours depuis le premier article
        min_date = dates.min()
        days = np.array([(d - min_date).total_seconds() / 86400 for d in dates])
        
        # Régression linéaire
        slope, intercept, r_value, p_value, std_err = stats.linregress(days, sentiments)
        
        # Calcule les résidus
        predicted = slope * days + intercept
        residuals = sentiments - predicted
        
        # Variance et écart-type
        variance = np.var(residuals, ddof=1)  # ddof=1 pour variance non biaisée
        std_dev = np.sqrt(variance)
        
        return TrendLine(
            slope=slope,
            intercept=intercept,
            r_squared=r_value**2,
            std_dev=std_dev,
            variance=variance
        )
    
    def _identify_outliers(self, articles: List[Dict]) -> List[OutlierArticle]:
        """
        Identifie les articles qui s'écartent significativement de la tendance
        
        Un article est outlier si : |résidu| > threshold * σ
        """
        outliers = []
        min_date = pd.to_datetime(articles[0]['published_at'])
        now = pd.Timestamp.now(tz='UTC')
        cutoff_date = now - pd.Timedelta(days=self.shift_window_days)
        
        for article in articles:
            try:
                # Date et sentiment
                pub_date = pd.to_datetime(article['published_at'])
                sentiment = article['sentiment_adjusted']
                
                # Position sur l'axe temporel (jours)
                days = (pub_date - min_date).total_seconds() / 86400
                
                # Valeur prédite par la régression
                predicted = self.trend_line.slope * days + self.trend_line.intercept
                
                # Résidu (distance à la droite)
                residual = sentiment - predicted
                
                # Résidu standardisé (en nombre d'écarts-types)
                std_residual = residual / self.trend_line.std_dev if self.trend_line.std_dev > 0 else 0
                
                # Poids de l'outlier
                outlier_weight = abs(std_residual)
                
                # Est-ce un outlier ?
                if outlier_weight >= self.outlier_threshold:
                    outliers.append(OutlierArticle(
                        article=article,
                        residual=residual,
                        std_residual=std_residual,
                        outlier_weight=outlier_weight,
                        direction='positive' if residual > 0 else 'negative',
                        is_recent=pub_date >= cutoff_date
                    ))
            
            except Exception:
                continue
        
        # Trie par poids décroissant
        outliers.sort(key=lambda x: x.outlier_weight, reverse=True)
        
        return outliers
    
    def _detect_shift(self) -> Dict | None:
        """
        Détecte un changement de pattern basé sur les outliers récents
        
        Shift confirmé si :
        - Au moins shift_min_articles outliers récents
        - Majorité (>60%) dans la même direction
        - Poids moyen > 2.5σ
        
        Returns:
            Dict avec infos du shift, ou None si pas de shift
        """
        # Filtre les outliers récents
        recent_outliers = [o for o in self.outliers if o.is_recent]
        
        if len(recent_outliers) < self.shift_min_articles:
            return None
        
        # Compte par direction
        positive_count = sum(1 for o in recent_outliers if o.direction == 'positive')
        negative_count = sum(1 for o in recent_outliers if o.direction == 'negative')
        total = len(recent_outliers)
        
        # Détermine la direction dominante
        dominant_direction = 'positive' if positive_count > negative_count else 'negative'
        dominant_count = max(positive_count, negative_count)
        dominant_pct = dominant_count / total
        
        # Vérifie les conditions du shift
        if dominant_pct < 0.6:
            return None  # Pas de direction claire
        
        # Poids moyen des outliers dominants
        dominant_outliers = [o for o in recent_outliers if o.direction == dominant_direction]
        avg_weight = np.mean([o.outlier_weight for o in dominant_outliers])
        
        if avg_weight < 2.5:
            return None  # Pas assez fort
        
        # Shift confirmé !
        return {
            'detected': True,
            'direction': dominant_direction,
            'strength': avg_weight,
            'outlier_count': len(dominant_outliers),
            'confidence': dominant_pct,
            'articles': [o.article['title'] for o in dominant_outliers[:5]],  # Top 5
            'interpretation': self._interpret_shift(dominant_direction, avg_weight)
        }
    
    def _interpret_shift(self, direction: str, strength: float) -> str:
        """Interprète le shift détecté"""
        if direction == 'positive':
            if strength > 4.0:
                return "Changement MAJEUR vers le positif - Signal très fort"
            elif strength > 3.0:
                return "Changement significatif vers le positif"
            else:
                return "Amélioration du sentiment détectée"
        else:
            if strength > 4.0:
                return "Changement MAJEUR vers le négatif - Signal très fort"
            elif strength > 3.0:
                return "Changement significatif vers le négatif"
            else:
                return "Détérioration du sentiment détectée"
    
    def _calculate_stats(self, articles: List[Dict]) -> Dict:
        """Statistiques générales"""
        sentiments = [a['sentiment_adjusted'] for a in articles]
        
        return {
            'count': len(articles),
            'mean_sentiment': np.mean(sentiments),
            'std_sentiment': np.std(sentiments),
            'min_sentiment': np.min(sentiments),
            'max_sentiment': np.max(sentiments),
            'outlier_count': len(self.outliers),
            'outlier_pct': len(self.outliers) / len(articles) * 100 if articles else 0,
            'trend_strength': abs(self.trend_line.slope) if self.trend_line else 0,
            'trend_quality': self.trend_line.r_squared if self.trend_line else 0
        }


def analyze_company_trend(ticker: str, data_path: str = '/data/files/companies') -> Dict:
    """
    Analyse la tendance d'une compagnie
    
    Args:
        ticker: Code boursier (ex: 'AMD', 'NVDA')
        data_path: Chemin vers les données
    
    Returns:
        Résultats de TrendDetector.analyze()
    """
    # Charge les articles
    file_path = f"{data_path}/{ticker}_news.json"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Gère les deux formats possibles
            if isinstance(data, dict) and 'articles' in data:
                articles = data['articles']
            else:
                articles = data
    except FileNotFoundError:
        return {'error': f'Fichier non trouvé: {file_path}'}
    
    # Lance l'analyse
    detector = TrendDetector(articles)
    return detector.analyze()


def analyze_all_companies(data_path: str = '/data/files/companies') -> Dict[str, Dict]:
    """
    Analyse toutes les compagnies
    
    Returns:
        Dict[ticker] = résultats de l'analyse
    """
    import os
    results = {}
    
    # Liste tous les fichiers JSON
    files = sorted([f for f in os.listdir(data_path) if f.endswith('_news.json')])
    
    for file in files:
        ticker = file.replace('_news.json', '')
        try:
            result = analyze_company_trend(ticker, data_path)
            results[ticker] = result
            
            # Affiche résumé
            if 'error' not in result:
                trend = result['trend_line']
                stats = result['stats']
                shift = result.get('shift')
                
                shift_icon = "[!]" if shift else ""
                print(f"{shift_icon}{ticker:10} | Pente: {trend.slope:+6.2f}/j | Outliers: {stats['outlier_count']:2} | " +
                      f"Sentiment: {stats['mean_sentiment']:+6.1f} | R2: {trend.r_squared:.3f}")
                
                if shift:
                    print(f"           └-> SHIFT {shift['direction'].upper()}: {shift['strength']:.1f}sigma ({shift['confidence']*100:.0f}% confiance)")
            else:
                print(f"{ticker:10} | ERREUR: {result['error']}")
        except Exception as e:
            print(f"{ticker:10} | EXCEPTION: {str(e)}")
            results[ticker] = {'error': str(e)}
    
    return results


if __name__ == '__main__':
    """Test sur AMD et analyse complète"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        print("=" * 80)
        print("TREND DETECTION - Analyse de toutes les compagnies (60 jours)")
        print("=" * 80)
        results = analyze_all_companies()
        
        # Résumé des shifts
        shifts = {k: v for k, v in results.items() if 'shift' in v and v['shift']}
        if shifts:
            print(f"\n{'='*80}")
            print(f"RESUME DES SHIFTS DETECTES: {len(shifts)}")
            print("=" * 80)
            for ticker, result in shifts.items():
                shift = result['shift']
                print(f"\n{ticker} - {shift['interpretation']}")
                print(f"  Force: {shift['strength']:.2f}sigma | Confiance: {shift['confidence']*100:.0f}%")
                print(f"  Articles concernes:")
                for title in shift['articles'][:3]:
                    print(f"    * {title[:75]}")
    else:
        print("=" * 60)
        print("TREND DETECTION - Test AMD (60 jours)")
        print("=" * 60)
        
        # Analyse AMD
        result = analyze_company_trend('AMD')
        
        if 'error' in result:
            print(f"ERREUR: {result['error']}")
        else:
            # Tendance
            trend = result['trend_line']
            print(f"\n[TENDANCE BASELINE]")
            print(f"   Pente: {trend.slope:.2f} points/jour")
            print(f"   R2: {trend.r_squared:.3f} (qualite du fit)")
            print(f"   Ecart-type sigma: {trend.std_dev:.2f}")
            print(f"   Variance sigma2: {trend.variance:.2f}")
            
            # Stats
            stats = result['stats']
            print(f"\n[STATISTIQUES]")
            print(f"   Articles: {stats['count']}")
            print(f"   Sentiment moyen: {stats['mean_sentiment']:.1f}")
            print(f"   Outliers: {stats['outlier_count']} ({stats['outlier_pct']:.1f}%)")
            
            # Outliers
            print(f"\n[TOP OUTLIERS] (>{result['outliers'][0].outlier_weight if result['outliers'] else 2.0:.1f}sigma)")
            for i, outlier in enumerate(result['outliers'][:10], 1):
                article = outlier.article
                direction_icon = "[+]" if outlier.direction == 'positive' else "[-]"
                recent_icon = "[RECENT]" if outlier.is_recent else ""
                print(f"\n   {i}. [{outlier.outlier_weight:.2f}sigma] {direction_icon} {recent_icon}")
                print(f"      {article['title'][:80]}")
                print(f"      Sentiment: {article['sentiment_adjusted']:.1f}")
                print(f"      Residu: {outlier.residual:+.1f}")
            
            # Shift
            if result['shift']:
                shift = result['shift']
                print(f"\n[!] SHIFT DETECTE!")
                print(f"   Direction: {shift['direction'].upper()}")
                print(f"   Force: {shift['strength']:.2f}sigma")
                print(f"   Confiance: {shift['confidence']*100:.0f}%")
                print(f"   Articles: {shift['outlier_count']}")
                print(f"   Interpretation: {shift['interpretation']}")
            else:
                print(f"\n[OK] Pas de shift detecte - Pattern stable")
