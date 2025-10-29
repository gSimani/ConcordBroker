# 🚀 SUPABASE OPTIMIZATION MASTER PLAN
**ConcordBroker - Complete Endpoint Optimization Strategy**

**Generated**: 2025-10-29
**Status**: Ready for Implementation
**Goal**: Optimize all Supabase endpoints across Property Pages, Detail Views, and Sunbiz components
**Expected Improvement**: 5-10x faster overall system performance

---

## 📊 EXECUTIVE SUMMARY

### Current System State

**Database**:
- ✅ 2M+ records in florida_parcels (Broward, Miami-Dade, Palm Beach)
- ✅ 96K+ sales history records
- ⚠️ **EMPTY** Sunbiz tables (2M+ corporate, 15M+ entities ready to load)
- ⚠️ Suboptimal indexes for current query patterns

**Performance Baseline**:
- Property Search: 2-4 seconds
- Property Detail Load: 3-6 seconds (with all tabs)
- Autocomplete: 800ms - 1.5s (4 parallel queries)
- Sales Data: 2-4s (3 sequential queries)
- Sunbiz (when loaded): Estimated 5-10s (no optimization yet)

**Target Performance**:
- Property Search: <500ms (5-8x faster)
- Property Detail Load: <1s (3-6x faster)
- Autocomplete: <200ms (4-7x faster)
- Sales Data: <400ms (5-10x faster)
- Sunbiz: <500ms (10-20x faster with pre-computed matches)

---

## 🎯 PRIORITY SYSTEM

**Priority Levels**:
- 🔴 **P0 - CRITICAL**: Must fix before Sunbiz data load (System breaking)
- 🟠 **P1 - HIGH**: Major performance impact, implement within 1 week
- 🟡 **P2 - MEDIUM**: Significant improvement, implement within 2 weeks
- 🟢 **P3 - LOW**: Nice to have, implement when convenient

**Impact Scoring** (1-10 scale):
- 10 = Transforms user experience, 10x+ improvement
- 7-9 = Major improvement, 3-5x faster
- 4-6 = Noticeable improvement, 2x faster
- 1-3 = Minor improvement, <50% faster

**Effort Scoring** (hours):
- XS = 0.5-2 hours
- S = 2-4 hours
- M = 4-8 hours
- L = 8-16 hours
- XL = 16-40 hours

---

## 🔴 P0 - CRITICAL OPTIMIZATIONS (Fix Before Sunbiz Data Load)

### P0-1: Create Missing Sunbiz Indexes 🔴

**Problem**: Address and name searches will do full table scans on 2M+ corporate + 15M+ entities

**Impact**: **10/10** - Without these, Sunbiz tab will timeout or take 30-60 seconds
**Effort**: **S** (2-3 hours)
**Dependencies**: None

**Action**:
```sql
-- Run in Supabase SQL Editor BEFORE loading Sunbiz data

-- Address matching indexes (CRITICAL for searchByExactAddress)
CREATE INDEX CONCURRENTLY idx_sunbiz_corporate_prin_addr1
  ON sunbiz_corporate(prin_addr1) WHERE prin_addr1 IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_sunbiz_corporate_mail_addr1
  ON sunbiz_corporate(mail_addr1) WHERE mail_addr1 IS NOT NULL;

-- Full-text search indexes (CRITICAL for fuzzy matching)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX CONCURRENTLY idx_sunbiz_corporate_entity_name_trgm
  ON sunbiz_corporate USING gist(entity_name gist_trgm_ops);

CREATE INDEX CONCURRENTLY idx_sunbiz_corporate_agent_trgm
  ON sunbiz_corporate USING gist(registered_agent gist_trgm_ops);

-- Fictitious name indexes
CREATE INDEX CONCURRENTLY idx_sunbiz_fictitious_name_gin
  ON sunbiz_fictitious USING gin(to_tsvector('english', name));

CREATE INDEX CONCURRENTLY idx_sunbiz_fictitious_owner_gin
  ON sunbiz_fictitious USING gin(to_tsvector('english', owner_name));

-- florida_parcels owner search index (for fetchOfficerProperties)
CREATE INDEX CONCURRENTLY idx_florida_parcels_owner_name
  ON florida_parcels(owner_name) WHERE owner_name IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_florida_parcels_owner_name_trgm
  ON florida_parcels USING gist(owner_name gist_trgm_ops);
```

