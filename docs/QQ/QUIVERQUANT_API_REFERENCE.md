# QuiverQuant API Reference

## 📡 Complete API Documentation

**Account:** bibep  
**Token:** 5f04adc7e07958d777b52aef00674d3451a365ff  
**Base URL:** https://api.quiverquant.com/beta

---

## 🏛️ Political & Government Data

### Congress Trading

**Endpoint:** `/live/congresstrading` or `/bulk/congresstrading`

**Methods:**
```python
# All recent trades
client.congress_trading()

# Specific ticker
client.congress_trading("AAPL")

# Specific politician
client.congress_trading("Nancy Pelosi", politician=True)
```

**Response Fields:**
- `Representative`: Politician name
- `TransactionDate`: Date of trade
- `ReportDate`: Date reported
- `Ticker`: Stock symbol
- `Transaction`: Purchase/Sale
- `Amount`: Dollar range

### Senate Trading

**Endpoint:** `/live/senatetrading`

```python
client.senate_trading()        # All Senate
client.senate_trading("TSLA")  # Tesla Senate trades
```

### House Trading

**Endpoint:** `/live/housetrading`

```python
client.house_trading()        # All House
client.house_trading("MSFT")  # Microsoft House trades
```

### Lobbying

**Endpoint:** `/live/lobbying`

```python
client.lobbying()        # All lobbying
client.lobbying("GOOGL") # Google lobbying
```

**Fields:**
- `Client`: Company name
- `Date`: Filing date
- `Amount`: Lobbying spend
- `Issue`: Topics lobbied

### Government Contracts

**Endpoint:** `/live/govcontractsall`

```python
client.gov_contracts()       # All contracts
client.gov_contracts("LMT")  # Lockheed contracts
```

---

## 💼 Institutional & Insider Data

### Insider Trading

**Endpoint:** `/live/insiders`

```python
client.insiders()         # All insiders
client.insiders("AAPL")   # Apple insiders
```

**Fields:**
- `Ticker`: Stock
- `Insider`: Name
- `Relationship`: Title (CEO, Director, etc.)
- `Date`: Transaction date
- `Transaction`: Sale/Purchase
- `Shares`: Number of shares
- `Value`: Dollar value

### SEC 13F Holdings

**Endpoint:** `/live/sec13f`

```python
# All 13F filings
client.sec13F()

# Specific stock
client.sec13F(ticker="TSLA")

# Specific fund
client.sec13F(owner="Berkshire Hathaway")

# Specific date/period
client.sec13F(date="2025-12-31", period="Q4")
```

**Fields:**
- `Owner`: Fund name
- `Ticker`: Stock
- `Shares`: Number held
- `Value`: Position value
- `ReportPeriod`: Quarter
- `Date`: Filing date

### 13F Position Changes

**Endpoint:** `/live/sec13fchanges`

```python
client.sec13FChanges(ticker="AAPL")
client.sec13FChanges(owner="ARK Investment Management")
```

Shows position increases/decreases quarter-over-quarter.

---

## 💬 Social Sentiment Data

### WallStreetBets

**Endpoint:** `/live/wallstreetbets`

```python
# All mentions
client.wallstreetbets()

# Specific stock
client.wallstreetbets("GME")

# Date range
client.wallstreetbets(date_from="2025-12-01", date_to="2025-12-31")

# Yesterday's data
client.wallstreetbets(yesterday=True)
```

**Fields:**
- `Ticker`: Stock
- `Mentions`: Number of mentions
- `Date`: Date
- `Sentiment`: Bullish/Bearish (if available)

### WSB Comments (Detailed)

**Endpoint:** `/live/wsbcomments`

```python
client.wallstreetbetsComments(ticker="GME", freq="daily")
client.wallstreetbetsCommentsFull(ticker="TSLA")
```

**Parameters:**
- `ticker`: Stock symbol
- `freq`: "hourly" or "daily"
- `date_from`, `date_to`: Date range

