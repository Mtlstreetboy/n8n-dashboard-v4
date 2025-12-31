# 🏗️ Architecture Smart Money Tracker

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SMART MONEY TRACKER v2                        │
│                    (edgartools powered)                          │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   Data Sources   │
                    └──────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     ┌────▼──┐    ┌─────▼──┐   ┌──────▼────┐
     │  SEC  │    │ Senate │   │   House   │
     │ EDGAR │    │  Stock │   │   Stock   │
     │       │    │ Watcher│   │  Watcher  │
     │Form 4 │    │(JSON)  │   │ (GitHub)  │
     │Form 13F   │        │   │           │
     │(⚠️ 404)    │(⚠️ 404)   │
     └────┬──┘    └─────┬──┘   └──────┬────┘
          │              │              │
          │     ┌────────┴──────────┐   │
          │     │ Capitol Trades   │   │
          │     │ (BeautifulSoup)  │   │
          │     └─────┬────────────┘   │
          │           │                │
          └───────────┼────────────────┘
                      │
        ┌─────────────▼─────────────┐
        │  EdgarSmartMoneyAnalyzer  │
        │        (Main Class)       │
        └─────────────┬─────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
  ┌───▼──────┐   ┌───▼──────┐   ┌───▼──────┐
  │ Insider  │   │ Political│   │ Combined │
  │  Trades  │   │  Trades  │   │ Signals  │
  │          │   │          │   │          │
  │ Method:  │   │ Method:  │   │ Method:  │
  │collect_  │   │collect_  │   │generate_ │
  │insider_  │   │political │   │combined_ │
  │trades()  │   │_trades() │   │signals() │
  │          │   │          │   │          │
  │✅WORKS   │   │⏳TODO    │   │✅CODE    │
  │119 trans │   │0 data    │   │READY     │
  └───┬──────┘   └───┬──────┘   └───┬──────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
        ┌────────────▼────────────┐
        │  Analysis & Filtering   │
        ├────────────────────────┤
        │- High Conviction Buys  │
        │- Political Clusters    │
        │- Insider Clusters      │
        │- Signal Scoring        │
        └────────────┬───────────┘
                     │
        ┌────────────▼────────────┐
        │   Output & Export       │
        ├────────────────────────┤
        │- CSV Files             │
        │- JSON Export           │
        │- Visualizations        │
        │- Reports               │
        └────────────┬───────────┘
                     │
        ┌────────────▼────────────┐
        │  Interactive Notebook   │
        │ (smart_money_testing)   │
        └────────────────────────┘
```

---

## Data Flow - Detailed

### Path 1: SEC EDGAR (✅ Working)

```
Company CIK (e.g., 0001045810)
    │
    ▼
Company.get_filings(form="4")  [SEC REST API]
    │
    ├─ Returns: 20 Form 4 filings
    │
    ▼
filing.obj()  [Parse XML]
    │
    ├─ Returns: Form4 object
    │
    ▼
ownership.to_dataframe()  [Magic line! ✨]
    │
    ├─ Returns: DataFrame with transactions
    │   - insider_name
    │   - transaction_date
    │   - shares
    │   - price_per_share
    │   - transaction_value
    │   - type (BUY/SELL)
    │
    ▼
DataFrame processed & returned
    │
    Result: 119 transactions for NVDA ✅
```

### Path 2: Political Data (⏳ To Implement)

#### Option A: BeautifulSoup (Current Plan)
```
BeautifulSoup Scraping
    │
    ├─ Source: https://www.capitoltrades.com/
    │
    ▼
response = requests.get(url)
    │
    ▼
soup = BeautifulSoup(response.content, 'html.parser')
    │
    ▼
soup.find_all('table')  [or div, tr, etc]
    │
    ▼
Extract:
    - politician name
    - chamber (Senate/House)
    - ticker
    - transaction_date
    - type (BUY/SELL)
    │
    ▼
pd.DataFrame(political_trades)
    │
    Result: 100+ transactions ⏳
```

#### Option B: GitHub Releases
```
GitHub API
    │
    ├─ URL: https://api.github.com/repos/...
    │
    ▼
Get releases with JSON/CSV attachments
    │
    ▼
Download file
    │
    ▼
Parse JSON or CSV
    │
    Result: Ready-made data ⏳
```

#### Option C: Selenium (Fallback)
```
if BeautifulSoup fails:
    │
    ▼
selenium.webdriver.Chrome()
    │
    ▼
driver.get('https://www.capitoltrades.com/')
    │
    ▼
Wait for JavaScript render
    │
    ▼
html = driver.page_source
    │
    ▼
BeautifulSoup(html, 'html.parser')
    │
    Result: Scraping with JS support
```

### Path 3: Analysis Pipeline (✅ Code Ready)

```
Insider Trades (119 trans)  +  Political Trades (N trans)
    │                             │
    └──────────────┬──────────────┘
                   │
                   ▼
    EdgarSmartMoneyAnalyzer
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
Filter HC   Detect Clusters  Score Signals
    │              │              │
    ├─Buy/Sell    ├─Multiple     ├─Insider
    │  code        │  insiders    │  score
    │             │  same ticker ├─Political
    ├─Min $100k    │             │  score
    │             ├─Within 7 days├─Combined
    │             │             │  score
    │             │             │
    └──────────────┼──────────────┘
                   │
                   ▼
        Combined Signals DataFrame
        (5 tickers, 3 scores each)
                   │
                   ▼
        generate_combined_signals()
                   │
        Recommendations for each:
        - BUY / HOLD / SELL
        - Conviction level
        - Supporting evidence
