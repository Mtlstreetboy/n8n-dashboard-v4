#!/usr/bin/env python3
"""
Génère un dashboard HTML SPA à 3 niveaux avec Options Deep Dive
Niveau 1: Grille | Niveau 2: Détail Ticker | Niveau 3: Options Deep Dive
"""
# -*- coding: utf-8 -*-
import json
import os
from pathlib import Path

# Chemins
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent # prod/dashboard -> prod -> root
# Fallback if local_files is in prod
if not (project_root / 'local_files').exists() and (current_dir.parent / 'local_files').exists():
    DATA_ROOT = current_dir.parent / 'local_files'
else:
    DATA_ROOT = project_root / 'local_files'

SENTIMENT_DIR = DATA_ROOT / 'sentiment_analysis'
OPTIONS_DIR = DATA_ROOT / 'options_data'
OUTPUT_FILE = current_dir / 'dashboard_v4_3levels.html'

# Liste des tickers
TICKERS = ['NVDA', 'MSFT', 'GOOGL', 'META', 'AMZN', 'AMD', 'TSLA', 'ORCL', 'CRM', 'PLTR', 'SNOW', 'AVGO', 'ADBE', 'NOW', 'INTC']

def load_all_data():
    """Charge toutes les données (sentiment + options + news)"""
    data = {}
    for ticker in TICKERS:
        # Sentiment data
        sentiment_file = SENTIMENT_DIR / f'{ticker}_latest_v4.json'
        # Options data
        options_file = OPTIONS_DIR / f'{ticker}_latest_sentiment.json'
        # News data - chemin corrigé vers local_files/companies
        news_file = DATA_ROOT / 'companies' / f'{ticker}_news.json'
        
        if sentiment_file.exists():
            with open(sentiment_file, 'r', encoding='utf-8') as f:
                ticker_data = json.load(f)
            
            # Ajouter les données d'options si disponibles
            if options_file.exists():
                with open(options_file, 'r', encoding='utf-8') as f:
                    ticker_data['options_detail'] = json.load(f)
            
            # Ajouter les données de nouvelles si disponibles
            if news_file.exists():
                print(f"📰 Traitement news pour {ticker}...")
                try:
                    with open(news_file, 'r', encoding='utf-8') as f:
                        news_data = json.load(f)
                        print(f"  → Fichier chargé, clés: {list(news_data.keys())}")
                        # Ne garder que les articles des 30 derniers jours
                        from datetime import datetime, timedelta
                        cutoff_date = datetime.now() - timedelta(days=30)
                        print(f"  → Date limite: {cutoff_date.strftime('%Y-%m-%d')}")
                        
                        if 'articles' in news_data:
                            print(f"  → {len(news_data['articles'])} articles totaux trouvés")
                            filtered_articles = []
                            for art in news_data['articles']:
                                if 'published_at' in art:
                                    try:
                                        # Parser la date et la convertir en naive datetime (sans timezone)
                                        pub_date = datetime.fromisoformat(art['published_at'].replace('Z', '+00:00'))
                                        # Retirer la timezone pour comparer avec datetime.now()
                                        pub_date_naive = pub_date.replace(tzinfo=None)
                                        if pub_date_naive >= cutoff_date:
                                            filtered_articles.append(art)
                                    except Exception as e:
                                        # Si erreur de parsing, on ignore cet article
                                        print(f"  ⚠️  Erreur parsing date: {e}")
                                        continue
                            
                            ticker_data['news_articles'] = {
                                'total': len(filtered_articles),
                                'articles': filtered_articles[:100]  # Limiter à 100 articles max
                            }
                            print(f"✅ {ticker}: {len(filtered_articles)} articles chargés (30 derniers jours)")
                        else:
                            print(f"  ⚠️  Clé 'articles' non trouvée dans {ticker}_news.json")
                except Exception as e:
                    print(f"⚠️ Erreur chargement news pour {ticker}: {e}")
                    import traceback
                    traceback.print_exc()
                    ticker_data['news_articles'] = {'total': 0, 'articles': []}
            else:
                print(f"  ℹ️  Pas de fichier news pour {ticker}")
            
            data[ticker] = ticker_data
    
    return data

