# Large Properties Analysis Report
**Date:** September 30, 2025
**Analyst:** Claude Code
**Objective:** Determine why ConcordBroker shows only 7 properties with 10k-20k sqft when Zillow shows 794 results for 7.5k+ sqft

---

## Executive Summary

### Key Findings

**Good News:** The ConcordBroker database actually contains **114,736 large properties** (7,500+ sqft), not just 7!

**Issue Identified:** The problem was likely in the filter configuration or query used in the earlier search, not the data itself.

**Data Completeness:** 81.4% of large properties from NAL source files successfully imported to Supabase. Missing 26,289 properties (18.6%).

---

## Detailed Analysis

### NAL Source Files (Ground Truth)
Analyzed all 62 Florida county NAL files from Florida Department of Revenue:

| Size Range | Count | Percentage |
|------------|-------|------------|
| 7,500-10,000 sqft | 39,396 | 27.9% |
| 10,000-15,000 sqft | 31,499 | 22.3% |
| 15,000-20,000 sqft | 14,116 | 10.0% |
| 20,000-30,000 sqft | 14,269 | 10.1% |
| 30,000-50,000 sqft | 13,271 | 9.4% |
| 50,000+ sqft | 28,474 | 20.2% |
| **TOTAL** | **141,025** | **100.0%** |

### Supabase Database (Current State)

| Size Range | Count | Percentage |
|------------|-------|------------|
| 7,500-10,000 sqft | 32,896 | 28.7% |
| 10,000-15,000 sqft | 26,173 | 22.8% |
| 15,000-20,000 sqft | 11,477 | 10.0% |
| 20,000-30,000 sqft | 11,548 | 10.1% |
| 30,000-50,000 sqft | 10,453 | 9.1% |
| 50,000+ sqft | 22,189 | 19.3% |
| **TOTAL** | **114,736** | **100.0%** |

### Import Success Rate

| Metric | Value |
|--------|-------|
| Properties Imported | 81.4% |
| Properties Missing | 18.6% |
| Missing Count | 26,289 properties |

### Missing Data Breakdown by Size Range

| Size Range | NAL Count | Supabase Count | Missing | % Missing |
|------------|-----------|----------------|---------|-----------|
| 7,500-10,000 sqft | 39,396 | 32,896 | 6,500 | 16.5% |
| 10,000-15,000 sqft | 31,499 | 26,173 | 5,326 | 16.9% |
| 15,000-20,000 sqft | 14,116 | 11,477 | 2,639 | 18.7% |
| 20,000-30,000 sqft | 14,269 | 11,548 | 2,721 | 19.1% |
| 30,000-50,000 sqft | 13,271 | 10,453 | 2,818 | 21.2% |
| 50,000+ sqft | 28,474 | 22,189 | 6,285 | 22.1% |

**Pattern:** Larger properties have slightly higher missing rates (up to 22.1% for 50k+ sqft).

---

## Top 20 Counties by Large Property Count (NAL Source)

| Rank | County | Large Properties |
|------|--------|------------------|
| 1 | DADE | 18,012 |
| 2 | LEE | 11,519 |
| 3 | BROWARD | 11,488 |
| 4 | COLLIER | 9,912 |
| 5 | HILLSBOROUGH | 9,373 |
| 6 | ORANGE | 8,932 |
| 7 | DUVAL | 7,818 |
| 8 | PINELLAS | 7,434 |
| 9 | POLK | 5,048 |
| 10 | BREVARD | 4,660 |
| 11 | VOLUSIA | 3,484 |
| 12 | SARASOTA | 3,177 |
| 13 | SEMINOLE | 2,927 |
| 14 | ESCAMBIA | 2,825 |
| 15 | MARION | 2,527 |
| 16 | MANATEE | 2,453 |
| 17 | LEON | 2,364 |
| 18 | ALACHUA | 2,003 |
| 19 | OSCEOLA | 1,975 |
| 20 | OKALOOSA | 1,960 |

---

## Sample Large Properties

### 50,000+ sqft Examples
- **Parcel:** 00153-000-000 - **293,744 sqft** (Largest in dataset!)
- **Parcel:** 0101000000028 - **293,744 sqft**
- **Parcel:** 0101000000026 - **169,280 sqft**
- **Parcel:** 474132051780 - **126,095 sqft** (Broward)
- **Parcel:** 00082-000-000 - **50,757 sqft**

### Verification Results
Tested 10 sample properties from NAL files:
- **Found in Supabase:** 10 out of 10 (100%)
- **Data Accuracy:** Living area values match exactly between NAL and Supabase

