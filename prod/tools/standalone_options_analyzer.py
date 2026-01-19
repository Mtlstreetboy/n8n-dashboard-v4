#!/usr/bin/env python3
"""
🛠️ STANDALONE OPTIONS ANALYZER (Zone 1)
----------------------------------------
Analyzes raw options data to determine Market Structure:
- Max Pain Price
- Call/Put Walls (OI Resistance/Support)
- Market Maker Positioning (GEX Proxy)

Generates a standalone HTML report.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
import datetime
import argparse
import webbrowser

# Adjust path to find config if needed (though this is standalone)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR)) # prod -> pipelines -> root
DATA_DIR = os.path.join(PROJECT_ROOT, 'local_files')
OPTIONS_DIR = os.path.join(DATA_DIR, 'options_data')
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')

class OptionsStructureAnalyzer:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.calls_df = pd.DataFrame()
        self.puts_df = pd.DataFrame()
        self.prev_calls_df = pd.DataFrame()
        self.prev_puts_df = pd.DataFrame()
        self.metrics = {}
        
    def load_latest_data(self):
        """Finds and loads the 2 most recent CSV files for the ticker to allow comparison."""
        # Find all files matching pattern
        call_files = glob.glob(os.path.join(OPTIONS_DIR, f"{self.ticker}_calls_*.csv"))
        put_files = glob.glob(os.path.join(OPTIONS_DIR, f"{self.ticker}_puts_*.csv"))
        
        if len(call_files) < 1 or len(put_files) < 1:
            print(f"❌ No options data found for {self.ticker} in {OPTIONS_DIR}")
            return False
            
        # Sort files by creation time (newest first)
        call_files.sort(key=os.path.getctime, reverse=True)
        put_files.sort(key=os.path.getctime, reverse=True)
        
        latest_call = call_files[0]
        latest_put = put_files[0]
        
        print(f"📂 Loading CURRENT data:\n  Calls: {os.path.basename(latest_call)}\n  Puts:  {os.path.basename(latest_put)}")
        
        try:
            self.calls_df = pd.read_csv(latest_call)
            self.puts_df = pd.read_csv(latest_put)
            
            # Load PREVIOUS data if available
            if len(call_files) > 1 and len(put_files) > 1:
                prev_call = call_files[1]
                prev_put = put_files[1]
                print(f"📂 Loading PREVIOUS data (for comparison):\n  Calls: {os.path.basename(prev_call)}\n  Puts:  {os.path.basename(prev_put)}")
                self.prev_calls_df = pd.read_csv(prev_call)
                self.prev_puts_df = pd.read_csv(prev_put)
            else:
                print("⚠️ No previous data found for comparison. Deltas will be 0.")

            # Ensure numeric columns for current data
            for col in ['openInterest', 'volume', 'strike', 'lastPrice', 'impliedVolatility']:
                if col in self.calls_df.columns:
                    self.calls_df[col] = pd.to_numeric(self.calls_df[col], errors='coerce').fillna(0)
                    self.puts_df[col] = pd.to_numeric(self.puts_df[col], errors='coerce').fillna(0)
            
            # Ensure numeric columns for previous data if loaded
            if not self.prev_calls_df.empty:
                 for col in ['openInterest', 'strike']:
                    if col in self.prev_calls_df.columns:
                        self.prev_calls_df[col] = pd.to_numeric(self.prev_calls_df[col], errors='coerce').fillna(0)
                        self.prev_puts_df[col] = pd.to_numeric(self.prev_puts_df[col], errors='coerce').fillna(0)
            
            return True
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def calculate_max_pain(self):
        """
        Calculates Max Pain: The strike price where option holders lose the most money.
        """
        if self.calls_df.empty or self.puts_df.empty: return
        
        def compute_pain(calls, puts):
            strikes = sorted(list(set(calls['strike'].unique()) | set(puts['strike'].unique())))
            results = []
            for price_candidate in strikes:
                call_cash_value = calls.apply(lambda row: max(0, price_candidate - row['strike']) * row['openInterest'], axis=1).sum()
                put_cash_value = puts.apply(lambda row: max(0, row['strike'] - price_candidate) * row['openInterest'], axis=1).sum()
                results.append({'strike': price_candidate, 'pain': call_cash_value + put_cash_value})
            df = pd.DataFrame(results)
            return df.loc[df['pain'].idxmin()]['strike']

        # Current Max Pain
        self.metrics['max_pain'] = compute_pain(self.calls_df, self.puts_df)
        print(f"🩸 Max Pain calculated: ${self.metrics['max_pain']}")
        
        # Previous Max Pain (if available)
        if not self.prev_calls_df.empty:
            prev_pain = compute_pain(self.prev_calls_df, self.prev_puts_df)
            self.metrics['prev_max_pain'] = prev_pain
            print(f"⏮️ Previous Max Pain: ${prev_pain}")

    def analyze_walls_and_gex(self):
        """
        Identifies huge OI levels (Walls) and Comparison.
        """
        if self.calls_df.empty: return
        
        # Helper to get wall and OI
        def get_wall(df):
            row = df.loc[df['openInterest'].idxmax()]
            return row['strike'], row['openInterest']

        # Current Walls
        call_wall, call_max_oi = get_wall(self.calls_df)
        put_wall, put_max_oi = get_wall(self.puts_df)
        
        self.metrics['call_wall'] = call_wall
        self.metrics['call_wall_oi'] = call_max_oi
        self.metrics['put_wall'] = put_wall
        self.metrics['put_wall_oi'] = put_max_oi
        
        # Calculate Deltas (Change in OI at the WALL Strike)
        # Note: We track the change at the *current* wall strike, to see if it's strengthening or weakening.
        call_oi_delta = 0
        put_oi_delta = 0
        
        if not self.prev_calls_df.empty:
            # Find OI of the CURRENT call wall strike in the PREVIOUS data
            prev_c_row = self.prev_calls_df[self.prev_calls_df['strike'] == call_wall]
            prev_c_oi = prev_c_row['openInterest'].sum() if not prev_c_row.empty else 0
            call_oi_delta = call_max_oi - prev_c_oi
            
            # Find OI of the CURRENT put wall strike in the PREVIOUS data
            prev_p_row = self.prev_puts_df[self.prev_puts_df['strike'] == put_wall]
            prev_p_oi = prev_p_row['openInterest'].sum() if not prev_p_row.empty else 0
            put_oi_delta = put_max_oi - prev_p_oi
            
        self.metrics['call_oi_delta'] = call_oi_delta
        self.metrics['put_oi_delta'] = put_oi_delta
        
        print(f"🧱 Call Wall: ${call_wall} (OI: {call_max_oi}, Delta: {call_oi_delta:+g})")
        print(f"🧱 Put Wall:  ${put_wall} (OI: {put_max_oi}, Delta: {put_oi_delta:+g})")

    def analyze_smart_flow(self):
        """
        Zone 2: Smart Money Flow.
        Detects 'Whales' (Vol > OI) and calculates Net Flow Sentiment.
        """
        if self.calls_df.empty: return

        # 1. Net Flow Sentiment
        total_call_vol = self.calls_df['volume'].sum()
        total_put_vol = self.puts_df['volume'].sum()
        total_vol = total_call_vol + total_put_vol
        
        net_flow = (total_call_vol - total_put_vol) / total_vol if total_vol > 0 else 0
        self.metrics['net_flow'] = net_flow
        self.metrics['total_call_vol'] = total_call_vol
        self.metrics['total_put_vol'] = total_put_vol

        # 2. Whale Hunting (Vol > OI)
        # We look for strikes where Volume is unusually high relative to OI
        # Threshold: Vol > OI * 1.5 AND Vol > 500 (avoid noise)
        
        whales = []
        
        # Check Calls
        for _, row in self.calls_df.iterrows():
            if row['volume'] > 500 and row['openInterest'] > 0:
                ratio = row['volume'] / row['openInterest']
                if ratio > 1.2: # Aggessive entry
                    whales.append({
                        'type': 'CALL',
                        'strike': row['strike'],
                        'volume': int(row['volume']),
                        'oi': int(row['openInterest']),
                        'ratio': round(ratio, 2),
                        'expiry': 'N/A' # Add expiry if available in future
                    })
        
        # Check Puts
        for _, row in self.puts_df.iterrows():
            if row['volume'] > 500 and row['openInterest'] > 0:
                ratio = row['volume'] / row['openInterest']
                if ratio > 1.2:
                    whales.append({
                        'type': 'PUT',
                        'strike': row['strike'],
                        'volume': int(row['volume']),
                        'oi': int(row['openInterest']),
                        'ratio': round(ratio, 2),
                        'expiry': 'N/A'
                    })
        
        # Sort whales by Ratio descending
        whales.sort(key=lambda x: x['ratio'], reverse=True)
        self.metrics['whales'] = whales[:10] # Top 10
        
        print(f"🐋 Whales Detected: {len(whales)}")
        print(f"🌊 Net Flow: {net_flow:.2f} (Call: {total_call_vol} vs Put: {total_put_vol})")

    def analyze_volatility_zone3(self):
        """
        Zone 3: Volatility & Skew.
        Calculates:
        1. Vertical Skew (Fear Index): OTM Put IV / OTM Call IV.
        2. GEX Proxy: Net Gamma Exposure (Estimates market stability).
        """
        if self.calls_df.empty: return
        
        # 1. Volatility Skew (Put/Call Ratio of IV)
        # We need an "At The Money" (ATM) reference. 
        # Approx ATM = Max Pain (often close enough) or infer from strike with lowest diff.
        # Let's find strike closest to where LastPrice is.
        # Since we don't have spot, use Max Pain as "Market Center" for now.
        center_price = self.metrics.get('max_pain', 0)
        
        # Look at 10% OTM
        downside_strike = center_price * 0.9
        upside_strike = center_price * 1.1
        
        # Find closest strikes
        put_iv_row = self.puts_df.iloc[(self.puts_df['strike'] - downside_strike).abs().argsort()[:1]]
        call_iv_row = self.calls_df.iloc[(self.calls_df['strike'] - upside_strike).abs().argsort()[:1]]
        
        put_iv = put_iv_row['impliedVolatility'].values[0] if not put_iv_row.empty else 0
        call_iv = call_iv_row['impliedVolatility'].values[0] if not call_iv_row.empty else 0
        
        skew = put_iv / call_iv if call_iv > 0 else 1.0
        self.metrics['skew'] = skew
        
        print(f"🌪️ Vol Skew (Fear Index): {skew:.2f} (Put IV: {put_iv:.2f} / Call IV: {call_iv:.2f})")
        
        # 2. GEX Proxy (Net Gamma Exposure)
        # If 'gamma' column is missing, we use a proxy: OI * (Call - Put) * Spot * 0.01
        # Here we just do a simplified "Net OI GEX" to see direction.
        # Positive GEX = Dealers Long Gamma = Suppress Volatility (Brakes)
        # Negative GEX = Dealers Short Gamma = Amplify Volatility (Accelerator)
        
        net_gex_proxy = 0
        has_gamma = 'gamma' in self.calls_df.columns
        
        for _, row in self.calls_df.iterrows():
            gamma = row.get('gamma', 0.01) # Default tiny gamma if missing to rely on OI
            net_gex_proxy += row['openInterest'] * gamma * row['strike']
            
        for _, row in self.puts_df.iterrows():
            gamma = row.get('gamma', 0.01)
            net_gex_proxy -= row['openInterest'] * gamma * row['strike']
            
        self.metrics['gex'] = net_gex_proxy
        gex_state = "BRAKES ON (Stable)" if net_gex_proxy > 0 else "ACCELERATOR (Volatile)"
        print(f"🚦 GEX Proxy: {net_gex_proxy:.0f} -> {gex_state}")

    def generate_html_report(self):
        """Generates a standalone HTML report with Volatility Smile Chart."""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(REPORTS_DIR, f"options_structure_{self.ticker}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.html")
        
        # Prepare Data for Volatility Smile (Zone 3 Visual)
        # 1. Find Nearest Expiration
        if 'expiration' in self.calls_df.columns:
            files_exps = sorted(self.calls_df['expiration'].unique())
            target_exp = files_exps[0] if files_exps else None
        else:
            target_exp = None
            
        chart_labels = []
        chart_call_iv = []
        chart_put_iv = []
        
        smile_title = "Volatility Smile"
        
        if target_exp:
            smile_title = f"Volatility Smile (Exp: {target_exp})"
            print(f"📉 Generating Smile for Expiration: {target_exp}")
            
            # Filter Data
            c_data = self.calls_df[self.calls_df['expiration'] == target_exp].sort_values('strike')
            p_data = self.puts_df[self.puts_df['expiration'] == target_exp].sort_values('strike')
            
            # Merge Strikes
            all_strikes = sorted(list(set(c_data['strike']) | set(p_data['strike'])))
            
            # Get IVs
            mp = self.metrics.get('max_pain', 0)
            lower_bound = mp * 0.6 # Widen to 40%
            upper_bound = mp * 1.4
            
            for k in all_strikes:
                if lower_bound <= k <= upper_bound:
                    # Find IV
                    c_iv = c_data.loc[c_data['strike'] == k, 'impliedVolatility'].values
                    p_iv = p_data.loc[p_data['strike'] == k, 'impliedVolatility'].values
                    
                    # Loosen IV filter slightly (allow >= 0 if we want to see it)
                    c_val = c_iv[0] if len(c_iv) > 0 and c_iv[0] > 0 else None
                    p_val = p_iv[0] if len(p_iv) > 0 and p_iv[0] > 0 else None
                    
                    if c_val is not None or p_val is not None:
                        chart_labels.append(k)
                        chart_call_iv.append(c_val)
                        chart_put_iv.append(p_val)
        
        # Whale Table Rows
        whale_rows = ""
        for w in self.metrics.get('whales', []):
            color = "#38bdf8" if w['type'] == 'CALL' else "#34d399"
            whale_rows += f"""<tr style="border-bottom: 1px solid #334155;"><td style="padding: 10px; color: {color}; font-weight: bold;">{w['type']}</td><td style="padding: 10px;">${w['strike']}</td><td style="padding: 10px;">{w['volume']}</td><td style="padding: 10px;">{w['oi']}</td><td style="padding: 10px; font-weight: bold;">{w['ratio']}x</td></tr>"""

        # Zone 2 Colors
        net_flow = self.metrics.get('net_flow', 0)
        flow_color = "#34d399" if net_flow > 0.1 else ("#f43f5e" if net_flow < -0.1 else "#94a3b8")
        flow_text = "BULLISH" if net_flow > 0.1 else ("BEARISH" if net_flow < -0.1 else "NEUTRAL")

        # Zone 3 Colors
        skew = self.metrics.get('skew', 1.0)
        skew_color = "#f43f5e" if skew > 1.2 else ("#34d399" if skew < 0.9 else "#fbbf24") # High Skew = Fear
        skew_text = "FEAR" if skew > 1.2 else ("GREED" if skew < 0.9 else "NEUTRAL")
        
        gex = self.metrics.get('gex', 0)
        gex_text = "STABLE (Brakes)" if gex > 0 else "VOLATILE (Accel)"
        gex_color = "#34d399" if gex > 0 else "#f43f5e"

        # Helpers
        def format_delta(val):
            if val > 0: return f"<span style='color: #34d399; font-size: 0.6em;'>(+{val:.0f}) ▲</span>"
            if val < 0: return f"<span style='color: #f43f5e; font-size: 0.6em;'>({val:.0f}) ▼</span>"
            return "<span style='color: #94a3b8; font-size: 0.6em;'>(=)</span>"

        c_delta = format_delta(self.metrics.get('call_oi_delta', 0))
        p_delta = format_delta(self.metrics.get('put_oi_delta', 0))
        pain_suffix = f"<span style='font-size: 0.6em; color: #fbbf24;'> (was ${self.metrics.get('prev_max_pain')})</span>" if (self.metrics.get('prev_max_pain') and self.metrics.get('prev_max_pain') != mp) else ""

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Smart Options Analysis: {self.ticker}</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: 'Inter', sans-serif; background-color: #0f172a; color: #e2e8f0; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .card {{ background: #1e293b; border-radius: 16px; padding: 24px; margin-bottom: 24px; border: 1px solid #334155; }}
                h1, h2 {{ color: #f8fafc; border-bottom: 1px solid #334155; padding-bottom: 10px; }}
                .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
                .metric-box {{ background: #0f172a; padding: 15px; border-radius: 12px; border: 1px solid #334155; text-align: center; }}
                .metric-label {{ font-size: 0.9em; color: #94a3b8; text-transform: uppercase; }}
                .metric-value {{ font-size: 2em; font-weight: bold; margin-top: 10px; }}
                .max-pain {{ color: #f43f5e; }} .call-wall {{ color: #38bdf8; }} .put-wall {{ color: #34d399; }}
                .badge {{ padding: 5px 10px; border-radius: 9999px; font-size: 0.8em; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🦅 Smart Options Analysis: {self.ticker}</h1>
                <p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;">
                    <!-- Zone 1 -->
                    <div class="card">
                        <h2>Zone 1: Market Structure (vs Previous)</h2>
                        <div class="metric-grid">
                            <div class="metric-box"><div class="metric-label">🩸 Max Pain</div><div class="metric-value max-pain">${self.metrics.get('max_pain')}{pain_suffix}</div></div>
                            <div class="metric-box"><div class="metric-label">🧱 Call Wall</div><div class="metric-value call-wall">${self.metrics.get('call_wall')}</div><div style="font-size:small">{c_delta}</div></div>
                            <div class="metric-box"><div class="metric-label">🧱 Put Wall</div><div class="metric-value put-wall">${self.metrics.get('put_wall')}</div><div style="font-size:small">{p_delta}</div></div>
                        </div>
                    </div>

                    <!-- Zone 2 -->
                    <div class="card">
                        <h2>Zone 2: Smart Money Flow <span class="badge" style="background: {flow_color}20; color: {flow_color};">{flow_text}</span></h2>
                        <div class="metric-grid">
                            <div class="metric-box"><div class="metric-label">🌊 Net Flow</div><div class="metric-value" style="color: {flow_color}">{self.metrics.get('net_flow', 0):.2%}</div></div>
                            <div class="metric-box"><div class="metric-label">🐋 Whales</div><div class="metric-value" style="color: #fbbf24">{len(self.metrics.get('whales', []))}</div></div>
                        </div>
                    </div>

                    <!-- Zone 3 -->
                    <div class="card">
                        <h2>Zone 3: Volatility & Sentiment <span class="badge" style="background: {skew_color}20; color: {skew_color};">{skew_text}</span></h2>
                        <div class="metric-grid">
                            <div class="metric-box">
                                <div class="metric-label">🌪️ Skew (Fear Index)</div>
                                <div class="metric-value" style="color: {skew_color}">{skew:.2f}</div>
                                <div style="font-size: 0.8em; color: #64748b;">Put IV / Call IV (>1.2 = Fear)</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">🚦 Gamma Exposure</div>
                                <div class="metric-value" style="color: {gex_color}">{gex_text}</div>
                                <div style="font-size: 0.8em; color: #64748b;">MMs are stabilizing (Pos) or amplifying (Neg)</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2>🎭 {smile_title}</h2>
                    <div style="height: 350px;"><canvas id="smileChart"></canvas></div>
                </div>

                <div class="card">
                    <h2>🐋 Whale Tracks</h2>
                    <table style="width:100%">{whale_rows}</table>
                </div>
            </div>
            
            <script>
                const ctx = document.getElementById('smileChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: {chart_labels},
                        datasets: [
                            {{ 
                                label: 'Call IV', 
                                data: {chart_call_iv}, 
                                borderColor: '#38bdf8',
                                backgroundColor: '#38bdf8',
                                borderWidth: 2,
                                tension: 0.4,
                                pointRadius: 2
                            }},
                            {{ 
                                label: 'Put IV', 
                                data: {chart_put_iv}, 
                                borderColor: '#34d399',
                                backgroundColor: '#34d399',
                                borderWidth: 2,
                                tension: 0.4,
                                pointRadius: 2
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{
                            mode: 'index',
                            intersect: false,
                        }},
                        scales: {{
                            x: {{ 
                                title: {{ display: true, text: 'Strike Price ($)', color: '#94a3b8' }},
                                grids: {{ color: '#334155' }}, 
                                ticks: {{ color: '#94a3b8' }} 
                            }},
                            y: {{ 
                                title: {{ display: true, text: 'Implied Volatility', color: '#94a3b8' }},
                                grids: {{ color: '#334155' }}, 
                                ticks: {{ color: '#94a3b8' }} 
                            }}
                        }},
                        plugins: {{
                            legend: {{ labels: {{ color: '#f8fafc' }} }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        return context.dataset.label + ': ' + (context.raw * 100).toFixed(1) + '%';
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Report generated: {report_path}")
        return report_path

def main():
    parser = argparse.ArgumentParser(description='Standalone Options Analyzer')
    parser.add_argument('--ticker', type=str, default='NVDA', help='Ticker symbol')
    args = parser.parse_args()
    
    analyzer = OptionsStructureAnalyzer(args.ticker)
    if analyzer.load_latest_data():
        analyzer.calculate_max_pain()
        analyzer.analyze_walls_and_gex()
        analyzer.analyze_smart_flow()
        analyzer.analyze_volatility_zone3()
        analyzer.generate_html_report()
    else:
        print("❌ Failed to run analysis.")

if __name__ == "__main__":
    main()