**Verification**:
```sql
-- Check indexes created
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('sunbiz_corporate', 'sunbiz_fictitious', 'florida_parcels')
  AND indexname LIKE '%trgm%' OR indexname LIKE '%gin%';
```

---

### P0-2: Create sunbiz_officers Table 🔴

**Problem**: Code references `sunbiz_officers` table that doesn't exist, causing silent failures

**Impact**: **8/10** - Officer matching completely broken without this
**Effort**: **XS** (1 hour)
**Dependencies**: None

**Action**:
```sql
-- Create missing officers table
CREATE TABLE IF NOT EXISTS sunbiz_officers (
  id BIGSERIAL PRIMARY KEY,
  doc_number VARCHAR(12) NOT NULL,
  officer_name VARCHAR(200) NOT NULL,
  officer_title VARCHAR(100),
  officer_address TEXT,
  filing_date DATE,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(doc_number, officer_name),
  FOREIGN KEY (doc_number) REFERENCES sunbiz_corporate(doc_number) ON DELETE CASCADE
);

-- Critical indexes
CREATE INDEX idx_sunbiz_officers_officer_name
  ON sunbiz_officers(officer_name);

CREATE INDEX idx_sunbiz_officers_doc_number
  ON sunbiz_officers(doc_number);

CREATE INDEX idx_sunbiz_officers_name_trgm
  ON sunbiz_officers USING gist(officer_name gist_trgm_ops);

-- Enable RLS
ALTER TABLE sunbiz_officers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read access on sunbiz_officers"
  ON sunbiz_officers FOR SELECT
  USING (true);
```

---

### P0-3: Fix/Remove ActiveCompaniesSection API Dependency 🔴

**Problem**: Component calls `/api/supabase/active-companies` which doesn't exist → 404 errors

**Impact**: **9/10** - Component completely broken, shows empty state
**Effort**: **S** (2-3 hours)
**Dependencies**: None

**Option A - Remove Component** (RECOMMENDED):
```typescript
// apps/web/src/components/property/tabs/SunbizTab.tsx

// REMOVE import
// import { ActiveCompaniesSection } from './ActiveCompaniesSection';

// REMOVE from JSX (lines ~300-320)
// <ActiveCompaniesSection ... />

// Reason: Duplicates main useSunbizData functionality
```

**Option B - Implement Missing API**:
```python
# apps/api/property_live_api.py

@app.post("/api/supabase/active-companies")
async def get_active_companies(request: ActiveCompaniesRequest):
    """Fetch active companies with filters"""
    query = supabase.table('sunbiz_corporate').select('*')

    if request.owner_name:
        query = query.or(f"entity_name.ilike.%{request.owner_name}%,registered_agent.ilike.%{request.owner_name}%")

    if request.property_address:
        query = query.or(f"prin_addr1.ilike.%{request.property_address}%,mail_addr1.ilike.%{request.property_address}%")

    if request.entity_type:
        query = query.eq('entity_type', request.entity_type)

    query = query.eq('status', 'ACTIVE').order('filing_date', desc=True)
    query = query.range(request.offset, request.offset + request.limit - 1)

    response = query.execute()

    return {
        "success": True,
        "companies": response.data,
        "total": len(response.data)
    }
```

---

### P0-4: Create Supabase RPC for Autocomplete 🔴

**Problem**: 4 parallel queries (address, owner, city, county) → 800ms-1.5s latency

**Impact**: **9/10** - Single biggest UX improvement
**Effort**: **M** (4-5 hours)
**Dependencies**: None

