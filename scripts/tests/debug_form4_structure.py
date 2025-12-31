"""
Debug script to inspect Form 4 XML structure from edgartools
"""
from edgar import Company, set_identity

# Configure SEC identity
set_identity("n8n-local-stack research@mtlstreetboy.com")

# Get NVDA filings
print("Fetching NVIDIA Form 4 filings...")
company = Company("0001045810")  # NVIDIA CIK
filings = company.get_filings(form="4").latest(5)

print(f"Found {len(filings)} Form 4 filings\n")

# Inspect first filing in detail
if len(filings) > 0:
    filing = filings[0]
    print(f"Filing Date: {filing.filing_date}")
    print(f"Accession: {filing.accession_no}")
    
    try:
        # Get the ownership document object
        ownership = filing.obj()
        
        print("\n=== OWNERSHIP OBJECT ATTRIBUTES ===")
        print(f"Type: {type(ownership)}")
        print(f"Dir: {dir(ownership)}")
        
        # Try to access reporting owner
        if hasattr(ownership, 'reportingOwner'):
            print("\n=== REPORTING OWNER (singular) ===")
            print(f"Type: {type(ownership.reportingOwner)}")
            print(f"Data: {ownership.reportingOwner}")
            
        if hasattr(ownership, 'reportingOwners'):
            print("\n=== REPORTING OWNERS (plural) ===")
            print(f"Type: {type(ownership.reportingOwners)}")
            print(f"Count: {len(ownership.reportingOwners) if hasattr(ownership.reportingOwners, '__len__') else 'N/A'}")
            if ownership.reportingOwners:
                owner = ownership.reportingOwners[0] if isinstance(ownership.reportingOwners, list) else ownership.reportingOwners
                print(f"First Owner Type: {type(owner)}")
                print(f"First Owner Dir: {dir(owner)}")
                print(f"First Owner Data: {owner}")
        
        # Try to access transactions
        if hasattr(ownership, 'nonDerivativeTransaction'):
            print("\n=== NON-DERIVATIVE TRANSACTION (singular) ===")
            print(f"Type: {type(ownership.nonDerivativeTransaction)}")
            print(f"Data: {ownership.nonDerivativeTransaction}")
            
        if hasattr(ownership, 'nonDerivativeTransactions'):
            print("\n=== NON-DERIVATIVE TRANSACTIONS (plural) ===")
            print(f"Type: {type(ownership.nonDerivativeTransactions)}")
            print(f"Data: {ownership.nonDerivativeTransactions}")
            
        if hasattr(ownership, 'nonDerivativeTable'):
            print("\n=== NON-DERIVATIVE TABLE ===")
            print(f"Type: {type(ownership.nonDerivativeTable)}")
            print(f"Data: {ownership.nonDerivativeTable}")
            
        if hasattr(ownership, 'derivativeTransaction'):
            print("\n=== DERIVATIVE TRANSACTION (singular) ===")
            print(f"Type: {type(ownership.derivativeTransaction)}")
            
        if hasattr(ownership, 'derivativeTransactions'):
            print("\n=== DERIVATIVE TRANSACTIONS (plural) ===")
            print(f"Type: {type(ownership.derivativeTransactions)}")
            
        # Print full object for inspection
        print("\n=== FULL OWNERSHIP OBJECT ===")
        print(ownership)
        
        # Try the easier methods
        print("\n=== USING to_dataframe() METHOD ===")
        try:
            df = ownership.to_dataframe()
            print(f"DataFrame shape: {df.shape}")
            print("\nDataFrame columns:")
            print(df.columns.tolist())
            print("\nDataFrame head:")
            print(df.head())
        except Exception as e:
            print(f"to_dataframe() error: {e}")
        
        # Try market_trades
        print("\n=== MARKET TRADES ===")
        try:
            trades = ownership.market_trades
            print(f"Type: {type(trades)}")
            print(f"Data: {trades}")
        except Exception as e:
            print(f"market_trades error: {e}")
        
        # Try reporting_owners
        print("\n=== REPORTING OWNERS ===")
        try:
            owners = ownership.reporting_owners
            print(f"Type: {type(owners)}")
            print(f"Count: {len(owners) if hasattr(owners, '__len__') else 'N/A'}")
            if owners:
                print(f"First owner: {owners[0]}")
        except Exception as e:
            print(f"reporting_owners error: {e}")
        
    except Exception as e:
        print(f"Error parsing filing: {e}")
        import traceback
        traceback.print_exc()
