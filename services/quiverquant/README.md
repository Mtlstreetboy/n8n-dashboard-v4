# QuiverQuant Integration

## 🎯 Overview

QuiverQuant provides alternative financial data including:
- 📊 **Congressional Trading** (Senate + House)
- 🏛️ **Lobbying Activity**
- 📜 **Government Contracts**
- 👔 **Insider Trading**
- 💬 **WallStreetBets Discussion**
- ✈️ **Corporate Jet Flights**
- 📰 **Wikipedia Page Views**
- 🐦 **Twitter Following**

---

## 🔑 Account Info

**Username:** `bibep`  
**Token:** `5f04adc7e07958d777b52aef00674d3451a365ff`  
**Created:** December 31, 2025

---

## 📦 Installation

```bash
pip install quiverquant
```

Or use the local client:
```python
from services.quiverquant.quiverquant_client import QuiverQuantClient
from services.quiverquant.config import QUIVERQUANT_TOKEN

client = QuiverQuantClient(QUIVERQUANT_TOKEN)
```

---

## 🚀 Quick Start

### Congressional Trading (Critical for Smart Money Tracker!)

```python
# All recent Congress trades
df_congress = client.congress_trading()

# Tesla trades by Congress
df_tesla = client.congress_trading("TSLA")

# Trades by specific politician
df_burr = client.congress_trading("Richard Burr", politician=True)

# Senate only
df_senate = client.senate_trading()

# House only
df_house = client.house_trading()
```

### Insider Trading

```python
# All recent insider trades
df_insiders = client.insiders()

# Apple insiders
df_aapl_insiders = client.insiders("AAPL")
```

### WallStreetBets Sentiment

```python
# Current WSB discussion
df_wsb = client.wallstreetbets()

# GameStop mentions
df_gme = client.wallstreetbets("GME")

# Date range
df_wsb_range = client.wallstreetbets(date_from="2025-12-01", date_to="2025-12-31")
```

### Government Contracts

```python
# All contracts
df_contracts = client.gov_contracts()

# Lockheed Martin contracts
df_lmt = client.gov_contracts("LMT")
```

### Lobbying Activity

```python
# All lobbying
df_lobbying = client.lobbying()

# Apple lobbying
df_aapl_lobby = client.lobbying("AAPL")
```

---

## 📊 Data Format Examples

### Congress Trading Output

```python
{
    'Representative': 'John Smith',
    'ReportDate': '2025-12-28',
    'TransactionDate': '2025-12-20',
    'Ticker': 'AAPL',
    'Transaction': 'Purchase',
    'Amount': '$15,001 - $50,000'
}
```

### Insider Trading Output

```python
{
    'Ticker': 'TSLA',
    'Insider': 'Elon Musk',
    'Relationship': 'CEO',
    'Date': '2025-12-25',
    'Transaction': 'Sale',
    'Shares': 100000,
    'Value': 25000000
}
```

---

## 🔧 Integration with Smart Money Tracker

### Replace Political Trade Collection

In `prod/edgar_smart_money_analyzer.py`, replace the broken JSON sources:

```python
from services.quiverquant.quiverquant_client import QuiverQuantClient
from services.quiverquant.config import QUIVERQUANT_TOKEN

class SmartMoneyAnalyzer:
    def __init__(self):
        self.quiver_client = QuiverQuantClient(QUIVERQUANT_TOKEN)
    
    def collect_political_trades(self, days_back: int = 90) -> pd.DataFrame:
        """
        Collect political trades via QuiverQuant (WORKING!)
        """
        logger.info("🏛️ Collecting Congressional trades via QuiverQuant...")
        
        try:
            # Get all Congress trades
            df_congress = self.quiver_client.congress_trading()
            
            # Filter recent
            cutoff_date = datetime.now() - timedelta(days=days_back)
            df_congress = df_congress[
                df_congress['TransactionDate'] >= cutoff_date
            ]
            
            # Standardize format
            df_congress = df_congress.rename(columns={
                'Representative': 'politician',
                'TransactionDate': 'transaction_date',
                'Ticker': 'ticker',
                'Transaction': 'type'
            })
            
            # Add chamber info
            df_congress['chamber'] = 'Congress'
            
            logger.info(f"✅ Collected {len(df_congress)} Congressional trades")
            return df_congress
            
        except Exception as e:
            logger.error(f"❌ QuiverQuant error: {e}")
            return pd.DataFrame()
```

---

## 📈 Advanced Usage

### Institutional Holdings (13F)

```python
# All 13F filings
df_13f = client.sec13F()

# Apple holdings
df_aapl_13f = client.sec13F(ticker="AAPL")

# Specific fund
df_ark_13f = client.sec13F(owner="ARK Investment Management")

# Position changes
df_changes = client.sec13FChanges(ticker="TSLA")
```

### Social Sentiment

```python
# WSB comments
df_comments = client.wallstreetbetsComments(ticker="GME")

# Twitter following
df_twitter = client.twitter("TSLA")

# Wikipedia views
df_wiki = client.wikipedia("AAPL")
```

---

## ⚠️ Important Notes

### Rate Limits
- Be respectful with API calls
- Add delays between bulk requests
- Cache data when possible

### Data Quality
- Congressional data updated regularly but with delays
- Insider trades have legal reporting delays
- Social sentiment is real-time

### Subscription Features
- Some endpoints require premium subscription
- Error message: "Upgrade your subscription plan to access this dataset."
- Contact: chris@quiverquant.com

---

## 🎯 Priority Use Cases for Smart Money Tracker

1. **Congressional Trading** ✅
   - Replace broken JSON sources
   - Real-time politician trades
   - Senate + House combined

2. **Insider Trading** ✅
   - Complement SEC Form 4 data
   - Additional insider signals

3. **Social Sentiment** 📊
   - WSB discussion as contrarian indicator
   - Twitter following as engagement metric

4. **Institutional Holdings** 💼
   - 13F data for "smart money" tracking
   - Position changes by major funds

---

## 📝 Next Steps

1. **Test Connection**
   ```bash
   python services/quiverquant/test_quiver_connection.py
   ```

2. **Integrate into Smart Money**
   - Update `edgar_smart_money_analyzer.py`
   - Replace `collect_political_trades()`
   - Add insider data complement

3. **Create Collector Script**
   - Scheduled collection
   - Data caching
   - Error handling

---

*Documentation created: 2025-12-31*  
*Integration target: Smart Money Tracker v2*
