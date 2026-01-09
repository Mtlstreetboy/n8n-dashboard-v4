import os
import json
import glob

# Paths
SOURCE_DIR = r"c:\n8n-local-stack\local_files\sentiment_analysis"
DEST_FILE = r"c:\n8n-local-stack\prod\dashboard\consolidated_sentiment_data.json"

def regenerate_dashboard_data():
    print(f"Reading sentiment files from {SOURCE_DIR}...")
    
    # Pattern to match latest V4 files
    pattern = os.path.join(SOURCE_DIR, "*_latest_v4.json")
    files = glob.glob(pattern)
    
    consolidated_data = {}
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            ticker = data.get('ticker')
            if ticker:
                consolidated_data[ticker] = data
                print(f"  Loaded {ticker}")
        except Exception as e:
            print(f"  Error reading {file_path}: {e}")
            
    print(f"Total tickers loaded: {len(consolidated_data)}")
    
    # Save to dashboard directory
    print(f"Saving to {DEST_FILE}...")
    with open(DEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(consolidated_data, f, indent=2)
        
    print("Done!")

if __name__ == "__main__":
    regenerate_dashboard_data()
