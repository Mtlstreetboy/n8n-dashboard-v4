#!/usr/bin/env python3
"""
Test des sources de données politiques
Senate Stock Watcher (GitHub) et House Stock Watcher (S3)
"""

import requests
import pandas as pd
from datetime import datetime
import json

print("="*70)
print("🏛️  TEST DES SOURCES POLITIQUES")
print("="*70)

# ==================== TEST 1: Senate Stock Watcher (GitHub) ====================
print("\n" + "="*70)
print("📋 TEST 1: Senate Stock Watcher (GitHub)")
print("="*70)

try:
    # URL correcte selon le rapport
    url = "https://raw.githubusercontent.com/dwyl/senate-stock-watcher-data/main/data/all_transactions.json"
    
    print(f"URL: {url}")
    print("Tentative de connexion...")
    
    response = requests.get(url, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
            print(f"✅ SUCCESS - {len(df)} transactions chargées")
            
            if not df.empty:
                print(f"\n📊 Colonnes disponibles:")
                print(f"   {list(df.columns)}")
                
                print(f"\n📋 Aperçu (3 premières lignes):")
                print(df.head(3).to_string())
                
                # Sauvegarder un échantillon
                sample_file = 'local_files/smart_money/senate_sample.csv'
                df.head(100).to_csv(sample_file, index=False)
                print(f"\n💾 Échantillon sauvegardé: {sample_file}")
        else:
            print(f"⚠️  Format inattendu: {type(data)}")
    else:
        print(f"❌ FAILED - HTTP {response.status_code}")
        print(f"   Réponse: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

# ==================== TEST 2: House Stock Watcher (S3) ====================
print("\n" + "="*70)
print("📋 TEST 2: House Stock Watcher (S3)")
print("="*70)

try:
    # URL S3 selon le rapport
    url = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
    
    print(f"URL: {url}")
    print("Tentative de connexion...")
    
    response = requests.get(url, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
            print(f"✅ SUCCESS - {len(df)} transactions chargées")
            
            if not df.empty:
                print(f"\n📊 Colonnes disponibles:")
                print(f"   {list(df.columns)}")
                
                print(f"\n📋 Aperçu (3 premières lignes):")
                print(df.head(3).to_string())
                
                # Sauvegarder un échantillon
                sample_file = 'local_files/smart_money/house_sample.csv'
                df.head(100).to_csv(sample_file, index=False)
                print(f"\n💾 Échantillon sauvegardé: {sample_file}")
        else:
            print(f"⚠️  Format inattendu: {type(data)}")
    else:
        print(f"❌ FAILED - HTTP {response.status_code}")
        print(f"   Réponse: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

# ==================== TEST 3: APIs Alternatives (Quiver, FMP) ====================
print("\n" + "="*70)
print("📋 TEST 3: Vérification URLs Alternatives")
print("="*70)

alternative_sources = [
    ("Senate GitHub (alt)", "https://github.com/dwyl/senate-stock-watcher-data/raw/main/data/all_transactions.json"),
    ("House S3 (alt region)", "https://house-stock-watcher-data.s3.us-west-2.amazonaws.com/data/all_transactions.json"),
]

for name, url in alternative_sources:
    try:
        print(f"\n   Testing: {name}")
        print(f"   URL: {url}")
        response = requests.get(url, timeout=15)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Valid JSON - {len(data) if isinstance(data, list) else 'dict'} items")
            except:
                print(f"   ⚠️  Not JSON")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

# ==================== RÉSUMÉ ====================
print("\n" + "="*70)
print("📊 RÉSUMÉ DES TESTS")
print("="*70)
print("\n💡 SOLUTIONS SI BLOQUÉ:")
print("   1. Utiliser un VPN ou proxy différent")
print("   2. Contacter le fournisseur de données (GitHub/S3)")
print("   3. Utiliser une API commerciale (Quiver Quant, FMP)")
print("   4. Scraper directement les sites officiels Congress.gov")
print("="*70)
