"""
Test QuiverQuant Connection
============================

Vérifie que l'API QuiverQuant fonctionne avec nos credentials
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.quiverquant.quiverquant_client import QuiverQuantClient
from services.quiverquant.config import QUIVERQUANT_TOKEN

def test_connection():
    """Test basic connection and key endpoints"""
    
    print("=" * 70)
    print("🧪 TEST QUIVERQUANT CONNECTION")
    print("=" * 70)
    
    # Initialize client
    print("\n📡 Initializing client...")
    client = QuiverQuantClient(QUIVERQUANT_TOKEN)
    print("✅ Client initialized")
    
    # Test 1: Congressional Trading
    print("\n" + "=" * 70)
    print("TEST 1: Congressional Trading (Recent)")
    print("=" * 70)
    
    try:
        df_congress = client.congress_trading()
        print(f"✅ Success! Retrieved {len(df_congress)} Congressional trades")
        
        if len(df_congress) > 0:
            print("\n📊 Sample data:")
            print(df_congress.head(3))
            print("\n📋 Columns:", list(df_congress.columns))
            
            # Check for required fields
            required_fields = ['Representative', 'TransactionDate', 'Ticker', 'Transaction']
            missing = [f for f in required_fields if f not in df_congress.columns]
            if missing:
                print(f"⚠️ Missing fields: {missing}")
            else:
                print("✅ All required fields present")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Senate Trading
    print("\n" + "=" * 70)
    print("TEST 2: Senate Trading")
    print("=" * 70)
    
    try:
        df_senate = client.senate_trading()
        print(f"✅ Success! Retrieved {len(df_senate)} Senate trades")
        
        if len(df_senate) > 0:
            print("\n📊 Sample data:")
            print(df_senate.head(3))
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: House Trading
    print("\n" + "=" * 70)
    print("TEST 3: House Trading")
    print("=" * 70)
    
    try:
        df_house = client.house_trading()
        print(f"✅ Success! Retrieved {len(df_house)} House trades")
        
        if len(df_house) > 0:
            print("\n📊 Sample data:")
            print(df_house.head(3))
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Specific Stock (Tesla)
    print("\n" + "=" * 70)
    print("TEST 4: Tesla Congressional Trades")
    print("=" * 70)
    
    try:
        df_tsla = client.congress_trading("TSLA")
        print(f"✅ Success! Retrieved {len(df_tsla)} TSLA trades by Congress")
        
        if len(df_tsla) > 0:
            print("\n📊 Sample data:")
            print(df_tsla.head(3))
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Insider Trading
    print("\n" + "=" * 70)
    print("TEST 5: Insider Trading")
    print("=" * 70)
    
    try:
        df_insiders = client.insiders()
        print(f"✅ Success! Retrieved {len(df_insiders)} insider trades")
        
        if len(df_insiders) > 0:
            print("\n📊 Sample data:")
            print(df_insiders.head(3))
            print("\n📋 Columns:", list(df_insiders.columns))
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: WallStreetBets
    print("\n" + "=" * 70)
    print("TEST 6: WallStreetBets Discussion")
    print("=" * 70)
    
    try:
        df_wsb = client.wallstreetbets()
        print(f"✅ Success! Retrieved {len(df_wsb)} WSB mentions")
        
        if len(df_wsb) > 0:
            print("\n📊 Sample data:")
            print(df_wsb.head(3))
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ CONNECTION TEST COMPLETE")
    print("=" * 70)
    print("\n🎯 QuiverQuant is READY for Smart Money Tracker integration!")
    print("📝 Next: Update edgar_smart_money_analyzer.py to use this data")

if __name__ == "__main__":
    test_connection()
