"""
Test Script: Trouver les données politiques
À lancer: 31 Décembre 2025 - Matin

Purpose: Investiguer les sources de données politiques
         et tester BeautifulSoup pour scraping
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json

print("=" * 80)
print("🔍 INVESTIGATION: POLITICAL TRADES DATA SOURCES")
print("=" * 80)
print(f"Timestamp: {datetime.now()}\n")

# ============================================================================
# TEST 1: Capitol Trades (Main Target)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: Capitol Trades (capitoltrades.com)")
print("=" * 80)

try:
    print("\n[1.1] Tentative de connexion...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get('https://www.capitoltrades.com/', headers=headers, timeout=10)
    print(f"✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Page récupérée ({len(response.content)} bytes)")
        
        # Parser HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher éléments clés
        print("\n[1.2] Analyse de la structure HTML...")
        
        # Tables
        tables = soup.find_all('table')
        print(f"   📊 Tables trouvées: {len(tables)}")
        
        if tables:
            table = tables[0]
            headers_row = table.find_all('th')
            print(f"   Colonnes: {[h.text.strip() for h in headers_row[:5]]}")
            
            rows = table.find_all('tr')[1:4]  # First 3 data rows
            print(f"\n   📋 Données brutes (première ligne):")
            if rows:
                cells = rows[0].find_all('td')
                for i, cell in enumerate(cells[:5]):
                    print(f"      Col {i}: {cell.text.strip()[:50]}")
        
        # Divs avec transaction data
        print(f"\n[1.3] Cherchant divs transaction...")
        divs = soup.find_all('div', class_=lambda x: x and ('transaction' in x.lower() or 'trade' in x.lower()))
        print(f"   📦 Divs trouvés: {len(divs)}")
        
        # Links vers stocks
        print(f"\n[1.4] Cherchant liens stocks...")
        stock_tickers = ['AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN', 'META', 'NVDA']
        found_links = []
        
        for ticker in stock_tickers:
            links = soup.find_all('a', href=lambda x: x and ticker in (x.upper()))
            if links:
                found_links.extend([(ticker, link.text.strip()) for link in links[:2]])
        
        print(f"   🔗 Links found: {len(found_links)}")
        for ticker, text in found_links[:5]:
            print(f"      {ticker}: {text}")
        
        # Status
        print("\n✅ CAPITOL TRADES: ACCESSIBLE VIA BEAUTIFULSOUP")
        
    else:
        print(f"❌ Erreur HTTP {response.status_code}")
        
except requests.exceptions.Timeout:
    print("❌ Timeout (site trop lent)")
except requests.exceptions.ConnectionError:
    print("❌ Connection refusée (site bloqué ou down)")
except Exception as e:
    print(f"❌ Erreur: {type(e).__name__}: {e}")

# ============================================================================
# TEST 2: GitHub House Stock Watcher (API)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: GitHub House Stock Watcher Releases (API)")
print("=" * 80)

try:
    print("\n[2.1] Recherche de releases...")
    url = 'https://api.github.com/repos/msnavy/house-stock-watcher/releases'
    
    response = requests.get(url, timeout=10)
    print(f"✅ Status: {response.status_code}")
    
    if response.status_code == 200:
        releases = response.json()
        print(f"✅ {len(releases)} releases trouvées\n")
        
        # Afficher dernières releases
        for release in releases[:3]:
            print(f"📌 {release['tag_name']} ({release['published_at'][:10]})")
            
            assets = release['assets']
            print(f"   Assets: {len(assets)}")
            
            for asset in assets:
                size_mb = asset['size'] / (1024*1024)
                print(f"   - {asset['name']} ({size_mb:.1f} MB)")
                
                # Si c'est du JSON ou CSV, afficher URL
                if any(ext in asset['name'].lower() for ext in ['json', 'csv']):
                    print(f"     Download: {asset['browser_download_url']}")
        
        print("\n✅ GITHUB: Releases trouvées - À télécharger")
        
    else:
        print(f"❌ Erreur HTTP {response.status_code}")
        
except Exception as e:
    print(f"❌ Erreur: {type(e).__name__}: {e}")

# ============================================================================
# TEST 3: Senate Stock Watcher (JSON - Fallback)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: Senate Stock Watcher JSON (Fallback)")
print("=" * 80)

try:
    print("\n[3.1] Tentative sans headers...")
    url = 'https://raw.githubusercontent.com/dwyl/senate-stock-watcher-data/main/data/all_transactions.json'
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {len(data)} transactions récupérées")
        
        # Exemple
        if data:
            print(f"\n📋 Exemple de transaction:")
            example = data[0]
            for key, value in example.items():
                print(f"   {key}: {value}")
        
        print("\n✅ SENATE: FONCTIONNE!")
        
    else:
        print(f"❌ HTTP {response.status_code}")
        
        # Essayer avec headers
        print("\n[3.2] Tentative avec User-Agent...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Fonctionne avec User-Agent!")
        else:
            print(f"❌ Toujours 404")
        
except Exception as e:
    print(f"❌ Erreur: {type(e).__name__}: {e}")

# ============================================================================
# TEST 4: House Stock Watcher (Raw CSV)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 4: House Stock Watcher CSV/JSON")
print("=" * 80)

try:
    print("\n[4.1] Tentative fichier CSV...")
    # URL pattern typique pour house-stock-watcher
    url = 'https://raw.githubusercontent.com/msnavy/house-stock-watcher/main/data/all_transactions.json'
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {len(data)} transactions House")
        print("✅ HOUSE: FONCTIONNE!")
        
    else:
        print(f"❌ HTTP {response.status_code}")
        
        # Chercher releases
        print("\n[4.2] Cherchant releases...")
        url = 'https://api.github.com/repos/msnavy/house-stock-watcher/releases'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            releases = response.json()
            if releases:
                for asset in releases[0]['assets']:
                    if 'json' in asset['name'].lower():
                        print(f"   → Télécharger: {asset['browser_download_url']}")
        
except Exception as e:
    print(f"❌ Erreur: {type(e).__name__}: {e}")

# ============================================================================
# RÉSUMÉ
# ============================================================================
print("\n" + "=" * 80)
print("📊 RÉSUMÉ DES RÉSULTATS")
print("=" * 80)

sources = {
    "Capitol Trades (BeautifulSoup)": "À tester",
    "Senate JSON": "❌ Bloqué (404)",
    "House JSON": "❌ Bloqué (404)",
    "GitHub Releases": "À télécharger",
}

print("\n📋 Sources disponibles:")
for source, status in sources.items():
    print(f"   {source}: {status}")

print("\n🎯 Recommandation pour demain:")
print("   1. Capitol Trades via BeautifulSoup (si HTML accessible)")
print("   2. Sinon: Télécharger depuis GitHub releases")
print("   3. Derniers recours: Selenium si JS bloquage")

print("\n" + "=" * 80)
print(f"✅ Investigation complétée: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 80)
