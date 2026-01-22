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
st.set_page_config(page_title="Benchmark Thématique (Equal-Weight)", layout="wide", page_icon="⚖️")

# Force Dark Mode for Plotly
import plotly.io as pio
pio.templates.default = "plotly_dark"

INITIAL_INVESTMENT_PER_TICKER = 1000.0

def get_tickers_config():
    """Extract tickers and metadata from config"""
    # On filtre les tickers vides ou invalides
    valid_companies = [c for c in AI_COMPANIES if c.get('ticker')]
    return valid_companies

def load_data(tickers, benchmark, start_date):
    """Fetch data from Yahoo Finance"""
    all_tickers = list(set(tickers + [benchmark, "CAD=X"]))
    
    try:
        # On recupere un peu avant pour etre sur d'avoir le 1er Janvier (ou premier jour ouvré)
        fetch_start = start_date - timedelta(days=5)
        data = yf.download(all_tickers, start=fetch_start, progress=False)['Close']
        
        # Filtrer pour ne garder qu'à partir de la date demandée
        data = data[data.index >= pd.Timestamp(start_date)]
        
        # Fill missing data (forward fill puis backward fill pour le début si besoin)
        data = data.ffill().bfill()
        
        return data
    except Exception as e:
        st.error(f"Erreur de chargement: {e}")
        return None

