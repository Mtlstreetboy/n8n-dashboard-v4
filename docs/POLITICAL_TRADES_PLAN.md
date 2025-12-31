# Plan d'Attaque: Political Trades - 31 Décembre 2025

## 🎯 Mission Critique

Débloquer les données des transactions politiques (Sénat + Chambre) pour compléter le Smart Money Tracker.

**Status:** Les deux sources JSON gratuites sont bloquées (404/403). Alternative nécessaire.

---

## 🕵️ Investigation BeautifulSoup

### Cible #1: Capitol Trades (capitoltrades.com)

**Avantages:**
- Site public, pas d'authentification
- Données en temps réel
- Mentions dans articles Smart Money
- HTML statique ou JS?

**Plan d'attaque:**
```python
import requests
from bs4 import BeautifulSoup

# Étape 1: Récupérer page principale
response = requests.get('https://www.capitoltrades.com/')
print(response.status_code)  # Si 200, c'est bon!

# Étape 2: Parser HTML
soup = BeautifulSoup(response.content, 'html.parser')

# Étape 3: Inspecter structure
print(soup.prettify())  # Voir le HTML

# Étape 4: Extraire tableau/données
tables = soup.find_all('table')
for table in tables:
    rows = table.find_all('tr')
    print(f"Table avec {len(rows)} lignes")
```

**Données à chercher:**
- Nom politicien
- Chambre (Senate/House)
- Ticker
- Date transaction
- Type (Buy/Sell)
- Nombre shares (optionnel)
- Prix (optionnel)

### Cible #2: GitHub House Stock Watcher

**URL:** `https://github.com/msnavy/house-stock-watcher`

Peut avoir:
- Releases avec JSON dump
- Instructions pour télécharger données
- Alternative data source

```python
# Essayer endpoint releases
url = 'https://api.github.com/repos/msnavy/house-stock-watcher/releases'
response = requests.get(url)
# Parser les assets pour trouver fichier CSV/JSON
```

---

## 📋 Script de Test - À Exécuter Demain

Créer `test_political_scraping.py`:

```python
"""
Test script: Tester BeautifulSoup sur sources politiques
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd

print("="*70)
print("TEST 1: Capitol Trades (capitoltrades.com)")
print("="*70)

try:
    response = requests.get('https://www.capitoltrades.com/', timeout=10)
    print(f"✅ Status: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher tableaux
        tables = soup.find_all('table')
        print(f"📊 Tables trouvées: {len(tables)}")
        
        # Chercher divs avec class 'transaction' ou similaire
        divs = soup.find_all('div', class_=lambda x: x and 'trade' in x.lower())
        print(f"📦 Divs transaction: {len(divs)}")
        
        # Chercher tout lien vers ticket
        links = soup.find_all('a', href=lambda x: x and any(t in x.upper() for t in ['AAPL','MSFT','TSLA']))
        print(f"🔗 Liens stock trouvés: {len(links)}")
        if links:
            for link in links[:5]:
                print(f"   - {link.text}: {link.get('href')}")
    
except requests.exceptions.ConnectionError:
    print("❌ Connection refusée (site bloqué ou down)")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "="*70)
print("TEST 2: GitHub House Stock Watcher Releases")
print("="*70)

try:
    url = 'https://api.github.com/repos/msnavy/house-stock-watcher/releases'
    response = requests.get(url, timeout=10)
    print(f"✅ Status: {response.status_code}")
    
    if response.status_code == 200:
        releases = response.json()
        print(f"📦 Releases trouvées: {len(releases)}")
        
        for release in releases[:3]:
            print(f"\n📌 {release['tag_name']}")
            print(f"   Date: {release['published_at']}")
            print(f"   Assets: {len(release['assets'])}")
            
            for asset in release['assets']:
                print(f"     - {asset['name']}")
                if 'json' in asset['name'].lower() or 'csv' in asset['name'].lower():
                    print(f"       → Download: {asset['browser_download_url']}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "="*70)
print("TEST 3: Senate Stock Watcher (fallback)")
print("="*70)

try:
    # Essayer avec different headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    url = 'https://raw.githubusercontent.com/dwyl/senate-stock-watcher-data/main/data/all_transactions.json'
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {len(data)} transactions")
        print(f"Exemple: {data[0]}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
```

---

## 🛠️ Implementation Strategy

