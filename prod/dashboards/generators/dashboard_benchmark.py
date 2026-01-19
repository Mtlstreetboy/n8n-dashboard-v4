import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import json
from datetime import datetime, timedelta
import sys
import os

# Configuration pour importer companies_config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from prod.config.companies_config import AI_COMPANIES

# Setup Streamlit
st.set_page_config(page_title="Benchmark vs VOO", layout="wide", page_icon="⚖️")

# Force Dark Mode for Plotly
import plotly.io as pio
pio.templates.default = "plotly_dark"

def get_tickers():
    """Extract tickers from config"""
    tickers = [c['ticker'] for c in AI_COMPANIES if c.get('ticker')]
    return sorted(list(set(tickers)))

def load_data(ticker, benchmark, start_date):
    """Fetch data from Yahoo Finance"""
    tickers = [ticker, benchmark]
    try:
        data = yf.download(tickers, start=start_date, progress=False)['Close']
        if data.empty:
            return None
        return data
    except Exception as e:
        st.error(f"Erreur de chargement: {e}")
        return None



def load_portfolio_config():
    """Load portfolio data from JSON"""
    portfolio_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../prod/config/portfolio_holdings.json'))
    if os.path.exists(portfolio_file):
        with open(portfolio_file, 'r') as f:
            return json.load(f)
    return []

