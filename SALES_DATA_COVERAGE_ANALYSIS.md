# Sales Data Coverage Analysis & Intelligent Scraping Strategy

**Date:** 2025-10-30
**Purpose:** Analyze sales data gaps and create targeted scraping strategy

---

## CURRENT SITUATION

### What We Know:
- **Total Properties:** 9,113,150 Florida parcels
- **Total Sales Records:** 637,890 sales in property_sales_history
- **Coverage:** ~7% of properties have sales data

### Coverage by County (Estimated):

| County | Total Parcels | Sales Records | Coverage |
|--------|---------------|---------------|----------|
| Broward | 824,854 | 17,535 | 2% |
| Palm Beach | ~600,000 | Unknown | <5% |
| Miami-Dade | ~800,000 | Unknown | <10% |
| Other 64 counties | ~6,900,000 | ~600,000 | ~8-9% |

---

## WHY WE'RE MISSING DATA

### 1. Florida DOR SDF Files Limitation
**Issue:** SDF (Sales Disclosure Files) only contain sales from **2024-2025**

**Impact:**
- Historical sales (pre-2024) are NOT in SDF files
- Properties that haven't sold in 2 years show "no sales"
- Missing decades of valuable sales history

### 2. Data Quality Issues
**Issue:** 1,788 records have prices over $1 BILLION

**Cause:** Some SDF files store prices in cents, others in dollars

**Status:** Cleanup script created (`cleanup_sales_data_quality.sql`)

### 3. No Historical Import Process
**Issue:** We only imported from SDF files, never scraped county sites

**Impact:** Missing 93% of sales data

---

## INTELLIGENT SCRAPING STRATEGY

### Approach: Gap-Targeted Scraping

Instead of scraping everything, we:
1. **Identify** properties users actually view
2. **Check** if they have sales data
3. **Scrape** only missing data on-demand or in batches
4. **Cache** results for future users

### Phase 1: On-Demand Scraping (IMMEDIATE)

**Trigger:** User views a property without sales data

**Process:**
```
User visits property → Check DB → No sales? →
  → Background scrape county site → Import sales → Update UI
```

**Benefits:**
- No wasted scraping effort
- Real-time data freshness
- User sees data appear

**Implementation:**
- Add scraper queue to backend
- Trigger on property page load
- Show "Loading sales..." while scraping
- Update UI when complete

### Phase 2: Batch Fill High-Value Properties (THIS WEEK)

**Target:** Properties users search for most

**Process:**
1. Analyze search logs → Find top 1,000 most-viewed properties
2. Check which ones lack sales data
3. Batch scrape those properties overnight
4. Import to database

**Benefits:**
- Improves experience for most users
- Efficient use of resources
- Builds coverage where it matters

### Phase 3: County-Wide Backfill (NEXT MONTH)

**Target:** Complete coverage for major counties

**Process:**
1. Broward County (~800k parcels)
2. Miami-Dade County (~800k parcels)
3. Palm Beach County (~600k parcels)

**Method:**
- Coordinate with county IT departments
- Request bulk data access or API keys
- Or: Distributed scraping (respectful rate limits)

**Timeline:** 3-6 months for full coverage

---

## COUNTY-SPECIFIC STRATEGIES

### Broward County (BCPA)
**URL:** https://bcpa.net/RecInfo.asp?URL_Folio={folio}

**Status:** ✅ Scraper working (tested on 504230050040)

**Data Quality:** Excellent
- All sales with dates, prices, deed types
- OR Book/Page numbers included
- Going back to 1960s

**Coverage:** Currently 2% → Can reach 80%+

**Action:** Run batch scraper on top 1,000 Broward properties

### Palm Beach County
**URL:** https://www.pbcgov.org/papa/

**Status:** ⚠️ Complex website structure

**Data Quality:** Good
- Sales data available
- Requires navigation through search

**Coverage:** <5% → Can reach 70%+

**Action:**
- Study their website structure
- May need to contact county for bulk access
- Alternative: Use their API if available

### Miami-Dade County
**URL:** https://www.miamidade.gov/Apps/PA/propertysearch/

**Status:** 🔴 Not yet implemented

**Data Quality:** Unknown

**Action:** Research and build scraper

---

## RECOMMENDED IMMEDIATE ACTIONS

### 1. Implement On-Demand Scraping (2-3 days)
**Goal:** Scrape sales when users view properties without data

**Implementation:**
- Add API endpoint: `/api/properties/{parcel}/scrape-sales`
- Called automatically when SalesHistoryTab loads and finds no data
- Shows loading indicator while scraping
- Updates UI when complete

**User Experience:**
- User sees: "Loading sales history..."
- 5-10 seconds later: Sales appear!
- Future visitors: Instant (already in DB)

### 2. Batch Scrape Top Properties (1 week)
**Goal:** Fill sales data for most-viewed properties