def main():
    st.title("⚖️ Benchmark Thématique: Indice Équipondéré")
    st.markdown("### Simulation: 1000$ investis sur chaque titre le 1er Janvier 2026")
    
    # Sidebar Controls
    with st.sidebar:
        st.header("Configuration")
        
        benchmark_ticker = st.selectbox("Benchmark", ["VOO", "SPY", "QQQ"], index=0)
        
        # Date Selection (Fixed to 2026-01-01 mostly, but adjustable)
        default_start = datetime(2026, 1, 1)
        start_date = st.date_input("Date de début", default_start)
        
        st.info(f"💰 Investissement initial: **${INITIAL_INVESTMENT_PER_TICKER:,.0f}** par titre")
        st.info(f"📅 Date de référence: **{start_date}**")

    # --- DATASOURCE ---
    companies = get_tickers_config()
    tickers = [c['ticker'] for c in companies]
    
    if not tickers:
        st.error("Aucune compagnie trouvée dans la configuration.")
        return

    with st.spinner("Simulation du portefeuille thématique en cours..."):
        data = load_data(tickers, benchmark_ticker, start_date)
        
        if data is None or data.empty:
            st.error("Impossible de récupérer les données.")
            return

    # --- CALCULATION ENGINE ---
    
    # 1. Exchange Rate (USD/CAD)
    if "CAD=X" in data.columns:
        usdcad = data["CAD=X"]
    else:
        usdcad = pd.Series(1.40, index=data.index)
        
    portfolio_series = pd.Series(0, index=data.index, name="Portfolio (CAD)")
    weights = {} # Current Value
    initial_weights = {} # Initial Investment Value (should be ~1000 converted)
    
    simulated_positions = []
    
    # Find start date index (first available date)
    start_idx = data.index[0]
    
    # Pre-calculate Benchmark in CAD for fair comparison
    if benchmark_ticker.endswith(".TO"):
        bench_series_cad = data[benchmark_ticker]
    else:
        bench_series_cad = data[benchmark_ticker] * usdcad
        
    # Normalize Benchmark to Portfolio Start Value
    # Total Initial Portfolio Value = N_Tickers * 1000 (approx, depending on currency base)
    # BUT user said "1000$ au montant du 1er janvier". Usually implies 1000$ CAD or USD?
    # Let's assume 1000$ CAD for simplicity if the user context is Canadian, OR 1000$ in the currency of the stock?
    # To be "Equal Weight" in a mixed portfolio, usually you convert 1000 CAD to USD for USD stocks.
    # Let's assume: Invest 1000 CAD equivalent into EACH stock.
    
    total_invested_cad = 0
    
    for company in companies:
        t = company['ticker']
        if t not in data.columns:
            continue
            
        price_series = data[t]
        start_price = price_series.loc[start_idx]
        
        if pd.isna(start_price):
            continue
            
        is_cad = t.endswith(".TO")
        
        # Logic: We invest 1000 CAD in EACH.
        # If stock is USD, we convert 1000 CAD to USD at start date rate, buy shares.
        
        investment_cad = INITIAL_INVESTMENT_PER_TICKER
        total_invested_cad += investment_cad
        
        if is_cad:
            # Buy directly
            qty = investment_cad / start_price
            val_series = price_series * qty
        else:
            # Convert 1000 CAD to USD at T0
            rate_t0 = usdcad.loc[start_idx]
            investment_usd = investment_cad / rate_t0
            qty = investment_usd / start_price
            
            # Value over time in CAD = Qty * Price(t)_USD * Rate(t)
            val_series = price_series * qty * usdcad
            
        portfolio_series += val_series
        current_val = val_series.iloc[-1]
        
        weights[t] = current_val
        
        perf = (val_series.iloc[-1] / val_series.iloc[0] - 1) * 100
        
        simulated_positions.append({
            "Ticker": t,
            "Sector": company.get('sector', 'N/A'),
            "Pillar": company.get('pillar', 'N/A'),
            "Qty": qty,
            "Start Price": start_price,
            "Current Val (CAD)": current_val,
            "Perf %": perf
        })
        
    # --- METRICS & VISUALIZATION ---
    
    total_curr_val = portfolio_series.iloc[-1]
    total_perf = (total_curr_val / total_invested_cad - 1) * 100
    
    # BENCHMARK METRICS
    bench_start = bench_series_cad.loc[start_idx]
    bench_curr = bench_series_cad.iloc[-1]
    bench_perf = (bench_curr / bench_start - 1) * 100
    
    alpha = total_perf - bench_perf
    
    # HEADER
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Investissement Total", f"${total_invested_cad:,.0f}")
    with c2: st.metric("Valeur Actuelle (CAD)", f"${total_curr_val:,.2f}", f"{total_perf:+.2f}%")
    with c3: st.metric(f"Benchmark ({benchmark_ticker})", f"{bench_perf:+.2f}%")
    with c4: st.metric("Alpha", f"{alpha:+.2f}%", delta="Lead" if alpha > 0 else "Lag")
    
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # CHART: Portfolio vs Benchmark (Normalized to Invested Capital)
        st.subheader("📈 Performance Comparée")
        
        # Normalize Benchmark to match Total Invested
        bench_scaled = (bench_series_cad / bench_start) * total_invested_cad
        
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=portfolio_series.index, y=portfolio_series, name="Indice Thématique (EqW)", line=dict(color="#00C853", width=4)))
        fig_p.add_trace(go.Scatter(x=bench_scaled.index, y=bench_scaled, name=f"{benchmark_ticker} (Base Investie)", line=dict(color="#B0BEC5", width=2, dash="dot")))
        
        # Add baseline (invested capital)
        fig_p.add_hline(y=total_invested_cad, line_dash="dash", line_color="white", opacity=0.3)
        
        fig_p.update_layout(height=450, hovermode="x unified", title="Évolution de la Valeur (CAD)")
        st.plotly_chart(fig_p, use_container_width=True)
        
    with col2:
        # SECTOR / PILLAR BREAKDOWN
        st.subheader("🍰 Performance par Pilier")
        df_pos = pd.DataFrame(simulated_positions)
        
        if not df_pos.empty:
            # Group by Pillar
            pillar_perf = df_pos.groupby("Pillar")[["Current Val (CAD)"]].sum()
            # Initial investment per pillar = Count of tickers in pillar * 1000
            pillar_counts = df_pos.groupby("Pillar")["Ticker"].count()
            pillar_invested = pillar_counts * INITIAL_INVESTMENT_PER_TICKER
            
            pillar_perf["Invested"] = pillar_invested
            pillar_perf["Perf %"] = ((pillar_perf["Current Val (CAD)"] - pillar_perf["Invested"]) / pillar_perf["Invested"]) * 100
            pillar_perf = pillar_perf.sort_values("Perf %", ascending=False)
            
            st.dataframe(
                pillar_perf[["Perf %"]],
                use_container_width=True,
                column_config={
                    "Perf %": st.column_config.ProgressColumn(
                        "Performance", 
                        format="%.1f%%", 
                        min_value=-50, 
                        max_value=50 # Visual range assumption
                    )
                }
            )
            
            # Pie Chart of Current Value by Pillar
            fig_pie = px.pie(pillar_perf, values='Current Val (CAD)', names=pillar_perf.index, hole=0.4, title="Allocation Actuelle")
            st.plotly_chart(fig_pie, use_container_width=True)

    # DETAILED TABLE
    st.subheader("📊 Détail des Positions Simulées")
    st.dataframe(
        df_pos[["Ticker", "Pillar", "Qty", "Start Price", "Current Val (CAD)", "Perf %"]].sort_values("Perf %", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker"),
            "Qty": st.column_config.NumberColumn("Actions (Sim)", format="%.4f"),
            "Start Price": st.column_config.NumberColumn("Prix Départ", format="$%.2f"),
            "Current Val (CAD)": st.column_config.NumberColumn("Valeur (CAD)", format="$%.2f"),
            "Perf %": st.column_config.NumberColumn("Performance", format="%.2f%%"),
        }
    )

if __name__ == "__main__":
    main()
