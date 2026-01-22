# -*- coding: utf-8 -*-
"""
Dashboard Benchmark V2 - Avec Risk Analytics Intégrés
=====================================================
Version améliorée avec:
- Beta (β) - Risque systématique  
- Volatilité (σ) - Risque total annualisé
- Ratio de Sharpe - Rendement ajusté au risque
- Rolling Beta (fenêtre glissante)
- Heatmap des corrélations
- Drawdown Analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from scipy import stats
import sys
import os

# Configuration pour importer companies_config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from prod.config.companies_config import AI_COMPANIES

# Setup Streamlit
st.set_page_config(
    page_title="Benchmark Pro v2 - Risk Analytics", 
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Force Dark Mode for Plotly
import plotly.io as pio
pio.templates.default = "plotly_dark"

# ==================== CONSTANTS ====================
TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE = 0.03  # 3% annuel

# ==================== UTILITY FUNCTIONS ====================

def get_tickers():
    """Extract tickers from config"""
    tickers = [c['ticker'] for c in AI_COMPANIES if c.get('ticker')]
    return sorted(list(set(tickers)))

def get_portfolio_tickers():
    """Get tickers from Questrade portfolio"""
    portfolio = load_portfolio_config()
    return [item['ticker'] for item in portfolio]

def get_all_tickers_no_duplicates():
    """Get all tickers (portfolio + watchlist) without duplicates"""
    portfolio_tickers = get_portfolio_tickers()
    watchlist_tickers = get_tickers()
    
    # Combine and remove duplicates
    all_tickers = list(set(portfolio_tickers + watchlist_tickers))
    return sorted(all_tickers)

def get_watchlist_only():
    """Get tickers from watchlist that are NOT in portfolio (no duplicates)"""
    portfolio_tickers = set(get_portfolio_tickers())
    watchlist_tickers = get_tickers()
    
    # Filter out portfolio tickers
    watchlist_only = [t for t in watchlist_tickers if t not in portfolio_tickers]
    return sorted(watchlist_only)

def load_portfolio_config():
    """Load portfolio data from JSON"""
    portfolio_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../prod/config/portfolio_holdings.json'))
    if os.path.exists(portfolio_file):
        with open(portfolio_file, 'r') as f:
            return json.load(f)
    return []

def extract_price_series(df, ticker):
    """Extrait une Series de prix depuis un DataFrame yfinance (gère MultiIndex)"""
    if df is None or df.empty:
        return None
    
    if isinstance(df.columns, pd.MultiIndex):
        if 'Close' in df.columns.get_level_values(0):
            if ticker in df['Close'].columns:
                return df['Close'][ticker]
            elif df['Close'].shape[1] == 1:
                return df['Close'].iloc[:, 0]
        return df.iloc[:, 0]
    else:
        if ticker in df.columns:
            return df[ticker]
        elif 'Close' in df.columns:
            return df['Close']
    return None

@st.cache_data(ttl=300)
def load_data_single(ticker, benchmark, start_date):
    """Fetch data from Yahoo Finance pour un seul ticker"""
    tickers = [ticker, benchmark]
    try:
        data = yf.download(tickers, start=start_date, progress=False)
        if data.empty:
            return None
        
        # Extraire les prix Close
        result = pd.DataFrame()
        for t in tickers:
            series = extract_price_series(data, t)
            if series is not None:
                result[t] = series
        
        return result.dropna() if not result.empty else None
    except Exception as e:
        st.error(f"Erreur de chargement: {e}")
        return None

@st.cache_data(ttl=300)
def load_data_batch(tickers, start_date):
    """Fetch data from Yahoo Finance pour plusieurs tickers"""
    try:
        data = yf.download(tickers, start=start_date, progress=False)
        if data.empty:
            return None
        
        # Extraire les prix Close pour chaque ticker
        result = pd.DataFrame()
        for t in tickers:
            series = extract_price_series(data, t)
            if series is not None:
                result[t] = series
        
        return result.ffill().dropna() if not result.empty else None
    except Exception as e:
        st.error(f"Erreur téléchargement batch: {e}")
        return None

# ==================== RISK ANALYTICS ====================

def calculate_beta(stock_returns, market_returns):
    """Calcule le bêta via régression linéaire"""
    if len(stock_returns) < 30 or len(market_returns) < 30:
        return 0, 0, 0
    
    # Aligner les données
    data = pd.concat([stock_returns.rename('stock'), market_returns.rename('market')], 
                     axis=1, join='inner').dropna()
    
    if len(data) < 30:
        return 0, 0, 0
    
    try:
        result = stats.linregress(data['market'].values, data['stock'].values)
        beta = result.slope if hasattr(result, 'slope') else result[0]
        alpha = result.intercept if hasattr(result, 'intercept') else result[1]
        r_squared = (result.rvalue if hasattr(result, 'rvalue') else result[2]) ** 2
        return float(beta), float(alpha), float(r_squared)
    except:
        return 0, 0, 0

def calculate_volatility(returns, annualize=True):
    """Calcule la volatilité (écart-type des rendements)"""
    if returns is None or len(returns) < 2:
        return 0
    vol = returns.std()
    if annualize:
        vol = vol * np.sqrt(TRADING_DAYS_PER_YEAR)
    return float(vol)

def calculate_sharpe_ratio(returns, risk_free_rate=RISK_FREE_RATE):
    """Calcule le ratio de Sharpe annualisé"""
    if returns is None or len(returns) < 30:
        return 0
    
    mean_return = returns.mean() * TRADING_DAYS_PER_YEAR
    volatility = returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    if volatility == 0:
        return 0
    
    sharpe = (mean_return - risk_free_rate) / volatility
    return float(sharpe)

def calculate_rolling_beta(stock_returns, market_returns, window=60):
    """Calcule le bêta rolling sur une fenêtre glissante"""
    data = pd.concat([stock_returns.rename('stock'), market_returns.rename('market')], 
                     axis=1, join='inner').dropna()
    
    if len(data) < window:
        return pd.Series(dtype=float)
    
    rolling_beta = []
    dates = []
    
    for i in range(window, len(data)):
        window_data = data.iloc[i-window:i]
        try:
            result = stats.linregress(window_data['market'].values, window_data['stock'].values)
            beta = result.slope if hasattr(result, 'slope') else result[0]
            rolling_beta.append(beta)
            dates.append(data.index[i])
        except:
            rolling_beta.append(np.nan)
            dates.append(data.index[i])
    
    return pd.Series(rolling_beta, index=dates)

def calculate_max_drawdown(prices):
    """Calcule le drawdown maximum"""
    if prices is None or len(prices) < 2:
        return 0, None, None
    
    peak = prices.expanding(min_periods=1).max()
    drawdown = (prices - peak) / peak
    max_dd = drawdown.min()
    
    return float(max_dd), drawdown, peak

def calculate_sortino_ratio(returns, risk_free_rate=RISK_FREE_RATE):
    """Calcule le ratio de Sortino (ne pénalise que la volatilité négative)"""
    if returns is None or len(returns) < 30:
        return 0
    
    mean_return = returns.mean() * TRADING_DAYS_PER_YEAR
    downside_returns = returns[returns < 0]
    
    if len(downside_returns) == 0:
        return 0
    
    downside_vol = downside_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    if downside_vol == 0:
        return 0
    
    sortino = (mean_return - risk_free_rate) / downside_vol
    return float(sortino)

def get_risk_color(value, metric_type):
    """Retourne une couleur selon la valeur du risque"""
    if metric_type == 'beta':
        if value > 1.5: return "#FF5252"  # Rouge - Très agressif
        if value > 1.2: return "#FF9800"  # Orange - Agressif
        if value > 0.8: return "#FFEB3B"  # Jaune - Neutre
        if value > 0.5: return "#8BC34A"  # Vert clair - Défensif
        return "#4CAF50"  # Vert - Très défensif
    
    elif metric_type == 'sharpe':
        if value > 1.5: return "#4CAF50"  # Vert - Excellent
        if value > 1.0: return "#8BC34A"  # Vert clair - Très bon
        if value > 0.5: return "#FFEB3B"  # Jaune - Acceptable
        if value > 0: return "#FF9800"   # Orange - Faible
        return "#FF5252"  # Rouge - Mauvais
    
    elif metric_type == 'volatility':
        if value > 0.5: return "#FF5252"  # Rouge - Très volatile
        if value > 0.3: return "#FF9800"  # Orange - Volatile
        if value > 0.2: return "#FFEB3B"  # Jaune - Modéré
        return "#4CAF50"  # Vert - Stable
    
    return "#FFFFFF"

# ==================== UI COMPONENTS ====================

def render_risk_gauge(value, title, min_val, max_val, metric_type):
    """Crée un gauge plotly pour visualiser une métrique de risque"""
    color = get_risk_color(value, metric_type)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 14}},
        number={'font': {'size': 24}},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [min_val, max_val * 0.33], 'color': 'rgba(76, 175, 80, 0.3)'},
                {'range': [max_val * 0.33, max_val * 0.66], 'color': 'rgba(255, 235, 59, 0.3)'},
                {'range': [max_val * 0.66, max_val], 'color': 'rgba(255, 82, 82, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 2},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'}
    )
    
    return fig

def render_risk_metrics_card(beta, volatility, sharpe, sortino=None, max_dd=None):
    """Affiche les métriques de risque dans une carte stylisée - tout sur une ligne"""
    
    # Interpréter le Beta
    if beta > 1.2:
        beta_desc = "🔴 Agressif"
    elif beta > 0.8:
        beta_desc = "🟡 Neutre"
    elif beta > 0:
        beta_desc = "🟢 Défensif"
    else:
        beta_desc = "⚫ Couverture"
    
    # Interpréter le Sharpe
    if sharpe > 1.0:
        sharpe_desc = "✅ Excellent"
    elif sharpe > 0.5:
        sharpe_desc = "🟡 Bon"
    elif sharpe > 0:
        sharpe_desc = "⚠️ Faible"
    else:
        sharpe_desc = "❌ Mauvais"
    
    # Textes d'aide détaillés
    beta_help = """
