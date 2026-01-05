"""
SEC EDGAR API Client for Smart Money Tracking

Tracks M&A activity (13D), insider trades (Form 4), and institutional positions (13G)
to provide investment signals for portfolio replication.
"""

from .sec_client import SecEdgarClient

__all__ = ['SecEdgarClient']
__version__ = '0.1.0'
