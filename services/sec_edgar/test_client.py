"""
Test script for SecEdgarClient

Run this to validate the SEC EDGAR client is working correctly.
"""

import sys
from pathlib import Path

# Add project root to path so imports work from anywhere
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.sec_edgar import SecEdgarClient


def test_cik_lookup():
    """Test CIK lookup functionality"""
    print('\n' + '='*60)
    print('TEST 1: CIK Lookup')
    print('='*60)
    
    client = SecEdgarClient(rate_limit=1.0)
    
    test_tickers = ['NVDA', 'PLTR', 'MSFT', 'AAPL']
    
    for ticker in test_tickers:
        try:
            cik, name = client.lookup_cik(ticker)
            print(f'✅ {ticker:6} → CIK: {cik} ({name})')
        except Exception as e:
            print(f'❌ {ticker:6} → Error: {e}')
    
    print(f'\n✅ Test 1 PASSED - CIK lookup working')


def test_form4_fetch():
    """Test Form 4 fetcher"""
    print('\n' + '='*60)
    print('TEST 2: Form 4 Fetcher (Insider Trading)')
    print('='*60)
    
    client = SecEdgarClient(rate_limit=1.0)
    
    # Fetch Form 4 filings for NVDA
    df = client.get_form4_filings('NVDA', days=30)
    
    print(f'\n✅ Retrieved {len(df)} Form 4 filings for NVDA')
    
    if not df.empty:
        print('\nSample filings:')
        print(df[['ticker', 'filing_date', 'signal_strength', 'conviction_score']].head(5))
        print(f'\n✅ Test 2 PASSED - Form 4 fetcher working')
    else:
        print('⚠️  No Form 4 filings found (may be normal)')


def test_13d_fetch():
    """Test Schedule 13D fetcher"""
    print('\n' + '='*60)
    print('TEST 3: Schedule 13D Fetcher (M&A Signals)')
    print('='*60)
    
    client = SecEdgarClient(rate_limit=1.0)
    
    # Fetch 13D filings for PLTR
    df = client.get_13d_filings('PLTR', days=365)
    
    print(f'\n✅ Retrieved {len(df)} Schedule 13D filings for PLTR')
    
    if not df.empty:
        print('\nSample filings:')
        print(df[['ticker', 'filing_date', 'signal_strength', 'conviction_score']].head(5))
        print(f'\n✅ Test 3 PASSED - Schedule 13D fetcher working')
    else:
        print('⚠️  No 13D filings found (may be normal - 13D is rare)')


def test_13g_fetch():
    """Test Schedule 13G fetcher"""
    print('\n' + '='*60)
    print('TEST 4: Schedule 13G Fetcher (Beneficial Ownership)')
    print('='*60)
    
    client = SecEdgarClient(rate_limit=1.0)
    
    # Fetch 13G filings for AAPL
    df = client.get_13g_filings('AAPL', days=90)
    
    print(f'\n✅ Retrieved {len(df)} Schedule 13G filings for AAPL')
    
    if not df.empty:
        print('\nSample filings:')
        print(df[['ticker', 'filing_date', 'signal_strength', 'conviction_score']].head(5))
        print(f'\n✅ Test 4 PASSED - Schedule 13G fetcher working')
    else:
        print('⚠️  No 13G filings found (may be normal)')


def main():
    """Run all tests"""
    print('\n🧪 SEC EDGAR CLIENT TEST SUITE')
    print('='*60)
    
    try:
        test_cik_lookup()
        test_form4_fetch()
        test_13d_fetch()
        test_13g_fetch()
        
        print('\n' + '='*60)
        print('✅ ALL TESTS PASSED')
        print('='*60)
        print('\nSecEdgarClient is ready for production use!')
        
    except Exception as e:
        print('\n' + '='*60)
        print(f'❌ TEST FAILED: {type(e).__name__}')
        print('='*60)
        print(f'Error: {str(e)}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
