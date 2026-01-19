import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime, timedelta
import altair as alt

# --- CONFIGURATION DU THÈME ---
st.set_page_config(
    page_title="Deep Dive News",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour déterminer le répertoire local
def get_local_files_dir():
    # En production (n8n-local-stack), c'est souvent c:\n8n-local-stack\local_files
    # On remonte de prod/dashboards/generators -> prod/dashboards -> prod -> root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    
    local_files = os.path.join(project_root, 'local_files')
    if os.path.exists(local_files):
        return local_files
    
    # Fallback pour Docker
    if os.path.exists('/data/files'):
        return '/data/files'
        
    return './local_files' # Fallback relatif

LOCAL_FILES_DIR = get_local_files_dir()
NEWS_DIR = os.path.join(LOCAL_FILES_DIR, 'companies')

# --- FONCTIONS DE CHARGEMENT ---
@st.cache_data(ttl=300) # Cache 5 mins
def get_available_tickers():
    """Liste les tickers ayant un fichier _news.json"""
    if not os.path.exists(NEWS_DIR):
        return []
        
    files = [f for f in os.listdir(NEWS_DIR) if f.endswith('_news.json')]
    tickers = sorted([f.replace('_news.json', '') for f in files])
    return tickers

@st.cache_data(ttl=60) # Cache 1 min
def load_news_data(ticker):
    """Charge les donnÃ©es brutes des nouvelles"""
    file_path = os.path.join(NEWS_DIR, f"{ticker}_news.json")
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Support des deux formats (old list vs new dict)
        articles = data.get('articles', []) if isinstance(data, dict) else data
        
        if not articles:
            return pd.DataFrame()
            
        df = pd.DataFrame(articles)
        
        # Conversion des dates en UTC
        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce', utc=True)
        
        # Extraction du sentiment
        def extract_sentiment(row):
            sent = row.get('sentiment')
            if isinstance(sent, dict):
                comp = sent.get('compound', 0)
                relevance = sent.get('relevance', 0)
                return comp, relevance
            return None, None

        # Appliquer l'extraction seulement si la colonne sentiment existe
        if 'sentiment' in df.columns:
            df[['sentiment_score', 'relevance']] = df.apply(
                lambda x: pd.Series(extract_sentiment(x)), axis=1
            )
        else:
            df['sentiment_score'] = None
            df['relevance'] = None
            
        return df.sort_values('published_at', ascending=False)
        
    except Exception as e:
        st.error(f"Erreur lors du chargement: {e}")
        return pd.DataFrame()

# --- INTERFACE ---

# 1. Gestion Ticker via URL
query_params = st.query_params
default_index = 0
available_tickers = get_available_tickers()

if "ticker" in query_params:
    target = query_params["ticker"]
    if target in available_tickers:
        default_index = available_tickers.index(target)

# Sidebar
with st.sidebar:
    st.title("📰 News Deep Dive")
    selected_ticker = st.selectbox(
        "Sélectionner un Ticker",
        available_tickers,
        index=default_index
    )
    
    st.markdown("---")
    st.markdown("""
    **Guide des Couleurs :**
    * 🟢 **Positif (> 0.2)**
    * 🔴 **Négatif (< -0.2)**
    * ⚪ **Neutre**
    """)

# Main Content
if selected_ticker:
    st.title(f"Analyse Temporelle des Nouvelles : {selected_ticker}")
    
    df = load_news_data(selected_ticker)
    
    if df.empty:
        st.warning("Aucune donnée disponible pour ce ticker.")
        st.stop()
        
    # Filtrer les articles analysés (avec sentiment)
    df_analyzed = df.dropna(subset=['sentiment_score'])
    
    # --- KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Articles Collectés", len(df))
    with col2:
        coverage = len(df_analyzed) / len(df) if len(df) > 0 else 0
        st.metric("Couverture Analyse", f"{coverage:.1%}", help="Articles analysés par FinBERT")
        
    with col3:
        if not df_analyzed.empty:
            avg_sent = df_analyzed['sentiment_score'].mean()
            st.metric("Sentiment Moyen (Global)", f"{avg_sent:+.3f}", 
                      delta="Bullish" if avg_sent > 0 else "Bearish")
        else:
            st.metric("Sentiment Moyen", "N/A")
            
    with col4:
        # Articles récents (24h)
        from datetime import timezone
        recent_cutoff = pd.Timestamp.now(tz=timezone.utc) - pd.Timedelta(hours=24)
        recent_count = len(df[df['published_at'] > recent_cutoff])
        st.metric("Volume 24h", recent_count)

    st.markdown("---")

    # --- GRAPHIQUES ---
    
    if not df_analyzed.empty:
        # Agrégation par jour
        # On regroupe par date (sans heure)
        df_analyzed['date'] = df_analyzed['published_at'].dt.date
        daily_stats = df_analyzed.groupby('date').agg({
            'sentiment_score': 'mean',
            'title': 'count'  # Volume
        }).reset_index()
        daily_stats.rename(columns={'title': 'volume'}, inplace=True)
        
        # Graphique Combiné Ligne + Barres
        fig = go.Figure()
        
        # Barres pour le volume (Axe Y secondaire optionnel, ou juste en bas)
        # "Smart Volume" : Couleur selon le sentiment
        fig.add_trace(go.Bar(
            x=daily_stats['date'],
            y=daily_stats['volume'],
            name='Volume Articles',
            marker=dict(
                color=daily_stats['sentiment_score'],
                colorscale='RdYlGn',
                cmin=-0.5, # Bornes pour que le vert/rouge soit bien visible
                cmax=0.5,
                opacity=0.4, # Transparence pour voir la ligne derrière
                showscale=False
            ),
            yaxis='y2'
        ))
        
        # Ligne pour le sentiment
        fig.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['sentiment_score'],
            name='Sentiment Moyen',
            mode='lines+markers',
            line=dict(width=3, color='#FFFFFF'), # Ligne blanche neutre
            marker=dict(
                size=12,
                color=daily_stats['sentiment_score'], # Points colorés
                colorscale='RdYlGn',
                cmin=-0.5,
                cmax=0.5,
                line=dict(width=2, color='#1E1E1E') # Contour sombre
            )
        ))
        
        fig.update_layout(
            title='Sentiment & Volume Quotidien (Smart Color)',
            template="plotly_dark",
            yaxis=dict(
                title='Sentiment Score (-1 à +1)',
                range=[-1, 1],
                zeroline=True,
                zerolinecolor='rgba(255,255,255,0.2)'
            ),
            yaxis2=dict(
                title='Volume Articles',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- HEATMAP / DISTRIBUTION ---
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Distribution du Sentiment")
            fig_hist = px.histogram(
                df_analyzed, 
                x="sentiment_score", 
                nbins=20,
                color_discrete_sequence=['#3d9dfc'],
                title="Répartition des scores FinBERT"
            )
            fig_hist.update_layout(template="plotly_dark", bargap=0.1)
            st.plotly_chart(fig_hist, use_container_width=True)
            
        with col_g2:
            st.subheader("Sources les plus actives")
            source_counts = df['source'].value_counts().head(10).reset_index()
            source_counts.columns = ['Source', 'Articles']
            fig_bar = px.bar(
                source_counts, 
                x='Articles', 
                y='Source', 
                orientation='h',
                color='Articles',
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(template="plotly_dark", yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.info("Pas assez de données analysées pour générer les graphiques historiques.")

    # --- TABLEAU DES ARTICLES ---
    st.subheader("Derniers Articles")
    
    # Custom CSS for compact list
    st.markdown("""
    <style>
    .news-row {
        display: flex;
        align_items: center;
        padding: 4px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-family: 'Source Sans Pro', sans-serif;
    }
    .news-icon {
        margin-right: 10px;
        font-size: 14px;
        min-width: 20px;
    }
    .news-content {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 14px;
        line-height: 1.5;
    }
    .news-link {
        color: #FAFAFA !important;
        text-decoration: none;
        font-weight: 500;
    }
    .news-link:hover {
        text-decoration: underline;
        color: #64B5F6 !important;
    }
    .news-meta {
        color: #666;
        font-size: 12px;
        margin-left: 8px;
    }
    .news-score {
        font-family: monospace;
        font-weight: bold;
        margin-right: 6px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Affichage tabloïde
    display_df = df.head(50).copy()
    
    html_content = ""
    for idx, row in display_df.iterrows():
        # Carte article compacte
        score = row.get('sentiment_score')
        
        # Determine Color & Icon
        color = "#888" # Grey default
        icon = "⚪"
        if pd.notna(score):
            if score > 0.2: 
                icon = "🟢"
                color = "#00C853" # Green
            elif score < -0.2: 
                icon = "🔴"
                color = "#FF1744" # Red

        score_text = f"{score:+.2f}" if pd.notna(score) else "N/A"
        date_str = row['published_at'].strftime('%d/%m %H:%M')
        
        html_content += f"""
        <div class="news-row">
            <span class="news-icon">{icon}</span>
            <div class="news-content">
                <span class="news-score" style="color:{color};">[{score_text}]</span>
                <a href="{row['url']}" target="_blank" class="news-link">{row['title']}</a>
                <span class="news-meta">({row['source']} - {date_str})</span>
            </div>
        </div>
        """
    
    st.markdown(html_content, unsafe_allow_html=True)