### r/SPACs

**Endpoint:** `/live/spacs`

```python
client.spacs()         # All SPAC mentions
client.spacs("CCIV")   # Specific SPAC
```

### Crypto Subreddits

**Endpoint:** `/live/cryptocomments`

```python
client.cryptoComments(ticker="BTC")
client.cryptoCommentsHistorical(ticker="ETH", date_from="2025-12-01")
```

---

## 📊 Alternative Metrics

### Wikipedia Page Views

**Endpoint:** `/live/wikipedia`

```python
client.wikipedia()        # All companies
client.wikipedia("AAPL")  # Apple views
```

**Use Case:** Interest/awareness proxy

### Twitter Following

**Endpoint:** `/live/twitter`

```python
client.twitter()       # All companies
client.twitter("TSLA") # Tesla followers
```

**Use Case:** Social media engagement

### Corporate Jet Flights

**Endpoint:** `/live/flights`

```python
client.flights()        # All flights
client.flights("AAPL")  # Apple jets
```

**Use Case:** M&A speculation, executive activity

### Patents

**Endpoint:** `/live/allpatents`

```python
client.patents()        # All patents
client.patents("GOOGL") # Google patents
```

**Fields:**
- `Date`: Filing date
- `Title`: Patent title
- `Assignee`: Company
- `Inventors`: Names

---

## 📈 Market Data

### Off-Exchange Short Volume

**Endpoint:** `/live/offexchange`

```python
client.offexchange()       # All stocks
client.offexchange("AMC")  # AMC short volume
```

**Use Case:** Dark pool activity, short interest

### Political Beta

**Endpoint:** `/live/politicalbeta`

```python
client.political_beta()        # All stocks
client.political_beta("LMT")   # Lockheed beta
```

**Use Case:** Sensitivity to political events

---

## 🔐 Authentication

All requests require:

```python
headers = {
    'accept': 'application/json',
    'X-CSRFToken': 'TyTJwjuEC7VV7mOqZ622haRaaUr0x0Ng4nrwSRFKQs7vdoBcJlK9qjAS69ghzhFu',
    'Authorization': 'Token 5f04adc7e07958d777b52aef00674d3451a365ff'
}
```

---

## ⚠️ Rate Limits & Best Practices

### Rate Limiting
- No official limit published
- Be respectful: 1-2 requests/second max
- Use caching for repeated queries

### Error Handling

```python
try:
    df = client.congress_trading()
except Exception as e:
    if "Upgrade your subscription" in str(e):
        print("Premium feature - contact chris@quiverquant.com")
    else:
        print(f"API error: {e}")
```

### Caching Strategy

```python
import pickle
from datetime import datetime, timedelta

CACHE_FILE = "political_trades_cache.pkl"
CACHE_DURATION = timedelta(hours=6)

def get_cached_or_fetch():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            cache = pickle.load(f)
        
        if datetime.now() - cache['timestamp'] < CACHE_DURATION:
            return cache['data']
    
    # Fetch fresh data
    data = client.congress_trading()
    
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump({'timestamp': datetime.now(), 'data': data}, f)
    
    return data
```

---

## 🎯 Smart Money Tracker Integration

### Priority Endpoints

1. **Congress Trading** - Main data source
2. **Senate/House Trading** - Granular breakdown
3. **Insider Trading** - Additional signals
4. **13F Holdings** - Institutional tracking
5. **WSB Sentiment** - Retail sentiment

### Data Flow

```
QuiverQuant API
    ↓
collect_political_trades.py
    ↓
local_files/smart_money/political_trades_YYYYMMDD.csv
    ↓
edgar_smart_money_analyzer.py
    ↓
Dashboard visualizations
```

---

## 📞 Support

**Email:** chris@quiverquant.com  
**Website:** https://www.quiverquant.com  
**Documentation:** https://api.quiverquant.com/docs

---

*Last Updated: 2025-12-31*  
*Account: bibep*
