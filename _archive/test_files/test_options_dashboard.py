#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
???? SCRIPT DE TEST - Dashboard Options
--------------------------------------------------------------------
Teste les 5 visualisations et v??rifie que les donn??es sont correctes
"""
import sys
import os
sys.path.insert(0, '/data/scripts')

import pandas as pd
import numpy as np
from datetime import datetime

# Import des fonctions du dashboard
from dashboard_options import (
    load_options_data,
    get_current_stock_price,
    calculate_composite_score
)

def test_data_loading():
    """Test 1: Chargement des donn??es"""
    print("\n" + "="*60)
    print("???? TEST 1: Chargement des donn??es")
    print("="*60)
    
    # Lister les tickers disponibles
    options_dir = '/data/options_data'
    tickers = set()
    
    for file in os.listdir(options_dir):
        if file.endswith('_calls_') or '_calls_' in file:
            ticker = file.split('_')[0]
            tickers.add(ticker)
    
    print(f"??? Tickers trouv??s: {', '.join(sorted(tickers))}")
    
    if not tickers:
        print("??? ??CHEC: Aucun ticker trouv??")
        return False
    
    # Tester le chargement pour chaque ticker
    for ticker in sorted(tickers)[:5]:  # Limiter ?? 5 pour le test
        print(f"\n???? Test de {ticker}...")
        
        calls_df, puts_df = load_options_data(ticker)
        
        if calls_df is None or puts_df is None:
            print(f"  ??? {ticker}: Impossible de charger")
            continue
        
        if calls_df.empty or puts_df.empty:
            print(f"  ??????  {ticker}: DataFrames vides")
            continue
        
        print(f"  ??? {ticker}: {len(calls_df)} calls, {len(puts_df)} puts")
        
        # V??rifier les colonnes requises
        required_cols = ['strike', 'volume', 'openInterest', 'lastPrice', 'impliedVolatility', 'expiration']
        
        for col in required_cols:
            if col not in calls_df.columns:
                print(f"  ??? Colonne manquante dans calls: {col}")
                return False
            if col not in puts_df.columns:
                print(f"  ??? Colonne manquante dans puts: {col}")
                return False
        
        print(f"  ??? Toutes les colonnes requises pr??sentes")
    
    return True

def test_price_calculation():
    """Test 2: Calcul du prix actuel"""
    print("\n" + "="*60)
    print("???? TEST 2: Calcul du prix actuel")
    print("="*60)
    
    options_dir = '/data/options_data'
    tickers = set()
    
    for file in os.listdir(options_dir):
        if '_calls_' in file:
            ticker = file.split('_')[0]
            tickers.add(ticker)
    
    for ticker in sorted(tickers)[:3]:
        price = get_current_stock_price(ticker)
        
        if price is None:
            print(f"??? {ticker}: Prix non calculable")
            return False
        
        if price <= 0:
            print(f"??? {ticker}: Prix invalide ({price})")
            return False
        
        print(f"??? {ticker}: Prix estim?? = ${price:.2f}")
    
    return True

def test_composite_score():
    """Test 3: Calcul du score composite"""
    print("\n" + "="*60)
    print("???? TEST 3: Calcul du score composite")
    print("="*60)
    
    options_dir = '/data/options_data'
    tickers = set()
    
    for file in os.listdir(options_dir):
        if '_calls_' in file:
            ticker = file.split('_')[0]
            tickers.add(ticker)
    
    for ticker in sorted(tickers)[:3]:
        calls_df, puts_df = load_options_data(ticker)
        
        if calls_df is None or puts_df is None or calls_df.empty or puts_df.empty:
            print(f"??????  {ticker}: Pas de donn??es")
            continue
        
        current_price = get_current_stock_price(ticker)
        
        if current_price is None:
            print(f"??????  {ticker}: Prix non calculable")
            continue
        
        try:
            scores = calculate_composite_score(calls_df.copy(), puts_df.copy(), current_price)
            
            # V??rifier que tous les scores sont pr??sents
            required_scores = ['volatility_skew', 'max_pain_distance', 'money_flow_ratio', 
                             'volume_concentration', 'composite']
            
            for score_name in required_scores:
                if score_name not in scores:
                    print(f"??? {ticker}: Score manquant: {score_name}")
                    return False
                
                score_val = scores[score_name]
                
                # V??rifier que c'est un nombre
                if not isinstance(score_val, (int, float, np.number)):
                    print(f"??? {ticker}: {score_name} n'est pas un nombre: {type(score_val)}")
                    return False
            
            composite = scores['composite']
            sentiment = "???? Bullish" if composite > 0.15 else "???? Bearish" if composite < -0.15 else "??????  Neutral"
            
            print(f"??? {ticker}:")
            print(f"   - Composite Score: {composite:.3f} ({sentiment})")
            print(f"   - Volatility Skew: {scores['volatility_skew']:.3f}")
            print(f"   - Max Pain Distance: {scores['max_pain_distance']:.2%}")
            print(f"   - Money Flow Ratio: {scores['money_flow_ratio']:.3f}")
            print(f"   - Volume Concentration: {scores['volume_concentration']:.3f}")
            
        except Exception as e:
            print(f"??? {ticker}: Erreur lors du calcul du score: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

def test_data_quality():
    """Test 4: Qualit?? des donn??es"""
    print("\n" + "="*60)
    print("???? TEST 4: Qualit?? des donn??es")
    print("="*60)
    
    options_dir = '/data/options_data'
    tickers = set()
    
    for file in os.listdir(options_dir):
        if '_calls_' in file:
            ticker = file.split('_')[0]
            tickers.add(ticker)
    
    for ticker in sorted(tickers)[:3]:
        calls_df, puts_df = load_options_data(ticker)
        
        if calls_df is None or puts_df is None or calls_df.empty or puts_df.empty:
            print(f"??????  {ticker}: Pas de donn??es")
            continue
        
        print(f"\n???? {ticker}:")
        
        # V??rifier les valeurs nulles
        calls_nulls = calls_df.isnull().sum()
        puts_nulls = puts_df.isnull().sum()
        
        if calls_nulls.sum() > 0:
            print(f"  ??????  Calls avec valeurs nulles:")
            print(f"     {calls_nulls[calls_nulls > 0].to_dict()}")
        else:
            print(f"  ??? Calls: Pas de valeurs nulles")
        
        if puts_nulls.sum() > 0:
            print(f"  ??????  Puts avec valeurs nulles:")
            print(f"     {puts_nulls[puts_nulls > 0].to_dict()}")
        else:
            print(f"  ??? Puts: Pas de valeurs nulles")
        
        # V??rifier les volumes
        calls_zero_vol = (calls_df['volume'] == 0).sum()
        puts_zero_vol = (puts_df['volume'] == 0).sum()
        
        print(f"  ???? Calls avec volume = 0: {calls_zero_vol}/{len(calls_df)} ({calls_zero_vol/len(calls_df)*100:.1f}%)")
        print(f"  ???? Puts avec volume = 0: {puts_zero_vol}/{len(puts_df)} ({puts_zero_vol/len(puts_df)*100:.1f}%)")
        
        # V??rifier les IV
        calls_iv_mean = calls_df['impliedVolatility'].mean()
        puts_iv_mean = puts_df['impliedVolatility'].mean()
        
        print(f"  ???? IV moyenne calls: {calls_iv_mean:.2%}")
        print(f"  ???? IV moyenne puts: {puts_iv_mean:.2%}")
        
        if calls_iv_mean > 2.0 or puts_iv_mean > 2.0:
            print(f"  ??????  IV anormalement ??lev??e (> 200%)")
        else:
            print(f"  ??? IV dans la plage normale")
        
        # V??rifier les strikes
        min_strike = min(calls_df['strike'].min(), puts_df['strike'].min())
        max_strike = max(calls_df['strike'].max(), puts_df['strike'].max())
        
        print(f"  ???? Plage de strikes: ${min_strike:.2f} - ${max_strike:.2f}")
    
    return True

def test_visualization_data():
    """Test 5: Donn??es pour les visualisations"""
    print("\n" + "="*60)
    print("???? TEST 5: Donn??es pour visualisations")
    print("="*60)
    
    options_dir = '/data/options_data'
    tickers = set()
    
    for file in os.listdir(options_dir):
        if '_calls_' in file:
            ticker = file.split('_')[0]
            tickers.add(ticker)
    
    if not tickers:
        print("??? Aucun ticker disponible")
        return False
    
    ticker = sorted(tickers)[0]  # Prendre le premier
    print(f"???? Test avec {ticker}")
    
    calls_df, puts_df = load_options_data(ticker)
    
    if calls_df is None or puts_df is None or calls_df.empty or puts_df.empty:
        print(f"??? Pas de donn??es pour {ticker}")
        return False
    
    # Test 1: Donn??es suffisantes pour Volatility Smile
    calls_with_iv = calls_df[calls_df['impliedVolatility'] > 0]
    puts_with_iv = puts_df[puts_df['impliedVolatility'] > 0]
    
    print(f"\n???? Volatility Smile:")
    print(f"  - Calls avec IV > 0: {len(calls_with_iv)}/{len(calls_df)}")
    print(f"  - Puts avec IV > 0: {len(puts_with_iv)}/{len(puts_df)}")
    
    if len(calls_with_iv) < 10 or len(puts_with_iv) < 10:
        print(f"  ??????  Peu de donn??es pour Volatility Smile")
    else:
        print(f"  ??? Donn??es suffisantes pour Volatility Smile")
    
    # Test 2: Donn??es pour Heatmap
    expirations = calls_df['expiration'].unique()
    
    print(f"\n???? Heatmap:")
    print(f"  - Nombre d'expirations: {len(expirations)}")
    print(f"  - Expirations: {', '.join(sorted(expirations)[:5])}")
    
    if len(expirations) < 3:
        print(f"  ??????  Peu d'expirations pour Heatmap")
    else:
        print(f"  ??? Donn??es suffisantes pour Heatmap")
    
    # Test 3: Donn??es pour Open Interest
    calls_with_oi = calls_df[calls_df['openInterest'] > 0]
    puts_with_oi = puts_df[puts_df['openInterest'] > 0]
    
    print(f"\n???? Open Interest:")
    print(f"  - Calls avec OI > 0: {len(calls_with_oi)}/{len(calls_df)}")
    print(f"  - Puts avec OI > 0: {len(puts_with_oi)}/{len(puts_df)}")
    
    total_call_oi = calls_df['openInterest'].sum()
    total_put_oi = puts_df['openInterest'].sum()
    
    print(f"  - Total Call OI: {total_call_oi:,.0f}")
    print(f"  - Total Put OI: {total_put_oi:,.0f}")
    
    if len(calls_with_oi) < 10 or len(puts_with_oi) < 10:
        print(f"  ??????  Peu de donn??es OI")
    else:
        print(f"  ??? Donn??es suffisantes pour OI Ladder")
    
    # Test 4: Donn??es pour Money Flow
    calls_with_price = calls_df[calls_df['lastPrice'] > 0]
    puts_with_price = puts_df[puts_df['lastPrice'] > 0]
    
    print(f"\n???? Money Flow:")
    print(f"  - Calls avec prix > 0: {len(calls_with_price)}/{len(calls_df)}")
    print(f"  - Puts avec prix > 0: {len(puts_with_price)}/{len(puts_df)}")
    
    if len(calls_with_price) < 10 or len(puts_with_price) < 10:
        print(f"  ??????  Peu de donn??es de prix")
    else:
        print(f"  ??? Donn??es suffisantes pour Money Flow")
    
    # Test 5: Donn??es pour 3D Surface
    print(f"\n???? 3D Surface:")
    print(f"  - Nombre d'expirations: {len(expirations)}")
    print(f"  - Nombre de strikes: {len(calls_df['strike'].unique())}")
    
    if len(expirations) < 3:
        print(f"  ??????  Peu d'expirations pour 3D")
    else:
        print(f"  ??? Donn??es suffisantes pour 3D Surface")
    
    return True

def main():
    """Ex??cute tous les tests"""
    print("="*60)
    print("???? SUITE DE TESTS - Dashboard Options")
    print("="*60)
    
    tests = [
        ("Chargement des donn??es", test_data_loading),
        ("Calcul du prix actuel", test_price_calculation),
        ("Calcul du score composite", test_composite_score),
        ("Qualit?? des donn??es", test_data_quality),
        ("Donn??es pour visualisations", test_visualization_data)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n??? ERREUR dans {test_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Rapport final
    print("\n" + "="*60)
    print("???? R??SULTATS DES TESTS")
    print("="*60)
    
    for test_name, result in results:
        status = "??? PASS" if result else "??? FAIL"
        print(f"{status} - {test_name}")
    
    total_pass = sum(1 for _, r in results if r)
    total_tests = len(results)
    
    print(f"\n???? Score: {total_pass}/{total_tests} tests pass??s ({total_pass/total_tests*100:.0f}%)")
    
    if total_pass == total_tests:
        print("\n???? TOUS LES TESTS SONT PASS??S!")
        return 0
    else:
        print(f"\n??????  {total_tests - total_pass} test(s) ont ??chou??")
        return 1

if __name__ == "__main__":
    exit(main())