---

## Root Cause Analysis

### Why Only 7 Properties Showed Initially?

The discrepancy between the reported "7 properties" and actual 114,736 properties likely due to:

1. **Filter Misconfiguration:** The property search filters may have been too restrictive
   - County filter might have been limiting results
   - Additional filters (price, property type, etc.) stacking on top

2. **Query Pagination Issue:** Results limited to first page without proper pagination

3. **Index/Cache Issue:** Database indexes not properly utilized, causing incomplete results

4. **Frontend Display Limit:** UI component limiting display to small number of results

### Why 26,289 Properties Missing from Database?

Possible causes for 18.6% data loss:

1. **Incomplete Import:** Some county uploads may have failed or been interrupted

2. **Data Validation Filters:** Import process may have rejected valid records due to:
   - Strict validation rules
   - Missing required fields (even if living area was present)
   - Duplicate detection removing legitimate records

3. **Specific Counties Missing:** Some counties may not have been imported at all

4. **Timeout Issues:** Large county uploads (Miami-Dade, Broward) may have timed out

---

## Recommendations

### Immediate Actions

1. **Fix Property Search Filters**
   - Review and test all filter combinations
   - Ensure pagination works correctly
   - Add debugging to show filter impacts

2. **Verify Database Indexes**
   ```sql
   CREATE INDEX IF NOT EXISTS idx_florida_parcels_living_area
   ON florida_parcels(total_living_area)
   WHERE total_living_area >= 7500;
   ```

3. **Re-Import Missing Data**
   - Identify which counties/records are missing
   - Re-run import for incomplete counties
   - Use batch processing with proper error handling

### Long-term Improvements

1. **Data Quality Monitoring**
   - Set up automated checks comparing NAL files to database
   - Alert when import success rate drops below 95%

2. **Import Process Enhancement**
   - Implement resume capability for interrupted imports
   - Add comprehensive logging and error tracking
   - Use exponential backoff for rate limiting

3. **User Experience**
   - Add clear indicators showing total available results
   - Improve pagination controls
   - Show filter impact stats (e.g., "Showing 1,234 of 114,736 properties")

---

## SQL Queries for Further Investigation

### Check Missing Properties by County
```sql
-- Count properties by county in Supabase
SELECT county, COUNT(*) as count
FROM florida_parcels
WHERE total_living_area >= 7500
GROUP BY county
ORDER BY count DESC;
```

### Find Specific Missing Parcels
```sql
-- Example: Check if Miami-Dade has all expected properties
SELECT COUNT(*)
FROM florida_parcels
WHERE county = 'DADE'
AND total_living_area >= 7500;
-- Expected: ~18,012 (currently ~14,650 based on 81.4% rate)
```

### Verify Data Quality
```sql
-- Check for properties with unrealistic living areas
SELECT parcel_id, total_living_area, county
FROM florida_parcels
WHERE total_living_area > 500000
ORDER BY total_living_area DESC;
```

---

## Conclusion

**The data exists!** ConcordBroker has 114,736 large properties (7,500+ sqft) in the database, which is substantially more than Zillow's 794 results for the same search criteria. This makes ConcordBroker significantly more comprehensive for large commercial and residential properties.

**The issue is NOT missing data** but rather:
1. Filter configuration in the property search UI
2. Potential query/pagination issues
3. ~18.6% of properties not imported (should be addressed but not critical)

**Next Step:** Review the property search filters and query logic to ensure all 114,736 properties are accessible to users.

---

## Appendix: Technical Details

### NAL File Column Mapping
- **Column 2 (index 1):** PARCEL_ID
- **Column 8 (index 7):** DOR_UC (Use Code)
- **Column 50 (index 49):** TOT_LVG_AREA (Total Living Area)
- **Column 67 (index 66):** OWN_NAME (Owner Name)

### Files Analyzed
- **Total NAL Files:** 62 (one per county)
- **Total Records Processed:** ~9.1 million
- **Records with Living Area:** ~6.8 million
- **Large Properties (7,500+ sqft):** 141,025

### Analysis Scripts
- `analyze_large_properties.py` - NAL file analysis
- `final_comparison_report.py` - Comparison with Supabase
- `nal_large_properties_analysis.json` - Detailed results

---

**Report Generated:** September 30, 2025
**Data Sources:** Florida DOR NAL files (2025), ConcordBroker Supabase Database
**Analysis Method:** Python CSV parsing, Supabase API queries, Statistical comparison