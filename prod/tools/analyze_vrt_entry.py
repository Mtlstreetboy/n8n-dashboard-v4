import yfinance as yf

# Fetch data for VRT from late 2025 to now
vrt = yf.download("VRT", start="2025-10-01", progress=False)['Close']

print("--- VRT Price Context ---")
print(f"Current Price: {vrt.iloc[-1]:.2f}")
print(f"Min since Oct 2025: {vrt.min():.2f}")
print(f"Max since Oct 2025: {vrt.max():.2f}")

# Check when price was around 162
around_162 = vrt[(vrt >= 160) & (vrt <= 165)]
print("\nDates where price was ~162$:")
print(around_162.tail(10))
