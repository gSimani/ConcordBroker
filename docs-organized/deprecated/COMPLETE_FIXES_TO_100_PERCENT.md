# Complete Fixes to Achieve 100% Test Pass Rate

**Target**: 23/23 Playwright tests passing (currently 16/23)

---

## Fix 1: Add Missing API Endpoint for Sunbiz Tab (CRITICAL)

**File**: `apps/api/property_live_api.py`
**Issue**: EnhancedSunbizTab calls `/api/supabase/active-companies` which doesn't exist
**Tests Fixed**: 1

### Add this endpoint:

```python
@app.get("/api/properties/{property_id}/sunbiz-entities")
async def get_property_sunbiz_entities(property_id: str):
    """Get Sunbiz entities for a property"""
    try:
        # Get property owner name
        property_result = supabase.table('florida_parcels')\
            .select('owner_name, parcel_id')\
            .eq('parcel_id', property_id)\
            .limit(1)\
            .execute()

        if not property_result.data or len(property_result.data) == 0:
            return {
                "companies": [],
                "total_count": 0,
                "message": "Property not found"
            }

        owner_name = property_result.data[0].get('owner_name', '')

        if not owner_name:
            return {
                "companies": [],
                "total_count": 0,
                "message": "No owner name available"
            }

        # Search Sunbiz corporate table
        entities_result = supabase.table('sunbiz_corporate')\
            .select('doc_number, entity_name, entity_type, status, filing_date, prin_addr1, prin_city, prin_state, prin_zip')\
            .ilike('entity_name', f'%{owner_name}%')\
            .limit(20)\
            .execute()

        companies = []
        for entity in entities_result.data:
            companies.append({
                "id": entity.get('doc_number'),
                "doc_number": entity.get('doc_number'),
                "entity_name": entity.get('entity_name', '').strip(),
                "entity_type": entity.get('entity_type', ''),
                "status": entity.get('status', 'Active'),
                "filing_date": entity.get('filing_date', ''),
                "business_address": f"{entity.get('prin_addr1', '')}, {entity.get('prin_city', '')}, {entity.get('prin_state', '')} {entity.get('prin_zip', '')}".strip()
            })

        return {
            "companies": companies,
            "total_count": len(companies)
        }

    except Exception as e:
        print(f"Error fetching Sunbiz entities: {e}")
        return {
            "companies": [],
            "total_count": 0,
            "error": str(e)
        }
```

---

## Fix 2: Update EnhancedSunbizTab to Use Correct Endpoint

**File**: `apps/web/src/components/property/tabs/EnhancedSunbizTab.tsx`
**Issue**: Calls wrong endpoint
**Tests Fixed**: 1 (same as Fix 1)

### Change line 38 from:

```typescript
const response = await fetch('/api/supabase/active-companies', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    property_address: propertyData?.address,
    owner_name: propertyData?.owner_name,
    limit: 100
  }),
});
```

### To:

```typescript
const parcelId = propertyData?.parcel_id || propertyData?.id;
const response = await fetch(`/api/properties/${parcelId}/sunbiz-entities`, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  },
});
```

---

## Fix 3: Add data-testid Attributes to PropertySearch

**File**: `apps/web/src/pages/properties/PropertySearch.tsx`
**Issue**: Missing data-testid attributes for Playwright tests
**Tests Fixed**: 3 (search input, filters, property cards)

### Changes Needed:

1. **Search Input** (around line 1800): Add `data-testid="search-input"`
2. **Property Cards** (line 2471): Add `data-testid="property-card"` to MiniPropertyCard wrapper
3. **Filter Inputs**: Add data-testids to min/max price inputs
4. **No Results Message**: Add "No properties found" message when properties.length === 0

---

## Fix 4: Add "No Properties Found" Message

**File**: `apps/web/src/pages/properties/PropertySearch.tsx`
**Location**: After line 2460 (before property cards rendering)
**Issue**: No message displayed when search returns 0 results
**Tests Fixed**: 1

### Add this code before the properties.map() section:

```typescript
{/* Results Section */}
{!loading && properties.length === 0 && (
  <Card className="p-8 text-center">
    <CardContent>
      <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
      <h3 className="text-lg font-semibold mb-2">No properties found</h3>
      <p className="text-gray-600 mb-4">
        Try adjusting your search criteria or browse by city
      </p>
      {/* Existing filter suggestion buttons... */}
    </CardContent>
  </Card>
)}
```

---

## Fix 5: Add data-testid to Sales History Tab

**File**: Check which file is being used for Sales History
**Issue**: Tab shows blank screen, no data or message
**Tests Fixed**: 1