**Action**:
```sql
-- Create unified autocomplete RPC
CREATE OR REPLACE FUNCTION search_property_autocomplete(
  p_query TEXT,
  p_county TEXT DEFAULT NULL,
  p_limit INT DEFAULT 20
)
RETURNS TABLE (
  parcel_id TEXT,
  phy_addr1 TEXT,
  phy_city TEXT,
  owner_name TEXT,
  just_value NUMERIC,
  property_use TEXT,
  match_type TEXT -- 'address', 'owner', 'city'
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY

  -- Address matches (highest priority)
  SELECT
    fp.parcel_id,
    fp.phy_addr1,
    fp.phy_city,
    fp.owner_name,
    fp.just_value,
    fp.property_use,
    'address'::TEXT as match_type
  FROM florida_parcels fp
  WHERE (p_county IS NULL OR fp.county = p_county)
    AND fp.phy_addr1 ILIKE p_query || '%'
    AND fp.year = 2025
  LIMIT (p_limit / 2)

  UNION ALL

  -- Owner matches
  SELECT
    fp.parcel_id,
    fp.phy_addr1,
    fp.phy_city,
    fp.owner_name,
    fp.just_value,
    fp.property_use,
    'owner'::TEXT as match_type
  FROM florida_parcels fp
  WHERE (p_county IS NULL OR fp.county = p_county)
    AND fp.owner_name ILIKE p_query || '%'
    AND fp.year = 2025
  LIMIT (p_limit / 3)

  UNION ALL

  -- City matches (lowest priority)
  SELECT
    fp.parcel_id,
    fp.phy_addr1,
    fp.phy_city,
    fp.owner_name,
    fp.just_value,
    fp.property_use,
    'city'::TEXT as match_type
  FROM florida_parcels fp
  WHERE (p_county IS NULL OR fp.county = p_county)
    AND fp.phy_city ILIKE p_query || '%'
    AND fp.year = 2025
  LIMIT (p_limit / 6)

  ORDER BY match_type, phy_addr1
  LIMIT p_limit;
END;
$$;
```

**Frontend Update**:
```typescript
// apps/web/src/hooks/usePropertyAutocomplete.ts

// BEFORE: 4 parallel queries
const addressResults = await supabase.from('florida_parcels').select('*').ilike('phy_addr1', `${query}%`);
const ownerResults = await supabase.from('florida_parcels').select('*').ilike('owner_name', `${query}%`);
const cityResults = await supabase.from('florida_parcels').select('*').ilike('phy_city', `${query}%`);
const countyResults = await supabase.from('florida_parcels').select('*').ilike('county', `${query}%`);

// AFTER: Single RPC call
const { data } = await supabase.rpc('search_property_autocomplete', {
  p_query: query,
  p_county: selectedCounty,
  p_limit: 20
});
```

**Impact**: 4 queries (800-1500ms) → 1 RPC (100-200ms) = **5-15x faster**

---

## 🟠 P1 - HIGH PRIORITY (Implement Within 1 Week)

### P1-1: Create Unified Property Data RPC 🟠

**Problem**: 3 sequential queries for property detail page (property + sales + entities + taxes)

**Impact**: **9/10** - 3-6 second load → <1 second
**Effort**: **M** (5-6 hours)
**Dependencies**: None

**Action**:
```sql
CREATE OR REPLACE FUNCTION get_property_complete(p_parcel_id TEXT, p_county TEXT)
RETURNS TABLE (
  property_data JSONB,
  sales_history JSONB,
  entities JSONB,
  tax_info JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    -- Property data
    row_to_json(fp.*)::jsonb as property_data,

    -- Sales history (aggregated)
    COALESCE(
      (SELECT json_agg(json_build_object(
        'sale_date', psh.sale_date,
        'sale_price', psh.sale_price,
        'sale_type', psh.sale_type,
        'qualified_sale', psh.qualified_sale
      ) ORDER BY psh.sale_date DESC)
      FROM property_sales_history psh
      WHERE psh.parcel_id = p_parcel_id),
      '[]'::json
    )::jsonb as sales_history,

    -- Linked entities
    COALESCE(
      (SELECT json_agg(json_build_object(
        'entity_name', sc.entity_name,
        'entity_type', sc.entity_type,
        'status', sc.status,
        'match_confidence', pel.confidence
      ))
      FROM parcel_entity_links pel
      JOIN sunbiz_corporate sc ON pel.sunbiz_doc_number = sc.doc_number
      WHERE pel.parcel_id = p_parcel_id),
      '[]'::json
    )::jsonb as entities,

    -- Tax certificates
    COALESCE(
      (SELECT json_agg(json_build_object(
        'certificate_number', tc.certificate_number,
        'face_amount', tc.face_amount,
        'tax_year', tc.tax_year
      ))
      FROM tax_certificates tc
      WHERE tc.parcel_id = p_parcel_id),
      '[]'::json
    )::jsonb as tax_info

  FROM florida_parcels fp
  WHERE fp.parcel_id = p_parcel_id
    AND fp.county = p_county
    AND fp.year = 2025;
END;
$$;
```

