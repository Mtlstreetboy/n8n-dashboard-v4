# 🎯 SEC EDGAR Integration - Implementation Roadmap

**Objective:** Add M&A & Insider Trading Detection to Political Trading Pipeline  
**Based on:** Tracking Hedge Fund and SEC Filings.md  
**Timeline:** 4-5 weeks  
**Complexity:** Medium-High

---

## 📍 PROJECT SCOPE

### What We're Building
```
Political Trading Pipeline (QuiverQuant)
         ↓
    ✅ EXISTING
   - Congress trades
   - Senate trades
   - House trades
   - Insider trades (by person)
         ↓
         + NEW (SEC EDGAR)
         ├─ Schedule 13D (M&A >5%)
         ├─ Form 4 (insider trades by company)
         └─ Schedule 13G (beneficial ownership changes)
         ↓
    Dashboard Integration
   "Smart Money + M&A Signals"
```

### Success Criteria
- ✅ Detect when a company acquires >5% stake in another (Schedule 13D)
- ✅ Track insider trading activity at company level (Form 4)
- ✅ Find the PLTR case: "PLTR acquired X% of [Company]"
- ✅ Real-time alerts (5 business days)
- ✅ Integrated dashboard view

---

## 📋 DETAILED BREAKDOWN

### PHASE 1: Research & Setup (1 week)

#### Task 1.1: SEC EDGAR API Investigation
**Owner:** You / AI  
**Duration:** 2-3 days  
**Deliverable:** `docs/EDGAR/API_EXPLORATION.md`

**What to discover:**
- [ ] Test SEC EDGAR REST API endpoints
- [ ] Understand CIK lookup mechanism
- [ ] Download sample 13D filing (XML format)
- [ ] Download sample Form 4 filing (XML format)
- [ ] Test rate limits & response times
- [ ] Document XML structure of each form type

**Tools:**
```bash
# Live test
curl "https://data.sec.gov/api/xbrl/companyfacts/CIK0001423053.json"

# Manual EDGAR search
https://www.sec.gov/cgi-bin/browse-edgar
```

**Reference:**
→ See "Tracking..." doc Section 7.1 (Manual EDGAR Navigation)

---

#### Task 1.2: Set Up Local SEC EDGAR Parser
**Owner:** You / AI  
**Duration:** 2-3 days  
**Deliverable:** `services/sec_edgar/sec_client.py`

**What to build:**
- [ ] Create `SecEdgarClient` class
- [ ] Implement CIK lookup by ticker/company name
- [ ] Implement Form 13D fetcher
- [ ] Implement Form 4 fetcher
- [ ] Implement Schedule 13G fetcher
- [ ] Error handling + retry logic
- [ ] Rate limiting (max 1 req/sec)

**Code skeleton:**
```python
class SecEdgarClient:
    def __init__(self, rate_limit=1.0):  # 1 req/sec
        self.base_url = "https://data.sec.gov/api"
    
    def lookup_cik(self, ticker: str) -> str:
        """Get CIK from ticker symbol"""
    
    def get_13d_filings(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """Get Schedule 13D filings (acquisitions >5%)"""
    
    def get_form4_filings(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """Get Form 4 filings (insider trades)"""
    
    def get_13g_filings(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """Get Schedule 13G filings (beneficial ownership)"""
```

**Reference:**
→ See "Tracking..." doc Section 7.1 (CIK Lookup, EDGAR Navigation)

---

#### Task 1.3: Data Structure Design
**Owner:** You  
**Duration:** 1 day  
**Deliverable:** `docs/EDGAR/DATA_SCHEMA.md`

**Define:**
- [ ] JSON schema for 13D events
- [ ] JSON schema for Form 4 events
- [ ] JSON schema for 13G events
- [ ] Database schema (if using SQLite/PostgreSQL)
- [ ] CSV output format

