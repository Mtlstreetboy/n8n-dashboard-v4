
import yfinance as yf
import pandas as pd
import time

print("✅ Bibliothèques chargées. Démarrage du test étendu...")

# Liste des tickers 100% canadiens vs Dual-listed pour tester l'hypothèse
TEST_CASES = [
    ("SHOP.TO", "SHOP"),   # Dual Listed (Tech)
    ("RY.TO", "RY"),       # Dual Listed (Bank)
    ("TD.TO", "TD"),       # Dual Listed (Bank)
    ("CSU.TO", "CSU"),     # TSX Only (Constation) -> CSU aux US est-il valide?
    ("ATD.TO", "ATD")      # TSX Only (Couche-Tard)
]

print(f"\n🧪 Test de {len(TEST_CASES)} paires (Ticker TSX vs Ticker US potentiel)...\n")

results = []

for tsx, us in TEST_CASES:
    print(f"🔍 Analyse {tsx} vs {us}...")
    
    # 1. Test TSX
    try:
        t_tsx = yf.Ticker(tsx)
        opts_tsx = t_tsx.options
        len_tsx = len(opts_tsx)
    except:
        len_tsx = -1
        
    # 2. Test US
    try:
        t_us = yf.Ticker(us)
        opts_us = t_us.options
        len_us = len(opts_us)
        
        # Verify valid US name to avoid false positives (e.g. CSU might be existing US ticker for other company)
        us_name = t_us.info.get('shortName', 'N/A')
    except:
        len_us = -1
        us_name = "Error"
        
    print(f"   🇨🇦 {tsx}: {len_tsx} expirations")
    print(f"   🇺🇸 {us}: {len_us} expirations ({us_name})")
    
    results.append({
        "tsx": tsx,
        "tsx_count": len_tsx,
        "us": us,
        "us_count": len_us,
        "us_name": us_name
    })
    time.sleep(1)

print("\n\n📊 RÉSUMÉ DES RÉSULTATS 📊")
print(f"{'TSX Ticker':<10} | {'Exp (CA)':<8} | {'US Ticker':<10} | {'Exp (US)':<8} | {'US Name'}")
print("-" * 70)
for r in results:
    print(f"{r['tsx']:<10} | {r['tsx_count']:<8} | {r['us']:<10} | {r['us_count']:<8} | {r['us_name']}")
