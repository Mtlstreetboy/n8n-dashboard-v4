#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Financial Data Collection - yfinance
Collecte prix, volume, et metriques d'options pour les compagnies AI
"""

import sys
sys.path.insert(0, '/data/scripts')

import yfinance as yf
import json
import os
from datetime import datetime, timedelta
from companies_config import get_all_companies

FINANCIALS_DIR = "/data/files/financials"

def ensure_directory():
    """Cree le dossier financials s'il n'existe pas"""
    os.makedirs(FINANCIALS_DIR, exist_ok=True)

def collect_company_financials(ticker: str, company_name: str):
    """
    Collecte les donnees financieres pour une compagnie
    
    Returns:
    - dict avec prix, volume, options metrics, historique 30j
    """
    
    print(f"  Fetching data for {ticker}...")
    
    stock = yf.Ticker(ticker)
    
    # 1. Prix + Volume (30 derniers jours)
    try:
        hist = stock.history(period="1mo")
        if hist.empty:
            print(f"  [!] No historical data for {ticker}")
            return None
    except Exception as e:
        print(f"  [X] Error fetching history for {ticker}: {e}")
        return None
    
    # 2. Options metrics (prochaine expiration)
    calls_volume = None
    puts_volume = None
    put_call_ratio = None
    avg_iv = None
    next_exp = None
    
    try:
        exp_dates = stock.options
        if exp_dates and len(exp_dates) > 0:
            next_exp = exp_dates[0]  # Prochaine expiration
            options = stock.option_chain(next_exp)
            
            # Volume total calls/puts
            calls_volume = int(options.calls['volume'].sum()) if 'volume' in options.calls else 0
            puts_volume = int(options.puts['volume'].sum()) if 'volume' in options.puts else 0
            
            # Put/Call Ratio
            if calls_volume > 0:
                put_call_ratio = round(puts_volume / calls_volume, 3)
            
            # Implied Volatility moyenne (calls seulement)
            if 'impliedVolatility' in options.calls.columns:
                avg_iv = round(float(options.calls['impliedVolatility'].mean()), 4)
                
            print(f"    Options: P/C={put_call_ratio}, IV={avg_iv}")
    except Exception as e:
        print(f"    [!] Options data unavailable for {ticker}: {e}")
    
    # 3. Structure de donnees
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Dernieres valeurs (jour le plus recent)
    last_row = hist.iloc[-1]
    
    financial_data = {
        'ticker': ticker,
        'company_name': company_name,
        'last_updated': datetime.now().isoformat(),
        'daily_data': {
            'date': today,
            'close': round(float(last_row['Close']), 2),
            'volume': int(last_row['Volume']),
            'high': round(float(last_row['High']), 2),
            'low': round(float(last_row['Low']), 2),
            'open': round(float(last_row['Open']), 2)
        },
        'options_metrics': {
            'put_call_ratio': put_call_ratio,
            'calls_volume': calls_volume,
            'puts_volume': puts_volume,
            'implied_volatility_avg': avg_iv,
            'next_expiration': next_exp
        },
        'historical_30d': []
    }
    
    # Historique 30 jours
    for date, row in hist.iterrows():
        financial_data['historical_30d'].append({
            'date': date.strftime('%Y-%m-%d'),
            'close': round(float(row['Close']), 2),
            'volume': int(row['Volume']),
            'high': round(float(row['High']), 2),
            'low': round(float(row['Low']), 2)
        })
    
    print(f"    [OK] Price: ${financial_data['daily_data']['close']}, Vol: {financial_data['daily_data']['volume']:,}")
    
    return financial_data


def save_financial_data(ticker: str, data: dict):
    """Sauvegarde les donnees financieres dans un fichier JSON"""
    filepath = os.path.join(FINANCIALS_DIR, f"{ticker}_market.json")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"    [SAVED] {filepath}")


def collect_all_companies():
    """
    Collecte les donnees financieres pour toutes les compagnies AI
    """
    
    ensure_directory()
    
    companies = get_all_companies()
    
    print("=" * 80)
    print(f"FINANCIAL DATA COLLECTION - {len(companies)} companies")
    print(f"Source: Yahoo Finance (yfinance)")
    print("=" * 80)
    
    success_count = 0
    error_count = 0
    
    for company in companies:
        ticker = company['ticker']
        company_name = company['name']
        
        print(f"\n[{ticker}] {company_name}")
        
        try:
            data = collect_company_financials(ticker, company_name)
            
            if data:
                save_financial_data(ticker, data)
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            print(f"  [X] Fatal error for {ticker}: {e}")
            error_count += 1
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {success_count} success, {error_count} errors")
    print("=" * 80)


def test_single_company(ticker: str = "NVDA"):
    """
    Test rapide sur une seule compagnie
    """
    ensure_directory()
    
    print(f"Testing yfinance with {ticker}...")
    
    try:
        data = collect_company_financials(ticker, "NVIDIA Corporation")
        
        if data:
            save_financial_data(ticker, data)
            print("\n[SUCCESS] Test completed!")
            print(f"\nData preview:")
            print(f"  Price: ${data['daily_data']['close']}")
            print(f"  Volume: {data['daily_data']['volume']:,}")
            print(f"  Put/Call Ratio: {data['options_metrics']['put_call_ratio']}")
            print(f"  Historical days: {len(data['historical_30d'])}")
        else:
            print("\n[FAILED] No data returned")
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Mode test: une seule compagnie
        test_single_company()
    else:
        # Mode production: toutes les compagnies
        collect_all_companies()
