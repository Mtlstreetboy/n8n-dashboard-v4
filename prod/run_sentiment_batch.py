#!/usr/bin/env python3
"""Run advanced_sentiment_engine_v4 for all public tickers"""
import sys
import os
import subprocess

# Add to path
if os.path.exists('/data/scripts'):
    sys.path.insert(0, '/data/scripts')
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(current_dir, 'prod'))

from config.companies_config import get_public_companies

tickers = [c['ticker'] for c in get_public_companies()]
print(f"🚀 Lancement advanced_sentiment_engine_v4 pour {len(tickers)} tickers\n")

for i, ticker in enumerate(tickers, 1):
    print(f"[{i}/{len(tickers)}] {ticker}...", end=" ", flush=True)
    result = subprocess.run(
        [sys.executable, "analysis/advanced_sentiment_engine_v4.py", ticker],
        capture_output=True,
        text=True,
        cwd="/data/scripts"
    )
    if result.returncode == 0:
        print("✅")
    else:
        print(f"❌")
        if result.stderr:
            print(f"       Error: {result.stderr.split(chr(10))[0][:80]}")

print("\n✅ Tous les tickers traités!")
