#!/usr/bin/env python3
"""
💰 FINANCIAL COLLECTOR V1 - Collecte Données Fondamentales
--------------------------------------------------------------------
Récupère les données "Summary", "Financials" et "Analysis" de Yahoo Finance
pour enrichir l'analyse (P/E, Target Price, Recommendations, Revenues).

Usage:
    python collect_financials.py          # Collecter pour tous les tickers
    python collect_financials.py NVDA     # Collecter pour NVDA uniquement
"""
import sys
import os
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np

# Environment Detection
if os.path.exists('/data/scripts'):
    sys.path.insert(0, '/data/scripts')
    DATA_FILES_DIR = '/data/files'
else:
    # Local Windows
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Go up 2 levels: collection -> pipelines -> prod
    PIPELINES_DIR = os.path.dirname(CURRENT_DIR)
    PROD_ROOT = os.path.dirname(PIPELINES_DIR)
    PROJECT_ROOT = os.path.dirname(PROD_ROOT) # C:\n8n-local-stack
    
    # We need PROD_ROOT in sys.path to import from 'config'
    sys.path.insert(0, PROD_ROOT)
    DATA_FILES_DIR = os.path.join(PROJECT_ROOT, 'local_files')

# Yahoo Finance
try:
    import yfinance as yf
except ImportError:
    print("📦 Installation de yfinance...")
    os.system("pip install yfinance -q")
    import yfinance as yf

# Rich pour affichage
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from tqdm import tqdm
    RICH_AVAILABLE = True
except ImportError:
    print("📦 Installation de rich et tqdm...")
    os.system("pip install rich tqdm -q")
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from tqdm import tqdm
    RICH_AVAILABLE = True

from config.companies_config import get_all_companies, get_company_by_ticker

console = Console()

# Configuration
FINANCIALS_DIR = os.path.join(DATA_FILES_DIR, 'financials')
MAX_WORKERS = 8