**Beta (β) - Risque Systématique**

Le beta mesure la sensibilité d'un actif aux mouvements du marché.

📊 **Interprétation:**
- **β > 1.5**: Très agressif - Amplifie fortement les mouvements du marché
- **β = 1.2-1.5**: Agressif - Amplifie les mouvements
- **β = 0.8-1.2**: Neutre - Suit le marché
- **β = 0.5-0.8**: Défensif - Amortit les mouvements
- **β < 0.5**: Très défensif - Protection contre la volatilité
- **β < 0**: Couverture - Corrélation inverse (rare)

📈 **Formule:** β = Cov(Ri, Rm) / Var(Rm)

💡 **Usage:** Un portefeuille avec β=1.2 gagnera ~12% si le marché monte de 10%, mais perdra ~12% si le marché baisse de 10%.
"""
    
    volatility_help = """
**Volatilité (σ) - Risque Total**

La volatilité mesure l'amplitude des variations de prix. C'est l'écart-type des rendements annualisé.

📊 **Interprétation:**
- **< 15%**: Faible volatilité (obligations, utilities)
- **15-25%**: Modérée (blue chips, ETF diversifiés)
- **25-40%**: Élevée (tech, growth stocks)
- **> 40%**: Très élevée (crypto, small caps, meme stocks)

📈 **Formule:** σ_annuel = σ_quotidien × √252

