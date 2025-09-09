# Comprehensive Property Data Analysis Report
## 12681 NW 78 MNR, PARKLAND, Florida 33076

**Analysis Date:** September 9, 2025  
**Analysis Time:** 17:44 UTC  
**Property URL:** http://localhost:5174/properties/parkland/12681-nw-78-mnr

---

## Executive Summary

This comprehensive analysis compared the localhost application data against official Broward County Property Appraiser, Tax Collector, and SunBiz records for property 12681 NW 78 MNR in Parkland, FL. **CRITICAL DATA DISCREPANCIES** were identified across multiple data points, indicating significant issues with the data integration pipeline.

### Key Findings:
- ❌ **MAJOR DISCREPANCIES:** Property values, owner information, and sales history show significant deviations
- ❌ **MISSING CRITICAL DATA:** SunBiz information completely missing despite official entity filing
- ❌ **DATABASE ERRORS:** 16 console errors and 14 network failures during data loading
- ⚠️ **API FAILURES:** Multiple Supabase table access issues preventing proper data retrieval

---

## Part 1: Localhost Application Data Analysis

### Overview Tab Analysis
**Data Captured:**
- Market Value: **$580,000** ✅
- Property Type: **001** (Single Family) ✅
- Year Built: **2003** ✅
- Living Area: **3,285 sqft** ✅
- Bedrooms/Bathrooms: **5 bed • 3.5 bath** ✅
- Property Owner: **INVITATION HOMES** ❌ (INCORRECT - missing "IH3 PROPERTY FLORIDA LP")
- Assessed Value: **$180** ❌ (CRITICALLY INCORRECT - should be $601,370)
- Land Value: **$145,000** ✅
- Building Value: **$435,000** ✅

### Core Property Info Tab Analysis
**Data Captured:**
- Parcel ID: **474131031040** ✅
- Sales History: **3 records** ❌ (INCOMPLETE - official shows 4+ records)
  - Aug 14, 2021: $425,000 (Warranty Deed) ⚠️ (Date discrepancy - official shows 11/6/2013: $375,000)
  - Mar 19, 2018: $380,000 (Warranty Deed) ❌ (Not in official records)
  - Jun 9, 2015: $350,000 (Warranty Deed) ❌ (Not in official records)

**Missing Official Sales:**
- 11/6/2013: $375,000 (WD-Q) ❌
- 9/15/2010: $100 (WD-T) ❌
- 7/27/2009: $327,000 (WD-Q) ❌
- 11/16/2004: $432,000 (WD) ❌

### SunBiz Info Tab Analysis
**CRITICAL FAILURE:**
- Status: **"No Sunbiz Information Found"** ❌
- Message: "No corporate filing information found for this property owner"

**Should Show (Official Data):**
- Entity Name: **IH3 PROPERTY FLORIDA LP**
- Document Number: **M13000005449**
- FEI/EIN: **80-0945919**
- Date Filed: **08/28/2013**
- Status: **ACTIVE**
- Principal Address: **5420 Lyndon B Johnson Freeway, Suite 600, Dallas, TX 75240**

### Property Tax Info Tab Analysis
**Data Captured:**
- Total Amount Due: **$24,432 DELINQUENT** ⚠️
- Annual Tax Amount: **$9,500** ❌ (Official 2024: $11,674.59)
- Tax Certificates: **2 Active liens** ✅
- Effective Tax Rate: **1.64%** ⚠️
- Monthly Tax Cost: **$792** ⚠️

**Should Show (Official Data):**
- 2024 Annual Bill: **$0.00 (PAID IN FULL)** ❌
- Last Payment: **12/02/2024 - $11,674.59** ❌
- Ad Valorem Taxes 2024: **$10,345.79** ❌

---

## Part 2: Official Source Data Comparison

### Broward Property Appraiser (BCPA) Official Data
| Field | Official Value | Localhost Value | Status |
|-------|---------------|-----------------|---------|
| Property Owner | IH3 PROPERTY FLORIDA LP | INVITATION HOMES | ❌ INCORRECT |
| Folio | 4741 31 03 1040 | 474131031040 | ✅ CORRECT |
| 2025 Just Value | $628,040 | $580,000 | ❌ INCORRECT |
| 2025 Assessed Value | $601,370 | $180 | ❌ CRITICALLY INCORRECT |
| 2025 Taxable Value | $601,370 | Not shown | ❌ MISSING |
| Land Value 2025 | $85,580 | $145,000 | ❌ INCORRECT |
| Building Value 2025 | $542,460 | $435,000 | ❌ INCORRECT |
| Year Built | 2003/2002 | 2003 | ⚠️ PARTIAL |

### Tax Collector Official Data
| Field | Official Value | Localhost Value | Status |
|-------|---------------|-----------------|---------|
| 2024 Amount Due | $0.00 (paid) | $24,432 DELINQUENT | ❌ CRITICALLY INCORRECT |
| Last Payment | 12/02/2024 - $11,674.59 | Not shown | ❌ MISSING |
| 2024 Ad Valorem | $10,345.79 | $9,500 | ❌ INCORRECT |
| 2024 Assessed | $546,700 | $180 | ❌ CRITICALLY INCORRECT |

### SunBiz Official Data
| Field | Official Value | Localhost Value | Status |
|-------|---------------|-----------------|---------|
| Entity Name | IH3 PROPERTY FLORIDA LP | Not found | ❌ MISSING |
| Document Number | M13000005449 | Not found | ❌ MISSING |
| Status | ACTIVE | Not found | ❌ MISSING |
| Filing Date | 08/28/2013 | Not found | ❌ MISSING |
| Principal Address | Dallas, TX 75240 | Not found | ❌ MISSING |

---

