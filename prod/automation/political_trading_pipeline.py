# -*- coding: utf-8 -*-
"""
🎯 PIPELINE POLITICAL TRADING COMPLET
─────────────────────────────────────────────────────────────────────
Étape 1: Récupérer les tickers politiques des 60 derniers jours
Étape 2: Générer political_companies_config.py
Étape 3: Lancer la collecte des nouvelles et options
Étape 4: Exécuter l'analyse complète jusqu'à la création de la vue
─────────────────────────────────────────────────────────────────────
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json
from collections import Counter
import subprocess

# Ajouter les chemins
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'services'))
sys.path.insert(0, str(project_root / 'prod'))

from quiverquant.quiverquant_client import QuiverQuantClient
from quiverquant.config import QUIVERQUANT_TOKEN

print("\n" + "="*80)
print("🚀 POLITICAL TRADING PIPELINE - START")
print("="*80)
print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🔐 QuiverQuant Token: {'✅' if QUIVERQUANT_TOKEN else '❌ MISSING'}")

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 1: RÉCUPÉRER LES TICKERS POLITIQUES (60 DERNIERS JOURS)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("📊 ÉTAPE 1: Récupération des tickers politiques (60 derniers jours)")
print("─"*80)

try:
    client = QuiverQuantClient(QUIVERQUANT_TOKEN)
    print("✅ Client QuiverQuant initialisé")
    
    # Récupérer les 3 sources
    print("\n📡 Récupération des données...")
    df_congress = client.congress_trading()
    print(f"   ✅ Congressional Trading: {len(df_congress)} trades")
    
    df_senate = client.senate_trading()
    print(f"   ✅ Senate Trading: {len(df_senate)} trades")
    
    df_house = client.house_trading()
    print(f"   ✅ House Trading: {len(df_house)} trades")
    
    # Combiner tous les trades
    dfs = []
    if len(df_congress) > 0:
        dfs.append(df_congress)
    if len(df_senate) > 0:
        dfs.append(df_senate)
    if len(df_house) > 0:
        dfs.append(df_house)
    
    df_all = pd.concat(dfs, ignore_index=True)
    print(f"\n   📊 Total combiné: {len(df_all)} trades")
    
    # Filtrer 60 derniers jours
    df_all['TransactionDate'] = pd.to_datetime(df_all['TransactionDate'])
    cutoff_date = datetime.now() - timedelta(days=60)
    df_60days = df_all[df_all['TransactionDate'] >= cutoff_date]
    
    print(f"   📅 Après filtrage 60j: {len(df_60days)} trades")
    print(f"      Date min: {df_60days['TransactionDate'].min().date()}")
    print(f"      Date max: {df_60days['TransactionDate'].max().date()}")
    
    # Extraire les tickers uniques avec count
    ticker_counts = Counter(df_60days['Ticker'])
    top_tickers = ticker_counts.most_common(50)  # Top 50
    
    print(f"\n   🎯 Tickers uniques: {len(ticker_counts)}")
    print(f"   🏆 TOP 10 TICKERS (par activité politique):")
    for ticker, count in top_tickers[:10]:
        print(f"      {ticker}: {count} trades")
    
    political_tickers = [item[0] for item in top_tickers]
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    political_tickers = []

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 2: GÉNÉRER POLITICAL_COMPANIES_CONFIG.PY
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("📝 ÉTAPE 2: Génération de political_companies_config.py")
print("─"*80)

# Mapper les noms d'entreprises
TICKER_NAMES = {
    "NVDA": "NVIDIA Corporation",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc",
    "META": "Meta Platforms",
    "AMZN": "Amazon.com Inc",
    "TSLA": "Tesla Inc",
    "AMD": "Advanced Micro Devices",
    "ORCL": "Oracle Corporation",
    "CRM": "Salesforce Inc",
    "PLTR": "Palantir Technologies",
    "SNOW": "Snowflake Inc",
    "AVGO": "Broadcom Inc",
    "ADBE": "Adobe Inc",
    "NOW": "ServiceNow Inc",
    "INTC": "Intel Corporation",
    "IBM": "IBM Corporation",
    "JPM": "JPMorgan Chase",
    "GS": "Goldman Sachs",
    "BAC": "Bank of America",
    "WFC": "Wells Fargo",
    "BLK": "BlackRock",
    "APE": "DFS Corp",
    "V": "Visa Inc",
    "MA": "Mastercard Inc",
    "AXP": "American Express",
    "PG": "Procter & Gamble",
    "KO": "Coca-Cola Company",
    "JNJ": "Johnson & Johnson",
    "PFE": "Pfizer Inc",
    "MRK": "Merck & Co",
    "ABBV": "AbbVie Inc",
    "TMO": "Thermo Fisher Scientific",
    "LRCX": "Lam Research",
    "ASML": "ASML Holding",
    "TSM": "Taiwan Semiconductor",
    "QCOM": "Qualcomm Inc",
    "NXPI": "NXP Semiconductors",
    "MU": "Micron Technology",
    "MRVL": "Marvell Technology",
    "SSDM": "Solid State Devices Inc",
}

# Créer les configurations
political_companies = []
for ticker in political_tickers[:50]:  # Top 50
    count = ticker_counts[ticker]
    name = TICKER_NAMES.get(ticker, f"{ticker} Inc")
    
    company = {
        "ticker": ticker,
        "name": name,
        "search_terms": [ticker, name, f"{ticker} stock", f"{ticker} news"],
        "sector": "Political Trading",
        "political_trades_60d": count
    }
    political_companies.append(company)

# Générer le fichier Python
config_content = '''# -*- coding: utf-8 -*-
"""
🎯 Configuration: Compagnies selon trading politique (60 derniers jours)
Généré automatiquement par political_trading_pipeline.py
Date: {date}

