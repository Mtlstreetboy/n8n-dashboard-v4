"""
QuiverQuant Client
==================

Client Python complet pour l'API QuiverQuant
Source: Documentation officielle QuiverQuant
"""

import requests
import json
import pandas as pd
from typing import Optional

class QuiverQuantClient:
    """Client pour interagir avec l'API QuiverQuant"""
    
    def __init__(self, token: str):
        """
        Initialize QuiverQuant client
        
        Args:
            token: API authorization token
        """
        self.token = token
        self.headers = {
            'accept': 'application/json',
            'X-CSRFToken': 'TyTJwjuEC7VV7mOqZ622haRaaUr0x0Ng4nrwSRFKQs7vdoBcJlK9qjAS69ghzhFu',
            'Authorization': f"Token {self.token}"
        }
    
    def congress_trading(self, ticker: str = "", politician: bool = False, recent: bool = True) -> pd.DataFrame:
        """
        Get Congressional trading data
        
        Args:
            ticker: Stock ticker or politician name
            politician: If True, treat ticker as politician name
            recent: If True, get recent data, else bulk data
        """
        if recent:
            urlStart = 'https://api.quiverquant.com/beta/live/congresstrading'
        else:
            urlStart = 'https://api.quiverquant.com/beta/bulk/congresstrading'
        
        if politician:
            ticker = ticker.replace(" ", "%20")
            url = f"{urlStart}?representative={ticker}"
        elif len(ticker) > 0:
            url = f"{urlStart}/{ticker}"
        else:
            url = urlStart
        
        print(f"📡 Fetching: {url}")
        r = requests.get(url, headers=self.headers)
        j = json.loads(r.content)
        df = pd.DataFrame(j)
        
        if not df.empty:
            df["ReportDate"] = pd.to_datetime(df["ReportDate"])
            df["TransactionDate"] = pd.to_datetime(df["TransactionDate"])
        
        return df
   
    def senate_trading(self, ticker: str = "") -> pd.DataFrame:
        """Get Senate trading data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/senatetrading/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/senatetrading"
        
        r = requests.get(url, headers=self.headers)
        j = json.loads(r.content)
        df = pd.DataFrame(j)
        
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"])
        
        return df

    def house_trading(self, ticker: str = "") -> pd.DataFrame:
        """Get House of Representatives trading data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/housetrading/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/housetrading"
        
        r = requests.get(url, headers=self.headers)
        j = json.loads(r.content)
        df = pd.DataFrame(j)
        
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"])
        
        return df    
    
    def offexchange(self, ticker: str = "") -> pd.DataFrame:
        """Get off-exchange short volume data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/offexchange/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/offexchange"
        
        r = requests.get(url, headers=self.headers)
        j = json.loads(r.content)
        df = pd.DataFrame(j)
        
        if len(ticker) > 0 and not df.empty:
            df["Date"] = pd.to_datetime(df["Date"])
        
        return df
    
    def gov_contracts(self, ticker: str = "") -> pd.DataFrame:
        """Get government contracts data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/govcontractsall/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/govcontractsall"

        r = requests.get(url, headers=self.headers)
        df = pd.DataFrame(json.loads(r.content))
        return df

    def lobbying(self, ticker: str = "") -> pd.DataFrame:
        """Get corporate lobbying data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/lobbying/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/lobbying"

        r = requests.get(url, headers=self.headers)
        df = pd.DataFrame(json.loads(r.content))
        
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"])
        
        return df
        
    def insiders(self, ticker: str = "") -> pd.DataFrame:
        """Get insider trading data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/live/insiders?ticker={ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/insiders"
         
        print(f"📡 Fetching: {url}")
        r = requests.get(url, headers=self.headers)
        df = pd.DataFrame(json.loads(r.content))
        return df     
            
    def wikipedia(self, ticker: str = "") -> pd.DataFrame:
        """Get Wikipedia page views data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/wikipedia/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/wikipedia"

        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset.')
            
        df = pd.DataFrame(json.loads(r.content))
        return df
    
    def wallstreetbets(self, ticker: str = "", date_from: str = "", date_to: str = "", yesterday: bool = False) -> pd.DataFrame:
        """Get WallStreetBets discussion data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/wallstreetbets/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/wallstreetbets?count_all=true"

            if len(date_from) > 0:
                date_from = pd.to_datetime(date_from).strftime('%Y%m%d')
                url = f"{url}&date_from={date_from}"
            if len(date_to) > 0:
                url = f"{url}&date_to={date_to}"

        if yesterday:
            url = "https://api.quiverquant.com/beta/live/wallstreetbets"

        print(f"📡 Fetching: {url}")
        r = requests.get(url, headers=self.headers)

        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset.')

        df = pd.DataFrame(json.loads(r.content))

        if not yesterday and not df.empty:
            try:
                df["Date"] = pd.to_datetime(df["Time"], unit='ms')
            except:
                df["Date"] = pd.to_datetime(df["Date"])
            
            if len(date_from) > 0:
                df = df[df["Date"] >= pd.to_datetime(date_from)]
            if len(date_to) > 0:
                df = df[df["Date"] <= pd.to_datetime(date_to)]

        return df 
    
    def twitter(self, ticker: str = "") -> pd.DataFrame:
        """Get Twitter following data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/twitter/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/twitter"

        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset.')
            
        df = pd.DataFrame(json.loads(r.content))
        return df 
    
    def spacs(self, ticker: str = "") -> pd.DataFrame:
        """Get r/SPACs discussion data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/spacs/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/spacs"

        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset.')
            
        df = pd.DataFrame(json.loads(r.content))
        return df 
    
    def flights(self, ticker: str = "") -> pd.DataFrame:
        """Get corporate private jet flights data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/flights/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/flights"

        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset.')
            
        df = pd.DataFrame(json.loads(r.content))
        return df 
        
    def political_beta(self, ticker: str = "") -> pd.DataFrame:
        """Get political beta data"""
        if len(ticker) > 0:
            url = f"https://api.quiverquant.com/beta/historical/politicalbeta/{ticker}"
        else:
            url = "https://api.quiverquant.com/beta/live/politicalbeta"

        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset.')
            
        df = pd.DataFrame(json.loads(r.content))
        return df 
    
    def patents(self, ticker: str = "") -> pd.DataFrame:
        """Get patent data"""
        if len(ticker) < 1:
            url = "https://api.quiverquant.com/beta/live/allpatents"
        else:
            url = f"https://api.quiverquant.com/beta/historical/allpatents/{ticker}"
       
        print(f"📡 Fetching: {url}")
        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset.')
        
        df = pd.DataFrame(json.loads(r.content))
        
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"])
        
        return df
    
    # Advanced features (contact chris@quiverquant.com for access)
    
    def sec13F(self, ticker: str = "", date: str = "", owner: str = "", period: str = "") -> pd.DataFrame:
        """Get SEC 13F institutional holdings data"""
        separator = "?"
        url = "https://api.quiverquant.com/beta/live/sec13f"
        
        if len(ticker) > 0:
            url = f"{url}{separator}ticker={ticker}"
            separator = "&"
        if len(date) > 0:
            url = f"{url}{separator}date={date}"
            separator = "&"
        if len(owner) > 0:
            url = f"{url}{separator}owner={owner}"
            separator = "&"
        if len(period) > 0:
            url = f"{url}{separator}period={period}"
            separator = "&"
            
        print(f"📡 Fetching: {url}")
        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset.')
            
        df = pd.DataFrame(json.loads(r.content))
        
        if not df.empty:
            df["ReportPeriod"] = pd.to_datetime(df["ReportPeriod"], unit='ms')
            df["Date"] = pd.to_datetime(df["Date"], unit="ms")
        
        return df
    
    def sec13FChanges(self, ticker: str = "", date: str = "", owner: str = "", period: str = "") -> pd.DataFrame:
        """Get SEC 13F position changes"""
        separator = "?"
        url = "https://api.quiverquant.com/beta/live/sec13fchanges"
        
        if len(ticker) > 0:
            url = f"{url}{separator}ticker={ticker}"
            separator = "&"
        if len(date) > 0:
            url = f"{url}{separator}date={date}"
            separator = "&"
        if len(owner) > 0:
            url = f"{url}{separator}owner={owner}"
            separator = "&"
        if len(period) > 0:
            url = f"{url}{separator}period={period}"
            separator = "&"
            
        print(f"📡 Fetching: {url}")
        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset.')
            
        df = pd.DataFrame(json.loads(r.content))
        
        if not df.empty:
            df["ReportPeriod"] = pd.to_datetime(df["ReportPeriod"], unit='ms')
            df["Date"] = pd.to_datetime(df["Date"], unit="ms")
        
        return df    
    
    def wallstreetbetsComments(self, ticker: str = "", freq: str = "", date_from: str = "", date_to: str = "") -> pd.DataFrame:
        """Get WallStreetBets comments data"""
        separator = "?"
        url = "https://api.quiverquant.com/beta/live/wsbcomments"
        
        if len(ticker) > 0:
            url = f"{url}{separator}ticker={ticker}"
            separator = "&"
        if len(freq) > 0:
            url = f"{url}{separator}freq={freq}"
            separator = "&"
        if len(date_from) > 0:
            url = f"{url}{separator}date_from={date_from}"
            separator = "&"
        if len(date_to) > 0:
            url = f"{url}{separator}date_to={date_to}"
            separator = "&"
            
        print(f"📡 Fetching: {url}")
        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset. Contact chris@quiverquant.com with questions.')
            
        df = pd.DataFrame(json.loads(r.content))
        
        if not df.empty:
            df['Datetime'] = pd.to_datetime(df["Time"], unit='ms')
        
        return df 
    
    def wallstreetbetsCommentsFull(self, ticker: str = "", freq: str = "", date_from: str = "", date_to: str = "") -> pd.DataFrame:
        """Get full WallStreetBets comments data"""
        separator = "?"
        url = "https://api.quiverquant.com/beta/live/wsbcommentsfull"
        
        if len(ticker) > 0:
            url = f"{url}{separator}ticker={ticker}"
            separator = "&"
        if len(freq) > 0:
            url = f"{url}{separator}freq={freq}"
            separator = "&"
        if len(date_from) > 0:
            url = f"{url}{separator}date_from={date_from}"
            separator = "&"
        if len(date_to) > 0:
            url = f"{url}{separator}date_to={date_to}"
            separator = "&"
            
        print(f"📡 Fetching: {url}")
        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset. Contact chris@quiverquant.com with questions.')
            
        df = pd.DataFrame(json.loads(r.content))
        
        if not df.empty:
            df['Datetime'] = pd.to_datetime(df["Time"], unit='ms')
        
        return df 
    
    def cryptoComments(self, ticker: str = "", freq: str = "", date_from: str = "", date_to: str = "") -> pd.DataFrame:
        """Get cryptocurrency comments data"""
        separator = "?"
        url = "https://api.quiverquant.com/beta/live/cryptocomments"
        
        if len(ticker) > 0:
            url = f"{url}{separator}ticker={ticker}"
            separator = "&"
        if len(freq) > 0:
            url = f"{url}{separator}freq={freq}"
            separator = "&"
        if len(date_from) > 0:
            url = f"{url}{separator}date_from={date_from}"
            separator = "&"
        if len(date_to) > 0:
            url = f"{url}{separator}date_to={date_to}"
            separator = "&"
            
        print(f"📡 Fetching: {url}")
        r = requests.get(url, headers=self.headers)
        
        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset. Contact chris@quiverquant.com with questions.')
            
        df = pd.DataFrame(json.loads(r.content))
        
        if not df.empty:
            df['Datetime'] = pd.to_datetime(df["Time"], unit='ms')
        
        return df 
    
    def cryptoCommentsHistorical(self, ticker: str = "", freq: str = "", date_from: str = "", date_to: str = "") -> pd.DataFrame:
        """Get historical cryptocurrency comments data"""
        separator = "?"
        url = "https://api.quiverquant.com/beta/live/cryptocommentsfull"
        
        if len(ticker) > 0:
            url = f"{url}{separator}ticker={ticker}"
            separator = "&"
        if len(freq) > 0:
            url = f"{url}{separator}freq={freq}"
            separator = "&"
        if len(date_from) > 0:
            url = f"{url}{separator}date_from={date_from}"
            separator = "&"
        if len(date_to) > 0:
            url = f"{url}{separator}date_to={date_to}"
            separator = "&"

        print(f"📡 Fetching: {url}")
        r = requests.get(url, headers=self.headers)

        if r.text == '"Upgrade your subscription plan to access this dataset."':
            raise NameError('Upgrade your subscription plan to access this dataset. Contact chris@quiverquant.com with questions.')

        df = pd.DataFrame(json.loads(r.content))
        
        if not df.empty:
            df['Datetime'] = pd.to_datetime(df["Time"], unit='ms')
        
        return df
