# 📊 SEC EDGAR Data Schema - Investment Focus

**Purpose:** Define data structures optimized for personal investment decision-making  
**Goal:** Track "smart money" signals for portfolio replication (40% cash allocation)

---

## 🎯 INVESTMENT CONTEXT

**Portfolio Allocation Strategy:**
- 60% Core Holdings (VOO, AMEX, VISA, MAG7, LULU, GOOGL, NVDA)
- 40% Smart Money Replication (guided by these signals)

**Signal Prioritization:**
1. **High Priority:** Large insider buys, M&A by growth companies (PLTR-style)
2. **Medium Priority:** Political trades with timing edge
3. **Low Priority:** Small insider transactions, routine filings

---

## 📋 SCHEMA DEFINITIONS

### 1. Schedule 13D Event (M&A Signal)

**Use Case:** Detect when smart money takes >5% stake (high conviction play)

```json
{
  "event_id": "13D_PLTR_20260103_001",
  "signal_type": "acquisition",
  "signal_strength": "high",
  
  // Who's buying
  "filer_cik": "0001321655",
  "filer_name": "Palantir Technologies Inc.",
  "filer_ticker": "PLTR",
  "filer_type": "strategic_buyer",
  
  // What they're buying
  "target_cik": "0009876543",
  "target_ticker": null,
  "target_name": "AI Defense Company Inc.",
  "target_is_public": false,
  
  // The bet
  "ownership_pct": 8.5,
  "shares_owned": 850000,
  "share_price": 50.00,
  "investment_value_usd": 42500000,
  
  // Timing
  "transaction_date": "2025-12-28",
  "filing_date": "2026-01-03",
  "days_to_filing": 5,
  
  // Intent analysis
  "item_4_intent": "strategic_investment",
  "item_4_text": "Filer intends to collaborate on AI defense solutions...",
  "investment_thesis": "Strategic acquisition for AI defense synergy with PLTR core business",
  
  // Decision support
  "actionable": true,
  "actionable_reason": "Can invest in PLTR as proxy for this bet",
  "research_priority": "high",
  "suggested_action": "Buy PLTR calls or shares",
  "conviction_score": 8.5,
  
  // Metadata
  "form_type": "SC 13D",
  "accession_number": "0001193125-26-000123",
  "sec_url": "https://www.sec.gov/cgi-bin/viewer?action=view&cik=1321655&accession_number=0001193125-26-000123",
  "retrieved_at": "2026-01-05T10:30:00Z"
}
```

**Key Fields for Filtering:**
- `signal_strength`: Filter for "high" only
- `actionable`: Only show if I can invest
- `investment_value_usd`: Bigger bets = more conviction
- `filer_ticker`: Track specific smart money (PLTR, Berkshire, etc.)

---

### 2. Form 4 Event (Insider Confidence Signal)

**Use Case:** Detect when insiders buy their own stock (skin in the game)

```json
{
  "event_id": "FORM4_NVDA_20260103_001",
  "signal_type": "insider_buying",
  "signal_strength": "high",
  
  // Which company
  "ticker": "NVDA",
  "company_name": "NVIDIA Corporation",
  "company_cik": "0001045810",
  
  // Who's trading
  "insider_name": "Jensen Huang",
  "insider_title": "CEO",
  "insider_relationship": "officer",
  "is_beneficial_owner": true,
  
  // The trade
  "transaction_code": "P",
  "transaction_type": "Purchase",
  "shares": 50000,
  "price_per_share": 850.00,
  "transaction_value_usd": 42500000,
  
  // Before/After
  "ownership_before_shares": 8500000,
  "ownership_after_shares": 8550000,
  "ownership_after_pct": 3.2,
  
  // Timing
  "transaction_date": "2026-01-01",
  "filing_date": "2026-01-03",
  "days_to_filing": 2,
  
  // Context
  "recent_stock_performance": -8.5,
  "is_dip_buy": true,
  "earnings_in_days": 15,
  
  // Decision support
  "signal_interpretation": "CEO buying $42.5M after dip = high confidence in recovery",
  "actionable": true,
  "research_priority": "medium",
  "suggested_action": "Monitor for entry below $850",
  "conviction_score": 7.0,
  
  // Metadata
  "form_type": "4",
  "accession_number": "0001199039-26-000015",
  "sec_url": "https://www.sec.gov/cgi-bin/viewer?action=view&cik=1045810&accession_number=0001199039-26-000015",
  "retrieved_at": "2026-01-05T10:30:00Z"
}
```

**Transaction Codes:**
- `P` = Purchase (🟢 Bullish)
- `S` = Sale (🔴 Bearish, but check if scheduled)
- `M` = Exercise of option (⚠️ Neutral, usually followed by sale)
- `A` = Grant (⚠️ Neutral, compensation)

**Filtering Rules:**
- Only show `P` (purchases) above $100k
- Ignore `S` if marked as 10b5-1 plan (automated)
- Weight CEO/CFO higher than VP/Directors

---

### 3. Schedule 13G Event (Passive Ownership)

**Use Case:** Track hedge fund positions (less urgent than 13D)