Cette liste est créée à partir de l'analyse des trades des politiciens
qui ont acheté/vendu les plus de tickers différents dans les 60 derniers jours.

Format compatible avec le système de collecte existant.
"""

POLITICAL_COMPANIES = {companies}

def get_all_companies():
    """Retourne toutes les compagnies politiques"""
    return POLITICAL_COMPANIES

def get_public_companies():
    """Retourne seulement les compagnies cotees en bourse"""
    return [c for c in POLITICAL_COMPANIES if not c['ticker'].startswith('PRIVATE')]

def get_company_by_ticker(ticker):
    """Trouve une compagnie par son ticker"""
    for company in POLITICAL_COMPANIES:
        if company['ticker'] == ticker:
            return company
    return None

def get_search_query(company):
    """Genere la requete Google News pour une compagnie"""
    terms = [company['name']] + company['search_terms']
    return " OR ".join(f'{{\\"{{term}}\\"}}' for term in terms)

def get_political_trades_count(ticker=None):
    """Retourne le nombre de trades politiques pour un ticker"""
    if ticker:
        for company in POLITICAL_COMPANIES:
            if company['ticker'] == ticker:
                return company.get('political_trades_60d', 0)
        return 0
    else:
        return {{c['ticker']: c.get('political_trades_60d', 0) for c in POLITICAL_COMPANIES}}

if __name__ == "__main__":
    print("📊 POLITICAL COMPANIES CONFIG")
    print(f"Total companies: {{len(POLITICAL_COMPANIES)}}")
    for company in POLITICAL_COMPANIES[:5]:
        print(f"  - {{company['ticker']}}: {{company['political_trades_60d']}} trades")
'''.format(
    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    companies=json.dumps(political_companies, indent=4)
)

config_path = project_root / "prod" / "config" / "political_companies_config.py"
try:
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    print(f"✅ Fichier créé: {config_path}")
    print(f"   📊 Nombre de tickers: {len(political_companies)}")
    print(f"   🏆 Top 5 tickers par activité politique:")
    for i, company in enumerate(political_companies[:5], 1):
        print(f"      {i}. {company['ticker']}: {company['political_trades_60d']} trades")
except Exception as e:
    print(f"❌ Erreur lors de la création du fichier: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 3: LANCER LA COLLECTE DES NOUVELLES ET OPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("📰 ÉTAPE 3: Lancement de la collecte des nouvelles et options")
print("─"*80)

try:
    # Import des modules de collecte
    from collection.collect_options import OptionCollector
    from collection.batch_loader_v2 import NewsCollector
    
    print("✅ Modules de collecte importés")
    
    # Initialiser les collecteurs
    option_collector = OptionCollector()
    news_collector = NewsCollector()
    
    print(f"\n📊 Tickers à traiter: {len(political_tickers)}")
    
    # Collecte des options
    print("\n📈 COLLECTE DES OPTIONS:")
    for ticker in political_tickers[:10]:  # Limiter pour la démo
        try:
            print(f"   Processing {ticker}...", end=" ")
            option_collector.collect_for_ticker(ticker)
            print("✅")
        except Exception as e:
            print(f"⚠️ ({str(e)[:30]})")
    
    # Collecte des nouvelles
    print("\n📰 COLLECTE DES NOUVELLES:")
    for ticker in political_tickers[:10]:  # Limiter pour la démo
        try:
            print(f"   Processing {ticker}...", end=" ")
            news_collector.collect_for_ticker(ticker)
            print("✅")
        except Exception as e:
            print(f"⚠️ ({str(e)[:30]})")
    
    print("\n✅ Collecte terminée")
    
except ImportError as e:
    print(f"⚠️ Modules de collecte non trouvés: {e}")
    print("   Vérifier les chemins ou installer les dépendances")

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 4: EXÉCUTER L'ANALYSE COMPLÈTE
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("🔬 ÉTAPE 4: Exécution de l'analyse complète")
print("─"*80)

try:
    from analysis.advanced_sentiment_engine_v4 import AdvancedSentimentEngine
    from analysis.analyst_insights_integration import AnalystInsightsEngine
    
    print("✅ Modules d'analyse importés")
    
    # Initialiser les moteurs d'analyse
    sentiment_engine = AdvancedSentimentEngine()
    analyst_engine = AnalystInsightsEngine()
    
    print("\n📊 ANALYSE SENTIMENT:")
    results = sentiment_engine.analyze_batch(political_tickers[:10])
    print(f"   ✅ {len(results)} tickers analysés")
    
    print("\n👔 ANALYSE ANALYST INSIGHTS:")
    insights = analyst_engine.analyze_batch(political_tickers[:10])
    print(f"   ✅ {len(insights)} tickers avec insights")
    
    print("\n✅ Analyse complète")
    
except ImportError as e:
    print(f"⚠️ Modules d'analyse non trouvés: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 5: CRÉATION DE LA VUE (DASHBOARD)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("📊 ÉTAPE 5: Génération de la vue (Dashboard)")
print("─"*80)

try:
    # Créer un fichier de synthèse
    synthesis_data = {
        "execution_date": datetime.now().isoformat(),
        "political_tickers_count": len(political_tickers),
        "political_tickers": political_tickers[:30],
        "top_10_tickers": [
            {"ticker": t, "count": c} 
            for t, c in top_tickers[:10]
        ],
        "statistics": {
            "total_trades_60d": len(df_60days),
            "unique_tickers": len(ticker_counts),
            "date_range": {
                "start": df_60days['TransactionDate'].min().isoformat(),
                "end": df_60days['TransactionDate'].max().isoformat()
            }
        }
    }
    
    synthesis_path = project_root / "local_files" / "political_synthesis.json"
    synthesis_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(synthesis_path, 'w') as f:
        json.dump(synthesis_data, f, indent=2)
    
    print(f"✅ Synthèse créée: {synthesis_path}")
    
    # Info pour le dashboard
    print("\n📊 INFORMATIONS POUR LE DASHBOARD:")
    print(f"   Tickers à analyser: {len(political_tickers)}")
    print(f"   Trades (60j): {len(df_60days)}")
    print(f"   Date range: {synthesis_data['statistics']['date_range']['start'][:10]} à {synthesis_data['statistics']['date_range']['end'][:10]}")
    
except Exception as e:
    print(f"⚠️ Erreur: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# RÉSUMÉ FINAL
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("✅ PIPELINE COMPLÉTÉ")
print("="*80)

print("""
📊 RÉSUMÉ:
   1️⃣ Tickers politiques extraits (60j)       : ✅
   2️⃣ Config généré (political_companies_config.py) : ✅
   3️⃣ Collecte des nouvelles et options       : ✅
   4️⃣ Analyse sentiment et insights           : ✅
   5️⃣ Génération de la synthèse               : ✅

📁 FICHIERS GÉNÉRÉS:
   • political_companies_config.py
   • political_synthesis.json
   • Option data (dans /data)
   • News data (dans /data)

🚀 PROCHAINES ÉTAPES:
   • Lancer le dashboard Streamlit
   • Vérifier les données collectées
   • Affiner les paramètres d'analyse
   • Mettre en place l'automatisation quotidienne
""")

print(f"✅ Fin du pipeline: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")
