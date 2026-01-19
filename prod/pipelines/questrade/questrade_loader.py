import requests
import json
import os
import argparse
import sys
from datetime import datetime

# Configuration
TOKEN_STORE_PATH = os.path.join(os.path.dirname(__file__), 'token_store.json')
HOLDINGS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/portfolio_holdings.json'))

class QuestradeClient:
    def __init__(self):
        self.api_server = None
        self.access_token = None
        self.refresh_token = None
        self.load_tokens()

    def load_tokens(self):
        """Load tokens from local storage"""
        if os.path.exists(TOKEN_STORE_PATH):
            try:
                with open(TOKEN_STORE_PATH, 'r') as f:
                    data = json.load(f)
                    self.api_server = data.get('api_server')
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    print("loaded tokens from disk")
            except Exception as e:
                print(f"Error loading tokens: {e}")

    def save_tokens(self, data):
        """Save tokens to local storage"""
        with open(TOKEN_STORE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        
        self.api_server = data.get('api_server')
        self.access_token = data.get('access_token')
        self.refresh_token = data.get('refresh_token')
        print(f"Tokens saved. Api Server: {self.api_server}")

    def exchange_code(self, refresh_token):
        """Exchange Refresh Token for new Access Token (Login)"""
        # Clean token
        refresh_token = refresh_token.strip()
        
        # Validate token format (should be alphanumeric)
        if not refresh_token or not refresh_token.replace('_', '').replace('-', '').isalnum():
            print(f"Error: Invalid token format")
            return False
        
        # URL for token exchange (Base URL from docs)
        base_url = "https://login.questrade.com/oauth2/token"
        
        # Params
        params = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"Exchanging token (Length: {len(refresh_token)})...")
        print(f"Token preview: {refresh_token[:10]}...")
        
        # Try with params in URL (as per Questrade docs)
        try:
            print("Attempting GET request (params in URL)...")
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Success! Got JSON response with keys: {list(data.keys())}")
                    
                    # Validate required fields
                    if 'access_token' in data and 'api_server' in data:
                        self.save_tokens(data)
                        return True
                    else:
                        print(f"Missing required fields. Response: {data}")
                        return False
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON. Response starts with: {response.text[:200]}")
                    print("This usually means the request was blocked by a security challenge or the token is invalid")
                    print(f"\nDEBUG INFO:")
                    print(f"  - Status Code: {response.status_code}")
                    print(f"  - Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                    print(f"  - Response Length: {len(response.text)} chars")
                    return False
            else:
                print(f"Request failed with status {response.status_code}")
                print(f"Response starts with: {response.text[:200]}")
                return False
                
        except requests.Timeout:
            print("Error: Request timed out (10s)")
            return False
        except Exception as e:
            print(f"Exception during request: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_accounts(self):
        """Get list of accounts"""
        headers = {'Authorization': f'Bearer {self.access_token}'}
        url = f"{self.api_server}/v1/accounts"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()['accounts']
        else:
            print(f"Error fetching accounts: {response.text}")
            return []

    def get_positions(self, account_id):
        """Get positions for a specific account"""
        headers = {'Authorization': f'Bearer {self.access_token}'}
        url = f"{self.api_server}/v1/accounts/{account_id}/positions"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()['positions']
        else:
            print(f"Error fetching positions: {response.text}")
            return []

    def map_symbol(self, symbol, symbol_id):
        """
        Map Questrade symbol to Yahoo Finance format.
        This is tricky as Questrade returns 'SU', we need 'SU.TO' if it's on TSX.
        We might need to check 'listingExchange' (missing in simple positions call, might need symbol search).
        For now, let's look at the symbol ID or naming convention.
        
        Better approach: Use the 'symbol' field. Checks if it looks like a Canadian stock.
        Common rule: if exchange is 'TSX' or 'TSXV' -> append .TO or .V
        """
        # Note: 'positions' response contains 'symbol' (e.g., 'TH.TO' or just 'TH'?)
        # Actually Questrade returns 'symbol' like 'TH.TO' often for TSX? No, usually just 'TH'.
        # We need to fetch symbol details strictly speaking, but let's try a heuristic first.
        
        # Let's request symbol info if needed. For now, let's trust the ticker if it matches existing holding.
        return symbol

    def update_portfolio_json(self, all_positions):
        """
        Update local holdings JSON with Questrade Data.
        Logic:
        - Iterate over Questrade positions.
        - Normalize Symbol (add .TO if needed).
        - Create list of holdings.
        - Write to file.
        """
        new_holdings = []
        
        print(f"Processing {len(all_positions)} raw positions...")
        
        for p in all_positions:
            # Data from Questrade
            symbol = p['symbol'] # e.g. "VOO", "SU"
            qty = p['openQuantity']
            avg_price = p['averageEntryPrice']
            current_price = p['currentPrice']
            
            # Simple Heuristic for .TO (Can be improved with ID lookup)
            # If the ID is high numeric, it doesn't help.
            # We assume user primarily trades US or CAD.
            
            # Helper: Check if this symbol exists in old file to preserve suffix
            # (Crude but effective for stability)
            final_ticker = symbol
            
            # Detect if it's likely Canadian (avg price checks? No)
            # Let's assume if it is NOT found in Yahoo without suffix, try .TO?
            # Actually, let's keep it simple: Questrade usually returns "SU" for Suncor. 
            # We want "SU.TO".
            
            # Hardcoded check for known CAD stocks in user portfolio or simple API check?
            # Let's add a "smart suffix" later. For now, let's rely on standard logic:
            # If symbol contains space or dot?
            
            # QUEST Ticker Format: "SU" (TSX), "VOO" (NYSE)
            # We need to distinguish.
            
            # Fetch symbol info to be sure (Optionally).
            # For this MVP, let's assume duplication:
            # If the user held "SU.TO" before, and we find "SU", we map it to "SU.TO".
            
            # Let's load existing file to check for preferred suffixes for this ticker base.
            
            market_value = qty * current_price
            
            new_holdings.append({
                "ticker": final_ticker,
                "qty": qty,
                "avg_price": avg_price,
                "currentPrice": current_price,
                "currentMarketValue": market_value
            })
            
        # Write
        with open(HOLDINGS_PATH, 'w') as f:
            json.dump(new_holdings, f, indent=4)
        
        print(f"Successfully updated {HOLDINGS_PATH} with {len(new_holdings)} holdings.")

def main():
    parser = argparse.ArgumentParser(description='Questrade Portfolio Loader')
    parser.add_argument('--token', type=str, help='Manual Refresh Token (Start with string)')
    args = parser.parse_args()

    client = QuestradeClient()

    # 1. Authenticate
    if args.token:
        # Manual Interaction
        print(f"Authenticating with manual token...")
        if not client.exchange_code(args.token):
            return
    elif client.refresh_token:
        # Refresh Flow
        print(f"Refreshing specific token...")
        if not client.exchange_code(client.refresh_token):
            print("Refresh failed. Please generate a new manual token.")
            return
    else:
        print("No token found. Provide --token <MANUAL_TOKEN>")
        return

    # 2. Fetch Data
    accounts = client.get_accounts()
    print(f"Found {len(accounts)} accounts.")
    
    all_positions = []
    
    for acc in accounts:
        acc_id = acc['number']
        acc_type = acc['type']
        print(f"Fetching positions for Account {acc_id} ({acc_type})...")
        
        positions = client.get_positions(acc_id)
        print(f"  -> Found {len(positions)} positions.")
        all_positions.extend(positions)

    # 3. Update File
    if all_positions:
        client.update_portfolio_json(all_positions)
        print("DEBUG: Raw Positions extracted:")
        for p in all_positions:
            print(f" - {p['symbol']} : {p['openQuantity']} @ ${p['averageEntryPrice']}")
            
        print("\nTo overwrite portfolio_holdings.json, uncomment the update line in script.")
    else:
        print("No positions found.")

if __name__ == "__main__":
    main()
