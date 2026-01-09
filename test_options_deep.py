import yfinance as yf
import sys

def test_ticker_options(ticker_symbol):
    print(f"\n{'='*50}")
    print(f"Testing Options for: {ticker_symbol}")
    print(f"{'='*50}")
    
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # 1. Force refresh of options dates
        print(f"Attributes options: {stock.options}")
        
        # 2. Try to get chain directly (sometimes .options property is lazy/cached empty)
        try:
            chain = stock.option_chain() # Should get nearest expiration by default
            print(f"SUCCESS! Found chain data immediately.")
            print(f"Calls: {len(chain.calls)}")
            print(f"Puts: {len(chain.puts)}")
        except Exception as e:
            print(f"Direct option_chain() call failed: {e}")

    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    # Test 1: CSU.TO (The problem)
    test_ticker_options("CSU.TO")
    
    # Test 2: SHOP.TO (Control - likely has liquid options)
    test_ticker_options("SHOP.TO")
