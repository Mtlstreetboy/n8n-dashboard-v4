#!/usr/bin/env python3
"""
Test rapide du fallback canadien dans collect_options.py
"""
import sys
sys.path.insert(0, 'c:/n8n-local-stack/prod/collection')

from collect_options import OptionsCollector

# Test avec un ticker canadien
collector = OptionsCollector()

print("🧪 TEST DU FALLBACK CANADIEN\n")
print("=" * 60)

# Test avec SHOP.TO (devrait automatiquement basculer sur SHOP)
result = collector.get_options_data("SHOP.TO", days_forward=30)

if result:
    print("\n✅ TEST RÉUSSI!")
    print(f"   Ticker final utilisé: {result['ticker']}")
    print(f"   Calls collectés: {result['calls_count']}")
    print(f"   Puts collectés: {result['puts_count']}")
else:
    print("\n❌ TEST ÉCHOUÉ - Aucune donnée collectée")