💡 **Usage:** Une volatilité de 30% signifie que le prix peut varier de ±30% autour de sa moyenne sur un an (intervalle de confiance 68%).
"""
    
    sharpe_help = """
**Ratio de Sharpe - Rendement Ajusté au Risque**

Le Sharpe ratio mesure le rendement excédentaire par unité de risque. C'est LA métrique clé pour comparer des investissements.

📊 **Interprétation:**
- **> 2.0**: Exceptionnel (rare, souvent temporaire)
- **1.0-2.0**: Excellent (objectif pour un bon gestionnaire)
- **0.5-1.0**: Bon (acceptable pour la plupart des investisseurs)
- **0-0.5**: Faible (le risque n'est pas bien rémunéré)
- **< 0**: Mauvais (rendement inférieur au taux sans risque)

📈 **Formule:** Sharpe = (Rp - Rf) / σp
- Rp = Rendement du portefeuille
- Rf = Taux sans risque (3% par défaut)
- σp = Volatilité du portefeuille

💡 **Usage:** Entre deux investissements, choisissez celui avec le Sharpe le plus élevé - il offre plus de rendement pour le même niveau de risque.
"""
    
    sortino_help = """
**Ratio de Sortino - Sharpe Amélioré**

Comme le Sharpe, mais ne pénalise que la volatilité négative (downside). Plus pertinent car les investisseurs ne détestent que les pertes, pas les gains!

📊 **Interprétation:**
- **> 2.0**: Exceptionnel
- **1.0-2.0**: Excellent  
- **0.5-1.0**: Bon
- **< 0.5**: Faible

📈 **Formule:** Sortino = (Rp - Rf) / σ_downside

💡 **Usage:** Un Sortino > Sharpe indique que la volatilité vient surtout des hausses (positif!). Préférez un actif avec Sortino élevé.
"""
    
    maxdd_help = """
**Maximum Drawdown - Perte Maximale**

Le drawdown mesure la perte maximale depuis un sommet historique. C'est le pire scénario vécu par l'investisseur.

📊 **Interprétation:**
- **< -10%**: Faible (obligations, money market)
- **-10% à -20%**: Modéré (portefeuille diversifié)
- **-20% à -40%**: Élevé (actions, ETF sectoriels)
- **> -40%**: Très élevé (actions individuelles, levier)

📈 **Formule:** MaxDD = (Prix - Sommet) / Sommet

💡 **Usage:** Demandez-vous: "Puis-je supporter une perte de X% sans paniquer?" Si votre Max Drawdown dépasse votre tolérance, réduisez votre exposition.

⚠️ **Note:** Le S&P 500 a connu des drawdowns de -50% (2008) et -34% (2020). C'est normal sur le long terme.
"""
    
    # Créer 5 colonnes sur une seule ligne
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label=f"Beta (β) {beta_desc}",
            value=f"{beta:.2f}",
            help=beta_help
        )
    
    with col2:
        st.metric(
            label="Volatilité Annualisée",
            value=f"{volatility*100:.1f}%",
            help=volatility_help
        )
    
    with col3:
        st.metric(
            label=f"Sharpe Ratio {sharpe_desc}",
            value=f"{sharpe:.2f}",
            help=sharpe_help
        )
    
    with col4:
        if sortino is not None:
            st.metric(
                label="Sortino Ratio",
                value=f"{sortino:.2f}",
                help=sortino_help
            )
        else:
            st.metric(label="Sortino", value="N/A", help=sortino_help)
    
    with col5:
        if max_dd is not None:
            st.metric(
                label="Max Drawdown",
                value=f"{max_dd*100:.1f}%",
                delta="Perte max depuis sommet",
                delta_color="inverse",
                help=maxdd_help
            )
        else:
            st.metric(label="Max Drawdown", value="N/A", help=maxdd_help)

# ==================== MAIN APPLICATION ====================

def main():
    st.title("📊 Benchmark Pro v2 - Risk Analytics")
    st.caption("Performance + Beta + Volatilité + Sharpe | Powered by Questrade Data")
    
    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Mode Selection
        mode = st.radio("Mode d'analyse", 
                       ["🎯 Ticker Unique", "🌍 Portfolio Global", "👀 Watch List"], 
                       index=0,
                       help="Ticker Unique: Analyse individuelle | Portfolio: Vue d'ensemble | Watch List: Tickers à surveiller")
        st.divider()
        
        benchmark_ticker = st.selectbox(
            "Benchmark de référence", 
            ["SPY", "VOO", "QQQ", "XIU.TO"],
            index=0,
            help="SPY/VOO pour actions US, XIU.TO pour actions canadiennes"
        )
        
        # Date Selection
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            default_start = datetime.now() - timedelta(days=365)
            start_date = st.date_input("Début", default_start)
        with col_d2:
            end_date = st.date_input("Fin", datetime.now())
        
        st.divider()
        
        # Risk Parameters
        st.subheader("📐 Paramètres de Risque")
        risk_free_rate = st.slider(
            "Taux sans risque (%)", 
            0.0, 10.0, 3.0, 0.5,
            help="Utilisé pour calculer le ratio de Sharpe"
        ) / 100
        
        rolling_window = st.slider(
            "Fenêtre Rolling Beta (jours)",
            20, 120, 60, 10,
            help="Période pour le calcul du beta glissant"
        )

    # --- MODE 1: TICKER UNIQUE ---
    if mode == "🎯 Ticker Unique":
        with st.sidebar:
            st.divider()
            # Get all tickers (portfolio + watchlist) without duplicates
            available_tickers = get_all_tickers_no_duplicates()
            portfolio_tickers = get_portfolio_tickers()
            
            query_params = st.query_params
            default_index = 0
            
            if "ticker" in query_params:
                url_ticker = query_params["ticker"]
                if url_ticker in available_tickers:
                    default_index = available_tickers.index(url_ticker)
            elif "NVDA" in available_tickers:
                default_index = available_tickers.index("NVDA")
            
            # Format ticker display with portfolio indicator
            ticker_labels = []
            for t in available_tickers:
                if t in portfolio_tickers:
                    ticker_labels.append(f"💼 {t} (Portfolio)")
                else:
                    ticker_labels.append(f"👀 {t} (Watchlist)")
            
            selected_idx = st.selectbox(
                "Ticker à analyser", 
                range(len(available_tickers)),
                format_func=lambda i: ticker_labels[i],
                index=default_index
            )
            selected_ticker = available_tickers[selected_idx]
            
            # Show ticker count info
            st.caption(f"📊 {len(available_tickers)} tickers disponibles ({len(portfolio_tickers)} en portfolio, {len(available_tickers) - len(portfolio_tickers)} en watchlist)")

        if selected_ticker and benchmark_ticker:
            st.subheader(f"Analyse: {selected_ticker} vs {benchmark_ticker}")
            
            # Load Data
            df = load_data_single(selected_ticker, benchmark_ticker, start_date)
            
            if df is None or len(df) == 0:
                st.warning("Aucune donnée disponible pour cette période.")
                return

            if selected_ticker == benchmark_ticker:
                st.warning("Veuillez choisir un benchmark différent du ticker.")
                return
            
            # Calculate returns
            stock_returns = df[selected_ticker].pct_change().dropna()
            market_returns = df[benchmark_ticker].pct_change().dropna()
            
            # ==================== RISK METRICS ====================
            st.markdown("---")
            st.subheader("📈 Métriques de Risque")
            
            # Calculate all risk metrics
            beta, alpha, r_squared = calculate_beta(stock_returns, market_returns)
            volatility = calculate_volatility(stock_returns)
            sharpe = calculate_sharpe_ratio(stock_returns, risk_free_rate)
            sortino = calculate_sortino_ratio(stock_returns, risk_free_rate)
            max_dd, drawdown_series, peak_series = calculate_max_drawdown(df[selected_ticker])
            
            # Display risk metrics
            render_risk_metrics_card(beta, volatility, sharpe, sortino, max_dd)
            
            # Additional stats
            with st.expander("📊 Statistiques détaillées"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Alpha (α)", f"{alpha*252*100:.2f}%", help="Rendement excédentaire annualisé")
                with col2:
                    st.metric("R²", f"{r_squared:.3f}", help="Qualité de la régression (0-1)")
                with col3:
                    st.metric("Corrélation", f"{stock_returns.corr(market_returns):.3f}")
                with col4:
                    ann_return = stock_returns.mean() * TRADING_DAYS_PER_YEAR * 100
                    st.metric("Rendement Ann.", f"{ann_return:.1f}%")
            
            # ==================== GAUGES ====================
            st.markdown("---")
            col_g1, col_g2, col_g3 = st.columns(3)
            
            with col_g1:
                fig_beta = render_risk_gauge(beta, "Beta (β)", 0, 3, 'beta')
                st.plotly_chart(fig_beta, use_container_width=True)
            
            with col_g2:
                fig_vol = render_risk_gauge(volatility, "Volatilité", 0, 1, 'volatility')
                st.plotly_chart(fig_vol, use_container_width=True)
            
            with col_g3:
                fig_sharpe = render_risk_gauge(sharpe, "Sharpe Ratio", -1, 3, 'sharpe')
                st.plotly_chart(fig_sharpe, use_container_width=True)
            
            # ==================== PERFORMANCE CHART ====================
            st.markdown("---")
            st.subheader("📉 Performance Comparée (Base 100)")
            
            df_norm = df / df.iloc[0] * 100
            
            # Portfolio context
            port_data = load_portfolio_config()
            holding = next((item for item in port_data if item["ticker"] == selected_ticker), None)
            
            # Performance metrics
            ticker_ret = (df[selected_ticker].iloc[-1] / df[selected_ticker].iloc[0] - 1) * 100
            bench_ret = (df[benchmark_ticker].iloc[-1] / df[benchmark_ticker].iloc[0] - 1) * 100
            alpha_perf = ticker_ret - bench_ret
            
            # KPI Row
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric(f"Perf {selected_ticker}", f"{ticker_ret:+.2f}%")
            with col2: st.metric(f"Perf {benchmark_ticker}", f"{bench_ret:+.2f}%")
            with col3: st.metric("Alpha", f"{alpha_perf:+.2f}%", delta="Lead" if alpha_perf > 0 else "Lag")
            with col4: st.metric("Corrélation", f"{stock_returns.corr(market_returns):.2f}")
            
            # Main performance chart
            fig_perf = go.Figure()
            fig_perf.add_trace(go.Scatter(
                x=df_norm.index, y=df_norm[selected_ticker], 
                name=selected_ticker, 
                line=dict(width=3, color='#00C853')
            ))
            fig_perf.add_trace(go.Scatter(
                x=df_norm.index, y=df_norm[benchmark_ticker], 
                name=benchmark_ticker, 
                line=dict(width=2, color='#B0BEC5', dash='dot')
            ))
            
            # Add PRU line if in portfolio
            if holding:
                avg_price = holding['avg_price']
                start_price = df[selected_ticker].iloc[0]
                avg_price_norm = (avg_price / start_price) * 100
                current_price = df[selected_ticker].iloc[-1]
                pl_pct = (current_price - avg_price) / avg_price * 100
                color_pl = "#00E676" if pl_pct >= 0 else "#FF1744"
                
                fig_perf.add_hline(
                    y=avg_price_norm, line_dash="longdash", line_color=color_pl, line_width=1,
                    annotation_text=f"PRU: ${avg_price:.2f} ({pl_pct:+.2f}%)", 
                    annotation_position="bottom right", 
                    annotation_font_color=color_pl
                )
                st.success(f"💼 **Position Portfolio** : {holding['qty']} actions @ ${avg_price:.2f}. P/L: **{pl_pct:+.2f}%**")
            
            fig_perf.update_layout(height=450, hovermode="x unified", title="Comparaison Base 100")
            st.plotly_chart(fig_perf, use_container_width=True)
            
            # ==================== ROLLING BETA CHART ====================
            st.markdown("---")
            st.subheader(f"📈 Beta Rolling ({rolling_window} jours)")
            
            rolling_beta = calculate_rolling_beta(stock_returns, market_returns, rolling_window)
            
            if len(rolling_beta) > 0:
                fig_rolling = go.Figure()
                
                # Rolling beta line
                fig_rolling.add_trace(go.Scatter(
                    x=rolling_beta.index, y=rolling_beta.values,
                    name=f'Beta Rolling {rolling_window}j',
                    line=dict(color='#29B6F6', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(41, 182, 246, 0.1)'
                ))
                
                # Reference lines
                fig_rolling.add_hline(y=1, line_dash="dash", line_color="white", line_width=1,
                    annotation_text="β=1 (Marché)", annotation_position="right")
                fig_rolling.add_hline(y=beta, line_dash="dot", line_color="#00C853", line_width=1,
                    annotation_text=f"β moyen = {beta:.2f}", annotation_position="left")
                
                fig_rolling.update_layout(
                    height=350, 
                    hovermode="x unified",
                    yaxis_title="Beta",
                    xaxis_title="Date"
                )
                st.plotly_chart(fig_rolling, use_container_width=True)
                
                # Stats sur le rolling beta
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Beta Min", f"{rolling_beta.min():.2f}")
                with col2:
                    st.metric("Beta Max", f"{rolling_beta.max():.2f}")
                with col3:
                    st.metric("Beta Actuel", f"{rolling_beta.iloc[-1]:.2f}" if len(rolling_beta) > 0 else "N/A")
            else:
                st.info(f"Pas assez de données pour calculer le beta rolling ({rolling_window} jours minimum)")
            
            # ==================== DRAWDOWN CHART ====================
            st.markdown("---")
            st.subheader("📉 Analyse du Drawdown")
            
            if drawdown_series is not None:
                fig_dd = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                       row_heights=[0.6, 0.4],
                                       vertical_spacing=0.05)
                
                # Price with peak
                fig_dd.add_trace(go.Scatter(
                    x=df[selected_ticker].index, y=df[selected_ticker],
                    name='Prix', line=dict(color='#00C853', width=2)
                ), row=1, col=1)
                
                fig_dd.add_trace(go.Scatter(
                    x=peak_series.index, y=peak_series,
                    name='Sommet', line=dict(color='#B0BEC5', width=1, dash='dot')
                ), row=1, col=1)
                
                # Drawdown
                fig_dd.add_trace(go.Scatter(
                    x=drawdown_series.index, y=drawdown_series * 100,
                    name='Drawdown %',
                    fill='tozeroy',
                    fillcolor='rgba(255, 82, 82, 0.3)',
                    line=dict(color='#FF5252', width=1)
                ), row=2, col=1)
                
                fig_dd.update_layout(height=500, hovermode="x unified")
                fig_dd.update_yaxes(title_text="Prix", row=1, col=1)
                fig_dd.update_yaxes(title_text="Drawdown %", row=2, col=1)
                
                st.plotly_chart(fig_dd, use_container_width=True)
            
            # ==================== RELATIVE STRENGTH ====================
            st.markdown("---")
            st.subheader("💪 Force Relative")
            
            rs_ratio = df[selected_ticker] / df[benchmark_ticker]
            
            fig_rs = go.Figure()
            fig_rs.add_trace(go.Scatter(
                x=rs_ratio.index, y=rs_ratio, 
                name='RS Ratio', 
                line=dict(color='#29B6F6', width=2), 
                fill='tozeroy', 
                fillcolor='rgba(41, 182, 246, 0.1)'
            ))
            fig_rs.add_trace(go.Scatter(
                x=rs_ratio.rolling(20).mean().index, 
                y=rs_ratio.rolling(20).mean(), 
                name='Trend (20d)', 
                line=dict(color='white', width=1, dash='dash')
            ))
            fig_rs.update_layout(height=350, hovermode="x unified", title="Force Relative (Ratio)")
            st.plotly_chart(fig_rs, use_container_width=True)

    # --- MODE 3: WATCH LIST ---
    elif mode == "👀 Watch List":
        st.subheader("👀 Watch List - Tickers à Surveiller")
        
        watchlist_tickers = get_watchlist_only()
        
        if not watchlist_tickers:
            st.warning("⚠️ Aucun ticker dans la watchlist qui ne soit pas déjà dans votre portfolio.")
            st.info("💡 Tous les tickers de `companies_config.py` sont déjà dans votre portfolio Questrade!")
            return
        
        st.info(f"📊 {len(watchlist_tickers)} tickers en watchlist (exclus du portfolio)")
        
        with st.spinner("Chargement des données pour la watchlist..."):
            all_tickers = list(set(watchlist_tickers + [benchmark_ticker]))
            data = load_data_batch(all_tickers, start_date)
            
            if data is None:
                st.error("Impossible de charger les données")
                return
        
        # Calculate metrics for each watchlist ticker
        watchlist_metrics = []
        
        bench_series = data[benchmark_ticker] if benchmark_ticker in data.columns else None
        bench_returns = bench_series.pct_change().dropna() if bench_series is not None else None
        
        for ticker in watchlist_tickers:
            if ticker not in data.columns:
                continue
            
            price_series = data[ticker]
            returns = price_series.pct_change().dropna()
            
            # Calculate metrics
            current_price = price_series.iloc[-1]
            start_price = price_series.iloc[0]
            perf = (current_price / start_price - 1) * 100
            
            beta, alpha, r_squared = calculate_beta(returns, bench_returns) if bench_returns is not None else (None, None, None)
            volatility = calculate_volatility(returns) * 100
            sharpe = calculate_sharpe_ratio(returns, risk_free_rate)
            max_dd, _, _ = calculate_max_drawdown(price_series)
            
            # 52W Range Position
            high_52w = price_series.rolling(min(252, len(price_series))).max().iloc[-1]
            low_52w = price_series.rolling(min(252, len(price_series))).min().iloc[-1]
            range_52w_pct = ((current_price - low_52w) / (high_52w - low_52w) * 100) if (high_52w - low_52w) > 0 else 50
            
            watchlist_metrics.append({
                'Ticker': ticker,
                'Prix': current_price,
                'Perf (%)': perf,
                'Beta': beta if beta is not None else 0,
                'Vol (%)': volatility,
                'Sharpe': sharpe,
                'Max DD (%)': max_dd * 100,
                '52W Position (%)': range_52w_pct,
                'R²': r_squared if r_squared is not None else 0
            })
        
        df_watchlist = pd.DataFrame(watchlist_metrics)
        
        if df_watchlist.empty:
            st.warning("Aucune donnée disponible pour la watchlist.")
            return
        
        # Sort by Performance by default
        df_watchlist = df_watchlist.sort_values('Perf (%)', ascending=False)
        
        # ==================== WATCHLIST KPIs ====================
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            avg_perf = df_watchlist['Perf (%)'].mean()
            st.metric("Perf Moyenne", f"{avg_perf:+.1f}%")
        
        with col2:
            best_ticker = df_watchlist.nlargest(1, 'Perf (%)').iloc[0]
            st.metric("Meilleur", f"{best_ticker['Ticker']}", f"{best_ticker['Perf (%)']:+.1f}%")
        
        with col3:
            worst_ticker = df_watchlist.nsmallest(1, 'Perf (%)').iloc[0]
            st.metric("Pire", f"{worst_ticker['Ticker']}", f"{worst_ticker['Perf (%)']:+.1f}%")
        
        with col4:
            avg_sharpe = df_watchlist['Sharpe'].mean()
            st.metric("Sharpe Moyen", f"{avg_sharpe:.2f}")
        
        with col5:
            avg_vol = df_watchlist['Vol (%)'].mean()
            st.metric("Vol Moyenne", f"{avg_vol:.1f}%")
        
        # ==================== WATCHLIST TABLE ====================
        st.markdown("---")
        st.subheader("📋 Tableau Détaillé")
        
        # Color coding functions
        def color_perf(val):
            if val > 10: return 'background-color: rgba(76, 175, 80, 0.4)'
            if val > 0: return 'background-color: rgba(139, 195, 74, 0.3)'
            if val > -10: return 'background-color: rgba(255, 152, 0, 0.3)'
            return 'background-color: rgba(255, 82, 82, 0.4)'
        
        def color_beta(val):
            if val > 1.5: return 'background-color: rgba(255, 82, 82, 0.3)'
            if val > 1.2: return 'background-color: rgba(255, 152, 0, 0.3)'
            if val > 0.8: return 'background-color: rgba(255, 235, 59, 0.3)'
            return 'background-color: rgba(76, 175, 80, 0.3)'
        
        def color_52w(val):
            if val > 90: return 'background-color: rgba(255, 82, 82, 0.3)'  # Near high
            if val < 20: return 'background-color: rgba(76, 175, 80, 0.3)'  # Near low (opportunity)
            return 'background-color: rgba(255, 235, 59, 0.2)'
        
        st.dataframe(
            df_watchlist.style.format({
                'Prix': '${:.2f}',
                'Perf (%)': '{:+.1f}%',
                'Beta': '{:.2f}',
                'Vol (%)': '{:.1f}%',
                'Sharpe': '{:.2f}',
                'Max DD (%)': '{:.1f}%',
                '52W Position (%)': '{:.0f}%',
                'R²': '{:.2f}'
            }).applymap(color_perf, subset=['Perf (%)']).applymap(color_beta, subset=['Beta']).applymap(color_52w, subset=['52W Position (%)']),
            use_container_width=True,
            height=500
        )
        
        st.caption("💡 **52W Position**: <20% = Proche du bas (opportunité), >90% = Proche du haut (prudence)")
        
        # ==================== WATCHLIST PERFORMANCE CHART ====================
        st.markdown("---")
        st.subheader("📈 Performance Comparée (Base 100)")
        
        fig_watch = go.Figure()
        
        # Add Benchmark
        bench_norm = (data[benchmark_ticker] / data[benchmark_ticker].iloc[0]) * 100
        fig_watch.add_trace(go.Scatter(
            x=bench_norm.index, y=bench_norm,
            name=benchmark_ticker,
            line=dict(color='white', width=3, dash='solid'),
            opacity=1.0
        ))
        
        # Add watchlist tickers
        colors = px.colors.qualitative.Plotly
        for i, ticker in enumerate(watchlist_tickers):
            if ticker not in data.columns:
                continue
            
            ticker_norm = (data[ticker] / data[ticker].iloc[0]) * 100
            fig_watch.add_trace(go.Scatter(
                x=ticker_norm.index,
                y=ticker_norm,
                name=ticker,
                line=dict(color=colors[i % len(colors)], width=1.5),
                opacity=0.7
            ))
        
        fig_watch.update_layout(
            height=600,
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig_watch, use_container_width=True)
        
        # ==================== OPPORTUNITIES ====================
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Opportunités (Près du Bas 52W)")
            opportunities = df_watchlist[df_watchlist['52W Position (%)'] < 25].nsmallest(5, '52W Position (%)')
            if not opportunities.empty:
                st.dataframe(opportunities[['Ticker', 'Prix', 'Perf (%)', '52W Position (%)']].style.format({
                    'Prix': '${:.2f}',
                    'Perf (%)': '{:+.1f}%',
                    '52W Position (%)': '{:.0f}%'
                }), use_container_width=True)
            else:
                st.info("Aucun ticker près du bas 52W actuellement.")
        
        with col2:
            st.subheader("⚠️ À Surveiller (Près du Haut 52W)")
            high_risk = df_watchlist[df_watchlist['52W Position (%)'] > 85].nlargest(5, '52W Position (%)')
            if not high_risk.empty:
                st.dataframe(high_risk[['Ticker', 'Prix', 'Perf (%)', '52W Position (%)']].style.format({
                    'Prix': '${:.2f}',
                    'Perf (%)': '{:+.1f}%',
                    '52W Position (%)': '{:.0f}%'
                }), use_container_width=True)
            else:
                st.info("Aucun ticker près du haut 52W actuellement.")

    # --- MODE 2: PORTFOLIO GLOBAL ---
    elif mode == "🌍 Portfolio Global":
        st.subheader("🌍 Analyse Globale du Portefeuille")
        
        port_data = load_portfolio_config()
        if not port_data:
            st.error("Aucune donnée de portfolio trouvée.")
            return

        with st.spinner("Téléchargement des données..."):
            tickers = [item['ticker'] for item in port_data]
            all_tickers = list(set(tickers + [benchmark_ticker, "CAD=X"]))
            
            data = load_data_batch(all_tickers, start_date)
            
            if data is None:
                st.error("Impossible de charger les données")
                return

        # Get USD/CAD Rate
        if "CAD=X" in data.columns:
            usdcad = data["CAD=X"]
        else:
            usdcad = pd.Series(1.40, index=data.index)
        
        # Calculate Portfolio Value Series
        portfolio_series = pd.Series(0, index=data.index, name="Portfolio (CAD)")
        weights = {}
        position_metrics = []
        
        for item in port_data:
            t = item['ticker']
            q = item['qty']
            avg_price = item.get('avg_price', 0)
            
            if t in data.columns:
                price_series = data[t]
                is_cad = t.endswith(".TO")
                
                if is_cad:
                    val_series = price_series * q
                    curr_val = val_series.iloc[-1]
                else:
                    val_series = price_series * q * usdcad
                    curr_val = val_series.iloc[-1]
                
                portfolio_series += val_series
                weights[t] = curr_val
                
                # Calculate individual metrics
                returns = price_series.pct_change().dropna()
                bench_returns = data[benchmark_ticker].pct_change().dropna() if benchmark_ticker in data.columns else None
                
                if bench_returns is not None:
                    beta, _, r2 = calculate_beta(returns, bench_returns)
                else:
                    beta, r2 = 0, 0
                
                vol = calculate_volatility(returns)
                sharpe = calculate_sharpe_ratio(returns, risk_free_rate)
                
                position_metrics.append({
                    'Ticker': t,
                    'Qty': q,
                    'Valeur ($)': curr_val,
                    'Poids (%)': 0,  # Will be calculated after
                    'Beta': beta,
                    'Vol (%)': vol * 100,
                    'Sharpe': sharpe,
                    'P/L (%)': ((price_series.iloc[-1] - avg_price) / avg_price * 100) if avg_price > 0 else 0
                })

        total_value = portfolio_series.iloc[-1]
        
        # Update weights
        for pm in position_metrics:
            pm['Poids (%)'] = (pm['Valeur ($)'] / total_value) * 100
        
        # Benchmark comparison
        bench_is_cad = benchmark_ticker.endswith(".TO")
        if not bench_is_cad and benchmark_ticker in data.columns:
            bench_series_cad = data[benchmark_ticker] * usdcad
        elif benchmark_ticker in data.columns:
            bench_series_cad = data[benchmark_ticker]
        else:
            st.error(f"Benchmark {benchmark_ticker} non trouvé")
            return

        # Portfolio metrics
        port_returns = portfolio_series.pct_change().dropna()
        bench_returns = bench_series_cad.pct_change().dropna()
        
        port_beta, port_alpha, port_r2 = calculate_beta(port_returns, bench_returns)
        port_vol = calculate_volatility(port_returns)
        port_sharpe = calculate_sharpe_ratio(port_returns, risk_free_rate)
        port_sortino = calculate_sortino_ratio(port_returns, risk_free_rate)
        port_max_dd, port_dd_series, _ = calculate_max_drawdown(portfolio_series)
        
        # ==================== PORTFOLIO RISK METRICS ====================
        st.markdown("---")
        st.subheader("📊 Métriques de Risque du Portefeuille")
        
        render_risk_metrics_card(port_beta, port_vol, port_sharpe, port_sortino, port_max_dd)
        
        # Performance metrics
        port_ret = (total_value / portfolio_series.iloc[0] - 1) * 100
        bench_ret = (bench_series_cad.iloc[-1] / bench_series_cad.iloc[0] - 1) * 100
        alpha_port = port_ret - bench_ret
        
        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Valeur Totale (CAD)", f"${total_value:,.2f}", f"{port_ret:+.2f}%")
        with c2: st.metric(f"Perf {benchmark_ticker}", f"{bench_ret:+.2f}%")
        with c3: st.metric("Alpha Portfolio", f"{alpha_port:+.2f}%", delta="Winning" if alpha_port > 0 else "Losing")
        with c4: st.metric("Nb Positions", len(port_data))
        
        # ==================== CHARTS ====================
        st.markdown("---")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📈 VS Benchmark (Base 100)")
            
            port_norm = portfolio_series / portfolio_series.iloc[0] * 100
            bench_norm = bench_series_cad / bench_series_cad.iloc[0] * 100
            
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(
                x=port_norm.index, y=port_norm, 
                name="Mon Portfolio", 
                line=dict(color="#00C853", width=4)
            ))
            fig_p.add_trace(go.Scatter(
                x=bench_norm.index, y=bench_norm, 
                name=benchmark_ticker, 
                line=dict(color="#B0BEC5", width=2, dash="dot")
            ))
            fig_p.update_layout(height=450, hovermode="x unified")
            st.plotly_chart(fig_p, use_container_width=True)
            
        with col2:
            st.markdown("### 🍰 Allocation")
            
            df_weights = pd.DataFrame.from_dict(weights, orient='index', columns=['Value'])
            df_weights = df_weights.sort_values('Value', ascending=False)
            
            palette = px.colors.qualitative.Plotly
            color_map = {ticker: palette[i % len(palette)] for i, ticker in enumerate(sorted(df_weights.index))}
            
            fig_pie = px.pie(df_weights, values='Value', names=df_weights.index, hole=0.4,
                             color=df_weights.index, color_discrete_map=color_map)
            fig_pie.update_layout(height=450, showlegend=False)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # ==================== RISK TABLE ====================
        st.markdown("---")
        st.subheader("📋 Détail des Positions avec Métriques de Risque")
        
        df_positions = pd.DataFrame(position_metrics)
        df_positions = df_positions.sort_values('Poids (%)', ascending=False)
        
        # Style the dataframe
        def color_beta(val):
            if val > 1.5: return 'background-color: rgba(255, 82, 82, 0.3)'
            if val > 1.2: return 'background-color: rgba(255, 152, 0, 0.3)'
            if val > 0.8: return 'background-color: rgba(255, 235, 59, 0.3)'
            return 'background-color: rgba(76, 175, 80, 0.3)'
        
        def color_sharpe(val):
            if val > 1.0: return 'background-color: rgba(76, 175, 80, 0.3)'
            if val > 0.5: return 'background-color: rgba(255, 235, 59, 0.3)'
            if val > 0: return 'background-color: rgba(255, 152, 0, 0.3)'
            return 'background-color: rgba(255, 82, 82, 0.3)'
        
        # Display with formatting
        st.dataframe(
            df_positions.style.format({
                'Valeur ($)': '${:,.2f}',
                'Poids (%)': '{:.1f}%',
                'Beta': '{:.2f}',
                'Vol (%)': '{:.1f}%',
                'Sharpe': '{:.2f}',
                'P/L (%)': '{:+.1f}%'
            }).applymap(color_beta, subset=['Beta']).applymap(color_sharpe, subset=['Sharpe']),
            use_container_width=True,
            height=400
        )
        
        # ==================== CORRELATION HEATMAP ====================
        st.markdown("---")
        st.subheader("🔥 Matrice de Corrélation")
        
        # Calculate returns for all tickers
        returns_df = data[[t for t in tickers if t in data.columns]].pct_change().dropna()
        
        if len(returns_df.columns) > 1:
            corr_matrix = returns_df.corr()
            
            fig_corr = px.imshow(
                corr_matrix,
                labels=dict(color="Corrélation"),
                x=corr_matrix.columns,
                y=corr_matrix.index,
                color_continuous_scale='RdYlGn',
                zmin=-1, zmax=1
            )
            fig_corr.update_layout(height=500)
            st.plotly_chart(fig_corr, use_container_width=True)
        
        # ==================== SPAGHETTI CHART ====================
        st.markdown("---")
        st.subheader("🍝 Tous les titres (Base 100)")
        
        fig_s = go.Figure()
        
        # Add Benchmark first
        fig_s.add_trace(go.Scatter(
            x=bench_norm.index, y=bench_norm, 
            name=benchmark_ticker, 
            line=dict(color="white", width=4, dash='solid'), 
            opacity=1.0
        ))
        
        start_prices = data.iloc[0]
        data_norm = data / start_prices * 100
        
        for t in data.columns:
            if t == benchmark_ticker or t == "CAD=X": continue
            
            color = color_map.get(t, "rgba(128, 128, 128, 0.5)")
            width = 2.5 if t in ["NVDA", "GOOGL", "VOO"] else 1.5
            
            fig_s.add_trace(go.Scatter(
                x=data_norm.index, 
                y=data_norm[t], 
                name=t, 
                line=dict(color=color, width=width), 
                opacity=0.8,
                hovertemplate=f"<b>{t}</b>: %{{y:.1f}}<extra></extra>"
            ))
            
        fig_s.update_layout(height=600, hovermode="x unified", showlegend=False)
        st.plotly_chart(fig_s, use_container_width=True)
        
        # ==================== TOP CONTRIBUTORS ====================
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Top 5 Contributeurs de Risque")
            df_risk = df_positions.copy()
            df_risk['Risk Contrib'] = df_risk['Beta'] * df_risk['Poids (%)'] / 100
            df_risk = df_risk.nlargest(5, 'Risk Contrib')[['Ticker', 'Poids (%)', 'Beta', 'Risk Contrib']]
            st.dataframe(df_risk.style.format({
                'Poids (%)': '{:.1f}%',
                'Beta': '{:.2f}',
                'Risk Contrib': '{:.4f}'
            }), use_container_width=True)
        
        with col2:
            st.subheader("🏆 Top 5 par Sharpe Ratio")
            df_sharpe = df_positions.nlargest(5, 'Sharpe')[['Ticker', 'Sharpe', 'Vol (%)', 'P/L (%)']]
            st.dataframe(df_sharpe.style.format({
                'Sharpe': '{:.2f}',
                'Vol (%)': '{:.1f}%',
                'P/L (%)': '{:+.1f}%'
            }), use_container_width=True)

if __name__ == "__main__":
    main()
