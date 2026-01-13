#!/usr/bin/env python3
"""
Dashboard Streamlit pour visualiser l'analyse de sentiment multi-dimensionnelle
Design basé sur le composant React avec gradient sombre et visualisations modernes
"""
import streamlit as st
import json
import os
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Sentiment Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé pour reproduire le design React
st.markdown("""
<style>
    /* Background gradient global */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    }
    
    /* Carte avec effet glassmorphism */
    .glass-card {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid #475569;
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Titres et textes */
    h1, h2, h3 {
        color: white !important;
    }
    
    .stMetric label {
        color: #94a3b8 !important;
        font-size: 0.875rem !important;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        color: white !important;
    }
    
    /* Progress bars personnalisées */
    .stProgress > div > div > div {
        background: linear-gradient(to right, #eab308, #f97316) !important;
    }
    
    /* Selectbox */
    .stSelectbox label {
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* Boutons */
    .stButton button {
        background: rgba(59, 130, 246, 0.2);
        color: white;
        border: 1px solid #3b82f6;
        border-radius: 0.5rem;
    }
    
    .stButton button:hover {
        background: rgba(59, 130, 246, 0.4);
        border-color: #60a5fa;
    }
</style>
""", unsafe_allow_html=True)

def get_sentiment_data_dir():
    """Détecte automatiquement le chemin des données (Docker ou local)"""
    docker_path = '/data/sentiment_analysis'
    local_path = './data/sentiment_analysis'
    
    if os.path.exists(docker_path):
        return docker_path
    elif os.path.exists(local_path):
        return local_path
    else:
        return None

def get_available_tickers():
    """Récupère la liste des tickers disponibles depuis les fichiers JSON"""
    data_dir = get_sentiment_data_dir()
    if not data_dir:
        return []
    
    try:
        files = [f for f in os.listdir(data_dir) if f.endswith('_latest.json')]
        tickers = sorted([f.replace('_latest.json', '') for f in files if f != 'consolidated_sentiment_report.json'])
        return tickers
    except Exception as e:
        st.error(f"Erreur lors de la lecture des tickers: {e}")
        return []

def load_sentiment_data(ticker: str):
    """Charge les données de sentiment pour un ticker"""
    data_dir = get_sentiment_data_dir()
    if not data_dir:
        return None
    
    filepath = os.path.join(data_dir, f"{ticker}_latest.json")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erreur lors du chargement des données pour {ticker}: {e}")
        return None

def get_sentiment_color(score: float) -> str:
    """Retourne la couleur hex appropriée pour un score de sentiment"""
    if score > 0.5:
        return "#10b981"  # green-600
    elif score > 0.2:
        return "#4ade80"  # green-400
    elif score < -0.5:
        return "#ef4444"  # red-600
    elif score < -0.2:
        return "#f87171"  # red-400
    else:
        return "#eab308"  # yellow-500

