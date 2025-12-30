# -*- coding: utf-8 -*-
"""
Dashboard AI Stocks Sentiment Analysis
Analyse comparative de sentiment pour actions AI
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from pathlib import Path

# Configuration
st.set_page_config(
    page_title="AI Stocks Sentiment",
    page_icon="\U0001F4C8",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Environment Detection
if Path('/data/files').exists():
    DATA_ROOT = Path('/data/files')
else:
    # Local Windows: prod/dashboard -> prod -> root -> local_files
    DATA_ROOT = Path(__file__).parent.parent.parent / 'local_files'

@st.cache_data
def load_summary_data():
    """Charge le fichier d'agregation"""
    data_path = DATA_ROOT / 'companies_sentiment_summary.json'
    
    if not data_path.exists():
        return None
    
    with open(data_path, 'r') as f:
        return json.load(f)

@st.cache_data
def load_company_details(ticker):
    """Charge les details d'une compagnie"""
    data_path = DATA_ROOT / 'companies' / f'{ticker}_news.json'
    
    if not data_path.exists():
        return None
    
    with open(data_path, 'r') as f:
        return json.load(f)

# ================== MAIN ==================

st.title("\U0001F4C8 AI Stocks Sentiment Dashboard")
st.markdown("### Analyse de sentiment des actions AI via nouvelles financieres")

