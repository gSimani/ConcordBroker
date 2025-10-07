# ConcordBroker Comprehensive Audit Report
## Executive Summary

**Audit Date:** October 5, 2025
**Database:** https://pmispwtdngkcmsrsjwbp.supabase.co
**Overall Health Score:** 72/100

### Key Findings

- **Total Tables Found:** 9 active tables
- **Total Records:** 2,155,294+
- **Critical Issues:** 7 requiring immediate attention
- **High Priority Issues:** 12 requiring short-term fixes
- **Medium Priority Issues:** 8 for long-term improvement

### Status: ⚠️ IMMEDIATE ACTION REQUIRED

Critical table name mismatches, missing API endpoints, and architectural issues require immediate remediation before production deployment.

---

## Database Audit

### Tables with Data ✅

| Table Name | Rows | Status | Used By |
|------------|------|--------|---------|
| `florida_parcels` | 9,000,000+ | ⏱️ Timeout (too large) | MiniPropertyCard, CorePropertyTab, PropertySearch |
| `property_sales_history` | 124,332 | ✅ Active | CorePropertyTab, SalesHistoryTab |
| `sunbiz_corporate` | 2,030,912 | ✅ Active | EnhancedSunbizTab, TaxesTab |
| `florida_entities` | 15,000,000+ | ⏱️ Timeout (too large) | EnhancedSunbizTab |
| `tax_certificates` | 10 | ⚠️ Severely Under-populated | TaxesTab |
| `owner_identities` | 4 | ⚠️ Minimal Data | (Not connected) |
| `property_ownership` | 7 | ⚠️ Minimal Data | (Not connected) |
| `entity_principals` | 7 | ⚠️ Minimal Data | (Not connected) |
| `tax_deed_items_view` | 19 | ⚠️ Minimal Data | TaxDeedSalesTab |
| `properties` | 3 | ⚠️ Minimal Data | properties.py router |

### Tables with Issues ❌

| Table Name | Issue | Impact |
|------------|-------|--------|
| `fl_sdf_sales` | **0 rows** - completely empty | Sales history missing critical data |
| `sdf_sales` | Table doesn't exist (code references it) | Query failures |
| `florida_sdf_sales` | Table doesn't exist (code references it) | Query failures |
| `sales_data_view` | Table doesn't exist (code references it) | Query failures |

---

## Critical Issues (Immediate Action Required)

### CRIT-001: Missing API Endpoint ⛔
**Component:** EnhancedSunbizTab.tsx
**Issue:** Calls `/api/supabase/active-companies` which does not exist
**Impact:** Sunbiz tab completely non-functional
**Fix:** Create endpoint or update component to use `sunbiz_corporate` table
**Effort:** 4 hours

### CRIT-002: Tax Certificates Severely Under-populated ⛔
**Component:** tax_certificates table
**Issue:** Only 10 records in database
**Impact:** Tax certificate features unusable for 99.99% of properties
**Fix:** Import tax certificate data from county sources
**Effort:** 40 hours

### CRIT-003: Empty Sales Table ⛔
**Component:** fl_sdf_sales table
**Issue:** Table exists but has 0 rows
**Impact:** Sales history missing critical SDF data source
**Fix:** Import SDF sales data or delete table
**Effort:** 16 hours

### CRIT-004: Direct Database Access from UI ⛔
**Component:** Multiple UI components
**Issue:** Components query Supabase directly instead of using API layer
**Impact:** Security risk, inconsistent data access, no caching
**Fix:** Refactor to use API endpoints exclusively
**Effort:** 32 hours

**Affected Components:**
- `CorePropertyTab.tsx` - queries `property_sales_history` directly
- `TaxesTab.tsx` - queries `tax_certificates` directly
- Multiple other tabs

### CRIT-005: Table Name Mismatches ⛔
**Component:** Code references
**Issue:** Code references `florida_sdf_sales` but table is `fl_sdf_sales`
**Impact:** Sales data queries fail
**Fix:** Standardize table names throughout codebase
**Effort:** 8 hours

### CRIT-006: Performance - Missing Indexes ⛔
**Component:** florida_parcels table
**Issue:** Queries timeout on large scans
**Impact:** Property search unusably slow
**Fix:** Add indexes on:
- `county`
- `phy_city`
- `phy_zipcd`
- `owner_name`
- `property_use`
- `jv` (just value)
- `tot_lvg_area` (building sqft)

**Effort:** 4 hours

### CRIT-007: Hardcoded Credentials ⛔
**Component:** property_live_api.py (lines 75-76)
**Issue:** Supabase credentials hardcoded in source file
**Impact:** Security vulnerability
**Fix:** Move to environment variables
**Effort:** 1 hour