## Part 3: Technical Issues Identified

### Console Errors (16 total)
```
Failed to load resource: the server responded with a status of 400
- sunbiz_corporate table queries (6 failures)
- sunbiz_officers table queries (2 failures)
- florida_permits table queries (2 failures)
- broward_permits table queries (2 failures)
- foreclosure_cases table queries (2 failures)
```

### Network Errors (14 total)
- **400 Status Errors:** Invalid query syntax or missing columns
- **404 Status Errors:** Missing tables (foreclosure_cases, broward_permits)

### Database Schema Issues
**Missing/Misconfigured Tables:**
- `foreclosure_cases` - Table not found
- `broward_permits` - Table not found  
- `sunbiz_corporate` - Query syntax errors
- `sunbiz_officers` - Query syntax errors

---

## Part 4: Critical Data Discrepancies Summary

### Severity: CRITICAL ❌
1. **Property Owner:** Shows "INVITATION HOMES" instead of "IH3 PROPERTY FLORIDA LP"
2. **Assessed Value:** Shows $180 instead of $601,370 (99.97% error)
3. **Tax Status:** Shows "DELINQUENT $24,432" instead of "PAID $0.00"
4. **SunBiz Data:** Completely missing despite active entity

### Severity: HIGH ❌
5. **Market Value:** $580,000 vs $628,040 (7.6% error)
6. **Land Value:** $145,000 vs $85,580 (69.4% error)
7. **Building Value:** $435,000 vs $542,460 (19.8% error)
8. **Sales History:** Missing 4+ official sales records

### Severity: MEDIUM ⚠️
9. **Tax Amount:** $9,500 vs $11,674.59 (18.6% error)
10. **Property Address Format:** Minor formatting differences

---

## Part 5: Root Cause Analysis

### Database Integration Issues
1. **Supabase Schema Mismatch:** Multiple tables missing or misconfigured
2. **Data Pipeline Failures:** Official data not properly imported/updated
3. **API Query Syntax:** Invalid PostgREST queries causing 400 errors

### Data Source Problems
1. **BCPA Integration:** Property values and ownership data outdated/incorrect
2. **SunBiz Integration:** Complete failure to retrieve entity information
3. **Tax Collector Integration:** Tax status and payment history missing

### Application Logic Issues
1. **Fallback Values:** App showing placeholder/demo data when real data fails
2. **Error Handling:** Silent failures masking data retrieval problems
3. **Data Validation:** No checks for data accuracy/freshness

---

## Part 6: Recommended Fixes

### Immediate Actions Required
1. **Fix Supabase Schema:**
   ```sql
   -- Create missing tables
   CREATE TABLE IF NOT EXISTS foreclosure_cases (...);
   CREATE TABLE IF NOT EXISTS broward_permits (...);
   
   -- Fix column names in sunbiz tables
   ALTER TABLE sunbiz_corporate ADD COLUMN IF NOT EXISTS officers TEXT[];
   ```

2. **Update Property Data:**
   ```sql
   UPDATE florida_parcels 
   SET 
     own_name = 'IH3 PROPERTY FLORIDA LP',
     jv = 628040,
     av_sd = 601370,
     lnd_val = 85580
   WHERE parcel_id = '474131031040';
   ```

3. **Load SunBiz Data:**
   ```sql
   INSERT INTO sunbiz_corporate VALUES (
     'M13000005449',
     'IH3 PROPERTY FLORIDA LP',
     'ACTIVE',
     '08/28/2013',
     ...
   );
   ```

### Database Schema Fixes
1. **Create missing tables:** foreclosure_cases, broward_permits
2. **Fix column mappings** in existing tables
3. **Add proper indexes** for performance
4. **Implement RLS policies** for security

### Data Pipeline Updates
1. **Refresh BCPA data** - current values are outdated
2. **Import SunBiz entity data** - completely missing
3. **Update tax collector records** - payment status incorrect
4. **Validate sales history** - missing multiple official records

### Application Code Fixes
1. **Improve error handling** - don't show demo data on API failures
2. **Add data validation** - check for reasonable value ranges
3. **Implement fallback logic** - graceful degradation when data missing
4. **Update API queries** - fix PostgREST syntax errors

---

## Part 7: Screenshots Generated

The following screenshots were captured during analysis:
- `property_comprehensive_2025-09-09T17-44-05-368Z.png` - Full page overview
- `property_tab_overview_2025-09-09T17-44-05-368Z.png` - Overview tab
- `property_tab_core_property_info_2025-09-09T17-44-05-368Z.png` - Core property info
- `property_tab_sunbiz_info_2025-09-09T17-44-05-368Z.png` - SunBiz tab (showing "No data found")
- `property_tab_property_tax_info_2025-09-09T17-44-05-368Z.png` - Tax info tab
- `property_tab_permit_2025-09-09T17-44-05-368Z.png` - Permit tab
- `property_tab_foreclosure_2025-09-09T17-44-05-368Z.png` - Foreclosure tab
- `property_tab_sales_tax_deed_2025-09-09T17-44-05-368Z.png` - Sales tax deed tab

---

## Conclusion

This analysis reveals **critical data integrity issues** that require immediate attention. The localhost application is displaying incorrect property values, missing entity information, and showing incorrect tax status. These discrepancies could lead to:

- **Investment decision errors** (wrong property values)
- **Legal compliance issues** (incorrect tax status)
- **Due diligence failures** (missing entity information)

**Priority Actions:**
1. ✅ Fix database schema and missing tables
2. ✅ Refresh all property data from official sources
3. ✅ Implement proper error handling and validation
4. ✅ Add monitoring for data accuracy and freshness

**Estimated Fix Time:** 2-3 hours for database fixes, 4-6 hours for complete data refresh.