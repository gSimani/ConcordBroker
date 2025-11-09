# ConcordBroker Critical Fixes Checklist

## 🔴 IMMEDIATE (Do Today - 9 hours total)

### ✅ Task 1: Remove Hardcoded Credentials (1 hour)
**File:** `apps/api/property_live_api.py` lines 75-76

**Current (BAD):**
```python
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Fix:**
```python
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
```

---

### ✅ Task 2: Add Critical Database Indexes (4 hours)

**File:** Create `database/critical_indexes.sql`

```sql
-- Property Search Performance
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county
  ON florida_parcels(county);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_city
  ON florida_parcels(phy_city);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_zip
  ON florida_parcels(phy_zipcd);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner
  ON florida_parcels(owner_name);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_value
  ON florida_parcels(jv);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_sqft
  ON florida_parcels(tot_lvg_area);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_use
  ON florida_parcels(property_use);

-- Composite indexes for common filter combinations
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_city
  ON florida_parcels(county, phy_city);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_value
  ON florida_parcels(county, jv);
```

**Test After:**
```sql
-- Should be fast now (< 1 second)
EXPLAIN ANALYZE
SELECT * FROM florida_parcels
WHERE county = 'BROWARD'
AND phy_city = 'FORT LAUDERDALE'
LIMIT 100;
```

---

### ✅ Task 3: Create Missing API Endpoint (4 hours)

**File:** `apps/api/routers/sunbiz.py` (NEW FILE)

```python
from fastapi import APIRouter, Query
from typing import List, Optional
from supabase import create_client, Client
import os

router = APIRouter(prefix="/api/sunbiz", tags=["sunbiz"])

# Get from environment
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

@router.post("/active-companies")
async def get_active_companies(
    property_address: Optional[str] = None,
    owner_name: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """
    Get active Florida companies matching property owner
    """
    try:
        query = supabase.table("sunbiz_corporate").select("*")

        # Filter by owner name if provided
        if owner_name:
            query = query.ilike("entity_name", f"%{owner_name}%")

        # Apply limit
        query = query.limit(limit)

        response = query.execute()

        return {
            "companies": response.data,
            "total_count": len(response.data)
        }
    except Exception as e:
        return {
            "companies": [],
            "total_count": 0,
            "error": str(e)
        }
```

**Then update** `apps/api/main.py`:
```python
from routers import sunbiz

app.include_router(sunbiz.router)
```

**Test:**
```bash
curl -X POST http://localhost:8000/api/sunbiz/active-companies \
  -H "Content-Type: application/json" \
  -d '{"owner_name": "LLC", "limit": 10}'
```

---

## 🟡 HIGH PRIORITY (Next Week - 17 hours)

### ✅ Task 4: Fix Table Name Mismatches (8 hours)

**Option A:** Rename table in database
```sql
ALTER TABLE fl_sdf_sales RENAME TO florida_sdf_sales;
```

**Option B:** Update all code references (search for):
- `florida_sdf_sales` → `fl_sdf_sales`
- `sdf_sales` → `fl_sdf_sales`

**Files to check:**
```bash
grep -r "florida_sdf_sales" apps/
grep -r "sdf_sales" apps/
```

---

### ✅ Task 5: Refactor CorePropertyTab to Use API (8 hours)

**Current (BAD):**
```typescript
// CorePropertyTab.tsx - DIRECT SUPABASE QUERY
const { data: salesHistoryData } = await supabase
  .from('property_sales_history')
  .select('*')
  .eq('parcel_id', parcelId);
```

**Step 1:** Create API endpoint in `apps/api/property_live_api.py`:
```python
@app.get("/api/properties/{property_id}/sales-history")
async def get_property_sales_history(property_id: str):
    try:
        response = supabase.table("property_sales_history")\
            .select("*")\
            .eq("parcel_id", property_id)\
            .order("sale_date", desc=True)\
            .execute()

        # Convert sale prices from cents to dollars
        for sale in response.data:
            if sale.get("sale_price"):
                sale["sale_price"] = sale["sale_price"] / 100

        return {
            "sales": response.data,
            "count": len(response.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2:** Update CorePropertyTab.tsx:
```typescript
// Use API instead
const fetchSalesHistory = async () => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/properties/${parcelId}/sales-history`
    );
    const data = await response.json();
    setSalesHistory(data.sales);
  } catch (error) {
    console.error('Error fetching sales:', error);
  }
};
```

---

### ✅ Task 6: Add Error Handling for Large Queries (1 hour)

**File:** `apps/web/src/hooks/usePropertyData.ts` (or similar)

```typescript
const fetchWithRetry = async (url: string, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();

    } catch (error) {
      if (i === maxRetries - 1) throw error;
      // Exponential backoff
      await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000));
    }
  }
};
```

---

## 🟠 MEDIUM PRIORITY (This Month)

### Task 7: Audit React Hooks (12 hours)
- [ ] Document `useSalesData` implementation
- [ ] Document `usePropertyData` implementation
- [ ] Document `useOptimizedPropertySearch` implementation
- [ ] Map all data flows

### Task 8: Standardize Field Names (12 hours)
- [ ] Create field mapping documentation
- [ ] Update all components to use consistent names
- [ ] Create utility functions for field access

### Task 9: Refactor TaxesTab (8 hours)
- [ ] Create `/api/properties/{id}/tax-certificates` endpoint
- [ ] Update tab to use API
- [ ] Add error handling for missing certificates

### Task 10: Fix EnhancedSunbizTab (4 hours)
- [ ] Remove hardcoded "8.35M+" text
- [ ] Query real database count
- [ ] Add proper error states

---

## 📊 Progress Tracking

### Week 1 Checklist
- [ ] Remove hardcoded credentials (1h)
- [ ] Add database indexes (4h)
- [ ] Create /api/sunbiz/active-companies (4h)
- **Total: 9 hours**

### Week 2 Checklist
- [ ] Fix table name mismatches (8h)
- [ ] Refactor CorePropertyTab API access (8h)
- [ ] Add error handling (1h)
- **Total: 17 hours**

### Week 3-4 Checklist
- [ ] Audit all React hooks (12h)
- [ ] Standardize field names (12h)
- [ ] Refactor TaxesTab (8h)
- [ ] Fix EnhancedSunbizTab (4h)
- **Total: 36 hours**

---

## 🧪 Testing Checklist

After each fix:

### Test 1: Property Search
```
1. Go to /properties/search
2. Enter city: "Fort Lauderdale"
3. Should return results in < 2 seconds
4. Check developer console for errors
```

### Test 2: Property Detail Sales
```
1. Go to /property/{any-property-id}
2. Click "Sales History" tab
3. Should show sales data (if any)
4. Check that prices are in dollars, not cents
```

### Test 3: Sunbiz Tab
```
1. Go to /property/{any-property-id}
2. Click "Sunbiz" tab
3. Should load without errors
4. Should show real company count (not hardcoded "8.35M+")
```

### Test 4: Tax Certificates Tab
```
1. Go to /property/504234-08-00-20 (has certificates)
2. Click "Taxes" tab
3. Should show certificate data
4. Should not have console errors
```

---

## 📝 Commit Messages

Use these formats:

```bash
# After Task 1
git commit -m "security: remove hardcoded Supabase credentials from property_live_api.py"

