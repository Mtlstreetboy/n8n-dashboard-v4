#!/usr/bin/env python3
"""
📊 COLLECTEUR D'OPTIONS (CALLS & PUTS) POUR SENTIMENT ANALYSIS
--------------------------------------------------------------------
Collecte les données d'options pour analyse de sentiment:
- Volume et Open Interest des Calls/Puts
- Ratio Put/Call
- Implied Volatility
- Prix d'exercice (Strike) et expiration
- Greeks (Delta, Gamma, Theta, Vega) si disponibles

Sources: Yahoo Finance (gratuit) + Alpha Vantage (backup)

Usage: python3 collect_options.py
"""
import sys
import os

# Environment Detection
if os.path.exists('/data/scripts'):
    sys.path.insert(0, '/data/scripts')
    DATA_DIR = '/data'
else:
    # Local Execution (Windows)
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROD_DIR = os.path.dirname(CURRENT_DIR)
    PROJECT_ROOT = os.path.dirname(PROD_DIR)
    # Add prod to path for config import
    sys.path.append(PROD_DIR)
    sys.path.append(PROJECT_ROOT)
    DATA_DIR = os.path.join(PROJECT_ROOT, 'local_files')

# Import absolute from config package to avoid relative import issues
from config.companies_config import get_all_companies
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
from collections import defaultdict
import pandas as pd
import requests

# Configuration
CACHE_DIR = os.path.join(DATA_DIR, 'options_cache')
OUTPUT_DIR = os.path.join(DATA_DIR, 'options_data')
ALPHA_VANTAGE_KEY = 'YOUR_KEY_HERE'  # Optionnel, backup si Yahoo echoue

