# ConcordBroker Comprehensive Audit - Findings & Action Plan

**Date**: October 5, 2025
**Status**: Complete Analysis Ready for Execution

---

## 🎯 EXECUTIVE SUMMARY

**Overall System Health**: 75/100
**Critical Issues**: 5
**High Priority Issues**: 12
**Medium Priority Issues**: 8

The comprehensive audit revealed that ConcordBroker has a solid foundation but requires immediate attention to data flow issues, UI-database mapping inconsistencies, and missing connections between components.

---

## 📊 DATABASE AUDIT RESULTS

### ✅ Working Tables (6)
| Table | Rows | Status | Data Quality |
|-------|------|--------|--------------|
| property_sales_history | 124,332 | ✅ Active | Good |
| sunbiz_corporate | 2,030,912 | ✅ Active | Needs cleanup |
| tax_certificates | 10 | ⚠️ Active | Very limited |
| owner_identities | 4 | ✅ Active | Excellent |
| property_ownership | 7 | ✅ Active | Excellent |
| entity_principals | 7 | ✅ Active | Excellent |

### ⏱️ Timeout Issues (2)
- **florida_parcels**: Times out (needs indexes)
- **florida_entities**: Times out (needs indexes)

### ❌ Missing/Referenced Tables (3)
- **sdf_sales**: Not found (code references it)
- **sales_data_view**: Not found (code references it)
- **florida_sdf_sales**: Not found (code references it)

---

## 🔴 CRITICAL ISSUES

### 1. **EnhancedSunbizTab: Missing API Endpoint**
**Location**: `apps/web/src/components/property/tabs/EnhancedSunbizTab.tsx`
**Issue**: Calls `/api/supabase/active-companies` which doesn't exist
**Impact**: Sunbiz tab fails to load data
**Fix**:
```typescript
// apps/web/src/components/property/tabs/EnhancedSunbizTab.tsx:line
// CHANGE FROM:
const response = await fetch(`/api/supabase/active-companies?property_id=${propertyId}`);

// CHANGE TO:
const response = await fetch(`/api/properties/${propertyId}/sunbiz-entities`);
```

### 2. **florida_parcels Query Timeouts**
**Issue**: No indexes on frequently queried columns
**Impact**: Search and property detail pages timeout
**Fix**: Add critical indexes (see SQL below)

### 3. **Data Field Name Inconsistencies**
**Component**: MiniPropertyCard.tsx
**Issue**: Expects 27 different field name variants
**Examples**:
- `own_name` vs `owner_name`
- `jv` vs `just_value` vs `justValue`
- `lnd_sqfoot` vs `landSqFt` vs `land_square_footage`

**Fix**: Standardize field names across codebase

### 4. **UI Components Bypassing API Layer**
**Components**: CorePropertyTab.tsx, TaxesTab.tsx
**Issue**: Direct Supabase queries instead of using API
**Impact**: Breaks caching, security, and data flow
**Fix**: Refactor to use API endpoints

### 5. **Tax Certificates Data Severely Limited**
**Issue**: Only 10 records for entire Florida
**Expected**: Thousands of records
**Impact**: Tax deed functionality incomplete
**Fix**: Import complete tax certificate dataset

---

## 📋 DETAILED FINDINGS BY COMPONENT

### Property Search (PropertySearch.tsx)
**Data Fields Used**: 85 different field names!
**Issues**:
- Inconsistent naming (camelCase, snake_case, abbreviations)
- Expects fields from multiple tables without proper joins
- No error handling for missing data

**Field Variants Found**:
```javascript
// Same data, different names:
'just_value', 'jv', 'justValue', 'market_value', 'marketValue', 'appraised_value'
'owner_name', 'own_name', 'owner'
'property_type', 'propertyType', 'propertyUse', 'propertyUseDesc', 'use_code', 'property_use_code', 'dor_uc'
```

### MiniPropertyCard Component
**Hooks Used**:
- `useSunbizMatching` - Works
- `useSalesData` - Needs audit