### Investigation needed:
1. Find the actual SalesHistoryTab component file
2. Verify it queries `property_sales_history` table
3. Add "No sales history" message when no data
4. Add data-testid="sale-record" to sale items
5. Add data-testid="sale-price" to price display

---

## Fix 6: Add data-testid to EnhancedPropertyProfile

**File**: `apps/web/src/pages/property/EnhancedPropertyProfile.tsx`
**Issue**: Missing data-testid="property-detail" for performance test
**Tests Fixed**: 1

### Add to main container (around line 100):

```typescript
<div className="property-profile" data-testid="property-detail">
  {/* existing content */}
</div>
```

---

## Fix 7: Fix undefined/null Display Issue

**File**: Unknown (need to find where "undefined" or "null" is displayed)
**Issue**: 1 instance of undefined/null/NaN visible in UI
**Tests Fixed**: 1

### Steps:
1. Run test to capture screenshot
2. Find exact location of undefined display
3. Add fallback: `{value || 'N/A'}` or `{value ?? '-'}`

---

## Fix 8: Update County Filter Interaction in Test

**File**: `apps/web/tests/comprehensive-concordbroker-suite.spec.ts`
**Issue**: County filter uses custom component, not native <select>
**Tests Fixed**: 1

### Update test (line 71) from:

```typescript
await countySelect.selectOption({ label: 'Broward' });
```

### To:

```typescript
await countySelect.click();
await page.locator('text=Broward').click();
```

---

## Fix 9: Update Price Filter Selectors in Test

**File**: `apps/web/tests/comprehensive-concordbroker-suite.spec.ts`
**Issue**: Filter inputs have incorrect selectors
**Tests Fixed**: 1

### Need to:
1. Inspect PropertySearch to find actual placeholder text
2. Update test selectors to match
3. Or add data-testid to filter inputs

---

## Deployment Sequence

### Step 1: Backend API (5 minutes)
```bash
cd apps/api
# Add endpoint to property_live_api.py
# Restart API server
```

### Step 2: Frontend Components (10 minutes)
1. Fix EnhancedSunbizTab endpoint call
2. Add data-testid attributes to PropertySearch
3. Add "No properties found" message
4. Add data-testid to EnhancedPropertyProfile
5. Find and fix Sales History tab

### Step 3: Fix Test Selectors (5 minutes)
1. Update county filter interaction
2. Fix price filter selectors

### Step 4: Verify (5 minutes)
```bash
cd apps/web
npx playwright test tests/comprehensive-concordbroker-suite.spec.ts
```

---

## Expected Results After All Fixes

```
Running 23 tests using 1 worker

  ✓ Property Search & Filters › Property search loads and displays results
  ✓ Property Search & Filters › Price filter works correctly
  ✓ Property Search & Filters › County filter works
  ✓ Property Detail - Core Tab › Core Property tab displays owner information
  ✓ Property Detail - Core Tab › Core tab shows property valuation
  ✓ Property Detail - Core Tab › Core tab shows property characteristics
  ✓ Property Detail - Sunbiz Tab › Sunbiz tab loads without errors
  ✓ Property Detail - Sunbiz Tab › Sunbiz tab displays entity details when available
  ✓ Property Detail - Sales History Tab › Sales History tab displays sale records
  ✓ Property Detail - Sales History Tab › Sale prices are formatted correctly
  ✓ Property Detail - Tax Certificates Tab › Tax tab loads and displays certificates or no-data message
  ✓ Property Detail - Tax Certificates Tab › Tax certificate shows buyer entity information
  ✓ Multi-Corporation Owner Tracking › Owner with multiple properties shows portfolio
  ✓ Multi-Corporation Owner Tracking › Portfolio shows total value and property count
  ✓ Data Integrity › No undefined or null displayed in UI
  ✓ Data Integrity › All property cards show required fields
  ✓ Data Integrity › Prices are in dollars not cents
  ✓ API Endpoints › Property search API responds
  ✓ API Endpoints › Property detail API responds
  ✓ API Endpoints › Sunbiz entities API responds
  ✓ API Endpoints › Tax certificates API responds
  ✓ Performance › Property search completes in < 3 seconds
  ✓ Performance › Property detail page loads in < 2 seconds

  23 passed (100%)
```

---

## Time Estimate

- Backend API: 5 minutes
- Frontend fixes: 15 minutes
- Test updates: 5 minutes
- Verification: 5 minutes
- **Total: 30 minutes**

---

**Status**: Ready to execute
**Priority**: CRITICAL - Blocks production deployment
