import json
import os

# Input/Output paths
INPUT_FILE = r'local_files/sentiment_analysis/consolidated_sentiment_report.json'
OUTPUT_FILE = r'prod/dashboard/consolidated_sentiment_data.json'

def transform_data():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if it has 'companies' list (Report format)
        if 'companies' in data and isinstance(data['companies'], list):
            dashboard_data = {}
            for company in data['companies']:
                ticker = company['ticker']
                dashboard_data[ticker] = company
            
            print(f"✅ Transformed {len(dashboard_data)} companies from Report format.")
        else:
            # Assume it's already in the right format or valid dictionary
            print("⚠️ Data might already be in dashboard format or structure is unknown.")
            dashboard_data = data

        # Write to dashboard directory
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2)
            
        print(f"💾 Saved to: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    transform_data()