def main():
    st.title("⚖️ Benchmark Deep Dive: Alpha & Performance")
    
    # Sidebar Controls
    with st.sidebar:
        st.header("Configuration")
        
        # Mode Selection
        mode = st.radio("Mode d'analyse", ["Ticker Unique", "Portfolio Global"])
        st.divider()
        
        benchmark_ticker = st.selectbox("Benchmark", ["VOO", "SPY", "QQQ"], index=0)
        
        # Date Selection (Default: 2026-01-01 as requested)
        default_start = datetime(2026, 1, 1)
        start_date = st.date_input("Date de début", default_start)
        st.info(f"📅 Analyse depuis le: **{start_date}**")

    # --- MODE 1: TICKER UNIQUE ---
    if mode == "Ticker Unique":
        with st.sidebar:
            st.divider()
            # Ticker Selection
            available_tickers = get_tickers()
            
            # Handle URL Query Params
            query_params = st.query_params
            default_index = 0
            
            if "ticker" in query_params:
                url_ticker = query_params["ticker"]
                if url_ticker in available_tickers:
                    default_index = available_tickers.index(url_ticker)
                elif "NVDA" in available_tickers: 
                    default_index = available_tickers.index("NVDA")
            elif "NVDA" in available_tickers:
                default_index = available_tickers.index("NVDA")
                
            selected_ticker = st.selectbox("Ticker Cible", available_tickers, index=default_index)

        if selected_ticker and benchmark_ticker:
            st.subheader(f"Comparaison Individuelle: {selected_ticker} vs {benchmark_ticker}")
            st.markdown("---")
            
            # Load Data
            df = load_data(selected_ticker, benchmark_ticker, start_date)
            
            if df is None or len(df) == 0:
                st.warning("Aucune donnée disponible pour cette période.")
                return

            if selected_ticker == benchmark_ticker:
                st.warning("Veuillez choisir un benchmark différent du ticker.")
                return
                
            # Data Processing
            df_norm = df / df.iloc[0] * 100
            rs_ratio = df[selected_ticker] / df[benchmark_ticker]
            
            # Helper for metrics
            def calc_ret(series): return (series.iloc[-1] / series.iloc[0] - 1) * 100
            
            ticker_ret = calc_ret(df[selected_ticker])
            bench_ret = calc_ret(df[benchmark_ticker])
            alpha = ticker_ret - bench_ret

            # KPI ROW
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric(f"Perf {selected_ticker}", f"{ticker_ret:+.2f}%")
            with col2: st.metric(f"Perf {benchmark_ticker}", f"{bench_ret:+.2f}%")
            with col3: st.metric("Alpha", f"{alpha:+.2f}%", delta="Lead" if alpha > 0 else "Lag")
            with col4: st.metric("Corrélation", f"{df[selected_ticker].corr(df[benchmark_ticker]):.2f}")

            # PORTFOLIO CONTEXT
            port_data = load_portfolio_config()
            holding = next((item for item in port_data if item["ticker"] == selected_ticker), None)
            
            # CHART 1
            fig_perf = go.Figure()
            fig_perf.add_trace(go.Scatter(x=df_norm.index, y=df_norm[selected_ticker], name=selected_ticker, line=dict(width=3, color='#00C853')))
            fig_perf.add_trace(go.Scatter(x=df_norm.index, y=df_norm[benchmark_ticker], name=benchmark_ticker, line=dict(width=2, color='#B0BEC5', dash='dot')))
            
            if holding:
                avg_price = holding['avg_price']
                start_price = df[selected_ticker].iloc[0]
                avg_price_norm = (avg_price / start_price) * 100
                current_price = df[selected_ticker].iloc[-1]
                pl_pct = (current_price - avg_price) / avg_price * 100
                color_pl = "#00E676" if pl_pct >= 0 else "#FF1744"
                
                fig_perf.add_hline(y=avg_price_norm, line_dash="longdash", line_color=color_pl, line_width=1,
                    annotation_text=f"PRU: ${avg_price:.2f} ({pl_pct:+.2f}%)", annotation_position="bottom right", annotation_font_color=color_pl)
                st.success(f"💼 **Position Portfolio** : {holding['qty']} actions @ ${avg_price:.2f}. P/L: **{pl_pct:+.2f}%**")

            fig_perf.update_layout(height=500, hovermode="x unified", title="Comparaison Base 100")
            st.plotly_chart(fig_perf, use_container_width=True)
            
            # CHART 2
            fig_rs = go.Figure()
            fig_rs.add_trace(go.Scatter(x=rs_ratio.index, y=rs_ratio, name='RS Ratio', line=dict(color='#29B6F6', width=2), fill='tozeroy', fillcolor='rgba(41, 182, 246, 0.1)'))
            fig_rs.add_trace(go.Scatter(x=rs_ratio.rolling(20).mean().index, y=rs_ratio.rolling(20).mean(), name='Trend (20d)', line=dict(color='white', width=1, dash='dash')))
            fig_rs.update_layout(height=400, hovermode="x unified", title="Force Relative (Ratio)")
            st.plotly_chart(fig_rs, use_container_width=True)

    # --- MODE 2: PORTFOLIO GLOBAL ---
    else:
        st.subheader("🌍 Performance Globale du Portefeuille")
        st.markdown("---")
        
        # Load Portfolio
        port_data = load_portfolio_config()
        if not port_data:
            st.error("Aucune donnée de portfolio trouvée.")
            return

        with st.spinner("Téléchargement des données pour tout le portfolio (avec conversion CAD)..."):
            tickers = [item['ticker'] for item in port_data]
            # Add Exchange Rate and Benchmark
            all_tickers = list(set(tickers + [benchmark_ticker, "CAD=X"]))
            
            try:
                # Batch Download
                data = yf.download(all_tickers, start=start_date, progress=False)['Close']
                
                # Fill missing data
                data = data.ffill().dropna()
                
            except Exception as e:
                st.error(f"Erreur téléchargement batch: {e}")
                return

        # Calculate Portfolio Value Series (Normalized to CAD)
        # Value(t) = Sum(Qty_i * Price_i(t) * ExchangeRate(t))
        portfolio_series = pd.Series(0, index=data.index, name="Portfolio (CAD)")
        
        # Get USD/CAD Rate
        if "CAD=X" in data.columns:
            # CAD=X gives USD to CAD rate (approx 1.30-1.40)
            usdcad = data["CAD=X"]
        else:
            usdcad = pd.Series(1.40, index=data.index) # Fallback if fails
        
        weights = {}
        
        for item in port_data:
            t = item['ticker']
            q = item['qty']
            
            if t in data.columns:
                price_series = data[t]
                
                # Determine Currency & Convert if needed
                # Assumption: Tickers ending in .TO are CAD, others are USD
                # VOO/SPY are USD.
                is_cad = t.endswith(".TO")
                
                if is_cad:
                    # Already in CAD
                    val_series = price_series * q
                    curr_val = val_series.iloc[-1]
                else:
                    # Convert USD to CAD
                    val_series = price_series * q * usdcad
                    curr_val = val_series.iloc[-1]
                
                # Add to total
                portfolio_series += val_series
                weights[t] = curr_val
                
            else:
                st.warning(f"Ticker introuvable ou sans données: {t}")

        # Benchmark comparison (Base 100)
        # We compare Total Portfolio (CAD) vs Benchmark (USD or CAD?)
        # Standard practice: Compare relative performance (%), so currency doesn't matter for the shape of the curve
        # BUT for Alpha, we should compare apples to apples.
        # If VOO is in USD, we simply compare the % change of Portfolio(CAD) vs % change of VOO(USD).
        # This shows "Did my CAD portfolio grow faster than the USD index?" 
        # (ignoring currency hedging for the benchmark itself for simplicity, unless we convert VOO to CAD too)
        
        # Let's convert Benchmark to CAD for fair comparison if it's VOO/SPY
        bench_is_cad = benchmark_ticker.endswith(".TO")
        if not bench_is_cad:
             bench_series_cad = data[benchmark_ticker] * usdcad
        else:
             bench_series_cad = data[benchmark_ticker]

        port_norm = portfolio_series / portfolio_series.iloc[0] * 100
        bench_norm = bench_series_cad / bench_series_cad.iloc[0] * 100
        
        # Metrics
        total_val = portfolio_series.iloc[-1]
        start_val = portfolio_series.iloc[0]
        port_ret = (total_val / start_val - 1) * 100
        bench_ret = (bench_series_cad.iloc[-1] / bench_series_cad.iloc[0] - 1) * 100
        alpha_port = port_ret - bench_ret
        
        # DISPLAY
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Valeur Totale (CAD)", f"${total_val:,.2f}", f"{port_ret:+.2f}%")
        with c2: st.metric(f"Perf {benchmark_ticker} (en CAD)", f"{bench_ret:+.2f}%")
        with c3: st.metric("Alpha Portfolio", f"{alpha_port:+.2f}%", delta="Winning" if alpha_port > 0 else "Losing")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # CHART: Portfolio vs Benchmark
            st.markdown("### 📈 VS Benchmark (Base 100)")
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=port_norm.index, y=port_norm, name="Mon Portfolio", line=dict(color="#00C853", width=4)))
            fig_p.add_trace(go.Scatter(x=bench_norm.index, y=bench_norm, name=benchmark_ticker, line=dict(color="#B0BEC5", width=2, dash="dot")))
            fig_p.update_layout(height=450, hovermode="x unified")
            st.plotly_chart(fig_p, use_container_width=True)
            
        with col2:
            # Generate consistent color map for Portfolio items
            unique_tickers = sorted(list(weights.keys()))
            # Use Plotly qualitative palette
            palette = px.colors.qualitative.Plotly
            # Map each ticker to a color
            color_map = {ticker: palette[i % len(palette)] for i, ticker in enumerate(unique_tickers)}

            # PIE: Composition
            st.markdown("### 🍰 Allocation Actuelle")
            df_weights = pd.DataFrame.from_dict(weights, orient='index', columns=['Value'])
            df_weights = df_weights.sort_values('Value', ascending=False)
            
            # Use the color_map in the PIE chart
            # We must ensure specific colors are assigned to specific index labels
            fig_pie = px.pie(df_weights, values='Value', names=df_weights.index, hole=0.4, 
                             color=df_weights.index, color_discrete_map=color_map)
            
            fig_pie.update_layout(height=450, showlegend=False)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            

            

            
        # SPAGHETTI CHART
        st.markdown("### 🍝 Tous les titres (Base 100)")
        fig_s = go.Figure()
        
        # Add Benchmark first
        fig_s.add_trace(go.Scatter(x=bench_norm.index, y=bench_norm, name=benchmark_ticker, line=dict(color="white", width=4, dash='solid'), opacity=1.0))
        
        start_prices = data.iloc[0]
        data_norm = data / start_prices * 100
        
        for t in data.columns:
            if t == benchmark_ticker or t == "CAD=X": continue
            
            # Use the same color map
            # If t is not in portfolio (maybe removed since start date?), fallback to grey
            color = color_map.get(t, "rgba(128, 128, 128, 0.5)")
            
            width = 1.5
            opacity = 0.8
            
            # Highlight NVDA or big weights
            if t in ["NVDA", "VOO", "GOOGL"]: width=2.5
            
            fig_s.add_trace(go.Scatter(
                x=data_norm.index, 
                y=data_norm[t], 
                name=t, 
                line=dict(color=color, width=width), 
                opacity=opacity,
                hovertemplate=f"<b>{t}</b>: %{{y:.1f}}<extra></extra>"
            ))
            
        fig_s.update_layout(height=600, hovermode="x unified", showlegend=False)
        st.plotly_chart(fig_s, use_container_width=True)

if __name__ == "__main__":
    main()
