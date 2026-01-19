# -*- coding: utf-8 -*-
"""
Beta Portfolio Calculator with Risk Metrics (Optimized)
Calcule le bêta, volatilité, et ratio de Sharpe du portefeuille Questrade
"""
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import json
import pandas as pd
import numpy as np
import yfinance as yf
from scipy import stats
from datetime import datetime, timedelta
import os
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
import sys
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Configuration
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

CONFIG = {
    'portfolio_holdings': 'prod/config/portfolio_holdings.json',
    'beta_results': 'prod/dashboards/assets/beta_results.json',
    'cache_dir': 'prod/dashboards/assets/.cache',
    'default_start_date': '2024-07-16',  # 6 mois au lieu de 1 an (plus rapide)
    'default_end_date': datetime.now().strftime('%Y-%m-%d'),
    'min_data_points': 30,
    'cad_benchmark': 'XIU.TO',
    'usd_benchmark': 'SPY',
    'risk_free_rate': 0.03,
    'trading_days_per_year': 252,
    'max_workers': 4,  # Parallélisation: 4 tickers simultanés
}


class BetaCalculator:
    """Calcule le bêta, volatilité et Sharpe d'un actif via régression linéaire"""
    
    def __init__(self, benchmark_symbol, start_date, end_date, risk_free_rate=0.03):
        """
        Initialise le calculateur avec un benchmark
        
        Args:
            benchmark_symbol: Symbole Yahoo Finance du benchmark (ex: 'XIU.TO', 'SPY')
            start_date: Date début au format 'YYYY-MM-DD'
            end_date: Date fin au format 'YYYY-MM-DD'
            risk_free_rate: Taux sans risque annuel (ex: 0.03 pour 3%)
        """
        self.benchmark_symbol = benchmark_symbol
        self.start_date = start_date
        self.end_date = end_date
        self.risk_free_rate = risk_free_rate
        self.market_data = None
        self.benchmark_metrics = None
        self._cache_key = f"{benchmark_symbol}_{start_date}_{end_date}"
        self._download_benchmark()
    
    def _get_cache_path(self, name):
        """Retourne le chemin du fichier cache"""
        os.makedirs(CONFIG['cache_dir'], exist_ok=True)
        return os.path.join(CONFIG['cache_dir'], f"{name}.pkl")
    
    def _load_cached_data(self):
        """Charge les données du benchmark depuis le cache si disponible"""
        cache_path = self._get_cache_path(self._cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                    print(f"✅ Cache hit: {self.benchmark_symbol}")
                    return data
            except:
                pass
        return None
    
    def _save_cached_data(self, data):
        """Sauvegarde les données du benchmark dans le cache"""
        cache_path = self._get_cache_path(self._cache_key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except:
            pass
    
    def _download_benchmark(self):
        """Télécharge et cache les rendements du benchmark"""
        # Essayer le cache d'abord
        cached_data = self._load_cached_data()
        if cached_data is not None:
            self.market_data = cached_data['market_data']
            self.benchmark_metrics = cached_data['metrics']
            return
        
        print(f"Telechargement benchmark: {self.benchmark_symbol}...", end='', flush=True)
        try:
            df = yf.download(
                self.benchmark_symbol, 
                start=self.start_date, 
                end=self.end_date,
                progress=False
            )
            if df.empty:
                print(f" ERREUR: Aucune donnee")
                self.market_data = None
                return
            
            # Gérer différentes formats de colonnes yfinance
            # yfinance peut retourner un MultiIndex si plusieurs tickers sont téléchargés
            # ou même pour un seul ticker dans certaines versions
            price_series = None
            
            if isinstance(df.columns, pd.MultiIndex):
                # Multi-index: colonnes comme (Close, SPY), (High, SPY), etc.
                if 'Close' in df.columns.get_level_values(0):
                    price_series = df['Close'].iloc[:, 0]  # Prendre la première colonne
                elif len(df.columns) > 0:
                    price_series = df.iloc[:, 0]  # Prendre la première colonne disponible
            else:
                # Index simple: colonnes comme 'Close', 'High', etc.
                if 'Adj Close' in df.columns:
                    price_series = df['Adj Close']
                elif 'Close' in df.columns:
                    price_series = df['Close']
                elif len(df.columns) > 0:
                    price_series = df.iloc[:, 0]
            
            if price_series is None or len(price_series) == 0:
                print(f" ERREUR: Format colonne non reconnu: {df.columns.tolist()}")
                self.market_data = None
                return
            
            # S'assurer que c'est une Series
            if isinstance(price_series, pd.DataFrame):
                price_series = price_series.iloc[:, 0]
            
            # Calculer rendements arithmétiques quotidiens
            self.market_data = price_series.pct_change().dropna()
            
            # Calculer les métriques du benchmark
            mean_return_daily = float(self.market_data.mean())
            mean_return_annual = mean_return_daily * CONFIG['trading_days_per_year']
            volatility_daily = float(self.market_data.std())
            volatility_annual = volatility_daily * np.sqrt(CONFIG['trading_days_per_year'])
            
            self.benchmark_metrics = {
                'mean_return_annual': mean_return_annual,
                'volatility_annual': volatility_annual,
                'volatility_daily': volatility_daily
            }
            
            # Sauvegarder dans le cache
            self._save_cached_data({
                'market_data': self.market_data,
                'metrics': self.benchmark_metrics
            })
            
            print(f" ✅ ({len(self.market_data)} jours)")
            
        except Exception as e:
            print(f" ❌ Erreur: {e}")
            self.market_data = None
    
    def calculate_beta(self, ticker):
        """
        Calcule le bêta, volatilité et ratio de Sharpe d'un ticker
        
        Args:
            ticker: Symbole Yahoo Finance (ex: 'AAPL', 'RY.TO')
        
        Returns:
            dict: Dictionnaire avec bêta, alpha, R², volatilité, Sharpe, etc.
        """
        if self.market_data is None or self.benchmark_metrics is None:
            return {
                'beta': 0,
                'alpha': 0,
                'r_squared': 0,
                'volatility': 0,
                'sharpe': 0,
                'error': 'Benchmark data unavailable'
            }
        
        # Télécharger les données du titre
        try:
            stock_df = yf.download(
                ticker,
                start=self.start_date,
                end=self.end_date,
                progress=False
            )
            
            if stock_df.empty:
                return {
                    'beta': 0,
                    'alpha': 0,
                    'r_squared': 0,
                    'volatility': 0,
                    'sharpe': 0,
                    'error': 'No data found'
                }
            
            # Gérer différentes formats de colonnes yfinance
            # yfinance peut retourner un MultiIndex même pour un seul ticker
            price_series = None
            
            if isinstance(stock_df.columns, pd.MultiIndex):
                # Multi-index: colonnes comme (Close, NVDA), (High, NVDA), etc.
                if 'Close' in stock_df.columns.get_level_values(0):
                    price_series = stock_df['Close'].iloc[:, 0]
                elif len(stock_df.columns) > 0:
                    price_series = stock_df.iloc[:, 0]
            else:
                # Index simple
                if 'Adj Close' in stock_df.columns:
                    price_series = stock_df['Adj Close']
                elif 'Close' in stock_df.columns:
                    price_series = stock_df['Close']
                elif len(stock_df.columns) > 0:
                    price_series = stock_df.iloc[:, 0]
            
            if price_series is None or len(price_series) == 0:
                return {
                    'beta': 0,
                    'alpha': 0,
                    'r_squared': 0,
                    'volatility': 0,
                    'sharpe': 0,
                    'error': 'No price series found'
                }
            
            # S'assurer que c'est une Series
            if isinstance(price_series, pd.DataFrame):
                price_series = price_series.iloc[:, 0]
            
            stock_returns = price_series.pct_change().dropna()
            
            if stock_returns is None or len(stock_returns) == 0:
                print(f"  Erreur {ticker}: Pas de series de retours")
                return {
                    'beta': 0,
                    'alpha': 0,
                    'r_squared': 0,
                    'volatility': 0,
                    'sharpe': 0,
                    'error': 'No returns series'
                }
            
        except Exception as e:
            print(f"  ⚠️  {ticker}: Erreur - {e}")
            return {
                'beta': 0,
                'alpha': 0,
                'r_squared': 0,
                'volatility': 0,
                'sharpe': 0,
                'error': str(e)
            }
        
        # Synchroniser les dates (intersection)
        # Aligner les deux Series par index - utiliser inner join pour garder seulement les dates communes
        # stock_returns et self.market_data doivent avoir le même index (dates)
        try:
            data = pd.concat([stock_returns, self.market_data], axis=1, keys=['Stock', 'Market'], join='inner').dropna()
        except Exception as align_err:
            print(f"  Erreur {ticker}: Concat - {align_err}")
            return {
                'beta': 0,
                'alpha': 0,
                'r_squared': 0,
                'volatility': 0,
                'sharpe': 0,
                'error': f'Concat error: {str(align_err)[:50]}'
            }
        
        if len(data) == 0 or data.shape[1] != 2:
            print(f"  Erreur {ticker}: Impossible d'aligner donnees (stock={len(stock_returns)}, market={len(self.market_data)})")
            return {
                'beta': 0,
                'alpha': 0,
                'r_squared': 0,
                'volatility': 0,
                'sharpe': 0,
                'error': 'Data alignment failed'
            }
        
        # Vérifier le nombre minimum de points
        if len(data) < CONFIG['min_data_points']:
            print(f"  ⚠️  {ticker}: Données insuffisantes (n={len(data)} < {CONFIG['min_data_points']})")
            return {
                'beta': 1.0,
                'alpha': 0,
                'r_squared': 0,
                'volatility': 0,
                'sharpe': 0,
                'warning': f'Insufficient data (n={len(data)})'
            }
        
        # Régression linéaire (OLS) pour BÊTA
        try:
            result = stats.linregress(
                data['Market'].values,
                data['Stock'].values
            )
            # Gérer les versions scipy antérieures et nouvelles
            slope = result.slope if hasattr(result, 'slope') else result[0]
            intercept = result.intercept if hasattr(result, 'intercept') else result[1]
            r_value = result.rvalue if hasattr(result, 'rvalue') else result[2]
            p_value = result.pvalue if hasattr(result, 'pvalue') else result[3]
            std_err = result.stderr if hasattr(result, 'stderr') else result[4]
            
            beta = float(slope)
            alpha = float(intercept)
            r_squared = float(r_value ** 2)
            correlation = float(data['Stock'].corr(data['Market']))
            
            # VOLATILITÉ annualisée
            sigma_stock_daily = float(data['Stock'].std())
            sigma_stock_annual = sigma_stock_daily * np.sqrt(CONFIG['trading_days_per_year'])
            
            # RENDEMENT MOYEN annualisé
            mean_return_daily = float(data['Stock'].mean())
            mean_return_annual = mean_return_daily * CONFIG['trading_days_per_year']
            
            # RATIO DE SHARPE
            if sigma_stock_annual > 0:
                sharpe_ratio = (mean_return_annual - self.risk_free_rate) / sigma_stock_annual
            else:
                sharpe_ratio = 0.0
            
            # Volatilités et ratios
            sigma_market = self.benchmark_metrics['volatility_daily']
            sigma_market_annual = sigma_market * np.sqrt(CONFIG['trading_days_per_year'])
            
            result = {
                'beta': beta,
                'alpha': alpha,
                'r_squared': r_squared,
                'correlation': correlation,
                'p_value': float(p_value),
                'std_err': float(std_err),
                'volatility_daily': sigma_stock_daily,
                'volatility_annual': sigma_stock_annual,
                'volatility_market_annual': sigma_market_annual,
                'mean_return_annual': mean_return_annual,
                'sharpe_ratio': sharpe_ratio,
                'risk_free_rate': self.risk_free_rate,
                'n_obs': len(data),
                'status': 'success'
            }
            
            return result
            
        except Exception as e:
            print(f"  ⚠️  {ticker}: Erreur régression - {e}")
            return {
                'beta': 0,
                'alpha': 0,
                'r_squared': 0,
                'volatility': 0,
                'sharpe': 0,
                'error': str(e)
            }


def load_portfolio():
    """Charge le portefeuille depuis le fichier JSON"""
    try:
        with open(CONFIG['portfolio_holdings'], 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {CONFIG['portfolio_holdings']}")
        return []


def detect_benchmark(symbol):
    """
    Détecte le benchmark approprié pour un symbole
    
    Args:
        symbol: Symbole Yahoo (ex: 'RY.TO' ou 'AAPL')
    
    Returns:
        str: Benchmark symbole ('XIU.TO' ou 'SPY')
    """
    if symbol.endswith('.TO') or symbol.endswith('.V'):
        return CONFIG['cad_benchmark']
    else:
        return CONFIG['usd_benchmark']


def analyze_portfolio(positions=None, start_date=None, end_date=None):
    """
    Analyse complète du portefeuille avec parallélisation
    
    Args:
        positions: Liste des positions (si None, charge depuis fichier)
        start_date: Date de début (si None, utilise CONFIG)
        end_date: Date de fin (si None, utilise CONFIG)
    
    Returns:
        tuple: (DataFrame résultats, métriques pondérées, détails)
    """
    # Charger les paramètres par défaut
    if positions is None:
        positions = load_portfolio()
    
    if not positions:
        print("ERREUR: Aucune position a analyser")
        return None, None, None
    
    start_date = start_date or CONFIG['default_start_date']
    end_date = end_date or CONFIG['default_end_date']
    
    print(f"\nANALYSE PORTFOLIO (OPTIMISE)")
    print(f"   Periode: {start_date} -> {end_date}")
    print(f"   Positions: {len(positions)}")
    print(f"   Taux sans risque: {CONFIG['risk_free_rate']*100:.1f}%")
    print(f"   Mode: Parallelise ({CONFIG['max_workers']} workers)")
    print("-" * 90)
    
    # Initialiser les calculateurs par benchmark
    calculators = {}
    
    # Calcul de la valeur totale
    total_value = sum(p.get('currentMarketValue', 0) for p in positions if p.get('ticker') != 'CASH')
    
    # Préparer les tâches de calcul
    tasks = []
    position_map = {}
    
    start_time = time.time()
    
    # Créer les calculateurs
    for benchmark in [CONFIG['cad_benchmark'], CONFIG['usd_benchmark']]:
        if benchmark not in calculators:
            calculators[benchmark] = BetaCalculator(
                benchmark, 
                start_date, 
                end_date,
                risk_free_rate=CONFIG['risk_free_rate']
            )
    
    print()
    
    # Préparer les tâches pour parallélisation
    with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        for idx, position in enumerate(positions):
            ticker = position.get('ticker')
            
            if ticker == 'CASH' or not ticker:
                continue
            
            benchmark = detect_benchmark(ticker)
            calculator = calculators[benchmark]
            
            # Soumettre la tâche
            future = executor.submit(calculator.calculate_beta, ticker)
            tasks.append((ticker, position, future, benchmark))
        
        # Traiter les résultats au fur et à mesure
        results = []
        weighted_metrics = {
            'beta': 0.0,
            'volatility': 0.0,
            'sharpe': 0.0,
            'mean_return': 0.0
        }
        
        completed = 0
        for ticker, position, future, benchmark in tasks:
            market_value = position.get('currentMarketValue', 0)
            qty = position.get('qty', 0)
            avg_price = position.get('avg_price', 0)
            weight = market_value / total_value if total_value > 0 else 0
            
            # Attendre le résultat
            metrics = future.result()
            completed += 1
            
            print(f"[{completed}/{len(tasks)}] {ticker:10s} ", end='', flush=True)
            
            beta = metrics.get('beta', 0)
            r_squared = metrics.get('r_squared', 0)
            volatility_annual = metrics.get('volatility_annual', 0)
            sharpe_ratio = metrics.get('sharpe_ratio', 0)
            mean_return_annual = metrics.get('mean_return_annual', 0)
            status = metrics.get('status', metrics.get('error', 'error'))
            
            # Contribution au risque
            risk_contribution = beta * weight
            
            # Contribution aux métriques pondérées
            weighted_metrics['beta'] += beta * weight
            weighted_metrics['volatility'] += volatility_annual * weight
            weighted_metrics['sharpe'] += sharpe_ratio * weight
            weighted_metrics['mean_return'] += mean_return_annual * weight
            
            # Couleur de sortie
            if beta > 1.2:
                risk_level = "🔴"
            elif beta > 0.8:
                risk_level = "🟡"
            else:
                risk_level = "🟢"
            
            sharpe_status = "✅" if sharpe_ratio > 0.5 else "⚠️" if sharpe_ratio > 0 else "❌"
            
            print(f"β={beta:6.2f} Vol={volatility_annual*100:5.1f}% Sharpe={sharpe_ratio:5.2f} {sharpe_status} {risk_level}")
            
            results.append({
                'Ticker': ticker,
                'Qty': qty,
                'Avg Price': f"${avg_price:.2f}",
                'Market Value': f"${market_value:,.2f}",
                'Weight (%)': round(weight * 100, 2),
                'Beta': round(beta, 3),
                'Volatilité (%)': round(volatility_annual * 100, 2),
                'Sharpe': round(sharpe_ratio, 2),
                'Rendement (%)': round(mean_return_annual * 100, 2),
                'Risk Contrib.': round(risk_contribution, 4),
                'R²': round(r_squared, 3) if r_squared > 0 else '-',
                'Benchmark': benchmark,
                'Status': status
            })
        
        # Ajouter cash
        cash_positions = [p for p in positions if p.get('ticker') == 'CASH' or not p.get('ticker')]
        for position in cash_positions:
            market_value = position.get('currentMarketValue', 0)
            qty = position.get('qty', 0)
            avg_price = position.get('avg_price', 0)
            weight = market_value / total_value if total_value > 0 else 0
            
            results.append({
                'Ticker': position.get('ticker') or 'CASH',
                'Qty': qty,
                'Avg Price': avg_price,
                'Market Value': f"${market_value:,.2f}",
                'Weight (%)': round(weight * 100, 2),
                'Beta': '-',
                'Volatilité (%)': '-',
                'Sharpe': '-',
                'Rendement (%)': '-',
                'Risk Contrib.': '-',
                'R²': '-',
                'Status': 'Cash'
            })
    
    elapsed = time.time() - start_time
    
    # Créer le DataFrame
    df_results = pd.DataFrame(results)
    
    print("-" * 90)
    print(f"⏱️  Temps d'exécution: {elapsed:.1f}s")
    print(f"📈 MÉTRIQUES PONDÉRÉES DU PORTEFEUILLE:")
    print(f"   Bêta:                {weighted_metrics['beta']:.3f}")
    print(f"   Volatilité:          {weighted_metrics['volatility']*100:.2f}%")
    print(f"   Rendement annuel:    {weighted_metrics['mean_return']*100:.2f}%")
    print(f"   Ratio de Sharpe:     {weighted_metrics['sharpe']:.3f}")
    print("-" * 90)
    
    # Analyser le bêta du portefeuille
    portfolio_beta = weighted_metrics['beta']
    if portfolio_beta > 1.2:
        characterization = "🔴 AGRESSIF (Amplifie les mouvements de marché)"
    elif portfolio_beta > 0.8:
        characterization = "🟡 NEUTRE (Suit le marché)"
    elif portfolio_beta > 0:
        characterization = "🟢 DÉFENSIF (Amortit les mouvements)"
    else:
        characterization = "⚫ COUVERTURE (Corrélation inverse)"
    
    # Analyser le Sharpe
    sharpe_ratio = weighted_metrics['sharpe']
    if sharpe_ratio > 1.0:
        sharpe_comment = "✅ EXCELLENT (Rendement justifie le risque)"
    elif sharpe_ratio > 0.5:
        sharpe_comment = "🟡 BON (Rapport risque/rendement acceptable)"
    elif sharpe_ratio > 0:
        sharpe_comment = "⚠️ FAIBLE (Peu de rendement pour le risque)"
    else:
        sharpe_comment = "❌ MAUVAIS (Rendement < taux sans risque)"
    
    print(f"\nCaractérisation:")
    print(f"  Bêta:        {characterization}")
    print(f"  Sharpe:      {sharpe_comment}")
    
    details = {
        'portfolio_beta': float(portfolio_beta),
        'portfolio_volatility': float(weighted_metrics['volatility']),
        'portfolio_sharpe': float(weighted_metrics['sharpe']),
        'portfolio_return': float(weighted_metrics['mean_return']),
        'characterization': characterization,
        'sharpe_comment': sharpe_comment,
        'total_value': total_value,
        'n_positions': len(positions),
        'risk_free_rate': CONFIG['risk_free_rate'],
        'execution_time': elapsed,
        'analysis_date': datetime.now().isoformat(),
        'period': f"{start_date} to {end_date}"
    }
    
    return df_results, weighted_metrics, details


def save_results(df_results, portfolio_metrics, details):
    """Sauvegarde les résultats en JSON et CSV"""
    
    # Préparer les données pour JSON
    results_json = {
        'metadata': details,
        'positions': df_results.to_dict(orient='records'),
        'summary': {
            'portfolio_beta': portfolio_metrics['beta'],
            'portfolio_volatility': portfolio_metrics['volatility'],
            'portfolio_sharpe': portfolio_metrics['sharpe'],
            'portfolio_return_annual': portfolio_metrics['mean_return'],
            'characterization': details.get('characterization'),
            'sharpe_comment': details.get('sharpe_comment'),
            'analysis_timestamp': datetime.now().isoformat()
        }
    }
    
    # Sauvegarder en JSON
    os.makedirs(os.path.dirname(CONFIG['beta_results']), exist_ok=True)
    with open(CONFIG['beta_results'], 'w') as f:
        json.dump(results_json, f, indent=2)
    print(f"\n✅ Résultats sauvegardés: {CONFIG['beta_results']}")
    
    # Sauvegarder en CSV aussi (pour Excel)
    csv_path = CONFIG['beta_results'].replace('.json', '.csv')
    df_results.to_csv(csv_path, index=False)
    print(f"✅ Résultats CSV: {csv_path}")


def display_top_risk_contributors(df_results, top_n=5):
    """Affiche les principaux contributeurs de risque"""
    
    # Convertir en numérique
    df_risk = df_results.copy()
    df_risk['Risk Contrib.'] = pd.to_numeric(df_risk['Risk Contrib.'], errors='coerce')
    
    top_contributors = df_risk.nlargest(top_n, 'Risk Contrib.')
    
    print(f"\n🎯 Top {top_n} Contributeurs de Risque Systématique")
    print("-" * 70)
    
    for idx, (_, row) in enumerate(top_contributors.iterrows(), 1):
        ticker = row['Ticker']
        contrib = row['Risk Contrib.']
        weight = row['Weight (%)']
        beta = row['Beta']
        
        print(f"{idx}. {ticker:10s} → {contrib:8.4f} (Poids: {weight:5.1f}%, β={beta:6.2f})")


def display_top_sharpe(df_results, top_n=5):
    """Affiche les meilleures positions par ratio de Sharpe"""
    
    # Convertir en numérique
    df_sharpe = df_results.copy()
    df_sharpe['Sharpe'] = pd.to_numeric(df_sharpe['Sharpe'], errors='coerce')
    
    top_sharpe = df_sharpe.nlargest(top_n, 'Sharpe')
    
    print(f"\n🏆 Top {top_n} Positions par Ratio de Sharpe")
    print("-" * 70)
    
    for idx, (_, row) in enumerate(top_sharpe.iterrows(), 1):
        ticker = row['Ticker']
        sharpe = row['Sharpe']
        volatility = row['Volatilité (%)']
        return_pct = row['Rendement (%)']
        
        sharpe_status = "✅" if sharpe > 0.5 else "⚠️" if sharpe > 0 else "❌"
        
        print(f"{idx}. {ticker:10s} → Sharpe: {sharpe:6.2f} {sharpe_status} " + 
              f"(Vol: {volatility:5.1f}%, Return: {return_pct:+6.2f}%)")


def main():
    """Fonction principale"""
    
    print("\n" + "=" * 90)
    print("PORTFOLIO RISK ANALYZER - Beta, Volatility & Sharpe Ratio")
    print("Questrade Integration via Python")
    print("=" * 90)
    
    # Analyser le portefeuille
    df_results, portfolio_metrics, details = analyze_portfolio()
    
    if df_results is None:
        return
    
    # Afficher les résultats
    print("\n📊 RÉSULTATS DÉTAILLÉS PAR POSITION:")
    print(df_results.to_string(index=False))
    
    # Top contributeurs
    display_top_risk_contributors(df_results, top_n=5)
    
    # Top par Sharpe
    display_top_sharpe(df_results, top_n=5)
    
    # Sauvegarder
    save_results(df_results, portfolio_metrics, details)
    
    print("\n" + "=" * 90)
    print("✅ Analyse complète!")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
