#!/usr/bin/env python3
"""
AI Stocks Timeline Dashboard - Intelligent Sentiment Evolution
Visualize sentiment trends over time with automatic event detection
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import numpy as np
from email.utils import parsedate_to_datetime
import sys

# Add scripts path for trend detection
sys.path.insert(0, '/data/scripts')
try:
    from trend_detection import TrendDetector
    TREND_DETECTION_AVAILABLE = True
except ImportError:
    TREND_DETECTION_AVAILABLE = False

# Configuration
st.set_page_config(
    page_title="AI Stocks Timeline",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded"
)

COMPANIES_DIR = "/data/files/companies"

@st.cache_data
def load_all_companies_timeline():
    """Load timeline data for all companies"""
    companies_data = []
    
    for filename in os.listdir(COMPANIES_DIR):
        if not filename.endswith('_news.json'):
            continue
            
        filepath = os.path.join(COMPANIES_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ticker = data['ticker']
        company_name = data['company_name']
        articles = data['articles']
        
        # Filter analyzed articles
        analyzed = [a for a in articles if 'sentiment_adjusted' in a]
        
        if not analyzed:
            continue
        
        # Convert dates and extract sentiment over time
        timeline_points = []
        for article in analyzed:
            try:
                pub_date_str = article.get('published_at', '')
                if 'GMT' in pub_date_str or ',' in pub_date_str:
                    # RSS format
                    pub_date = parsedate_to_datetime(pub_date_str)
                else:
                    # ISO format
                    pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                
                # Normalize to offset-aware UTC
                if pub_date.tzinfo is None:
                    from datetime import timezone
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                
                timeline_points.append({
                    'date': pub_date,
                    'ticker': ticker,
                    'company': company_name,
                    'sentiment_raw': article['sentiment_raw'],
                    'sentiment_adjusted': article['sentiment_adjusted'],
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'llm_explanation': article.get('llm_sentiment', '')
                })
            except Exception as e:
                continue
        
        companies_data.extend(timeline_points)
    
    if not companies_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(companies_data)
    df = df.sort_values('date')
    return df

def detect_sentiment_events(df, ticker, threshold=20):
    """Detect significant sentiment changes (spikes/drops)"""
    company_df = df[df['ticker'] == ticker].copy()
    company_df = company_df.sort_values('date')
    
    events = []
    for i in range(1, len(company_df)):
        prev_sentiment = company_df.iloc[i-1]['sentiment_adjusted']
        curr_sentiment = company_df.iloc[i]['sentiment_adjusted']
        change = curr_sentiment - prev_sentiment
        
        if abs(change) >= threshold:
            event_type = "[UP] Spike" if change > 0 else "[DOWN] Drop"
            events.append({
                'date': company_df.iloc[i]['date'],
                'type': event_type,
                'change': change,
                'sentiment': curr_sentiment,
                'title': company_df.iloc[i]['title']
            })
    
    return events

def calculate_rolling_average(df, ticker, window_days=7):
    """Calculate rolling average sentiment"""
    company_df = df[df['ticker'] == ticker].copy()
    company_df = company_df.sort_values('date')
    company_df = company_df.set_index('date')
    
    # Resample to daily and fill missing days
    daily = company_df.resample('D').agg({
        'sentiment_adjusted': 'mean'
    })
    
    # Calculate rolling average
    daily['rolling_avg'] = daily['sentiment_adjusted'].rolling(
        window=window_days, 
        min_periods=1
    ).mean()
    
    return daily.reset_index()

# ================== MAIN ==================

st.title("AI Stocks Sentiment Timeline")
st.markdown("### Intelligent Timeline Analysis with Automatic Event Detection")

# Load data
df = load_all_companies_timeline()

if df.empty:
    st.error("[!] No analyzed data found. Run analysis first!")
    st.stop()

# Sidebar filters
st.sidebar.header("[Filters]")

# Company selection
available_tickers = sorted(df['ticker'].unique())
selected_tickers = st.sidebar.multiselect(
    "Select Companies",
    available_tickers,
    default=available_tickers[:5] if len(available_tickers) >= 5 else available_tickers
)

# Date range
min_date = df['date'].min().date()
max_date = df['date'].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df[
        (df['ticker'].isin(selected_tickers)) &
        (df['date'].dt.date >= start_date) &
        (df['date'].dt.date <= end_date)
    ]
    date_range_days = (end_date - start_date).days
else:
    df_filtered = df[df['ticker'].isin(selected_tickers)]
    date_range_days = 60  # Default

# Analysis options
st.sidebar.header("[Analysis Options]")
show_rolling_avg = st.sidebar.checkbox("Show Rolling Average (7d)", value=True)
show_events = st.sidebar.checkbox("Show Significant Events", value=True)
event_threshold = st.sidebar.slider("Event Detection Threshold", 10, 50, 20)

# ================== OVERVIEW METRICS ==================

st.header("Current Status Overview")

cols = st.columns(4)

with cols[0]:
    st.metric(
        "Total Articles",
        f"{len(df_filtered):,}",
        delta=None
    )

with cols[1]:
    avg_sentiment = df_filtered['sentiment_adjusted'].mean()
    st.metric(
        "Average Sentiment",
        f"{avg_sentiment:+.1f}",
        delta=None,
        delta_color="normal" if avg_sentiment > 0 else "inverse"
    )

with cols[2]:
    # Calculate trend (last 7 days vs previous 7 days)
    import pandas as pd
    today = pd.Timestamp.now(tz='UTC')
    last_7d = df_filtered[df_filtered['date'] >= today - pd.Timedelta(days=7)]
    prev_7d = df_filtered[
        (df_filtered['date'] >= today - pd.Timedelta(days=14)) &
        (df_filtered['date'] < today - pd.Timedelta(days=7))
    ]
    
    if len(last_7d) > 0 and len(prev_7d) > 0:
        trend = last_7d['sentiment_adjusted'].mean() - prev_7d['sentiment_adjusted'].mean()
        st.metric(
            "7-Day Trend",
            f"{last_7d['sentiment_adjusted'].mean():+.1f}",
            delta=f"{trend:+.1f}",
            delta_color="normal" if trend > 0 else "inverse"
        )
    else:
        st.metric("7-Day Trend", "N/A")

with cols[3]:
    # Volatility (std dev of last 30 days)
    import pandas as pd
    today_utc = pd.Timestamp.now(tz='UTC')
    last_30d = df_filtered[df_filtered['date'] >= today_utc - pd.Timedelta(days=30)]
    if len(last_30d) > 0:
        volatility = last_30d['sentiment_adjusted'].std()
        st.metric(
            "Volatility (30d)",
            f"{volatility:.1f}",
            delta=None
        )
    else:
        st.metric("Volatility (30d)", "N/A")

# ================== MAIN TIMELINE CHART ==================

st.header("Sentiment Evolution Timeline")

fig = go.Figure()

# Color palette for companies
colors = px.colors.qualitative.Plotly

for i, ticker in enumerate(selected_tickers):
    ticker_df = df_filtered[df_filtered['ticker'] == ticker]
    company_name = ticker_df.iloc[0]['company'] if len(ticker_df) > 0 else ticker
    
    # Add scatter plot for individual articles
    fig.add_trace(go.Scatter(
        x=ticker_df['date'],
        y=ticker_df['sentiment_adjusted'],
        mode='markers',
        name=f"{ticker} - Articles",
        marker=dict(
            size=8,
            color=colors[i % len(colors)],
            opacity=0.6,
            line=dict(width=1, color='white')
        ),
        customdata=ticker_df[['title', 'url']],
        hovertemplate=(
            f"<b>{ticker}</b><br>" +
            "Date: %{x|%Y-%m-%d %H:%M}<br>" +
            "Sentiment: %{y:+.1f}<br>" +
            "Title: %{customdata[0]}<br>" +
            "<extra></extra>"
        ),
        legendgroup=ticker
    ))
    
    # Add rolling average if enabled
    if show_rolling_avg and len(ticker_df) > 3:
        rolling_df = calculate_rolling_average(df_filtered, ticker, window_days=7)
        fig.add_trace(go.Scatter(
            x=rolling_df['date'],
            y=rolling_df['rolling_avg'],
            mode='lines',
            name=f"{ticker} - 7d Avg",
            line=dict(
                color=colors[i % len(colors)],
                width=3
            ),
            legendgroup=ticker,
            showlegend=False
        ))
    
    # Detect and mark significant events
    if show_events:
        events = detect_sentiment_events(df_filtered, ticker, threshold=event_threshold)
        if events:
            events_df = pd.DataFrame(events)
            
            # Spikes et Drops d??sactiv??s pour ne pas afficher de triangles
            # Garde seulement les lignes de tendance (rolling average)
            pass

# Add zero line
fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

# Add threshold zones
fig.add_hrect(y0=40, y1=100, fillcolor="green", opacity=0.1, line_width=0)
fig.add_hrect(y0=-40, y1=-100, fillcolor="red", opacity=0.1, line_width=0)

fig.update_layout(
    title="Sentiment Evolution Over Time",
    xaxis_title="Date",
    yaxis_title="Sentiment Score (-100 to +100)",
    hovermode='closest',
    height=600,
    showlegend=True,
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left",
        x=1.01
    ),
    plot_bgcolor='rgba(240,240,240,0.5)',
    yaxis=dict(
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='black',
        range=[-100, 100]
    )
)

st.plotly_chart(fig, use_container_width=True)

# ================== EVENTS TABLE ==================

if show_events:
    st.header("Significant Sentiment Events")
    
    # Company filter for events
    col1, col2 = st.columns([3, 1])
    with col1:
        event_companies = st.multiselect(
            "Filter events by company:",
            selected_tickers,
            default=selected_tickers,
            key="event_company_filter"
        )
    with col2:
        st.metric("Event Threshold", f"{event_threshold}")
    
    all_events = []
    for ticker in event_companies:
        events = detect_sentiment_events(df_filtered, ticker, threshold=event_threshold)
        for event in events:
            event['ticker'] = ticker
        all_events.extend(events)
    
    if all_events:
        events_df = pd.DataFrame(all_events)
        events_df = events_df.sort_values('date', ascending=False)
        
        # Format for display
        events_df['date_formatted'] = events_df['date'].dt.strftime('%Y-%m-%d %H:%M')
        events_df['sentiment_formatted'] = events_df['sentiment'].apply(lambda x: f"{x:+.1f}")
        events_df['change_formatted'] = events_df['change'].apply(lambda x: f"{x:+.1f}")
        
        st.dataframe(
            events_df[['date_formatted', 'ticker', 'type', 'sentiment_formatted', 'change_formatted', 'title']].rename(columns={
                'date_formatted': 'Date',
                'ticker': 'Ticker',
                'type': 'Event',
                'sentiment_formatted': 'Sentiment',
                'change_formatted': 'Change',
                'title': 'Article Title'
            }),
            use_container_width=True,
            height=400
        )
        
        # Summary stats
        st.markdown(f"**Total Events:** {len(events_df)} | **Spikes:** {len(events_df[events_df['type'] == '[UP] Spike'])} | **Drops:** {len(events_df[events_df['type'] == '[DOWN] Drop'])}")
    else:
        st.info("No significant events detected with current threshold.")

# ================== COMPARATIVE HEATMAP ==================

st.header("Sentiment Heatmap (Daily Averages)")

# Prepare data for heatmap
heatmap_data = []
for ticker in selected_tickers:
    ticker_df = df_filtered[df_filtered['ticker'] == ticker].copy()
    ticker_df['date_only'] = ticker_df['date'].dt.date
    daily_avg = ticker_df.groupby('date_only')['sentiment_adjusted'].mean().reset_index()
    daily_avg['ticker'] = ticker
    heatmap_data.append(daily_avg)

if heatmap_data:
    heatmap_df = pd.concat(heatmap_data)
    
    # Pivot for heatmap
    pivot_df = heatmap_df.pivot(index='ticker', columns='date_only', values='sentiment_adjusted')
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=[str(d) for d in pivot_df.columns],
        y=pivot_df.index,
        colorscale='RdYlGn',
        zmid=0,
        zmin=-50,
        zmax=50,
        colorbar=dict(title="Sentiment"),
        hovertemplate='Date: %{x}<br>Ticker: %{y}<br>Sentiment: %{z:+.1f}<extra></extra>'
    ))
    
    fig_heatmap.update_layout(
        title="Daily Average Sentiment Heatmap",
        xaxis_title="Date",
        yaxis_title="Company",
        height=400
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)

# ================== COMPANY COMPARISON ==================

st.header("Company Comparison")

comparison_data = []
for ticker in selected_tickers:
    ticker_df = df_filtered[df_filtered['ticker'] == ticker]
    if len(ticker_df) > 0:
        comparison_data.append({
            'Ticker': ticker,
            'Company': ticker_df.iloc[0]['company'],
            'Articles': len(ticker_df),
            'Avg Sentiment': ticker_df['sentiment_adjusted'].mean(),
            'Max Sentiment': ticker_df['sentiment_adjusted'].max(),
            'Min Sentiment': ticker_df['sentiment_adjusted'].min(),
            'Volatility (StdDev)': ticker_df['sentiment_adjusted'].std()
        })

if comparison_data:
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df = comparison_df.sort_values('Avg Sentiment', ascending=False)
    
    # Format numbers
    comparison_df['Avg Sentiment'] = comparison_df['Avg Sentiment'].apply(lambda x: f"{x:+.1f}")
    comparison_df['Max Sentiment'] = comparison_df['Max Sentiment'].apply(lambda x: f"{x:+.1f}")
    comparison_df['Min Sentiment'] = comparison_df['Min Sentiment'].apply(lambda x: f"{x:+.1f}")
    comparison_df['Volatility (StdDev)'] = comparison_df['Volatility (StdDev)'].apply(lambda x: f"{x:.1f}")
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

# ================== TREND ANALYSIS WITH REGRESSION ==================

if TREND_DETECTION_AVAILABLE and len(selected_tickers) > 0:
    st.header("Trend Analysis & Pattern Detection")
    
    # Select company for detailed trend analysis
    trend_ticker = st.selectbox(
        "Select company for detailed trend analysis:",
        selected_tickers,
        key="trend_analysis_selector"
    )
    
    if trend_ticker:
        # Load full company data
        filepath = os.path.join(COMPANIES_DIR, f"{trend_ticker}_news.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            company_data = json.load(f)
        
        articles = company_data.get('articles', company_data)
        
        # Run trend detection
        detector = TrendDetector(
            articles,
            outlier_threshold=1.2,
            shift_window_days=14,
            shift_min_articles=2,
            lookback_days=date_range_days
        )
        
        result = detector.analyze()
        
        if 'error' not in result:
            trend_line = result['trend_line']
            stats = result['stats']
            outliers = result['outliers']
            shift = result.get('shift')
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Trend Slope", f"{trend_line.slope:+.2f} pts/day")
            with col2:
                st.metric("R2 (Fit Quality)", f"{trend_line.r_squared:.3f}")
            with col3:
                st.metric("Std Dev (sigma)", f"{trend_line.std_dev:.1f}")
            with col4:
                st.metric("Outliers", f"{stats['outlier_count']}")
            
            # Shift detection alert
            if shift:
                st.warning(f"**SHIFT DETECTED**: {shift['interpretation']}")
                st.markdown(f"**Force:** {shift['strength']:.2f}sigma | **Confidence:** {shift['confidence']*100:.0f}%")
            
            # Prepare data for regression plot
            ticker_df = df_filtered[df_filtered['ticker'] == trend_ticker].copy()
            ticker_df = ticker_df.sort_values('date')
            
            if len(ticker_df) > 0:
                # Calculate regression line points
                min_date_ts = ticker_df['date'].min()
                ticker_df['days_from_start'] = (ticker_df['date'] - min_date_ts).dt.total_seconds() / 86400
                
                days = ticker_df['days_from_start'].values
                predicted = trend_line.slope * days + trend_line.intercept
                upper_band = predicted + 2 * trend_line.std_dev
                lower_band = predicted - 2 * trend_line.std_dev
                
                # Create figure
                fig_trend = go.Figure()
                
                # Actual sentiment points
                fig_trend.add_trace(go.Scatter(
                    x=ticker_df['date'],
                    y=ticker_df['sentiment_adjusted'],
                    mode='markers',
                    name='Actual Sentiment',
                    marker=dict(size=6, color='lightblue', opacity=0.6),
                    hovertemplate='%{x}<br>Sentiment: %{y:+.1f}<extra></extra>'
                ))
                
                # Regression line
                fig_trend.add_trace(go.Scatter(
                    x=ticker_df['date'],
                    y=predicted,
                    mode='lines',
                    name='Trend Line (Regression)',
                    line=dict(color='red', width=2, dash='dash'),
                    hovertemplate='Predicted: %{y:+.1f}<extra></extra>'
                ))
                
                # Variance bands (+/-2 sigma)
                fig_trend.add_trace(go.Scatter(
                    x=ticker_df['date'],
                    y=upper_band,
                    mode='lines',
                    name='+2sigma Band',
                    line=dict(color='rgba(255,0,0,0.2)', width=0),
                    showlegend=True,
                    hoverinfo='skip'
                ))
                
                fig_trend.add_trace(go.Scatter(
                    x=ticker_df['date'],
                    y=lower_band,
                    mode='lines',
                    name='-2sigma Band',
                    line=dict(color='rgba(255,0,0,0.2)', width=0),
                    fill='tonexty',
                    fillcolor='rgba(255,0,0,0.1)',
                    showlegend=True,
                    hoverinfo='skip'
                ))
                
                # Highlight outliers
                if outliers:
                    outlier_dates = [o.article.get('published_at') for o in outliers]
                    outlier_sentiments = [o.article.get('sentiment_adjusted') for o in outliers]
                    outlier_colors = ['green' if o.direction == 'positive' else 'red' for o in outliers]
                    
                    # Parse dates
                    outlier_dates_parsed = []
                    for d in outlier_dates:
                        try:
                            if 'GMT' in d or ',' in d:
                                outlier_dates_parsed.append(parsedate_to_datetime(d))
                            else:
                                outlier_dates_parsed.append(datetime.fromisoformat(d.replace('Z', '+00:00')))
                        except:
                            outlier_dates_parsed.append(None)
                    
                    fig_trend.add_trace(go.Scatter(
                        x=outlier_dates_parsed,
                        y=outlier_sentiments,
                        mode='markers',
                        name='Outliers (>1.2sigma)',
                        marker=dict(
                            size=12,
                            color=outlier_colors,
                            symbol='star',
                            line=dict(width=2, color='white')
                        ),
                        hovertemplate='%{x}<br>Outlier: %{y:+.1f}<extra></extra>'
                    ))
                
                fig_trend.update_layout(
                    title=f"{trend_ticker} - Regression Line & Variance Bands (+/-2sigma)",
                    xaxis_title="Date",
                    yaxis_title="Sentiment Score",
                    hovermode='closest',
                    height=500,
                    showlegend=True
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # Outliers table
                if outliers:
                    st.subheader("Detected Outliers")
                    outlier_data = []
                    for o in outliers[:10]:
                        outlier_data.append({
                            'Weight (sigma)': f"{o.outlier_weight:.2f}",
                            'Direction': '[+] Positive' if o.direction == 'positive' else '[-] Negative',
                            'Sentiment': f"{o.article.get('sentiment_adjusted'):+.1f}",
                            'Residual': f"{o.residual:+.1f}",
                            'Recent': '[!] Yes' if o.is_recent else 'No',
                            'Title': o.article.get('title', '')[:60]
                        })
                    
                    st.dataframe(pd.DataFrame(outlier_data), use_container_width=True, hide_index=True)
        else:
            st.info(f"Not enough data for trend analysis: {result.get('error')}")
else:
    if not TREND_DETECTION_AVAILABLE:
        st.info("Trend detection module not available. Install scipy to enable.")

# ================== FOOTER ==================

st.markdown("---")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown(f"**Total Companies Analyzed:** {len(available_tickers)} | **Date Range:** {min_date} to {max_date}")
