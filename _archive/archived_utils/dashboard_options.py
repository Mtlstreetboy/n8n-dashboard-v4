#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 VISUALISATION INNOVANTE: Prix & Volume des Options
--------------------------------------------------------------------
Représentations multiples pour capturer la complexité:
1. Smile Chart - Volatilité implicite par strike
2. Volume Heatmap - Concentration des volumes
3. Open Interest Ladder - Profondeur du carnet
4. Money Flow - Flux acheteurs/vendeurs
5. 3D Surface - Pattern recognition
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import json
import os
from datetime import datetime
from pathlib import Path

def get_data_dir():
    """Détermine le répertoire de données selon l'environnement (Docker ou local)"""
    # Docker
    if os.path.exists('/data/options_data'):
        return '/data/options_data'
    # Local avec copie des données
    elif os.path.exists('./data_local/options_data'):
        return './data_local/options_data'
    # Fallback: répertoire relatif
    else:
        return os.getenv('OPTIONS_DATA_DIR', './options_data')

OPTIONS_DATA_DIR = get_data_dir()

def get_available_tickers():
    """Récupère la liste des tickers disponibles dans le répertoire de données"""
    try:
        tickers = set()
        for file in os.listdir(OPTIONS_DATA_DIR):
            if file.endswith('_latest_sentiment.json'):
                ticker = file.replace('_latest_sentiment.json', '')
                tickers.add(ticker)
        return sorted(list(tickers))
    except Exception:
        return ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META']  # Fallback

def load_options_data(ticker):
    """Charge les données d'options complètes"""
    calls_file = None
    puts_file = None
    
    # Trouver les fichiers les plus récents
    for file in os.listdir(OPTIONS_DATA_DIR):
        if file.startswith(f'{ticker}_calls_') and file.endswith('.csv'):
            calls_file = os.path.join(OPTIONS_DATA_DIR, file)
        elif file.startswith(f'{ticker}_puts_') and file.endswith('.csv'):
            puts_file = os.path.join(OPTIONS_DATA_DIR, file)
    
    if not calls_file or not puts_file:
        return None, None
    
    calls_df = pd.read_csv(calls_file)
    puts_df = pd.read_csv(puts_file)
    
    return calls_df, puts_df

def get_current_stock_price(ticker):
    """Récupère le prix actuel du stock (approximation depuis les options ATM)"""
    calls_df, puts_df = load_options_data(ticker)
    if calls_df is None or calls_df.empty:
        return None
    
    # Prix approximatif = strike of call et put ont des prix similaires
    # Ou simplement la moyenne des strikes
    return calls_df['strike'].median()

