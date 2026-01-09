import yfinance as yf
import pandas as pd

# Liste de tickers canadiens à tester
CANADIAN_TICKERS = [
    "SHOP.TO",  # Shopify
    "RY.TO",    # Royal Bank
    "TD.TO",    # TD Bank
    "ENB.TO",   # Enbridge
    "CNR.TO",   # Canadian National Railway
    "BMO.TO",   # Bank of Montreal
]

print("🧪 Test systématique des tickers canadiens\n")
print("=" * 80)

results = []

for ticker in CANADIAN_TICKERS:
    print(f"\n📊 Test de {ticker}")
    print("-" * 40)
    
    # Test avec suffixe .TO
    stock_ca = yf.Ticker(ticker)
    try:
        expirations_ca = stock_ca.options
        n_ca = len(expirations_ca)
        print(f"   {ticker}: {n_ca} dates d'expiration")
    except Exception as e:
        n_ca = 0
        print(f"   {ticker}: ❌ Erreur ({e})")
    
    # Test sans suffixe (ticker US)
    ticker_us = ticker.replace('.TO', '')
    stock_us = yf.Ticker(ticker_us)
    try:
        expirations_us = stock_us.options
        n_us = len(expirations_us)
        print(f"   {ticker_us}: {n_us} dates d'expiration")
        if n_us > 0:
            print(f"      Exemple: {expirations_us[0]}")
    except Exception as e:
        n_us = 0
        print(f"   {ticker_us}: ❌ Erreur ({e})")
    
    results.append({
        'ticker_ca': ticker,
        'options_ca': n_ca,
        'ticker_us': ticker_us,
        'options_us': n_us,
        'use_us': n_us > n_ca
    })

print("\n" + "=" * 80)
print("\n📋 RÉSUMÉ DES RÉSULTATS\n")

df = pd.DataFrame(results)
print(df.to_string(index=False))

print("\n🎯 CONCLUSION:")
dual_listed = df[df['use_us'] == True]
if len(dual_listed) > 0:
    print(f"   {len(dual_listed)}/{len(df)} tickers ont plus d'options sur le ticker US")
    print(f"   Tickers concernés: {', '.join(dual_listed['ticker_ca'].tolist())}")
else:
    print("   Aucun pattern détecté - les tickers .TO fonctionnent correctement")