**Frontend Update**:
```typescript
// apps/web/src/hooks/usePropertyData.ts

// BEFORE: 3-4 sequential calls
const property = await supabase.from('florida_parcels').select('*').eq('parcel_id', id).single();
const sales = await supabase.from('property_sales_history').select('*').eq('parcel_id', id);
const entities = await supabase.from('florida_entities').select('*').eq('parcel_id', id);
const taxes = await supabase.from('tax_certificates').select('*').eq('parcel_id', id);

// AFTER: Single RPC call
const { data } = await supabase.rpc('get_property_complete', {
  p_parcel_id: id,
  p_county: county
});

// data.property_data, data.sales_history, data.entities, data.tax_info
```

**Impact**: 3 queries (2-4s) → 1 RPC (300-600ms) = **4-7x faster**

---

### P1-2: Create Pre-Computed Sunbiz-Property Matching Table 🟠

**Problem**: fetchOfficerProperties() makes 10 parallel queries to 9.7M properties = 5-10 seconds

**Impact**: **10/10** - Eliminates most expensive operation in Sunbiz tab
**Effort**: **XL** (20-30 hours initial, then incremental updates)
**Dependencies**: P0-1 (indexes), P0-2 (officers table)

**Phase 1 - Create Table**:
```sql
CREATE TABLE IF NOT EXISTS sunbiz_property_matches (
  id BIGSERIAL PRIMARY KEY,
  parcel_id VARCHAR(20) NOT NULL,
  sunbiz_doc_number VARCHAR(12) NOT NULL,
  match_type VARCHAR(50) NOT NULL, -- 'exact_address', 'owner_name_exact', 'owner_name_fuzzy', 'officer_name'
  match_confidence DECIMAL(3,2) NOT NULL, -- 0.00-1.00
  matched_date TIMESTAMP DEFAULT NOW(),
  last_verified TIMESTAMP,
  is_verified BOOLEAN DEFAULT FALSE,

  UNIQUE(parcel_id, sunbiz_doc_number),
  FOREIGN KEY (parcel_id) REFERENCES florida_parcels(parcel_id) ON DELETE CASCADE,
  FOREIGN KEY (sunbiz_doc_number) REFERENCES sunbiz_corporate(doc_number) ON DELETE CASCADE
);

CREATE INDEX idx_sunbiz_property_matches_parcel
  ON sunbiz_property_matches(parcel_id);

CREATE INDEX idx_sunbiz_property_matches_sunbiz
  ON sunbiz_property_matches(sunbiz_doc_number);

CREATE INDEX idx_sunbiz_property_matches_confidence
  ON sunbiz_property_matches(match_confidence DESC);
```

**Phase 2 - Populate Matches** (Run as background job):
```sql
-- Insert exact address matches (highest confidence)
INSERT INTO sunbiz_property_matches (parcel_id, sunbiz_doc_number, match_type, match_confidence)
SELECT DISTINCT
  fp.parcel_id,
  sc.doc_number,
  'exact_address',
  1.00
FROM florida_parcels fp
JOIN sunbiz_corporate sc ON (
  UPPER(TRIM(fp.phy_addr1)) = UPPER(TRIM(sc.prin_addr1))
  OR UPPER(TRIM(fp.phy_addr1)) = UPPER(TRIM(sc.mail_addr1))
)
WHERE fp.year = 2025
  AND sc.status = 'ACTIVE'
ON CONFLICT (parcel_id, sunbiz_doc_number) DO NOTHING;

-- Insert owner name exact matches (high confidence)
INSERT INTO sunbiz_property_matches (parcel_id, sunbiz_doc_number, match_type, match_confidence)
SELECT DISTINCT
  fp.parcel_id,
  sc.doc_number,
  'owner_name_exact',
  0.95
FROM florida_parcels fp
JOIN sunbiz_corporate sc ON
  UPPER(TRIM(fp.owner_name)) = UPPER(TRIM(sc.entity_name))
WHERE fp.year = 2025
  AND sc.status = 'ACTIVE'
ON CONFLICT (parcel_id, sunbiz_doc_number) DO NOTHING;

-- Insert fuzzy name matches (medium confidence)
INSERT INTO sunbiz_property_matches (parcel_id, sunbiz_doc_number, match_type, match_confidence)
SELECT DISTINCT
  fp.parcel_id,
  sc.doc_number,
  'owner_name_fuzzy',
  similarity(fp.owner_name, sc.entity_name)::DECIMAL(3,2)
FROM florida_parcels fp
CROSS JOIN sunbiz_corporate sc
WHERE fp.year = 2025
  AND sc.status = 'ACTIVE'
  AND similarity(fp.owner_name, sc.entity_name) > 0.6 -- 60% similarity threshold
ON CONFLICT (parcel_id, sunbiz_doc_number) DO NOTHING;

-- Est. Runtime: 8-12 hours for full dataset
-- Run during off-hours
```

