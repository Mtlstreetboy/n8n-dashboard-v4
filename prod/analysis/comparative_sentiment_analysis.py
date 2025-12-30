#!/usr/bin/env python3
"""
📊 Analyse Comparative de Sentiment Multi-Tickers
--------------------------------------------------------------------
Compare les sentiments entre différentes compagnies tech pour identifier
les tendances, leaders et laggards du marché.

Usage:
    python3 comparative_sentiment_analysis.py [options]
    
Options:
    --days N          Analyser les N derniers jours (défaut: 30)
    --min-articles N  Minimum d'articles requis (défaut: 10)
    --export CSV      Exporter en CSV
"""
import sys
sys.path.insert(0, '/data/scripts')

import os
import json
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import statistics

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    print("📦 Installation de rich...")
    os.system("pip install rich -q")
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True

console = Console()

NEWS_DATA_DIR = '/data/files/companies'

# Catégories de compagnies
CATEGORIES = {
    "Semiconducteurs": ["NVDA", "AMD", "INTC", "AVGO"],
    "Cloud/SaaS": ["MSFT", "GOOGL", "AMZN", "CRM", "NOW", "SNOW"],
    "AI Pure Players": ["OPENAI", "ANTHROPIC", "MISTRAL", "COHERE"],
    "Data/Analytics": ["PLTR", "ORCL"],
    "Design/Creative": ["ADBE"],
    "Autres": ["TSLA", "META"]
}

def load_ticker_sentiments(ticker, days=30):
    """Charge les sentiments d'un ticker pour les N derniers jours"""
    filepath = os.path.join(NEWS_DATA_DIR, f"{ticker}_news.json")
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get('articles', [])
    # Utiliser des dates aware en UTC pour comparer correctement
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    sentiments = []
    recent_articles = 0
    
    for article in articles:
        pub_date_str = article.get('published_at', '')
        if not pub_date_str:
            continue
        
        try:
            pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            else:
                pub_date = pub_date.astimezone(timezone.utc)
        except:
            continue
        
        if pub_date < cutoff_date:
            continue
        
        recent_articles += 1
        sentiment = article.get('sentiment', {})
        
        if sentiment and sentiment.get('model') == 'finbert':
            sentiments.append({
                'compound': sentiment.get('compound', 0.0),
                'positive': sentiment.get('positive', 0.0),
                'negative': sentiment.get('negative', 0.0),
                'neutral': sentiment.get('neutral', 0.0),
                'date': pub_date
            })
    
    return {
        'ticker': ticker,
        'total_articles': recent_articles,
        'analyzed_articles': len(sentiments),
        'sentiments': sentiments
    }

def calculate_metrics(sentiments):
    """Calcule les métriques agrégées"""
    if not sentiments:
        return None
    
    compounds = [s['compound'] for s in sentiments]
    positives = [s['positive'] for s in sentiments]
    negatives = [s['negative'] for s in sentiments]
    
    return {
        'avg_compound': statistics.mean(compounds),
        'median_compound': statistics.median(compounds),
        'stdev_compound': statistics.stdev(compounds) if len(compounds) > 1 else 0,
        'avg_positive': statistics.mean(positives),
        'avg_negative': statistics.mean(negatives),
        'bullish_ratio': sum(1 for c in compounds if c > 0.05) / len(compounds),
        'bearish_ratio': sum(1 for c in compounds if c < -0.05) / len(compounds),
        'neutral_ratio': sum(1 for c in compounds if -0.05 <= c <= 0.05) / len(compounds)
    }

def sentiment_to_emoji(compound):
    """Convertit un score compound en emoji"""
    if compound > 0.5:
        return "🚀"
    elif compound > 0.2:
        return "📈"
    elif compound > 0.05:
        return "🟢"
    elif compound > -0.05:
        return "➖"
    elif compound > -0.2:
        return "🔴"
    elif compound > -0.5:
        return "📉"
    else:
        return "💥"