def create_volatility_smile(calls_df, puts_df, current_price):
    """
    VUE 1: VOLATILITY SMILE
    Montre comment l'IV varie selon le strike (détecte la peur/euphorie)
    """
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        subplot_titles=("Volatility Smile - Implied Volatility par Strike", 
                       "Volume Distribution"),
        vertical_spacing=0.15,
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )
    
    # Préparer les données
    calls_sorted = calls_df.sort_values('strike')
    puts_sorted = puts_df.sort_values('strike')
    
    # Calculer moneyness (distance au prix actuel)
    calls_sorted['moneyness'] = (calls_sorted['strike'] - current_price) / current_price * 100
    puts_sorted['moneyness'] = (puts_sorted['strike'] - current_price) / current_price * 100
    
    # Plot 1: IV Smile
    # sanitize volume columns to avoid NaN sizes for marker
    calls_vol = pd.to_numeric(calls_sorted.get('volume', pd.Series([])).fillna(0), errors='coerce').fillna(0)
    puts_vol = pd.to_numeric(puts_sorted.get('volume', pd.Series([])).fillna(0), errors='coerce').fillna(0)

    max_calls_vol = calls_vol.max() if len(calls_vol) else 0
    max_puts_vol = puts_vol.max() if len(puts_vol) else 0

    if max_calls_vol <= 0:
        calls_sizes = np.full(len(calls_sorted), 8)
    else:
        calls_sizes = (calls_vol / max_calls_vol) * 30 + 5

    if max_puts_vol <= 0:
        puts_sizes = np.full(len(puts_sorted), 8)
    else:
        puts_sizes = (puts_vol / max_puts_vol) * 30 + 5

    fig.add_trace(
        go.Scatter(
            x=calls_sorted['strike'],
            y=calls_sorted['impliedVolatility'],
            mode='markers+lines',
            name='Calls IV',
            marker=dict(
                size=calls_sizes,
                color=calls_vol,
                colorscale='Greens',
                showscale=False,
                line=dict(width=1, color='white')
            ),
            line=dict(color='#00C853', width=2),
            hovertemplate='<b>Call Strike: %{x:.2f}</b><br>' +
                         'IV: %{y:.2%}<br>' +
                         'Volume: %{marker.color:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=puts_sorted['strike'],
            y=puts_sorted['impliedVolatility'],
            mode='markers+lines',
            name='Puts IV',
            marker=dict(
                size=puts_sizes,
                color=puts_vol,
                colorscale='Reds',
                showscale=False,
                line=dict(width=1, color='white')
            ),
            line=dict(color='#DD2C00', width=2),
            hovertemplate='<b>Put Strike: %{x:.2f}</b><br>' +
                         'IV: %{y:.2%}<br>' +
                         'Volume: %{marker.color:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Ligne du prix actuel
    fig.add_vline(
        x=current_price,
        line_dash="dash",
        line_color="yellow",
        annotation_text=f"Prix Actuel: ${current_price:.2f}",
        annotation_position="top",
        row=1, col=1
    )
    
    # Plot 2: Volume Distribution (bars)
    fig.add_trace(
        go.Bar(
            x=calls_sorted['strike'],
            y=calls_sorted['volume'],
            name='Call Volume',
            marker_color='rgba(0, 200, 83, 0.6)',
            hovertemplate='Strike: %{x:.2f}<br>Volume: %{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=puts_sorted['strike'],
            y=-puts_sorted['volume'],  # Négatif pour montrer en dessous
            name='Put Volume',
            marker_color='rgba(221, 44, 0, 0.6)',
            hovertemplate='Strike: %{x:.2f}<br>Volume: %{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.add_vline(x=current_price, line_dash="dash", line_color="yellow", row=2, col=1)
    
    # Layout
    fig.update_xaxes(title_text="Strike Price ($)", row=2, col=1)
    fig.update_yaxes(title_text="Implied Volatility", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    fig.update_layout(
        height=800,
        showlegend=True,
        hovermode='x unified',
        title_text="Volatility Smile & Volume Distribution"
    )
    
    return fig

def create_option_heatmap(calls_df, puts_df, current_price):
    """
    VUE 2: HEATMAP VOLUME/PRIX
    Visualise où se concentrent les positions (support/résistance)
    """
    # Créer des bins pour les strikes
    all_strikes = pd.concat([calls_df['strike'], puts_df['strike']]).unique()
    all_strikes.sort()
    
    # Préparer les données pour heatmap
    expirations = sorted(calls_df['expiration'].unique())[:10]  # Limiter à 10 expirations
    
    # Matrices pour calls et puts
    call_matrix = []
    put_matrix = []
    
    for exp in expirations:
        calls_exp = calls_df[calls_df['expiration'] == exp]
        puts_exp = puts_df[puts_df['expiration'] == exp]
        
        call_row = []
        put_row = []
        
        for strike in all_strikes:
            call_vol = calls_exp[calls_exp['strike'] == strike]['volume'].sum()
            put_vol = puts_exp[puts_exp['strike'] == strike]['volume'].sum()
            
            call_row.append(call_vol)
            put_row.append(put_vol)
        
        call_matrix.append(call_row)
        put_matrix.append(put_row)
    
    # Créer le subplot
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("📈 Calls Volume Heatmap", "📉 Puts Volume Heatmap"),
        horizontal_spacing=0.1
    )
    
    # Heatmap Calls
    fig.add_trace(
        go.Heatmap(
            z=call_matrix,
            x=all_strikes,
            y=expirations,
            colorscale='Greens',
            name='Calls',
            hovertemplate='Strike: %{x:.2f}<br>Expiration: %{y}<br>Volume: %{z:,.0f}<extra></extra>',
            colorbar=dict(title="Volume", x=0.45)
        ),
        row=1, col=1
    )
    
    # Heatmap Puts
    fig.add_trace(
        go.Heatmap(
            z=put_matrix,
            x=all_strikes,
            y=expirations,
            colorscale='Reds',
            name='Puts',
            hovertemplate='Strike: %{x:.2f}<br>Expiration: %{y}<br>Volume: %{z:,.0f}<extra></extra>',
            colorbar=dict(title="Volume", x=1.02)
        ),
        row=1, col=2
    )
    
    # Ligne du prix actuel
    fig.add_vline(x=current_price, line_dash="dash", line_color="yellow", row=1, col=1)
    fig.add_vline(x=current_price, line_dash="dash", line_color="yellow", row=1, col=2)
    
    fig.update_xaxes(title_text="Strike Price", row=1, col=1)
    fig.update_xaxes(title_text="Strike Price", row=1, col=2)
    fig.update_yaxes(title_text="Expiration", row=1, col=1)
    
    fig.update_layout(
        height=600,
        title_text="Option Volume Heatmap - Zones de Concentration"
    )
    
    return fig

def create_open_interest_ladder(calls_df, puts_df, current_price):
    """
    VUE 3: OPEN INTEREST LADDER
    Montre la profondeur des positions (max pain, support/résistance)
    """
    # Grouper par strike
    calls_by_strike = calls_df.groupby('strike').agg({
        'openInterest': 'sum',
        'volume': 'sum',
        'lastPrice': 'mean'
    }).reset_index()
    
    puts_by_strike = puts_df.groupby('strike').agg({
        'openInterest': 'sum',
        'volume': 'sum',
        'lastPrice': 'mean'
    }).reset_index()
    
    # Calculer le notional value (OI × Prix × 100)
    calls_by_strike['notional'] = calls_by_strike['openInterest'] * calls_by_strike['lastPrice'] * 100
    puts_by_strike['notional'] = puts_by_strike['openInterest'] * puts_by_strike['lastPrice'] * 100
    
    # Calculer max pain (strike où OI total est maximum)
    merged = pd.merge(
        calls_by_strike[['strike', 'openInterest']].rename(columns={'openInterest': 'call_oi'}),
        puts_by_strike[['strike', 'openInterest']].rename(columns={'openInterest': 'put_oi'}),
        on='strike',
        how='outer'
    ).fillna(0)
    
    merged['total_oi'] = merged['call_oi'] + merged['put_oi']
    max_pain = merged.loc[merged['total_oi'].idxmax(), 'strike']
    
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.6, 0.4],
        subplot_titles=(
            "Open Interest Ladder (Profondeur des Positions)",
            "Notional Value ($ en jeu)"
        ),
        vertical_spacing=0.12
    )
    
    # Plot 1: OI Ladder
    fig.add_trace(
        go.Bar(
            x=calls_by_strike['strike'],
            y=calls_by_strike['openInterest'],
            name='Call OI',
            marker_color='rgba(0, 200, 83, 0.7)',
            text=calls_by_strike['openInterest'],
            texttemplate='%{text:,.0f}',
            textposition='outside',
            hovertemplate='<b>Call</b><br>Strike: %{x:.2f}<br>OI: %{y:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=puts_by_strike['strike'],
            y=-puts_by_strike['openInterest'],  # Négatif
            name='Put OI',
            marker_color='rgba(221, 44, 0, 0.7)',
            text=puts_by_strike['openInterest'],
            texttemplate='%{text:,.0f}',
            textposition='outside',
            hovertemplate='<b>Put</b><br>Strike: %{x:.2f}<br>OI: %{y:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Plot 2: Notional Value
    fig.add_trace(
        go.Scatter(
            x=calls_by_strike['strike'],
            y=calls_by_strike['notional'],
            mode='lines+markers',
            name='Call Notional',
            line=dict(color='#00C853', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(0, 200, 83, 0.2)',
            hovertemplate='<b>Call Notional</b><br>Strike: %{x:.2f}<br>Value: $%{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=puts_by_strike['strike'],
            y=puts_by_strike['notional'],
            mode='lines+markers',
            name='Put Notional',
            line=dict(color='#DD2C00', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(221, 44, 0, 0.2)',
            hovertemplate='<b>Put Notional</b><br>Strike: %{x:.2f}<br>Value: $%{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Lignes de référence
    fig.add_vline(x=current_price, line_dash="dash", line_color="yellow", 
                  annotation_text=f"Prix: ${current_price:.2f}", row=1, col=1)
    fig.add_vline(x=max_pain, line_dash="dot", line_color="orange",
                  annotation_text=f"Max Pain: ${max_pain:.2f}", row=1, col=1)
    
    fig.add_vline(x=current_price, line_dash="dash", line_color="yellow", row=2, col=1)
    fig.add_vline(x=max_pain, line_dash="dot", line_color="orange", row=2, col=1)
    
    # Layout
    fig.update_xaxes(title_text="Strike Price", row=2, col=1)
    fig.update_yaxes(title_text="Open Interest", row=1, col=1)
    fig.update_yaxes(title_text="Notional Value ($)", row=2, col=1)
    
    fig.update_layout(
        height=900,
        showlegend=True,
        title_text=f"Open Interest Ladder - Max Pain 📉 ${max_pain:.2f}"
    )
    
    return fig

def create_money_flow_analysis(calls_df, puts_df, current_price):
    """
    VUE 4: MONEY FLOW ANALYSIS
    Détecte les flux d'argent (acheteurs vs vendeurs)
    """
    # Calculer le money flow: (Prix x Volume) avec direction
    # Si bid < ask significativement = acheteurs agressifs
    # Si ask < bid significativement = vendeurs agressifs
    
    # Approximation: utiliser lastPrice et volume
    calls_df['call_flow'] = calls_df['lastPrice'] * calls_df['volume'] * 100
    puts_df['put_flow'] = puts_df['lastPrice'] * puts_df['volume'] * 100
    
    # Grouper par moneyness zones
    def categorize_moneyness(strike, current):
        diff_pct = (strike - current) / current * 100
        if diff_pct < -10:
            return 'Deep OTM'
        elif diff_pct < -2:
            return 'OTM'
        elif diff_pct < 2:
            return 'ATM'
        elif diff_pct < 10:
            return 'ITM'
        else:
            return 'Deep ITM'
    
    calls_df['moneyness'] = calls_df['strike'].apply(lambda x: categorize_moneyness(x, current_price))
    puts_df['moneyness'] = puts_df['strike'].apply(lambda x: categorize_moneyness(x, current_price))
    
    # Agréger par moneyness
    call_flow_by_moneyness = calls_df.groupby('moneyness')['call_flow'].sum()
    put_flow_by_moneyness = puts_df.groupby('moneyness')['put_flow'].sum()
    
    # Ordre logique
    moneyness_order = ['Deep OTM', 'OTM', 'ATM', 'ITM', 'Deep ITM']
    
    fig = go.Figure()
    
    # Calls (positif)
    fig.add_trace(go.Bar(
        x=moneyness_order,
        y=[call_flow_by_moneyness.get(m, 0) for m in moneyness_order],
        name='Call Money Flow',
        marker_color='#00C853',
        text=[f"${call_flow_by_moneyness.get(m, 0)/1e6:.1f}M" for m in moneyness_order],
        textposition='outside',
        hovertemplate='<b>Calls - %{x}</b><br>Flow: $%{y:,.0f}<extra></extra>'
    ))
    
    # Puts (négatif pour contraste)
    fig.add_trace(go.Bar(
        x=moneyness_order,
        y=[-put_flow_by_moneyness.get(m, 0) for m in moneyness_order],
        name='Put Money Flow',
        marker_color='#DD2C00',
        text=[f"${put_flow_by_moneyness.get(m, 0)/1e6:.1f}M" for m in moneyness_order],
        textposition='outside',
        hovertemplate='<b>Puts - %{x}</b><br>Flow: $%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="📊 Money Flow by Moneyness - Où va l'argent?",
        xaxis_title="Moneyness Zone",
        yaxis_title="Money Flow ($)",
        height=600,
        barmode='relative',
        hovermode='x unified'
    )
    
    # Annotations
    total_call_flow = calls_df['call_flow'].sum()
    total_put_flow = puts_df['put_flow'].sum()
    ratio = total_call_flow / max(total_put_flow, 1)
    
    fig.add_annotation(
        text=f"Total Call Flow: ${total_call_flow/1e6:.1f}M<br>" +
             f"Total Put Flow: ${total_put_flow/1e6:.1f}M<br>" +
             f"Ratio: {ratio:.2f}x",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1
    )
    
    return fig

def create_price_volume_3d(calls_df, puts_df, current_price):
    """
    VUE 5: 3D SURFACE - Prix/Volume/Expiration
    Vue tridimensionnelle pour pattern recognition
    """
    # Préparer les données
    expirations = sorted(calls_df['expiration'].unique())[:5]  # Prendre les 5 premières expirations
    
    # Créer une grille
    strikes = sorted(calls_df['strike'].unique())
    
    # Matrices 3D
    call_surface = []
    put_surface = []
    
    for exp in expirations:
        call_row = []
        put_row = []
        
        for strike in strikes:
            call_vol = calls_df[(calls_df['expiration'] == exp) & (calls_df['strike'] == strike)]['volume'].sum()
            put_vol = puts_df[(puts_df['expiration'] == exp) & (puts_df['strike'] == strike)]['volume'].sum()
            
            call_row.append(call_vol)
            put_row.append(put_vol)
        
        call_surface.append(call_row)
        put_surface.append(put_row)
    
    # Créer le subplot 3D
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'surface'}, {'type': 'surface'}]],
        subplot_titles=("📊 Calls Volume 3D", "📊 Puts Volume 3D")
    )
    
    # Surface Calls
    fig.add_trace(
        go.Surface(
            z=call_surface,
            x=strikes,
            y=expirations,
            colorscale='Greens',
            name='Calls',
            hovertemplate='Strike: %{x:.2f}<br>Exp: %{y}<br>Volume: %{z:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Surface Puts
    fig.add_trace(
        go.Surface(
            z=put_surface,
            x=strikes,
            y=expirations,
            colorscale='Reds',
            name='Puts',
            hovertemplate='Strike: %{x:.2f}<br>Exp: %{y}<br>Volume: %{z:,.0f}<extra></extra>'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title="📊 3D Volume Surface - Pattern Recognition",
        height=600,
        scene=dict(
            xaxis_title='Strike',
            yaxis_title='Expiration',
            zaxis_title='Volume'
        ),
        scene2=dict(
            xaxis_title='Strike',
            yaxis_title='Expiration',
            zaxis_title='Volume'
        )
    )
    
    return fig

def calculate_composite_score(calls_df, puts_df, current_price):
    """
    Calcule un score composite bas sur les 5 vues
    """
    scores = {}
    
    # 1. Volatility Skew (25%)
    call_iv_mean = calls_df['impliedVolatility'].mean()
    put_iv_mean = puts_df['impliedVolatility'].mean()
    iv_skew = (put_iv_mean - call_iv_mean) / max(call_iv_mean, 0.01)
    scores['volatility_skew'] = -iv_skew  # Négatif = bearish (puts chers)
    
    # 2. Max Pain Distance (20%)
    calls_by_strike = calls_df.groupby('strike')['openInterest'].sum()
    puts_by_strike = puts_df.groupby('strike')['openInterest'].sum()
    merged = pd.DataFrame({
        'call_oi': calls_by_strike,
        'put_oi': puts_by_strike
    }).fillna(0)
    merged['total_oi'] = merged['call_oi'] + merged['put_oi']
    max_pain = merged['total_oi'].idxmax()
    max_pain_distance = (current_price - max_pain) / current_price
    scores['max_pain_distance'] = max_pain_distance
    
    # 3. Money Flow Ratio (30%)
    call_flow = (calls_df['lastPrice'] * calls_df['volume']).sum()
    put_flow = (puts_df['lastPrice'] * puts_df['volume']).sum()
    flow_ratio = (call_flow - put_flow) / (call_flow + put_flow + 1)
    scores['money_flow_ratio'] = flow_ratio
    
    # 4. Volume Concentration (25%)
    # Calculer où se concentre le volume (OTM calls = bullish)
    def get_moneyness_category(strike, current):
        diff_pct = (strike - current) / current * 100
        if diff_pct < -2:
            return 'OTM'
        elif diff_pct < 2:
            return 'ATM'
        else:
            return 'ITM'
    
    calls_df['money_cat'] = calls_df['strike'].apply(lambda x: get_moneyness_category(x, current_price))
    puts_df['money_cat'] = puts_df['strike'].apply(lambda x: get_moneyness_category(x, current_price))
    
    call_otm_vol = calls_df[calls_df['money_cat'] == 'OTM']['volume'].sum()
    put_otm_vol = puts_df[puts_df['money_cat'] == 'OTM']['volume'].sum()
    
    total_vol = calls_df['volume'].sum() + puts_df['volume'].sum()
    volume_concentration = (call_otm_vol - put_otm_vol) / max(total_vol, 1)
    scores['volume_concentration'] = volume_concentration
    
    # Score composite final
    composite = (
        scores['volatility_skew'] * 0.25 +
        scores['max_pain_distance'] * 0.20 +
        scores['money_flow_ratio'] * 0.30 +
        scores['volume_concentration'] * 0.25
    )
    
    scores['composite'] = composite
    
    return scores

# === STREAMLIT APP ===
def main():
    st.set_page_config(page_title="Options Analysis", layout="wide", page_icon="📊")
    
    st.title("Analyse Innovante des Options - 5 Vues Complémentaires")
    st.markdown("---")
    
    # Récupérer les tickers disponibles
    available_tickers = get_available_tickers()
    
    # Sélection du ticker
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.selectbox(
            "Sélectionner un ticker",
            options=available_tickers,
            index=0 if available_tickers else None
        )
    with col2:
        if st.button("📊 Analyser", type="primary", use_container_width=True):
            st.rerun()
    
    if ticker:
        with st.spinner(f'Chargement des données pour {ticker}...'):
            calls_df, puts_df = load_options_data(ticker)
        
        if calls_df is None or puts_df is None or calls_df.empty or puts_df.empty:
            st.error(f"❌ Aucune donnée d'options pour {ticker}")
            st.info("📢 Lancez d'abord: `docker exec n8n_data_architect python3 /data/scripts/collect_options.py`")
            return
        
        current_price = get_current_stock_price(ticker)
        
        if current_price is None:
            st.error("❌ Impossible de déterminer le prix actuel")
            return
        
        # Calculer le score composite
        scores = calculate_composite_score(calls_df.copy(), puts_df.copy(), current_price)
        
        # Métriques clés
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Prix Estimé", f"${current_price:.2f}")
        
        with col2:
            total_call_vol = calls_df['volume'].sum()
            st.metric("Call Volume", f"{total_call_vol:,.0f}")
        
        with col3:
            total_put_vol = puts_df['volume'].sum()
            st.metric("Put Volume", f"{total_put_vol:,.0f}")
        
        with col4:
            pcr = total_put_vol / max(total_call_vol, 1)
            st.metric("Put/Call Ratio", f"{pcr:.2f}")
        
        with col5:
            composite = scores['composite']
            sentiment = "📈 Bullish" if composite > 0.15 else "📉 Bearish" if composite < -0.15 else "⚖️ Neutral"
            st.metric("Options Score", f"{composite:.2f}", sentiment)
        
        # Score détaillé
        with st.expander("📊 Décomposition du Score Composite"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Volatility Skew", f"{scores['volatility_skew']:.2f}", "25%")
            with col2:
                st.metric("Max Pain Distance", f"{scores['max_pain_distance']:.2%}", "20%")
            with col3:
                st.metric("Money Flow Ratio", f"{scores['money_flow_ratio']:.2f}", "30%")
            with col4:
                st.metric("Volume Concentration", f"{scores['volume_concentration']:.2f}", "25%")
            
            st.markdown("""
            **Interprétation:**
            - **Score > 0.15** = Configuration Bullish
            - **Score -0.15 ?? 0.15** = Neutre/Indécis
            - **Score < -0.15** = Configuration Bearish
            """)
        
        st.markdown("---")
        
        # Tabs pour les différentes vues
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Volatility Smile",
            "📊 Volume Heatmap",
            "📉 Open Interest",
            "📊 Money Flow",
            "📊 3D Surface"
        ])
        
        with tab1:
            st.plotly_chart(
                create_volatility_smile(calls_df, puts_df, current_price),
                use_container_width=True
            )
            
            st.markdown("""
            ### 📈 Interprétation:
            - **Smile prononcé** = Marché nerveux, attend de gros mouvements
            - **Volume élevé OTM** = Spéculation ou hedging
            - **IV élevé Put vs Call** = Peur, protection baissière
            - **Taille des bulles** = Importance du volume à ce strike
            """)
        
        with tab2:
            st.plotly_chart(
                create_option_heatmap(calls_df, puts_df, current_price),
                use_container_width=True
            )
            
            st.markdown("""
            ### 📊 Interprétation:
            - **Zones chaudes (rouge foncé)** = Concentration de positions (support/résistance magnétique)
            - **Mur de calls** = Résistance potentielle
            - **Mur de puts** = Support potentiel
            - **Concentration temporelle** = Événement attendu (earnings, annonce)
            """)
        
        with tab3:
            st.plotly_chart(
                create_open_interest_ladder(calls_df, puts_df, current_price),
                use_container_width=True
            )
            
            st.markdown("""
            ### 📉 Interprétation:
            - **Max Pain** = Strike où les market makers perdent le moins (attraction magnétique)
            - **OI élevé** = Support/résistance forte
            - **Notional Value** = Argent réellement en jeu (stake des positions)
            - **Asymétrie** = Direction probable du marché
            """)
        
        with tab4:
            st.plotly_chart(
                create_money_flow_analysis(calls_df, puts_df, current_price),
                use_container_width=True
            )
            
            st.markdown("""
            ### 📊 Interprétation:
            - **Flow ATM élevé** = Trading actif, momentum fort
            - **Flow OTM calls** = Spéculation haussière (lottery tickets)
            - **Flow ITM puts** = Protection institutionnelle ou bearish conviction
            - **Ratio déséquilibré** = Direction claire du smart money
            """)
        
        with tab5:
            st.plotly_chart(
                create_price_volume_3d(calls_df, puts_df, current_price),
                use_container_width=True
            )
            
            st.markdown("""
            ### 📊 Interprétation:
            - **Pics 3D** = Zones de forte activité (intérêt massif)
            - **Vallées** = Strikes ignorés
            - **Pente temporelle** = Évolution des attentes dans le temps
            - **Patterns** = Formations répétitives (ex: escalier = hedging progressif)
            """)
        
        # Section Scénarios
        st.markdown("---")
        st.subheader("📊 Scénarios Détectés")
        
        # Analyser les patterns
        composite = scores['composite']
        iv_skew = scores['volatility_skew']
        flow_ratio = scores['money_flow_ratio']
        
        scenarios = []
        
        # Scénario Bullish
        if composite > 0.2 and flow_ratio > 0.2:
            scenarios.append({
                'type': '📈 BULLISH SETUP',
                'confidence': 'Élevée',
                'indicators': [
                    f"📊 Score Composite: {composite:.2f}",
                    f"📊 Money Flow Ratio: {flow_ratio:.2f}",
                    f"📊 Volume Concentration: {scores['volume_concentration']:.2f}"
                ],
                'signal': 'FORTE CONVICTION BULLISH - Calls dominants'
            })
        
        # Scénario Bearish
        if composite < -0.2 and iv_skew < -0.1:
            scenarios.append({
                'type': '📉 BEARISH HEDGE',
                'confidence': 'Élevée',
                'indicators': [
                    f"📊 Score Composite: {composite:.2f}",
                    f"📊 Volatility Skew: {iv_skew:.2f}",
                    f"📊 Money Flow Ratio: {flow_ratio:.2f}"
                ],
                'signal': 'PROTECTION MASSIVE - Puts dominants'
            })
        
        # Scénario Squeeze
        if abs(composite) < 0.1 and abs(flow_ratio) < 0.1:
            scenarios.append({
                'type': '🤏 SQUEEZE SETUP',
                'confidence': 'Moyenne',
                'indicators': [
                    f"🤏 Score Composite proche de 0: {composite:.2f}",
                    f"🤏 Flow déséquilibré: {flow_ratio:.2f}",
                    f"🤏 Max Pain proche: {scores['max_pain_distance']:.2%}"
                ],
                'signal': 'COMPRESSION - Breakout imminent'
            })
        
        if scenarios:
            for scenario in scenarios:
                with st.expander(f"{scenario['type']} - Confiance: {scenario['confidence']}"):
                    for indicator in scenario['indicators']:
                        st.markdown(indicator)
                    st.info(f"**Signal:** {scenario['signal']}")
        else:
            st.info("Aucun scénario clair détecté - Marché indécis")

if __name__ == "__main__":
    main()
