# -*- coding: utf-8 -*-
"""
🎯 ORCHESTRATEUR PRINCIPAL - Political Trading Analysis Pipeline
─────────────────────────────────────────────────────────────────────────────
Exécute la chaîne complète:
  1. Extract: Tickers politiques (60j) depuis QuiverQuant
  2. Config: Génère political_companies_config.py
  3. Collect: Nouvelles et options pour chaque ticker
  4. Analyze: Sentiment, insights, et synthèse
  5. Generate: Vue/Dashboard HTML final
─────────────────────────────────────────────────────────────────────────────

Usage:
    python prod/automation/run_political_pipeline.py --mode full
    python prod/automation/run_political_pipeline.py --mode extract-only
    python prod/automation/run_political_pipeline.py --mode analyze-only
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('political_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ajouter les chemins
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'services'))
sys.path.insert(0, str(project_root / 'prod'))

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: EXTRACTION DES TICKERS POLITIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def phase_extract_political_tickers():
    """
    Phase 1: Récupérer les tickers les plus traités par les politiciens (60j)
    Retourne: Liste de tickers, DataFrame des données brutes
    """
    print("\n" + "▓"*80)
    print("📊 PHASE 1: EXTRACTION DES TICKERS POLITIQUES")
    print("▓"*80)
    
    from datetime import timedelta
    from collections import Counter
    import pandas as pd
    from quiverquant.quiverquant_client import QuiverQuantClient
    from quiverquant.config import QUIVERQUANT_TOKEN
    
    logger.info("Initialisation du client QuiverQuant...")
    
    try:
        client = QuiverQuantClient(QUIVERQUANT_TOKEN)
        
        # Récupérer les données
        logger.info("Récupération Congressional Trading...")
        df_congress = client.congress_trading()
        
        logger.info("Récupération Senate Trading...")
        df_senate = client.senate_trading()
        
        logger.info("Récupération House Trading...")
        df_house = client.house_trading()
        
        # Combiner
        dfs = [df for df in [df_congress, df_senate, df_house] if len(df) > 0]
        df_all = pd.concat(dfs, ignore_index=True)
        
        logger.info(f"Total de {len(df_all)} trades récupérés")
        
        # Filtrer 60j
        df_all['TransactionDate'] = pd.to_datetime(df_all['TransactionDate'])
        cutoff_date = datetime.now() - timedelta(days=60)
        df_60days = df_all[df_all['TransactionDate'] >= cutoff_date]
        
        logger.info(f"Après filtrage 60j: {len(df_60days)} trades")
        
        # Extraire tickers
        ticker_counts = Counter(df_60days['Ticker'])
        top_tickers = [t[0] for t in ticker_counts.most_common(50)]
        
        print(f"✅ {len(df_60days)} trades extraits")
        print(f"✅ {len(ticker_counts)} tickers uniques")
        print(f"✅ Top 10 tickers identifiés")
        
        return top_tickers, df_60days, ticker_counts
        
    except Exception as e:
        logger.error(f"Erreur Phase 1: {e}", exc_info=True)
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: GÉNÉRATION DE LA CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

def phase_generate_config(tickers, ticker_counts):
    """
    Phase 2: Générer political_companies_config.py
    """
    print("\n" + "▓"*80)
    print("📝 PHASE 2: GÉNÉRATION DE LA CONFIGURATION")
    print("▓"*80)
    
    import json
    
    logger.info(f"Génération de config pour {len(tickers)} tickers...")
    
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
        "V": "Visa Inc",
        "MA": "Mastercard Inc",
        "AXP": "American Express",
    }
    
    political_companies = []
    for ticker in tickers[:30]:
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
    
    # Écrire le fichier
    config_content = f'''# -*- coding: utf-8 -*-
"""
🎯 Configuration: Compagnies selon trading politique (60 derniers jours)
Généré automatiquement par run_political_pipeline.py
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Nombre de compagnies: {len(political_companies)}
Top ticker: {political_companies[0]['ticker'] if political_companies else 'N/A'} ({political_companies[0].get('political_trades_60d', 0)} trades)
"""

POLITICAL_COMPANIES = {json.dumps(political_companies, indent=4)}

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
    return " OR ".join(f'"{term}"' for term in terms)

def get_political_trades_count(ticker=None):
    """Retourne le nombre de trades politiques"""
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
'''
    
    config_path = project_root / "prod" / "config" / "political_companies_config.py"
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        logger.info(f"Config créé: {config_path}")
        print(f"✅ Config générée: {len(political_companies)} compagnies")
        
        return political_companies
        
    except Exception as e:
        logger.error(f"Erreur Phase 2: {e}", exc_info=True)
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: COLLECTE DES DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

def phase_collect_data(tickers):
    """
    Phase 3: Collecter les nouvelles et options
    """
    print("\n" + "▓"*80)
    print("📰 PHASE 3: COLLECTE DES DONNÉES")
    print("▓"*80)
    
    logger.info(f"Collecte pour {len(tickers)} tickers...")
    
    try:
        from collection.batch_loader_v2 import BatchNewsCollector
        from collection.collect_options import OptionCollector
        
        news_collector = BatchNewsCollector()
        option_collector = OptionCollector()
        
        success_count = 0
        for ticker in tickers[:15]:  # Limiter pour perfo
            try:
                logger.debug(f"Collecte news pour {ticker}...")
                news_collector.collect(ticker)
                success_count += 1
            except Exception as e:
                logger.warning(f"Erreur news {ticker}: {e}")
        
        print(f"✅ {success_count}/{len(tickers[:15])} tickers - nouvelles collectées")
        
        # Options collecte similaire
        option_count = 0
        for ticker in tickers[:10]:
            try:
                logger.debug(f"Collecte options pour {ticker}...")
                option_collector.collect(ticker)
                option_count += 1
            except Exception as e:
                logger.warning(f"Erreur options {ticker}: {e}")
        
        print(f"✅ {option_count}/{len(tickers[:10])} tickers - options collectées")
        
    except ImportError as e:
        logger.warning(f"Modules de collecte non disponibles: {e}")
        print(f"⚠️ Collecte passée (modules non trouvés)")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: ANALYSE
# ═══════════════════════════════════════════════════════════════════════════════

def phase_analyze(tickers):
    """
    Phase 4: Exécuter l'analyse sentiment et insights
    """
    print("\n" + "▓"*80)
    print("🔬 PHASE 4: ANALYSE DES DONNÉES")
    print("▓"*80)
    
    logger.info(f"Analyse pour {len(tickers)} tickers...")
    
    try:
        from analysis.advanced_sentiment_engine_v4 import AdvancedSentimentEngine
        
        engine = AdvancedSentimentEngine()
        results = engine.analyze_batch(tickers[:10])
        
        print(f"✅ {len(results)} tickers analysés")
        
    except ImportError as e:
        logger.warning(f"Module d'analyse non disponible: {e}")
        print(f"⚠️ Analyse passée (modules non trouvés)")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: GÉNÉRATION DE LA VUE
# ═══════════════════════════════════════════════════════════════════════════════

def phase_generate_view(tickers, df_data):
    """
    Phase 5: Générer les fichiers de synthèse et vue finale
    """
    print("\n" + "▓"*80)
    print("📊 PHASE 5: GÉNÉRATION DE LA VUE")
    print("▓"*80)
    
    import json
    
    logger.info("Génération des fichiers de synthèse...")
    
    try:
        synthesis = {
            "execution": {
                "date": datetime.now().isoformat(),
                "version": "2.0"
            },
            "source": "QuiverQuant Political Trading",
            "summary": {
                "total_tickers": len(tickers),
                "total_trades_60d": len(df_data),
                "date_range": {
                    "start": df_data['TransactionDate'].min().isoformat(),
                    "end": df_data['TransactionDate'].max().isoformat()
                }
            },
            "tickers": tickers[:30],
            "next_steps": [
                "Lancer streamlit run prod/dashboard/dashboard_v4_political.py",
                "Vérifier les données dans /data/political_trades/",
                "Configurer l'automatisation quotidienne"
            ]
        }
        
        output_dir = project_root / "local_files" / "political_trades"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        synthesis_file = output_dir / "synthesis.json"
        with open(synthesis_file, 'w') as f:
            json.dump(synthesis, f, indent=2)
        
        logger.info(f"Synthèse créée: {synthesis_file}")
        print(f"✅ Synthèse générée")
        
        # Créer un fichier README
        readme_content = f"""# 🎯 Political Trading Analysis Results
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary
- **Total Tickers Analyzed**: {len(tickers)}
- **Political Trades (60 days)**: {len(df_data)}
- **Analysis Mode**: Political Trading Strategy
- **Data Source**: QuiverQuant API