**Example 13D Event:**
```json
{
  "filer_cik": "0001423053",
  "filer_name": "Citadel Advisors LLC",
  "target_ticker": "NVDA",
  "target_name": "NVIDIA Corporation",
  "ownership_pct": 5.2,
  "shares_owned": 1234567,
  "filing_date": "2026-01-03",
  "filing_deadline": "2026-01-08",
  "transaction_date": "2025-12-30",
  "item_4_intent": "acquisition_for_control",
  "item_4_text": "Filer intends to acquire majority stake...",
  "form_type": "SC 13D"
}
```

---

### PHASE 2: Core Development (2 weeks)

#### Task 2.1: SEC Client - Implement & Test
**Owner:** AI  
**Duration:** 3-4 days  
**Deliverable:** `services/sec_edgar/sec_client.py` (complete + tested)

**Implementation steps:**
1. [ ] Create CIK lookup (ticker → CIK)
2. [ ] Create 13D fetcher with XML parsing
3. [ ] Create Form 4 fetcher with XML parsing
4. [ ] Create 13G fetcher with XML parsing
5. [ ] Unit tests for each function
6. [ ] Integration test (full flow)

**Test cases:**
```python
# Test case 1: Find PLTR's acquisitions
pltr_13d = client.get_13d_filings("PLTR", days=365)
# Expected: Find Palantir's 5%+ stakes in other companies

# Test case 2: Find insider activity at PLTR
pltr_form4 = client.get_form4_filings("PLTR", days=90)
# Expected: CEO/Directors buying/selling PLTR shares

# Test case 3: CIK lookup
pltr_cik = client.lookup_cik("PLTR")
# Expected: 0001321655
```

**Reference:**
→ See "Tracking..." doc Section 7.2 (Tools Comparison - API Model)

---

#### Task 2.2: Parser - Extract Intelligence
**Owner:** AI  
**Duration:** 3-4 days  
**Deliverable:** `services/sec_edgar/sec_parser.py`

**What to build:**
- [ ] Parse Item 4 from Schedule 13D (intent, purpose)
- [ ] Extract insider relationship from Form 4 (CEO, Director, VP, etc.)
- [ ] Calculate ownership percentage changes
- [ ] Flag "13G to 13D switch" (signal!)
- [ ] Sentiment/intent classification (Positive/Neutral/Negative)

**Parser logic for 13D Item 4:**
```python
def classify_intent(item_4_text: str) -> str:
    """
    Classify intent from Item 4:
    - "acquisition_for_control" → Seeking majority
    - "activist_pressure" → Forcing changes
    - "investment_only" → Passive stake
    - "passive_parking" → Treasury building
    """
```

**Reference:**
→ See "Tracking..." doc Section 3.2.1 (13D Item 4 - Purpose)

---

#### Task 2.3: Pipeline Integration
**Owner:** You / AI  
**Duration:** 3-5 days  
**Deliverable:** Modified `prod/automation/political_trading_pipeline.py`

**Integration points:**
```python
# PHASE 1B: Add SEC EDGAR to political trading extraction
Phase_1_QuiverQuant_Trades()     # ← Existing
    ↓
Phase_1B_SEC_EDGAR_13D()        # ← NEW: M&A activity
Phase_1B_SEC_EDGAR_Form4()      # ← NEW: Insider trades
    ↓
Phase_2_Generate_Config()       # ← Add EDGAR tickers
    ↓
Phase_3_Collect_Data()
Phase_4_Analyze()
Phase_5_Generate_Dashboard()
```

**New config format:**
```python
# political_companies_config.py should now include:
{
    "ticker": "NVDA",
    "name": "NVIDIA Corp",
    "political_trades_60d": 12,       # ← QuiverQuant
    "ma_activity_90d": 3,              # ← NEW: 13D filings
    "insider_trades_30d": 8,           # ← NEW: Form 4
    "acquisition_target": False,       # ← NEW: Is being acquired?
}
```

**Reference:**
→ See "Tracking..." doc Section 8 (Fund Archetypes - Strategy Specific)

---

### PHASE 3: Dashboard Integration (1.5 weeks)