```

---

## Module Structure

```
EdgarSmartMoneyAnalyzer
│
├─ __init__()
│  └─ Initialize edgartools, setup CIK cache
│
├─ get_cik_for_ticker(ticker)
│  └─ Returns CIK from cache
│
├─ collect_insider_trades(ticker, days_back=90)
│  ├─ Get Form 4 filings
│  ├─ Parse with to_dataframe()
│  └─ Return DataFrame: 119 rows
│
├─ collect_political_trades(days_back=90)
│  ├─ [TO IMPLEMENT]
│  ├─ Scrape Capitol Trades or GitHub
│  └─ Return DataFrame: N rows
│
├─ filter_high_conviction_buys(df, min_value=100000)
│  ├─ Filter code P or BUY
│  ├─ Min $100k value
│  ├─ Detect clusters
│  └─ Return scored DataFrame
│
├─ detect_political_clusters(df, window_days=14)
│  ├─ Group by ticker & date range
│  ├─ Count number of buyers
│  ├─ Calculate signal strength
│  └─ Return clusters DataFrame
│
└─ generate_combined_signals(tickers, days_insider=30, days_political=60)
   ├─ Collect insider trades per ticker
   ├─ Collect political trades per ticker
   ├─ Score each data source
   ├─ Combine scores
   └─ Return recommendation DataFrame
```

---

## Data Models

### Insider Trade (Form 4)
```python
{
    'ticker': 'NVDA',
    'filing_date': '2025-12-22',
    'transaction_date': '2025-12-18',
    'insider_name': 'Mark A Stevens',
    'role': 'Director',
    'transaction_code': 'S',  # SEC code
    'shares': 222500,
    'price_per_share': 180.17,
    'transaction_value': 40087380,
    'type': 'SELL'  # BUY/SELL/OTHER
}
```

### Political Trade (TBD - Structure)
```python
{
    'politician': 'John Smith',
    'chamber': 'Senate',  # Senate/House
    'ticker': 'AAPL',
    'transaction_date': '2025-12-20',
    'type': 'BUY',  # BUY/SELL
    'shares': 1000,  # Peut être absent
    'price': 150.50,  # Peut être absent
    'transaction_value': 150500,  # Calculé
}
```

### Combined Signal
```python
{
    'ticker': 'NVDA',
    'political_score': 0,      # 0-100 (no data)
    'insider_score': 45,       # 0-100 (mostly sells)
    'combined_score': 22,      # 0-100
    'recommendation': 'HOLD',  # BUY/HOLD/SELL
    'details': {
        'num_insider_buys': 0,
        'insider_value': '$0',
        'num_political_buys': 0,
        'political_value': '$0',
        'clusters': 0
    }
}
```

---

## Technology Stack

```
Dependencies
│
├─ edgartools 5.6.4 ✅
│  ├─ httpx (HTTP client)
│  ├─ hishel (caching)
│  ├─ pydantic (validation)
│  └─ beautifulsoup4 (XML parsing)
│
├─ pandas ✅
│  └─ Data manipulation
│
├─ requests ✅
│  └─ HTTP requests
│
├─ beautifulsoup4 ✅
│  └─ HTML scraping
│
├─ matplotlib, seaborn ✅
│  └─ Visualizations
│
└─ selenium (IF needed)
   └─ JS rendering fallback
```

---

## Status by Component

```
Component                   Status      Progress    Notes
─────────────────────────────────────────────────────────
SEC EDGAR Form 4           ✅ Ready     100%        119 trans NVDA
Form 13F Support           ✅ Ready      50%        Code in place
Political Scraping         ⏳ TODO        0%        BeautifulSoup next
Data Validation            ✅ Ready     100%        Type checking
High Conviction Filter     ✅ Ready      90%        Logic ready
Cluster Detection          ✅ Ready      90%        Waiting for data
Signal Scoring             ✅ Ready      90%        Waiting for data
Visualizations             ✅ Ready      80%        Code not tested
CSV Export                 ✅ Ready     100%        Ready to use
Notebook Integration       ✅ Ready      80%        Needs political
─────────────────────────────────────────────────────────
OVERALL                    ⏳ 70%        70%        Political = blocker
```

---

## Critical Path to Production

```
Day 1 (30 Dec)  ✅ DONE
├─ SEC EDGAR setup
└─ Form 4 working

Day 2 (31 Dec)  ⏳ IN PROGRESS
├─ Political data (BeautifulSoup)
├─ Integration testing
└─ Final validation

Day 3 (2 Jan)   ⏳ TODO
├─ Production deployment
├─ Monitoring setup
└─ Documentation finalization
```

---

## Deployment Target

```
Future Deployment
│
├─ Docker Container
│  ├─ Python 3.10
│  ├─ edgartools 5.6.4
│  └─ All dependencies
│
├─ Scheduled Runs
│  ├─ Daily: Collect new trades
│  ├─ Daily: Generate signals
│  └─ Daily: Export results
│
├─ Output
│  ├─ CSV files
│  ├─ JSON API
│  └─ Web Dashboard
│
└─ Monitoring
   ├─ Error logging
   ├─ Data quality checks
   └─ Performance metrics
```

---

*Architecture Diagram - Smart Money Tracker*  
*Created: 2025-12-30*  
*Version: 2.0 (edgartools)*  
*Status: 70% Complete*