class OptionsCollector:
    def __init__(self, cache_dir=CACHE_DIR, output_dir=OUTPUT_DIR):
        self.cache_dir = cache_dir
        self.output_dir = output_dir
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
    def get_options_data(self, ticker, days_forward=90):
        """
        Collecte les données d'options pour un ticker
        """
        print(f"\n{'='*60}")
        print(f"📊 {ticker} - Collecte des Options")
        print(f"{'='*60}")
        
        # [V2 SMART CACHE] Check if we already have data for TODAY
        today_str = datetime.now().strftime('%Y-%m-%d')
        daily_file = os.path.join(self.output_dir, f'{ticker}_sentiment_{today_str}.json')
        
        if os.path.exists(daily_file) and '--force' not in sys.argv:
            try:
                print(f"  ⚡ [CACHE] Données du jour trouvées ({today_str}) - SKIP")
                with open(daily_file, 'r') as f:
                    metrics = json.load(f)
                
                # We return the cached data to include it in the report
                return {
                    'ticker': ticker,
                    'calls_count': 0, # Placeholder, data is in metrics
                    'puts_count': 0,
                    'sentiment_metrics': metrics
                }
            except Exception as e:
                print(f"  [!] Erreur lecture cache: {e}. Force collecte.")
        else:
             print(f"  🔄 Pas de données pour {today_str} - Lancement collecte...")
        
        try:
            # Créer l'objet ticker
            stock = yf.Ticker(ticker)
            
            # Récupérer les dates d'expiration disponibles
            expirations = stock.options
            
            # 🇨🇦 CANADIAN TICKER FALLBACK LOGIC
            # If no options found and ticker has .TO suffix, try US ticker
            if not expirations and ticker.endswith('.TO'):
                us_ticker = ticker.replace('.TO', '')
                print(f"  🔄 Aucune option pour {ticker}, tentative avec {us_ticker}...")
                stock = yf.Ticker(us_ticker)
                expirations = stock.options
                
                if expirations:
                    print(f"  ✅ Options trouvées avec {us_ticker} ({len(expirations)} dates)")
                    # Update ticker for the rest of the processing
                    ticker = us_ticker
                else:
                    print(f"  ❌ Aucune option pour {us_ticker} non plus")
            
            if not expirations:
                print(f"⚠️ Aucune option disponible pour {ticker}")
                return None
            
            print(f"📅 {len(expirations)} dates d'expiration disponibles")
            
            # Filtrer les expirations dans les X prochains jours
            cutoff_date = (datetime.now() + timedelta(days=days_forward)).strftime('%Y-%m-%d')
            valid_expirations = [exp for exp in expirations if exp <= cutoff_date]
            
            print(f"🎯 {len(valid_expirations)} expirations dans les {days_forward} prochains jours")
            
            all_calls = []
            all_puts = []
            
            # Collecter pour chaque date d'expiration
            for i, exp_date in enumerate(valid_expirations, 1):
                try:
                    print(f"  [{i}/{len(valid_expirations)}] {exp_date}...", end='')
                    
                    # Récupérer la chaîne d'options
                    opt_chain = stock.option_chain(exp_date)
                    
                    # Calls
                    calls = opt_chain.calls
                    calls['expiration'] = exp_date
                    calls['type'] = 'call'
                    calls['ticker'] = ticker
                    calls['collected_at'] = datetime.now().isoformat()
                    all_calls.append(calls)
                    
                    # Puts
                    puts = opt_chain.puts
                    puts['expiration'] = exp_date
                    puts['type'] = 'put'
                    puts['ticker'] = ticker
                    puts['collected_at'] = datetime.now().isoformat()
                    all_puts.append(puts)
                    
                    print(f" ✅ {len(calls)} calls, {len(puts)} puts")
                    
                    # Délai pour éviter le rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f" ❌ {str(e)[:50]}")
                    continue
            
            if not all_calls and not all_puts:
                print(f"⚠️ Aucune donnée collectée pour {ticker}")
                return None
            
            # Combiner toutes les données
            calls_df = pd.concat(all_calls, ignore_index=True) if all_calls else pd.DataFrame()
            puts_df = pd.concat(all_puts, ignore_index=True) if all_puts else pd.DataFrame()
            
            # Calculer les métriques de sentiment
            sentiment_metrics = self._calculate_sentiment_metrics(ticker, calls_df, puts_df)
            
            # Sauvegarder
            self._save_options_data(ticker, calls_df, puts_df, sentiment_metrics)
            
            print(f"\n✅ {ticker} TERMINÉ:")
            print(f"   📞 Calls: {len(calls_df)}")
            print(f"   📉 Puts: {len(puts_df)}")
            # Affichage sécurisé du Put/Call Ratio (éviter formatage sur 'N/A')
            pcr_val = sentiment_metrics.get('put_call_ratio_volume')
            try:
                pcr_str = f"{float(pcr_val):.2f}" if pcr_val is not None else "N/A"
            except Exception:
                pcr_str = str(pcr_val)

            print(f"   🎯 Put/Call Ratio: {pcr_str}")
            print(f"   💡 Sentiment: {sentiment_metrics.get('sentiment_label', 'N/A')}")
            
            return {
                'ticker': ticker,
                'calls_count': len(calls_df),
                'puts_count': len(puts_df),
                'sentiment_metrics': sentiment_metrics
            }
            
        except Exception as e:
            print(f"❌ Erreur pour {ticker}: {str(e)}")
            return None
    
    def _calculate_sentiment_metrics(self, ticker, calls_df, puts_df):
        """
        Calcule les métriques de sentiment basées sur les options
        """
        metrics = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat()
        }
        
        if calls_df.empty and puts_df.empty:
            return metrics
        
        try:
            # Volume total
            call_volume = calls_df['volume'].sum() if not calls_df.empty and 'volume' in calls_df else 0
            put_volume = puts_df['volume'].sum() if not puts_df.empty and 'volume' in puts_df else 0
            
            # Open Interest total
            call_oi = calls_df['openInterest'].sum() if not calls_df.empty and 'openInterest' in calls_df else 0
            put_oi = puts_df['openInterest'].sum() if not puts_df.empty and 'openInterest' in puts_df else 0
            
            # Ratio Put/Call (Volume)
            pcr_volume = put_volume / call_volume if call_volume > 0 else 0
            
            # Ratio Put/Call (Open Interest)
            pcr_oi = put_oi / call_oi if call_oi > 0 else 0
            
            # Implied Volatility moyenne
            call_iv = calls_df['impliedVolatility'].mean() if not calls_df.empty and 'impliedVolatility' in calls_df else 0
            put_iv = puts_df['impliedVolatility'].mean() if not puts_df.empty and 'impliedVolatility' in puts_df else 0
            
            # Déterminer le sentiment
            # PCR < 0.7 = Bullish (plus de calls)
            # PCR 0.7-1.0 = Neutral
            # PCR > 1.0 = Bearish (plus de puts)
            if pcr_volume < 0.7:
                sentiment = 'bullish'
                sentiment_score = 1 - pcr_volume
            elif pcr_volume > 1.0:
                sentiment = 'bearish'
                sentiment_score = -(pcr_volume - 1)
            else:
                sentiment = 'neutral'
                sentiment_score = 0
            
            metrics.update({
                'call_volume': int(call_volume),
                'put_volume': int(put_volume),
                'call_open_interest': int(call_oi),
                'put_open_interest': int(put_oi),
                'put_call_ratio_volume': round(pcr_volume, 3),
                'put_call_ratio_oi': round(pcr_oi, 3),
                'call_implied_volatility': round(call_iv, 4),
                'put_implied_volatility': round(put_iv, 4),
                'sentiment_label': sentiment,
                'sentiment_score': round(sentiment_score, 3),
                'total_contracts': int(call_volume + put_volume),
                'total_open_interest': int(call_oi + put_oi)
            })
            
            # Analyse par expiration (court terme vs long terme)
            if not calls_df.empty:
                near_term = calls_df[calls_df['expiration'] <= 
                    (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')]
                far_term = calls_df[calls_df['expiration'] > 
                    (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')]
                
                metrics['near_term_call_volume'] = int(near_term['volume'].sum() if not near_term.empty else 0)
                metrics['far_term_call_volume'] = int(far_term['volume'].sum() if not far_term.empty else 0)
            
            if not puts_df.empty:
                near_term = puts_df[puts_df['expiration'] <= 
                    (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')]
                far_term = puts_df[puts_df['expiration'] > 
                    (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')]
                
                metrics['near_term_put_volume'] = int(near_term['volume'].sum() if not near_term.empty else 0)
                metrics['far_term_put_volume'] = int(far_term['volume'].sum() if not far_term.empty else 0)
            
        except Exception as e:
            print(f"??????  Erreur calcul metrics: {str(e)}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _save_options_data(self, ticker, calls_df, puts_df, sentiment_metrics):
        """
        Sauvegarde les données d'options (V2: Daily + Latest)
        """
        # Timestamp complet pour archivage CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Date jour pour cache intelligent
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Sauvegarder les DataFrames (Archives)
        if not calls_df.empty:
            calls_file = os.path.join(self.output_dir, f'{ticker}_calls_{timestamp}.csv')
            calls_df.to_csv(calls_file, index=False)
        
        if not puts_df.empty:
            puts_file = os.path.join(self.output_dir, f'{ticker}_puts_{timestamp}.csv')
            puts_df.to_csv(puts_file, index=False)
        
        # 1. Sauvegarder DAILY Cache (pour le skip)
        daily_file = os.path.join(self.output_dir, f'{ticker}_sentiment_{today_str}.json')
        with open(daily_file, 'w') as f:
            json.dump(sentiment_metrics, f, indent=2)
            
        # 2. Sauvegarder ARCHIVE Timestamped (historique fin)
        metrics_file = os.path.join(self.output_dir, f'{ticker}_sentiment_{timestamp}.json')
        with open(metrics_file, 'w') as f:
            json.dump(sentiment_metrics, f, indent=2)
        
        # 3. Maintenir un fichier "latest" pour le dashboard
        latest_file = os.path.join(self.output_dir, f'{ticker}_latest_sentiment.json')
        with open(latest_file, 'w') as f:
            json.dump(sentiment_metrics, f, indent=2)
    
    def collect_all_companies(self, companies, days_forward=90):
        """
        Collecte les options pour toutes les compagnies
        """
        print("="*80)
        print("???? COLLECTEUR D'OPTIONS - SENTIMENT ANALYSIS")
        print(f"???? {len(companies)} compagnies ?? Options sur {days_forward} jours")
        print("="*80)
        
        start_time = time.time()
        results = []
        
        for i, company in enumerate(companies, 1):
            ticker = company['ticker']
            print(f"\n[{i}/{len(companies)}] Traitement de {ticker}...")
            
            result = self.get_options_data(ticker, days_forward)
            
            if result:
                results.append(result)
            
            # D??lai entre compagnies
            time.sleep(1)
        
        # Rapport final
        elapsed = (time.time() - start_time) / 60
        
        print("\n" + "="*80)
        print("??? COLLECTE D'OPTIONS TERMINÉE")
        print("="*80)
        print(f"???? Compagnies traitées: {len(results)}/{len(companies)}")
        print(f"???? Total Calls: {sum(r['calls_count'] for r in results)}")
        print(f"???? Total Puts: {sum(r['puts_count'] for r in results)}")
        print(f"??????  Durée: {elapsed:.1f} minutes")
        print("="*80)
        
        # Analyse de sentiment global
        print("\n???? SENTIMENT PAR COMPAGNIE:")
        print("-"*80)
        print(f"{'Ticker':<10} {'P/C Ratio':<12} {'Sentiment':<12} {'Score':<10} {'Volume':<10}")
        print("-"*80)
        
        for r in results:
            metrics = r['sentiment_metrics']
            pcr = metrics.get('put_call_ratio_volume', 0)
            sentiment = metrics.get('sentiment_label', 'N/A')
            score = metrics.get('sentiment_score', 0)
            volume = metrics.get('total_contracts', 0)
            
            print(f"{r['ticker']:<10} {pcr:<12.3f} {sentiment:<12} {score:<10.3f} {volume:<10}")
        
        print("-"*80)
        
        # Distribution des sentiments
        sentiment_counts = defaultdict(int)
        for r in results:
            sentiment = r['sentiment_metrics'].get('sentiment_label', 'unknown')
            sentiment_counts[sentiment] += 1
        
        print("\n???? DISTRIBUTION DES SENTIMENTS:")
        for sentiment, count in sentiment_counts.items():
            pct = (count / len(results) * 100) if results else 0
            print(f"   {sentiment.upper():<10}: {count} compagnies ({pct:.1f}%)")
        
        return results
    
    def generate_sentiment_report(self, results):
        """
        G??n??re un rapport de sentiment consolid??
        """
        report_file = os.path.join(self.output_dir, 'sentiment_report.json')
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_companies': len(results),
            'companies': []
        }
        
        for r in results:
            company_data = {
                'ticker': r['ticker'],
                'sentiment_metrics': r['sentiment_metrics']
            }
            report['companies'].append(company_data)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n???? Rapport sauvegard??: {report_file}")
        
        # Cr??er aussi un CSV pour analyse facile
        csv_file = os.path.join(self.output_dir, 'sentiment_summary.csv')
        summary_data = []
        
        for r in results:
            metrics = r['sentiment_metrics']
            summary_data.append({
                'ticker': r['ticker'],
                'put_call_ratio': metrics.get('put_call_ratio_volume', 0),
                'sentiment': metrics.get('sentiment_label', 'N/A'),
                'sentiment_score': metrics.get('sentiment_score', 0),
                'call_volume': metrics.get('call_volume', 0),
                'put_volume': metrics.get('put_volume', 0),
                'call_oi': metrics.get('call_open_interest', 0),
                'put_oi': metrics.get('put_open_interest', 0),
                'call_iv': metrics.get('call_implied_volatility', 0),
                'put_iv': metrics.get('put_implied_volatility', 0)
            })
        
        df = pd.DataFrame(summary_data)
        df.to_csv(csv_file, index=False)
        
        print(f"???? R??sum?? CSV: {csv_file}")


def main():
    """
    Collecte les options pour les compagnies AI/Finance
    """
    # Récupérer les compagnies
    all_companies = get_all_companies()
    
    # Filtrer uniquement les compagnies cotées (qui ont des options)
    # Exclure les startups privées comme OPENAI, ANTHROPIC, COHERE, MISTRAL
    public_companies = [c for c in all_companies 
                       if c['ticker'] not in ['OPENAI', 'ANTHROPIC', 'COHERE', 'MISTRAL']]
    
    print(f"\n???? Compagnies sélectionnées ({len(public_companies)}):")
    for c in public_companies:
        print(f"   ??? {c['ticker']:<6} - {c['name']}")
    
    # Créer le collecteur
    collector = OptionsCollector()
    
    # Collecter les donn??es
    results = collector.collect_all_companies(
        companies=public_companies,
        days_forward=90  # Options expirant dans les 90 prochains jours
    )
    
    # Générer le rapport
    if results:
        collector.generate_sentiment_report(results)


if __name__ == "__main__":
    main()
