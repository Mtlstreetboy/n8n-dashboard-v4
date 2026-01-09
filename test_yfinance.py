import yfinance as yf
import json

ticker = "CSU.TO"
print(f"Testing yfinance for {ticker}...")

try:
    stock = yf.Ticker(ticker)
    
    # 1. Check basic info
    print("\n--- Basic Info ---")
    try:
        info = stock.info
        print(f"Name: {info.get('longName')}")
        print(f"Current Price: {info.get('currentPrice')}")
    except Exception as e:
        print(f"Error fetching info: {e}")

    # 2. Check history
    print("\n--- History (5d) ---")
    try:
        hist = stock.history(period="5d")
        print(hist)
    except Exception as e:
        print(f"Error fetching history: {e}")

    # 3. Check options
    print("\n--- Options ---")
    try:
        dates = stock.options
        print(f"Options dates: {dates}")
        if dates:
            print(f"First date chain: {stock.option_chain(dates[0])}")
    except Exception as e:
        print(f"Error fetching options: {e}")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
