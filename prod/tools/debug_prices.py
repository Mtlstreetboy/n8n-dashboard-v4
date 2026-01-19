import yfinance as yf

tickers = ["AMZN", "VRT", "URA", "AIA", "MU", "VOO", "CRWD", "NVDA"]
print("Fetching prices for:", tickers)
data = yf.download(tickers, period="1d", progress=False)['Close']
print(data.iloc[-1])
