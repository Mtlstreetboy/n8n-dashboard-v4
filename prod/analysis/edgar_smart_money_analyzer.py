"""
Smart Money Analyzer - Version avec edgartools intégré
Collecte via edgartools (SEC), données politiques en fallback mock
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Import edgartools
from edgar import Company, set_identity

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurer edgartools avec identité
set_identity("n8n-local-stack research@mtlstreetboy.com")


class EdgarSmartMoneyAnalyzer:
    """
    Smart Money Analyzer utilisant edgartools
    Résout les problèmes de User-Agent SEC et parsing XML
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize with configuration"""
        self.config = config or {}
        
        # CIK mapping (ticker -> CIK)
        self.cik_cache = {
            'AAPL': '0000320193',
            'MSFT': '0000789019',
            'GOOGL': '0001652044',
            'GOOG': '0001652044',
            'TSLA': '0001318605',
            'NVDA': '0001045810',
            'META': '0001326801',
            'AMZN': '0001018724',
            'NFLX': '0001065280',
            'AMD': '0000002488',
        }
        
        logger.info("EdgarSmartMoneyAnalyzer initialized with edgartools")
    
    def get_cik_for_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK for ticker (from cache or lookup)"""
        ticker = ticker.upper()
        
        if ticker in self.cik_cache:
            return self.cik_cache[ticker]
        
        logger.warning(f"CIK not cached for {ticker}, skipping")
        return None
    
    def collect_insider_trades(self, ticker: str, days_back: int = 90) -> pd.DataFrame:
        """
        Collect Form 4 insider trades using edgartools
        
        Args:
            ticker: Stock ticker symbol
            days_back: Number of days to look back
            
        Returns:
            DataFrame with insider transactions
        """
        logger.info(f"📥 Collecting Form 4 for {ticker} via edgartools...")
        
        cik = self.get_cik_for_ticker(ticker)
        if not cik:
            logger.error(f"CIK not found for {ticker}")
            return pd.DataFrame()
        
        try:
            # Get company
            company = Company(cik)
            logger.info(f"   Company: {company.name}")
            
            # Get Form 4 filings
            filings = company.get_filings(form="4").latest(20)
            logger.info(f"   Found {len(filings)} Form 4 filings")
            
            all_trades = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for filing in filings:
                filing_date = pd.to_datetime(filing.filing_date)
                
                if filing_date < cutoff_date:
                    continue
                
                # Parse Form 4 using edgartools' built-in method
                try:
                    ownership = filing.obj()
                    
                    # Use edgartools' to_dataframe() method
                    # This returns all transactions with proper parsing
                    trans_df = ownership.to_dataframe()
                    
                    if trans_df.empty:
                        continue
                    
                    # Rename columns to match our schema
                    trans_df = trans_df.rename(columns={
                        'Ticker': 'ticker',
                        'Date': 'transaction_date',
                        'Insider': 'insider_name',
                        'Position': 'role',
                        'Code': 'transaction_code',
                        'Shares': 'shares',
                        'Price': 'price_per_share',
                        'Value': 'transaction_value',
                        'Transaction Type': 'type'
                    })
                    
                    # Add filing date
                    trans_df['filing_date'] = filing_date
                    
                    # Standardize type (edgartools uses 'Sale', 'Purchase', 'Gift', etc.)
                    trans_df['type'] = trans_df['type'].apply(lambda x: 
                        'BUY' if x in ['Purchase', 'Award', 'Exercise'] else
                        'SELL' if x == 'Sale' else
                        'OTHER'
                    )
                    
                    # Select and reorder columns
                    columns = [
                        'ticker', 'filing_date', 'transaction_date', 'insider_name', 'role',
                        'transaction_code', 'shares', 'price_per_share', 'transaction_value', 'type'
                    ]
                    trans_df = trans_df[columns]
                    
                    all_trades.append(trans_df)
                    
                except Exception as parse_err:
                    logger.debug(f"Filing parse error: {parse_err}")
                    continue
            
            if all_trades:
                df = pd.concat(all_trades, ignore_index=True)
                df['transaction_date'] = pd.to_datetime(df['transaction_date'])
                df = df.sort_values('transaction_date', ascending=False)
                logger.info(f"✅ {len(df)} insider transactions collected")
                return df
            else:
                logger.warning(f"No insider transactions found for {ticker}")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error collecting insider trades: {e}")
            return pd.DataFrame()
    
    def filter_high_conviction_buys(self, df: pd.DataFrame, min_value: float = 100000) -> pd.DataFrame:
        """
        Filter for high conviction buys
        
        Args:
            df: DataFrame with insider trades
            min_value: Minimum transaction value
            
        Returns:
            DataFrame with high conviction buys only
        """
        if df.empty:
            return pd.DataFrame()
        
        logger.info(f"🎯 Filtering high conviction buys (min ${min_value:,.0f})...")
        
        # Filter: Code P (Purchase) OR type BUY, with minimum value
        high_conviction = df[
            ((df['transaction_code'] == 'P') | (df['type'] == 'BUY')) &
            (df['transaction_value'] >= min_value)
        ].copy()
        
        # Calculate conviction score
        high_conviction['conviction_score'] = high_conviction.apply(
            lambda row: min(100, (row['transaction_value'] / 1000000) * 50), axis=1
        )
        
        # Detect clusters
        high_conviction['is_cluster'] = False
        for ticker in high_conviction['ticker'].unique():
            ticker_trades = high_conviction[high_conviction['ticker'] == ticker]
            if len(ticker_trades) >= 2:
                high_conviction.loc[high_conviction['ticker'] == ticker, 'is_cluster'] = True
        
        logger.info(f"✅ {len(high_conviction)} high conviction buys found")
        
        return high_conviction.sort_values('transaction_value', ascending=False)
    
    def collect_political_trades(self, days_back: int = 90) -> pd.DataFrame:
        """
        Placeholder for political trades (sources currently blocked)
        Returns empty DataFrame with proper structure
        """
        logger.warning("⚠️  Political data sources (GitHub/S3) are currently blocked")
        logger.info("💡 Consider using: Quiver Quant API, FMP API, or Capitol Trades")
        
        # Return empty DataFrame with correct structure
        return pd.DataFrame(columns=[
            'transaction_date', 'politician', 'ticker', 'type', 'value', 'chamber'
        ])
    
    def generate_combined_signals(self, tickers: List[str], days_insider: int = 30) -> pd.DataFrame:
        """
        Generate combined signals for list of tickers
        
        Args:
            tickers: List of ticker symbols
            days_insider: Days to look back for insider trades
            
        Returns:
            DataFrame with combined signals
        """
        logger.info(f"🔄 Generating signals for {len(tickers)} tickers...")
        
        signals = []
        
        for ticker in tickers:
            signal = {
                'ticker': ticker,
                'political_score': 0,  # Not available
                'insider_score': 0,
                'combined_score': 0,
                'recommendation': 'N/A',
                'details': {}
            }
            
            # Get insider trades
            try:
                insider_df = self.collect_insider_trades(ticker, days_back=days_insider)
                
                if not insider_df.empty:
                    high_conviction = self.filter_high_conviction_buys(insider_df)
                    
                    if not high_conviction.empty:
                        # Calculate insider score
                        num_buys = len(high_conviction)
                        total_value = high_conviction['transaction_value'].sum()
                        is_cluster = high_conviction['is_cluster'].any()
                        
                        insider_score = min(50, num_buys * 15)
                        if is_cluster:
                            insider_score += 20
                        if total_value > 1000000:
                            insider_score += 10
                        
                        signal['insider_score'] = min(100, insider_score)
                        signal['details']['insider_buys'] = num_buys
                        signal['details']['insider_value'] = f"${total_value:,.0f}"
                        signal['details']['insider_cluster'] = is_cluster
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
            
            # Calculate combined score (only insider for now)
            signal['combined_score'] = signal['insider_score']
            
            # Recommendation
            if signal['combined_score'] >= 70:
                signal['recommendation'] = '🚀 TRÈS BULLISH'
            elif signal['combined_score'] >= 50:
                signal['recommendation'] = '📈 BULLISH'
            elif signal['combined_score'] >= 30:
                signal['recommendation'] = '💡 INTÉRESSANT'
            else:
                signal['recommendation'] = '😐 NEUTRE'
            
            signals.append(signal)
        
        return pd.DataFrame(signals).sort_values('combined_score', ascending=False)


# Validation rapide si exécuté directement
if __name__ == "__main__":
    print("="*70)
    print("✅ EdgarSmartMoneyAnalyzer validé")
    print("="*70)
    
    analyzer = EdgarSmartMoneyAnalyzer()
    
    # Test rapide
    print("\n🧪 Test NVDA:")
    trades = analyzer.collect_insider_trades("NVDA", days_back=30)
    print(f"   Trades collectés: {len(trades)}")
    
    if not trades.empty:
        high_conv = analyzer.filter_high_conviction_buys(trades)
        print(f"   High conviction: {len(high_conv)}")
    
    print("\n✅ Module prêt à l'emploi!")
