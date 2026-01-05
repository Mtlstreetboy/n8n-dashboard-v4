"""
SEC EDGAR API Client

Production-ready client for fetching SEC filings with rate limiting,
caching, and error handling.
"""

import requests
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecEdgarClient:
    """
    Client for SEC EDGAR API to fetch M&A and insider trading data.
    
    Supports:
    - Schedule 13D: Acquisitions >5% ownership
    - Form 4: Insider trading
    - Schedule 13G: Beneficial ownership changes
    
    Features:
    - Rate limiting (configurable req/sec)
    - CIK caching for performance
    - Error handling with retries
    - Investment signal enrichment
    """
    
    def __init__(self, rate_limit: float = 1.0, user_agent: str = None):
        """
        Initialize SEC EDGAR client.
        
        Args:
            rate_limit: Requests per second (1.0 = conservative, 10.0 = max)
            user_agent: Custom User-Agent header (required by SEC)
        """
        self.base_url = "https://data.sec.gov/submissions"
        self.company_tickers_url = "https://www.sec.gov/files/company_tickers.json"
        
        # SEC requires polite User-Agent with contact info
        self.headers = {
            'User-Agent': user_agent or 'n8n-sentiment-dashboard/1.0 (contact: admin@example.com)'
        }
        
        self.rate_limit = rate_limit
        self.last_request_time = 0
        
        # Caching
        self.ticker_to_cik_cache = {}
        self._company_tickers = None
        
        logger.info(f'SecEdgarClient initialized (rate_limit={rate_limit} req/sec)')
    
    def _rate_limit_wait(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        wait_time = (1.0 / self.rate_limit) - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, timeout: int = 10) -> requests.Response:
        """
        Make rate-limited HTTP request with error handling.
        
        Args:
            url: URL to request
            timeout: Request timeout in seconds
        
        Returns:
            Response object
        
        Raises:
            requests.RequestException: If request fails after retries
        """
        self._rate_limit_wait()
        
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            logger.error(f'Timeout accessing {url}')
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f'HTTP error {e.response.status_code}: {url}')
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {type(e).__name__}: {str(e)}')
            raise
    
    def lookup_cik(self, ticker: str) -> Tuple[str, str]:
        """
        Convert ticker symbol to CIK number.
        
        Args:
            ticker: Stock symbol (e.g., 'NVDA', 'PLTR')
        
        Returns:
            Tuple of (CIK, company_name)
        
        Raises:
            ValueError: If ticker not found
        """
        ticker = ticker.upper()
        
        # Check cache first
        if ticker in self.ticker_to_cik_cache:
            return self.ticker_to_cik_cache[ticker]
        
        # Load company tickers file (once per session)
        if self._company_tickers is None:
            logger.info('Loading SEC company tickers database...')
            response = self._make_request(self.company_tickers_url)
            self._company_tickers = response.json()
            logger.info(f'Loaded {len(self._company_tickers)} companies')
        
        # Look up the ticker
        for key, company in self._company_tickers.items():
            if company.get('ticker', '').upper() == ticker:
                cik = str(company.get('cik_str')).zfill(10)
                name = company.get('title')
                
                # Cache it
                self.ticker_to_cik_cache[ticker] = (cik, name)
                logger.debug(f'CIK lookup: {ticker} → {cik} ({name})')
                return cik, name
        
        raise ValueError(f'Ticker {ticker} not found in SEC EDGAR database')
    
    def get_form4_filings(
        self, 
        ticker: str, 
        days: int = 30,
        enrich: bool = True
    ) -> pd.DataFrame:
        """
        Fetch Form 4 filings (insider trading) for a company.
        
        Args:
            ticker: Stock symbol (e.g., 'NVDA')
            days: How many days back to search
            enrich: Add investment signal fields
        
        Returns:
            DataFrame with Form 4 filing metadata
        """
        cik, company_name = self.lookup_cik(ticker)
        cik_padded = cik.zfill(10)
        
        logger.info(f'Fetching Form 4 filings for {ticker} ({company_name})...')
        
        # Fetch submissions for this CIK
        url = f'{self.base_url}/CIK{cik_padded}.json'
        response = self._make_request(url)
        data = response.json()
        
        # Extract Form 4 filings from columnar structure
        recent = data['filings']['recent']
        
        filings = []
        accession_nums = recent.get('accessionNumber', [])
        filing_dates = recent.get('filingDate', [])
        report_dates = recent.get('reportDate', [])
        forms = recent.get('form', [])
        
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        
        for i, form in enumerate(forms):
            if form == '4':  # Form 4 = insider trading
                filing_date = filing_dates[i]
                filing_date_obj = datetime.strptime(filing_date, '%Y-%m-%d').date()
                
                if filing_date_obj >= cutoff_date:
                    filings.append({
                        'ticker': ticker,
                        'company_name': company_name,
                        'accession': accession_nums[i],
                        'filing_date': filing_date,
                        'report_date': report_dates[i],
                        'form_type': form,
                        'sec_url': f'https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession_nums[i].replace("-", "")}',
                    })
        
        df = pd.DataFrame(filings)
        
        if not df.empty and enrich:
            df = self._enrich_form4_signals(df)
        
        logger.info(f'Found {len(df)} Form 4 filings for {ticker} (last {days} days)')
        return df
    
    def _enrich_form4_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add investment signal fields to Form 4 data.
        
        Args:
            df: Raw Form 4 DataFrame
        
        Returns:
            Enriched DataFrame with signal fields
        """
        # Calculate days to filing
        df['filing_date_dt'] = pd.to_datetime(df['filing_date'])
        df['report_date_dt'] = pd.to_datetime(df['report_date'])
        df['days_to_filing'] = (df['filing_date_dt'] - df['report_date_dt']).dt.days
        
        # Add placeholder signal fields (will be populated by parser later)
        df['signal_type'] = 'insider_activity'
        df['signal_strength'] = 'unknown'  # Will be: high/medium/low
        df['actionable'] = True
        df['research_priority'] = 'medium'
        df['conviction_score'] = 5.0  # Default 5/10
        
        # Drop temporary datetime columns
        df = df.drop(['filing_date_dt', 'report_date_dt'], axis=1)
        
        return df
    
    def get_13d_filings(
        self, 
        ticker: str, 
        days: int = 90,
        enrich: bool = True
    ) -> pd.DataFrame:
        """
        Fetch Schedule 13D filings (acquisitions >5%) for a company.
        
        Args:
            ticker: Stock symbol (e.g., 'PLTR')
            days: How many days back to search
            enrich: Add investment signal fields
        
        Returns:
            DataFrame with 13D filing metadata
        """
        cik, company_name = self.lookup_cik(ticker)
        cik_padded = cik.zfill(10)
        
        logger.info(f'Fetching Schedule 13D filings for {ticker} ({company_name})...')
        
        # Fetch submissions for this CIK
        url = f'{self.base_url}/CIK{cik_padded}.json'
        response = self._make_request(url)
        data = response.json()
        
        # Extract 13D filings from columnar structure
        recent = data['filings']['recent']
        
        filings = []
        accession_nums = recent.get('accessionNumber', [])
        filing_dates = recent.get('filingDate', [])
        report_dates = recent.get('reportDate', [])
        forms = recent.get('form', [])
        
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        
        for i, form in enumerate(forms):
            if 'SC 13D' in form or form == '13D':  # Schedule 13D = M&A >5%
                filing_date = filing_dates[i]
                filing_date_obj = datetime.strptime(filing_date, '%Y-%m-%d').date()
                
                if filing_date_obj >= cutoff_date:
                    filings.append({
                        'ticker': ticker,
                        'company_name': company_name,
                        'accession': accession_nums[i],
                        'filing_date': filing_date,
                        'report_date': report_dates[i],
                        'form_type': form,
                        'sec_url': f'https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession_nums[i].replace("-", "")}',
                    })
        
        df = pd.DataFrame(filings)
        
        if not df.empty and enrich:
            df = self._enrich_13d_signals(df)
        
        logger.info(f'Found {len(df)} Schedule 13D filings for {ticker} (last {days} days)')
        return df
    
    def _enrich_13d_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add investment signal fields to Schedule 13D data.
        
        Args:
            df: Raw 13D DataFrame
        
        Returns:
            Enriched DataFrame with signal fields
        """
        # Calculate days to filing
        df['filing_date_dt'] = pd.to_datetime(df['filing_date'])
        df['report_date_dt'] = pd.to_datetime(df['report_date'])
        df['days_to_filing'] = (df['filing_date_dt'] - df['report_date_dt']).dt.days
        
        # Add placeholder signal fields (will be populated by parser later)
        df['signal_type'] = 'acquisition'
        df['signal_strength'] = 'high'  # 13D is always high conviction
        df['actionable'] = True
        df['research_priority'] = 'high'
        df['conviction_score'] = 8.0  # Default 8/10 for M&A
        
        # Drop temporary datetime columns
        df = df.drop(['filing_date_dt', 'report_date_dt'], axis=1)
        
        return df
    
    def get_13g_filings(
        self, 
        ticker: str, 
        days: int = 90,
        enrich: bool = True
    ) -> pd.DataFrame:
        """
        Fetch Schedule 13G filings (beneficial ownership) for a company.
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            days: How many days back to search
            enrich: Add investment signal fields
        
        Returns:
            DataFrame with 13G filing metadata
        """
        cik, company_name = self.lookup_cik(ticker)
        cik_padded = cik.zfill(10)
        
        logger.info(f'Fetching Schedule 13G filings for {ticker} ({company_name})...')
        
        # Fetch submissions for this CIK
        url = f'{self.base_url}/CIK{cik_padded}.json'
        response = self._make_request(url)
        data = response.json()
        
        # Extract 13G filings from columnar structure
        recent = data['filings']['recent']
        
        filings = []
        accession_nums = recent.get('accessionNumber', [])
        filing_dates = recent.get('filingDate', [])
        report_dates = recent.get('reportDate', [])
        forms = recent.get('form', [])
        
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        
        for i, form in enumerate(forms):
            if 'SC 13G' in form or form == '13G':  # Schedule 13G = passive ownership
                filing_date = filing_dates[i]
                filing_date_obj = datetime.strptime(filing_date, '%Y-%m-%d').date()
                
                if filing_date_obj >= cutoff_date:
                    filings.append({
                        'ticker': ticker,
                        'company_name': company_name,
                        'accession': accession_nums[i],
                        'filing_date': filing_date,
                        'report_date': report_dates[i],
                        'form_type': form,
                        'sec_url': f'https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession_nums[i].replace("-", "")}',
                    })
        
        df = pd.DataFrame(filings)
        
        if not df.empty and enrich:
            df = self._enrich_13g_signals(df)
        
        logger.info(f'Found {len(df)} Schedule 13G filings for {ticker} (last {days} days)')
        return df
    
    def _enrich_13g_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add investment signal fields to Schedule 13G data.
        
        Args:
            df: Raw 13G DataFrame
        
        Returns:
            Enriched DataFrame with signal fields
        """
        # Calculate days to filing
        df['filing_date_dt'] = pd.to_datetime(df['filing_date'])
        df['report_date_dt'] = pd.to_datetime(df['report_date'])
        df['days_to_filing'] = (df['filing_date_dt'] - df['report_date_dt']).dt.days
        
        # Add placeholder signal fields (will be populated by parser later)
        df['signal_type'] = 'passive_ownership'
        df['signal_strength'] = 'medium'  # 13G is lower priority than 13D
        df['actionable'] = True
        df['research_priority'] = 'low'
        df['conviction_score'] = 6.0  # Default 6/10 for passive
        
        # Drop temporary datetime columns
        df = df.drop(['filing_date_dt', 'report_date_dt'], axis=1)
        
        return df
    
    def __repr__(self):
        return f'SecEdgarClient(rate_limit={self.rate_limit}, cached_tickers={len(self.ticker_to_cik_cache)})'