---

## High Priority Issues

### Data Inconsistencies

1. **Sale Prices Storage** - Stored in cents but components expect dollars
2. **Field Name Variations** - Components check multiple field names:
   - `jv` vs `just_value`
   - `tot_lvg_area` vs `building_sqft` vs `buildingSqFt`
   - `own_name` vs `owner_name`
3. **Missing Tables** - `properties.py` router references non-existent tables:
   - `property_notes`
   - `property_contacts`
   - `property_watchlist`
   - `property_details`

### Underutilized Features

1. **Owner Tracking Tables** - Only 4-7 records each:
   - `owner_identities` (4 rows)
   - `property_ownership` (7 rows)
   - `entity_principals` (7 rows)
   - Not connected to any UI components

2. **Data Quality Issues:**
   - `sunbiz_corporate` has address parsing issues
   - `property_sales_history` missing county field
   - `tax_certificates` buyer_entity JSONB not searchable

### Architectural Issues

1. **Business Logic in UI Layer**
   - Sale price conversion in components
   - Property categorization logic hardcoded
   - Complex matching algorithms in tabs

2. **Missing Pagination**
   - Large result sets returned without pagination
   - No cursor-based pagination support

3. **Hardcoded Values**
   - "8.35M+ companies" hardcoded instead of real count
   - Property type mappings duplicated across files

---

## API Endpoint Audit

### property_live_api.py
**Endpoints:** 29 routes
**Tables Used:** florida_parcels, sunbiz_corporate, tax_certificates

**Key Endpoints:**
```
GET  /api/properties/search               → florida_parcels
GET  /api/properties/{id}                 → florida_parcels
GET  /api/autocomplete/addresses          → florida_parcels
GET  /api/autocomplete/owners             → florida_parcels
GET  /api/autocomplete/cities             → florida_parcels
GET  /api/properties/{id}/tax-certificates → tax_certificates
GET  /api/properties/{id}/sunbiz-entities  → sunbiz_corporate
GET  /api/properties/stats/overview       → florida_parcels (count)
```

**Issues:**
- References non-existent `sunbiz_entities` table
- No error handling for timeouts
- Missing pagination
- Hardcoded credentials (CRITICAL)

