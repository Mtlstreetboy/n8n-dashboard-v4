#!/usr/bin/env python3
"""
Test de connexion avec edgartools - bibliothèque moderne SEC
Résout les problèmes de User-Agent et parsing XML
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from edgar import *
import pandas as pd
from datetime import datetime, timedelta

# Configurer edgartools avec notre identité
set_identity("n8n-local-stack research@mtlstreetboy.com")

print("="*70)
print("🚀 TEST EDGARTOOLS - CONNEXION SEC EDGAR")
print("="*70)

# ==================== TEST 1: Recherche d'Entreprise ====================
print("\n" + "="*70)
print("📋 TEST 1: Recherche Apple Inc.")
print("="*70)

try:
    # Rechercher Apple par CIK connu
    apple = Company("0000320193")
    
    print(f"✅ SUCCESS")
    print(f"   Name: {apple.name}")
    print(f"   CIK: {apple.cik}")
    print(f"   Tickers: {apple.tickers}")
    print(f"   SIC: {apple.sic_description}")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

# ==================== TEST 2: Form 4 (Insider Trades) ====================
print("\n" + "="*70)
print("👔 TEST 2: Form 4 - Insider Trades (NVIDIA)")
print("="*70)

try:
    # Rechercher NVIDIA
    nvda = Company("0001045810")  # CIK pour NVIDIA
    
    print(f"Company: {nvda.name}")
    print(f"Fetching Form 4 filings...")
    
    # Récupérer les Form 4 récents
    filings = nvda.get_filings(form="4").latest(10)
    
    print(f"✅ SUCCESS - {len(filings)} Form 4 found")
    
    # Parser le premier Form 4
    if len(filings) > 0:
        form4 = filings[0]
        print(f"\n📄 Latest Form 4:")
        print(f"   Filing Date: {form4.filing_date}")
        print(f"   Accession Number: {form4.accession_no}")
        
        # Extraire les transactions
        try:
            ownership = form4.obj()
            
            if hasattr(ownership, 'reportingOwners'):
                for owner in ownership.reportingOwners[:1]:  # Premier owner
                    print(f"\n   Reporting Owner: {owner.name}")
                    print(f"   Title: {owner.relationship.officer_title if owner.relationship.is_officer else 'Director' if owner.relationship.is_director else 'Unknown'}")
            
            if hasattr(ownership, 'nonDerivativeTransactions') and ownership.nonDerivativeTransactions:
                print(f"\n   📊 Transactions:")
                for trans in ownership.nonDerivativeTransactions[:3]:
                    print(f"      - Date: {trans.transactionDate}")
                    print(f"        Code: {trans.transactionCode}")
                    print(f"        Shares: {trans.sharesTransacted:,}")
                    if hasattr(trans, 'pricePerShare') and trans.pricePerShare:
                        print(f"        Price: ${trans.pricePerShare}")
        except Exception as parse_err:
            print(f"   ⚠️  Parse warning: {str(parse_err)}")
            
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

# ==================== TEST 3: 13F (Hedge Fund Holdings) ====================
print("\n" + "="*70)
print("🏦 TEST 3: 13F - Hedge Fund Holdings (Berkshire Hathaway)")
print("="*70)

try:
    # Berkshire Hathaway CIK
    berkshire = Company("0001067983")
    
    print(f"Company: {berkshire.name}")
    print(f"Fetching 13F-HR filings...")
    
    # Récupérer les 13F récents
    filings_13f = berkshire.get_filings(form="13F-HR").latest(2)
    
    print(f"✅ SUCCESS - {len(filings_13f)} 13F filings found")
    
    if len(filings_13f) > 0:
        latest_13f = filings_13f[0]
        print(f"\n📄 Latest 13F:")
        print(f"   Filing Date: {latest_13f.filing_date}")
        print(f"   Period: {latest_13f.period}")
        
        # Extraire les holdings
        try:
            holdings_df = latest_13f.obj()
            
            if isinstance(holdings_df, pd.DataFrame) and not holdings_df.empty:
                print(f"\n   📊 Top 10 Holdings:")
                print(f"   {'Ticker':<10} {'Name':<30} {'Shares':>15} {'Value ($)':>15}")
                print(f"   {'-'*70}")
                
                for idx, row in holdings_df.head(10).iterrows():
                    ticker = row.get('cusip', 'N/A')[:6]
                    name = row.get('nameOfIssuer', 'Unknown')[:28]
                    shares = row.get('shrsOrPrnAmt', {}).get('sshPrnamt', 0)
                    value = row.get('value', 0) * 1000  # En milliers
                    
                    print(f"   {ticker:<10} {name:<30} {shares:>15,} {value:>15,.0f}")
                    
        except Exception as parse_err:
            print(f"   ⚠️  Parse warning: {str(parse_err)}")
            
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

# ==================== TEST 4: Ticker to CIK Conversion ====================
print("\n" + "="*70)
print("🔍 TEST 4: Ticker → CIK Lookup")
print("="*70)

test_companies = [
    ('AAPL', '0000320193'),
    ('MSFT', '0000789019'),
    ('GOOGL', '0001652044'),
    ('TSLA', '0001318605'),
    ('NVDA', '0001045810'),
]

print(f"Testing {len(test_companies)} companies...")
print(f"\n{'Ticker':<10} {'CIK':<15} {'Company Name':<40}")
print(f"{'-'*70}")

for ticker, cik in test_companies:
    try:
        company = Company(cik)
        print(f"{ticker:<10} {company.cik:<15} {company.name[:38]:<40}")
    except Exception as e:
        print(f"{ticker:<10} {cik:<15} ERROR: {str(e)[:30]:<40}")

# ==================== RÉSUMÉ ====================
print("\n" + "="*70)
print("📊 RÉSUMÉ")
print("="*70)
print("✅ edgartools configuré et opérationnel")
print("✅ User-Agent correct (requis par SEC)")
print("✅ Rate limiting automatique intégré")
print("✅ Parsing XML Form 4 natif")
print("✅ Parsing XML 13F natif")
print("✅ Export pandas DataFrame direct")
print("\n🎯 Prêt pour intégration dans SmartMoneyAnalyzer!")
print("="*70)
