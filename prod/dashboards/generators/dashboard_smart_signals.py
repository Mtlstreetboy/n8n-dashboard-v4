# -*- coding: utf-8 -*-
"""
Dashboard Smart Signals - Indicateurs Intelligents pour Analyse Technique
============================================================================

Ce dashboard répond aux questions comme "Pourquoi le prix d'Amazon drop?"
en fournissant:
- RSI & Détection de Survente/Surachat
- MA200 & Niveaux de Support/Résistance  
- Indicateurs de Valorisation (P/E, PEG)
- Analyse du Volume (Détection de capitulation)
- Signaux Smart Money

Port: 8504
Usage: streamlit run dashboard_smart_signals.py --server.port=8504
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
import sys
import os

# Configuration pour importer companies_config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from prod.config.companies_config import AI_COMPANIES

# Setup Streamlit
st.set_page_config(
    page_title="📡 Smart Signals - Analyse Technique Intelligente",
    layout="wide",
    page_icon="📡",
    initial_sidebar_state="expanded"
)

# Force Dark Mode for Plotly
import plotly.io as pio
pio.templates.default = "plotly_dark"

# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate RSI (Relative Strength Index)
    RSI < 30 = Oversold (buy signal)
    RSI > 70 = Overbought (sell signal)
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculate MACD (Moving Average Convergence Divergence)
    """
    exp_fast = prices.ewm(span=fast, adjust=False).mean()
    exp_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = exp_fast - exp_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2):
    """
    Calculate Bollinger Bands
    """
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, sma, lower_band

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate ATR (Average True Range) - Volatility Indicator
    """
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Calculate OBV (On-Balance Volume) - Volume Trend Indicator
    """
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv

def detect_support_resistance(prices: pd.Series, window: int = 20):
    """
    Detect support and resistance levels based on local min/max
    """
    supports = []
    resistances = []
    
    # Ensure we're working with a 1D series
    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0]
    prices = prices.squeeze()
    
    for i in range(window, len(prices) - window):
        local_window = prices.iloc[i-window:i+window+1]
        current_val = float(prices.iloc[i])
        local_min = float(local_window.min())
        local_max = float(local_window.max())
        
        # Local minimum = Support
        if abs(current_val - local_min) < 0.001:
            supports.append((prices.index[i], current_val))
        # Local maximum = Resistance
        if abs(current_val - local_max) < 0.001:
            resistances.append((prices.index[i], current_val))
    
    return supports[-3:] if len(supports) >= 3 else supports, \
           resistances[-3:] if len(resistances) >= 3 else resistances

def detect_volume_anomaly(volume: pd.Series, threshold: float = 2.0) -> pd.Series:
    """
    Detect volume anomalies (potential institutional activity)
    Returns True where volume > threshold * 20-day average
    """
    avg_volume = volume.rolling(20).mean()
    return volume > (threshold * avg_volume)

def calculate_volume_profile(df: pd.DataFrame, bins: int = 20):
    """
    Calculate Volume Profile (Volume at Price levels)
    """
    price_min, price_max = df['Close'].min(), df['Close'].max()
    price_bins = np.linspace(price_min, price_max, bins)
    
    volume_at_price = []
    for i in range(len(price_bins) - 1):
        mask = (df['Close'] >= price_bins[i]) & (df['Close'] < price_bins[i+1])
        vol = df.loc[mask, 'Volume'].sum()
        volume_at_price.append({
            'price_low': price_bins[i],
            'price_high': price_bins[i+1],
            'price_mid': (price_bins[i] + price_bins[i+1]) / 2,
            'volume': vol
        })
    
    return pd.DataFrame(volume_at_price)

# ============================================================================
# VALUATION METRICS
# ============================================================================