#### Task 3.1: Create M&A Data Module
**Owner:** AI  
**Duration:** 2-3 days  
**Deliverable:** `prod/analysis/sec_edgar_analyzer.py`

**What to build:**
- [ ] Aggregate 13D/Form 4 data per ticker
- [ ] Generate M&A sentiment score (-1 to +1)
- [ ] Create alerts for high-conviction plays
- [ ] Timeline of M&A activity

**Output format:**
```json
{
  "ticker": "NVDA",
  "m_and_a_activity": {
    "recent_13d_filings": [
      {
        "acquirer": "Citadel Advisors",
        "ownership_pct": 5.2,
        "intent": "acquisition_for_control",
        "filing_date": "2026-01-03",
        "days_old": 2
      }
    ],
    "insider_activity": [
      {
        "insider_name": "Jensen Huang",
        "title": "CEO",
        "transaction": "buy",
        "shares": 50000,
        "date": "2026-01-02"
      }
    ],
    "m_and_a_score": 0.65,  # ← -1 (negative M&A) to +1 (positive)
    "alert_level": "HIGH"
  }
}
```

**Reference:**
→ See "Tracking..." doc Section 6 (Cloning Methodologies - Best Ideas)

---

#### Task 3.2: Extend Dashboard HTML
**Owner:** You / AI  
**Duration:** 3-5 days  
**Deliverable:** Modified `prod/dashboard/dashboard_v4_split.html`

**Add new views:**
- [ ] "M&A Activity" tab (per ticker)
- [ ] "Insider Trading" tab
- [ ] "Beneficial Ownership" timeline
- [ ] "13D to 13G Switch" alerts (red flags)

**New dashboard section example:**
```html
<!-- M&A Activity Level 2 View -->
<div className="m-and-a-activity">
  <h3>M&A & Institutional Moves</h3>
  
  <table>
    <tr>
      <td>Recent 13D Filings (5% Stakes)</td>
      <td>Form 4 Insider Activity</td>
      <td>13G Changes (Beneficial Ownership)</td>
    </tr>
  </table>
  
  <timeline>
    {/* Timeline of acquisition attempts */}
  </timeline>
</div>
```

**Reference:**
→ See "Tracking..." doc Section 3.2-3.3 (13D/13G Interpretation)

---

#### Task 3.3: Generate M&A Dashboard
**Owner:** AI  
**Duration:** 2-3 days  
**Deliverable:** New script `prod/analysis/generate_edgar_views.py`

**What to do:**
- [ ] Combine SEC data with sentiment analysis
- [ ] Create HTML sections for M&A
- [ ] Inject into main dashboard
- [ ] Version as `dashboard_v4_with_edgar.html`

**Reference:**
→ See "Tracking..." doc Section 7.2 (Tools - Heatmaps)

---

### PHASE 4: Testing & Validation (1 week)

#### Task 4.1: Unit Tests
**Owner:** AI  
**Duration:** 2 days  
**Deliverable:** `tests/test_sec_edgar_client.py`

**Test coverage:**
- [ ] CIK lookup (edge cases)
- [ ] 13D parsing (malformed XML handling)
- [ ] Form 4 parsing (different transaction codes)
- [ ] Rate limiting
- [ ] Error handling (404, 403, timeouts)

**Test command:**
```bash
pytest tests/test_sec_edgar_client.py -v
```

---

#### Task 4.2: Integration Test - PLTR Case Study
**Owner:** You  
**Duration:** 2-3 days  
**Deliverable:** `tests/test_pltr_case_study.py`

**Test scenario:**
```python
def test_pltr_acquisitions():
    """Find: PLTR acquired >5% of [Company]"""
    # Query: All 13D filings where filer_ticker = "PLTR"
    # Expected: Return list of companies PLTR acquired stakes in
    
def test_pltr_insider_activity():
    """Find: PLTR insiders trading PLTR shares"""
    # Query: All Form 4 filings at PLTR
    # Expected: CEO/CFO buy signals, sell signals
    
def test_sector_rotation():
    """Find: Multiple institutions moving into same sector"""
    # Query: 13D filings clustering (heatmap)
    # Expected: Identify hot sectors (e.g., AI, Defense)
```