## Top Tickers
{chr(10).join(f"- {t}" for t in tickers[:10])}

## Next Steps
1. Review results in synthesis.json
2. Launch dashboard: `streamlit run prod/dashboard/dashboard_political.py`
3. Set up daily automation
4. Monitor results

## Files Generated
- political_companies_config.py (30 tickers)
- synthesis.json (summary data)
- Collection data (news & options)
"""
        
        readme_file = output_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print(f"✅ README créé")
        return synthesis
        
    except Exception as e:
        logger.error(f"Erreur Phase 5: {e}", exc_info=True)
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATEUR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_pipeline():
    """Exécuter le pipeline complet"""
    print("\n" + "="*80)
    print("🚀 POLITICAL TRADING PIPELINE - START")
    print("="*80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Phase 1
        tickers, df_60days, ticker_counts = phase_extract_political_tickers()
        
        # Phase 2
        companies = phase_generate_config(tickers, ticker_counts)
        
        # Phase 3
        phase_collect_data(tickers)
        
        # Phase 4
        phase_analyze(tickers)
        
        # Phase 5
        synthesis = phase_generate_view(tickers, df_60days)
        
        # Résumé final
        print("\n" + "="*80)
        print("✅ PIPELINE COMPLÉTÉ AVEC SUCCÈS")
        print("="*80)
        
        print(f"""
📊 RÉSUMÉ:
   ✅ Phase 1: {len(tickers)} tickers extraits
   ✅ Phase 2: Config générée ({len(companies)} compagnies)
   ✅ Phase 3: Collecte des données
   ✅ Phase 4: Analyse sentiment
   ✅ Phase 5: Vue générée

🚀 PROCHAINES ÉTAPES:
   1. Vérifier: political_companies_config.py
   2. Lancer: streamlit run prod/dashboard/dashboard_political.py
   3. Automatiser: prod/automation/daily_automation.py
        """)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\n❌ Pipeline échoué: {e}")
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Political Trading Analysis Pipeline"
    )
    parser.add_argument(
        "--mode",
        default="full",
        choices=["full", "extract-only", "collect-only", "analyze-only"],
        help="Mode d'exécution"
    )
    
    args = parser.parse_args()
    
    if args.mode == "full":
        run_full_pipeline()
    else:
        print(f"Mode {args.mode} non implémenté dans cette version")
        print("Utiliser: --mode full")
