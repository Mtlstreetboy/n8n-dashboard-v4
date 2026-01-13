#!/usr/bin/env python3
"""
Analyse avec paramètres optimisés pour détecter les shifts
"""
import sys
sys.path.insert(0, '/data/scripts')

from trend_detection import TrendDetector
import json
import os

def analyze_with_adjusted_params(ticker, data_path='/data/files/companies'):
    """
    Analyse avec paramètres adaptés:
    - Seuil: 1.2σ (plus sensible)
    - Fenêtre shift: 14 jours
    - Min articles: 2
    - Lookback: 60 jours
    """
    file_path = f"{data_path}/{ticker}_news.json"
    
    with open(file_path, 'r') as f:
        data = json.load(f)
        articles = data.get('articles', data)
    
    detector = TrendDetector(
        articles,
        outlier_threshold=1.2,  # Plus sensible
        shift_window_days=14,    # Fenêtre plus large
        shift_min_articles=2,    # Minimum 2 outliers
        lookback_days=60
    )
    
    return detector.analyze()

if __name__ == '__main__':
    print("=" * 90)
    print("ANALYSE COMPLETE - Parametres optimises (1.2sigma, 14j, min 2)")
    print("=" * 90)
    
    data_path = '/data/files/companies'
    files = sorted([f for f in os.listdir(data_path) if f.endswith('_news.json')])
    
    all_results = {}
    shifts_detected = []
    
    for file in files:
        ticker = file.replace('_news.json', '')
        
        try:
            result = analyze_with_adjusted_params(ticker)
            all_results[ticker] = result
            
            if 'error' not in result:
                trend = result['trend_line']
                stats = result['stats']
                shift = result.get('shift')
                
                # Icones
                shift_icon = "[!]" if shift else "   "
                trend_icon = "[UP]" if trend.slope > 1 else "[DN]" if trend.slope < -1 else "[->]"
                
                # Affichage
                print(f"{shift_icon}{trend_icon} {ticker:10} | " +
                      f"Pente: {trend.slope:+6.2f}/j | " +
                      f"Outliers: {stats['outlier_count']:2} | " +
                      f"Sentiment: {stats['mean_sentiment']:+6.1f} +/- {trend.std_dev:5.1f} | " +
                      f"R2: {trend.r_squared:.3f}")
                
                if shift:
                    shifts_detected.append((ticker, shift))
                    print(f"             └-> SHIFT {shift['direction'].upper()}: " +
                          f"{shift['strength']:.1f}sigma ({shift['confidence']*100:.0f}% confiance) - " +
                          f"{shift['outlier_count']} articles")
            else:
                print(f"    {ticker:10} | Pas assez de donnees")
        
        except Exception as e:
            print(f"    {ticker:10} | ERREUR: {str(e)[:60]}")
    
    # Resume final
    print("\n" + "=" * 90)
    print(f"RESUME: {len(shifts_detected)} SHIFT(S) DETECTE(S)")
    print("=" * 90)
    
    if shifts_detected:
        for ticker, shift in shifts_detected:
            print(f"\n{ticker} -> {shift['interpretation']}")
            print(f"  Force: {shift['strength']:.2f}sigma | Confiance: {shift['confidence']*100:.0f}%")
            print(f"  Articles concernes:")
            for title in shift['articles'][:3]:
                print(f"    * {title[:80]}")
    else:
        print("\nAucun shift majeur detecte sur les 60 derniers jours.")
        print("Les patterns de sentiment sont relativement stables.")
    
    # Compagnies avec plus forte tendance
    print("\n" + "=" * 90)
    print("TOP TENDANCES (|pente| > 2)")
    print("=" * 90)
    
    trends = [(t, r['trend_line'].slope, r['stats']['mean_sentiment']) 
              for t, r in all_results.items() 
              if 'trend_line' in r and abs(r['trend_line'].slope) > 2]
    
    if trends:
        trends.sort(key=lambda x: abs(x[1]), reverse=True)
        for ticker, slope, sentiment in trends[:5]:
            direction = "Hausse" if slope > 0 else "Baisse"
            print(f"  {ticker:10} {direction:8} {slope:+6.2f} pts/jour (sentiment actuel: {sentiment:+.1f})")