**Run:**
```bash
pytest tests/test_pltr_case_study.py -v -s
```

---

#### Task 4.3: End-to-End Pipeline Test
**Owner:** You / AI  
**Duration:** 2-3 days  
**Deliverable:** Working `political_trading_pipeline.py` with SEC data

**Test flow:**
1. [ ] Launch pipeline with SEC enabled
2. [ ] Verify 13D data ingested
3. [ ] Verify Form 4 data ingested
4. [ ] Check generated config includes M&A data
5. [ ] Verify dashboard renders M&A sections
6. [ ] Manual QA: Does it look right?

**Command:**
```bash
python prod/automation/political_trading_pipeline.py --include-sec-edgar
```

---

## 🗓️ TIMELINE SUMMARY

| Phase | Task | Duration | Owner | Deliverable |
|-------|------|----------|-------|-------------|
| **1** | 1.1: API Research | 2-3 days | You/AI | API_EXPLORATION.md |
| **1** | 1.2: SEC Client | 2-3 days | AI | sec_client.py |
| **1** | 1.3: Schema Design | 1 day | You | DATA_SCHEMA.md |
| **2** | 2.1: Implementation | 3-4 days | AI | sec_client.py (complete) |
| **2** | 2.2: Parser | 3-4 days | AI | sec_parser.py |
| **2** | 2.3: Pipeline Integration | 3-5 days | You/AI | modified political_trading_pipeline.py |
| **3** | 3.1: M&A Module | 2-3 days | AI | sec_edgar_analyzer.py |
| **3** | 3.2: Dashboard Extend | 3-5 days | You/AI | modified dashboard_v4_split.html |
| **3** | 3.3: Generate Views | 2-3 days | AI | generate_edgar_views.py |
| **4** | 4.1: Unit Tests | 2 days | AI | test_sec_edgar_client.py |
| **4** | 4.2: PLTR Case | 2-3 days | You | test_pltr_case_study.py |
| **4** | 4.3: E2E Test | 2-3 days | You/AI | working pipeline |
| | **TOTAL** | **~4-5 weeks** | Mixed | **Integrated Dashboard** |

---

## 🎯 QUICK WINS (Do First)

If time is limited, prioritize:

1. **Task 1.1** (2-3 days) → Understand SEC API
2. **Task 2.1** (3-4 days) → Build SEC Client
3. **Task 2.3** (3-5 days) → Integrate into pipeline
4. **Task 4.2** (2-3 days) → Validate PLTR case

**Result after 2 weeks:** "PLTR acquired X% of [Company] on [date]"

Then extend to dashboard later.

---

## 📚 REFERENCE MAP

**For each task, refer to:**

| Task | Section in "Tracking..." Doc |
|------|------------------------------|
| 1.1: API Research | Section 7.1 (Manual EDGAR Navigation) |
| 1.2: SEC Client | Section 7.2 (Automated Tools - API Model) |
| 2.1: Parsing 13D | Section 3.2 (Schedule 13D - Item 4) |
| 2.1: Parsing Form 4 | Section 4 (Forms 3, 4, 5 - Insider Sentiment) |
| 2.1: Parsing 13G | Section 3.3 (Schedule 13G - Passive Giant) |
| 2.3: Integration | Section 8 (Fund Archetypes - Strategy Selection) |
| 3.1: Sentiment | Section 6 (Cloning - Best Ideas Strategy) |
| 4.2: PLTR Case | Section 2.4 (Confidential Treatment - Amendment Indicator) |

---

## 🚀 NEXT STEPS

1. **Review this roadmap** - Any changes?
2. **Approve Task 1.1** - Ready to explore SEC API?
3. **Assign ownership** - You lead or AI lead?
4. **Set start date** - When do we kick off?

---

**Questions?** Ask me to clarify any task.  
**Ready to start?** Let me know which task to begin with.