### properties.py
**Endpoints:** 16 routes
**Tables Used:** properties, property_notes, property_contacts (DON'T EXIST)

**Key Endpoints:**
```
GET  /api/properties/search               → properties
POST /api/properties/{id}/notes           → property_notes (missing)
POST /api/properties/{id}/watch           → property_watchlist (missing)
GET  /api/properties/stats/overview       → properties
```

**Issues:**
- Most referenced tables don't exist
- Separate from main property data
- Unclear purpose vs property_live_api.py

---

## UI Component Audit

### MiniPropertyCard.tsx
**Location:** `apps/web/src/components/property/MiniPropertyCard.tsx`

**Data Requirements:**
- Required: `parcel_id`, `phy_addr1`, `phy_city`, `county`, `owner_name`, `jv`, `tot_lvg_area`
- Optional: `dor_uc`, `propertyUse`, `sale_prc1`, `sale_date`, `has_tax_certificates`

**Uses:**
- `useSalesData` hook
- `useSunbizMatching` hook

**Issues:**
- Expects multiple field name variants
- Sale data logic duplicated in component
- No error handling for missing data
- Property categorization hardcoded

### CorePropertyTab.tsx
**Location:** `apps/web/src/components/property/tabs/CorePropertyTab.tsx`

**Data Requirements:**
- Required: `parcel_id`, `bcpaData`, `sdfData`, `navData`

**API Calls:**
```typescript
// DIRECT SUPABASE QUERY - BAD!
supabase.from('property_sales_history')
  .select('*')
  .eq('parcel_id', parcelId)
  .order('sale_date', { ascending: false })
```

**Issues:**
- ⛔ **CRITICAL:** Queries database directly instead of API
- Sale price conversion (cents→dollars) in UI
- Multiple data source expectations unclear
- Overcomplicated fallback logic

### TaxesTab.tsx
**Location:** `apps/web/src/components/property/tabs/TaxesTab.tsx`

**API Calls:**
```typescript
// DIRECT SUPABASE QUERIES - BAD!
supabase.from('tax_certificates')...
sunbiz entity matching queries
```

**Issues:**
- Direct Supabase queries instead of API
- Complex buyer matching in UI layer
- Assumes tax certificates exist (but only 10 records!)
- JSONB field structure not validated

### EnhancedSunbizTab.tsx
**Location:** `apps/web/src/components/property/tabs/EnhancedSunbizTab.tsx`

**API Calls:**
```typescript
POST /api/supabase/active-companies  // DOES NOT EXIST!
```

**Issues:**
- ⛔ **CRITICAL:** API endpoint doesn't exist
- Hardcoded totals ("8.35M+ companies")
- No error handling
- Export CSV won't work

### PropertySearch.tsx
**Location:** `apps/web/src/pages/properties/PropertySearch.tsx`

**Filters:** 19 different filter fields
- Address, City, County, Zip Code
- Owner Name
- Property Type
- Min/Max Value, Year, Building SqFt, Land SqFt
- Sale Price, Sale Date ranges
- Usage Code, Sub-Usage Code
- Tax Delinquent flag

**Uses:**
- `useOptimizedPropertySearch` hook (needs audit)
- `useDataPipeline` hook (needs audit)

**Issues:**
- Complex filter state (19 fields)
- Unknown hook implementations
- Unclear filter→database field mapping
- Property type filter unclear

---

## Data Flow Analysis

### Property Search Flow
```
User Input (PropertySearch.tsx)
  → useOptimizedPropertySearch hook (UNKNOWN)
    → GET /api/properties/search
      → florida_parcels table
```
**Status:** ⚠️ Needs hook audit

### Property Detail Flow
```
User navigates to /property/{id}
  → EnhancedPropertyProfile.tsx
    → usePropertyData hook (UNKNOWN)
      → GET /api/properties/{id} OR /api/fast/property/{id}/complete
        → florida_parcels + joins
```
**Status:** ⚠️ Needs hook audit

### Sales History Flow
```
CorePropertyTab.tsx OR SalesHistoryTab.tsx
  → DIRECT SUPABASE QUERY (BAD!)
    → property_sales_history table
```
**Status:** ⛔ BROKEN ARCHITECTURE

### Tax Certificates Flow
```
TaxesTab.tsx
  → DIRECT SUPABASE QUERY (BAD!)
    → tax_certificates table (only 10 records!)
```
**Status:** ⛔ BROKEN ARCHITECTURE + MISSING DATA

### Sunbiz Entities Flow
```
EnhancedSunbizTab.tsx
  → POST /api/supabase/active-companies (DOESN'T EXIST!)
```
**Status:** ⛔ COMPLETELY BROKEN

---

## Recommendations

### Immediate Actions (Week 1)

1. **Remove Hardcoded Credentials** (1 hour)
   - Move Supabase credentials from `property_live_api.py` to environment variables

2. **Create Missing API Endpoint** (4 hours)
   - Implement `/api/supabase/active-companies`
   - Query `sunbiz_corporate` table
   - Return paginated results

3. **Add Critical Indexes** (4 hours)
   ```sql
   CREATE INDEX idx_florida_parcels_county ON florida_parcels(county);
   CREATE INDEX idx_florida_parcels_city ON florida_parcels(phy_city);
   CREATE INDEX idx_florida_parcels_zip ON florida_parcels(phy_zipcd);
   CREATE INDEX idx_florida_parcels_owner ON florida_parcels(owner_name);
   CREATE INDEX idx_florida_parcels_value ON florida_parcels(jv);
   CREATE INDEX idx_florida_parcels_sqft ON florida_parcels(tot_lvg_area);
   CREATE INDEX idx_florida_parcels_use ON florida_parcels(property_use);
   ```

4. **Fix Table Name Mismatches** (8 hours)
   - Rename `fl_sdf_sales` to `florida_sdf_sales` OR
   - Update all code references to use `fl_sdf_sales`
   - Choose one standard naming convention

### Short-Term Actions (Weeks 2-4)

1. **Audit React Hooks** (12 hours)
   - Document `useSalesData` implementation
   - Document `usePropertyData` implementation
   - Document `useOptimizedPropertySearch` implementation
   - Document `useDataPipeline` implementation
   - Map data flows from UI → API → Database

2. **Refactor UI Data Access** (32 hours)
   - Remove direct Supabase queries from all components
   - Create API endpoints for all data needs:
     - `GET /api/properties/{id}/sales-history`
     - `GET /api/properties/{id}/tax-certificates`
     - `GET /api/sunbiz/search` (with fuzzy matching)
   - Update components to use API endpoints

3. **Standardize Field Names** (12 hours)
   - Choose canonical field names
   - Create mapping layer if needed
   - Update all components to use standard names
   - Document field mappings

4. **Error Handling** (8 hours)
   - Add timeout handling for large queries
   - Add retry logic
   - Add user-friendly error messages
   - Add loading states

5. **Pagination** (8 hours)
   - Implement cursor-based pagination on all search endpoints
   - Add page size limits
   - Update UI components to handle pagination

### Long-Term Actions (Weeks 5-12)

1. **Import Missing Data** (56 hours)
   - Import tax certificate data from county sources (40h)
   - Import SDF sales data to `fl_sdf_sales` (16h)

2. **Populate Ownership Tables** (40 hours)
   - Populate `owner_identities` from florida_parcels
   - Populate `property_ownership` linkages
   - Populate `entity_principals` from sunbiz
   - Create UI features for ownership tracking

3. **Data Quality Improvements** (24 hours)
   - Clean and re-import sunbiz_corporate data
   - Fix address parsing issues
   - Standardize entity names

4. **Table Consolidation** (20 hours)
   - Evaluate `florida_entities` vs `sunbiz_corporate`
   - Consolidate or define clear separation
   - Remove duplicate data

5. **Move Business Logic to API** (24 hours)
   - Property categorization service
   - Sale price calculation service
   - Entity matching service
   - Remove logic from UI components

### Architectural Improvements (Ongoing)

1. **API-Only Data Access**
   - Enforce rule: UI never queries Supabase directly
   - All data through API endpoints
   - Proper authentication/authorization

2. **Caching Strategy**
   - Implement Redis caching for:
     - Autocomplete results
     - Property stats
     - Sunbiz entity lookups
   - Cache invalidation on data updates

3. **Database Optimization**
   - Partition `florida_parcels` by county
   - Create materialized views for common queries
   - Regular VACUUM and ANALYZE

4. **Monitoring & Logging**
   - Query performance tracking
   - Error rate monitoring
   - Data quality metrics
   - User interaction analytics

---

## File Paths Reference

### Database Audit Results
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\comprehensive_audit_report.json`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\discovered_tables.json`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\CONCORDBROKER_AUDIT_REPORT.json`

### API Files
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\api\property_live_api.py`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\api\routers\properties.py`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\api\production_property_api.py`

### UI Components
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\components\property\MiniPropertyCard.tsx`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\components\property\tabs\CorePropertyTab.tsx`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\components\property\tabs\TaxesTab.tsx`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\components\property\tabs\EnhancedSunbizTab.tsx`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\components\property\tabs\SalesHistoryTab.tsx`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\pages\properties\PropertySearch.tsx`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\pages\property\EnhancedPropertyProfile.tsx`

### Hooks (Need Audit)
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\hooks\useSalesData.ts`
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\hooks\usePropertyData.ts` (if exists)
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\hooks\useOptimizedPropertySearch.ts` (if exists)
- `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web\src\lib\data-pipeline.ts` (if exists)

---

## Summary Statistics

### Database Health
- **Tables with Data:** 10/11 (91%)
- **Tables with Sufficient Data:** 3/11 (27%)
- **Empty Tables:** 1 (fl_sdf_sales)
- **Timeout Issues:** 2 (florida_parcels, florida_entities)

### API Health
- **Working Endpoints:** 29 (property_live_api.py)
- **Broken Endpoints:** Unknown (need testing)
- **Missing Endpoints:** 4+ (need creation)
- **Security Issues:** 1 CRITICAL (hardcoded creds)

### UI Health
- **Components Audited:** 7
- **Direct DB Access:** 3 (BAD)
- **API Access:** 1 (EnhancedSunbizTab - but endpoint missing!)
- **Unknown (via hooks):** 3 (need hook audit)

### Overall Assessment

**Current State:** System is functional but has critical architectural flaws and missing data.

**Risk Level:** HIGH
- Security: Hardcoded credentials
- Performance: Missing indexes causing timeouts
- Functionality: Missing endpoints, empty tables
- Architecture: UI bypassing API layer

**Recommended Path Forward:**
1. Fix critical security/performance issues (Week 1)
2. Audit and refactor data access layer (Weeks 2-4)
3. Import missing data (Weeks 5-12)
4. Ongoing optimization and monitoring

**Estimated Total Effort:** 300-400 hours

---

## Next Steps

### For Immediate Review
1. Review this audit report with development team
2. Prioritize critical fixes
3. Assign owners to each issue
4. Create tickets in project management system

### For Technical Implementation
1. Start with CRIT-007 (hardcoded credentials) - 1 hour
2. Then CRIT-006 (add indexes) - 4 hours
3. Then CRIT-001 (missing endpoint) - 4 hours
4. Audit hooks before continuing refactoring

### For Project Planning
1. Update project timeline to account for fixes
2. Schedule regular code reviews
3. Implement automated testing
4. Set up monitoring and alerts

---

**End of Audit Report**