**Data Requirements**:
- Expects 27 different field variations
- No fallback for missing fields
- Hardcoded field expectations

### Sales History System
**Tables**:
- `property_sales_history`: 124K rows, sale_price in cents (needs /100)
- Missing views: `sales_data_view`, `florida_sdf_sales`

**Issues**:
- Price conversion not consistent
- No date range filtering
- County field is NULL

### Sunbiz Corporate Data
**Issues**:
- Address fields are scrambled (prin_addr1 contains mixed data)
- Entity names have extra padding (200+ chars)
- Status field is empty
- Filing dates are NULL

**Sample Bad Data**:
```json
{
  "entity_name": "STEADY MILES TRANSPORT LLC                         [+150 spaces]        AFLAL",
  "prin_addr1": "BLVD                   801                                       JACKSONVILLE                  3225",
  "prin_city": "8       14701 BARTRAM PARK BLVD",
  "status": "",
  "filing_date": null
}
```

---

## 🔧 ACTION PLAN

### Week 1: Critical Fixes (16 hours)

#### Day 1-2: Database Performance (8h)
```sql
-- Add critical indexes to florida_parcels
CREATE INDEX CONCURRENTLY idx_florida_parcels_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX CONCURRENTLY idx_florida_parcels_county ON florida_parcels(county);
CREATE INDEX CONCURRENTLY idx_florida_parcels_owner_name ON florida_parcels(owner_name);
CREATE INDEX CONCURRENTLY idx_florida_parcels_phy_addr1 ON florida_parcels(phy_addr1);
CREATE INDEX CONCURRENTLY idx_florida_parcels_phy_city ON florida_parcels(phy_city);
CREATE INDEX CONCURRENTLY idx_florida_parcels_just_value ON florida_parcels(just_value);

-- Add indexes to florida_entities
CREATE INDEX CONCURRENTLY idx_florida_entities_entity_id ON florida_entities(entity_id);
CREATE INDEX CONCURRENTLY idx_florida_entities_business_name ON florida_entities(business_name);
```

#### Day 3: API Fixes (4h)
1. **Create Missing Endpoint**:
```python
# apps/api/property_live_api.py
@app.get("/api/properties/{property_id}/sunbiz-entities")
async def get_property_sunbiz_entities(property_id: str):
    """Get Sunbiz entities for a property"""
    # Get property owner
    property_result = supabase.table('florida_parcels')\\
        .select('owner_name')\\
        .eq('parcel_id', property_id)\\
        .limit(1)\\
        .execute()

    if not property_result.data:
        return {"companies": [], "total_count": 0}

    owner_name = property_result.data[0]['owner_name']

    # Search Sunbiz
    entities = supabase.table('sunbiz_corporate')\\
        .select('*')\\
        .ilike('entity_name', f'%{owner_name}%')\\
        .limit(10)\\
        .execute()

    return {
        "companies": entities.data,
        "total_count": len(entities.data)
    }
```

2. **Fix EnhancedSunbizTab.tsx**:
```typescript
// Line 45: Update API call
const response = await fetch(
  `/api/properties/${propertyId}/sunbiz-entities`
);
```

#### Day 4: Field Name Standardization (4h)
Create field mapping utility:
```typescript
// apps/web/src/utils/fieldMapper.ts
export const standardizeFields = (data: any) => {
  return {
    // Owner
    owner_name: data.owner_name || data.own_name || data.owner,

    // Value
    just_value: data.just_value || data.jv || data.justValue || data.market_value,

    // Property type
    property_use: data.property_use || data.propertyUse || data.property_type,
    dor_use_code: data.dor_use_code || data.dor_uc || data.use_code,

    // Square footage
    land_sqft: data.land_sqft || data.lnd_sqfoot || data.landSqFt,
    total_living_area: data.total_living_area || data.tot_lvg_area || data.living_area,

    // Address
    phy_addr1: data.phy_addr1 || data.address || data.property_address,
    phy_city: data.phy_city || data.city || data.property_city,

    // Year
    year_built: data.year_built || data.act_yr_blt || data.yearBuilt
  };
};
```