def get_valuation_metrics(ticker: str) -> dict:
    """
    Fetch valuation metrics from Yahoo Finance
    Calculate PEG manually if not available
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Basic metrics
        trailing_pe = info.get('trailingPE')
        forward_pe = info.get('forwardPE')
        peg_ratio = info.get('pegRatio')
        earnings_growth = info.get('earningsGrowth')
        revenue_growth = info.get('revenueGrowth')
        earnings_quarterly_growth = info.get('earningsQuarterlyGrowth')
        
        # Calculate PEG manually if not available
        if peg_ratio is None and forward_pe is not None:
            # Try different growth metrics
            growth_rate = None
            if earnings_growth is not None and earnings_growth > 0:
                growth_rate = earnings_growth * 100  # Convert to percentage
            elif earnings_quarterly_growth is not None and earnings_quarterly_growth > 0:
                growth_rate = earnings_quarterly_growth * 100
            elif revenue_growth is not None and revenue_growth > 0:
                growth_rate = revenue_growth * 100
            
            if growth_rate is not None and growth_rate > 0:
                peg_ratio = forward_pe / growth_rate
        
        metrics = {
            'P/E Trailing': trailing_pe,
            'P/E Forward': forward_pe,
            'PEG Ratio': peg_ratio,
            'Earnings Growth': earnings_growth,
            'Revenue Growth': revenue_growth,
            'Earnings Quarterly Growth': earnings_quarterly_growth,
            'Price/Book': info.get('priceToBook'),
            'Price/Sales': info.get('priceToSalesTrailing12Months'),
            'EV/EBITDA': info.get('enterpriseToEbitda'),
            'EV/Revenue': info.get('enterpriseToRevenue'),
            'Profit Margin': info.get('profitMargins'),
            'Operating Margin': info.get('operatingMargins'),
            'ROE': info.get('returnOnEquity'),
            'ROA': info.get('returnOnAssets'),
            'Debt/Equity': info.get('debtToEquity'),
            'Current Ratio': info.get('currentRatio'),
            'Quick Ratio': info.get('quickRatio'),
            'Beta': info.get('beta'),
            '52W High': info.get('fiftyTwoWeekHigh'),
            '52W Low': info.get('fiftyTwoWeekLow'),
            'Market Cap': info.get('marketCap'),
            'Avg Volume': info.get('averageVolume'),
            'Dividend Yield': info.get('dividendYield'),
            'Payout Ratio': info.get('payoutRatio'),
            'Target Price': info.get('targetMeanPrice'),
            'Target High': info.get('targetHighPrice'),
            'Target Low': info.get('targetLowPrice'),
            'Recommendation': info.get('recommendationKey'),
            'Number of Analysts': info.get('numberOfAnalystOpinions'),
            'Sector': info.get('sector'),
            'Industry': info.get('industry'),
            'Short Ratio': info.get('shortRatio'),
            'Short % Float': info.get('shortPercentOfFloat'),
            'Shares Outstanding': info.get('sharesOutstanding'),
            'Float Shares': info.get('floatShares'),
        }
        
        # Filter out None values and keep track of calculated vs real PEG
        filtered = {k: v for k, v in metrics.items() if v is not None}
        
        # Add metadata for PEG if it was calculated
        if peg_ratio is not None and info.get('pegRatio') is None:
            filtered['PEG Calculated'] = True
        
        return filtered
    except Exception as e:
        st.warning(f"Erreur récupération métriques: {e}")
        return {}

# ============================================================================
# SMART MONEY SIGNALS
# ============================================================================

def generate_smart_signals(df: pd.DataFrame, rsi: pd.Series, volume_anomaly: pd.Series) -> list:
    """
    Generate intelligent trading signals based on multiple indicators
    """
    signals = []
    current_price = df['Close'].iloc[-1]
    current_rsi = rsi.iloc[-1]
    ma50 = df['Close'].rolling(50).mean().iloc[-1]
    ma200 = df['Close'].rolling(200).mean().iloc[-1]
    
    # RSI Signals
    if current_rsi < 30:
        signals.append({
            'type': '🟢 OVERSOLD',
            'indicator': 'RSI',
            'value': f'{current_rsi:.1f}',
            'action': 'Potentiel rebond technique - Zone de survente',
            'strength': 'HIGH' if current_rsi < 25 else 'MEDIUM'
        })
    elif current_rsi > 70:
        signals.append({
            'type': '🔴 OVERBOUGHT',
            'indicator': 'RSI',
            'value': f'{current_rsi:.1f}',
            'action': 'Prudence - Zone de surachat',
            'strength': 'HIGH' if current_rsi > 80 else 'MEDIUM'
        })
    
    # Moving Average Signals
    if current_price > ma200 and ma50 > ma200:
        signals.append({
            'type': '🟢 BULLISH TREND',
            'indicator': 'MA Cross',
            'value': f'Prix > MA200 ({ma200:.2f})',
            'action': 'Tendance haussière confirmée',
            'strength': 'HIGH'
        })
    elif current_price < ma200:
        signals.append({
            'type': '🔴 BEARISH TREND',
            'indicator': 'MA200',
            'value': f'Prix < MA200 ({ma200:.2f})',
            'action': 'Sous la MA200 - Pression baissière',
            'strength': 'MEDIUM'
        })
    
    # Volume Anomaly
    if volume_anomaly.iloc[-1]:
        recent_return = (current_price / df['Close'].iloc[-2] - 1) * 100
        if recent_return < -2:
            signals.append({
                'type': '⚠️ CAPITULATION?',
                'indicator': 'Volume Spike',
                'value': f'Volume 2x+ moyenne',
                'action': 'Volume anormal avec baisse - Possible capitulation',
                'strength': 'HIGH'
            })
        elif recent_return > 2:
            signals.append({
                'type': '🟢 ACCUMULATION',
                'indicator': 'Volume Spike',
                'value': f'Volume 2x+ moyenne',
                'action': 'Volume anormal avec hausse - Accumulation institutionnelle',
                'strength': 'HIGH'
            })
    
    # Price vs 52W Range
    recent_high = df['Close'].rolling(252).max().iloc[-1]
    recent_low = df['Close'].rolling(252).min().iloc[-1]
    range_position = (current_price - recent_low) / (recent_high - recent_low) * 100
    
    if range_position < 20:
        signals.append({
            'type': '🟡 NEAR 52W LOW',
            'indicator': '52W Range',
            'value': f'{range_position:.1f}% du range',
            'action': 'Proche du plus bas 52 semaines',
            'strength': 'MEDIUM'
        })
    elif range_position > 90:
        signals.append({
            'type': '🟡 NEAR 52W HIGH',
            'indicator': '52W Range',
            'value': f'{range_position:.1f}% du range',
            'action': 'Proche du plus haut 52 semaines',
            'strength': 'MEDIUM'
        })
    
    return signals

# ============================================================================
# PORTFOLIO INTEGRATION
# ============================================================================

def load_portfolio_holdings():
    """Load portfolio from Questrade sync file"""
    portfolio_file = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../../prod/config/portfolio_holdings.json'
    ))
    if os.path.exists(portfolio_file):
        with open(portfolio_file, 'r') as f:
            return json.load(f)
    return []

def get_tickers():
    """Extract tickers from config"""
    tickers = [c['ticker'] for c in AI_COMPANIES if c.get('ticker')]
    return sorted(list(set(tickers)))

# ============================================================================
# CHART BUILDERS
# ============================================================================

def build_price_chart_with_indicators(df: pd.DataFrame, ticker: str, 
                                       show_bollinger: bool = True,
                                       show_ma: bool = True,
                                       supports=None, resistances=None):
    """
    Build comprehensive price chart with technical indicators
    """
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=(f'{ticker} - Prix & Indicateurs', 'RSI', 'MACD', 'Volume')
    )
    
    # Candlestick Chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Prix',
        increasing_line_color='#26A69A',
        decreasing_line_color='#EF5350'
    ), row=1, col=1)
    
    # Moving Averages
    if show_ma:
        ma20 = df['Close'].rolling(20).mean()
        ma50 = df['Close'].rolling(50).mean()
        ma200 = df['Close'].rolling(200).mean()
        
        fig.add_trace(go.Scatter(x=df.index, y=ma20, name='MA20', 
                                  line=dict(color='#FFC107', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=ma50, name='MA50', 
                                  line=dict(color='#2196F3', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=ma200, name='MA200', 
                                  line=dict(color='#FF5722', width=2)), row=1, col=1)
    
    # Bollinger Bands
    if show_bollinger:
        upper, middle, lower = calculate_bollinger_bands(df['Close'])
        fig.add_trace(go.Scatter(x=df.index, y=upper, name='BB Upper',
                                  line=dict(color='rgba(255,255,255,0.3)', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=lower, name='BB Lower',
                                  line=dict(color='rgba(255,255,255,0.3)', width=1),
                                  fill='tonexty', fillcolor='rgba(255,255,255,0.05)'), row=1, col=1)
    
    # Support/Resistance Lines
    if supports:
        for date, price in supports:
            fig.add_hline(y=price, line_dash="dash", line_color="green", 
                          line_width=1, opacity=0.7, row=1, col=1)
    if resistances:
        for date, price in resistances:
            fig.add_hline(y=price, line_dash="dash", line_color="red", 
                          line_width=1, opacity=0.7, row=1, col=1)
    
    # RSI
    rsi = calculate_rsi(df['Close'])
    fig.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI',
                              line=dict(color='#9C27B0', width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=1, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=1, row=2, col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, row=2, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, row=2, col=1)
    
    # MACD
    macd_line, signal_line, histogram = calculate_macd(df['Close'])
    colors = ['#26A69A' if h >= 0 else '#EF5350' for h in histogram]
    fig.add_trace(go.Bar(x=df.index, y=histogram, name='MACD Hist', marker_color=colors), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=macd_line, name='MACD', 
                              line=dict(color='#2196F3', width=1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=signal_line, name='Signal', 
                              line=dict(color='#FF9800', width=1)), row=3, col=1)
    
    # Volume
    volume_colors = ['#26A69A' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#EF5350' 
                     for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume',
                          marker_color=volume_colors, opacity=0.7), row=4, col=1)
    
    # Volume MA
    vol_ma = df['Volume'].rolling(20).mean()
    fig.add_trace(go.Scatter(x=df.index, y=vol_ma, name='Vol MA20',
                              line=dict(color='#FFC107', width=1)), row=4, col=1)
    
    fig.update_layout(
        height=900,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )
    
    fig.update_yaxes(title_text="Prix ($)", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    fig.update_yaxes(title_text="Volume", row=4, col=1)
    
    return fig

def build_valuation_gauge(value, title, min_val, max_val, good_range, bad_range):
    """Build a gauge chart for valuation metrics"""
    if value is None:
        return None
    
    # Determine color based on value
    if good_range[0] <= value <= good_range[1]:
        bar_color = "#26A69A"
    elif bad_range[0] <= value <= bad_range[1]:
        bar_color = "#EF5350"
    else:
        bar_color = "#FFC107"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 14}},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': bar_color},
            'steps': [
                {'range': good_range, 'color': 'rgba(38, 166, 154, 0.3)'},
                {'range': bad_range, 'color': 'rgba(239, 83, 80, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 2},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# ============================================================================
# DIAGNOSTIC GENERATOR
# ============================================================================

def generate_diagnostic(ticker: str, df: pd.DataFrame, metrics: dict, signals: list) -> str:
    """
    Generate an AI-style diagnostic explaining price movement
    """
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
    daily_change = (current_price / prev_price - 1) * 100
    
    rsi = calculate_rsi(df['Close']).iloc[-1]
    ma200 = df['Close'].rolling(200).mean().iloc[-1]
    vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
    current_vol = df['Volume'].iloc[-1]
    vol_ratio = current_vol / vol_avg if vol_avg > 0 else 1
    
    diagnostic = f"## 📊 Diagnostic Technique: {ticker}\n\n"
    
    # Price Action
    emoji = "📈" if daily_change > 0 else "📉"
    diagnostic += f"### {emoji} Mouvement du Jour: **{daily_change:+.2f}%**\n\n"
    
    # Key Factors
    diagnostic += "### 🔍 Facteurs Clés:\n\n"
    
    # RSI Analysis
    if rsi < 30:
        diagnostic += f"1. **RSI en Survente ({rsi:.1f})**: Le titre est techniquement survendu. "
        diagnostic += "Historiquement, cela précède souvent un rebond technique. "
        diagnostic += "Les traders 'mean reversion' entrent généralement à ces niveaux.\n\n"
    elif rsi > 70:
        diagnostic += f"1. **RSI en Surachat ({rsi:.1f})**: Zone de prudence. "
        diagnostic += "Le titre pourrait consolider ou corriger à court terme.\n\n"
    else:
        diagnostic += f"1. **RSI Neutre ({rsi:.1f})**: Pas de signal extrême de momentum.\n\n"
    
    # MA200 Analysis
    ma200_dist = (current_price / ma200 - 1) * 100
    if current_price < ma200:
        diagnostic += f"2. **Sous la MA200 ({ma200_dist:.1f}%)**: Pression baissière. "
        diagnostic += "La MA200 agit comme résistance. Les institutionnels attendent souvent "
        diagnostic += "ce niveau pour réévaluer leurs positions.\n\n"
    else:
        diagnostic += f"2. **Au-dessus de la MA200 (+{ma200_dist:.1f}%)**: Tendance haussière confirmée.\n\n"
    
    # Volume Analysis
    if vol_ratio > 2:
        diagnostic += f"3. **Volume Anormal ({vol_ratio:.1f}x la moyenne)**: "
        if daily_change < -2:
            diagnostic += "Possible capitulation. Un pic de volume à la baisse marque souvent "
            diagnostic += "la fin d'un mouvement correctif à court terme.\n\n"
        elif daily_change > 2:
            diagnostic += "Accumulation institutionnelle probable. L'argent intelligent entre.\n\n"
        else:
            diagnostic += "Activité inhabituelle à surveiller.\n\n"
    
    # Valuation Context
    if metrics.get('P/E Forward'):
        pe_fwd = metrics['P/E Forward']
        diagnostic += f"4. **P/E Forward: {pe_fwd:.1f}x**: "
        if pe_fwd < 15:
            diagnostic += "Valorisation attractive par rapport aux standards historiques.\n\n"
        elif pe_fwd > 30:
            diagnostic += "Valorisation élevée - la croissance doit se maintenir.\n\n"
        else:
            diagnostic += "Valorisation dans la moyenne.\n\n"
    
    if metrics.get('PEG Ratio'):
        peg = metrics['PEG Ratio']
        diagnostic += f"5. **PEG Ratio: {peg:.2f}**: "
        if peg < 1:
            diagnostic += "La croissance n'est pas assez 'payée' - opportunité GARP.\n\n"
        elif peg > 2:
            diagnostic += "Prime importante pour la croissance.\n\n"
    
    # Summary
    diagnostic += "### 💡 Synthèse:\n\n"
    
    buy_signals = sum(1 for s in signals if '🟢' in s['type'])
    sell_signals = sum(1 for s in signals if '🔴' in s['type'])
    
    if buy_signals > sell_signals:
        diagnostic += "**Biais: CONSTRUCTIF** - Les indicateurs techniques suggèrent "
        diagnostic += "une opportunité d'entrée potentielle. L'approche prudente serait "
        diagnostic += "d'attendre une confirmation (stabilisation sur support ou divergence RSI).\n"
    elif sell_signals > buy_signals:
        diagnostic += "**Biais: PRUDENT** - Les indicateurs suggèrent de la prudence. "
        diagnostic += "Considérer un allègement ou attendre une stabilisation.\n"
    else:
        diagnostic += "**Biais: NEUTRE** - Pas de signal dominant. Surveiller l'évolution.\n"
    
    return diagnostic

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.title("📡 Smart Signals - Analyse Technique Intelligente")
    st.caption("Répondez aux questions: 'Pourquoi le prix drop?' avec des indicateurs actionnables")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.info("🧪 Port 8504 - Beta Version")
        
        # Ticker Selection
        available_tickers = get_tickers()
        
        # Add common tickers not in portfolio
        extra_tickers = ["AAPL", "MSFT", "META", "TSLA", "AMD", "INTC", "BA", "DIS", "JPM"]
        all_tickers = sorted(list(set(available_tickers + extra_tickers)))
        
        # URL Params handling
        query_params = st.query_params
        default_idx = all_tickers.index("AMZN") if "AMZN" in all_tickers else 0
        if "ticker" in query_params and query_params["ticker"] in all_tickers:
            default_idx = all_tickers.index(query_params["ticker"])
        
        selected_ticker = st.selectbox("🎯 Ticker", all_tickers, index=default_idx)
        
        st.divider()
        
        # Period Selection
        period_options = {
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 365,
            "2Y": 730,
            "5Y": 1825
        }
        selected_period = st.select_slider("📅 Période", options=list(period_options.keys()), value="1Y")
        days = period_options[selected_period]
        
        st.divider()
        
        # Display Options
        st.subheader("📊 Options d'Affichage")
        show_bollinger = st.checkbox("Bollinger Bands", value=True)
        show_ma = st.checkbox("Moving Averages", value=True)
        show_support_resistance = st.checkbox("Support/Résistance", value=True)
        
        st.divider()
        
        # Portfolio Context
        portfolio = load_portfolio_holdings()
        holding = next((h for h in portfolio if h['ticker'] == selected_ticker), None)
        
        if holding:
            st.success(f"💼 **En Portfolio**")
            st.metric("Quantité", holding['qty'])
            st.metric("PRU", f"${holding['avg_price']:.2f}")
    
    # Main Content
    if selected_ticker:
        # Load Data
        start_date = datetime.now() - timedelta(days=days + 250)  # Extra for MA200
        
        with st.spinner(f"Chargement des données pour {selected_ticker}..."):
            try:
                df = yf.download(selected_ticker, start=start_date, progress=False)
                
                # Handle multi-index columns from yfinance
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                # Ensure columns are properly named
                df.columns = [str(c) for c in df.columns]
                
                if df.empty:
                    st.error("Aucune donnée disponible")
                    return
            except Exception as e:
                st.error(f"Erreur: {e}")
                return
        
        # Calculate Indicators (squeeze Series to ensure 1D)
        close_series = df['Close'].squeeze() if isinstance(df['Close'], pd.DataFrame) else df['Close']
        volume_series = df['Volume'].squeeze() if isinstance(df['Volume'], pd.DataFrame) else df['Volume']
        
        rsi = calculate_rsi(close_series)
        volume_anomaly = detect_volume_anomaly(volume_series)
        supports, resistances = detect_support_resistance(close_series) if show_support_resistance else (None, None)
        
        # Get Valuation Metrics
        with st.spinner("Récupération des métriques de valorisation..."):
            metrics = get_valuation_metrics(selected_ticker)
        
        # Generate Signals
        signals = generate_smart_signals(df, rsi, volume_anomaly)
        
        # ========================
        # SIGNALS SECTION
        # ========================
        st.markdown("---")
        st.subheader("🚦 Signaux Intelligents")
        
        if signals:
            cols = st.columns(min(len(signals), 4))
            for i, signal in enumerate(signals[:4]):
                with cols[i]:
                    strength_color = {"HIGH": "🔥", "MEDIUM": "⚡", "LOW": "💤"}.get(signal['strength'], "")
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                        padding: 15px;
                        border-radius: 10px;
                        border-left: 4px solid {'#26A69A' if '🟢' in signal['type'] else '#EF5350' if '🔴' in signal['type'] else '#FFC107'};
                    ">
                        <h4 style="margin:0">{signal['type']}</h4>
                        <p style="color: #888; margin: 5px 0;">{signal['indicator']}: {signal['value']}</p>
                        <p style="margin: 5px 0;">{signal['action']}</p>
                        <p style="color: #FFC107; margin: 0;">{strength_color} {signal['strength']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Aucun signal fort détecté actuellement.")
        
        # ========================
        # MAIN CHART
        # ========================
        st.markdown("---")
        
        # Trim to requested period for display
        df_display = df.tail(days + 50)  # Extra buffer for indicators
        
        fig = build_price_chart_with_indicators(
            df_display, selected_ticker,
            show_bollinger=show_bollinger,
            show_ma=show_ma,
            supports=supports if show_support_resistance else None,
            resistances=resistances if show_support_resistance else None
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # ========================
        # METRICS ROW
        # ========================
        st.markdown("---")
        st.subheader("📈 Métriques de Valorisation")
        
        # Display Growth Metrics if available
        if any(k in metrics for k in ['Earnings Growth', 'Revenue Growth']):
            growth_info = []
            if metrics.get('Earnings Growth'):
                growth_info.append(f"📈 Croissance Earnings: **{metrics['Earnings Growth']*100:.1f}%**")
            if metrics.get('Revenue Growth'):
                growth_info.append(f"📊 Croissance Revenus: **{metrics['Revenue Growth']*100:.1f}%**")
            if growth_info:
                st.info(" | ".join(growth_info))
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            val = metrics.get('P/E Trailing')
            if val:
                # Color code based on value
                if val < 15:
                    st.metric("P/E Trailing", f"{val:.1f}x", "Attractif 🟢",
                              help="Prix / Bénéfice (12 derniers mois). <15 = bon marché")
                elif val > 30:
                    st.metric("P/E Trailing", f"{val:.1f}x", "Élevé 🔴",
                              help="Prix / Bénéfice (12 derniers mois). >30 = cher")
                else:
                    st.metric("P/E Trailing", f"{val:.1f}x",
                              help="Prix / Bénéfice (12 derniers mois)")
            else:
                st.metric("P/E Trailing", "N/A", help="Données non disponibles")
        
        with col2:
            val = metrics.get('P/E Forward')
            delta = None
            if val and metrics.get('P/E Trailing'):
                delta = "Expansion ⚠️" if val > metrics['P/E Trailing'] else "Compression ✅"
            st.metric("P/E Forward", f"{val:.1f}x" if val else "N/A", delta,
                      help="P/E basé sur les bénéfices projetés")
        
        with col3:
            val = metrics.get('PEG Ratio')
            if val:
                calculated = metrics.get('PEG Calculated', False)
                label = "PEG Ratio" + (" *" if calculated else "")
                
                # Color code based on value
                if val < 1.0:
                    st.metric(label, f"{val:.2f}", "GARP 🟢",
                              help="P/E / Croissance. <1 = sous-évalué (Growth At Reasonable Price)")
                elif val > 2.0:
                    st.metric(label, f"{val:.2f}", "Prime élevée 🔴",
                              help="P/E / Croissance. >2 = surévalué")
                else:
                    st.metric(label, f"{val:.2f}",
                              help="P/E / Croissance. ~1-2 = juste valeur")
                
                if calculated:
                    st.caption("*Calculé manuellement")
            else:
                # Show alternative if PEG not available
                if metrics.get('P/E Forward') and metrics.get('Earnings Growth'):
                    pe = metrics['P/E Forward']
                    growth = metrics['Earnings Growth'] * 100
                    manual_peg = pe / growth if growth > 0 else None
                    if manual_peg:
                        st.metric("PEG (estimé)", f"{manual_peg:.2f}",
                                  help=f"Calculé: P/E {pe:.1f} / Growth {growth:.1f}%")
                    else:
                        st.metric("PEG Ratio", "N/A", help="Croissance négative ou données manquantes")
                else:
                    st.metric("PEG Ratio", "N/A", help="Données de croissance non disponibles")
        
        with col4:
            val = metrics.get('Beta')
            if val:
                if val > 1.3:
                    st.metric("Beta", f"{val:.2f}", "Haute volatilité 🔴",
                              help="Volatilité vs marché. >1.3 = beaucoup plus volatil")
                elif val < 0.7:
                    st.metric("Beta", f"{val:.2f}", "Faible volatilité 🟢",
                              help="Volatilité vs marché. <0.7 = moins volatil")
                else:
                    st.metric("Beta", f"{val:.2f}",
                              help="Volatilité vs marché. ~1 = similaire au marché")
            else:
                st.metric("Beta", "N/A", help="Données non disponibles")
        
        with col5:
            val = metrics.get('Short % Float')
            if val:
                if val > 0.20:
                    st.metric("Short Interest", f"{val*100:.1f}%", "Squeeze Risk 🔥",
                              help="% des actions en position short. >20% = risque de short squeeze élevé")
                elif val > 0.10:
                    st.metric("Short Interest", f"{val*100:.1f}%", "Élevé ⚠️",
                              help="% des actions en position short. >10% = élevé")
                else:
                    st.metric("Short Interest", f"{val*100:.1f}%",
                              help="% des actions en position short")
            else:
                st.metric("Short Interest", "N/A", help="Données non disponibles")
        
        # ========================
        # DETAILED METRICS
        # ========================
        with st.expander("📊 Toutes les Métriques de Valorisation"):
            if metrics:
                col1, col2, col3 = st.columns(3)
                
                metric_groups = {
                    "Valorisation": ['P/E Trailing', 'P/E Forward', 'PEG Ratio', 'Price/Book', 
                                     'Price/Sales', 'EV/EBITDA', 'EV/Revenue', 'Market Cap'],
                    "Croissance & Qualité": ['Earnings Growth', 'Revenue Growth', 'Earnings Quarterly Growth',
                                             'Profit Margin', 'Operating Margin', 'ROE', 'ROA'],
                    "Santé Financière": ['Debt/Equity', 'Current Ratio', 'Quick Ratio', 'Dividend Yield', 
                                        'Payout Ratio'],
                    "Trading & Sentiment": ['Beta', '52W High', '52W Low', 'Avg Volume', 'Short Ratio', 
                                'Short % Float', 'Target Price', 'Target High', 'Target Low',
                                'Recommendation', 'Number of Analysts']
                }
                
                # Display first 2 groups in first 2 columns
                for i, (group_name, metric_list) in enumerate(list(metric_groups.items())[:3]):
                    with [col1, col2, col3][i]:
                        st.markdown(f"**{group_name}**")
                        for m in metric_list:
                            if m in metrics:
                                val = metrics[m]
                                if isinstance(val, float):
                                    if m in ['Profit Margin', 'Operating Margin', 'ROE', 'ROA', 
                                            'Dividend Yield', 'Short % Float', 'Earnings Growth',
                                            'Revenue Growth', 'Earnings Quarterly Growth', 'Payout Ratio']:
                                        st.write(f"{m}: **{val*100:.2f}%**")
                                    elif m in ['Market Cap', 'Avg Volume', 'Shares Outstanding', 'Float Shares']:
                                        # Format large numbers
                                        if val >= 1e12:
                                            st.write(f"{m}: **${val/1e12:.2f}T**" if 'Cap' in m else f"{m}: **{val/1e12:.2f}T**")
                                        elif val >= 1e9:
                                            st.write(f"{m}: **${val/1e9:.2f}B**" if 'Cap' in m else f"{m}: **{val/1e9:.2f}B**")
                                        elif val >= 1e6:
                                            st.write(f"{m}: **${val/1e6:.2f}M**" if 'Cap' in m else f"{m}: **{val/1e6:.2f}M**")
                                        else:
                                            st.write(f"{m}: **{val:,.0f}**")
                                    else:
                                        st.write(f"{m}: **{val:.2f}**")
                                else:
                                    st.write(f"{m}: **{val}**")
                
                # Display trading group in expander at bottom
                if 'Trading & Sentiment' in metric_groups:
                    st.markdown("---")
                    with st.expander("🎯 Trading & Sentiment (détails)"):
                        for m in metric_groups['Trading & Sentiment']:
                            if m in metrics:
                                val = metrics[m]
                                if isinstance(val, float):
                                    if m in ['Short % Float']:
                                        st.write(f"{m}: **{val*100:.2f}%**")
                                    elif m in ['Avg Volume']:
                                        st.write(f"{m}: **{val:,.0f}**")
                                    else:
                                        st.write(f"{m}: **{val:.2f}**")
                                else:
                                    st.write(f"{m}: **{val}**")
            else:
                st.warning("Métriques non disponibles pour ce ticker.")
        
        # ========================
        # DIAGNOSTIC
        # ========================
        st.markdown("---")
        diagnostic = generate_diagnostic(selected_ticker, df, metrics, signals)
        st.markdown(diagnostic)
        
        # ========================
        # VOLUME PROFILE
        # ========================
        st.markdown("---")
        st.subheader("📊 Profil de Volume")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Recent price action with volume
            df_recent = df.tail(60)
            
            fig_vol = go.Figure()
            
            # Price Line
            fig_vol.add_trace(go.Scatter(
                x=df_recent.index, y=df_recent['Close'],
                name='Prix', line=dict(color='#2196F3', width=2)
            ))
            
            # Volume Bars
            fig_vol.add_trace(go.Bar(
                x=df_recent.index, 
                y=df_recent['Volume'],
                name='Volume',
                marker_color=['#26A69A' if df_recent['Close'].iloc[i] >= df_recent['Open'].iloc[i] 
                             else '#EF5350' for i in range(len(df_recent))],
                opacity=0.5,
                yaxis='y2'
            ))
            
            # Highlight volume spikes
            vol_spikes = df_recent[detect_volume_anomaly(df_recent['Volume'])]
            if not vol_spikes.empty:
                fig_vol.add_trace(go.Scatter(
                    x=vol_spikes.index,
                    y=vol_spikes['Close'],
                    mode='markers',
                    marker=dict(size=12, color='#FFC107', symbol='star'),
                    name='Volume Spike'
                ))
            
            fig_vol.update_layout(
                height=400,
                yaxis=dict(title='Prix ($)', side='right'),
                yaxis2=dict(title='Volume', overlaying='y', side='left', showgrid=False),
                hovermode='x unified',
                legend=dict(orientation='h', yanchor='bottom', y=1.02)
            )
            
            st.plotly_chart(fig_vol, use_container_width=True)
        
        with col2:
            # Volume Profile
            vp = calculate_volume_profile(df.tail(90), bins=15)
            
            fig_vp = go.Figure(go.Bar(
                x=vp['volume'],
                y=vp['price_mid'],
                orientation='h',
                marker_color='#29B6F6',
                opacity=0.7
            ))
            
            # Mark current price
            current_price = df['Close'].iloc[-1]
            fig_vp.add_hline(y=current_price, line_dash="dash", line_color="white", line_width=2,
                            annotation_text=f"Prix: ${current_price:.2f}")
            
            fig_vp.update_layout(
                height=400,
                title="Volume at Price (90j)",
                xaxis_title="Volume",
                yaxis_title="Prix ($)"
            )
            
            st.plotly_chart(fig_vp, use_container_width=True)
        
        # ========================
        # FOOTER
        # ========================
        st.markdown("---")
        st.caption(f"📡 Données: Yahoo Finance | Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.caption("⚠️ Ceci n'est pas un conseil financier. Faites vos propres recherches.")

if __name__ == "__main__":
    main()
