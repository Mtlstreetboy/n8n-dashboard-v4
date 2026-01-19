import yfinance as yf
import pandas as pd

ticker = "GOOGL"
t = yf.Ticker(ticker)

print(f"--- FETCHING DATA FOR {ticker} ---")
try:
    ud = t.upgrades_downgrades
    if ud is not None and not ud.empty:
        print("\nColumns:", list(ud.columns))
        print("\nFirst 5 rows:")
        print(ud.head(5).to_string())
        
        # Check specifically for the Goldman Sachs event on 2026-01-13 if possible (dates are likely past)
        # Note: 2026 is future, user's machine time is 2026.
    else:
        print("upgrades_downgrades is Empty")
except Exception as e:
    print(f"Error: {e}")