### Week 2: Data Flow Refactoring (24 hours)

#### Day 1-2: Refactor UI Components (16h)
1. **CorePropertyTab.tsx**: Remove direct Supabase, use API
2. **TaxesTab.tsx**: Remove direct Supabase, use API
3. **MiniPropertyCard.tsx**: Use field mapper utility
4. **PropertySearch.tsx**: Standardize field usage

#### Day 3: Multi-Corporation UI (8h)
```typescript
// apps/web/src/components/property/OwnerPortfolioCard.tsx
export const OwnerPortfolioCard = ({ ownerId }: { ownerId: string }) => {
  const { data } = useQuery({
    queryKey: ['owner-portfolio', ownerId],
    queryFn: async () => {
      const res = await supabase.rpc('get_owner_portfolio', {
        p_owner_identity_id: ownerId
      });
      return res.data;
    }
  });

  return (
    <Card>
      <CardHeader>
        <h3>{data?.owner?.name}</h3>
        <Badge>{data?.summary?.total_properties} properties</Badge>
      </CardHeader>
      <CardContent>
        <div>Portfolio Value: ${data?.summary?.total_portfolio_value?.toLocaleString()}</div>
        <div>Entities: {data?.summary?.total_entities}</div>

        {data?.entities?.map(entity => (
          <div key={entity.entity_id}>
            {entity.entity_name} ({entity.role})
          </div>
        ))}

        <Button>View Complete Portfolio</Button>
      </CardContent>
    </Card>
  );
};
```

### Week 3: Data Import & Cleanup (32 hours)

#### Tax Certificates Import (16h)
- Scrape Florida county tax collector sites
- Import complete tax certificate dataset
- Expected: 10,000+ records

#### Sunbiz Data Cleanup (16h)
- Parse and fix address fields
- Trim entity names
- Extract proper status and dates

---

## 🧪 PLAYWRIGHT TEST SUITE

### Test Coverage Required

#### 1. Property Search Tests
```typescript
// apps/web/tests/property-search.spec.ts
test('Property search returns results', async ({ page }) => {
  await page.goto('/properties');

  // Fill search
  await page.fill('[data-testid="search-input"]', 'Miami');
  await page.click('[data-testid="search-button"]');

  // Verify results
  await expect(page.locator('[data-testid="property-card"]')).toHaveCount.greaterThan(0);
});

test('All filters work correctly', async ({ page }) => {
  await page.goto('/properties');

  // Test price filter
  await page.fill('[data-testid="min-price"]', '100000');
  await page.fill('[data-testid="max-price"]', '500000');

  // Test county filter
  await page.selectOption('[data-testid="county-select"]', 'BROWARD');

  // Apply filters
  await page.click('[data-testid="apply-filters"]');

  // Verify filtered results
  const cards = await page.locator('[data-testid="property-card"]').all();
  for (const card of cards) {
    const priceText = await card.locator('[data-testid="price"]').textContent();
    const price = parseInt(priceText.replace(/[^0-9]/g, ''));
    expect(price).toBeGreaterThanOrEqual(100000);
    expect(price).toBeLessThanOrEqual(500000);
  }
});
```

