#!/usr/bin/env python3
"""
Génère consolidated_sentiment_data.json à partir des fichiers v4 générés
Filtre seulement les tickers présents dans companies_config.py
Utilisé par dashboard_v4_split.html pour charger les données dynamiquement
"""
import sys
import os
import json
import glob
from pathlib import Path

# Environment Detection
if os.path.exists('/data/scripts'):
    sys.path.insert(0, '/data/scripts')
    SENTIMENT_DIR = '/data/sentiment_analysis'
    OUTPUT_FILE = '/data/sentiment_analysis/consolidated_sentiment_data.json'
    from config.companies_config import get_all_companies
else:
    # Local Windows
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR) # Fix: prod -> n8n-local-stack (1 level up, not 2)
    SENTIMENT_DIR = os.path.join(PROJECT_ROOT, 'local_files', 'sentiment_analysis')
    OUTPUT_FILE = os.path.join(SENTIMENT_DIR, 'consolidated_sentiment_data.json')
    sys.path.append(PROJECT_ROOT)
    from prod.config.companies_config import get_all_companies

def load_sentiment_files():
    """Charge les fichiers *_latest_v4.json pour les tickers de la config uniquement"""
    data = {}
    
    # Récupérer les tickers configurés
    configured_tickers = {c['ticker'] for c in get_all_companies()}
    print(f"🎯 Tickers configurés: {len(configured_tickers)}")
    print(f"   {', '.join(sorted(configured_tickers))}\n")
    
    # Chercher tous les fichiers de sentiment v4
    pattern = os.path.join(SENTIMENT_DIR, '*_latest_v4.json')
    files = glob.glob(pattern)
    
    print(f"📂 Cherchant des fichiers dans: {SENTIMENT_DIR}")
    print(f"📊 Fichiers disponibles: {len(files)}\n")
    
    loaded = 0
    skipped = 0
    
    for filepath in sorted(files):
        try:
            ticker = os.path.basename(filepath).replace('_latest_v4.json', '')
            
            # Filtrer: ne charger que les tickers configurés
            if ticker not in configured_tickers:
                skipped += 1
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)
                data[ticker] = content
                loaded += 1
                print(f"✅ {ticker}: Chargé")
        except Exception as e:
            print(f"❌ {ticker}: Erreur - {str(e)}")
    
    print(f"\n📊 Résumé:")
    print(f"   ✅ Chargés: {loaded}")
    print(f"   ⏭️ Ignorés (non-configurés): {skipped}")
    
    return data

def save_consolidated(data):
    """Sauvegarde les données consolidées en JSON"""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    file_size = os.path.getsize(OUTPUT_FILE) / 1024 / 1024
    print(f"\n✅ Consolidé: {OUTPUT_FILE}")
    print(f"📦 Taille: {file_size:.2f} MB")
    print(f"📊 Tickers: {len(data)}")

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 GÉNÉRATION DONNÉES CONSOLIDÉES POUR DASHBOARD")
    print("=" * 80 + "\n")
    
    data = load_sentiment_files()
    
    if data:
        save_consolidated(data)
        print("\n✅ Données prêtes pour le dashboard!")
    else:
        print("\n❌ Aucun fichier de sentiment trouvé!")
        sys.exit(1)


def save_consolidated(data):
    """Sauvegarde les données consolidées en JSON"""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    file_size = os.path.getsize(OUTPUT_FILE) / 1024 / 1024
    print(f"\n✅ Consolidé: {OUTPUT_FILE}")
    print(f"📦 Taille: {file_size:.2f} MB")
    print(f"📊 Tickers: {len(data)}")

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 GÉNÉRATION DONNÉES CONSOLIDÉES POUR DASHBOARD")
    print("=" * 80 + "\n")
    
    data = load_sentiment_files()
    
    if data:
        save_consolidated(data)
        print("\n✅ Données prêtes pour le dashboard!")
    else:
        print("\n❌ Aucun fichier de sentiment trouvé!")
        sys.exit(1)