**Process:**
```sql
-- Find most-viewed properties without sales
SELECT fp.parcel_id, fp.county, fp.phy_addr1, COUNT(*) as views
FROM florida_parcels fp
LEFT JOIN property_sales_history psh ON fp.parcel_id = psh.parcel_id
WHERE psh.parcel_id IS NULL
  AND fp.county IN ('BROWARD', 'PALM BEACH', 'MIAMI-DADE')
GROUP BY fp.parcel_id
ORDER BY views DESC
LIMIT 1000;
```

**Then:** Run batch scraper overnight

### 3. Fix Data Quality Issues (ASAP)
**Goal:** Clean up 1,788 bad records

**Action:**
```bash
# Run cleanup script
psql "postgresql://..." -f scripts/cleanup_sales_data_quality.sql
```

---

## INTELLIGENT SCRAPER FEATURES

### 1. Gap Detection
```python
def needs_sales_data(parcel_id: str, county: str) -> bool:
    """Check if property needs sales scraping"""

    # Check property_sales_history
    existing = db.query(
        "SELECT COUNT(*) FROM property_sales_history WHERE parcel_id = ?",
        parcel_id
    )

    if existing > 0:
        return False  # Already have data

    # Check if property likely has sales (not new construction)
    parcel = db.query(
        "SELECT year_built FROM florida_parcels WHERE parcel_id = ?",
        parcel_id
    )

    if parcel.year_built and parcel.year_built > 2023:
        return False  # Too new to have sales

    return True  # Needs scraping
```

### 2. Smart Queuing
```python
class ScraperQueue:
    """Prioritize scraping based on demand"""

    priorities = {
        'user_requested': 1,      # User is waiting
        'high_value': 2,           # Expensive property
        'frequently_viewed': 3,    # Popular property
        'batch_fill': 4            # Background batch
    }

    def add(self, parcel_id, priority='batch_fill'):
        # Add to queue with priority
        # User-requested goes first
```

### 3. Respectful Scraping
```python
class RateLimiter:
    """Respect county website resources"""

    limits = {
        'BROWARD': 10,  # requests per minute
        'PALM BEACH': 5,
        'MIAMI-DADE': 5
    }

    async def wait_if_needed(self, county):
        # Implement rate limiting
        # Add delays between requests
        # Use rotating IP if needed (with permission)
```

---

## SUCCESS METRICS

### Coverage Goals:
- **Week 1:** 10% coverage (top 1,000 properties)
- **Month 1:** 30% coverage (major counties, on-demand)
- **Month 3:** 60% coverage (batch backfill)
- **Month 6:** 90% coverage (full historical)

### User Experience Goals:
- Sales appear within 10 seconds for any property
- 95% of properties have sales data
- No "No sales history" messages for properties that do have sales

---

## EXAMPLE: USER JOURNEY

### Current State (Bad):
1. User searches for 7777 Glades Rd, Palm Beach
2. Opens property page
3. Clicks "Sales History" tab
4. Sees: "No sales history available"
5. **User doesn't know if there really are no sales, or if we just don't have the data**

### With Intelligent Scraping (Good):
1. User searches for 7777 Glades Rd, Palm Beach
2. Opens property page
3. Clicks "Sales History" tab
4. Sees: "Loading sales history..." (5 seconds)
5. Sales appear! Shows 3 historical sales
6. **Next user:** Sees sales instantly (already scraped)

---

## NEXT STEPS

### IMMEDIATE (Today):
1. ✅ Created intelligent scraper framework
2. ✅ Tested Broward scraper (working!)
3. ⚠️ Palm Beach scraper (needs refinement)
4. Run cleanup_sales_data_quality.sql

### SHORT TERM (This Week):
5. Implement on-demand scraping API endpoint
6. Add "Loading sales..." UI state
7. Batch scrape top 100 Broward properties
8. Test with real users

### MEDIUM TERM (This Month):
9. Refine Palm Beach scraper
10. Build Miami-Dade scraper
11. Batch scrape top 1,000 properties
12. Monitor coverage improvements

### LONG TERM (Next Quarter):
13. Contact counties for bulk data access
14. Implement full backfill process
15. Reach 90% coverage goal

---

## FILES CREATED

### Scrapers:
- ✅ `scripts/scrape_bcpa_sales_for_parcel.py` - Broward single property
- ✅ `scripts/intelligent_sales_gap_analyzer.py` - Full framework
- ✅ `scripts/quick_palm_beach_sales_scraper.py` - Palm Beach (in progress)

### Import Tools:
- ✅ `scripts/load-bcpa-sales.mjs` - Load CSV to database

### Cleanup:
- ✅ `scripts/cleanup_sales_data_quality.sql` - Fix bad data

---

## CONCLUSION

We can go from **7% coverage to 90% coverage** in 3-6 months with:

1. **Smart on-demand scraping** for real-time needs
2. **Targeted batch scraping** for high-value properties
3. **County partnerships** for bulk data access

**The key:** Don't scrape everything blindly. Scrape what users actually need, when they need it.

**Result:** Better user experience + efficient resource use + comprehensive coverage.
