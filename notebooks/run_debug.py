
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Config d'affichage
pd.set_option('display.max_rows', 20)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

print("✅ Bibliothèques chargées")

# 1. CONFIGURATION
TICKER = "SHOP.TO"
print(f"🔍 Initialisation de l'objet Ticker pour {TICKER}...")
stock = yf.Ticker(TICKER)

try:
    info = stock.info
    print(f"✅ Ticker reconnu: {info.get('shortName', 'Nom inconnu')} ({info.get('currency', 'Devise inconnue')})")
    print(f"   Prix actuel: {info.get('currentPrice')}")
except Exception as e:
    print(f"⚠️ Attention: Impossible de récupérer les infos de base: {e}")

# 2. EXPIRATIONS
print("⏳ Récupération des dates d'expiration...")
try:
    expirations = stock.options
    if not expirations:
        print("❌ AUCUNE date d'expiration trouvée.")
    else:
        print(f"✅ {len(expirations)} dates trouvées: {expirations}")
except Exception as e:
    print(f"❌ ERREUR GRAVE: {e}")

# 3. ANALYSE PREMIERE DATE
if expirations:
    target_date = expirations[0]
    print(f"🔬 Analyse pour: {target_date}")
    try:
        chain = stock.option_chain(target_date)
        print(f"\\n📞 CALLS: {len(chain.calls)}")
        if not chain.calls.empty:
            print(chain.calls[['contractSymbol', 'lastTradeDate', 'strike', 'lastPrice', 'volume', 'openInterest']].head())
            
        print(f"\\n📉 PUTS: {len(chain.puts)}")
        if not chain.puts.empty:
            print(chain.puts[['contractSymbol', 'lastTradeDate', 'strike', 'lastPrice', 'volume', 'openInterest']].head())
    except Exception as e:
        print(f"❌ Erreur téléchargement chaîne: {e}")

# 5. DIAGNOSTIC VARIANTES
TEST_ALTERNATIVES = [TICKER, TICKER.replace('.TO', '.TRT'), TICKER.split('.')[0]]
print("\\n🧪 Test des variantes...")
for alt in TEST_ALTERNATIVES:
    if alt == TICKER: continue
    print(f"\\n🔄 Test variante: {alt}")
    s = yf.Ticker(alt)
    try:
        exps = s.options
        print(f"   Dates trouvées: {len(exps)}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
