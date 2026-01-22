import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta, timezone
import numpy as np
from collections import Counter
import re

# --- CONFIGURATION DU THÈME ---
st.set_page_config(
    page_title="🎯 Smart News Analytics",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour déterminer le répertoire local
def get_local_files_dir():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    
    local_files = os.path.join(project_root, 'local_files')
    if os.path.exists(local_files):
        return local_files
    
    if os.path.exists('/data/files'):
        return '/data/files'
        
    return './local_files'

LOCAL_FILES_DIR = get_local_files_dir()
NEWS_DIR = os.path.join(LOCAL_FILES_DIR, 'companies')

# --- FONCTIONS DE CHARGEMENT ---
@st.cache_data(ttl=300)
def get_available_tickers():
    """Liste les tickers ayant un fichier _news.json"""
    if not os.path.exists(NEWS_DIR):
        return []
        
    files = [f for f in os.listdir(NEWS_DIR) if f.endswith('_news.json')]
    tickers = sorted([f.replace('_news.json', '') for f in files])
    return tickers

@st.cache_data(ttl=60)
def load_news_data(ticker):
    """Charge les données brutes des nouvelles"""
    file_path = os.path.join(NEWS_DIR, f"{ticker}_news.json")
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        articles = data.get('articles', []) if isinstance(data, dict) else data
        
        if not articles:
            return pd.DataFrame()
            
        df = pd.DataFrame(articles)
        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce', utc=True)
        
        def extract_sentiment(row):
            sent = row.get('sentiment')
            if isinstance(sent, dict):
                comp = sent.get('compound', 0)
                relevance = sent.get('relevance', 0)
                return comp, relevance
            return None, None

        if 'sentiment' in df.columns:
            df[['sentiment_score', 'relevance']] = df.apply(
                lambda x: pd.Series(extract_sentiment(x)), axis=1
            )
        else:
            df['sentiment_score'] = None
            df['relevance'] = None
        
        # Enrichissement temporel
        df['hour'] = df['published_at'].dt.hour
        df['day_of_week'] = df['published_at'].dt.day_name()
        df['date'] = df['published_at'].dt.date
            
        return df.sort_values('published_at', ascending=False)
        
    except Exception as e:
        st.error(f"Erreur lors du chargement: {e}")
        return pd.DataFrame()

# --- FONCTIONS D'ANALYSE ---
def extract_words_from_texts(texts, min_length=4, max_words=100):
    """Extrait les mots les plus fréquents des textes"""
    # Mots à exclure (stopwords basiques)
    stopwords = set([
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
        'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 'just', 'about', 'into',
        'through', 'during', 'before', 'after', 'above', 'below', 'between',
        'under', 'again', 'further', 'then', 'once', 'here', 'there', 'all',
        'its', 'your', 'their', 'our', 'my', 'his', 'her'
    ])
    
    all_words = []
    for text in texts:
        if pd.notna(text):
            # Nettoyer et extraire les mots
            words = re.findall(r'\b[a-zA-Z]+\b', str(text).lower())
            words = [w for w in words if len(w) >= min_length and w not in stopwords]
            all_words.extend(words)
    
    # Compter les fréquences
    word_freq = Counter(all_words)
    return dict(word_freq.most_common(max_words))

def detect_entities_simple(texts, ticker):
    """Détection simple d'entités nommées basique"""
    # Pattern pour noms propres (capitalisés)
    entities = []
    
    # Mots-clés communs à exclure
    exclude = {'The', 'And', 'But', 'For', 'With', 'This', 'That', 'CEO', 'CFO', 'Inc'}
    
    for text in texts:
        if pd.notna(text):
            # Trouver les mots capitalisés
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', str(text))
            entities.extend([w for w in words if w not in exclude and w != ticker])
    
    entity_freq = Counter(entities)
    return dict(entity_freq.most_common(20))

def calculate_momentum(df_analyzed, recent_days=7):
    """Calcule le momentum du sentiment"""
    if len(df_analyzed) < 2:
        return 0, "neutral"
    
    recent_cutoff = pd.Timestamp.now(tz=timezone.utc) - pd.Timedelta(days=recent_days)
    recent = df_analyzed[df_analyzed['published_at'] > recent_cutoff]['sentiment_score'].mean()
    historical = df_analyzed[df_analyzed['published_at'] <= recent_cutoff]['sentiment_score'].mean()
    
    if pd.isna(recent) or pd.isna(historical):
        return 0, "neutral"
    
    momentum = recent - historical
    
    if momentum > 0.1:
        direction = "📈 Hausse"
    elif momentum < -0.1:
        direction = "📉 Baisse"
    else:
        direction = "➡️ Stable"
    
    return momentum, direction

# --- INTERFACE ---
query_params = st.query_params
default_index = 0
available_tickers = get_available_tickers()

if "ticker" in query_params:
    target = query_params["ticker"]
    if target in available_tickers:
        default_index = available_tickers.index(target)

# Sidebar
with st.sidebar:
    st.title("🎯 Smart News Analytics")
    
    selected_ticker = st.selectbox(
        "Sélectionner un Ticker",
        available_tickers,
        index=default_index
    )
    
    st.markdown("---")
    
    # Options de visualisation
    st.subheader("🎨 Options")
    show_wordcloud = st.checkbox("WordCloud", value=True)
    show_heatmap = st.checkbox("Heatmap Temporelle", value=True)
    show_treemap = st.checkbox("Treemap Sources", value=True)
    show_entities = st.checkbox("Entités Détectées", value=True)
    
    st.markdown("---")
    st.markdown("""
    **Guide des Couleurs :**
    * 🟢 **Positif (> 0.2)**
    * 🔴 **Négatif (< -0.2)**
    * ⚪ **Neutre**
    """)

# Main Content
if selected_ticker:
    st.title(f"🎯 Smart News Analytics : {selected_ticker}")
    
    df = load_news_data(selected_ticker)
    
    if df.empty:
        st.warning("Aucune donnée disponible pour ce ticker.")
        st.stop()
        
    df_analyzed = df.dropna(subset=['sentiment_score'])
    
    # --- KPIs AMÉLIORÉS ---
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Total Articles", len(df))
    
    with col2:
        coverage = len(df_analyzed) / len(df) if len(df) > 0 else 0
        st.metric("🎯 Couverture", f"{coverage:.1%}")
    
    with col3:
        if not df_analyzed.empty:
            avg_sent = df_analyzed['sentiment_score'].mean()
            st.metric("💭 Sentiment Moyen", f"{avg_sent:+.3f}")
        else:
            st.metric("💭 Sentiment", "N/A")
    
    with col4:
        recent_cutoff = pd.Timestamp.now(tz=timezone.utc) - pd.Timedelta(hours=24)
        recent_count = len(df[df['published_at'] > recent_cutoff])
        st.metric("🕐 Volume 24h", recent_count)
    
    with col5:
        if not df_analyzed.empty:
            momentum, direction = calculate_momentum(df_analyzed)
            st.metric("📈 Momentum 7j", direction, f"{momentum:+.3f}")
        else:
            st.metric("📈 Momentum", "N/A")

    st.markdown("---")

    # --- GRAPHIQUES PRINCIPAUX ---
    if not df_analyzed.empty:
        
        # 1. Timeline avec Momentum
        st.subheader("📈 Sentiment & Volume Timeline")
        
        daily_stats = df_analyzed.groupby('date').agg({
            'sentiment_score': 'mean',
            'title': 'count'
        }).reset_index()
        daily_stats.rename(columns={'title': 'volume'}, inplace=True)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Volume (barres)
        fig.add_trace(
            go.Bar(
                x=daily_stats['date'],
                y=daily_stats['volume'],
                name='Volume',
                marker=dict(
                    color=daily_stats['sentiment_score'],
                    colorscale='RdYlGn',
                    cmin=-0.5,
                    cmax=0.5,
                    opacity=0.5
                ),
                hovertemplate='<b>%{x}</b><br>Volume: %{y}<extra></extra>'
            ),
            secondary_y=True
        )
        
        # Sentiment (ligne)
        fig.add_trace(
            go.Scatter(
                x=daily_stats['date'],
                y=daily_stats['sentiment_score'],
                name='Sentiment',
                mode='lines+markers',
                line=dict(width=3, color='#00D9FF'),
                marker=dict(
                    size=10,
                    color=daily_stats['sentiment_score'],
                    colorscale='RdYlGn',
                    cmin=-0.5,
                    cmax=0.5,
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>%{x}</b><br>Sentiment: %{y:.3f}<extra></extra>'
            ),
            secondary_y=False
        )
        
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Sentiment Score", secondary_y=False, range=[-1, 1])
        fig.update_yaxes(title_text="Volume Articles", secondary_y=True)
        fig.update_layout(
            template="plotly_dark",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- GRAPHIQUES EN COLONNES ---
        col_left, col_right = st.columns(2)
        
        with col_left:
            # 2. Violin Plot (distribution avancée)
            st.subheader("🎻 Distribution du Sentiment")
            
            fig_violin = go.Figure()
            fig_violin.add_trace(go.Violin(
                y=df_analyzed['sentiment_score'],
                box_visible=True,
                meanline_visible=True,
                fillcolor='#3d9dfc',
                opacity=0.6,
                line_color='white',
                name='Sentiment'
            ))
            
            fig_violin.update_layout(
                template="plotly_dark",
                yaxis_title="Sentiment Score",
                showlegend=False,
                height=350
            )
            
            st.plotly_chart(fig_violin, use_container_width=True)
        
        with col_right:
            # 3. Source Performance (Treemap)
            if show_treemap and 'source' in df_analyzed.columns:
                st.subheader("🌳 Sources par Sentiment")
                
                source_sentiment = df_analyzed.groupby('source').agg({
                    'sentiment_score': 'mean',
                    'title': 'count'
                }).reset_index()
                source_sentiment.columns = ['source', 'avg_sentiment', 'count']
                source_sentiment = source_sentiment[source_sentiment['count'] >= 2]  # Min 2 articles
                
                fig_tree = px.treemap(
                    source_sentiment,
                    path=['source'],
                    values='count',
                    color='avg_sentiment',
                    color_continuous_scale='RdYlGn',
                    color_continuous_midpoint=0,
                    range_color=[-0.5, 0.5],
                    hover_data={'count': True, 'avg_sentiment': ':.3f'}
                )
                
                fig_tree.update_layout(
                    template="plotly_dark",
                    height=350
                )
                
                st.plotly_chart(fig_tree, use_container_width=True)
        
        # --- HEATMAP TEMPORELLE ---
        if show_heatmap and 'hour' in df_analyzed.columns and 'day_of_week' in df_analyzed.columns:
            st.subheader("🔥 Heatmap Temporelle : Sentiment par Jour/Heure")
            
            # Créer une matrice jour/heure
            heatmap_data = df_analyzed.groupby(['day_of_week', 'hour'])['sentiment_score'].mean().reset_index()
            heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='sentiment_score')
            
            # Ordonner les jours
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_pivot = heatmap_pivot.reindex([d for d in day_order if d in heatmap_pivot.index])
            
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=heatmap_pivot.values,
                x=heatmap_pivot.columns,
                y=heatmap_pivot.index,
                colorscale='RdYlGn',
                zmid=0,
                zmin=-0.5,
                zmax=0.5,
                hovertemplate='<b>%{y}</b> à %{x}h<br>Sentiment: %{z:.3f}<extra></extra>'
            ))
            
            fig_heatmap.update_layout(
                template="plotly_dark",
                xaxis_title="Heure de Publication",
                yaxis_title="Jour de la Semaine",
                height=300
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # --- WORDCLOUDS PAR SENTIMENT ---
        if show_wordcloud:
            st.subheader("☁️ WordClouds par Sentiment")
            
            col_wc1, col_wc2, col_wc3 = st.columns(3)
            
            # Séparer par sentiment
            df_positive = df_analyzed[df_analyzed['sentiment_score'] > 0.2]
            df_negative = df_analyzed[df_analyzed['sentiment_score'] < -0.2]
            df_neutral = df_analyzed[(df_analyzed['sentiment_score'] >= -0.2) & (df_analyzed['sentiment_score'] <= 0.2)]
            
            with col_wc1:
                st.markdown("**🟢 Positif**")
                if len(df_positive) > 0:
                    pos_words = extract_words_from_texts(df_positive['title'].tolist() + df_positive['description'].fillna('').tolist())
                    if pos_words:
                        # Afficher top 10 mots
                        top_pos = list(pos_words.items())[:10]
                        for word, freq in top_pos:
                            st.text(f"• {word} ({freq})")
                else:
                    st.info("Pas assez d'articles positifs")
            
            with col_wc2:
                st.markdown("**⚪ Neutre**")
                if len(df_neutral) > 0:
                    neu_words = extract_words_from_texts(df_neutral['title'].tolist())
                    if neu_words:
                        top_neu = list(neu_words.items())[:10]
                        for word, freq in top_neu:
                            st.text(f"• {word} ({freq})")
                else:
                    st.info("Pas assez d'articles neutres")
            
            with col_wc3:
                st.markdown("**🔴 Négatif**")
                if len(df_negative) > 0:
                    neg_words = extract_words_from_texts(df_negative['title'].tolist() + df_negative['description'].fillna('').tolist())
                    if neg_words:
                        top_neg = list(neg_words.items())[:10]
                        for word, freq in top_neg:
                            st.text(f"• {word} ({freq})")
                else:
                    st.info("Pas assez d'articles négatifs")
        
        # --- ENTITÉS DÉTECTÉES ---
        if show_entities:
            st.subheader("👥 Entités Fréquemment Mentionnées")
            
            entities = detect_entities_simple(
                df_analyzed['title'].tolist() + df_analyzed['description'].fillna('').tolist(),
                selected_ticker
            )
            
            if entities:
                # Créer un bar chart horizontal
                entity_df = pd.DataFrame(list(entities.items())[:15], columns=['Entity', 'Mentions'])
                
                fig_entities = px.bar(
                    entity_df,
                    x='Mentions',
                    y='Entity',
                    orientation='h',
                    color='Mentions',
                    color_continuous_scale='Viridis'
                )
                
                fig_entities.update_layout(
                    template="plotly_dark",
                    yaxis={'categoryorder': 'total ascending'},
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig_entities, use_container_width=True)
            else:
                st.info("Aucune entité significative détectée")

    else:
        st.info("Pas assez de données analysées pour générer les visualisations avancées.")

    # --- TABLEAU DES ARTICLES ---
    st.markdown("---")
    st.subheader("📰 Derniers Articles")
    
    # Custom CSS
    st.markdown("""
    <style>
    .news-row {
        display: flex;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-family: 'Source Sans Pro', sans-serif;
    }
    .news-icon {
        margin-right: 12px;
        font-size: 16px;
        min-width: 25px;
    }
    .news-content {
        flex: 1;
        font-size: 14px;
    }
    .news-link {
        color: #FAFAFA !important;
        text-decoration: none;
        font-weight: 500;
    }
    .news-link:hover {
        text-decoration: underline;
        color: #00D9FF !important;
    }
    .news-meta {
        color: #888;
        font-size: 12px;
        margin-top: 4px;
    }
    .news-score {
        font-family: monospace;
        font-weight: bold;
        font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Filtres
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        sentiment_filter = st.selectbox(
            "Filtrer par Sentiment",
            ["Tous", "Positif", "Négatif", "Neutre"]
        )
    with col_filter2:
        num_articles = st.slider("Nombre d'articles", 10, 100, 30)
    
    # Appliquer les filtres
    display_df = df.copy()
    
    if sentiment_filter == "Positif":
        display_df = display_df[display_df['sentiment_score'] > 0.2]
    elif sentiment_filter == "Négatif":
        display_df = display_df[display_df['sentiment_score'] < -0.2]
    elif sentiment_filter == "Neutre":
        display_df = display_df[(display_df['sentiment_score'] >= -0.2) & (display_df['sentiment_score'] <= 0.2)]
    
    display_df = display_df.head(num_articles)
    
    html_content = ""
    for idx, row in display_df.iterrows():
        score = row.get('sentiment_score')
        
        color = "#888"
        icon = "⚪"
        if pd.notna(score):
            if score > 0.2: 
                icon = "🟢"
                color = "#00C853"
            elif score < -0.2: 
                icon = "🔴"
                color = "#FF1744"

        score_text = f"{score:+.2f}" if pd.notna(score) else "N/A"
        date_str = row['published_at'].strftime('%d/%m %H:%M') if pd.notna(row['published_at']) else "N/A"
        
        html_content += f"""
        <div class="news-row">
            <span class="news-icon">{icon}</span>
            <div class="news-content">
                <span class="news-score" style="color:{color};">[{score_text}]</span>
                <a href="{row['url']}" target="_blank" class="news-link">{row['title']}</a>
                <div class="news-meta">{row['source']} • {date_str}</div>
            </div>
        </div>
        """
    
    st.markdown(html_content, unsafe_allow_html=True)

else:
    st.info("Sélectionnez un ticker dans la sidebar pour commencer")