def render_sentiment_gauge(score: float):
    """Rendu de la jauge de sentiment avec gradient (HTML pur)"""
    position = ((score + 1) / 2) * 100
    
    st.markdown(f"""
    <div style='margin: 2rem 0;'>
        <!-- Labels -->
        <div style='display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.75rem;'>
            <span style='flex: 1; text-align: left;'>Bearish Fort</span>
            <span style='flex: 1; text-align: center;'>Neutre</span>
            <span style='flex: 1; text-align: right;'>Bullish Fort</span>
        </div>
        
        <!-- Gradient bar -->
        <div style='position: relative; height: 3rem; border-radius: 0.75rem; overflow: hidden; 
                    background: linear-gradient(to right, #ef4444 0%, #f87171 25%, #eab308 50%, #4ade80 75%, #10b981 100%);'>
            
            <!-- Marqueurs -->
            <div style='position: absolute; inset: 0; display: flex; justify-content: space-between; padding: 0 0.25rem;'>
                <div style='width: 1px; background: rgba(255,255,255,0.3); height: 100%;'></div>
                <div style='width: 1px; background: rgba(255,255,255,0.5); height: 100%;'></div>
                <div style='width: 1px; background: rgba(255,255,255,0.3); height: 100%;'></div>
            </div>
            
            <!-- Indicateur -->
            <div style='position: absolute; top: 0; bottom: 0; width: 4px; background: white; 
                        box-shadow: 0 0 10px rgba(0,0,0,0.5); transition: left 0.7s ease; left: {position}%;'>
                <div style='position: absolute; top: -2rem; left: 50%; transform: translateX(-50%); 
                            background: white; color: #0f172a; padding: 0.25rem 0.75rem; 
                            border-radius: 0.5rem; font-size: 0.875rem; font-weight: bold; 
                            white-space: nowrap; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
                    {'+' if score > 0 else ''}{score:.4f}
                </div>
            </div>
        </div>
        
        <!-- Scale -->
        <div style='display: flex; justify-content: space-between; font-size: 0.75rem; color: #64748b; margin-top: 0.5rem;'>
            <span>-1.00</span>
            <span>-0.50</span>
            <span>0.00</span>
            <span>+0.50</span>
            <span>+1.00</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_component_bar(emoji: str, label: str, score: float, confidence: float = None, weight: float = None):
    """Rendu d'une barre de composante avec progress bar"""
    color = get_sentiment_color(score)
    
    # Calcul de la largeur et position de la barre
    bar_width = abs(score) * 100
    margin_left = (100 - bar_width) if score < 0 else 0
    
    st.markdown(f"""
    <div style='margin-bottom: 1.5rem;'>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;'>
            <span style='color: white; font-weight: 500;'>{emoji} {label}</span>
            <span style='font-weight: bold; color: {color}; font-size: 1.1rem;'>
                {'+' if score > 0 else ''}{score:.4f}
            </span>
        </div>
        <div style='width: 100%; background: #334155; border-radius: 9999px; height: 0.75rem; overflow: hidden;'>
            <div style='background: {color}; height: 0.75rem; transition: width 0.5s ease; 
                        width: {bar_width}%; margin-left: {margin_left}%;'></div>
        </div>
    """, unsafe_allow_html=True)
    
    if confidence is not None and weight is not None:
        st.markdown(f"""
        <div style='display: flex; justify-content: space-between; font-size: 0.75rem; color: #94a3b8; margin-top: 0.5rem;'>
            <span>Confiance: {confidence * 100:.1f}%</span>
            <span>Poids: {weight * 100:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    # Sélection du ticker en haut
    available_tickers = get_available_tickers()
    
    if not available_tickers:
        st.error("❌ Aucun ticker disponible. Vérifiez que les analyses ont été générées.")
        st.info("💡 Exécutez: `python3 /data/scripts/analyze_all_sentiment.py`")
        return
    
    col1, col2 = st.columns([4, 1])
    with col1:
        selected_ticker = st.selectbox(
            "🎯 Sélectionner un ticker",
            options=available_tickers,
            index=0
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Rafraîchir"):
            st.rerun()
    
    # Charger les données
    data = load_sentiment_data(selected_ticker)
    
    if not data:
        st.error(f"❌ Impossible de charger les données pour {selected_ticker}")
        return
    
    # === HEADER ===
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div class='glass-card'>
            <h1 style='margin-bottom: 0.5rem;'>
                {data['ticker']}
                <span style='font-size: 1.5rem; color: #94a3b8; margin-left: 1rem;'>Analyse Multi-Dimensionnelle</span>
            </h1>
            <p style='color: #94a3b8; margin: 0;'>
                {datetime.fromisoformat(data['timestamp'].replace('Z', '')).strftime('%d %B %Y à %H:%M:%S')}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        score_color = get_sentiment_color(data['final_sentiment_score'])
        st.markdown(f"""
        <div class='glass-card' style='text-align: right;'>
            <div style='font-size: 3rem; font-weight: bold; color: {score_color}; line-height: 1;'>
                {'+' if data['final_sentiment_score'] > 0 else ''}{(data['final_sentiment_score'] * 100):.2f}
            </div>
            <div style='color: #94a3b8; font-size: 0.875rem; margin-top: 0.25rem;'>Score Final</div>
        </div>
        """, unsafe_allow_html=True)
    
    # === CLASSIFICATION & CONVICTION ===
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class='glass-card'>
            <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;'>
                <span style='font-size: 1.5rem;'>🎯</span>
                <span style='color: #94a3b8; font-size: 0.875rem;'>Classification</span>
            </div>
            <div style='font-size: 1.875rem; font-weight: bold; color: {get_sentiment_color(data['final_sentiment_score'])};'>
                {data['classification']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='glass-card'>
            <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;'>
                <span style='font-size: 1.5rem;'>⚡</span>
                <span style='color: #94a3b8; font-size: 0.875rem;'>Conviction</span>
            </div>
            <div style='font-size: 1.875rem; font-weight: bold; color: white;'>
                {data['conviction_score'] * 100:.1f}%
            </div>
            <div style='width: 100%; background: #334155; border-radius: 9999px; height: 0.5rem; margin-top: 0.75rem; overflow: hidden;'>
                <div style='background: linear-gradient(to right, #eab308, #f97316); height: 0.5rem; 
                            transition: width 0.5s ease; width: {data['conviction_score'] * 100}%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='glass-card'>
            <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;'>
                <span style='font-size: 1.5rem;'>📈</span>
                <span style='color: #94a3b8; font-size: 0.875rem;'>Confiance</span>
            </div>
            <div style='font-size: 1.875rem; font-weight: bold; color: white;'>
                {data['confidence_level']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # === JAUGE DE SENTIMENT ===
    st.markdown("""
    <div class='glass-card'>
        <h2 style='margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;'>
            <span style='font-size: 1.5rem;'>📊</span>
            Sentiment Global
        </h2>
    """, unsafe_allow_html=True)
    
    render_sentiment_gauge(data['final_sentiment_score'])
    st.markdown("</div>", unsafe_allow_html=True)
    
    # === COMPOSANTES MULTI-DIMENSIONNELLES ===
    st.markdown("""
    <div class='glass-card'>
        <h2 style='margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;'>
            <span style='font-size: 1.5rem;'>📈</span>
            Composantes Multi-Dimensionnelles
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    comp = data['components']
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_component_bar(
            "📰", "Sentiment Nouvelles", 
            comp['news_sentiment'], 
            comp['news_confidence'], 
            comp['news_weight']
        )
        render_component_bar(
            "🚀", "Momentum Narratif", 
            comp['narrative_momentum']
        )
    
    with col2:
        render_component_bar(
            "📊", "Sentiment Options", 
            comp['options_sentiment'], 
            comp['options_confidence'], 
            comp['options_weight']
        )
        render_component_bar(
            "😨", "Peur/Greed Asymétrie", 
            comp['fear_greed_asymmetry']
        )
    
    # === ANALYSE DE DIVERGENCE ===
    div = data['divergence_analysis']
    st.markdown("""
    <div class='glass-card'>
        <h2 style='margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;'>
            <span style='font-size: 1.5rem;'>⚠️</span>
            Détection de Divergence
        </h2>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div>
            <div style='color: #94a3b8; font-size: 0.875rem; margin-bottom: 0.5rem;'>Type</div>
            <div style='font-size: 1.5rem; font-weight: bold; color: white;'>
                {div['type'].replace('_', ' ').upper()}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div>
            <div style='color: #94a3b8; font-size: 0.875rem; margin-bottom: 0.5rem;'>Magnitude</div>
            <div style='font-size: 1.5rem; font-weight: bold; color: #06b6d4;'>
                {div['magnitude']:.4f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div>
            <div style='color: #94a3b8; font-size: 0.875rem; margin-bottom: 0.5rem;'>Score d'Opportunité</div>
            <div style='font-size: 1.5rem; font-weight: bold; color: #a855f7;'>
                {div['opportunity_score']:.4f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style='margin-top: 1.5rem; padding: 1rem; background: rgba(51, 65, 85, 0.5); 
                    border-radius: 0.75rem; border: 1px solid #475569;'>
            <div style='color: white;'>{div['interpretation']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # === MÉTADONNÉES ===
    meta = data['metadata']
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class='glass-card'>
            <div style='color: #94a3b8; font-size: 0.875rem; margin-bottom: 0.25rem;'>Articles Analysés</div>
            <div style='font-size: 1.875rem; font-weight: bold; color: white;'>{meta['news_articles_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='glass-card'>
            <div style='color: #94a3b8; font-size: 0.875rem; margin-bottom: 0.25rem;'>Volume Options</div>
            <div style='font-size: 1.875rem; font-weight: bold; color: white;'>{meta['options_volume']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='glass-card'>
            <div style='color: #94a3b8; font-size: 0.875rem; margin-bottom: 0.25rem;'>Profondeur d'Analyse</div>
            <div style='font-size: 1.875rem; font-weight: bold; color: white;'>{meta['analysis_depth']}</div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
