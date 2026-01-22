"""
Multi-Stock News Scraper
Récupère les nouvelles financières depuis Yahoo Finance et Google News
Configuration via config.json
"""

import yfinance as yf
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
import time
from collections import defaultdict

class StockNewsScraper:
    def __init__(self, config_file='config.json'):
        """Initialise le scraper avec la configuration"""
        self.config = self.load_config(config_file)
        self.all_news = []
        
    def load_config(self, config_file):
        """Charge le fichier de configuration"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ Configuration chargée depuis {config_file}")
            return config
        except FileNotFoundError:
            print(f"❌ Fichier {config_file} introuvable")
            exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de lecture JSON: {e}")
            exit(1)
    
    def get_enabled_tickers(self) -> List[Dict]:
        """Retourne la liste des tickers activés"""
        return [t for t in self.config['tickers'] if t['enabled']]
    
    def get_yahoo_finance_news(self, ticker_info: Dict) -> List[Dict]:
        """Récupère les nouvelles depuis Yahoo Finance"""
        symbol = ticker_info['symbol']
        news_list = []
        
        if 'yahoo' not in ticker_info['sources']:
            return news_list
            
        try:
            print(f"  📊 Yahoo Finance: {symbol}...")
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            for article in news:
                try:
                    timestamp = article.get('providerPublishTime', 0)
                    publish_date = datetime.fromtimestamp(timestamp)
                    
                    # Filtrer par date (40 derniers jours)
                    days_back = self.config['settings']['days_back']
                    if publish_date < datetime.now() - timedelta(days=days_back):
                        continue
                    
                    news_item = {
                        'ticker': symbol,
                        'company': ticker_info['name'],
                        'title': article.get('title', ''),
                        'publisher': article.get('publisher', 'Yahoo Finance'),
                        'link': article.get('link', ''),
                        'publish_date': publish_date.strftime('%Y-%m-%d'),
                        'publish_time': publish_date.strftime('%H:%M:%S'),
                        'type': article.get('type', 'news'),
                        'source': 'Yahoo Finance',
                        'thumbnail': self._get_thumbnail(article)
                    }
                    
                    # Appliquer les filtres
                    if self._apply_filters(news_item):
                        news_list.append(news_item)
                        
                except Exception as e:
                    print(f"    ⚠️ Erreur article: {e}")
                    continue
            
            print(f"    ✅ {len(news_list)} nouvelles récupérées")
            
        except Exception as e:
            print(f"    ❌ Erreur Yahoo: {e}")
        
        return news_list
    
    def get_google_news(self, ticker_info: Dict) -> List[Dict]:
        """Récupère les nouvelles depuis Google News RSS"""
        symbol = ticker_info['symbol']
        company_name = ticker_info['name']
        news_list = []
        
        if 'google' not in ticker_info['sources']:
            return news_list
        
        try:
            print(f"  🔍 Google News: {symbol}...")
            
            # Construire l'URL RSS de Google News
            days = self.config['settings']['days_back']
            lang = self.config['settings']['language']
            country = self.config['settings']['country']
            
            query = f"{company_name}+stock+{symbol}"
            url = f"https://news.google.com/rss/search?q={query}+when:{days}d&hl={lang}&gl={country}&ceid={country}:{lang}"
            
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=10)
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            for item in items[:self.config['settings']['news_per_day']]:
                try:
                    pub_date_str = item.find('pubDate').text
                    pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                    
                    news_item = {
                        'ticker': symbol,
                        'company': company_name,
                        'title': item.find('title').text,
                        'publisher': item.find('source').text if item.find('source') else 'Google News',
                        'link': item.find('link').text,
                        'publish_date': pub_date.strftime('%Y-%m-%d'),
                        'publish_time': pub_date.strftime('%H:%M:%S'),
                        'type': 'news',
                        'source': 'Google News',
                        'description': item.find('description').text if item.find('description') else ''
                    }
                    
                    if self._apply_filters(news_item):
                        news_list.append(news_item)
                        
                except Exception as e:
                    print(f"    ⚠️ Erreur article: {e}")
                    continue
            
            print(f"    ✅ {len(news_list)} nouvelles récupérées")
            
        except Exception as e:
            print(f"    ❌ Erreur Google News: {e}")
        
        # Petit délai pour éviter le rate limiting
        time.sleep(1)
        return news_list
    
    def _get_thumbnail(self, article: Dict) -> str:
        """Extrait l'URL de la miniature"""
        try:
            thumbnail = article.get('thumbnail', {})
            if thumbnail and 'resolutions' in thumbnail:
                return thumbnail['resolutions'][0].get('url', '')
        except:
            pass
        return ''
    
    def _apply_filters(self, news_item: Dict) -> bool:
        """Applique les filtres de configuration"""
        filters = self.config['filters']
        
        # Filtre longueur titre
        if len(news_item['title']) < filters['min_title_length']:
            return False
        
        # Filtre mots exclus
        title_lower = news_item['title'].lower()
        for keyword in filters['exclude_keywords']:
            if keyword.lower() in title_lower:
                return False
        
        return True
    
    def scrape_all(self):
        """Scrape toutes les sources pour tous les tickers activés"""
        enabled_tickers = self.get_enabled_tickers()
        
        print(f"\n🚀 Démarrage du scraping pour {len(enabled_tickers)} tickers...")
        print(f"📅 Période: {self.config['settings']['days_back']} derniers jours\n")
        
        for ticker_info in enabled_tickers:
            print(f"📈 {ticker_info['name']} ({ticker_info['symbol']})")
            
            # Yahoo Finance
            if self.config['sources']['yahoo']['enabled']:
                yahoo_news = self.get_yahoo_finance_news(ticker_info)
                self.all_news.extend(yahoo_news)
            
            # Google News
            if self.config['sources']['google']['enabled']:
                google_news = self.get_google_news(ticker_info)
                self.all_news.extend(google_news)
            
            print()
        
        # Trier par date (plus récent en premier)
        self.all_news.sort(key=lambda x: x['publish_date'], reverse=True)
        
        return self.all_news
    
    def save_to_json(self):
        """Sauvegarde les nouvelles en JSON"""
        output_file = self.config['settings']['output_file']
        
        output_data = {
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_news': len(self.all_news),
                'tickers': [t['symbol'] for t in self.get_enabled_tickers()],
                'days_covered': self.config['settings']['days_back']
            },
            'news': self.all_news
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Données sauvegardées dans {output_file}")
            print(f"📊 Total: {len(self.all_news)} nouvelles")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
    
    def get_statistics(self):
        """Affiche des statistiques sur les données collectées"""
        if not self.all_news:
            return
        
        print("\n" + "="*60)
        print("📊 STATISTIQUES")
        print("="*60)
        
        # Par ticker
        by_ticker = defaultdict(int)
        for news in self.all_news:
            by_ticker[news['ticker']] += 1
        
        print("\n📈 Nouvelles par ticker:")
        for ticker, count in sorted(by_ticker.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ticker}: {count} nouvelles")
        
        # Par source
        by_source = defaultdict(int)
        for news in self.all_news:
            by_source[news['source']] += 1
        
        print("\n📰 Nouvelles par source:")
        for source, count in by_source.items():
            print(f"  {source}: {count} nouvelles")
        
        # Par date
        by_date = defaultdict(int)
        for news in self.all_news:
            by_date[news['publish_date']] += 1
        
        print(f"\n📅 Couverture: {len(by_date)} jours différents")
        print(f"📊 Moyenne: {len(self.all_news) / len(by_date):.1f} nouvelles/jour")
        print("="*60 + "\n")


def main():
    """Fonction principale"""
    print("="*60)
    print("  📰 STOCK NEWS SCRAPER 📰")
    print("="*60)
    
    # Initialiser le scraper
    scraper = StockNewsScraper('config.json')
    
    # Scraper toutes les sources
    scraper.scrape_all()
    
    # Afficher les statistiques
    scraper.get_statistics()
    
    # Sauvegarder en JSON
    scraper.save_to_json()
    
    print("\n✅ Terminé!\n")


if __name__ == "__main__":
    main()