### Étape 1: Détecter Structure HTML
```python
# Dans test_political_scraping.py, identifier:
# - Où sont les noms politiciens
# - Où sont les tickers
# - Où sont les dates
# - Où sont les types (buy/sell)
```

### Étape 2: Parser avec BeautifulSoup/Selenium
```python
# Si HTML statique → BeautifulSoup suffit
# Si JavaScript → Selenium ou Playwright nécessaire

from selenium import webdriver

driver = webdriver.Chrome()
driver.get('https://www.capitoltrades.com/')
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
```

### Étape 3: Implémenter dans edgar_smart_money_analyzer.py
```python
def collect_political_trades(self, days_back: int = 90) -> pd.DataFrame:
    """
    Collecter trades politiques via BeautifulSoup scraping
    """
    logger.info("🕵️ Scraping political trades...")
    
    try:
        # 1. Récupérer HTML
        response = requests.get('https://www.capitoltrades.com/')
        
        # 2. Parser
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 3. Extraire data
        trades = []
        for row in soup.find_all('tr')[1:]:  # Skip header
            cells = row.find_all('td')
            if len(cells) >= 4:
                trades.append({
                    'politician': cells[0].text.strip(),
                    'chamber': cells[1].text.strip(),
                    'ticker': cells[2].text.strip(),
                    'transaction_date': cells[3].text.strip(),
                    # ...
                })
        
        # 4. Retourner DataFrame
        return pd.DataFrame(trades)
        
    except Exception as e:
        logger.error(f"Political scraping error: {e}")
        return pd.DataFrame()
```

---

## 📊 Données Attendues

Format final pour `collect_political_trades()`:

```python
{
    'politician': 'John Smith',
    'chamber': 'Senate',           # ou 'House'
    'ticker': 'AAPL',
    'transaction_date': '2025-12-28',
    'type': 'BUY',                 # ou 'SELL'
    'shares': 1000,                # Optionnel
    'price': 150.50,               # Optionnel
    'transaction_value': 150500,   # Calculé si dispo
}
```

---

## ⚠️ Pièges à Éviter

1. **Rate Limiting**
   ```python
   import time
   time.sleep(1)  # Entre chaque requête
   ```

2. **User-Agent Blocking**
   ```python
   headers = {
       'User-Agent': 'Mozilla/5.0 ...'
   }
   requests.get(url, headers=headers)
   ```

3. **JavaScript Rendering**
   - Si page vide avec BeautifulSoup → faut Selenium
   - Détecté en comparant requests vs Selenium results

4. **Données Incomplètes**
   - Ne pas assumer tous les champs existent
   - Utiliser `.get()` avec defaults
   - Valider data avant insertion

---

## 🎬 Action Demain

### 9h00 - Lancer Investigation
```bash
cd c:\n8n-local-stack
python test_political_scraping.py
```

### 9h30 - Analyser Résultats
- Quel site fonctionne?
- Quelle structure HTML?
- JavaScript ou statique?

### 10h00 - Implémenter
- Adapter `collect_political_trades()`
- Ajouter BeautifulSoup/Selenium au code
- Tester avec petit dataset

### 11h00 - Intégration
- Test notebook complet
- Signaux combinés avec données réelles
- Visualisations finales

---

## 💡 Alternative: Data Local

Si aucun scraping ne fonctionne:

```python
# Créer data_political_trades.csv avec format attendu
# Minimum: politicien, chamber, ticker, date, type

# Ou générer mock data réaliste:
import random
from datetime import timedelta

politicians = ['John Smith', 'Jane Doe', 'Robert Johnson']
chambers = ['Senate', 'House']
tickers = ['AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META']
types = ['BUY', 'SELL']

def generate_mock_political_trades(n=100):
    trades = []
    for _ in range(n):
        trades.append({
            'politician': random.choice(politicians),
            'chamber': random.choice(chambers),
            'ticker': random.choice(tickers),
            'transaction_date': (datetime.now() - timedelta(days=random.randint(0, 90))),
            'type': random.choice(types),
            'transaction_value': random.randint(10000, 1000000)
        })
    return pd.DataFrame(trades)
```

---

## 📌 Notes Importantes

- **Ne pas faire:** Scraper avec force brute (bloquer compte)
- **Ne pas faire:** Ignorer robots.txt
- **À faire:** Utiliser delays respectueux
- **À faire:** Cacher User-Agent réaliste
- **À faire:** Respecter Terms of Service

---

*Plan créé: 2025-12-30*
*À exécuter: 2025-12-31*
