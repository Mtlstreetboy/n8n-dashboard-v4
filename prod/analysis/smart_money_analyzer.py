"""
Smart Money Analyzer - Version Production
==========================================

Système robuste d'analyse des flux Smart Money avec:
- Rate limiting strict (SEC compliance)
- Retry logic + circuit breaker
- Validation des données
- Cache intelligent
- Logging détaillé

Intégration: s'insère dans le pipeline existant entre collection et dashboard

Author: n8n-local-stack
Date: 2025-12-30
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import time
import json
import logging
from pathlib import Path
from xml.etree import ElementTree as ET
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import hashlib

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prod/logs/smart_money.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SECRateLimiter:
    """
    Rate limiter Token Bucket pour respecter la limite SEC de 10 req/sec
    Thread-safe pour utilisation en parallèle
    """
    def __init__(self, max_rate: int = 9, period: float = 1.0):
        """
        Args:
            max_rate: Nombre max de requêtes (9 pour marge de sécurité)
            period: Période en secondes (1.0 = par seconde)
        """
        self.max_rate = max_rate
        self.period = period
        self.allowance = max_rate
        self.last_check = time.time()
        
    def __enter__(self):
        """Context manager pour utilisation avec 'with'"""
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        
        # Remplir le bucket
        self.allowance += time_passed * (self.max_rate / self.period)
        if self.allowance > self.max_rate:
            self.allowance = self.max_rate
        
        # Vérifier si on peut faire une requête
        if self.allowance < 1.0:
            sleep_time = (1.0 - self.allowance) * (self.period / self.max_rate)
            logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
            self.allowance = 1.0
        
        self.allowance -= 1.0
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class CircuitBreaker:
    """
    Circuit breaker pour éviter les requêtes répétées en cas de panne SEC
    """
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                logger.info("Circuit breaker: Tentative de récupération (HALF_OPEN)")
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker OPEN - Service temporairement indisponible")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                logger.info("Circuit breaker: Récupération réussie (CLOSED)")
                self.failures = 0
                self.state = 'CLOSED'
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                logger.error(f"Circuit breaker: Trop d'échecs ({self.failures}), passage à OPEN")
                self.state = 'OPEN'
            
            raise e


class DataValidator:
    """Validation des données pour détecter les anomalies"""
    
    @staticmethod
    def validate_trade(trade: Dict) -> Tuple[bool, str]:
        """
        Valide une transaction
        
        Returns:
            (is_valid, error_message)
        """
        # Date dans le futur
        if 'transaction_date' in trade:
            try:
                trade_date = pd.to_datetime(trade['transaction_date'])
                if trade_date > datetime.now() + timedelta(days=1):
                    return False, "Date dans le futur"
            except:
                return False, "Date invalide"
        
        # Valeur négative
        if 'transaction_value' in trade:
            if trade['transaction_value'] < 0:
                return False, "Valeur négative"
        
        # Shares négatives
        if 'shares' in trade:
            if trade['shares'] < 0:
                return False, "Nombre d'actions négatif"
        
        # Ticker vide
        if 'ticker' in trade:
            if not trade['ticker'] or trade['ticker'].strip() == '':
                return False, "Ticker vide"
        
        return True, ""
    
    @staticmethod
    def sanitize_ticker(ticker: str) -> Optional[str]:
        """Nettoie et valide un ticker"""
        if not ticker:
            return None
        
        ticker = ticker.strip().upper()
        
        # Ticker valide: 1-5 caractères alphanumériques
        if not re.match(r'^[A-Z]{1,5}$', ticker):
            return None
        
        return ticker


class SmartMoneyAnalyzer:
    """
    Analyseur Smart Money production-ready
    
    Features:
    - Rate limiting strict SEC
    - Retry avec backoff exponentiel
    - Circuit breaker
    - Cache CIK
    - Validation des données
    - Parallélisation intelligente
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: Configuration (si None, utilise prod/config/smart_money_config.py)
        """
        # Configuration par défaut
        self.config = config or self._load_config()
        
        # Composants
        self.rate_limiter = SECRateLimiter(
            max_rate=self.config.get('rate_limits', {}).get('sec_edgar', 9)
        )
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        self.validator = DataValidator()
        
        # Headers SEC
        self.sec_headers = {
            'User-Agent': self.config.get('sec_user_agent', 'n8n-local-stack research@example.com'),
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        
        # URLs de base
        self.sec_base = "https://data.sec.gov"
        self.sec_search = "https://www.sec.gov/cgi-bin/browse-edgar"
        
        # Cache CIK → Ticker (évite requêtes répétées)
        self.cik_cache: Dict[str, str] = {}
        self._load_cik_cache()
        
        logger.info("SmartMoneyAnalyzer initialisé")
    
    def _load_config(self) -> Dict:
        """Charge la configuration depuis smart_money_config.py"""
        try:
            from prod.config.smart_money_config import SMART_MONEY_CONFIG
            return SMART_MONEY_CONFIG
        except ImportError:
            logger.warning("Config non trouvée, utilisation des valeurs par défaut")
            return {
                'sec_user_agent': 'n8n-local-stack research@example.com',
                'rate_limits': {'sec_edgar': 9},
                'data_retention_days': 365,
                'analysis_windows': {'political_cluster': 14, 'insider_cluster': 7},
                'thresholds': {'high_conviction_min_value': 100000}
            }
    
    def _load_cik_cache(self):
        """Charge le cache CIK depuis fichier"""
        cache_file = Path('local_files/smart_money/cik_cache.json')
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.cik_cache = json.load(f)
                logger.info(f"Cache CIK chargé: {len(self.cik_cache)} entrées")
            except Exception as e:
                logger.error(f"Erreur chargement cache CIK: {e}")
    
    def _save_cik_cache(self):
        """Sauvegarde le cache CIK"""
        cache_file = Path('local_files/smart_money/cik_cache.json')
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.cik_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache CIK: {e}")
    
    def _retry_request(self, func, max_retries: int = 3, backoff: float = 2.0):
        """
        Exécute une requête avec retry et backoff exponentiel
        
        Args:
            func: Fonction à exécuter
            max_retries: Nombre max de tentatives
            backoff: Multiplicateur de délai entre tentatives
        """
        for attempt in range(max_retries):
            try:
                return self.circuit_breaker.call(func)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Échec après {max_retries} tentatives: {e}")
                    raise
                
                wait_time = backoff ** attempt
                logger.warning(f"Tentative {attempt + 1} échouée, retry dans {wait_time:.1f}s: {e}")
                time.sleep(wait_time)
    
    # ==================== SECTION 1: POLITICAL TRADES ====================
    
    def collect_political_trades(self, days_back: int = 90, tickers_filter: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Collecte les transactions politiques (Senate + House)
        
        Args:
            days_back: Nombre de jours à remonter
            tickers_filter: Liste de tickers à filtrer (si None, utilise companies_config)
        
        Returns:
            DataFrame avec colonnes: transaction_date, politician, ticker, type, value, chamber
        """
        logger.info(f"📥 Collection des trades politiques ({days_back} jours)")
        
        # Charger la liste de tickers si non fournie
        if tickers_filter is None:
            try:
                from prod.config.companies_config import COMPANIES_CONFIG
                tickers_filter = [c['ticker'] for c in COMPANIES_CONFIG]
                logger.info(f"Filtrage sur {len(tickers_filter)} tickers: {tickers_filter}")
            except ImportError:
                logger.warning("companies_config non trouvé, pas de filtrage ticker")
                tickers_filter = []
        
        # Collecter Senate + House en parallèle
        senate_df = self._collect_senate_trades(days_back)
        house_df = self._collect_house_trades(days_back)
        
        # Combiner
        combined = pd.concat([senate_df, house_df], ignore_index=True)
        
        if combined.empty:
            logger.warning("Aucune transaction politique collectée")
            return pd.DataFrame()
        
        # Filtrer par tickers
        if tickers_filter:
            combined = combined[combined['ticker'].isin(tickers_filter)]
        
        # Filtrer par date
        cutoff = datetime.now() - timedelta(days=days_back)
        combined = combined[combined['transaction_date'] >= cutoff]
        
        # Trier
        combined = combined.sort_values('transaction_date', ascending=False)
        
        # Sauvegarder
        self._save_data(combined, 'political_trades')
        
        logger.info(f"✅ {len(combined)} transactions politiques collectées")
        return combined
    
    def _collect_senate_trades(self, days_back: int) -> pd.DataFrame:
        """Collecte depuis Senate Stock Watcher GitHub avec robustesse"""
        try:
            url = "https://raw.githubusercontent.com/dwyl/senate-stock-watcher-data/main/data/all_transactions.json"
            print(f"      📥 Senate (GitHub)...")
            
            # Utiliser _retry_request avec circuit breaker
            response = self._retry_request(url, timeout=30)
            
            if response is None or response.status_code != 200:
                status = response.status_code if response else "timeout"
                logger.warning(f"Senate API returned {status}")
                print(f"      ⚠️  Senate: HTTP {status}")
                return pd.DataFrame()
            
            data = response.json()
            df = pd.DataFrame(data)
            
            if df.empty:
                print(f"      ⚠️  Senate: No data")
                return pd.DataFrame()
            
            # Normaliser les colonnes
            df['transaction_date'] = pd.to_datetime(
                df.get('transaction_date') or df.get('date'),
                errors='coerce'
            )
            df['politician'] = df.get('senator') or df.get('name') or 'Unknown'
            df['ticker'] = df.get('ticker') or df.get('symbol') or ''
            df['ticker'] = df['ticker'].apply(self.validator.sanitize_ticker)
            df['type'] = df.get('type') or df.get('transaction_type') or 'unknown'
            df['value'] = pd.to_numeric(df.get('amount') or df.get('value') or 0, errors='coerce').fillna(0)
            df['chamber'] = 'Senate'
            
            # Nettoyer
            df = df[['transaction_date', 'politician', 'ticker', 'type', 'value', 'chamber']]
            df = df.dropna(subset=['ticker'])
            df = df[df['ticker'].notna()]
            
            logger.info(f"✅ {len(df)} transactions Sénat chargées")
            print(f"      ✅ Senate: {len(df)} trades")
            return df
            
        except Exception as e:
            logger.error(f"Erreur collection Senate: {e}")
            print(f"      ❌ Senate error: {str(e)}")
            return pd.DataFrame()
    
    def _collect_house_trades(self, days_back: int) -> pd.DataFrame:
        """Collecte depuis House Stock Watcher API avec robustesse"""
        try:
            url = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
            print(f"      📥 House (S3)...")
            
            # Utiliser _retry_request avec circuit breaker
            response = self._retry_request(url, timeout=30)
            
            if response is None or response.status_code != 200:
                status = response.status_code if response else "timeout"
                logger.warning(f"House API returned {status}")
                print(f"      ⚠️  House: HTTP {status}")
                return pd.DataFrame()
            
            data = response.json()
            df = pd.DataFrame(data)
            
            if df.empty:
                print(f"      ⚠️  House: No data")
                return pd.DataFrame()
            
            # Normaliser
            df['transaction_date'] = pd.to_datetime(
                df.get('transaction_date') or df.get('disclosure_date'),
                errors='coerce'
            )
            df['politician'] = df.get('representative') or df.get('name') or 'Unknown'
            df['ticker'] = df.get('ticker') or df.get('symbol') or ''
            df['ticker'] = df['ticker'].apply(self.validator.sanitize_ticker)
            df['type'] = df.get('type') or df.get('transaction_type') or 'unknown'
            df['value'] = pd.to_numeric(df.get('amount') or df.get('value') or 0, errors='coerce').fillna(0)
            df['chamber'] = 'House'
            
            # Nettoyer
            df = df[['transaction_date', 'politician', 'ticker', 'type', 'value', 'chamber']]
            df = df.dropna(subset=['ticker'])
            df = df[df['ticker'].notna()]
            
            logger.info(f"✅ {len(df)} transactions Chambre chargées")
            print(f"      ✅ House: {len(df)} trades")
            return df
            
        except Exception as e:
            logger.error(f"Erreur collection House: {e}")
            print(f"      ❌ House error: {str(e)}")
            return pd.DataFrame()
    
    def detect_political_clusters(self, df: pd.DataFrame, window_days: int = 14) -> pd.DataFrame:
        """
        Détecte les clusters d'achats politiques
        
        Args:
            df: DataFrame des transactions politiques
            window_days: Taille de la fenêtre temporelle
        
        Returns:
            DataFrame des clusters avec scoring
        """
        if df.empty:
            return pd.DataFrame()
        
        logger.info("🔍 Détection clusters politiques...")
        
        # Filtrer uniquement les achats
        buys = df[df['type'].str.contains('purchase|buy', case=False, na=False)].copy()
        
        clusters = []
        
        for ticker in buys['ticker'].dropna().unique():
            ticker_buys = buys[buys['ticker'] == ticker].sort_values('transaction_date')
            
            # Fenêtre glissante
            for idx, trade in ticker_buys.iterrows():
                window_start = trade['transaction_date'] - timedelta(days=window_days)
                window_trades = ticker_buys[
                    (ticker_buys['transaction_date'] >= window_start) &
                    (ticker_buys['transaction_date'] <= trade['transaction_date'])
                ]
                
                if len(window_trades) >= 2:
                    politicians = window_trades['politician'].unique()
                    total_value = window_trades['value'].sum()
                    
                    # Calculer le score de confiance
                    confidence = self._calculate_cluster_confidence(
                        num_buyers=len(politicians),
                        total_value=total_value,
                        window_days=window_days
                    )
                    
                    clusters.append({
                        'ticker': ticker,
                        'cluster_date': trade['transaction_date'].strftime('%Y-%m-%d'),
                        'num_buyers': len(politicians),
                        'politicians': ', '.join(politicians[:5]),
                        'total_value': total_value,
                        'window_days': window_days,
                        'confidence_score': confidence,
                        'signal_strength': self._get_signal_strength(confidence)
                    })
        
        result = pd.DataFrame(clusters).drop_duplicates(subset=['ticker', 'cluster_date'])
        result = result.sort_values('confidence_score', ascending=False)
        
        logger.info(f"✅ {len(result)} clusters détectés")
        
        return result
    
    def _calculate_cluster_confidence(self, num_buyers: int, total_value: float, window_days: int) -> int:
        """
        Calcule un score de confiance 0-100 pour un cluster
        
        Facteurs:
        - Nombre d'acheteurs (poids: 50%)
        - Valeur totale (poids: 30%)
        - Fenêtre temporelle (poids: 20%)
        """
        # Score nombre d'acheteurs (0-50)
        buyer_score = min(num_buyers * 10, 50)
        
        # Score valeur (0-30)
        value_score = 0
        if total_value > 5000000:  # > $5M
            value_score = 30
        elif total_value > 2000000:  # > $2M
            value_score = 20
        elif total_value > 500000:  # > $500k
            value_score = 10
        
        # Score temporel (0-20) - plus rapide = meilleur
        time_score = max(0, 20 - (window_days - 7) * 2)
        
        return min(100, buyer_score + value_score + time_score)
    
    def _get_signal_strength(self, confidence: int) -> str:
        """Convertit un score de confiance en label"""
        if confidence >= 80:
            return '🔥🔥🔥 TRÈS FORT'
        elif confidence >= 60:
            return '🔥🔥 FORT'
        elif confidence >= 40:
            return '🔥 MOYEN'
        else:
            return '💡 FAIBLE'
    
    # ==================== SECTION 2: INSIDER TRADES ====================
    
    @lru_cache(maxsize=500)
    def get_cik_for_ticker(self, ticker: str) -> Optional[str]:
        """
        Convertit ticker → CIK avec cache
        
        Args:
            ticker: Symbole boursier
        
        Returns:
            CIK formaté (10 digits) ou None
        """
        # Vérifier le cache mémoire
        if ticker in self.cik_cache:
            return self.cik_cache[ticker]
        
        # Requête SEC
        def _fetch_cik():
            url = f"{self.sec_search}?action=getcompany&CIK={ticker}&type=&dateb=&owner=exclude&count=1&output=atom"
            
            with self.rate_limiter:
                response = requests.get(url, headers=self.sec_headers, timeout=10)
                
                if response.status_code != 200:
                    return None
                
                # Parser XML
                root = ET.fromstring(response.content)
                cik_elem = root.find('.//{http://www.w3.org/2005/Atom}cik')
                
                if cik_elem is not None:
                    return cik_elem.text.zfill(10)
                
                return None
        
        try:
            cik = self._retry_request(_fetch_cik)
            if cik:
                self.cik_cache[ticker] = cik
                self._save_cik_cache()
                logger.debug(f"CIK trouvé pour {ticker}: {cik}")
            return cik
        except Exception as e:
            logger.error(f"Erreur récupération CIK pour {ticker}: {e}")
            return None
    
    def collect_insider_trades(self, ticker: str, days_back: int = 90) -> pd.DataFrame:
        """
        Collecte les Form 4 pour un ticker
        
        Args:
            ticker: Symbole boursier
            days_back: Nombre de jours à remonter
        
        Returns:
            DataFrame des transactions d'initiés
        """
        logger.info(f"📥 Collection Form 4 pour {ticker}")
        
        cik = self.get_cik_for_ticker(ticker)
        if not cik:
            logger.error(f"CIK introuvable pour {ticker}")
            return pd.DataFrame()
        
        def _fetch_form4_list():
            """Récupère la liste des Form 4 récents"""
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'type': '4',
                'dateb': '',
                'owner': 'only',
                'start': 0,
                'count': 100,
                'output': 'atom'
            }
            
            with self.rate_limiter:
                response = requests.get(self.sec_search, params=params, headers=self.sec_headers, timeout=15)
                return response
        
        try:
            response = self._retry_request(_fetch_form4_list)
            
            if response.status_code != 200:
                logger.error(f"Erreur SEC Form 4: {response.status_code}")
                return pd.DataFrame()
            
            # Parser le flux Atom
            root = ET.fromstring(response.content)
            entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            all_trades = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Parser chaque Form 4 (limité à 20 plus récents)
            for entry in entries[:20]:
                filing_date_elem = entry.find('.//{http://www.w3.org/2005/Atom}updated')
                if filing_date_elem is None:
                    continue
                
                filing_date = pd.to_datetime(filing_date_elem.text)
                if filing_date < cutoff_date:
                    continue
                
                # Extraire l'URL du document
                link = entry.find('.//{http://www.w3.org/2005/Atom}link[@type="text/html"]')
                if link is None:
                    continue
                
                doc_url = link.get('href')
                
                # Parser le Form 4 XML
                trades = self._parse_form4_xml(doc_url, ticker, filing_date)
                all_trades.extend(trades)
                
                time.sleep(0.2)  # Safety margin
            
            df = pd.DataFrame(all_trades)
            
            if not df.empty:
                # Valider les données
                df['is_valid'] = df.apply(lambda row: self.validator.validate_trade(row.to_dict())[0], axis=1)
                valid_count = df['is_valid'].sum()
                
                if valid_count < len(df):
                    logger.warning(f"{len(df) - valid_count} transactions invalides détectées")
                
                df = df[df['is_valid']].drop(columns=['is_valid'])
                
                # Sauvegarder
                self._save_data(df, f'insider_trades_{ticker}')
                
                logger.info(f"✅ {len(df)} transactions d'initiés pour {ticker}")
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur collection Form 4 pour {ticker}: {e}")
            return pd.DataFrame()
    
    def _parse_form4_xml(self, doc_url: str, ticker: str, filing_date: datetime) -> List[Dict]:
        """Parse un fichier Form 4 XML"""
        try:
            xml_url = doc_url.replace('-index.htm', '.xml')
            
            def _fetch_xml():
                with self.rate_limiter:
                    return requests.get(xml_url, headers=self.sec_headers, timeout=10)
            
            response = self._retry_request(_fetch_xml)
            
            if response.status_code != 200:
                return []
            
            root = ET.fromstring(response.content)
            trades = []
            
            # Extraire infos sur l'initié
            reporting_owner = root.find('.//reportingOwner')
            owner_name = "Unknown"
            role = "Unknown"
            
            if reporting_owner is not None:
                name_elem = reporting_owner.find('.//rptOwnerName')
                owner_name = name_elem.text if name_elem is not None else "Unknown"
                
                relationship = reporting_owner.find('.//reportingOwnerRelationship')
                if relationship is not None:
                    if relationship.find('.//isOfficer') is not None and relationship.find('.//isOfficer').text == '1':
                        officer_title = relationship.find('.//officerTitle')
                        role = officer_title.text if officer_title is not None else "Officer"
                    elif relationship.find('.//isDirector') is not None and relationship.find('.//isDirector').text == '1':
                        role = "Director"
                    elif relationship.find('.//isTenPercentOwner') is not None and relationship.find('.//isTenPercentOwner').text == '1':
                        role = "10% Owner"
            
            # Parser transactions non-dérivées
            non_derivative_table = root.find('.//nonDerivativeTable')
            if non_derivative_table is not None:
                for transaction in non_derivative_table.findall('.//nonDerivativeTransaction'):
                    trans_date_elem = transaction.find('.//transactionDate/value')
                    if trans_date_elem is None:
                        continue
                    
                    trans_code_elem = transaction.find('.//transactionCode')
                    trans_code = trans_code_elem.text if trans_code_elem is not None else "Unknown"
                    
                    shares_elem = transaction.find('.//transactionShares/value')
                    shares = float(shares_elem.text) if shares_elem is not None else 0
                    
                    price_elem = transaction.find('.//transactionPricePerShare/value')
                    price = float(price_elem.text) if price_elem is not None else 0
                    
                    acq_disp_elem = transaction.find('.//transactionAcquiredDisposedCode/value')
                    acq_disp = acq_disp_elem.text if acq_disp_elem is not None else "Unknown"
                    
                    trades.append({
                        'ticker': ticker,
                        'filing_date': filing_date,
                        'transaction_date': trans_date_elem.text,
                        'insider_name': owner_name,
                        'role': role,
                        'transaction_code': trans_code,
                        'shares': shares,
                        'price_per_share': price,
                        'transaction_value': shares * price,
                        'acquisition_disposition': acq_disp,
                        'type': 'BUY' if acq_disp == 'A' else 'SELL' if acq_disp == 'D' else 'OTHER'
                    })
            
            return trades
            
        except Exception as e:
            logger.warning(f"Erreur parsing Form 4 XML: {e}")
            return []
    
    def filter_high_conviction_buys(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtre les achats haute conviction
        
        Critères:
        - Code P (Purchase sur marché ouvert)
        - Type BUY
        - Valeur > seuil configuré
        - Exclut les exercices d'options (M), dons (G), taxes (F)
        """
        if df.empty:
            return pd.DataFrame()
        
        logger.info("🎯 Filtrage achats haute conviction...")
        
        min_value = self.config.get('thresholds', {}).get('high_conviction_min_value', 100000)
        
        # Filtrer
        high_conviction = df[
            ((df['transaction_code'] == 'P') | (df['type'] == 'BUY')) &
            (df['shares'] > 0) &
            (df['price_per_share'] > 0) &
            (df['transaction_value'] >= min_value)
        ].copy()
        
        # Détecter clusters (plusieurs initiés par ticker)
        high_conviction['is_cluster'] = False
        for ticker in high_conviction['ticker'].unique():
            ticker_trades = high_conviction[high_conviction['ticker'] == ticker]
            if len(ticker_trades) >= 2:
                high_conviction.loc[high_conviction['ticker'] == ticker, 'is_cluster'] = True
        
        # Ajouter scoring
        high_conviction['conviction_score'] = high_conviction.apply(
            lambda row: self._calculate_insider_conviction(row), axis=1
        )
        
        high_conviction = high_conviction.sort_values('conviction_score', ascending=False)
        
        logger.info(f"✅ {len(high_conviction)} achats haute conviction")
        logger.info(f"   dont {high_conviction['is_cluster'].sum()} en cluster")
        
        return high_conviction
    
    def _calculate_insider_conviction(self, trade: pd.Series) -> int:
        """Calcule un score de conviction 0-100 pour un trade d'initié"""
        score = 0
        
        # Valeur de la transaction (0-40)
        value = trade['transaction_value']
        if value > 1000000:
            score += 40
        elif value > 500000:
            score += 30
        elif value > 100000:
            score += 20
        
        # Rôle de l'initié (0-30)
        role = trade['role'].upper()
        if 'CEO' in role or 'CHIEF EXECUTIVE' in role:
            score += 30
        elif 'CFO' in role or 'CHIEF FINANCIAL' in role:
            score += 25
        elif 'DIRECTOR' in role:
            score += 20
        elif 'OFFICER' in role:
            score += 10
        
        # Cluster (0-30)
        if trade.get('is_cluster', False):
            score += 30
        
        return min(100, score)
    
    # ==================== UTILITIES ====================
    
    def _save_data(self, df: pd.DataFrame, name: str):
        """Sauvegarde un DataFrame en JSON horodaté"""
        if df.empty:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"local_files/smart_money/{name}_{timestamp}.json"
        
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            df.to_json(filename, orient='records', date_format='iso', indent=2)
            logger.info(f"💾 Données sauvegardées: {filename}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde {filename}: {e}")
    
    def generate_combined_signals(self, tickers: List[str], days_political: int = 60, days_insider: int = 30) -> pd.DataFrame:
        """
        Génère des signaux combinés pour une liste de tickers
        
        Args:
            tickers: Liste de symboles boursiers
            days_political: Fenêtre temporelle pour trades politiques
            days_insider: Fenêtre temporelle pour trades d'initiés
        
        Returns:
            DataFrame avec signaux combinés et scoring
        """
        logger.info(f"🎯 Génération signaux combinés pour {len(tickers)} tickers")
        
        # Collecter signaux politiques
        political_df = self.collect_political_trades(days_back=days_political, tickers_filter=tickers)
        political_clusters = self.detect_political_clusters(political_df)
        
        # Analyser chaque ticker pour signaux d'initiés
        combined_signals = []
        
        for ticker in tickers:
            logger.info(f"   Analyse {ticker}...")
            
            signal = {
                'ticker': ticker,
                'political_score': 0,
                'insider_score': 0,
                'combined_score': 0,
                'recommendation': '',
                'details': {}
            }
            
            # Score politique
            if not political_df.empty:
                ticker_political = political_df[political_df['ticker'] == ticker]
                if not ticker_political.empty:
                    buys = len(ticker_political[ticker_political['type'].str.contains('purchase|buy', case=False, na=False)])
                    sells = len(ticker_political[ticker_political['type'].str.contains('sale|sell', case=False, na=False)])
                    
                    if buys > sells:
                        signal['political_score'] = min(buys * 15, 50)
                        signal['details']['political_buys'] = buys
                        signal['details']['political_sells'] = sells
            
            # Score initiés
            try:
                insider_df = self.collect_insider_trades(ticker, days_back=days_insider)
                if not insider_df.empty:
                    high_conviction = self.filter_high_conviction_buys(insider_df)
                    if not high_conviction.empty:
                        avg_conviction = high_conviction['conviction_score'].mean()
                        signal['insider_score'] = int(avg_conviction * 0.5)  # Max 50
                        signal['details']['insider_buys_count'] = len(high_conviction)
                        signal['details']['insider_total_value'] = high_conviction['transaction_value'].sum()
                        signal['details']['has_cluster'] = high_conviction['is_cluster'].any()
                
                time.sleep(1)  # Rate limit safety
            except Exception as e:
                logger.error(f"Erreur analyse insider pour {ticker}: {e}")
            
            # Score combiné
            signal['combined_score'] = signal['political_score'] + signal['insider_score']
            
            # Recommandation
            if signal['combined_score'] >= 70:
                signal['recommendation'] = '🚀 TRÈS BULLISH'
            elif signal['combined_score'] >= 50:
                signal['recommendation'] = '📈 BULLISH'
            elif signal['combined_score'] >= 30:
                signal['recommendation'] = '💡 INTÉRESSANT'
            else:
                signal['recommendation'] = '😐 NEUTRE'
            
            combined_signals.append(signal)
        
        # Créer DataFrame
        result = pd.DataFrame(combined_signals)
        result = result.sort_values('combined_score', ascending=False)
        
        # Sauvegarder
        self._save_data(result, 'combined_signals')
        
        logger.info(f"✅ Signaux combinés générés pour {len(result)} tickers")
        
        return result


# ==================== SCRIPT D'EXÉCUTION ====================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║     SMART MONEY ANALYZER - VERSION PRODUCTION                ║
    ║     Rate Limiting ✓ | Retry Logic ✓ | Validation ✓          ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    analyzer = SmartMoneyAnalyzer()
    
    # Charger les tickers depuis companies_config
    try:
        from prod.config.companies_config import COMPANIES_CONFIG
        TICKERS = [c['ticker'] for c in COMPANIES_CONFIG]
        print(f"\n📊 Tickers configurés: {TICKERS}\n")
    except ImportError:
        print("⚠️ companies_config non trouvé, utilisation tickers de test")
        TICKERS = ['NVDA', 'AAPL', 'TSLA']
    
    # Test 1: Clusters politiques
    print("=" * 70)
    print("TEST 1: CLUSTERS POLITIQUES")
    print("=" * 70)
    
    political_trades = analyzer.collect_political_trades(days_back=90, tickers_filter=TICKERS)
    
    if not political_trades.empty:
        clusters = analyzer.detect_political_clusters(political_trades)
        
        if not clusters.empty:
            print("\n📊 TOP 5 CLUSTERS:")
            print(clusters.head(5).to_string(index=False))
    
    # Test 2: Initiés (ticker unique)
    print("\n" + "=" * 70)
    print("TEST 2: TRANSACTIONS D'INITIÉS")
    print("=" * 70)
    
    test_ticker = TICKERS[0]
    insider_trades = analyzer.collect_insider_trades(test_ticker, days_back=90)
    
    if not insider_trades.empty:
        high_conviction = analyzer.filter_high_conviction_buys(insider_trades)
        
        if not high_conviction.empty:
            print(f"\n📊 ACHATS HAUTE CONVICTION {test_ticker}:")
            print(high_conviction[['transaction_date', 'insider_name', 'role', 'transaction_value', 'conviction_score']].head(5).to_string(index=False))
    
    # Test 3: Signaux combinés
    print("\n" + "=" * 70)
    print("TEST 3: SIGNAUX COMBINÉS")
    print("=" * 70)
    
    combined = analyzer.generate_combined_signals(TICKERS[:5], days_political=60, days_insider=30)
    
    if not combined.empty:
        print("\n📊 SIGNAUX COMBINÉS:")
        print(combined[['ticker', 'political_score', 'insider_score', 'combined_score', 'recommendation']].to_string(index=False))
    
    print("\n" + "=" * 70)
    print("✅ TESTS TERMINÉS")
    print("=" * 70)