# After Task 2
git commit -m "perf: add critical indexes to florida_parcels table for search optimization"

# After Task 3
git commit -m "feat: add /api/sunbiz/active-companies endpoint for EnhancedSunbizTab"

# After Task 5
git commit -m "refactor: move CorePropertyTab sales queries from direct DB to API layer"
```

---

## 🚨 Rollback Plan

If anything breaks:

### Rollback Task 1 (Credentials)
```bash
# Revert commit
git revert HEAD

# Or manually restore
# Edit apps/api/property_live_api.py
# Add back SUPABASE_URL and SUPABASE_KEY constants
```

### Rollback Task 2 (Indexes)
```sql
-- Drop indexes if they cause issues
DROP INDEX IF EXISTS idx_florida_parcels_county;
DROP INDEX IF EXISTS idx_florida_parcels_city;
-- ... etc
```

### Rollback Task 3 (New Endpoint)
```bash
# Remove router from main.py
# Delete apps/api/routers/sunbiz.py
```

---

## 📞 Help & Resources

### Database Access
- **Supabase URL:** https://pmispwtdngkcmsrsjwbp.supabase.co
- **Dashboard:** https://app.supabase.com/project/pmispwtdngkcmsrsjwbp

### Key Files
- API: `apps/api/property_live_api.py`
- Routers: `apps/api/routers/properties.py`
- Components: `apps/web/src/components/property/`
- Tabs: `apps/web/src/components/property/tabs/`

### Audit Reports
- Full audit: `CONCORDBROKER_AUDIT_REPORT.json`
- Summary: `AUDIT_SUMMARY.md`
- This checklist: `CRITICAL_FIXES_CHECKLIST.md`

---

**Start with Task 1. Test. Then Task 2. Test. Then Task 3. Test.**

**Don't skip testing between tasks!**