```json
{
  "event_id": "13G_BRK_AAPL_20260103",
  "signal_type": "passive_ownership",
  "signal_strength": "medium",
  
  // Who owns it
  "filer_name": "Berkshire Hathaway Inc.",
  "filer_ticker": "BRK.B",
  "filer_type": "institutional_investor",
  
  // What they own
  "target_ticker": "AAPL",
  "target_name": "Apple Inc.",
  "ownership_pct": 5.8,
  "shares_owned": 920000000,
  "position_value_usd": 180000000000,
  
  // Change detection
  "ownership_change_pct": 0.5,
  "ownership_change_direction": "increase",
  "is_new_position": false,
  
  // Timing
  "filing_date": "2026-01-03",
  "report_date": "2025-12-31",
  
  // Decision support
  "actionable": true,
  "research_priority": "low",
  "suggested_action": "Hold current AAPL position",
  "conviction_score": 6.0,
  
  // Metadata
  "form_type": "SC 13G",
  "accession_number": "0001193125-26-000456",
  "retrieved_at": "2026-01-05T10:30:00Z"
}
```

---

### 4. Political Trade Event (QuiverQuant)

**Use Case:** Track Congress/Senate trades for timing edge

```json
{
  "event_id": "POLITICAL_PELOSI_NVDA_20260103",
  "signal_type": "political_trade",
  "signal_strength": "high",
  
  // Who's trading
  "politician_name": "Nancy Pelosi",
  "politician_title": "Representative",
  "party": "Democrat",
  "state": "California",
  
  // The trade
  "ticker": "NVDA",
  "transaction_type": "purchase",
  "amount_range": "$1M - $5M",
  "amount_midpoint_usd": 3000000,
  
  // Timing advantage
  "transaction_date": "2025-12-28",
  "disclosure_date": "2026-01-03",
  "days_to_disclosure": 5,
  "earnings_in_days": 10,
  "upcoming_vote": "AI Regulation Bill - Jan 15",
  
  // Context
  "politician_committee": "AI Oversight Committee",
  "has_insider_info": "likely",
  
  // Decision support
  "signal_interpretation": "Purchase before earnings + committee access = strong signal",
  "actionable": true,
  "research_priority": "high",
  "suggested_action": "Buy NVDA before Jan 10 earnings",
  "conviction_score": 8.0,
  
  // Metadata
  "source": "quiverquant",
  "retrieved_at": "2026-01-05T10:30:00Z"
}
```

---

## 📊 DASHBOARD AGGREGATION FORMAT

**Use Case:** Daily summary of actionable signals for portfolio decisions

```json
{
  "summary_date": "2026-01-05",
  "portfolio_context": {
    "cash_available": 40,
    "cash_allocated": 0,
    "cash_remaining": 40,
    "target_positions": 3
  },
  
  "high_priority_signals": [
    {
      "rank": 1,
      "ticker": "PLTR",
      "signal": "Acquired 8.5% of AI Defense Company",
      "value": "$42.5M",
      "date": "2026-01-03",
      "conviction": 8.5,
      "action": "BUY: Allocate 10% cash to PLTR shares",
      "rationale": "Strategic M&A indicates confidence in defense AI sector",
      "research_notes": ""
    },
    {
      "rank": 2,
      "ticker": "NVDA",
      "signal": "CEO bought $42.5M after 8.5% dip",
      "date": "2026-01-01",
      "conviction": 7.0,
      "action": "MONITOR: Wait for entry below $850",
      "rationale": "CEO buying dip before earnings = confidence signal",
      "research_notes": ""
    }
  ],
  
  "medium_priority_signals": [
    {
      "ticker": "AAPL",
      "signal": "Berkshire increased position by 0.5%",
      "action": "HOLD: Maintain current position"
    }
  ],
  
  "replication_plan": {
    "suggested_allocations": [
      {
        "ticker": "PLTR",
        "allocation_pct": 10,
        "reason": "M&A conviction signal",
        "entry_strategy": "Market order",
        "exit_strategy": "Trailing stop -15%"
      }
    ],
    "total_allocation": 10,
    "cash_after": 30
  },
  
  "backtest_performance": {
    "signals_followed_30d": 5,
    "avg_return": 8.2,
    "hit_rate": 0.8
  }
}
```

---

## 🔄 DATA PIPELINE FLOW

```
SEC EDGAR API
     ↓
SecEdgarClient.get_form4_filings()
     ↓
Parse & Enrich (add conviction score, actionability)
     ↓
Filter (signal_strength = high, actionable = true)
     ↓
Rank (by conviction_score DESC)
     ↓
Dashboard JSON
     ↓
Streamlit Visualization
     ↓
Investment Decision
```

---

## 💾 STORAGE STRATEGY

**Option 1: JSON Files (Simple)**
```
data/signals/
  ├── 13d/
  │   └── 2026-01-05.json
  ├── form4/
  │   └── 2026-01-05.json
  └── summary/
      └── 2026-01-05.json
```

**Option 2: SQLite (Queryable)**
```sql
CREATE TABLE signals (
    event_id TEXT PRIMARY KEY,
    signal_type TEXT,
    ticker TEXT,
    signal_strength TEXT,
    conviction_score REAL,
    actionable BOOLEAN,
    filing_date DATE,
    data JSON
);

CREATE INDEX idx_actionable ON signals(actionable, conviction_score DESC);
```

---

## ✅ VALIDATION CHECKLIST

For each schema, ensure:
- [ ] All timestamp fields in ISO 8601 format
- [ ] All monetary values in USD
- [ ] `actionable` field is boolean (not string)
- [ ] `conviction_score` is 0-10 scale
- [ ] SEC URLs are clickable for verification
- [ ] Can answer: "Should I invest based on this signal?"

---

**Next Step:** Implement these schemas in `SecEdgarClient` class and test with real PLTR/NVDA data