def main(days=30, min_articles=10, export_csv=None):
    """Analyse comparative principale"""
    console.print(f"\n[bold cyan]📊 Analyse Comparative de Sentiment - {days} derniers jours[/bold cyan]\n")
    
    # Collecter les données
    all_data = {}
    
    for ticker in [t for cats in CATEGORIES.values() for t in cats]:
        data = load_ticker_sentiments(ticker, days)
        if data and data['analyzed_articles'] >= min_articles:
            metrics = calculate_metrics(data['sentiments'])
            if metrics:
                all_data[ticker] = {**data, 'metrics': metrics}
    
    if not all_data:
        console.print("[red]❌ Aucune donnée disponible[/red]")
        return
    
    # Tableau global: Top/Bottom performers
    table_global = Table(title=f"🏆 Classement Global ({len(all_data)} tickers)")
    table_global.add_column("Rang", style="cyan", width=5)
    table_global.add_column("Ticker", style="bold yellow", width=8)
    table_global.add_column("Sentiment", style="green", width=10)
    table_global.add_column("Score", justify="right", width=8)
    table_global.add_column("Articles", justify="right", width=8)
    table_global.add_column("Bullish", justify="right", width=8)
    table_global.add_column("Bearish", justify="right", width=8)
    table_global.add_column("Volatilité", justify="right", width=10)
    
    # Trier par score compound
    sorted_tickers = sorted(
        all_data.items(),
        key=lambda x: x[1]['metrics']['avg_compound'],
        reverse=True
    )
    
    for rank, (ticker, data) in enumerate(sorted_tickers, 1):
        metrics = data['metrics']
        emoji = sentiment_to_emoji(metrics['avg_compound'])
        
        style = "green" if metrics['avg_compound'] > 0 else "red" if metrics['avg_compound'] < 0 else "yellow"
        
        table_global.add_row(
            f"#{rank}",
            ticker,
            emoji,
            f"[{style}]{metrics['avg_compound']:+.3f}[/{style}]",
            str(data['analyzed_articles']),
            f"{metrics['bullish_ratio']*100:.1f}%",
            f"{metrics['bearish_ratio']*100:.1f}%",
            f"±{metrics['stdev_compound']:.3f}"
        )
    
    console.print(table_global)
    console.print()
    
    # Tableaux par catégorie
    for category, tickers in CATEGORIES.items():
        category_data = {t: all_data[t] for t in tickers if t in all_data}
        
        if not category_data:
            continue
        
        table_cat = Table(title=f"🔍 {category}")
        table_cat.add_column("Ticker", style="bold yellow", width=10)
        table_cat.add_column("Sentiment", width=10)
        table_cat.add_column("Score", justify="right", width=10)
        table_cat.add_column("Tendance", width=15)
        table_cat.add_column("Articles", justify="right", width=8)
        
        sorted_cat = sorted(
            category_data.items(),
            key=lambda x: x[1]['metrics']['avg_compound'],
            reverse=True
        )
        
        for ticker, data in sorted_cat:
            metrics = data['metrics']
            emoji = sentiment_to_emoji(metrics['avg_compound'])
            
            # Tendance bullish/bearish
            if metrics['bullish_ratio'] > 0.6:
                trend = "🐂 Très bullish"
            elif metrics['bullish_ratio'] > 0.4:
                trend = "📈 Bullish"
            elif metrics['bearish_ratio'] > 0.6:
                trend = "🐻 Très bearish"
            elif metrics['bearish_ratio'] > 0.4:
                trend = "📉 Bearish"
            else:
                trend = "➖ Neutre"
            
            style = "green" if metrics['avg_compound'] > 0 else "red" if metrics['avg_compound'] < 0 else "yellow"
            
            table_cat.add_row(
                ticker,
                emoji,
                f"[{style}]{metrics['avg_compound']:+.3f}[/{style}]",
                trend,
                str(data['analyzed_articles'])
            )
        
        console.print(table_cat)
        console.print()
    
    # Statistiques agrégées
    all_compounds = [d['metrics']['avg_compound'] for d in all_data.values()]
    
    stats_panel = Panel(
        f"""
[cyan]Statistiques Globales[/cyan]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Tickers analysés: [bold]{len(all_data)}[/bold]
📝 Total articles: [bold]{sum(d['analyzed_articles'] for d in all_data.values()):,}[/bold]

🎯 Sentiment moyen: [bold]{statistics.mean(all_compounds):+.3f}[/bold]
📈 Plus positif: [bold green]{max(all_compounds):+.3f}[/bold green] ({[t for t,d in all_data.items() if d['metrics']['avg_compound'] == max(all_compounds)][0]})
📉 Plus négatif: [bold red]{min(all_compounds):+.3f}[/bold red] ({[t for t,d in all_data.items() if d['metrics']['avg_compound'] == min(all_compounds)][0]})
📊 Médiane: [bold]{statistics.median(all_compounds):+.3f}[/bold]
        """,
        title="📈 Résumé du Marché",
        border_style="cyan"
    )
    
    console.print(stats_panel)
    
    # Export CSV si demandé
    if export_csv:
        import csv
        with open(export_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Ticker', 'Articles', 'Compound', 'Positive', 'Negative',
                'Bullish%', 'Bearish%', 'Neutral%', 'Volatilité'
            ])
            
            for ticker, data in sorted_tickers:
                metrics = data['metrics']
                writer.writerow([
                    ticker,
                    data['analyzed_articles'],
                    f"{metrics['avg_compound']:.4f}",
                    f"{metrics['avg_positive']:.4f}",
                    f"{metrics['avg_negative']:.4f}",
                    f"{metrics['bullish_ratio']*100:.2f}",
                    f"{metrics['bearish_ratio']*100:.2f}",
                    f"{metrics['neutral_ratio']*100:.2f}",
                    f"{metrics['stdev_compound']:.4f}"
                ])
        
        console.print(f"\n[green]✅ Exporté vers {export_csv}[/green]")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyse comparative de sentiment')
    parser.add_argument('--days', type=int, default=30, help='Nombre de jours à analyser')
    parser.add_argument('--min-articles', type=int, default=10, help='Minimum d\'articles requis')
    parser.add_argument('--export', type=str, help='Exporter en CSV')
    
    args = parser.parse_args()
    
    main(days=args.days, min_articles=args.min_articles, export_csv=args.export)