try:
    summary = load_summary_data()
    
    if not summary or not summary.get('companies'):
        st.error("Aucune donnee disponible. Executez d'abord les scripts de collection et d'analyse.")
        st.stop()
    
    companies = summary['companies']
    global_stats = summary['global_stats']
    
    # ================== SIDEBAR ==================
    st.sidebar.header("\U0001F50D Filtres")
    
    # Filtre par secteur
    sectors = list(set(c['sector'] for c in companies))
    selected_sector = st.sidebar.selectbox("Secteur", ["Tous"] + sorted(sectors))
    
    # Filtre par tendance
    trends = ["Toutes", "improving", "stable", "declining"]
    selected_trend = st.sidebar.selectbox("Tendance", trends)
    
    # Appliquer filtres
    filtered_companies = companies
    
    if selected_sector != "Tous":
        filtered_companies = [c for c in filtered_companies if c['sector'] == selected_sector]
    
    if selected_trend != "Toutes":
        filtered_companies = [c for c in filtered_companies if c['trend_label'] == selected_trend]
    
    df = pd.DataFrame(filtered_companies)
    
    # ================== METRIQUES PRINCIPALES ==================
    
    with st.expander("\U0001F4D6 Guide: Comprendre le Sentiment Financier"):
        st.markdown("""
        **Sentiment Index** (-1 a +1)
        - Mesure si les nouvelles sont POSITIVES ou NEGATIVES pour l'action
        - **Positif** (> 0.15): Nouvelles favorables (earnings beat, partnerships, innovation)
        - **Neutre** (-0.15 a 0.15): Nouvelles equilibrees
        - **Negatif** (< -0.15): Nouvelles defavorables (earnings miss, layoffs, legal issues)
        
        **Tendance 7j vs 30j**
        - \U00002B06 Improving: Sentiment recent meilleur que tendance long terme
        - \U000027A1 Stable: Sentiment constant
        - \U00002B07 Declining: Sentiment recent moins bon
        
        **Volatilite**
        - Variation du sentiment sur 7 jours
        - Haute volatilite = nouvelles contradictoires ou marche instable
        """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Compagnies Analysees",
            global_stats['total_companies'],
            delta=f"{len(filtered_companies)} filtrees"
        )
    
    with col2:
        st.metric(
            "Articles Analyses",
            global_stats['total_analyzed']
        )
    
    with col3:
        avg_sentiment = global_stats['avg_sentiment_all']
        emoji = "\U0001F4C8" if avg_sentiment > 0 else "\U0001F4C9"
        st.metric(
            "Sentiment Moyen Global",
            f"{emoji} {avg_sentiment:+.3f}"
        )
    
    with col4:
        improving_pct = global_stats['improving_count'] / global_stats['total_companies'] * 100
        st.metric(
            "Tendance Positive",
            f"{global_stats['improving_count']}/{global_stats['total_companies']}",
            delta=f"{improving_pct:.0f}%"
        )
    
    # ================== HEATMAP SENTIMENT ==================
    st.markdown("---")
    st.subheader("\U0001F525 Heatmap: Sentiment par Compagnie")
    
    # Creer heatmap
    df_sorted = df.sort_values('avg_sentiment', ascending=False)
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=[[row['avg_sentiment']] for _, row in df_sorted.iterrows()],
        y=df_sorted['ticker'],
        x=['Sentiment'],
        colorscale=[
            [0, 'darkred'],
            [0.4, 'red'],
            [0.5, 'yellow'],
            [0.6, 'lightgreen'],
            [1, 'darkgreen']
        ],
        zmid=0,
        text=[[f"{row['avg_sentiment']:+.3f}"] for _, row in df_sorted.iterrows()],
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Sentiment")
    ))
    
    fig_heatmap.update_layout(
        height=max(400, len(df_sorted) * 25),
        margin=dict(l=100, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # ================== TABLE COMPARATIVE ==================
    st.markdown("---")
    st.subheader("\U0001F4CA Tableau Comparatif")
    
    # Preparer donnees pour affichage
    display_df = df[['ticker', 'company_name', 'sector', 'avg_sentiment', 'avg_sentiment_7d', 
                     'trend_label', 'volatility_7d', 'analyzed_articles']].copy()
    
    display_df.columns = ['Ticker', 'Compagnie', 'Secteur', 'Sentiment', 'Sentiment 7j', 
                          'Tendance', 'Volatilite', 'Articles']
    
    # Formater
    display_df['Sentiment'] = display_df['Sentiment'].apply(lambda x: f"{x:+.3f}")
    display_df['Sentiment 7j'] = display_df['Sentiment 7j'].apply(lambda x: f"{x:+.3f}")
    display_df['Volatilite'] = display_df['Volatilite'].apply(lambda x: f"{x:.3f}")
    
    # Afficher
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Tendance": st.column_config.TextColumn(
                "Tendance",
                help="Tendance 7j vs 30j"
            )
        }
    )
    
    # ================== GRAPHIQUES PAR SECTEUR ==================
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**\U0001F4CA Sentiment Moyen par Secteur**")
        sector_avg = df.groupby('sector')['avg_sentiment'].mean().sort_values(ascending=False)
        
        fig_sector = px.bar(
            x=sector_avg.values,
            y=sector_avg.index,
            orientation='h',
            color=sector_avg.values,
            color_continuous_scale=['red', 'yellow', 'green'],
            color_continuous_midpoint=0
        )
        fig_sector.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_sector, use_container_width=True)
    
    with col2:
        st.markdown("**\U0001F4C8 Distribution des Tendances**")
        trend_counts = df['trend_label'].value_counts()
        
        fig_trends = px.pie(
            values=trend_counts.values,
            names=trend_counts.index,
            color=trend_counts.index,
            color_discrete_map={
                'improving': 'green',
                'stable': 'yellow',
                'declining': 'red'
            }
        )
        fig_trends.update_layout(height=400)
        st.plotly_chart(fig_trends, use_container_width=True)
    
    # ================== TOP MOVERS ==================
    st.markdown("---")
    st.subheader("\U0001F4A5 Top Movers (Changements Significatifs)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**\U0001F680 Top 5 Improving (7j vs 30j)**")
        improving = df.nlargest(5, 'trend_delta')[['ticker', 'company_name', 'avg_sentiment_7d', 'trend_delta']]
        for _, row in improving.iterrows():
            st.write(f"\U00002B06 **{row['ticker']}** ({row['company_name'][:25]}) - "
                    f"7j: {row['avg_sentiment_7d']:+.3f} (Δ {row['trend_delta']:+.3f})")
    
    with col2:
        st.markdown("**\U0001F4C9 Top 5 Declining (7j vs 30j)**")
        declining = df.nsmallest(5, 'trend_delta')[['ticker', 'company_name', 'avg_sentiment_7d', 'trend_delta']]
        for _, row in declining.iterrows():
            st.write(f"\U00002B07 **{row['ticker']}** ({row['company_name'][:25]}) - "
                    f"7j: {row['avg_sentiment_7d']:+.3f} (Δ {row['trend_delta']:+.3f})")
    
    # ================== DETAIL COMPAGNIE ==================
    st.markdown("---")
    st.subheader("\U0001F50D Detail par Compagnie")
    
    selected_ticker = st.selectbox(
        "Selectionner une compagnie:",
        options=df['ticker'].tolist(),
        format_func=lambda x: f"{x} - {df[df['ticker']==x].iloc[0]['company_name']}"
    )
    
    if selected_ticker:
        company_data = df[df['ticker'] == selected_ticker].iloc[0]
        details = load_company_details(selected_ticker)
        
        if details:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Sentiment Moyen", f"{company_data['avg_sentiment']:+.3f}")
            
            with col2:
                st.metric("Sentiment 7j", f"{company_data['avg_sentiment_7d']:+.3f}",
                         delta=f"{company_data['trend_delta']:+.3f}")
            
            with col3:
                st.metric("Articles Analyses", company_data['analyzed_articles'])
            
            with col4:
                st.metric("Volatilite", f"{company_data['volatility_7d']:.3f}")
            
            # Distribution
            st.markdown("**Distribution du Sentiment**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("POSITIF", company_data['positive_count'], 
                         f"{company_data['positive_pct']:.1f}%")
            
            with col2:
                st.metric("NEUTRE", company_data['neutral_count'])
            
            with col3:
                st.metric("NEGATIF", company_data['negative_count'],
                         f"{company_data['negative_pct']:.1f}%")
            
            # Top articles
            st.markdown("**Top Articles Positifs**")
            for article in company_data['top_positive_articles']:
                with st.expander(f"\U0001F4C8 [{article['sentiment']:+.3f}] {article['title']}"):
                    st.write(f"**Date:** {article['date']}")
                    st.write(f"**Sentiment:** {article['sentiment']:+.3f}")
                    st.write(f"**URL:** {article['url']}")
            
            st.markdown("**Top Articles Negatifs**")
            for article in company_data['top_negative_articles']:
                with st.expander(f"\U0001F4C9 [{article['sentiment']:+.3f}] {article['title']}"):
                    st.write(f"**Date:** {article['date']}")
                    st.write(f"**Sentiment:** {article['sentiment']:+.3f}")
                    st.write(f"**URL:** {article['url']}")
    
    # ================== FOOTER ==================
    st.sidebar.markdown("---")
    st.sidebar.info(f"""
    **\U0001F4CA Statistiques**
    - Compagnies: {global_stats['total_companies']}
    - Articles: {global_stats['total_analyzed']}
    - Derniere MAJ: {summary.get('generated_at', 'N/A')[:16]}
    """)

except FileNotFoundError as e:
    st.error(f"Fichier introuvable: {e}")
    st.info("Executez: aggregate_companies.py")
except Exception as e:
    st.error(f"Erreur: {e}")
    st.exception(e)
