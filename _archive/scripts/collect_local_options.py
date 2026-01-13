#!/usr/bin/env python3
"""
Helper: fetch options for tickers using yfinance and save into ./data/options_data
Usage: python scripts/collect_local_options.py AAPL MSFT
"""
import sys
import os
from datetime import datetime, timedelta
import time
import pandas as pd
import yfinance as yf

OUTPUT_DIR = os.path.join(os.getcwd(), 'data', 'options_data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def collect_ticker(ticker, days_forward=90):
    print(f"Collecting options for {ticker}")
    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options
        if not expirations:
            print(f"No expirations for {ticker}")
            return
        cutoff_date = (datetime.now() + timedelta(days=days_forward)).strftime('%Y-%m-%d')
        valid_exp = [exp for exp in expirations if exp <= cutoff_date]
        all_calls = []
        all_puts = []
        for exp in valid_exp:
            try:
                opt = stock.option_chain(exp)
                calls = opt.calls.copy()
                puts = opt.puts.copy()
                calls['expiration'] = exp
                puts['expiration'] = exp
                calls['ticker'] = ticker
                puts['ticker'] = ticker
                all_calls.append(calls)
                all_puts.append(puts)
                time.sleep(0.25)
            except Exception as e:
                print(f"  warning: {e}")
                continue
        if all_calls:
            calls_df = pd.concat(all_calls, ignore_index=True)
        else:
            calls_df = pd.DataFrame()
        if all_puts:
            puts_df = pd.concat(all_puts, ignore_index=True)
        else:
            puts_df = pd.DataFrame()
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        if not calls_df.empty:
            calls_df.to_csv(os.path.join(OUTPUT_DIR, f"{ticker}_calls_{ts}.csv"), index=False)
        if not puts_df.empty:
            puts_df.to_csv(os.path.join(OUTPUT_DIR, f"{ticker}_puts_{ts}.csv"), index=False)
        metrics = {
            'ticker': ticker,
            'calls': len(calls_df),
            'puts': len(puts_df)
        }
        print(f"Saved: {metrics}")
    except Exception as e:
        print(f"Error collecting {ticker}: {e}")

if __name__ == '__main__':
    tickers = sys.argv[1:] or ['AAPL']
    for t in tickers:
        collect_ticker(t)
