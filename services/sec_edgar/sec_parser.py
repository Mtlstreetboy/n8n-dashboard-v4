"""
SEC EDGAR Form Parser

Extracts detailed transaction and ownership information from SEC Form 4 and Schedule 13D filings.

Task 2.2: XML Parsing for Form 4 and 13D

The SEC provides detailed transaction data in XML format embedded in Form 4 and Schedule 13D filings.
This module handles:

1. Form 4 (Insider Trading):
   - insider_name: Full name of insider
   - insider_title: Position (CEO, Director, VP, etc.)
   - transaction_type: "P" (purchase) or "S" (sale)
   - shares: Number of shares in transaction
   - price_per_share: Transaction price
   - transaction_date: When transaction occurred
   - ownership_after: Total shares owned after transaction
   - ownership_pct: Percent of company owned

2. Schedule 13D (Acquisition / M&A):
   - target_company: Company being acquired/influenced
   - filer_name: Company/entity making acquisition
   - ownership_pct: Percent ownership stake
   - item_4_intent: Intent (control, influence, passive, treasury)
   - item_4_summary: Full Item 4 text

3. Schedule 13G (Beneficial Ownership):
   - Similar to 13D but passive nature
"""

import logging
import requests
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

SEC_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Portfolio Tracker) investsmart/1.0 contact@example.com'
}


class SecParser:
    """Parse detailed information from SEC EDGAR Form 4 and Schedule 13D filings."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(SEC_HEADERS)

    def parse_form4(self, accession: str, company_cik: str) -> Dict:
        """
        Parse Form 4 filing to extract insider transaction details.

        Args:
            accession: Accession number (e.g., "0001199039-25-000015")
            company_cik: CIK of the company being reported on

        Returns:
            Dict with fields:
            - insider_name
            - insider_title
            - transaction_type (P/S)
            - shares
            - price_per_share
            - transaction_date
            - ownership_after
            - ownership_pct

        TODO: Implement XML parsing
        - Locate Form 4 XML file in SEC filing directory
        - Parse <reportingOwner>, <reportingOwnerRelationship>, and <derivativeSecurityTransaction> tags
        - Extract specific fields from XML structure
        """
        logger.info(f"Parsing Form 4: {accession}")

        result = {
            "accession": accession,
            "company_cik": company_cik,
            "form_type": "4",
            "status": "parsing_not_implemented",
            "insider_name": None,
            "insider_title": None,
            "transaction_type": None,
            "shares": None,
            "price_per_share": None,
            "transaction_date": None,
            "ownership_after": None,
            "ownership_pct": None,
        }

        # TODO: Implement actual parsing
        # Step 1: Locate XML file in SEC filing directory
        # Step 2: Download XML content
        # Step 3: Parse XML with ElementTree or BeautifulSoup
        # Step 4: Extract transaction and ownership fields
        # Step 5: Validate and clean data

        return result

    def parse_13d(self, accession: str, company_cik: str) -> Dict:
        """
        Parse Schedule 13D filing to extract M&A activity details.

        Args:
            accession: Accession number
            company_cik: CIK of target company

        Returns:
            Dict with fields:
            - filer_name: Who filed
            - target_company: Company being targeted
            - ownership_pct: Stake percentage
            - item_4_intent: Intent of acquisition
            - item_4_summary: Full Item 4 text
            - shares_held: Number of shares
            - investment_value: USD value

        TODO: Implement XML parsing
        - Parse Item 1 for target company details
        - Parse Item 4 for intent/purpose
        - Extract ownership percentages
        """
        logger.info(f"Parsing Schedule 13D: {accession}")

        result = {
            "accession": accession,
            "company_cik": company_cik,
            "form_type": "13D",
            "status": "parsing_not_implemented",
            "filer_name": None,
            "target_company": None,
            "target_cik": None,
            "ownership_pct": None,
            "item_4_intent": None,
            "item_4_summary": None,
            "shares_held": None,
            "investment_value": None,
        }

        # TODO: Implement actual parsing
        # Step 1: Locate 13D submission files
        # Step 2: Parse Item 1 for target company
        # Step 3: Parse Item 4 for intent classification
        # Step 4: Extract financials (shares, value)
        # Step 5: Cross-reference target CIK

        return result

    def _locate_form4_xml(self, accession: str, company_cik: str) -> Optional[str]:
        """
        Locate Form 4 XML file in SEC EDGAR filing directory.

        SEC EDGAR directory structure:
        /Archives/edgar/CIK_PARENT/CIK_COMPANY/accession_number/

        Returns URL to XML file or None if not found.

        TODO: Test different path patterns and extraction methods
        """
        pass

    def _locate_13d_xml(self, accession: str, company_cik: str) -> Optional[str]:
        """
        Locate Schedule 13D document in SEC EDGAR.

        Returns URL to document or None if not found.
        """
        pass

    @staticmethod
    def classify_13d_intent(item_4_text: str) -> str:
        """
        Classify intent from Schedule 13D Item 4.

        Returns one of:
        - "acquisition_for_control": Seeking control
        - "activist_pressure": Forcing changes
        - "investment_only": Passive investment
        - "passive_parking": Treasury/temporary holding

        TODO: Implement intent classification using text analysis
        Keywords:
        - "control": acquisition_for_control
        - "change", "voting", "board": activist_pressure
        - "investment": investment_only
        - "temporary", "treasury": passive_parking
        """
        pass


# TODO: Additional parsing utilities

def extract_form4_transactions(xml_content: str) -> List[Dict]:
    """
    Extract all transactions from Form 4 XML.

    Returns list of dicts with transaction details.
    """
    pass


def extract_13d_target(xml_content: str) -> Dict:
    """
    Extract target company information from Schedule 13D.

    Returns dict with target_company, target_cik, etc.
    """
    pass
