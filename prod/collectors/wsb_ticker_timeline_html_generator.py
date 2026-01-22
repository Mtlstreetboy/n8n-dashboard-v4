"""
Generate an interactive HTML dashboard from WSB ticker timeline analysis.
Ultra-lightweight - vanilla JS + Chart.js CDN, no build process needed.
"""

import json
from pathlib import Path
from datetime import datetime

def generate_html_dashboard(analysis_json_path: str, output_html_path: str) -> str:
    """Generate interactive HTML dashboard from ticker analysis JSON."""
    
    # Load analysis data
    with open(analysis_json_path, 'r') as f:
        data = json.load(f)
    
    # Handle both formats: direct dict or nested under 'ticker_info'
    ticker_info = data.get('ticker_info', data) if isinstance(data, dict) else data
    
    # Separate tickers by category
    high_momentum = sorted(
        [(t, info) for t, info in ticker_info.items()],
        key=lambda x: x[1]['momentum'],
        reverse=True
    )[:15]
    
    new_tickers = [
        (t, info) for t, info in ticker_info.items()
        if info.get('first_mention') and '2026-01-19' in info['first_mention']
    ]
    new_tickers = sorted(new_tickers, key=lambda x: x[1]['total_mentions'], reverse=True)[:20]
    
    all_tickers = sorted(
        ticker_info.items(),
        key=lambda x: x[1]['total_mentions'],
        reverse=True
    )
    
    # Prepare data for charts
    top_20_labels = [t[0] for t in all_tickers[:20]]
    top_20_volumes = [t[1]['total_mentions'] for t in all_tickers[:20]]
    
    momentum_labels = [t[0] for t in high_momentum]
    momentum_values = [t[1]['momentum'] for t in high_momentum]
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WSB Ticker Timeline - Interactive Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        header p {{
            font-size: 1.1em;
            opacity: 0.95;
            margin-bottom: 10px;
        }}
        
        .timestamp {{
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 10px;
        }}
        
        .nav-tabs {{
            display: flex;
            border-bottom: 3px solid #e5e7eb;
            background: #f9fafb;
        }}
        
        .nav-tabs button {{
            flex: 1;
            padding: 16px 20px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.05em;
            font-weight: 500;
            color: #666;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
            margin-bottom: -3px;
        }}
        
        .nav-tabs button:hover {{
            background: #f3f4f6;
            color: #667eea;
        }}
        
        .nav-tabs button.active {{
            color: #667eea;
            border-bottom-color: #667eea;
        }}
        
        .tab-content {{
            display: none;
            padding: 30px;
            animation: fadeIn 0.3s ease;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-card .value {{
            font-size: 2em;
            font-weight: 700;
            margin: 10px 0;
        }}
        
        .stat-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 30px;
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #667eea;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        tr:hover {{
            background: #f9fafb;
        }}
        
        .ticker {{
            font-weight: 600;
            color: #667eea;
            font-family: monospace;
            font-size: 1.1em;
        }}
        
        .momentum {{
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }}
        
        .momentum.positive {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .momentum.negative {{
            background: #fee2e2;
            color: #7f1d1d;
        }}
        
        .momentum.neutral {{
            background: #f3f4f6;
            color: #374151;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        
        .badge.new {{
            background: #fbbf24;
            color: #78350f;
        }}
        
        .search-box {{
            margin-bottom: 20px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 10px 15px;
            border: 2px solid #e5e7eb;
            border-radius: 6px;
            font-size: 1em;
            transition: border-color 0.3s;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .footer {{
            background: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #e5e7eb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 WSB Ticker Timeline</h1>
            <p>Real-time momentum tracking and trend detection from Wall Street Bets</p>
            <div class="timestamp">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        </header>
        
        <div class="nav-tabs">
            <button class="tab-btn active" data-tab="momentum">🔥 Trending</button>
            <button class="tab-btn" data-tab="new">✨ New Entries</button>
            <button class="tab-btn" data-tab="all">📊 All Tickers</button>
            <button class="tab-btn" data-tab="charts">📈 Analytics</button>
        </div>
        
        <!-- TAB: MOMENTUM -->
        <div id="momentum" class="tab-content active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">Top Movers</div>
                    <div class="value">{len(high_momentum)}</div>
                </div>
                <div class="stat-card">
                    <div class="label">Max Momentum</div>
                    <div class="value">{(high_momentum[0][1]['momentum'] if high_momentum else 0):.0f}%</div>
                </div>
                <div class="stat-card">
                    <div class="label">Total Unique Tickers</div>
                    <div class="value">{len(ticker_info)}</div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Ticker</th>
                        <th>Momentum</th>
                        <th>Total Mentions</th>
                        <th>Days Active</th>
                        <th>First Mention</th>
                    </tr>
                </thead>
                <tbody id="momentum-table">
"""
    
    # Add momentum rows
    for idx, (ticker, info) in enumerate(high_momentum, 1):
        momentum = info['momentum']
        momentum_class = 'positive' if momentum > 0 else ('negative' if momentum < 0 else 'neutral')
        
        html_content += f"""
                    <tr>
                        <td>{idx}</td>
                        <td><span class="ticker">{ticker}</span></td>
                        <td><span class="momentum {momentum_class}">{momentum:+.1f}%</span></td>
                        <td>{info['total_mentions']}</td>
                        <td>{info['days_active']}</td>
                        <td>{info['first_mention']}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <!-- TAB: NEW ENTRIES -->
        <div id="new" class="tab-content">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">New Tickers Today</div>
                    <div class="value">""" + str(len(new_tickers)) + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">Avg Mentions (New)</div>
                    <div class="value">""" + (str(sum(t[1]['total_mentions'] for t in new_tickers) // len(new_tickers)) if new_tickers else '0') + """</div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Ticker</th>
                        <th>Mentions</th>
                        <th>First Seen</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for idx, (ticker, info) in enumerate(new_tickers, 1):
        html_content += f"""
                    <tr>
                        <td>{idx}</td>
                        <td><span class="ticker">{ticker}</span> <span class="badge new">NEW</span></td>
                        <td>{info['total_mentions']}</td>
                        <td>{info['first_mention']}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <!-- TAB: ALL TICKERS -->
        <div id="all" class="tab-content">
            <div class="search-box">
                <input type="text" id="search-input" placeholder="🔍 Search ticker or company...">
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Mentions</th>
                        <th>Days Active</th>
                        <th>Momentum</th>
                        <th>First Mention</th>
                    </tr>
                </thead>
                <tbody id="all-table">
"""
    
    for ticker, info in all_tickers:
        momentum = info['momentum']
        momentum_class = 'positive' if momentum > 0 else ('negative' if momentum < 0 else 'neutral')
        
        html_content += f"""
                    <tr class="ticker-row">
                        <td><span class="ticker">{ticker}</span></td>
                        <td>{info['total_mentions']}</td>
                        <td>{info['days_active']}</td>
                        <td><span class="momentum {momentum_class}">{momentum:+.1f}%</span></td>
                        <td>{info['first_mention']}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <!-- TAB: CHARTS -->
        <div id="charts" class="tab-content">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">Total Mentions</div>
                    <div class="value">""" + str(sum(info['total_mentions'] for info in ticker_info.values())) + """</div>
                </div>
            </div>
            
            <div class="chart-container">
                <canvas id="top20-chart"></canvas>
            </div>
            
            <div class="chart-container">
                <canvas id="momentum-chart"></canvas>
            </div>
        </div>
        
        <div class="footer">
            📊 WSB Ticker Timeline Dashboard | Data updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
        </div>
    </div>
    
    <script>
        // Tab navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.getElementById(e.target.dataset.tab).classList.add('active');
                e.target.classList.add('active');
            });
        });
        
        // Search functionality
        document.getElementById('search-input').addEventListener('keyup', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.ticker-row').forEach(row => {
                const ticker = row.querySelector('.ticker').textContent.toLowerCase();
                row.style.display = ticker.includes(query) ? '' : 'none';
            });
        });
        
        // Charts
        const ctx20 = document.getElementById('top20-chart').getContext('2d');
        new Chart(ctx20, {
            type: 'bar',
            data: {
                labels: """ + json.dumps(top_20_labels) + """,
                datasets: [{
                    label: 'Total Mentions',
                    data: """ + json.dumps(top_20_volumes) + """,
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true },
                    title: { display: true, text: 'Top 20 Most Mentioned Tickers' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        const ctxMom = document.getElementById('momentum-chart').getContext('2d');
        new Chart(ctxMom, {
            type: 'bar',
            data: {
                labels: """ + json.dumps(momentum_labels) + """,
                datasets: [{
                    label: 'Momentum (%)',
                    data: """ + json.dumps(momentum_values) + """,
                    backgroundColor: """ + json.dumps([
                        'rgba(16, 185, 129, 0.6)' if v > 500 else 'rgba(102, 126, 234, 0.6)' if v > 100 else 'rgba(245, 158, 11, 0.6)'
                        for v in momentum_values
                    ]) + """,
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true },
                    title: { display: true, text: 'Top 15 Tickers by Momentum' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Generated interactive dashboard: {output_html_path}")
    return output_html_path


if __name__ == '__main__':
    import sys
    
    analysis_file = sys.argv[1] if len(sys.argv) > 1 else 'local_files/wsb_data/wsb_ticker_analysis.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'local_files/wsb_data/wsb_ticker_dashboard.html'
    
    # Ensure paths are absolute
    base_dir = Path(__file__).parent.parent.parent
    analysis_file = str(base_dir / analysis_file)
    output_file = str(base_dir / output_file)
    
    generate_html_dashboard(analysis_file, output_file)
