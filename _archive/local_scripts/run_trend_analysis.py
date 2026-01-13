#!/usr/bin/env python3
"""
Script pour tester diff??rents param??tres de d??tection de shift
"""
import sys
sys.path.insert(0, '/data/scripts')

from trend_detection import TrendDetector, analyze_company_trend
import json

def test_with_params(ticker, threshold=1.5, window=14, min_articles=2):
    """Teste avec param??tres ajustables"""
    file_path = f'/data/files/companies/{ticker}_news.json'
    
    with open(file_path, 'r') as f:
        data = json.load(f)
        articles = data.get('articles', data)
    
    detector = TrendDetector(
        articles,
        outlier_threshold=threshold,
        shift_window_days=window,
        shift_min_articles=min_articles,
        lookback_days=60
    )
    
    return detector.analyze()

if __name__ == '__main__':
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'AMD'
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5
    window = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    min_art = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    
    print(f"Analyse {ticker} - Seuil: {threshold}??, Fen??tre: {window}j, Min: {min_art} articles")
    print("=" * 80)
    
    result = test_with_params(ticker, threshold, window, min_art)
    
    if 'error' in result:
        print(f"ERREUR: {result['error']}")
    else:
        trend = result['trend_line']
        stats = result['stats']
        
        print(f"\nTendance: {trend.slope:+.2f} pts/jour (R??={trend.r_squared:.3f})")
        print(f"Sentiment moyen: {stats['mean_sentiment']:.1f} ?? {trend.std_dev:.1f}")
        print(f"Outliers: {stats['outlier_count']} ({stats['outlier_pct']:.1f}%)")
        
        if result['outliers']:
            print(f"\nTop 5 Outliers:")
            for i, o in enumerate(result['outliers'][:5], 1):
                icon = "????" if o.direction == 'positive' else "????"
                recent = "????" if o.is_recent else ""
                print(f"  {i}. [{o.outlier_weight:.2f}??] {icon}{recent} {o.article['title'][:60]}")
        
        if result['shift']:
            s = result['shift']
            print(f"\n??????  SHIFT D??TECT??: {s['interpretation']}")
            print(f"    Force: {s['strength']:.2f}?? | Confiance: {s['confidence']*100:.0f}%")
            print(f"    Articles: {s['outlier_count']}")
        else:
            print("\n??? Pattern stable")
