# 48-County RealAuction Scraper System Architecture

## Executive Summary

**Goal**: Automate daily scraping of foreclosure and tax deed auction data from 48 Florida counties on the RealAuction platform.

**Current State**:
- ✅ Auction site directory (`auction_sites` table) with 48 counties
- ✅ Manual links in UI for all counties
- ✅ Broward County automated scraper (1 of 48)
- ✅ Palm Beach & Miami-Dade scraper (runs manually)
- ❌ No automation for remaining 45 counties

**Target State**:
- ✅ Automated daily scraping for all 48 counties
- ✅ Both foreclosure AND tax deed auctions
- ✅ Unified authentication and session management
- ✅ Robust error handling and monitoring
- ✅ GitHub Actions schedule for daily runs

**Estimated Effort**: 2-3 weeks full development

---

## System Architecture

### 1. Data Sources (Input)

**Source**: RealAuction Platform
- **Foreclosure Sites**: 40 counties via realforeclose.com
- **Tax Deed Sites**: 46 counties via realtaxdeed.com
- **Combined Sites**: 7 counties (same URL for both types)
- **Coming Soon**: 1 county (COLUMBIA - skip for now)

**Authentication**:
- Username: `gSimani`
- Password: `12261226`
- Login location: "Upper-left corner beneath county banner"

### 2. Database Schema (Output)

**Existing Tables**:
```sql
-- Tax Deed Auctions
tax_deed_bidding_items (
  composite_key TEXT PRIMARY KEY,
  county TEXT,
  tax_deed_number TEXT,
  parcel_id TEXT,
  legal_situs_address TEXT,
  opening_bid NUMERIC,
  assessed_value NUMERIC,
  item_status TEXT,
  source_url TEXT,
  scraped_at TIMESTAMPTZ,
  close_time TIMESTAMPTZ,
  auction_description TEXT
)

-- Foreclosure Cases
foreclosure_cases (
  id BIGSERIAL PRIMARY KEY,
  parcel_id TEXT,
  case_number TEXT,
  filing_date DATE,
  case_status TEXT,
  plaintiff TEXT,
  defendant TEXT,
  original_loan_amount NUMERIC,
  judgment_amount NUMERIC,
  auction_date DATE,
  auction_status TEXT,
  winning_bid NUMERIC,
  certificate_holder TEXT,
  redemption_deadline DATE,
  final_judgment_date DATE,
  property_status TEXT,
  county TEXT,
  source_url TEXT,
  scraped_at TIMESTAMPTZ
)
```

### 3. Scraper Architecture

#### Phase 1: Configuration Layer
```python
# Dynamic county configuration from auction_sites table
class CountyConfig:
    - Load from Supabase auction_sites table
    - Filter by is_active = true
    - Determine scrape types (foreclosure, tax_deed, both)
    - Build URLs dynamically
    - Handle site_type variants
```

#### Phase 2: Authentication Module
```python
class RealAuctionAuth:
    - Shared session per browser context
    - Login once, reuse for multiple counties
    - Handle session expiration
    - Cookie/localStorage persistence
    - Auto-retry on auth failures
```

#### Phase 3: Discovery Module
```python
class AuctionDiscovery:
    - Navigate to auction listing page
    - Find active auction dates dynamically
    - Parse auction calendar/schedule
    - Return list of auction IDs/dates
    - Handle no-auctions-found gracefully
```

#### Phase 4: Data Extraction Module
```python
class AuctionExtractor:
    - For each discovered auction:
      - Navigate to detail page
      - Extract structured data
      - Parse currency values
      - Parse dates
      - Capture source URL
    - Return normalized data dict
```

#### Phase 5: Storage Module
```python
class AuctionStorage:
    - Upsert to Supabase
    - Composite key deduplication
    - Track scrape metadata
    - Handle errors gracefully
    - Batch inserts for performance
```

#### Phase 6: Orchestration Layer
```python
class ScraperOrchestrator:
    - Load county configs
    - Initialize browser pool (4 parallel)
    - Authenticate once per browser
    - Distribute counties to workers
    - Aggregate results
    - Generate summary report
    - Handle failures per county
```

---

## Implementation Phases

### Phase 1: Foundation (Days 1-3)
- [ ] Design Supabase schema updates (if needed)
- [ ] Create base scraper classes
- [ ] Implement authentication module
- [ ] Add county config loader from auction_sites table
- [ ] Test with 2-3 sample counties

### Phase 2: Core Scraping (Days 4-7)
- [ ] Build auction discovery module
- [ ] Implement data extraction for tax deeds
- [ ] Implement data extraction for foreclosures
- [ ] Handle different site layouts
- [ ] Test with 10 counties

### Phase 3: Scaling & Optimization (Days 8-10)
- [ ] Add parallel browser processing
- [ ] Optimize for 48-county runtime
- [ ] Add rate limiting/politeness delays
- [ ] Test full 48-county run
- [ ] Optimize database inserts

### Phase 4: Monitoring & Reliability (Days 11-13)
- [ ] Add per-county error tracking
- [ ] Create scrape_runs table for audit log
- [ ] Build failure alerting system
- [ ] Add retry logic with exponential backoff
- [ ] Create monitoring dashboard

