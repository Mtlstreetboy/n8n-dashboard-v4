
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import sys

# Config d'affichage
pd.set_option('display.max_rows', 20)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

print("✅ Bibliothèques chargées")

# 1. CONFIGURATION DU TICKER
TICKER = "SHOP.TO"

print(f"🔍 Initialisation de l'objet Ticker pour {TICKER}...")
stock = yf.Ticker(TICKER)

# Vérification basique
try:
    info = stock.info
    print(f"✅ Ticker reconnu: {info.get('shortName', 'Nom inconnu')} ({info.get('currency', 'Devise inconnue')})")
    print(f"   Prix actuel: {info.get('currentPrice')}")
except Exception as e:
    print(f"⚠️ Attention: Impossible de récupérer les infos de base: {e}")

# 2. RÉCUPÉRATION DES DATES D'EXPIRATION
print("⏳ Récupération des dates d'expiration...")
expirations = ()
try:
    expirations = stock.options
    if not expirations:
        print("❌ AUCUNE date d'expiration trouvée. C'est souvent ici que ça bloque pour le TSX.")
        print("   Pistes: Ticker invalide ? Pas d'options liquides ? Problème API Yahoo ?")
    else:
        print(f"✅ {len(expirations)} dates trouvées:")
        print(expirations)
except Exception as e:
    print(f"❌ ERREUR GRAVE lors de la récupération des options: {e}")

# 3. ANALYSE DE LA PREMIÈRE DATE (CHAIN)
if expirations:
    target_date = expirations[0]
    print(f"🔬 Analyse détaillée pour l'expiration: {target_date}")
    
    try:
        # Téléchargement de la chaîne
        chain = stock.option_chain(target_date)
        calls = chain.calls
        puts = chain.puts
        
        print(f"\n📞 CALLS: {len(calls)} contrats")
        if not calls.empty:
            print(calls[['contractSymbol', 'lastTradeDate', 'strike', 'lastPrice', 'volume', 'openInterest']].head())
            
        print(f"\n📉 PUTS: {len(puts)} contrats")
        if not puts.empty:
            print(puts[['contractSymbol', 'lastTradeDate', 'strike', 'lastPrice', 'volume', 'openInterest']].head())
            
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement de la chaîne: {e}")
else:
    print("⚠️ Pas d'expirations, impossible de tester la chaîne.")

# 4. DIAGNOSTIC COMPLET (BOUCLE)
if expirations:
    print("🔄 Test de TOUTES les expirations (Max 5)...")
    for date in expirations[:5]:
        try:
            c = stock.option_chain(date)
            n_calls = len(c.calls)
            n_puts = len(c.puts)
            print(f"  📅 {date}: {n_calls} Calls, {n_puts} Puts")
            time.sleep(0.5) # Pause respectueuse
        except Exception as e:
            print(f"  📅 {date}: ❌ ERREUR ({e})")
else:
    print("⚠️ Rien à tester sur la boucle.")

# 5. LA SOLUTION POTENTIELLE ?
TEST_ALTERNATIVES = [TICKER, TICKER.replace('.TO', '.TRT'), TICKER.split('.')[0]]

print("🧪 Test des variantes de ticker pour voir si les options apparaissent...")

for alt in TEST_ALTERNATIVES:
    if alt == TICKER: 
        continue # Déjà testé
        
    print(f"\n🔄 Test variante: {alt}")
    s = yf.Ticker(alt)
    try:
        exps = s.options
        print(f"   Dates trouvées: {len(exps)}")
        if exps:
            print(f"   Exemple: {exps[0]}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
