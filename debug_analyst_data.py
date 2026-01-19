import yfinance as yf
import pandas as pd

ticker = "GOOGL"
t = yf.Ticker(ticker)

print(f"--- FETCHING DATA FOR {ticker} ---")

print("\n[1] t.recommendations:")
try:
    recs = t.recommendations
    if recs is not None and not recs.empty:
        print(recs.tail(10))
        print("\nColumns:", recs.columns)
    else:
        print("Empty or None")
except Exception as e:
    print(f"Error: {e}")

print("\n[2] t.upgrades_downgrades:")
try:
    ud = t.upgrades_downgrades
    if ud is not None and not ud.empty:
        print(ud.tail(10))
        print("\nColumns:", ud.columns)
    else:
        print("Empty or None")
except Exception as e:
    print(f"Error: {e}")

print("\n[3] t.recommendations_summary:")
try:
    rs = t.recommendations_summary
    if rs is not None and not rs.empty:
        print(rs)
    else:
        print("Empty or None")
except Exception as e:
    print(f"Error: {e}")