**Phase 3 - Update Frontend**:
```typescript
// apps/web/src/components/property/tabs/SunbizTab.tsx

// BEFORE: fetchOfficerProperties() - 10 parallel queries
const propertyPromises = Array.from(searchNames).slice(0, 10).map(async (searchName) => {
  return supabase.from('florida_parcels').select('...').ilike('owner_name', `%${searchName}%`).limit(3);
});
const results = await Promise.all(propertyPromises);

// AFTER: Single query to pre-computed matches
const { data: properties } = await supabase
  .from('sunbiz_property_matches')
  .select(`
    parcel_id,
    match_confidence,
    florida_parcels:parcel_id (
      phy_addr1,
      phy_city,
      owner_name,
      just_value
    )
  `)
  .eq('sunbiz_doc_number', docNumber)
  .gte('match_confidence', 0.6)
  .order('match_confidence', { ascending: false })
  .limit(10);
```

**Impact**: 10×1000ms queries → 1×50ms query = **200x faster**

---

### P1-3: Implement Adaptive Field Selection 🟠

**Problem**: Queries return all 50+ columns when most views need only 10-15

**Impact**: **7/10** - Reduces payload size by 60-70%
**Effort**: **M** (6-8 hours)
**Dependencies**: None

**Backend Changes**:
```python
# apps/api/property_live_api.py

# Define field sets
FIELD_SETS = {
    "minimal": [
        "parcel_id", "phy_addr1", "phy_city", "county",
        "owner_name", "just_value", "property_use"
    ],
    "list_view": [
        "parcel_id", "phy_addr1", "phy_city", "phy_zipcd", "county",
        "owner_name", "just_value", "year_built", "bedrooms", "bathrooms",
        "living_area", "property_use"
    ],
    "detail_view": [
        "parcel_id", "phy_addr1", "phy_addr2", "phy_city", "phy_zipcd", "county",
        "owner_name", "owner_addr1", "owner_city", "owner_state",
        "just_value", "assessed_value", "taxable_value", "land_value", "building_value",
        "year_built", "bedrooms", "bathrooms", "living_area", "land_sqft",
        "property_use", "sale_date", "sale_price"
    ],
    "complete": ["*"]
}

@app.get("/api/properties/search")
async def search_properties(
    fields: Optional[str] = Query("list_view", description="Field set: minimal, list_view, detail_view, complete, or comma-separated list")
):
    # Parse field selection
    if fields in FIELD_SETS:
        selected_fields = ','.join(FIELD_SETS[fields])
    elif ',' in fields:
        selected_fields = fields  # Custom field list
    else:
        selected_fields = ','.join(FIELD_SETS["list_view"])

    # Query with field selection
    query = supabase.table('florida_parcels').select(selected_fields)
    # ... rest of query ...
```

**Frontend Usage**:
```typescript
// Minimal for autocomplete
const { data } = await fetch('/api/properties/search?fields=minimal&q=main');

// List view for search results
const { data } = await fetch('/api/properties/search?fields=list_view&county=Broward');

// Detail view for property cards
const { data } = await fetch('/api/properties/search?fields=detail_view&parcel_id=123');

// Complete for property detail page
const { data } = await fetch('/api/properties/search?fields=complete&parcel_id=123');
```

**Impact**:
- Autocomplete: 3.5KB → 800 bytes per record (**77% reduction**)
- List view: 3.5KB → 1.5KB per record (**57% reduction**)
- 1000 properties: 3.5MB → 1.5MB (**2MB saved**)

---

### P1-4: Implement Batch API Endpoint 🟠

**Problem**: MiniPropertyCards fetch sales data individually = N requests for N properties

**Impact**: **8/10** - Batch loading 100x more efficient
**Effort**: **M** (4-6 hours)
**Dependencies**: None

