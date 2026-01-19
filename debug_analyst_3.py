import yfinance as yf
import pandas as pd

ticker = "GOOGL"
t = yf.Ticker(ticker)

with open("debug_columns.txt", "w") as f:
    try:
        ud = t.upgrades_downgrades
        if ud is not None and not ud.empty:
            f.write(f"Columns: {list(ud.columns)}\n")
            f.write("Sample Row:\n")
            f.write(str(ud.iloc[0].to_dict()) + "\n")
        else:
            f.write("Empty\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