### Phase 5: Deployment (Days 14-15)
- [ ] Update GitHub Actions workflow
- [ ] Add environment secrets
- [ ] Configure timeout (120 minutes for 48 counties)
- [ ] Test manual trigger
- [ ] Verify daily schedule

### Phase 6: Verification & Documentation (Days 16-17)
- [ ] Run full 48-county test
- [ ] Verify data in Supabase
- [ ] Check UI tabs display data correctly
- [ ] Write operation manual
- [ ] Create troubleshooting guide

---

## Technical Specifications

### Performance Targets
- **Total Runtime**: <2 hours for 48 counties
- **Per County**: ~2-3 minutes average
- **Parallel Workers**: 4 browsers
- **Batch Size**: 12 counties per worker

### Error Handling
- **Per-County Isolation**: One county failure doesn't stop others
- **Retry Logic**: 3 attempts with exponential backoff
- **Graceful Degradation**: Continue on partial failures
- **Detailed Logging**: Per-county success/failure logs
- **Alert Threshold**: >10 counties fail → send alert

### Monitoring
```python
scrape_runs (
  id BIGSERIAL PRIMARY KEY,
  run_date DATE,
  start_time TIMESTAMPTZ,
  end_time TIMESTAMPTZ,
  total_counties INT,
  successful_counties INT,
  failed_counties INT,
  total_auctions_found INT,
  total_auctions_saved INT,
  error_summary JSONB,
  run_metadata JSONB
)

county_scrape_logs (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT REFERENCES scrape_runs(id),
  county TEXT,
  scrape_type TEXT, -- 'foreclosure', 'tax_deed', 'both'
  status TEXT, -- 'success', 'failure', 'partial'
  auctions_found INT,
  auctions_saved INT,
  duration_seconds INT,
  error_message TEXT,
  scraped_at TIMESTAMPTZ
)
```

---

## File Structure

```
scripts/
├── realauction_48_county_scraper.py       # Main orchestrator
├── realauction_auth.py                    # Authentication module
├── realauction_discovery.py               # Auction discovery
├── realauction_extractors/
│   ├── tax_deed_extractor.py             # Tax deed data extraction
│   └── foreclosure_extractor.py          # Foreclosure data extraction
├── realauction_storage.py                 # Database operations
└── realauction_config.py                  # Configuration loader

.github/workflows/
└── daily-realauction-48-counties.yml      # GitHub Action

supabase/migrations/
└── 20250106_realauction_monitoring.sql    # Monitoring tables
```

---

## Deployment Configuration

### GitHub Action Schedule
```yaml
name: Daily RealAuction 48-County Scraper

on:
  schedule:
    - cron: '0 3 * * *'  # 10 PM EST = 3 AM UTC (after business hours)
  workflow_dispatch:     # Manual trigger

jobs:
  scrape-48-counties:
    runs-on: ubuntu-latest
    timeout-minutes: 120  # 2 hours max

    steps:
      - Checkout code
      - Setup Python 3.12
      - Install Playwright + dependencies
      - Load Supabase credentials
      - Run scraper
      - Upload artifacts (JSON backups)
      - Send failure alerts
```

### Environment Secrets Required
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `REALAUCTION_USERNAME` (gSimani)
- `REALAUCTION_PASSWORD` (12261226)

---

## Risks & Mitigation

### Risk 1: Site Structure Changes
**Impact**: High
**Mitigation**:
- Version detection in scraper
- Fallback to alternative selectors
- Alert on unexpected DOM structure
- Manual review queue for failures

### Risk 2: Rate Limiting / IP Blocking
**Impact**: Medium
**Mitigation**:
- Respectful delays between requests (2-5 seconds)
- Rotate user agents
- Use GitHub Actions IP rotation
- Monitor for 429/403 responses

### Risk 3: Long Runtime (>2 hours)
**Impact**: Medium
**Mitigation**:
- Parallel processing (4 workers)
- Skip coming_soon counties
- Cache authentication per browser
- Optimize DOM queries

### Risk 4: Data Quality Issues
**Impact**: Medium
**Mitigation**:
- Validate all extracted data
- Flag suspicious values
- Compare against historical data
- Manual review for outliers

---

## Success Metrics

### Week 1 (Post-Deployment)
- [ ] All 48 counties scraped successfully
- [ ] <5% failure rate per county
- [ ] Data appears correctly in UI tabs
- [ ] Runtime <2 hours

### Month 1 (Ongoing Operations)
- [ ] 95%+ daily success rate
- [ ] <10 user-reported data issues
- [ ] Zero missed days
- [ ] Monitoring dashboard shows green

---

## Next Steps

**Decision Point**: Do you want to proceed with this implementation?

**Options**:
1. **Full Implementation** (2-3 weeks) - Build entire system as described
2. **Phased Rollout** (Week 1: Tax Deed only, Week 2: Add Foreclosures)
3. **Pilot Program** (Start with 10 high-priority counties, expand gradually)
4. **Alternative Approach** (Different architecture or tools)

**Questions for You**:
1. Which counties are highest priority? (So we can test with those first)
2. Do you need foreclosure data, tax deed data, or both?
3. Is 2-3 weeks acceptable timeline?
4. Any specific monitoring/alerting requirements?

---

**Created**: 2025-01-06
**Status**: Awaiting approval to begin implementation