**Backend**:
```python
# apps/api/property_live_api.py

@app.post("/api/properties/batch")
async def batch_property_data(request: BatchPropertyRequest):
    """Fetch data for multiple properties in one call"""

    parcel_ids = request.parcel_ids[:100]  # Limit to 100 per batch
    include_sales = request.include_sales or False
    include_entities = request.include_entities or False

    # Main property data
    properties_query = supabase.table('florida_parcels').select(
        ','.join(FIELD_SETS[request.field_set or "list_view"])
    ).in_('parcel_id', parcel_ids)

    properties = properties_query.execute().data

    # Optional: Add sales data
    if include_sales:
        sales_query = supabase.table('property_sales_history').select('*').in_('parcel_id', parcel_ids)
        sales = sales_query.execute().data

        # Map sales to properties
        sales_by_parcel = {}
        for sale in sales:
            if sale['parcel_id'] not in sales_by_parcel:
                sales_by_parcel[sale['parcel_id']] = []
            sales_by_parcel[sale['parcel_id']].append(sale)

        for prop in properties:
            prop['sales_history'] = sales_by_parcel.get(prop['parcel_id'], [])

    return {
        "success": True,
        "data": properties,
        "count": len(properties),
        "requested": len(parcel_ids)
    }
```

**Frontend Update**:
```typescript
// apps/web/src/hooks/useBatchPropertyData.ts (NEW)

export function useBatchPropertyData(parcelIds: string[]) {
  const [data, setData] = useState<PropertyData[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (parcelIds.length === 0) return;

    const fetchBatch = async () => {
      setLoading(true);

      // Batch into groups of 100
      const batches = chunk(parcelIds, 100);

      const results = await Promise.all(
        batches.map(batch =>
          fetch('/api/properties/batch', {
            method: 'POST',
            body: JSON.stringify({
              parcel_ids: batch,
              field_set: 'list_view',
              include_sales: true
            })
          }).then(r => r.json())
        )
      );

      setData(results.flatMap(r => r.data));
      setLoading(false);
    };

    fetchBatch();
  }, [parcelIds]);

  return { data, loading };
}
```

**Impact**: 100 requests → 1 batch request = **100x reduction in network calls**

---

## 🟡 P2 - MEDIUM PRIORITY (Implement Within 2 Weeks)

### P2-1: Add Database Query Caching Strategy 🟡

**Impact**: **7/10**
**Effort**: **M** (5-7 hours)

```python
# Redis caching layer
CACHE_TTL = {
    "search_results": 30 * 60,      # 30 minutes
    "autocomplete": 5 * 60,          # 5 minutes
    "property_detail": 60 * 60,      # 1 hour
    "preloaded_counties": -1,        # Permanent until data update
}

@app.get("/api/properties/search")
async def search_properties(...):
    cache_key = f"search:{county}:{filters_hash}"

    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query database
    results = supabase.table('florida_parcels').select('*')...

    # Cache results
    redis_client.setex(cache_key, CACHE_TTL["search_results"], json.dumps(results))

    return results
```

---

### P2-2: Name Normalization for Entity Matching 🟡

**Impact**: **6/10**
**Effort**: **S** (3-4 hours)

```typescript
// apps/web/src/utils/nameNormalization.ts

export function normalizeEntityName(name: string): string {
  return name
    .toUpperCase()
    .trim()
    .replace(/\s+LLC\s*$/i, '')           // Remove " LLC"
    .replace(/\s+INC\.?\s*$/i, '')        // Remove " INC"
    .replace(/\s+CORP\.?\s*$/i, '')       // Remove " CORP"
    .replace(/\s+LIMITED\s*$/i, '')       // Remove " LIMITED"
    .replace(/\s*,\s*/g, ' ')             // ", " → " "
    .replace(/\s+/g, ' ')                 // Collapse spaces
    .replace(/[.,\-\(\)]/g, '');          // Remove punctuation
}
```

---

### P2-3: Add Result Caching in Frontend 🟡

**Impact**: **6/10**
**Effort**: **S** (2-3 hours)

```typescript
// apps/web/src/hooks/useSearchCache.ts

const CACHE = new Map<string, CachedResult>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export function useSearchCache(key: string, fetcher: () => Promise<any>) {
  const [data, setData] = useState(null);

  useEffect(() => {
    const cached = CACHE.get(key);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      setData(cached.data);
      return;
    }

    fetcher().then(result => {
      CACHE.set(key, { data: result, timestamp: Date.now() });
      setData(result);
    });
  }, [key]);

  return data;
}
```