def generate_3level_spa_html(all_data):
    """Génère le HTML SPA à 3 niveaux"""
    
    data_json = json.dumps(all_data, ensure_ascii=False)
    
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentiment V4 Dashboard - 3 Levels</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
        const {{ useState }} = React;
        const EMBEDDED_DATA = {data_json};

        // Utility functions
        const getSentimentColor = (score) => {{
            if (score > 0.5) return 'text-green-500';
            if (score > 0.2) return 'text-green-400';
            if (score < -0.5) return 'text-red-500';
            if (score < -0.2) return 'text-red-400';
            return 'text-yellow-500';
        }};

        const getSentimentBg = (score) => {{
            if (score > 0.5) return 'bg-green-500';
            if (score > 0.2) return 'bg-green-400';
            if (score < -0.5) return 'bg-red-500';
            if (score < -0.2) return 'bg-red-400';
            return 'bg-yellow-500';
        }};

        // Breadcrumb Component
        const Breadcrumb = ({{ path, onNavigate }}) => (
            <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
                {{path.map((item, idx) => (
                    <React.Fragment key={{idx}}>
                        {{idx > 0 && <span>›</span>}}
                        <button
                            onClick={{() => onNavigate(item.view, item.ticker, item.section)}}
                            className={{`hover:text-cyan-400 transition-colors ${{idx === path.length - 1 ? 'text-white font-semibold' : ''}}`}}
                        >
                            {{item.label}}
                        </button>
                    </React.Fragment>
                ))}}
            </div>
        );

        // NIVEAU 3: Options Deep Dive
        const OptionsDeepDive = ({{ ticker, data, onBack }}) => {{
            const opts = data.options_detail;
            if (!opts) {{
                return (
                    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
                        <div className="max-w-7xl mx-auto">
                            <button onClick={{onBack}} className="text-cyan-400 hover:text-cyan-300 mb-6">← Retour</button>
                            <div className="text-white text-2xl">Données d'options non disponibles</div>
                        </div>
                    </div>
                );
            }}

            const pcrVolume = opts.put_call_ratio_volume;
            const pcrOI = opts.put_call_ratio_oi;
            const callIV = opts.call_implied_volatility;
            const putIV = opts.put_implied_volatility;
            const ivSkew = callIV - putIV;

            return (
                <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
                    <div className="max-w-7xl mx-auto space-y-6">
                        <Breadcrumb 
                            path={{[
                                {{ label: 'Grille', view: 'grid' }},
                                {{ label: ticker, view: 'detail', ticker }},
                                {{ label: 'Options Deep Dive', view: 'deepdive', ticker, section: 'options' }}
                            ]}}
                            onNavigate={{(view, t, s) => {{
                                if (view === 'grid') onBack('grid');
                                else if (view === 'detail') onBack('detail');
                            }}}}
                        />

                        {{/* Header */}}
                        <div className="bg-gradient-to-r from-cyan-900/30 to-blue-900/30 backdrop-blur-sm border border-cyan-700/50 rounded-2xl p-8">
                            <h1 className="text-4xl font-bold text-white mb-2">📊 Options Deep Dive - {{ticker}}</h1>
                            <p className="text-slate-400">Analyse détaillée du marché des options</p>
                        </div>

                        {{/* Key Metrics Grid */}}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-2">Sentiment Global</div>
                                <div className={{`text-3xl font-bold ${{opts.sentiment_label === 'bullish' ? 'text-green-400' : opts.sentiment_label === 'bearish' ? 'text-red-400' : 'text-yellow-400'}}`}}>
                                    {{opts.sentiment_label.toUpperCase()}}
                                </div>
                                <div className="text-slate-500 text-sm mt-2">Score: {{opts.sentiment_score.toFixed(3)}}</div>
                            </div>

                            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-2">Volume Total</div>
                                <div className="text-3xl font-bold text-white">{{opts.total_contracts.toLocaleString()}}</div>
                                <div className="text-slate-500 text-sm mt-2">Contrats</div>
                            </div>

                            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-2">Open Interest</div>
                                <div className="text-3xl font-bold text-white">{{opts.total_open_interest.toLocaleString()}}</div>
                                <div className="text-slate-500 text-sm mt-2">Contrats ouverts</div>
                            </div>

                            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-2">Timestamp</div>
                                <div className="text-lg font-bold text-white">{{new Date(opts.timestamp).toLocaleTimeString('fr-FR')}}</div>
                                <div className="text-slate-500 text-sm mt-2">{{new Date(opts.timestamp).toLocaleDateString('fr-FR')}}</div>
                            </div>
                        </div>

                        {{/* Put/Call Ratios */}}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
                                <h2 className="text-xl font-semibold text-white mb-6">📊 Put/Call Ratio - Volume</h2>
                                <div className="text-center mb-6">
                                    <div className={{`text-6xl font-bold ${{pcrVolume < 0.7 ? 'text-green-400' : pcrVolume > 1.0 ? 'text-red-400' : 'text-yellow-400'}}`}}>
                                        {{pcrVolume.toFixed(3)}}
                                    </div>
                                    <div className="text-slate-400 text-sm mt-2">
                                        {{pcrVolume < 0.7 ? '🚀 Très Bullish' : pcrVolume > 1.0 ? '🐻 Bearish' : '⚖️ Neutre'}}
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-slate-400">Call Volume</span>
                                        <span className="text-green-400 font-bold">{{opts.call_volume.toLocaleString()}}</span>
                                    </div>
                                    <div className="w-full bg-slate-700 rounded-full h-3">
                                        <div className="bg-green-500 h-3 rounded-full" style={{{{ width: `${{(opts.call_volume / opts.total_contracts) * 100}}%` }}}}></div>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-slate-400">Put Volume</span>
                                        <span className="text-red-400 font-bold">{{opts.put_volume.toLocaleString()}}</span>
                                    </div>
                                    <div className="w-full bg-slate-700 rounded-full h-3">
                                        <div className="bg-red-500 h-3 rounded-full" style={{{{ width: `${{(opts.put_volume / opts.total_contracts) * 100}}%` }}}}></div>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
                                <h2 className="text-xl font-semibold text-white mb-6">📈 Put/Call Ratio - Open Interest</h2>
                                <div className="text-center mb-6">
                                    <div className={{`text-6xl font-bold ${{pcrOI < 0.7 ? 'text-green-400' : pcrOI > 1.0 ? 'text-red-400' : 'text-yellow-400'}}`}}>
                                        {{pcrOI.toFixed(3)}}
                                    </div>
                                    <div className="text-slate-400 text-sm mt-2">
                                        {{pcrOI < 0.7 ? '📈 Positionnement Haussier' : pcrOI > 1.0 ? '📉 Positionnement Baissier' : '➡️ Équilibré'}}
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-slate-400">Call OI</span>
                                        <span className="text-green-400 font-bold">{{opts.call_open_interest.toLocaleString()}}</span>
                                    </div>
                                    <div className="w-full bg-slate-700 rounded-full h-3">
                                        <div className="bg-green-500 h-3 rounded-full" style={{{{ width: `${{(opts.call_open_interest / opts.total_open_interest) * 100}}%` }}}}></div>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-slate-400">Put OI</span>
                                        <span className="text-red-400 font-bold">{{opts.put_open_interest.toLocaleString()}}</span>
                                    </div>
                                    <div className="w-full bg-slate-700 rounded-full h-3">
                                        <div className="bg-red-500 h-3 rounded-full" style={{{{ width: `${{(opts.put_open_interest / opts.total_open_interest) * 100}}%` }}}}></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {{/* Implied Volatility */}}
                        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
                            <h2 className="text-xl font-semibold text-white mb-6">🌪️ Implied Volatility Analysis</h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="bg-slate-700/50 rounded-xl p-6">
                                    <div className="text-slate-400 text-sm mb-2">Call IV</div>
                                    <div className="text-4xl font-bold text-green-400 mb-2">{{(callIV * 100).toFixed(1)}}%</div>
                                    <div className="text-slate-500 text-xs">Volatilité implicite des calls</div>
                                </div>
                                <div className="bg-slate-700/50 rounded-xl p-6">
                                    <div className="text-slate-400 text-sm mb-2">Put IV</div>
                                    <div className="text-4xl font-bold text-red-400 mb-2">{{(putIV * 100).toFixed(1)}}%</div>
                                    <div className="text-slate-500 text-xs">Volatilité implicite des puts</div>
                                </div>
                                <div className="bg-slate-700/50 rounded-xl p-6">
                                    <div className="text-slate-400 text-sm mb-2">IV Skew</div>
                                    <div className={{`text-4xl font-bold ${{ivSkew > 0 ? 'text-orange-400' : 'text-purple-400'}}`}}>
                                        {{ivSkew > 0 ? '+' : ''}}{{(ivSkew * 100).toFixed(1)}}%
                                    </div>
                                    <div className="text-slate-500 text-xs">
                                        {{ivSkew > 0 ? '📞 Call skew (spéculation haussière)' : '📉 Put skew (protection baissière)'}}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {{/* Near-term vs Far-term */}}
                        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
                            <h2 className="text-xl font-semibold text-white mb-6">⏰ Distribution Temporelle</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <h3 className="text-lg font-semibold text-white mb-4">Calls</h3>
                                    <div className="space-y-4">
                                        <div>
                                            <div className="flex justify-between text-sm mb-2">
                                                <span className="text-slate-400">Near-term</span>
                                                <span className="text-green-400 font-bold">{{opts.near_term_call_volume.toLocaleString()}}</span>
                                            </div>
                                            <div className="w-full bg-slate-700 rounded-full h-3">
                                                <div className="bg-green-500 h-3 rounded-full" style={{{{ width: `${{(opts.near_term_call_volume / opts.call_volume) * 100}}%` }}}}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-sm mb-2">
                                                <span className="text-slate-400">Far-term</span>
                                                <span className="text-green-300 font-bold">{{opts.far_term_call_volume.toLocaleString()}}</span>
                                            </div>
                                            <div className="w-full bg-slate-700 rounded-full h-3">
                                                <div className="bg-green-300 h-3 rounded-full" style={{{{ width: `${{(opts.far_term_call_volume / opts.call_volume) * 100}}%` }}}}></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-white mb-4">Puts</h3>
                                    <div className="space-y-4">
                                        <div>
                                            <div className="flex justify-between text-sm mb-2">
                                                <span className="text-slate-400">Near-term</span>
                                                <span className="text-red-400 font-bold">{{opts.near_term_put_volume.toLocaleString()}}</span>
                                            </div>
                                            <div className="w-full bg-slate-700 rounded-full h-3">
                                                <div className="bg-red-500 h-3 rounded-full" style={{{{ width: `${{(opts.near_term_put_volume / opts.put_volume) * 100}}%` }}}}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-sm mb-2">
                                                <span className="text-slate-400">Far-term</span>
                                                <span className="text-red-300 font-bold">{{opts.far_term_put_volume.toLocaleString()}}</span>
                                            </div>
                                            <div className="w-full bg-slate-700 rounded-full h-3">
                                                <div className="bg-red-300 h-3 rounded-full" style={{{{ width: `${{(opts.far_term_put_volume / opts.put_volume) * 100}}%` }}}}></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {{/* Interpretation */}}
                        <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 border border-purple-700/50 rounded-2xl p-8">
                            <h2 className="text-xl font-semibold text-white mb-4">💡 Interprétation</h2>
                            <div className="space-y-3 text-slate-300">
                                <p>
                                    <strong className="text-white">Sentiment:</strong> Le marché des options affiche un sentiment <strong className={{opts.sentiment_label === 'bullish' ? 'text-green-400' : 'text-red-400'}}>{{opts.sentiment_label}}</strong> avec un score de {{opts.sentiment_score.toFixed(3)}}.
                                </p>
                                <p>
                                    <strong className="text-white">Put/Call Ratio:</strong> {{pcrVolume < 0.7 ? 'Le faible PCR volume indique une forte demande pour les calls, suggérant un positionnement haussier agressif.' : pcrVolume > 1.0 ? 'Le PCR élevé montre une préférence pour les puts, indiquant une couverture baissière ou des paris directionnels négatifs.' : 'Le PCR équilibré suggère un marché indécis ou une activité de hedging symétrique.'}}
                                </p>
                                <p>
                                    <strong className="text-white">IV Skew:</strong> {{ivSkew > 0 ? 'Le skew positif (call IV > put IV) indique une spéculation haussière agressive avec prime sur les calls.' : 'Le skew négatif (put IV > call IV) suggère une demande élevée pour la protection baissière.'}}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }};

        // NIVEAU 3B: News Timeline SIMPLIFIED PREMIUM (30 derniers jours)
        const NewsTimeline = ({{ ticker, data, onBack }}) => {{
            const newsData = data.news_articles || {{ total: 0, articles: [] }};
            const articles = newsData.articles || [];
            
            // Grouper par semaine
            const groupByWeek = () => {{
                const weeks = {{}};
                const sorted = [...articles].sort((a,b) => new Date(b.published_at) - new Date(a.published_at));
                sorted.forEach(art => {{
                    const d = new Date(art.published_at);
                    const weekStart = new Date(d);
                    weekStart.setDate(d.getDate() - d.getDay());
                    const key = weekStart.toIs oString().split('T')[0];
                    if (!weeks[key]) weeks[key] = {{ articles: [], startDate: weekStart, avg: 0 }};
                    weeks[key].articles.push(art);
                }});
                Object.values(weeks).forEach(w => {{
                    w.avg = w.articles.reduce((s,a) => s + (a.sentiment?.compound||0), 0) / w.articles.length;
                }});
                return Object.entries(weeks).sort((a,b) => b[1].startDate - a[1].startDate).map(([_,v]) => v);
            }};
            
            const weeks = groupByWeek();
            const avgSent = articles.length > 0 ? articles.reduce((s,a) => s+(a.sentiment?.compound||0),0)/articles.length : 0;
            const posCount = articles.filter(a => (a.sentiment?.compound||0) > 0.3).length;
            const negCount = articles.filter(a => (a.sentiment?.compound||0) < -0.3).length;
            const neuCount = articles.length - posCount - negCount;
            
            const getColor = (s) => s > 0.3 ? 'emerald' : s < -0.3 ? 'rose' : 'amber';
            const getBadge = (s) => {{
                if (s > 0.3) return {{ l: 'POSITIF', c: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50' }};
                if (s < -0.3) return {{ l: 'NÉGATIF', c: 'bg-rose-500/20 text-rose-300 border-rose-500/50' }};
                return {{ l: 'NEUTRE', c: 'bg-amber-500/20 text-amber-300 border-amber-500/50' }};
            }};

            return (
                <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-purple-950 p-6">
                    <div className="max-w-7xl mx-auto space-y-6">
                        <Breadcrumb 
                            path={{{{[
                                {{{{ label: 'Grille', view: 'grid' }}}},
                                {{{{ label: ticker, view: 'detail', ticker }}}},
                                {{{{ label: 'Nouvelles', view: 'news' }}}}
                            ]}}}}
                            onNavigate={{{{(v) => {{{{ if (v === 'grid') onBack('grid'); if (v === 'detail') onBack('detail'); }}}} }}}}
                        />

                        {{/* Header Premium */}}
                        <div className="relative overflow-hidden bg-gradient-to-r from-purple-900/40 via-fuchsia-800/30 to-pink-900/40 backdrop-blur-xl border border-purple-500/30 rounded-2xl p-8 shadow-2xl">
                            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTSA0MCAwIEwgMCAwIDAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9zdmc+')] opacity-30"></div>
                            <div className="relative">
                                <h1 className="text-5xl font-bold text-white mb-3 flex items-center gap-3">
                                    <span className="text-6xl">\U0001F4F0</span>
                                    <span className="bg-gradient-to-r from-purple-200 via-fuchsia-200 to-pink-200 bg-clip-text text-transparent">Timeline Nouvelles</span>
                                </h1>
                                <div className="flex items-center gap-4 text-purple-200/80 flex-wrap">
                                    <span className="font-semibold text-2xl">{{{{ticker}}}}</span>
                                    <span className="text-purple-300/60">•</span>
                                    <span>30 derniers jours</span>
                                    <span className="text-purple-300/60">•</span>
                                    <span className="font-medium">{{{{articles.length}}}} articles</span>
                                </div>
                            </div>
                        </div>

                        {{/* Stats Cards */}}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className={{{{`rounded-xl p-6 border backdrop-blur-sm bg-${{{{getColor(avgSent)}}}}-500/10 border-${{{{getColor(avgSent)}}}}-500/30`}}}}>
                                <div className="text-slate-400 text-sm mb-2 font-medium">Sentiment Moyen</div>
                                <div className={{{{`text-4xl font-bold text-${{{{getColor(avgSent)}}}}-400`}}}}>
                                    {{{{avgSent > 0 ? '+' : ''}}}}{{{{avgSent.toFixed(3)}}}}
                                </div>
                                <div className="text-xs text-slate-500 mt-2">{{{{getBadge(avgSent).l}}}}</div>
                            </div>
                            
                            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-2">\U0001F7E2 Positifs</div>
                                <div className="text-4xl font-bold text-emerald-400">{{{{posCount}}}}</div>
                                <div className="text-xs text-slate-500 mt-2">{{{{((posCount/articles.length)*100).toFixed(0)}}}}%</div>
                            </div>
                            
                            <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-2">\U0001F534 Négatifs</div>
                                <div className="text-4xl font-bold text-rose-400">{{{{negCount}}}}</div>
                                <div className="text-xs text-slate-500 mt-2">{{{{((negCount/articles.length)*100).toFixed(0)}}}}%</div>
                            </div>
                            
                            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-2">\U0001F7E1 Neutres</div>
                                <div className="text-4xl font-bold text-amber-400">{{{{neuCount}}}}</div>
                                <div className="text-xs text-slate-500 mt-2">{{{{((neuCount/articles.length)*100).toFixed(0)}}}}%</div>
                            </div>
                        </div>

                        {{/* Articles Groupés par Semaine */}}
                        <div className="bg-slate-900/70 border border-purple-500/20 rounded-2xl p-8">
                            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                                <span className="text-3xl">\U0001F4DD</span>
                                <span>Articles par Semaine</span>
                            </h2>
                            
                            {{{{weeks.length > 0 ? (
                                <div className="space-y-6">
                                    {{{{weeks.slice(0, 5).map((week, idx) => {{{{
                                        const endDate = new Date(week.startDate);
                                        endDate.setDate(endDate.getDate() + 6);
                                        const badge = getBadge(week.avg);
                                        const color = getColor(week.avg);
                                        
                                        return (
                                            <div key={{{{idx}}}} className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
                                                <div className={{{{`px-6 py-4 border-b border-slate-700/50 bg-${{{{color}}}}-500/10 border-${{{{color}}}}-500/30`}}}}>
                                                    <div className="flex items-center justify-between flex-wrap gap-4">
                                                        <div>
                                                            <div className="text-white font-semibold text-lg">
                                                                {{{{week.startDate.toLocaleDateString('fr-FR', {{{{ month: 'long', day: 'numeric' }}}})}}}} - {{{{endDate.toLocaleDateString('fr-FR', {{{{ month: 'long', day: 'numeric', year: 'numeric' }}}} )}}}}
                                                            </div>
                                                            <div className="text-slate-400 text-sm mt-1">{{{{week.articles.length}}}} articles</div>
                                                        </div>
                                                        <div className={{{{`px-4 py-2 rounded-full border font-bold ${{{{badge.c}}}}`}}}}>
                                                            {{{{badge.l}}}} {{{{week.avg.toFixed(2)}}}}
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <div className="p-4 space-y-3">
                                                    {{{{week.articles.slice(0, 8).map((art, i) => {{{{
                                                        const sent = art.sentiment?.compound || 0;
                                                        const artBadge = getBadge(sent);
                                                        const artColor = getColor(sent);
                                                        
                                                        return (
                                                            <div key={{{{i}}}} className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/50 hover:border-purple-400/50 transition-all">
                                                                <div className="flex items-start justify-between gap-4 flex-wrap">
                                                                    <div className="flex-1 min-w-0">
                                                                        <h3 className="text-white font-medium mb-2 leading-snug">{{{{art.title}}}}</h3>
                                                                        <div className="flex items-center gap-3 text-xs text-slate-400 flex-wrap">
                                                                            <span>\U0001F4C5 {{{{new Date(art.published_at).toLocaleDateString('fr-FR', {{{{ day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }}}})}} }}</span>
                                                                            {{{{art.url && (
                                                                                <a href={{{{art.url}}}} target="_blank" rel="noopener" className="text-cyan-400 hover:text-cyan-300">
                                                                                    Lire →
                                                                                </a>
                                                                            )}}}}
                                                                        </div>
                                                                    </div>
                                                                    <div className={{{{`px-3 py-1 rounded-lg border text-xs font-bold whitespace-nowrap ${{{{artBadge.c}}}}`}}}}>
                                                                        {{{{sent > 0 ? '+' : ''}}}}{{{{sent.toFixed(2)}}}}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        );
                                                    }}}}}}}}
                                                    {{{{week.articles.length > 8 && (
                                                        <div className="text-center text-slate-500 text-sm pt-2">
                                                            + {{{{week.articles.length - 8}}}} autres articles
                                                        </div>
                                                    )}}}}
                                                </div>
                                            </div>
                                        );
                                    }}}}}}}}
                                </div>
                            ) : (
                                <div className="text-center text-slate-400 py-16">
                                    <div className="text-7xl mb-4">\U0001F4F0</div>
                                    <div className="text-xl">Aucun article sur les 30 derniers jours</div>
                                </div>
                            )}}}}
                        </div>
                    </div>
                </div>
            );
        }};

        // NIVEAU 2: Détail Ticker (Vue complète riche) = ({{ ticker, data, onBack }}) => {{
            const newsData = data.news_articles || {{ total: 0, articles: [] }};
            const articles = newsData.articles || [];
            
            // Préparer les données pour le graphique 30 jours
            const prepareChartData = () => {{
                const now = new Date();
                const thirtyDaysAgo = new Date(now);
                thirtyDaysAgo.setDate(now.getDate() - 30);
                
                // Créer des buckets journaliers
                const dailyData = {{}};
                for (let d = new Date(thirtyDaysAgo); d <= now; d.setDate(d.getDate() + 1)) {{
                    const key = d.toISOString().split('T')[0];
                    dailyData[key] = {{ sentiments: [], count: 0 }};
                }}
                
                // Remplir avec les articles
                articles.forEach(art => {{
                    const date = new Date(art.published_at);
                    const key = date.toISOString().split('T')[0];
                    if (dailyData[key]) {{
                        dailyData[key].sentiments.push(art.sentiment?.compound || 0);
                        dailyData[key].count++;
                    }}
                }});
                
                // Calculer les moyennes journalières et créer la moving average
                const points = Object.entries(dailyData).map(([date, data]) => {{
                    const avg = data.sentiments.length > 0 
                        ? data.sentiments.reduce((a,b) => a+b, 0) / data.sentiments.length 
                        : null;
                    return {{ date, avg, count: data.count }};
                }});
                
                return points;
            }};
            
            const chartData = prepareChartData();
            
            // Grouper articles par semaine
            const groupArticlesByWeek = () => {{
                const weeks = {{}};
                const sortedArticles = [...articles].sort((a,b) => 
                    new Date(b.published_at) - new Date(a.published_at)
                );
                
                sortedArticles.forEach(art => {{
                    const date = new Date(art.published_at);
                    // Calculer la semaine (ISO week)
                    const startOfYear = new Date(date.getFullYear(), 0, 1);
                    const weekNum = Math.ceil((((date - startOfYear) / 86400000) + startOfYear.getDay() + 1) / 7);
                    const weekKey = `${date.getFullYear()}-W${weekNum}`;
                    
                    if (!weeks[weekKey]) {{
                        weeks[weekKey] = {{ 
                            articles: [], 
                            startDate: new Date(date),
                            avgSentiment: 0
                        }};
                    }}
                    weeks[weekKey].articles.push(art);
                }});
                
                // Calculer sentiment moyen par semaine
                Object.values(weeks).forEach(week => {{
                    week.avgSentiment = week.articles.reduce((sum, art) => 
                        sum + (art.sentiment?.compound || 0), 0) / week.articles.length;
                }});
                
                return Object.entries(weeks).sort((a,b) => 
                    b[1].startDate - a[1].startDate
                ).map(([key, data]) => data);
            }};
            
            const weeklyGroups = groupArticlesByWeek();
            
            // Stats globales
            const avgSentiment = articles.length > 0 
                ? articles.reduce((sum, art) => sum + (art.sentiment?.compound || 0), 0) / articles.length 
                : 0;
            
            const positiveCount = articles.filter(a => (a.sentiment?.compound || 0) > 0.3).length;
            const negativeCount = articles.filter(a => (a.sentiment?.compound || 0) < -0.3).length;
            const neutralCount = articles.length - positiveCount - negativeCount;
            
            const getSentimentColor = (score) => {{
                if (score > 0.3) return 'text-emerald-400';
                if (score < -0.3) return 'text-rose-400';
                return 'text-amber-400';
            }};
            
            const getSentimentBg = (score) => {{
                if (score > 0.3) return 'bg-emerald-500/10 border-emerald-500/30';
                if (score < -0.3) return 'bg-rose-500/10 border-rose-500/30';
                return 'bg-amber-500/10 border-amber-500/30';
            }};
            
            const getSentimentBadge = (score) => {{
                if (score > 0.3) return {{ label: 'POSITIF', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50' }};
                if (score < -0.3) return {{ label: 'NÉGATIF', color: 'bg-rose-500/20 text-rose-300 border-rose-500/50' }};
                return {{ label: 'NEUTRE', color: 'bg-amber-500/20 text-amber-300 border-amber-500/50' }};
            }};

            return (
                <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-purple-950 p-6">
                    <div className="max-w-7xl mx-auto space-y-6">
                        <Breadcrumb 
                            path={{[
                                {{ label: 'Grille', view: 'grid' }},
                                {{ label: ticker, view: 'detail', ticker }},
                                {{ label: 'Nouvelles', view: 'news' }}
                            ]}}
                            onNavigate={{(view) => {{
                                if (view === 'grid') onBack('grid');
                                if (view === 'detail') onBack('detail');
                            }}}}
                        />

                        {{/* Premium Header */}}
                        <div className="relative overflow-hidden bg-gradient-to-r from-purple-900/40 via-fuchsia-800/30 to-pink-900/40 backdrop-blur-xl border border-purple-500/30 rounded-2xl p-8 shadow-2xl">
                            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDMpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-30"></div>
                            <div className="relative">
                                <h1 className="text-5xl font-bold text-white mb-3 flex items-center gap-3">
                                    <span className="text-6xl">\U0001F4F0</span>
                                    <span className="bg-gradient-to-r from-purple-200 via-fuchsia-200 to-pink-200 bg-clip-text text-transparent">Timeline Nouvelles</span>
                                </h1>
                                <div className="flex items-center gap-4 text-purple-200/80">
                                    <span className="font-semibold text-2xl">{ticker}</span>
                                    <span className="text-purple-300/60">•</span>
                                    <span>Analyse temporelle sur 30 jours</span>
                                    <span className="text-purple-300/60">•</span>
                                    <span className="font-medium">{newsData.total} articles</span>
                                </div>
                            </div>
                        </div>

                        {{/* Premium Stats Grid */}}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className={{`relative overflow-hidden rounded-xl p-6 border ${{getSentimentBg(avgSentiment)}} backdrop-blur-sm`}}>
                                <div className="text-slate-400 text-sm mb-2 font-medium">Sentiment Moyen</div>
                                <div className={{`text-4xl font-bold ${{getSentimentColor(avgSentiment)}}`}}>
                                    {{avgSentiment > 0 ? '+' : ''}}{{avgSentiment.toFixed(3)}}
                                </div>
                                <div className="text-xs text-slate-500 mt-2">{{getSentimentBadge(avgSentiment).label}}</div>
                            </div>
                            
                            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6 backdrop-blur-sm">
                                <div className="text-slate-400 text-sm mb-2 font-medium">\U0001F7E2 Positifs</div>
                                <div className="text-4xl font-bold text-emerald-400">{{positiveCount}}</div>
                                <div className="text-xs text-slate-500 mt-2">{{((positiveCount/articles.length)*100).toFixed(0)}}% du total</div>
                            </div>
                            
                            <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-6 backdrop-blur-sm">
                                <div className="text-slate-400 text-sm mb-2 font-medium">\U0001F534 Négatifs</div>
                                <div className="text-4xl font-bold text-rose-400">{{negativeCount}}</div>
                                <div className="text-xs text-slate-500 mt-2">{{((negativeCount/articles.length)*100).toFixed(0)}}% du total</div>
                            </div>
                            
                            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-6 backdrop-blur-sm">
                                <div className="text-slate-400 text-sm mb-2 font-medium">\U0001F7E1 Neutres</div>
                                <div className="text-4xl font-bold text-amber-400">{{neutralCount}}</div>
                                <div className="text-xs text-slate-500 mt-2">{{((neutralCount/articles.length)*100).toFixed(0)}}% du total</div>
                            </div>
                        </div>

                        {{/* Premium SVG Timeline Chart */}}
                        <div className="bg-slate-900/70 border border-purple-500/20 rounded-2xl p-8 backdrop-blur-sm shadow-2xl">
                            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                                <span className="text-3xl">\U0001F4C8</span>
                                <span>Évolution Temporelle - 30 Jours</span>
                            </h2>
                            
                            {{chartData.length > 0 ? (
                                <div className="relative h-80 bg-slate-950/50 rounded-xl p-6 border border-slate-700/50">
                                    <svg viewBox="0 0 1000 300" className="w-full h-full">
                                        {{/* Grid lines */}}
                                        <defs>
                                            <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                                <stop offset="0%" stopColor="#a78bfa" />
                                                <stop offset="50%" stopColor="#f472b6" />
                                                <stop offset="100%" stopColor="#fb7185" />
                                            </linearGradient>
                                            <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                                <stop offset="0%" stopColor="#a78bfa" stopOpacity="0.3" />
                                                <stop offset="100%" stopColor="#a78bfa" stopOpacity="0" />
                                            </linearGradient>
                                        </defs>
                                        
                                        {{/* Horizontal grid */}}
                                        {{[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {{
                                            const y = 250 - (ratio * 200);
                                            const value = (-1 + ratio * 2).toFixed(1);
                                            return (
                                                <g key={{i}}>
                                                    <line x1="50" y1={{y}} x2="980" y2={{y}} stroke="rgba(148,163,184,0.1)" strokeWidth="1" />
                                                    <text x="25" y={{y+5}} fill="#94a3b8" fontSize="12" textAnchor="end">{{value}}</text>
                                                </g>
                                            );
                                        }})}}
                                        
                                        {{/* Zero line */}}
                                        <line x1="50" y1="150" x2="980" y2="150" stroke="rgba(148, 163, 184, 0.4)" strokeWidth="2" strokeDasharray="5,5" />
                                        
                                        {{/* Data line with gradient */}}
                                        {{(() => {{
                                            const validPoints = chartData.filter(p => p.avg !== null);
                                            if (validPoints.length === 0) return null;
                                            
                                            const xStep = 930 / (chartData.length - 1);
                                            const pointsStr = validPoints.map((point, i) => {{
                                                const actualIndex = chartData.findIndex(p => p === point);
                                                const x = 50 + actualIndex * xStep;
                                                const y = 150 - (point.avg * 100); // Map -1 to 1 => 100px range centered on 150
                                                return `${{x}},${{y}}`;
                                            }}).join(' ');
                                            
                                            // Area path
                                            const firstPoint = validPoints[0];
                                            const lastPoint = validPoints[validPoints.length - 1];
                                            const firstIndex = chartData.findIndex(p => p === firstPoint);
                                            const lastIndex = chartData.findIndex(p => p === lastPoint);
                                            const areaPath = `M ${{50 + firstIndex * xStep}},250 L ` + pointsStr + ` L ${{50 + lastIndex * xStep}},250 Z`;
                                            
                                            return (
                                                <>
                                                    <path d={{areaPath}} fill="url(#areaGradient)" />
                                                    <polyline 
                                                        points={{pointsStr}} 
                                                        fill="none" 
                                                        stroke="url(#lineGradient)" 
                                                        strokeWidth="3" 
                                                        strokeLinejoin="round"
                                                        strokeLinecap="round"
                                                    />
                                                    {{validPoints.map((point, i) => {{
                                                        const actualIndex = chartData.findIndex(p => p === point);
                                                        const x = 50 + actualIndex * xStep;
                                                        const y = 150 - (point.avg * 100);
                                                        const color = point.avg > 0.3 ? '#10b981' : point.avg < -0.3 ? '#f43f5e' : '#fbbf24';
                                                        return <circle key={{i}} cx={{x}} cy={{y}} r="4" fill={{color}} stroke="white" strokeWidth="2" />;
                                                    }}}}
                                                </>
                                            );
                                        }})()}}
                                        
                                        {{/* X-axis dates (every 5 days) */}}
                                        {{chartData.filter((_, i) => i % 5 === 0).map((point, i) => {{
                                            const actualIndex = chartData.findIndex((p, idx) => idx % 5 === 0 && p === point);
                                            const x = 50 + actualIndex * (930 / (chartData.length - 1));
                                            const date = new Date(point.date);
                                            return (
                                                <text 
                                                    key={{i}} 
                                                    x={{x}} 
                                                    y="280" 
                                                    fill="#94a3b8" 
                                                    fontSize="11" 
                                                    textAnchor="middle"
                                                >
                                                    {{date.getDate()}}/{{date.getMonth()+1}}
                                                </text>
                                            );
                                        }})}}
                                    </svg>
                                    
                                    {{/* Legend */}}
                                    <div className="flex justify-center gap-6 mt-4 text-sm">
                                        <div className="flex items-center gap-2">
                                            <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                                            <span className="text-slate-400">Positif (+0.3)</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                                            <span className="text-slate-400">Neutre</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <div className="w-3 h-3 rounded-full bg-rose-500"></div>
                                            <span className="text-slate-400">Négatif (-0.3)</span>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center text-slate-400 py-16">Aucune donnée disponible</div>
                            )}}
                        </div>

                        {{/* Weekly Grouped Articles */}}
                        <div className="bg-slate-900/70 border border-purple-500/20 rounded-2xl p-8 backdrop-blur-sm">
                            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                                <span className="text-3xl">\U0001F4DD</span>
                                <span>Articles par Semaine</span>
                            </h2>
                            
                            {{weeklyGroups.length > 0 ? (
                                <div className="space-y-6">
                                    {{weeklyGroups.map((week, weekIdx) => {{
                                        const startDate = week.startDate;
                                        const endDate = new Date(startDate);
                                        endDate.setDate(endDate.getDate() + 6);
                                        const badge = getSentimentBadge(week.avgSentiment);
                                        
                                        return (
                                            <div key={{weekIdx}} className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
                                                {{/* Week Header */}}
                                                <div className={{`px-6 py-4 border-b border-slate-700/50 ${{getSentimentBg(week.avgSentiment)}}`}}>
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <div className="text-white font-semibold text-lg">
                                                                {{startDate.toLocaleDateString('fr-FR', {{ day: 'numeric', month: 'long' }})}} - {{endDate.toLocaleDateString('fr-FR', {{ day: 'numeric', month: 'long', year: 'numeric' }})}}
                                                            </div>
                                                            <div className="text-slate-400 text-sm mt-1">{{week.articles.length}} articles</div>
                                                        </div>
                                                        <div className={{`px-4 py-2 rounded-full border font-bold ${{badge.color}}`}}>
                                                            {{badge.label}} {{week.avgSentiment.toFixed(2)}}
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                {{/* Articles */}}
                                                <div className="p-4 space-y-3">
                                                    {{week.articles.slice(0, 10).map((article, artIdx) => {{
                                                        const sentiment = article.sentiment?.compound || 0;
                                                        const artBadge = getSentimentBadge(sentiment);
                                                        
                                                        return (
                                                            <div key={{artIdx}} className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/50 hover:border-purple-400/50 transition-all group">
                                                                <div className="flex items-start justify-between gap-4">
                                                                    <div className="flex-1">
                                                                        <h3 className="text-white font-medium mb-2 leading-snug group-hover:text-purple-200 transition-colors">
                                                                            {{article.title}}
                                                                        </h3>
                                                                        <div className="flex items-center gap-3 text-xs text-slate-400 mb-2">
                                                                            <span>\U0001F4C5 {{new Date(article.published_at).toLocaleDateString('fr-FR', {{ day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }})}}</span>
                                                                            {{article.sentiment && (
                                                                                <>
                                                                                    <span className="text-slate-600">•</span>
                                                                                    <span className="text-emerald-400">\U0001F7E2 {{(article.sentiment.positive * 100).toFixed(0)}}%</span>
                                                                                    <span className="text-rose-400">\U0001F534 {{(article.sentiment.negative * 100).toFixed(0)}}%</span>
                                                                                </>
                                                                            )}}
                                                                        </div>
                                                                        {{article.url && (
                                                                            <a 
                                                                                href={{article.url}} 
                                                                                target="_blank" 
                                                                                rel="noopener noreferrer"
                                                                                className="text-cyan-400 hover:text-cyan-300 text-xs flex items-center gap-1 transition-colors"
                                                                            >
                                                                                Lire l'article →
                                                                            </a>
                                                                        )}}
                                                                    </div>
                                                                    <div className={{`px-3 py-1 rounded-lg border text-xs font-bold whitespace-nowrap ${{artBadge.color}}`}}>
                                                                        {{sentiment > 0 ? '+' : ''}}{{sentiment.toFixed(2)}}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        );
                                                    }})}}
                                                    {{week.articles.length > 10 && (
                                                        <div className="text-center text-slate-500 text-sm pt-2">
                                                            + {{week.articles.length - 10}} articles supplémentaires
                                                        </div>
                                                    )}}
                                                </div>
                                            </div>
                                        );
                                    }})}}
                                </div>
                            ) : (
                                <div className="text-center text-slate-400 py-16">
                                    <div className="text-7xl mb-4">\U0001F4F0</div>
                                    <div className="text-xl">Aucun article disponible sur les 30 derniers jours</div>
                                </div>
                            )}}
                        </div>
                    </div>
                </div>
            );
        }};

        // NIVEAU 2: Détail Ticker (Vue complète riche)
        const DetailView = ({{ ticker, data, onBack, onDeepDive }}) => {{
            const getSentimentColor = (score) => {{
                if (score > 0.5) return 'text-green-500';
                if (score > 0.2) return 'text-green-400';
                if (score < -0.5) return 'text-red-500';
                if (score < -0.2) return 'text-red-400';
                return 'text-yellow-500';
            }};

            const getSentimentBg = (score) => {{
                if (score > 0.5) return 'bg-green-500';
                if (score > 0.2) return 'bg-green-400';
                if (score < -0.5) return 'bg-red-500';
                if (score < -0.2) return 'bg-red-400';
                return 'bg-yellow-500';
            }};

            const gaugePosition = ((data.final_sentiment_score + 1) / 2) * 100;

            return (
                <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
                    <div className="max-w-7xl mx-auto space-y-6">
                        <Breadcrumb 
                            path={{[
                                {{ label: 'Grille', view: 'grid' }},
                                {{ label: ticker, view: 'detail', ticker }}
                            ]}}
                            onNavigate={{(view) => view === 'grid' && onBack()}}
                        />

                        {{/* Header */}}
                        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h1 className="text-5xl font-bold text-white mb-2">{{ticker}}</h1>
                                    <p className="text-slate-400">
                                        {{new Date(data.timestamp).toLocaleString('fr-FR')}} • V4 Dual Brain
                                    </p>
                                </div>
                                <div className="text-right">
                                    <div className={{`text-6xl font-bold ${{getSentimentColor(data.final_sentiment_score)}}`}}>
                                        {{data.final_sentiment_score > 0 ? '+' : ''}}{{(data.final_sentiment_score * 100).toFixed(2)}}
                                    </div>
                                    <div className="text-slate-400 text-sm mt-1">Score Final</div>
                                    
                                    {{/* BOUTON DEEP DIVE INTEGRE */}}
                                    <button
                                        onClick={{() => onDeepDive('options')}}
                                        className="mt-4 bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded-lg font-semibold transition-colors flex items-center gap-2 ml-auto"
                                    >
                                        \U0001F4CA Options Deep Dive
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={{2}} d="M9 5l7 7-7 7" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>

                        {{/* Classification & Metrics */}}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-2">Classification</div>
                                <div className={{`text-3xl font-bold ${{getSentimentColor(data.final_sentiment_score)}}`}}>
                                    {{data.classification}}
                                </div>
                            </div>
                            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-2">Conviction</div>
                                <div className="text-3xl font-bold text-white">
                                    {{(data.conviction_score * 100).toFixed(1)}}%
                                </div>
                                <div className="w-full bg-slate-700 rounded-full h-2 mt-3">
                                    <div 
                                        className="bg-gradient-to-r from-yellow-500 to-orange-500 h-2 rounded-full"
                                        style={{{{ width: `${{data.conviction_score * 100}}%` }}}}
                                    />
                                </div>
                            </div>
                            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-2">Confiance</div>
                                <div className="text-3xl font-bold text-white">
                                    {{data.confidence_level}}
                                </div>
                            </div>
                        </div>

                        {{/* Gauge */}}
                        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8">
                            <h2 className="text-xl font-semibold text-white mb-6">Sentiment Global</h2>
                            <div className="relative">
                                <div className="flex justify-between text-xs text-slate-400 mb-2">
                                    <span>Bearish Fort</span>
                                    <span>Neutre</span>
                                    <span>Bullish Fort</span>
                                </div>
                                <div className="relative h-12 rounded-xl overflow-hidden bg-gradient-to-r from-red-600 via-yellow-500 to-green-600">
                                    <div 
                                        className="absolute top-0 bottom-0 w-1 bg-white shadow-lg"
                                        style={{{{ left: `${{gaugePosition}}%` }}}}
                                    >
                                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-white text-slate-900 px-3 py-1 rounded-lg text-sm font-bold whitespace-nowrap shadow-lg">
                                            {{data.final_sentiment_score > 0 ? '+' : ''}}{{data.final_sentiment_score.toFixed(4)}}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex justify-between text-xs text-slate-500 mt-2">
                                    <span>-1.00</span>
                                    <span>-0.50</span>
                                    <span>0.00</span>
                                    <span>+0.50</span>
                                    <span>+1.00</span>
                                </div>
                            </div>
                        </div>

                        {{/* Components */}}
                        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8">
                            <h2 className="text-xl font-semibold text-white mb-6">6 Dimensions de Sentiment</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {{/* News */}}
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-white font-medium">\U0001F4F0 Sentiment Nouvelles</span>
                                        <span className={{`font-bold ${{getSentimentColor(data.components.news_sentiment)}}`}}>
                                            {{data.components.news_sentiment > 0 ? '+' : ''}}{{data.components.news_sentiment.toFixed(4)}}
                                        </span>
                                    </div>
                                    <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                                        <div 
                                            className={{`${{getSentimentBg(data.components.news_sentiment)}} h-3`}}
                                            style={{{{ 
                                                width: `${{Math.abs(data.components.news_sentiment) * 100}}%`,
                                                marginLeft: data.components.news_sentiment < 0 ? `${{100 - Math.abs(data.components.news_sentiment) * 100}}%` : '0'
                                            }}}}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs text-slate-400">
                                        <span>Confiance: {{(data.components.news_confidence * 100).toFixed(1)}}%</span>
                                        <span>Poids: {{(data.components.news_weight * 100).toFixed(1)}}%</span>
                                    </div>
                                </div>

                                {{/* Options */}}
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-white font-medium">\U0001F4CA Sentiment Options</span>
                                        <span className={{`font-bold ${{getSentimentColor(data.components.options_sentiment)}}`}}>
                                            {{data.components.options_sentiment > 0 ? '+' : ''}}{{data.components.options_sentiment.toFixed(4)}}
                                        </span>
                                    </div>
                                    <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                                        <div 
                                            className={{`${{getSentimentBg(data.components.options_sentiment)}} h-3`}}
                                            style={{{{ 
                                                width: `${{Math.abs(data.components.options_sentiment) * 100}}%`,
                                                marginLeft: data.components.options_sentiment < 0 ? `${{100 - Math.abs(data.components.options_sentiment) * 100}}%` : '0'
                                            }}}}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs text-slate-400">
                                        <span>Confiance: {{(data.components.options_confidence * 100).toFixed(1)}}%</span>
                                        <span>Poids: {{(data.components.options_weight * 100).toFixed(1)}}%</span>
                                    </div>
                                </div>

                                {{/* Analysts */}}
                                <div className="space-y-3 bg-purple-900/20 p-4 rounded-lg border border-purple-600/30">
                                    <div className="flex justify-between items-center">
                                        <span className="text-white font-medium">\U0001F465 Sentiment Analystes</span>
                                        <span className={{`font-bold ${{getSentimentColor(data.components.analyst_sentiment)}}`}}>
                                            {{data.components.analyst_sentiment > 0 ? '+' : ''}}{{data.components.analyst_sentiment.toFixed(4)}}
                                        </span>
                                    </div>
                                    <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                                        <div 
                                            className="bg-gradient-to-r from-purple-500 to-blue-500 h-3"
                                            style={{{{ 
                                                width: `${{Math.abs(data.components.analyst_sentiment) * 100}}%`,
                                                marginLeft: data.components.analyst_sentiment < 0 ? `${{100 - Math.abs(data.components.analyst_sentiment) * 100}}%` : '0'
                                            }}}}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs text-slate-400">
                                        <span>Confiance: {{(data.components.analyst_confidence * 100).toFixed(1)}}%</span>
                                        <span>Poids: {{(data.components.analyst_weight * 100).toFixed(1)}}%</span>
                                    </div>
                                </div>

                                {{/* Momentum */}}
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-white font-medium">\U0001F680 Momentum Narratif</span>
                                        <span className={{`font-bold ${{getSentimentColor(data.components.narrative_momentum)}}`}}>
                                            {{data.components.narrative_momentum > 0 ? '+' : ''}}{{data.components.narrative_momentum.toFixed(4)}}
                                        </span>
                                    </div>
                                    <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                                        <div 
                                            className={{`${{getSentimentBg(data.components.narrative_momentum)}} h-3`}}
                                            style={{{{ 
                                                width: `${{Math.abs(data.components.narrative_momentum) * 100}}%`,
                                                marginLeft: data.components.narrative_momentum < 0 ? `${{100 - Math.abs(data.components.narrative_momentum) * 100}}%` : '0'
                                            }}}}
                                        />
                                    </div>
                                </div>
                            </div>

                            {{/* Weight Distribution */}}
                            <div className="mt-8 pt-6 border-t border-slate-700">
                                <h3 className="text-sm font-semibold text-slate-300 mb-4">Pondération des Sources</h3>
                                <div className="flex gap-2 h-8">
                                    <div 
                                        className="bg-blue-500 rounded flex items-center justify-center text-white text-xs font-semibold"
                                        style={{{{ width: `${{data.components.news_weight * 100}}%` }}}}
                                    >
                                        News {{(data.components.news_weight * 100).toFixed(0)}}%
                                    </div>
                                    <div 
                                        className="bg-cyan-500 rounded flex items-center justify-center text-white text-xs font-semibold"
                                        style={{{{ width: `${{data.components.options_weight * 100}}%` }}}}
                                    >
                                        Options {{(data.components.options_weight * 100).toFixed(0)}}%
                                    </div>
                                    <div 
                                        className="bg-purple-500 rounded flex items-center justify-center text-white text-xs font-semibold"
                                        style={{{{ width: `${{data.components.analyst_weight * 100}}%` }}}}
                                    >
                                        Analysts {{(data.components.analyst_weight * 100).toFixed(0)}}%
                                    </div>
                                </div>
                            </div>
                        </div>

                        {{/* Analyst Insights */}}
                        {{data.analyst_insights && (
                            <div className="bg-gradient-to-br from-purple-900/30 to-blue-900/30 backdrop-blur-sm border border-purple-700/50 rounded-2xl p-8">
                                <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                                    \U0001F465 Analyst Insights - Consensus Professionnel
                                    <span className="ml-auto text-sm bg-purple-600 px-3 py-1 rounded-full">
                                        {{data.analyst_insights.recommendation_count}} analystes
                                    </span>
                                </h2>
                                
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {{/* Recommendation */}}
                                    <div className="bg-slate-800/50 rounded-xl p-5 border border-purple-600/30">
                                        <div className="text-slate-300 text-sm mb-2">Recommandation</div>
                                        <div className="text-2xl font-bold text-white mb-2">
                                            {{data.analyst_insights.recommendation_summary}}
                                        </div>
                                        <div className="text-sm text-slate-400">
                                            Moyenne: {{data.analyst_insights.recommendation_mean?.toFixed(2) || 'N/A'}}/5.0
                                        </div>
                                    </div>

                                    {{/* Price Target */}}
                                    <div className="bg-slate-800/50 rounded-xl p-5 border border-blue-600/30">
                                        <div className="text-slate-300 text-sm mb-2">Price Target</div>
                                        <div className="text-2xl font-bold text-white mb-2">
                                            {{data.analyst_insights.target_mean ? `$${{data.analyst_insights.target_mean.toFixed(2)}}` : 'N/A'}}
                                        </div>
                                        <div className="text-sm text-slate-400">
                                            Prix actuel: {{data.analyst_insights.current_price ? `$${{data.analyst_insights.current_price.toFixed(2)}}` : 'N/A'}}
                                        </div>
                                        {{data.analyst_insights.upside_potential != null && (
                                            <div className={{`text-lg font-bold mt-2 ${{data.analyst_insights.upside_potential > 0 ? 'text-green-400' : 'text-red-400'}}`}}>
                                                {{data.analyst_insights.upside_potential > 0 ? '+' : ''}}{{(data.analyst_insights.upside_potential * 100).toFixed(1)}}%
                                            </div>
                                        )}}
                                    </div>

                                    {{/* Revisions */}}
                                    <div className="bg-slate-800/50 rounded-xl p-5 border border-cyan-600/30">
                                        <div className="text-slate-300 text-sm mb-2">Révisions 30j</div>
                                        <div className="flex gap-4 mb-2">
                                            <div>
                                                <div className="text-xl font-bold text-green-400">
                                                    ↑ {{data.analyst_insights.upgrades_30d || 0}}
                                                </div>
                                                <div className="text-xs text-slate-400">Upgrades</div>
                                            </div>
                                            <div>
                                                <div className="text-xl font-bold text-red-400">
                                                    ↓ {{data.analyst_insights.downgrades_30d || 0}}
                                                </div>
                                                <div className="text-xs text-slate-400">Downgrades</div>
                                            </div>
                                        </div>
                                        <div className={{`text-lg font-bold ${{(data.analyst_insights.net_changes_30d || 0) > 0 ? 'text-green-400' : 'text-red-400'}}`}}>
                                            Net: {{(data.analyst_insights.net_changes_30d || 0) > 0 ? '+' : ''}}{{data.analyst_insights.net_changes_30d || 0}}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}}

                        {{/* Volatility Regime */}}
                        {{data.volatility_regime && (
                            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8">
                                <h2 className="text-xl font-semibold text-white mb-6">\U0001F32A\uFE0F Régime de Volatilité</h2>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <div className="text-slate-400 text-sm mb-2">Régime Actuel</div>
                                        <div className="text-3xl font-bold text-orange-400 mb-4">
                                            {{data.volatility_regime.regime}} - {{data.volatility_regime.sub_regime}}
                                        </div>
                                        <div className="text-slate-300">
                                            {{data.volatility_regime.implications}}
                                        </div>
                                    </div>
                                    <div className="bg-slate-700/50 rounded-xl p-6">
                                        <div className="text-slate-400 text-sm mb-3">Recommandation</div>
                                        <div className="text-white">
                                            {{data.volatility_regime.recommendation}}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}}

                        {{/* Catalysts */}}
                        {{data.catalysts && data.catalysts.catalysts_detected && data.catalysts.catalysts_detected.length > 0 && (
                            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8">
                                <h2 className="text-xl font-semibold text-white mb-6">
                                    \U0001F3AF Catalyseurs Détectés ({{data.catalysts.count}})
                                </h2>
                                <div className="space-y-4">
                                    {{data.catalysts.catalysts_detected.slice(0, 5).map((catalyst, idx) => (
                                        <div key={{idx}} className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                                            <div className="flex items-start justify-between mb-2">
                                                <div className="flex-1">
                                                    <div className="text-white font-medium mb-1">{{catalyst.title}}</div>
                                                    <div className="flex gap-3 text-xs text-slate-400">
                                                        <span>Type: {{catalyst.type}}</span>
                                                        <span>Impact: {{(catalyst.impact_score * 100).toFixed(0)}}%</span>
                                                        <span>Sentiment: {{catalyst.sentiment > 0 ? '+' : ''}}{{catalyst.sentiment.toFixed(2)}}</span>
                                                    </div>
                                                </div>
                                                <div className="text-xs text-slate-500">
                                                    {{new Date(catalyst.timestamp).toLocaleDateString('fr-FR')}}
                                                </div>
                                            </div>
                                        </div>
                                    ))}}
                                </div>
                            </div>
                        )}}

                        {{/* Alerts */}}
                        {{data.alerts && data.alerts.length > 0 && (
                            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8">
                                <h2 className="text-xl font-semibold text-white mb-6">\U0001F6A8 Alertes ({{data.alerts.length}})</h2>
                                <div className="space-y-4">
                                    {{data.alerts.map((alert, idx) => (
                                        <div 
                                            key={{idx}} 
                                            className={{`rounded-lg p-6 border ${{
                                                alert.priority === 'HIGH' ? 'bg-red-900/20 border-red-600/50' :
                                                alert.priority === 'MEDIUM' ? 'bg-yellow-900/20 border-yellow-600/50' :
                                                'bg-blue-900/20 border-blue-600/50'
                                            }}`}}
                                        >
                                            <div className="flex items-start gap-3">
                                                <div className="text-2xl">{{alert.icon}}</div>
                                                <div className="flex-1">
                                                    <div className="text-white font-semibold mb-2">{{alert.title}}</div>
                                                    <div className="text-slate-300 text-sm mb-3">{{alert.message}}</div>
                                                    <div className="text-cyan-400 text-sm">→ {{alert.action}}</div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}}
                                </div>
                            </div>
                        )}}

                        {{/* Metadata */}}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-1">Articles Analysés</div>
                                <div className="text-3xl font-bold text-white">{{data.metadata.news_articles_count}}</div>
                            </div>
                            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-1">Volume Options</div>
                                <div className="text-3xl font-bold text-white">{{data.metadata.options_volume.toLocaleString()}}</div>
                            </div>
                            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
                                <div className="text-slate-400 text-sm mb-1">Version / Profondeur</div>
                                <div className="text-3xl font-bold text-white">
                                    {{data.metadata.version || 'V4'}} / {{data.metadata.analysis_depth}}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }};

        // NIVEAU 1: Grille 
        const GridView = ({{ tickersData, onSelectTicker, onDirectDeepDive }}) => {{
            return (
                <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
                    <div className="max-w-7xl mx-auto">
                        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 mb-6">
                            <h1 className="text-4xl font-bold text-white mb-2">\U0001F9E0 Sentiment V4 - Triple Brain Dashboard</h1>
                            <p className="text-slate-400">{{tickersData.length}} tickers • Choisissez votre analyse</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {{tickersData.map(({{ ticker, data }}) => (
                                <div 
                                    key={{ticker}}
                                    className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 hover:border-cyan-500 transition-all group"
                                >
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="text-3xl font-bold text-white">{{ticker}}</div>
                                        <div className={{`text-4xl font-bold ${{data.final_sentiment_score > 0 ? 'text-green-400' : data.final_sentiment_score < -0.2 ? 'text-red-400' : 'text-yellow-400'}}`}}>
                                            {{data.final_sentiment_score > 0 ? '+' : ''}}{{(data.final_sentiment_score * 100).toFixed(1)}}
                                        </div>
                                    </div>
                                    <div className="text-lg font-bold text-white mb-4">{{data.classification}}</div>
                                    
                                    {{/* Action Buttons */}}
                                    <div className="grid grid-cols-3 gap-2 mt-4">
                                        <button
                                            onClick={{() => onSelectTicker(ticker)}}
                                            className="bg-slate-700 hover:bg-blue-600 text-white py-2 px-1 rounded-lg font-medium transition-colors flex flex-col items-center justify-center gap-1 text-sm"
                                        >
                                            <span className="text-lg">\U0001F9E0</span>
                                            <span>Sentiment</span>
                                        </button>
                                        <button
                                            onClick={{() => onDirectDeepDive(ticker, 'options')}}
                                            className="bg-slate-700 hover:bg-cyan-600 text-white py-2 px-1 rounded-lg font-medium transition-colors flex flex-col items-center justify-center gap-1 text-sm"
                                        >
                                            <span className="text-lg">\U0001F4CA</span>
                                            <span>Options</span>
                                        </button>
                                        <button
                                            onClick={{() => onDirectDeepDive(ticker, 'news')}}
                                            className="bg-slate-700 hover:bg-purple-600 text-white py-2 px-1 rounded-lg font-medium transition-colors flex flex-col items-center justify-center gap-1 text-sm"
                                        >
                                            <span className="text-lg">\U0001F4F0</span>
                                            <span>Nouvelles</span>
                                        </button>
                                    </div>
                                </div>
                            ))}}
                        </div>
                    </div>
                </div>
            );
        }};

        // App Principal avec Router 3 niveaux
        const App = () => {{
            const [view, setView] = useState('grid');
            const [selectedTicker, setSelectedTicker] = useState(null);
            const [deepDiveSection, setDeepDiveSection] = useState(null);
            const [tickersData, setTickersData] = useState([]);

            React.useEffect(() => {{
                const data = Object.entries(EMBEDDED_DATA).map(([ticker, data]) => ({{ ticker, data, loaded: true }}));
                setTickersData(data);
            }}, []);

            const handleSelectTicker = (ticker) => {{
                setSelectedTicker(ticker);
                setView('detail');
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }};

            const handleDeepDive = (section) => {{
                setDeepDiveSection(section);
                setView('deepdive');
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }};

            const handleDirectDeepDive = (ticker, section) => {{
                setSelectedTicker(ticker);
                setDeepDiveSection(section);
                setView('deepdive');
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }};

            const handleBack = (target = 'grid') => {{
                if (target === 'grid') {{
                    setView('grid');
                    setSelectedTicker(null);
                    setDeepDiveSection(null);
                }} else if (target === 'detail') {{
                    setView('detail');
                    setDeepDiveSection(null);
                }}
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }};

            if (tickersData.length === 0) {{
                return (
                    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
                        <div className="text-white text-2xl">Chargement...</div>
                    </div>
                );
            }}

            const tickerData = selectedTicker ? tickersData.find(t => t.ticker === selectedTicker) : null;

            if (view === 'deepdive' && tickerData && deepDiveSection === 'options') {{
                return <OptionsDeepDive ticker={{selectedTicker}} data={{tickerData.data}} onBack={{handleBack}} />;
            }}

            if (view === 'deepdive' && tickerData && deepDiveSection === 'news') {{
                return <NewsTimeline ticker={{selectedTicker}} data={{tickerData.data}} onBack={{handleBack}} />;
            }}

            if (view === 'detail' && tickerData) {{
                return <DetailView ticker={{selectedTicker}} data={{tickerData.data}} onBack={{() => handleBack('grid')}} onDeepDive={{handleDeepDive}} />;
            }}

            return <GridView tickersData={{tickersData}} onSelectTicker={{handleSelectTicker}} onDirectDeepDive={{handleDirectDeepDive}} />;
        }};

        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>"""
    
    # Remplacer le placeholder de données
    html = html.replace('{data_json}', data_json)
    
    return html

def main():
    print("🔄 Chargement des données (sentiment + options)...")
    all_data = load_all_data()
    print(f"✅ {len(all_data)} tickers chargés")
    
    print("📝 Génération du HTML SPA à 3 niveaux...")
    html_content = generate_3level_spa_html(all_data)
    
    print(f"💾 Sauvegarde vers {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard 3-niveaux généré: {OUTPUT_FILE}")
    print(f"🌐 Ouvrir avec: start {OUTPUT_FILE}")
    print("\n📊 Navigation:")
    print("  Niveau 1: Grille → Clic sur ticker")
    print("  Niveau 2: Détail → Bouton 'Options Deep Dive'")
    print("  Niveau 3: Options Deep Dive → Breadcrumb pour retour")

if __name__ == '__main__':
    main()