class FinancialCollector:
    def __init__(self, ticker, company_name):
        self.ticker = ticker
        self.company_name = company_name
        self.output_file = os.path.join(FINANCIALS_DIR, f'{ticker}_financials.json')
    
    def collect(self):
        """Collecte toutes les données financières disponibles"""
        try:
            ticker_obj = yf.Ticker(self.ticker)
            
            # 1. Info / Summary / Analysis
            info = ticker_obj.info
            
            # Sélection des métriques clés pour alléger le JSON
            key_metrics = {
                # Valuation
                'marketCap': info.get('marketCap'),
                'trailingPE': info.get('trailingPE'),
                'forwardPE': info.get('forwardPE'),
                'pegRatio': info.get('pegRatio'),
                'priceToBook': info.get('priceToBook'),
                'enterpriseValue': info.get('enterpriseValue'),
                'enterpriseToEbitda': info.get('enterpriseToEbitda'),
                
                # Targets & Recommendations
                'targetHighPrice': info.get('targetHighPrice'),
                'targetLowPrice': info.get('targetLowPrice'),
                'targetMeanPrice': info.get('targetMeanPrice'),
                'targetMedianPrice': info.get('targetMedianPrice'),
                'currentPrice': info.get('currentPrice'),
                'recommendationKey': info.get('recommendationKey'),
                'recommendationMean': info.get('recommendationMean'),
                'numberOfAnalystOpinions': info.get('numberOfAnalystOpinions'),
                
                # Margins & Growth
                'profitMargins': info.get('profitMargins'),
                'grossMargins': info.get('grossMargins'),
                'operatingMargins': info.get('operatingMargins'),
                'revenueGrowth': info.get('revenueGrowth'),
                'earningsGrowth': info.get('earningsGrowth'),
                
                # Risk
                'auditRisk': info.get('auditRisk'),
                'boardRisk': info.get('boardRisk'),
                'compensationRisk': info.get('compensationRisk'),
                'shareHolderRightsRisk': info.get('shareHolderRightsRisk'),
                'overallRisk': info.get('overallRisk'),
                
                # Short Interest
                'shortRatio': info.get('shortRatio'),
                'shortPercentOfFloat': info.get('shortPercentOfFloat')
            }
            
            # 2. Financials (Income Statement, Balance Sheet) - Derniers disponibles
            financials_data = {}
            
            try:
                # Récupérer les 2 dernières années seulement pour limiter la taille
                income_stmt = ticker_obj.financials.iloc[:, :2] if not ticker_obj.financials.empty else pd.DataFrame()
                balance_sheet = ticker_obj.balance_sheet.iloc[:, :2] if not ticker_obj.balance_sheet.empty else pd.DataFrame()
                cash_flow = ticker_obj.cashflow.iloc[:, :2] if not ticker_obj.cashflow.empty else pd.DataFrame()
                
                # Helper pour convertir DataFrame en dict serializable (en gérant les timestamps)
                def df_to_dict(df):
                    if df.empty: return {}
                    # Convertir les index (dates) en str ISO
                    df.columns = [col.strftime('%Y-%m-%d') if isinstance(col, datetime) else str(col) for col in df.columns]
                    # Remplacer NaN par None
                    return df.replace({np.nan: None}).to_dict()

                financials_data['income_statement'] = df_to_dict(income_stmt)
                financials_data['balance_sheet'] = df_to_dict(balance_sheet)
                financials_data['cash_flow'] = df_to_dict(cash_flow)
                
            except Exception as e:
                print(f"⚠️ Erreur financials raw pour {self.ticker}: {e}")
            
            # 3. Earnings History (Surprises)
            earnings_history = []
            try:
                # Via info ou une autre méthode, yfinance a changé earnings_history récemment
                # On tente via calendar ou earnings_dates si dispo, sinon skip
                pass 
            except Exception:
                pass

            # Assemblage final
            final_data = {
                'ticker': self.ticker,
                'name': self.company_name,
                'collected_at': datetime.now().isoformat(),
                'metrics': key_metrics,
                'financials': financials_data,
                'currency': info.get('currency', 'USD')
            }
            
            # Calcul de l'upside potentiel
            if key_metrics['targetMeanPrice'] and key_metrics['currentPrice']:
                upside = (key_metrics['targetMeanPrice'] - key_metrics['currentPrice']) / key_metrics['currentPrice']
                final_data['metrics']['analyst_upside_potential'] = round(upside, 4)
            
            self._save(final_data)
            return {
                'ticker': self.ticker,
                'success': True,
                'data': final_data
            }
            
        except Exception as e:
            return {
                'ticker': self.ticker,
                'success': False,
                'error': str(e)
            }

    def _save(self, data):
        """Sauvegarde en JSON"""
        os.makedirs(FINANCIALS_DIR, exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def process_ticker(company):
    collector = FinancialCollector(company['ticker'], company['name'])
    return collector.collect()

def main():
    # Déterminer les tickers
    targets = []
    if len(sys.argv) > 1:
        req_ticker = sys.argv[1].upper()
        company = get_company_by_ticker(req_ticker)
        if company:
            targets = [company]
        else:
            targets = [{'ticker': req_ticker, 'name': req_ticker}] # Fallback custom ticker
    else:
        targets = get_all_companies()
    
    console.print("\n" + "="*70, style="bold green")
    console.print("💰 FINANCIAL COLLECTOR V1", style="bold green", justify="center")
    console.print("="*70, style="bold green")
    
    print(f"Output Directory: {FINANCIALS_DIR}")
    print(f"Cibles: {len(targets)} compagnies")
    
    start_time = time.time()
    results = []
    
    with tqdm(total=len(targets), desc="Collecte", unit="ticker", ncols=100) as pbar:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_ticker = {executor.submit(process_ticker, co): co for co in targets}
            
            for future in as_completed(future_to_ticker):
                company = future_to_ticker[future]
                try:
                    res = future.result()
                    results.append(res)
                    
                    if res['success']:
                        metrics = res['data']['metrics']
                        upside_str = ""
                        if metrics.get('analyst_upside_potential'):
                            up = metrics['analyst_upside_potential'] * 100
                            color = "green" if up > 0 else "red"
                            upside_str = f" | 🎯 Upside: [{color}]{up:+.1f}%[/{color}]"
                        
                        rec = metrics.get('recommendationMean', 'N/A')
                        
                        console.print(f"  ✅ [bold]{company['ticker']:<6}[/bold] | Rec: {rec} {upside_str}")
                    else:
                        console.print(f"  ❌ [bold]{company['ticker']:<6}[/bold] | Erreur: {res.get('error')}", style="red")
                        
                except Exception as e:
                    console.print(f"  ❌ {company['ticker']} | Exception: {e}", style="red")
                
                pbar.update(1)

    elapsed = time.time() - start_time
    success_count = sum(1 for r in results if r['success'])
    
    console.print("\n" + "="*70, style="bold green")
    console.print(f"🎉 Terminé en {elapsed:.1f}s | Succès: {success_count}/{len(targets)}", style="bold green", justify="center")
    console.print("="*70)

if __name__ == "__main__":
    main()