#### 2. Property Tabs Tests
```typescript
// apps/web/tests/property-tabs.spec.ts
test('Core Property tab displays all data', async ({ page }) => {
  await page.goto('/property/504203060330');

  await page.click('[data-testid="core-property-tab"]');

  // Verify all sections present
  await expect(page.locator('[data-testid="owner-info"]')).toBeVisible();
  await expect(page.locator('[data-testid="property-details"]')).toBeVisible();
  await expect(page.locator('[data-testid="valuation-info"]')).toBeVisible();
});

test('Sunbiz tab loads entities', async ({ page }) => {
  await page.goto('/property/504203060330');

  await page.click('[data-testid="sunbiz-tab"]');

  // Should show entities or "No entities found"
  const hasEntities = await page.locator('[data-testid="entity-card"]').count() > 0;
  const hasNoEntities = await page.locator(':text("No entities found")').isVisible();

  expect(hasEntities || hasNoEntities).toBeTruthy();
});

test('Sales History tab displays sales', async ({ page }) => {
  await page.goto('/property/474119030010'); // Property with known sales

  await page.click('[data-testid="sales-history-tab"]');

  await expect(page.locator('[data-testid="sale-record"]')).toHaveCount.greaterThan(0);

  // Verify price formatting (should be in dollars, not cents)
  const firstSale = page.locator('[data-testid="sale-record"]').first();
  const price = await firstSale.locator('[data-testid="sale-price"]').textContent();
  expect(price).toMatch(/\$[\d,]+/); // Should show $525,000 not $52500000
});

test('Tax Certificates tab shows certificates', async ({ page }) => {
  await page.goto('/property/504234-08-00-20'); // Property with known certs

  await page.click('[data-testid="tax-tab"]');

  await expect(page.locator('[data-testid="tax-certificate"]')).toHaveCount.greaterThan(0);
});
```

#### 3. Multi-Corporation Tests
```typescript
// apps/web/tests/owner-portfolio.spec.ts
test('Owner portfolio shows all entities', async ({ page }) => {
  await page.goto('/property/01462306000192680'); // MD LAND LLC property

  // Click on owner name to see portfolio
  await page.click('[data-testid="owner-link"]');

  // Should show multi-corporation view
  await expect(page.locator('[data-testid="portfolio-summary"]')).toBeVisible();
  await expect(page.locator(':text("MD LAND LLC"))).toBeVisible();
  await expect(page.locator(':text("4 properties")')).toBeVisible();
  await expect(page.locator(':text("$15.4M")')).toBeVisible();
});
```

---

## 📈 SUCCESS METRICS

### Performance
- [ ] Property search < 500ms response time
- [ ] Property detail page < 300ms load time
- [ ] All tabs load < 200ms
- [ ] No timeout errors

### Data Quality
- [ ] 100% of property cards show all required fields
- [ ] No undefined/null display in UI
- [ ] Prices formatted correctly (dollars not cents)
- [ ] All filters return accurate results

### Functionality
- [ ] All 45+ API endpoints working
- [ ] All property tabs load data
- [ ] Multi-corporation tracking visible in UI
- [ ] Search and filters work correctly

### Test Coverage
- [ ] 100% of tabs tested with Playwright
- [ ] All filters verified
- [ ] Edge cases covered
- [ ] Error states tested

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] Run comprehensive audit again
- [ ] All Playwright tests pass
- [ ] Performance benchmarks met
- [ ] Data migration complete

### Deployment
- [ ] Deploy database indexes (zero downtime)
- [ ] Deploy API changes
- [ ] Deploy UI changes
- [ ] Update documentation

### Post-Deployment
- [ ] Monitor error rates
- [ ] Check query performance
- [ ] Verify data flow
- [ ] User acceptance testing

---

## 📁 FILES CREATED

1. **comprehensive_audit_report.json** - Full audit data
2. **COMPLETE_AUDIT_FINDINGS_AND_ACTION_PLAN.md** - This document
3. **apps/web/tests/comprehensive-suite.spec.ts** - Playwright tests (to be created)
4. **scripts/fix_data_inconsistencies.py** - Data cleanup script (to be created)
5. **apps/web/src/utils/fieldMapper.ts** - Field standardization (to be created)

---

## 🎯 IMMEDIATE NEXT STEPS

1. **Run this command to add critical indexes** (15 min):
```bash
# See Week 1, Day 1-2 SQL above
```

2. **Fix EnhancedSunbizTab** (30 min):
```bash
# Edit apps/web/src/components/property/tabs/EnhancedSunbizTab.tsx
# Edit apps/api/property_live_api.py
```

3. **Run Playwright verification** (2 hours):
```bash
cd apps/web
npx playwright test
```

---

**Total Estimated Effort**: 72 hours (9 days)
**Priority**: HIGH - Production readiness depends on these fixes
**Status**: Ready to execute
