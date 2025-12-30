#!/usr/bin/env python3
"""
Worker wrapper to collect options for a single ticker.
Usage: python3 collect_options_worker.py TICKER
"""
import sys
import os

sys.path.insert(0, '/data/scripts')

try:
    from collect_options import OptionsCollector
except Exception as e:
    print('ERROR importing collect_options:', e)
    raise


def main():
    if len(sys.argv) < 2:
        print('Usage: collect_options_worker.py TICKER')
        sys.exit(2)

    ticker = sys.argv[1].upper()

    # Ensure logs/output directories exist
    os.makedirs('/data/scripts/logs', exist_ok=True)
    os.makedirs('/data/options_data', exist_ok=True)

    collector = OptionsCollector()
    try:
        result = collector.get_options_data(ticker)
        if result:
            print(f'OK: options collected for {ticker}')
        else:
            print(f'NO DATA: {ticker}')
    except Exception as e:
        print(f'ERROR collecting options for {ticker}:', str(e))


if __name__ == '__main__':
    main()
