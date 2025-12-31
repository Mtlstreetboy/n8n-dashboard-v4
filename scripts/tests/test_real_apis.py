#!/usr/bin/env python3
"""
Test des vraies connexions API pour Smart Money Tracker
Teste: Senate GitHub, House S3, SEC EDGAR
"""

import requests
import json
from datetime import datetime, timedelta
import time
import pandas as pd
from typing import Optional, Dict, List

class RealAPITester:
    """Teste les vraies connexions aux APIs"""
    
    def __init__(self):
        self.results = {
            'senate_github': None,
            'house_s3': None,
            'sec_ticker_lookup': None,
            'sec_form4': None,
            'sec_13f': None,
        }
        
        # Headers SEC
        self.sec_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
    
    # ==================== SECTION 1: POLITICIENS ====================
    
    def test_senate_github(self) -> bool:
        """Test GitHub Senate Stock Watcher"""
        print("\n" + "="*70)
        print("🏛️  TEST 1: Senate Stock Watcher (GitHub)")
        print("="*70)
        
        try:
            url = "https://raw.githubusercontent.com/dwyl/senate-stock-watcher-data/main/data/all_transactions.json"
            print(f"URL: {url}")
            
            response = requests.get(url, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                
                print(f"✅ SUCCESS - {len(df)} transactions loaded")
                print(f"   Columns: {list(df.columns)}")
                print(f"   Sample:")
                print(f"   {df.head(2).to_string()}")
                
                self.results['senate_github'] = {
                    'status': 'OK',
                    'count': len(df),
                    'columns': list(df.columns),
                    'sample': df.head(1).to_dict(orient='records')[0] if len(df) > 0 else None
                }
                return True
            else:
                print(f"❌ FAILED - HTTP {response.status_code}")
                self.results['senate_github'] = {'status': f'HTTP {response.status_code}'}
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            self.results['senate_github'] = {'status': f'ERROR: {str(e)}'}
            return False
    
    def test_house_s3(self) -> bool:
        """Test House Stock Watcher (S3)"""
        print("\n" + "="*70)
        print("🏛️  TEST 2: House Stock Watcher (S3)")
        print("="*70)
        
        try:
            url = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
            print(f"URL: {url}")
            
            response = requests.get(url, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                
                print(f"✅ SUCCESS - {len(df)} transactions loaded")
                print(f"   Columns: {list(df.columns)}")
                print(f"   Sample:")
                print(f"   {df.head(2).to_string()}")
                
                self.results['house_s3'] = {
                    'status': 'OK',
                    'count': len(df),
                    'columns': list(df.columns),
                    'sample': df.head(1).to_dict(orient='records')[0] if len(df) > 0 else None
                }
                return True
            else:
                print(f"❌ FAILED - HTTP {response.status_code}")
                self.results['house_s3'] = {'status': f'HTTP {response.status_code}'}
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            self.results['house_s3'] = {'status': f'ERROR: {str(e)}'}
            return False
    
    # ==================== SECTION 2: INITIÉS (SEC EDGAR) ====================
    
    def test_sec_ticker_lookup(self, ticker: str = "NVDA") -> Optional[str]:
        """Test conversion ticker → CIK (SEC EDGAR)"""
        print("\n" + "="*70)
        print(f"👔 TEST 3: SEC Ticker Lookup ({ticker} → CIK)")
        print("="*70)
        
        try:
            # Méthode 1: Browse-Edgar XML
            url = "https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'company': ticker,
                'type': '',
                'dateb': '',
                'owner': 'exclude',
                'count': 1,
                'output': 'atom'
            }
            
            print(f"URL: {url}")
            print(f"Params: {params}")
            
            response = requests.get(url, params=params, headers=self.sec_headers, timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                # Parse XML pour extraire CIK
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(response.content)
                    
                    # Chercher l'élément CIK dans Atom feed
                    namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
                    entries = root.findall('atom:entry', namespaces)
                    
                    if entries:
                        entry = entries[0]
                        title = entry.findtext('atom:title', namespaces=namespaces)
                        summary = entry.findtext('atom:summary', namespaces=namespaces)
                        
                        print(f"✅ SUCCESS - Found company")
                        print(f"   Title: {title}")
                        print(f"   Summary: {summary[:100] if summary else 'N/A'}...")
                        
                        # Extract CIK from link
                        for link in entry.findall('atom:link', namespaces):
                            href = link.get('href')
                            if 'CIK=' in href:
                                cik = href.split('CIK=')[1].split('&')[0]
                                print(f"   CIK: {cik}")
                                
                                self.results['sec_ticker_lookup'] = {
                                    'status': 'OK',
                                    'ticker': ticker,
                                    'cik': cik,
                                    'title': title
                                }
                                return cik
                    
                    print(f"❌ FAILED - No entries in response")
                    self.results['sec_ticker_lookup'] = {'status': 'No entries found'}
                    return None
                    
                except Exception as parse_err:
                    print(f"❌ XML Parse Error: {str(parse_err)}")
                    self.results['sec_ticker_lookup'] = {'status': f'Parse error: {str(parse_err)}'}
                    return None
            else:
                print(f"❌ FAILED - HTTP {response.status_code}")
                self.results['sec_ticker_lookup'] = {'status': f'HTTP {response.status_code}'}
                return None
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            self.results['sec_ticker_lookup'] = {'status': f'ERROR: {str(e)}'}
            return None
    
    def test_sec_form4(self, ticker: str = "NVDA", cik: Optional[str] = None) -> bool:
        """Test téléchargement des Form 4 depuis SEC"""
        print("\n" + "="*70)
        print(f"📋 TEST 4: SEC Form 4 Collection ({ticker})")
        print("="*70)
        
        try:
            # Si CIK non fourni, le chercher
            if not cik:
                cik = self.test_sec_ticker_lookup(ticker)
            
            if not cik:
                print(f"❌ FAILED - Cannot find CIK for {ticker}")
                return False
            
            # Chercher les Form 4
            url = "https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'type': '4',
                'dateb': '',
                'owner': 'only',
                'start': 0,
                'count': 10,
                'output': 'atom'
            }
            
            print(f"CIK: {cik}")
            print(f"Searching for Form 4 filings...")
            
            response = requests.get(url, params=params, headers=self.sec_headers, timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', namespaces)
                
                if entries:
                    print(f"✅ SUCCESS - {len(entries)} Form 4 filings found")
                    
                    # Show first few
                    for i, entry in enumerate(entries[:3]):
                        title = entry.findtext('atom:title', namespaces=namespaces)
                        updated = entry.findtext('atom:updated', namespaces=namespaces)
                        print(f"   [{i+1}] {title} - {updated}")
                    
                    self.results['sec_form4'] = {
                        'status': 'OK',
                        'ticker': ticker,
                        'cik': cik,
                        'count': len(entries),
                        'filings': [
                            {
                                'title': entry.findtext('atom:title', namespaces=namespaces),
                                'date': entry.findtext('atom:updated', namespaces=namespaces)
                            }
                            for entry in entries[:5]
                        ]
                    }
                    return True
                else:
                    print(f"❌ FAILED - No Form 4 filings found")
                    self.results['sec_form4'] = {'status': 'No filings found'}
                    return False
            else:
                print(f"❌ FAILED - HTTP {response.status_code}")
                self.results['sec_form4'] = {'status': f'HTTP {response.status_code}'}
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            self.results['sec_form4'] = {'status': f'ERROR: {str(e)}'}
            return False
    
    def test_sec_13f(self, fund_cik: str = "0001067983") -> bool:
        """Test 13F filings (Berkshire Hathaway)"""
        print("\n" + "="*70)
        print(f"🏦 TEST 5: SEC 13F Filings (Berkshire Hathaway)")
        print("="*70)
        
        try:
            url = "https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'CIK': fund_cik,
                'type': '13F-HR',
                'dateb': '',
                'owner': 'exclude',
                'start': 0,
                'count': 5,
                'output': 'atom'
            }
            
            print(f"CIK: {fund_cik}")
            print(f"Searching for 13F filings...")
            
            response = requests.get(url, params=params, headers=self.sec_headers, timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', namespaces)
                
                if entries:
                    print(f"✅ SUCCESS - {len(entries)} 13F filings found")
                    
                    for i, entry in enumerate(entries[:3]):
                        title = entry.findtext('atom:title', namespaces=namespaces)
                        updated = entry.findtext('atom:updated', namespaces=namespaces)
                        print(f"   [{i+1}] {title} - {updated}")
                    
                    self.results['sec_13f'] = {
                        'status': 'OK',
                        'cik': fund_cik,
                        'count': len(entries),
                        'filings': [
                            {
                                'title': entry.findtext('atom:title', namespaces=namespaces),
                                'date': entry.findtext('atom:updated', namespaces=namespaces)
                            }
                            for entry in entries[:5]
                        ]
                    }
                    return True
                else:
                    print(f"❌ FAILED - No 13F filings found")
                    self.results['sec_13f'] = {'status': 'No filings found'}
                    return False
            else:
                print(f"❌ FAILED - HTTP {response.status_code}")
                self.results['sec_13f'] = {'status': f'HTTP {response.status_code}'}
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            self.results['sec_13f'] = {'status': f'ERROR: {str(e)}'}
            return False
    
    # ==================== RAPPORT FINAL ====================
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("\n" + "╔" + "="*68 + "╗")
        print("║" + " SMART MONEY TRACKER - REAL API CONNECTION TESTS ".center(68) + "║")
        print("╚" + "="*68 + "╝")
        
        tests = [
            ("Senate GitHub", self.test_senate_github),
            ("House S3", self.test_house_s3),
            ("SEC Form 4", lambda: self.test_sec_form4("NVDA")),
            ("SEC 13F", self.test_sec_13f),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except:
                failed += 1
            
            time.sleep(1)  # Rate limit between tests
        
        # Résumé
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.0f}%" if (passed+failed) > 0 else "N/A")
        
        # Détails
        print("\n📋 DETAILED RESULTS:")
        for key, value in self.results.items():
            status = value.get('status', 'Unknown') if value else 'Not tested'
            print(f"   {key}: {status}")
        
        # Export JSON
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print("\n💾 Results saved to test_results.json")


if __name__ == "__main__":
    tester = RealAPITester()
    tester.run_all_tests()
