#!/usr/bin/env python3
"""
Test du batch loader v2 sur un seul ticker
"""
import sys
sys.path.insert(0, '/data/scripts')

from batch_loader_v2 import process_single_ticker

# Test sur NVDA
test_company = {
    'ticker': 'NVDA',
    'name': 'NVIDIA Corporation',
    'search_terms': ['NVIDIA', 'NVDA', 'Jensen Huang']
}

print("🧪 TEST BATCH LOADER V2 - TICKER UNIQUE")
print("="*80)

result = process_single_ticker(test_company, days=30)  # 30 jours pour test rapide

print("\n" + "="*80)
print("📊 RÉSULTAT DU TEST:")
print("="*80)

if result.get('success'):
    print(f"✅ Succès!")
    print(f"   🆕 Nouveaux articles: {result.get('new', 0)}")
    print(f"   📚 Total articles: {result.get('total', 0)}")
    print(f"   📊 Qualité: {result.get('confidence_score', 0):.1f}/100")
    print(f"   ⏱️ Durée: {result.get('duration', 0):.1f}s")
    print(f"   ❌ Erreurs: {result.get('errors', 0)}")
else:
    print(f"❌ Échec: {result.get('error', 'Unknown')}")

print("="*80)
