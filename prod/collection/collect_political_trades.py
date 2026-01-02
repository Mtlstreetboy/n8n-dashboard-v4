#!/usr/bin/env python3
"""
💰 COLLECTEUR DE TRADES POLITIQUES (CONGRESS, SENATE, HOUSE)
--------------------------------------------------------------------
Collecte les trades politiques et identifie les stocks les plus actifs
pour alimenter le processus d'analyse sentiment.

Usage: python3 collect_political_trades.py
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Environment Detection
if os.path.exists('/data/scripts'):
    sys.path.insert(0, '/data/scripts')
    DATA_DIR = '/data'
else:
    # Local Execution (Windows)
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
    sys.path.append(PROJECT_ROOT)
    DATA_DIR = os.path.join(PROJECT_ROOT, 'local_files')

from services.quiverquant.quiverquant_client import QuiverQuantClient
from services.quiverquant.config import QUIVERQUANT_TOKEN

import pandas as pd
import json
from collections import Counter

# Configuration
POLITICAL_DATA_DIR = os.path.join(DATA_DIR, 'political_trades')
CACHE_DIR = os.path.join(POLITICAL_DATA_DIR, 'cache')
OUTPUT_DIR = POLITICAL_DATA_DIR

# Créer les répertoires
os.makedirs(POLITICAL_DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)


class PoliticalTradesCollector:
    """
    Collecteur de trades politiques avec cache et analyse des stocks
    """
    
    def __init__(self):
        self.client = QuiverQuantClient(QUIVERQUANT_TOKEN)
        self.cache_dir = Path(CACHE_DIR)
        self.output_dir = Path(OUTPUT_DIR)
        
    def log(self, message):
        """Log avec timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
        
    def collect_all_trades(self):
        """
        Collecte tous les types de trades politiques
        """
        self.log("=" * 70)
        self.log("💰 DÉBUT COLLECTE TRADES POLITIQUES")
        self.log("=" * 70)
        
        results = {}
        
        # 1. Congressional Trading (tous)
        self.log("\n1️⃣ Collecte Congressional Trading...")
        try:
            df_congress = self.client.congress_trading()
            results['congressional'] = df_congress
            self.log(f"   ✅ {len(df_congress)} trades collectés")
        except Exception as e:
            self.log(f"   ❌ Erreur: {e}")
            results['congressional'] = pd.DataFrame()
        
        # 2. Senate Trading
        self.log("\n2️⃣ Collecte Senate Trading...")
        try:
            df_senate = self.client.senate_trading()
            results['senate'] = df_senate
            self.log(f"   ✅ {len(df_senate)} trades collectés")
        except Exception as e:
            self.log(f"   ❌ Erreur: {e}")
            results['senate'] = pd.DataFrame()
        
        # 3. House Trading
        self.log("\n3️⃣ Collecte House Trading...")
        try:
            df_house = self.client.house_trading()
            results['house'] = df_house
            self.log(f"   ✅ {len(df_house)} trades collectés")
        except Exception as e:
            self.log(f"   ❌ Erreur: {e}")
            results['house'] = pd.DataFrame()
        
        return results
    
    def save_raw_data(self, results):
        """
        Sauvegarde les données brutes
        """
        self.log("\n📁 Sauvegarde des données brutes...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for source, df in results.items():
            if len(df) > 0:
                # CSV
                csv_path = self.output_dir / f"{source}_trades_{timestamp}.csv"
                df.to_csv(csv_path, index=False)
                self.log(f"   ✅ {csv_path.name}")
                
                # Latest (écrase le précédent)
                latest_path = self.output_dir / f"{source}_trades_latest.csv"
                df.to_csv(latest_path, index=False)
        
        self.log("   ✅ Données brutes sauvegardées")
    
    def cache_with_history(self, df_new, source_name):
        """
        Cache avec accumulation historique (résout problème 1000 résultats)
        """
        cache_file = self.cache_dir / f"{source_name}_cache.parquet"
        
        if cache_file.exists():
            # Charger ancien cache
            df_old = pd.read_parquet(cache_file)
            self.log(f"   📦 Cache existant: {len(df_old)} trades")
            
            # Identifier colonnes pour déduplication
            if 'Representative' in df_new.columns:
                dedup_cols = ['Representative', 'TransactionDate', 'Ticker']
            elif 'Senator' in df_new.columns:
                dedup_cols = ['Senator', 'Date', 'Ticker']
            else:
                dedup_cols = None
            
            # Merger et dédupliquer
            if dedup_cols:
                df_merged = pd.concat([df_new, df_old]).drop_duplicates(
                    subset=dedup_cols,
                    keep='first'
                )
            else:
                df_merged = pd.concat([df_new, df_old]).drop_duplicates()
            
            self.log(f"   🔄 Après merge: {len(df_merged)} trades (ajout de {len(df_merged) - len(df_old)})")
        else:
            df_merged = df_new
            self.log(f"   🆕 Nouveau cache: {len(df_merged)} trades")
        
        # Sauvegarder cache
        df_merged.to_parquet(cache_file)
        
        return df_merged
    
    def analyze_stocks(self, results):
        """
        Analyse les stocks les plus tradés
        """
        self.log("\n" + "=" * 70)
        self.log("📊 ANALYSE DES STOCKS LES PLUS TRADÉS")
        self.log("=" * 70)
        
        all_tickers = []
        
        for source, df in results.items():
            if len(df) > 0 and 'Ticker' in df.columns:
                tickers = df['Ticker'].tolist()
                all_tickers.extend(tickers)
        
        if not all_tickers:
            self.log("⚠️ Aucun ticker trouvé")
            return None
        
        # Compter les occurrences
        ticker_counts = Counter(all_tickers)
        
        # Créer DataFrame
        df_tickers = pd.DataFrame([
            {'ticker': ticker, 'trade_count': count}
            for ticker, count in ticker_counts.most_common()
        ])
        
        self.log(f"\n✅ {len(df_tickers)} tickers uniques identifiés")
        self.log(f"\n📈 TOP 20 STOCKS LES PLUS TRADÉS:")
        self.log("-" * 70)
        
        for idx, row in df_tickers.head(20).iterrows():
            self.log(f"   {idx+1:2d}. {row['ticker']:6s} - {row['trade_count']:4d} trades")
        
        return df_tickers
    
    def analyze_sentiment_60days(self, results):
        """
        Analyse le sentiment (achats vs ventes) sur 60 jours
        """
        self.log("\n" + "=" * 70)
        self.log("📅 ANALYSE SENTIMENT - 60 DERNIERS JOURS")
        self.log("=" * 70)
        
        cutoff_date = datetime.now() - timedelta(days=60)
        
        sentiment_data = []
        
        for source, df in results.items():
            if len(df) == 0:
                continue
                
            # Identifier colonnes de date et transaction
            date_col = None
            trans_col = None
            
            if 'TransactionDate' in df.columns:
                date_col = 'TransactionDate'
            elif 'Date' in df.columns:
                date_col = 'Date'
            
            if 'Transaction' in df.columns:
                trans_col = 'Transaction'
            
            if not date_col or not trans_col or 'Ticker' not in df.columns:
                continue
            
            # Convertir dates
            df[date_col] = pd.to_datetime(df[date_col])
            
            # Filtrer 60 jours
            df_60d = df[df[date_col] >= cutoff_date].copy()
            
            self.log(f"\n{source.upper()}: {len(df_60d)} trades dans les 60 derniers jours")
            
            if len(df_60d) == 0:
                continue
            
            # Analyser par ticker
            for ticker in df_60d['Ticker'].unique():
                df_ticker = df_60d[df_60d['Ticker'] == ticker]
                
                purchases = df_ticker[df_ticker[trans_col].str.contains('Purchase|Buy', case=False, na=False)]
                sales = df_ticker[df_ticker[trans_col].str.contains('Sale|Sell', case=False, na=False)]
                
                buy_count = len(purchases)
                sell_count = len(sales)
                
                if buy_count + sell_count > 0:
                    sentiment_score = (buy_count - sell_count) / (buy_count + sell_count)
                    
                    sentiment_data.append({
                        'ticker': ticker,
                        'source': source,
                        'purchases': buy_count,
                        'sales': sell_count,
                        'total': buy_count + sell_count,
                        'sentiment_score': sentiment_score,
                        'signal': 'BULLISH' if sentiment_score > 0.3 else 'BEARISH' if sentiment_score < -0.3 else 'NEUTRAL'
                    })
        
        if not sentiment_data:
            self.log("⚠️ Pas de données sentiment sur 60 jours")
            return None
        
        df_sentiment = pd.DataFrame(sentiment_data)
        
        # Agréger par ticker
        df_agg = df_sentiment.groupby('ticker').agg({
            'purchases': 'sum',
            'sales': 'sum',
            'total': 'sum'
        }).reset_index()
        
        df_agg['sentiment_score'] = (df_agg['purchases'] - df_agg['sales']) / df_agg['total']
        df_agg['signal'] = df_agg['sentiment_score'].apply(
            lambda x: 'BULLISH' if x > 0.3 else 'BEARISH' if x < -0.3 else 'NEUTRAL'
        )
        df_agg = df_agg.sort_values('sentiment_score', ascending=False)
        
        self.log(f"\n📊 TOP 10 BULLISH STOCKS:")
        self.log("-" * 70)
        for idx, row in df_agg.head(10).iterrows():
            self.log(f"   {row['ticker']:6s} | Score: {row['sentiment_score']:+.2f} | "
                    f"Achats: {row['purchases']:3d} | Ventes: {row['sales']:3d}")
        
        self.log(f"\n📊 TOP 10 BEARISH STOCKS:")
        self.log("-" * 70)
        for idx, row in df_agg.tail(10).iterrows():
            self.log(f"   {row['ticker']:6s} | Score: {row['sentiment_score']:+.2f} | "
                    f"Achats: {row['purchases']:3d} | Ventes: {row['sales']:3d}")
        
        return df_sentiment, df_agg
    
    def generate_stock_list_for_analysis(self, df_tickers, df_sentiment_agg, min_trades=5):
        """
        Génère la liste des stocks recommandés pour l'analyse sentiment
        """
        self.log("\n" + "=" * 70)
        self.log("🎯 GÉNÉRATION LISTE POUR ANALYSE SENTIMENT")
        self.log("=" * 70)
        
        # Filtrer par minimum de trades
        df_filtered = df_tickers[df_tickers['trade_count'] >= min_trades].copy()
        
        # Merger avec sentiment si disponible
        if df_sentiment_agg is not None:
            df_filtered = df_filtered.merge(
                df_sentiment_agg[['ticker', 'sentiment_score', 'signal']],
                on='ticker',
                how='left'
            )
        
        # Trier par trade_count
        df_filtered = df_filtered.sort_values('trade_count', ascending=False)
        
        self.log(f"\n✅ {len(df_filtered)} stocks avec minimum {min_trades} trades")
        
        # Sauvegarder
        output_file = self.output_dir / 'stocks_for_analysis.csv'
        df_filtered.to_csv(output_file, index=False)
        self.log(f"   📁 Sauvegardé: {output_file}")
        
        # Générer aussi format JSON pour intégration
        stocks_dict = {
            'generated_date': datetime.now().isoformat(),
            'total_stocks': len(df_filtered),
            'min_trades_threshold': min_trades,
            'stocks': df_filtered.to_dict('records')
        }
        
        json_file = self.output_dir / 'stocks_for_analysis.json'
        with open(json_file, 'w') as f:
            json.dump(stocks_dict, f, indent=2)
        self.log(f"   📁 Sauvegardé: {json_file}")
        
        return df_filtered
    
    def generate_summary_report(self, results, df_tickers, df_sentiment_agg):
        """
        Génère un rapport de synthèse
        """
        self.log("\n" + "=" * 70)
        self.log("📋 RAPPORT DE SYNTHÈSE")
        self.log("=" * 70)
        
        report = {
            'collection_date': datetime.now().isoformat(),
            'sources': {},
            'top_stocks': {},
            'sentiment_summary': {}
        }
        
        # Stats par source
        for source, df in results.items():
            if len(df) > 0:
                report['sources'][source] = {
                    'total_trades': len(df),
                    'unique_tickers': df['Ticker'].nunique() if 'Ticker' in df.columns else 0,
                    'date_range': {
                        'min': str(df[df.columns[1]].min()) if len(df.columns) > 1 else None,
                        'max': str(df[df.columns[1]].max()) if len(df.columns) > 1 else None
                    }
                }
        
        # Top stocks
        if df_tickers is not None:
            report['top_stocks'] = {
                'total_unique': len(df_tickers),
                'top_20': df_tickers.head(20).to_dict('records')
            }
        
        # Sentiment
        if df_sentiment_agg is not None:
            report['sentiment_summary'] = {
                'bullish_count': len(df_sentiment_agg[df_sentiment_agg['signal'] == 'BULLISH']),
                'bearish_count': len(df_sentiment_agg[df_sentiment_agg['signal'] == 'BEARISH']),
                'neutral_count': len(df_sentiment_agg[df_sentiment_agg['signal'] == 'NEUTRAL']),
                'top_bullish': df_sentiment_agg.head(10).to_dict('records'),
                'top_bearish': df_sentiment_agg.tail(10).to_dict('records')
            }
        
        # Sauvegarder
        report_file = self.output_dir / 'collection_summary.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"\n✅ Rapport sauvegardé: {report_file}")
        
        return report
    
    def run(self):
        """
        Exécution complète du processus
        """
        try:
            # 1. Collecter les trades
            results = self.collect_all_trades()
            
            # 2. Sauvegarder données brutes
            self.save_raw_data(results)
            
            # 3. Cache avec historique
            self.log("\n📦 Mise en cache avec historique...")
            for source, df in results.items():
                if len(df) > 0:
                    self.cache_with_history(df, source)
            
            # 4. Analyser les stocks
            df_tickers = self.analyze_stocks(results)
            
            # 5. Analyser sentiment 60 jours
            df_sentiment, df_sentiment_agg = self.analyze_sentiment_60days(results)
            
            # 6. Générer liste pour analyse
            if df_tickers is not None:
                df_stocks = self.generate_stock_list_for_analysis(
                    df_tickers, 
                    df_sentiment_agg,
                    min_trades=5
                )
            
            # 7. Générer rapport
            report = self.generate_summary_report(results, df_tickers, df_sentiment_agg)
            
            # 8. Résumé final
            self.log("\n" + "=" * 70)
            self.log("✅ COLLECTE TERMINÉE")
            self.log("=" * 70)
            self.log(f"\n📁 Fichiers générés dans: {self.output_dir}")
            self.log(f"   - stocks_for_analysis.csv")
            self.log(f"   - stocks_for_analysis.json")
            self.log(f"   - collection_summary.json")
            self.log(f"   - *_trades_latest.csv (par source)")
            self.log(f"\n🎯 PROCHAINE ÉTAPE:")
            self.log(f"   Utiliser stocks_for_analysis.csv pour lancer l'analyse sentiment")
            
            return True
            
        except Exception as e:
            self.log(f"\n❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    collector = PoliticalTradesCollector()
    success = collector.run()
    sys.exit(0 if success else 1)
