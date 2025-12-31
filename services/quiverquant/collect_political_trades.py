"""
Political Trades Collector via QuiverQuant
===========================================

Collecte automatique des transactions politiques (Congress, Senate, House)
Pour intégration dans Smart Money Tracker
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.quiverquant.quiverquant_client import QuiverQuantClient
from services.quiverquant.config import QUIVERQUANT_TOKEN

# Output directory
OUTPUT_DIR = Path("c:/n8n-local-stack/local_files/smart_money")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def collect_all_political_trades(days_back: int = 90):
    """
    Collecte toutes les transactions politiques
    
    Args:
        days_back: Nombre de jours à remonter
    
    Returns:
        DataFrame consolidé
    """
    print("=" * 70)
    print("🏛️ COLLECTION POLITICAL TRADES VIA QUIVERQUANT")
    print("=" * 70)
    
    # Initialize client
    print("\n📡 Connecting to QuiverQuant...")
    client = QuiverQuantClient(QUIVERQUANT_TOKEN)
    print("✅ Connected")
    
    all_trades = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    # 1. Congressional Trading (combined)
    print("\n" + "=" * 70)
    print("1️⃣ Collecting Congressional Trades (Senate + House)")
    print("=" * 70)
    
    try:
        df_congress = client.congress_trading()
        
        if not df_congress.empty:
            # Filter by date
            df_congress = df_congress[
                pd.to_datetime(df_congress['TransactionDate']) >= cutoff_date
            ]
            
            # Standardize
            df_congress['source'] = 'Congress (Combined)'
            df_congress['chamber'] = df_congress.get('Chamber', 'Unknown')
            
            print(f"✅ Retrieved {len(df_congress)} Congressional trades")
            all_trades.append(df_congress)
            
            # Top politicians
            if len(df_congress) > 0:
                top_politicians = df_congress['Representative'].value_counts().head(5)
                print("\n📊 Most Active Politicians:")
                for pol, count in top_politicians.items():
                    print(f"   - {pol}: {count} trades")
        else:
            print("⚠️ No Congressional data")
    
    except Exception as e:
        print(f"❌ Error collecting Congress: {e}")
    
    # 2. Senate Trading
    print("\n" + "=" * 70)
    print("2️⃣ Collecting Senate Trades")
    print("=" * 70)
    
    try:
        df_senate = client.senate_trading()
        
        if not df_senate.empty:
            df_senate = df_senate[
                pd.to_datetime(df_senate['Date']) >= cutoff_date
            ]
            
            df_senate['source'] = 'Senate'
            df_senate['chamber'] = 'Senate'
            
            print(f"✅ Retrieved {len(df_senate)} Senate trades")
            all_trades.append(df_senate)
        else:
            print("⚠️ No Senate data")
    
    except Exception as e:
        print(f"❌ Error collecting Senate: {e}")
    
    # 3. House Trading
    print("\n" + "=" * 70)
    print("3️⃣ Collecting House Trades")
    print("=" * 70)
    
    try:
        df_house = client.house_trading()
        
        if not df_house.empty:
            df_house = df_house[
                pd.to_datetime(df_house['Date']) >= cutoff_date
            ]
            
            df_house['source'] = 'House'
            df_house['chamber'] = 'House'
            
            print(f"✅ Retrieved {len(df_house)} House trades")
            all_trades.append(df_house)
        else:
            print("⚠️ No House data")
    
    except Exception as e:
        print(f"❌ Error collecting House: {e}")
    
    # Consolidate
    print("\n" + "=" * 70)
    print("📊 Consolidating Data")
    print("=" * 70)
    
    if all_trades:
        df_all = pd.concat(all_trades, ignore_index=True)
        
        # Standardize columns
        column_mapping = {
            'TransactionDate': 'transaction_date',
            'Date': 'transaction_date',
            'ReportDate': 'report_date',
            'Representative': 'politician',
            'Ticker': 'ticker',
            'Transaction': 'transaction_type',
            'Amount': 'amount'
        }
        
        df_all = df_all.rename(columns={k: v for k, v in column_mapping.items() if k in df_all.columns})
        
        # Ensure date format
        if 'transaction_date' in df_all.columns:
            df_all['transaction_date'] = pd.to_datetime(df_all['transaction_date'])
        
        # Sort by date
        df_all = df_all.sort_values('transaction_date', ascending=False)
        
        print(f"\n✅ Total trades collected: {len(df_all)}")
        print(f"📅 Date range: {df_all['transaction_date'].min()} to {df_all['transaction_date'].max()}")
        
        # Top tickers
        if 'ticker' in df_all.columns:
            print("\n📈 Most Traded Tickers:")
            top_tickers = df_all['ticker'].value_counts().head(10)
            for ticker, count in top_tickers.items():
                print(f"   - {ticker}: {count} trades")
        
        # Save to files
        print("\n" + "=" * 70)
        print("💾 Saving Data")
        print("=" * 70)
        
        # CSV
        csv_path = OUTPUT_DIR / f"political_trades_{datetime.now().strftime('%Y%m%d')}.csv"
        df_all.to_csv(csv_path, index=False)
        print(f"✅ Saved CSV: {csv_path}")
        
        # JSON
        json_path = OUTPUT_DIR / f"political_trades_{datetime.now().strftime('%Y%m%d')}.json"
        df_all.to_json(json_path, orient='records', date_format='iso', indent=2)
        print(f"✅ Saved JSON: {json_path}")
        
        # Summary
        summary = {
            'collection_date': datetime.now().isoformat(),
            'total_trades': len(df_all),
            'date_range_days': days_back,
            'sources': df_all['source'].value_counts().to_dict() if 'source' in df_all.columns else {},
            'unique_politicians': df_all['politician'].nunique() if 'politician' in df_all.columns else 0,
            'unique_tickers': df_all['ticker'].nunique() if 'ticker' in df_all.columns else 0,
            'top_tickers': df_all['ticker'].value_counts().head(10).to_dict() if 'ticker' in df_all.columns else {}
        }
        
        summary_path = OUTPUT_DIR / f"political_trades_summary_{datetime.now().strftime('%Y%m%d')}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✅ Saved Summary: {summary_path}")
        
        return df_all
    
    else:
        print("❌ No data collected from any source")
        return pd.DataFrame()

def main():
    """Main execution"""
    try:
        df_trades = collect_all_political_trades(days_back=90)
        
        print("\n" + "=" * 70)
        print("✅ COLLECTION COMPLETE")
        print("=" * 70)
        print(f"\n📊 Total trades: {len(df_trades)}")
        print(f"📁 Data saved to: {OUTPUT_DIR}")
        print("\n🎯 Ready for Smart Money Tracker integration!")
        
    except Exception as e:
        print(f"\n❌ Error in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