---

## 🟢 P3 - LOW PRIORITY (Nice to Have)

### P3-1: Implement Cursor-Based Pagination 🟢

**Impact**: **5/10**
**Effort**: **M** (4-5 hours)

**Benefit**: 50x faster pagination for large result sets (page 100+)

---

### P3-2: Add Health Checks for Data Availability 🟢

**Impact**: **4/10**
**Effort**: **XS** (1-2 hours)

```typescript
async function checkSunbizDataLoaded(): Promise<boolean> {
  const { count } = await supabase
    .from('sunbiz_corporate')
    .select('*', { count: 'exact', head: true });

  return count > 0;
}

// Show message if no data
if (!await checkSunbizDataLoaded()) {
  showNotification('Sunbiz data is being loaded, check back later');
}
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Before Sunbiz Data Load (MUST COMPLETE)
- [ ] **P0-1**: Create missing Sunbiz indexes (2-3 hrs)
- [ ] **P0-2**: Create sunbiz_officers table (1 hr)
- [ ] **P0-3**: Fix ActiveCompaniesSection (2-3 hrs)
- [ ] **P0-4**: Create autocomplete RPC (4-5 hrs)
- [ ] **TOTAL**: ~10-12 hours

### Week 1 (High Impact)
- [ ] **P1-1**: Create unified property data RPC (5-6 hrs)
- [ ] **P1-2**: Create pre-computed matching table (20-30 hrs background job)
- [ ] **P1-3**: Implement adaptive field selection (6-8 hrs)
- [ ] **P1-4**: Implement batch API endpoint (4-6 hrs)
- [ ] **TOTAL**: ~15-20 hours

### Week 2 (Medium Impact)
- [ ] **P2-1**: Add database query caching (5-7 hrs)
- [ ] **P2-2**: Name normalization (3-4 hrs)
- [ ] **P2-3**: Frontend result caching (2-3 hrs)
- [ ] **TOTAL**: ~10-14 hours

### Week 3+ (Nice to Have)
- [ ] **P3-1**: Cursor-based pagination (4-5 hrs)
- [ ] **P3-2**: Health checks (1-2 hrs)

---

## 📊 EXPECTED PERFORMANCE IMPROVEMENTS

| Component | Current | After P0 | After P1 | Total Improvement |
|-----------|---------|----------|----------|-------------------|
| Autocomplete | 800-1500ms | 100-200ms | - | **5-15x faster** |
| Property Search | 2000-4000ms | 1000-2000ms | 300-600ms | **7-13x faster** |
| Property Detail | 3000-6000ms | 2000-3000ms | 400-800ms | **4-15x faster** |
| Sunbiz Tab | 5000-10000ms | 500-1000ms | 100-300ms | **17-100x faster** |
| MiniCard Batch (100) | 8500ms | - | 400-600ms | **14-21x faster** |

**Overall System Performance**: **10-20x faster** after all optimizations

---

## 🚨 CRITICAL WARNINGS

1. **DO NOT** load Sunbiz data before P0 optimizations complete
   - System will timeout or take 30-60 seconds per query
   - User experience will be terrible

2. **RUN** index creation with `CONCURRENTLY` to avoid table locks
   - Non-concurrent creates lock table during creation
   - Service downtime during index creation

3. **TEST** pre-computed matching table on staging first
   - 20-30 hour runtime for full dataset
   - Verify matching algorithm accuracy before production

4. **MONITOR** Supabase connection pool limits
   - Batch operations can exhaust connections
   - Configure pool size appropriately

---

## 📈 SUCCESS METRICS

Track these metrics to measure optimization success:

1. **Page Load Times**:
   - Property Search: Target <500ms
   - Property Detail: Target <1s
   - Sunbiz Tab: Target <500ms

2. **API Request Counts**:
   - Autocomplete: 4 queries → 1 RPC
   - Property Detail: 3-4 queries → 1 RPC
   - Batch Loading: N queries → 1 batch

3. **Database Query Performance**:
   - Index scans vs table scans (aim for 100% index scans)
   - Query execution time <100ms for 95th percentile

4. **User Experience**:
   - Time to interactive <2s
   - Scroll performance 60 FPS
   - Cache hit rate >80%

---

**Generated by**: Claude Code Audit System
**Next Review**: After P0 implementation complete
