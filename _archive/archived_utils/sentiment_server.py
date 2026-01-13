#!/usr/bin/env python3
"""
Serveur HTTP simple pour servir les données de sentiment
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from urllib.parse import urlparse

SENTIMENT_DIR = '/data/sentiment_analysis'

def _iter_latest_files():
    """Yield (ticker, filepath) for latest files.

    Prefer *_latest_v3.json > *_latest_v2.json > *_latest.json when multiple exist.
    """
    latest_v3 = {}
    latest_v2 = {}
    latest_v1 = {}
    for filename in os.listdir(SENTIMENT_DIR):
        if filename.endswith('_latest_v3.json'):
            ticker = filename.replace('_latest_v3.json', '')
            latest_v3[ticker.upper()] = os.path.join(SENTIMENT_DIR, filename)
        elif filename.endswith('_latest_v2.json'):
            ticker = filename.replace('_latest_v2.json', '')
            latest_v2[ticker.upper()] = os.path.join(SENTIMENT_DIR, filename)
        elif filename.endswith('_latest.json'):
            ticker = filename.replace('_latest.json', '')
            latest_v1[ticker.upper()] = os.path.join(SENTIMENT_DIR, filename)

    # Prefer v3 > v2 > v1 if available
    all_tickers = set(latest_v1.keys()) | set(latest_v2.keys()) | set(latest_v3.keys())
    for ticker in sorted(all_tickers):
        yield ticker, (latest_v3.get(ticker) or latest_v2.get(ticker) or latest_v1.get(ticker))


def _get_latest_filepath(ticker: str) -> str:
    ticker = (ticker or '').upper()
    v3 = os.path.join(SENTIMENT_DIR, f'{ticker}_latest_v3.json')
    if os.path.exists(v3):
        return v3
    v2 = os.path.join(SENTIMENT_DIR, f'{ticker}_latest_v2.json')
    if os.path.exists(v2):
        return v2
    v1 = os.path.join(SENTIMENT_DIR, f'{ticker}_latest.json')
    return v1

class SentimentHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Route: liste des tickers
        if parsed_path.path == '/list-tickers':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            tickers = [t for t, _ in _iter_latest_files()]
            self.wfile.write(json.dumps(tickers).encode())
            return
        
        # Route: données d'un ticker
        if parsed_path.path.startswith('/sentiment/'):
            ticker = parsed_path.path.split('/')[-1].upper()
            filepath = _get_latest_filepath(ticker)
            
            if os.path.exists(filepath):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Ticker not found'}).encode())
            return
        
        # Route: servir le HTML
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_path = '/data/scripts/dashboard_sentiment.html'
            if os.path.exists(html_path):
                with open(html_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.wfile.write(b'<h1>Dashboard not found</h1>')
            return
        
        # Autre: 404
        self.send_response(404)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'404 Not Found')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run(port=8501):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SentimentHandler)
    print(f'🚀 Serveur démarré sur http://localhost:{port}')
    print(f'📊 Dashboard: http://localhost:{port}/')
    print(f'📋 API tickers: http://localhost:{port}/list-tickers')
    print(f'📈 API sentiment: http://localhost:{port}/sentiment/NVDA')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
