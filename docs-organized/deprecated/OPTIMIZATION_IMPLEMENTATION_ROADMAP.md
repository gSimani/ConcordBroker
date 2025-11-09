# 🗺️ SUPABASE OPTIMIZATION - METHODICAL IMPLEMENTATION ROADMAP
**ConcordBroker - Step-by-Step Implementation Guide**

**Generated**: 2025-10-29
**Approach**: Foundation First → Quick Wins → Advanced Features
**Total Time**: 4-6 weeks (working methodically with testing between phases)

---

## 🎯 GUIDING PRINCIPLES

1. **Foundation First**: Database optimization before frontend changes
2. **Risk Mitigation**: Test after each phase, rollback plan for each change
3. **Measure Everything**: Baseline → Implement → Measure → Verify
4. **No Breaking Changes**: System stays functional throughout
5. **Quick Wins Early**: Show value within first week

---

## 📊 PHASE 0: PREPARATION & BASELINE (Day 1 - 4 hours)

**Goal**: Establish current performance metrics and create safety nets

### Step 0.1: Capture Current Performance Baseline (1 hour)

**Create Baseline Test Script**:

```bash
# File: test-performance-baseline.js
# Run this to establish current metrics

node scripts/test-performance-baseline.js > baseline-results.json
```

**Create**: `scripts/test-performance-baseline.js`

```javascript
const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

async function measureQuery(name, queryFn) {
  const start = Date.now();
  try {
    await queryFn();
    const duration = Date.now() - start;
    console.log(`✅ ${name}: ${duration}ms`);
    return { name, duration, success: true };
  } catch (error) {
    console.log(`❌ ${name}: FAILED - ${error.message}`);
    return { name, duration: null, success: false, error: error.message };
  }
}

async function runBaseline() {
  console.log('🔍 Running Performance Baseline Tests\n');

  const results = {};

  // Test 1: Autocomplete (4 parallel queries - current implementation)
  results.autocomplete = await measureQuery('Autocomplete (4 queries)', async () => {
    await Promise.all([
      supabase.from('florida_parcels').select('parcel_id,phy_addr1,phy_city,owner_name').ilike('phy_addr1', 'main%').limit(5),
      supabase.from('florida_parcels').select('parcel_id,phy_addr1,phy_city,owner_name').ilike('owner_name', 'main%').limit(5),
      supabase.from('florida_parcels').select('parcel_id,phy_addr1,phy_city,owner_name').ilike('phy_city', 'main%').limit(5),
      supabase.from('florida_parcels').select('parcel_id,phy_addr1,phy_city,owner_name').eq('county', 'BROWARD').limit(5)
    ]);
  });

  // Test 2: Property Search (single county, no filters)
  results.propertySearch = await measureQuery('Property Search (county filter)', async () => {
    await supabase
      .from('florida_parcels')
      .select('*')
      .eq('county', 'BROWARD')
      .eq('year', 2025)
      .limit(100);
  });

  // Test 3: Property Detail (single property)
  results.propertyDetail = await measureQuery('Property Detail (single parcel)', async () => {
    await supabase
      .from('florida_parcels')
      .select('*')
      .eq('parcel_id', '0642100101234')
      .eq('county', 'BROWARD')
      .single();
  });

  // Test 4: Sales History (single property)
  results.salesHistory = await measureQuery('Sales History (single parcel)', async () => {
    await supabase
      .from('property_sales_history')
      .select('*')
      .eq('parcel_id', '0642100101234');
  });

  // Test 5: Owner Search (ILIKE - expensive)
  results.ownerSearch = await measureQuery('Owner Search (ILIKE)', async () => {
    await supabase
      .from('florida_parcels')
      .select('parcel_id,phy_addr1,owner_name')
      .ilike('owner_name', '%SMITH%')
      .limit(50);
  });

  // Test 6: Address Search (ILIKE - expensive)
  results.addressSearch = await measureQuery('Address Search (ILIKE)', async () => {
    await supabase
      .from('florida_parcels')
      .select('parcel_id,phy_addr1,phy_city')
      .ilike('phy_addr1', '%MAIN%')
      .limit(50);
  });

  console.log('\n📊 BASELINE RESULTS:');
  console.log(JSON.stringify(results, null, 2));

  return results;
}

runBaseline().then(() => process.exit(0)).catch(console.error);
```

**Run Baseline**:
```bash
cd C:\Users\gsima\Documents\MyProject\ConcordBroker
node scripts/test-performance-baseline.js
```

**Save Output** to `BASELINE_PERFORMANCE.json`

---

### Step 0.2: Create Database Backup & Rollback Plan (30 min)

**In Supabase Dashboard**:
1. Go to Settings → Database
2. Click "Create Backup" → Name: "pre-optimization-backup"
3. Download backup locally as safety net

**Document Current Indexes**:
```sql
-- Save current index state
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('florida_parcels', 'sunbiz_corporate', 'sunbiz_fictitious', 'property_sales_history')
ORDER BY tablename, indexname;
```

Save output to `EXISTING_INDEXES.txt`

---

### Step 0.3: Set Up Monitoring Dashboard (1 hour)

**Create Simple Performance Monitor**:

```sql
-- Create performance monitoring view
CREATE OR REPLACE VIEW v_query_performance AS
SELECT
  query,
  calls,
  total_time,
  mean_time,
  max_time,
  min_time
FROM pg_stat_statements
WHERE query LIKE '%florida_parcels%'
   OR query LIKE '%sunbiz%'
ORDER BY mean_time DESC
LIMIT 20;

-- Enable pg_stat_statements if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

**Check Current Slow Queries**:
```sql
SELECT * FROM v_query_performance;
```

---

### Step 0.4: Create Git Branch & Commit Current State (30 min)

```bash
# Create optimization branch
git checkout -b feature/database-optimization

# Commit baseline results
git add BASELINE_PERFORMANCE.json EXISTING_INDEXES.txt
git commit -m "feat: add performance baseline before optimization"
git push origin feature/database-optimization
```

---

## 🗄️ PHASE 1: DATABASE FOUNDATION (Week 1 - Days 2-3, ~8 hours)

**Goal**: Optimize database layer FIRST before touching any frontend code

**Why First?**: Database is the bottleneck. Fixing it provides immediate benefits to ALL queries, even with current frontend code.

---

### Step 1.1: Create Critical Indexes for florida_parcels (2 hours)

**Priority**: 🔴 CRITICAL
**Risk**: LOW (indexes are additive, don't break existing queries)
**Impact**: 5-50x faster queries

**SQL to Run**:
```sql
-- =====================================================
-- PHASE 1.1: FLORIDA PARCELS INDEXES
-- Time: ~30-45 minutes with CONCURRENTLY
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Index 1: County + Year (most common filter)
CREATE INDEX CONCURRENTLY idx_fp_county_year
  ON florida_parcels(county, year)
  WHERE year = 2025;

-- Index 2: Parcel ID (unique lookups)
CREATE INDEX CONCURRENTLY idx_fp_parcel_id
  ON florida_parcels(parcel_id)
  WHERE parcel_id IS NOT NULL;

-- Index 3: Address search (prefix matching)
CREATE INDEX CONCURRENTLY idx_fp_address_prefix
  ON florida_parcels(LEFT(phy_addr1, 10))
  WHERE phy_addr1 IS NOT NULL;

-- Index 4: Address fuzzy search (trigram)
CREATE INDEX CONCURRENTLY idx_fp_address_trgm
  ON florida_parcels USING gist(phy_addr1 gist_trgm_ops);

-- Index 5: Owner name exact
CREATE INDEX CONCURRENTLY idx_fp_owner_name
  ON florida_parcels(owner_name)
  WHERE owner_name IS NOT NULL;

-- Index 6: Owner name fuzzy (trigram)
CREATE INDEX CONCURRENTLY idx_fp_owner_trgm
  ON florida_parcels USING gist(owner_name gist_trgm_ops);

-- Index 7: City lookup
CREATE INDEX CONCURRENTLY idx_fp_city
  ON florida_parcels(phy_city)
  WHERE phy_city IS NOT NULL;

-- Index 8: Value range queries
CREATE INDEX CONCURRENTLY idx_fp_just_value
  ON florida_parcels(just_value)
  WHERE just_value IS NOT NULL;

-- Index 9: Year built range queries
CREATE INDEX CONCURRENTLY idx_fp_year_built
  ON florida_parcels(year_built)
  WHERE year_built IS NOT NULL;

-- Index 10: Property use filtering
CREATE INDEX CONCURRENTLY idx_fp_property_use
  ON florida_parcels(property_use)
  WHERE property_use IS NOT NULL;
```

**Verify Indexes Created**:
```sql
SELECT
  indexname,
  indexdef,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
WHERE tablename = 'florida_parcels'
  AND indexname LIKE 'idx_fp_%'
ORDER BY indexname;
```

**Expected**: 10 new indexes, total ~500-800 MB

**Test Impact**:
```bash
# Re-run baseline tests
node scripts/test-performance-baseline.js > after-phase1.1-results.json

# Compare
node scripts/compare-performance.js baseline-results.json after-phase1.1-results.json
```

**Rollback Plan** (if needed):
```sql
-- Drop all new indexes
DROP INDEX CONCURRENTLY IF EXISTS idx_fp_county_year;
DROP INDEX CONCURRENTLY IF EXISTS idx_fp_parcel_id;
-- ... (repeat for all 10)
```

---

### Step 1.2: Optimize property_sales_history Table (1 hour)

**SQL to Run**:
```sql
-- =====================================================
-- PHASE 1.2: SALES HISTORY INDEXES
-- Time: ~10-15 minutes
-- =====================================================

-- Index 1: Parcel lookup (most common)
CREATE INDEX CONCURRENTLY idx_sales_parcel_date
  ON property_sales_history(parcel_id, sale_date DESC)
  WHERE sale_date IS NOT NULL;

-- Index 2: Sale date range queries
CREATE INDEX CONCURRENTLY idx_sales_date
  ON property_sales_history(sale_date DESC)
  WHERE sale_date IS NOT NULL;

-- Index 3: Sale price filtering
CREATE INDEX CONCURRENTLY idx_sales_price
  ON property_sales_history(sale_price)
  WHERE sale_price IS NOT NULL;

-- Verify
SELECT
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
WHERE tablename = 'property_sales_history'
  AND indexname LIKE 'idx_sales_%';
```

---

### Step 1.3: Prepare Sunbiz Tables (Even If Empty) (3 hours)

**Why Now?**: Create structure and indexes BEFORE loading data (much faster than creating after)

**Step 1.3a: Create sunbiz_officers Table**
```sql
-- =====================================================
-- PHASE 1.3a: CREATE OFFICERS TABLE
-- Time: ~5 minutes
-- =====================================================

CREATE TABLE IF NOT EXISTS sunbiz_officers (
  id BIGSERIAL PRIMARY KEY,
  doc_number VARCHAR(12) NOT NULL,
  officer_name VARCHAR(200) NOT NULL,
  officer_title VARCHAR(100),
  officer_address TEXT,
  filing_date DATE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(doc_number, officer_name, officer_title),
  FOREIGN KEY (doc_number) REFERENCES sunbiz_corporate(doc_number) ON DELETE CASCADE
);

-- Indexes (create now, before data load)
CREATE INDEX idx_officers_doc_number ON sunbiz_officers(doc_number);
CREATE INDEX idx_officers_name ON sunbiz_officers(officer_name);
CREATE INDEX idx_officers_name_trgm ON sunbiz_officers USING gist(officer_name gist_trgm_ops);

-- RLS
ALTER TABLE sunbiz_officers ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read on officers" ON sunbiz_officers FOR SELECT USING (true);
```

**Step 1.3b: Create Sunbiz Indexes (Before Data Load)**
```sql
-- =====================================================
-- PHASE 1.3b: SUNBIZ CORPORATE INDEXES
-- Time: ~5 minutes (tables empty, indexes created instantly)
-- =====================================================

-- Address indexes (for property matching)
CREATE INDEX idx_sunbiz_prin_addr ON sunbiz_corporate(prin_addr1)
  WHERE prin_addr1 IS NOT NULL;

CREATE INDEX idx_sunbiz_mail_addr ON sunbiz_corporate(mail_addr1)
  WHERE mail_addr1 IS NOT NULL;

-- Name indexes
CREATE INDEX idx_sunbiz_entity_name ON sunbiz_corporate(entity_name);
CREATE INDEX idx_sunbiz_entity_trgm ON sunbiz_corporate USING gist(entity_name gist_trgm_ops);

-- Agent index
CREATE INDEX idx_sunbiz_agent ON sunbiz_corporate(registered_agent)
  WHERE registered_agent IS NOT NULL;
CREATE INDEX idx_sunbiz_agent_trgm ON sunbiz_corporate USING gist(registered_agent gist_trgm_ops);

-- Status + Date composite
CREATE INDEX idx_sunbiz_status_date ON sunbiz_corporate(status, filing_date DESC)
  WHERE status = 'ACTIVE';

-- Doc number (for joins)
CREATE INDEX idx_sunbiz_doc_number ON sunbiz_corporate(doc_number);

-- =====================================================
-- PHASE 1.3c: SUNBIZ FICTITIOUS INDEXES
-- =====================================================

CREATE INDEX idx_fict_name ON sunbiz_fictitious(name);
CREATE INDEX idx_fict_name_trgm ON sunbiz_fictitious USING gist(name gist_trgm_ops);
CREATE INDEX idx_fict_owner ON sunbiz_fictitious(owner_name);
CREATE INDEX idx_fict_owner_trgm ON sunbiz_fictitious USING gist(owner_name gist_trgm_ops);
CREATE INDEX idx_fict_name_gin ON sunbiz_fictitious USING gin(to_tsvector('english', name));
```

**Verify All Sunbiz Indexes**:
```sql
SELECT tablename, indexname
FROM pg_indexes
WHERE tablename LIKE 'sunbiz%'
ORDER BY tablename, indexname;
```

**Expected**: ~15 indexes across sunbiz tables

---

### Step 1.4: Create Analysis & Monitoring Functions (2 hours)

**Create Query Performance Monitoring**:
```sql
-- =====================================================
-- PHASE 1.4: MONITORING FUNCTIONS
-- =====================================================

-- Function 1: Get slow queries
CREATE OR REPLACE FUNCTION get_slow_queries(min_time_ms INT DEFAULT 1000)
RETURNS TABLE (
  query TEXT,
  calls BIGINT,
  total_time_ms NUMERIC,
  mean_time_ms NUMERIC,
  max_time_ms NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    LEFT(pg_stat_statements.query, 200) as query,
    pg_stat_statements.calls,
    ROUND(pg_stat_statements.total_exec_time::numeric, 2) as total_time_ms,
    ROUND(pg_stat_statements.mean_exec_time::numeric, 2) as mean_time_ms,
    ROUND(pg_stat_statements.max_exec_time::numeric, 2) as max_time_ms
  FROM pg_stat_statements
  WHERE mean_exec_time > min_time_ms
  ORDER BY mean_exec_time DESC
  LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Get table statistics
CREATE OR REPLACE FUNCTION get_table_stats()
RETURNS TABLE (
  table_name TEXT,
  row_count BIGINT,
  table_size TEXT,
  index_size TEXT,
  total_size TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    relname::TEXT as table_name,
    n_live_tup as row_count,
    pg_size_pretty(pg_total_relation_size(relid) - pg_indexes_size(relid)) as table_size,
    pg_size_pretty(pg_indexes_size(relid)) as index_size,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size
  FROM pg_stat_user_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(relid) DESC;
END;
$$ LANGUAGE plpgsql;

-- Function 3: Index usage stats
CREATE OR REPLACE FUNCTION get_index_usage()
RETURNS TABLE (
  table_name TEXT,
  index_name TEXT,
  index_scans BIGINT,
  rows_read BIGINT,
  index_size TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    schemaname || '.' || tablename as table_name,
    indexrelname as index_name,
    idx_scan as index_scans,
    idx_tup_read as rows_read,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
  FROM pg_stat_user_indexes
  WHERE schemaname = 'public'
  ORDER BY idx_scan DESC;
END;
$$ LANGUAGE plpgsql;
```

**Test Monitoring**:
```sql
-- Check slow queries
SELECT * FROM get_slow_queries(100);

-- Check table stats
SELECT * FROM get_table_stats();

-- Check index usage
SELECT * FROM get_index_usage();
```

---

### Phase 1 Checkpoint: Measure Impact (1 hour)

**Run Performance Tests**:
```bash
node scripts/test-performance-baseline.js > after-phase1-results.json
```

**Compare Results**:
```bash
# Expected improvements:
# - County searches: 2000ms → 50ms (40x faster)
# - Address ILIKE: 3000ms → 200ms (15x faster)
# - Owner ILIKE: 3000ms → 300ms (10x faster)
```

**Commit Progress**:
```bash
git add -A
git commit -m "feat: Phase 1 complete - database indexes optimized"
git push origin feature/database-optimization
```

**Decision Point**:
- ✅ If Phase 1 tests show 5-20x improvement → Proceed to Phase 2
- ⚠️ If tests show <2x improvement → Review explain plans, investigate missing indexes
- ❌ If tests fail or performance degrades → Rollback indexes, investigate

---

## 🔌 PHASE 2: BACKEND RPC FUNCTIONS (Week 1-2 - Days 4-5, ~10 hours)

**Goal**: Replace multiple queries with single RPC calls (N+1 problem elimination)

**Why Now?**: Database is optimized, now we reduce round-trips

---

### Step 2.1: Create Autocomplete RPC (2 hours)

**File to Create**: `supabase/migrations/20250129_autocomplete_rpc.sql`

```sql
-- =====================================================
-- PHASE 2.1: UNIFIED AUTOCOMPLETE RPC
-- Replaces 4 parallel queries with 1 optimized query
-- =====================================================

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
  match_type TEXT,
  match_score INT
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  RETURN QUERY

  -- Priority 1: Exact address match (highest score)
  SELECT
    fp.parcel_id::TEXT,
    fp.phy_addr1::TEXT,
    fp.phy_city::TEXT,
    fp.owner_name::TEXT,
    fp.just_value,
    fp.property_use::TEXT,
    'address_exact'::TEXT as match_type,
    100 as match_score
  FROM florida_parcels fp
  WHERE (p_county IS NULL OR fp.county = p_county)
    AND fp.phy_addr1 ILIKE p_query
    AND fp.year = 2025
  LIMIT 5

  UNION ALL

  -- Priority 2: Address prefix match
  SELECT
    fp.parcel_id::TEXT,
    fp.phy_addr1::TEXT,
    fp.phy_city::TEXT,
    fp.owner_name::TEXT,
    fp.just_value,
    fp.property_use::TEXT,
    'address_prefix'::TEXT as match_type,
    90 as match_score
  FROM florida_parcels fp
  WHERE (p_county IS NULL OR fp.county = p_county)
    AND fp.phy_addr1 ILIKE p_query || '%'
    AND fp.year = 2025
  LIMIT 7

  UNION ALL

  -- Priority 3: Owner name match
  SELECT
    fp.parcel_id::TEXT,
    fp.phy_addr1::TEXT,
    fp.phy_city::TEXT,
    fp.owner_name::TEXT,
    fp.just_value,
    fp.property_use::TEXT,
    'owner'::TEXT as match_type,
    80 as match_score
  FROM florida_parcels fp
  WHERE (p_county IS NULL OR fp.county = p_county)
    AND fp.owner_name ILIKE p_query || '%'
    AND fp.year = 2025
  LIMIT 5

  UNION ALL

  -- Priority 4: City match
  SELECT
    fp.parcel_id::TEXT,
    fp.phy_addr1::TEXT,
    fp.phy_city::TEXT,
    fp.owner_name::TEXT,
    fp.just_value,
    fp.property_use::TEXT,
    'city'::TEXT as match_type,
    70 as match_score
  FROM florida_parcels fp
  WHERE (p_county IS NULL OR fp.county = p_county)
    AND fp.phy_city ILIKE p_query || '%'
    AND fp.year = 2025
  LIMIT 3

  ORDER BY match_score DESC, phy_addr1
  LIMIT p_limit;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION search_property_autocomplete TO anon, authenticated;

-- Test the function
SELECT * FROM search_property_autocomplete('main', 'BROWARD', 10);
```

**Deploy**:
```bash
# Apply migration in Supabase
psql -h your-supabase-host -U postgres -f supabase/migrations/20250129_autocomplete_rpc.sql
```

**Test Performance**:
```sql
-- Measure RPC performance
EXPLAIN ANALYZE
SELECT * FROM search_property_autocomplete('main', 'BROWARD', 20);

-- Expected: <100ms execution time
```

---

### Step 2.2: Create Unified Property Data RPC (3 hours)

**File**: `supabase/migrations/20250129_property_complete_rpc.sql`

```sql
-- =====================================================
-- PHASE 2.2: UNIFIED PROPERTY DATA RPC
-- Replaces 3-4 sequential queries with 1 call
-- =====================================================

CREATE OR REPLACE FUNCTION get_property_complete(
  p_parcel_id TEXT,
  p_county TEXT
)
RETURNS JSON
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'property', (
      SELECT row_to_json(fp.*)
      FROM florida_parcels fp
      WHERE fp.parcel_id = p_parcel_id
        AND fp.county = p_county
        AND fp.year = 2025
    ),
    'sales_history', (
      SELECT COALESCE(json_agg(json_build_object(
        'sale_date', psh.sale_date,
        'sale_price', psh.sale_price,
        'sale_type', psh.sale_type,
        'qualified_sale', psh.qualified_sale,
        'book_page', psh.book_page
      ) ORDER BY psh.sale_date DESC), '[]'::json)
      FROM property_sales_history psh
      WHERE psh.parcel_id = p_parcel_id
    ),
    'tax_certificates', (
      SELECT COALESCE(json_agg(json_build_object(
        'certificate_number', tc.certificate_number,
        'face_amount', tc.face_amount,
        'tax_year', tc.tax_year
      )), '[]'::json)
      FROM tax_certificates tc
      WHERE tc.parcel_id = p_parcel_id
    ),
    'nav_assessments', (
      SELECT COALESCE(json_agg(json_build_object(
        'assessment_year', na.assessment_year,
        'district_name', na.district_name,
        'total_assessment', na.total_assessment
      )), '[]'::json)
      FROM nav_assessments na
      WHERE na.parcel_id = p_parcel_id
    )
  ) INTO result;

  RETURN result;
END;
$$;

GRANT EXECUTE ON FUNCTION get_property_complete TO anon, authenticated;

-- Test
SELECT get_property_complete('0642100101234', 'BROWARD');
```

---

### Step 2.3: Create Batch Property Lookup RPC (2 hours)

**File**: `supabase/migrations/20250129_batch_properties_rpc.sql`

```sql
-- =====================================================
-- PHASE 2.3: BATCH PROPERTY LOOKUP RPC
-- Fetch multiple properties in one call
-- =====================================================

CREATE OR REPLACE FUNCTION get_properties_batch(
  p_parcel_ids TEXT[],
  p_include_sales BOOLEAN DEFAULT false
)
RETURNS JSON
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  result JSON;
BEGIN
  IF p_include_sales THEN
    -- Include sales data
    SELECT json_agg(
      json_build_object(
        'property', row_to_json(fp.*),
        'sales', (
          SELECT COALESCE(json_agg(json_build_object(
            'sale_date', psh.sale_date,
            'sale_price', psh.sale_price
          )), '[]'::json)
          FROM property_sales_history psh
          WHERE psh.parcel_id = fp.parcel_id
        )
      )
    )
    INTO result
    FROM florida_parcels fp
    WHERE fp.parcel_id = ANY(p_parcel_ids)
      AND fp.year = 2025;
  ELSE
    -- Properties only
    SELECT json_agg(row_to_json(fp.*))
    INTO result
    FROM florida_parcels fp
    WHERE fp.parcel_id = ANY(p_parcel_ids)
      AND fp.year = 2025;
  END IF;

  RETURN COALESCE(result, '[]'::json);
END;
$$;

GRANT EXECUTE ON FUNCTION get_properties_batch TO anon, authenticated;

-- Test
SELECT get_properties_batch(
  ARRAY['0642100101234', '0642100101235'],
  true
);
```

---

### Phase 2 Checkpoint: Test RPC Functions (2 hours)

**Create RPC Test Suite**:

```javascript
// scripts/test-rpc-functions.js

const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

async function testRPCs() {
  console.log('🧪 Testing RPC Functions\n');

  // Test 1: Autocomplete RPC
  console.log('Test 1: Autocomplete RPC');
  const start1 = Date.now();
  const { data: autocomplete, error: error1 } = await supabase.rpc('search_property_autocomplete', {
    p_query: 'main',
    p_county: 'BROWARD',
    p_limit: 20
  });
  console.log(`✅ Time: ${Date.now() - start1}ms, Results: ${autocomplete?.length || 0}`);
  if (error1) console.error('❌ Error:', error1);

  // Test 2: Property Complete RPC
  console.log('\nTest 2: Property Complete RPC');
  const start2 = Date.now();
  const { data: complete, error: error2 } = await supabase.rpc('get_property_complete', {
    p_parcel_id: '0642100101234',
    p_county: 'BROWARD'
  });
  console.log(`✅ Time: ${Date.now() - start2}ms`);
  if (error2) console.error('❌ Error:', error2);

  // Test 3: Batch Properties RPC
  console.log('\nTest 3: Batch Properties RPC');
  const start3 = Date.now();
  const { data: batch, error: error3 } = await supabase.rpc('get_properties_batch', {
    p_parcel_ids: ['0642100101234', '0642100101235', '0642100101236'],
    p_include_sales: true
  });
  console.log(`✅ Time: ${Date.now() - start3}ms, Properties: ${batch?.length || 0}`);
  if (error3) console.error('❌ Error:', error3);
}

testRPCs().then(() => process.exit(0)).catch(console.error);
```

**Run Tests**:
```bash
node scripts/test-rpc-functions.js
```

**Expected Results**:
- Autocomplete: <200ms
- Property Complete: <400ms
- Batch (3 properties): <300ms

**Commit Progress**:
```bash
git add supabase/migrations/*.sql scripts/test-rpc-functions.js
git commit -m "feat: Phase 2 complete - RPC functions created and tested"
git push
```

---

## 🎨 PHASE 3: FRONTEND INTEGRATION (Week 2 - Days 6-8, ~12 hours)

**Goal**: Update frontend to use new RPC functions

**Why Now?**: Database and RPC functions are ready, now we integrate

---

### Step 3.1: Update Autocomplete Hook to Use RPC (3 hours)

**Backup Original File**:
```bash
cp apps/web/src/hooks/usePropertyAutocomplete.ts apps/web/src/hooks/usePropertyAutocomplete.ts.backup
```

**Update**: `apps/web/src/hooks/usePropertyAutocomplete.ts`

```typescript
// NEW IMPLEMENTATION using RPC
import { useState, useEffect, useMemo } from 'react';
import { supabase } from '@/lib/supabase';

interface AutocompleteResult {
  parcelId: string;
  address: string;
  city: string;
  owner: string;
  value: number;
  propertyUse: string;
  matchType: string;
  matchScore: number;
  icon: string;
}

export function usePropertyAutocomplete(
  query: string,
  county?: string,
  debounceMs: number = 300
) {
  const [suggestions, setSuggestions] = useState<AutocompleteResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounce query
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedQuery(query), debounceMs);
    return () => clearTimeout(handler);
  }, [query, debounceMs]);

  // Fetch suggestions using RPC
  useEffect(() => {
    if (!debouncedQuery || debouncedQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    const fetchSuggestions = async () => {
      setLoading(true);
      setError(null);

      try {
        const { data, error: rpcError } = await supabase.rpc('search_property_autocomplete', {
          p_query: debouncedQuery,
          p_county: county || null,
          p_limit: 20
        });

        if (rpcError) throw rpcError;

        // Transform to UI format
        const results: AutocompleteResult[] = (data || []).map((item: any) => ({
          parcelId: item.parcel_id,
          address: item.phy_addr1,
          city: item.phy_city,
          owner: item.owner_name,
          value: item.just_value,
          propertyUse: item.property_use,
          matchType: item.match_type,
          matchScore: item.match_score,
          icon: getIconForMatchType(item.match_type)
        }));

        setSuggestions(results);
      } catch (err) {
        console.error('Autocomplete error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSuggestions();
  }, [debouncedQuery, county]);

  return { suggestions, loading, error };
}

function getIconForMatchType(matchType: string): string {
  const iconMap: Record<string, string> = {
    'address_exact': 'MapPinned',
    'address_prefix': 'MapPin',
    'owner': 'User',
    'city': 'Building'
  };
  return iconMap[matchType] || 'Search';
}
```

**Test**:
1. Start dev server: `npm run dev`
2. Open http://localhost:5191/properties
3. Type "main" in search box
4. Open DevTools → Network tab
5. Verify: **1 RPC call** instead of **4 parallel queries**

**Measure Improvement**:
```
BEFORE: 4 queries, 800-1500ms total
AFTER: 1 RPC call, 100-200ms
IMPROVEMENT: 5-15x faster
```

---

### Step 3.2: Update Property Data Hook to Use RPC (4 hours)

**Backup**:
```bash
cp apps/web/src/hooks/usePropertyData.ts apps/web/src/hooks/usePropertyData.ts.backup
```

**Update**: `apps/web/src/hooks/usePropertyData.ts`

```typescript
// NEW IMPLEMENTATION using get_property_complete RPC

export function usePropertyData(parcelId: string, county: string) {
  const [data, setData] = useState<PropertyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelId || !county) {
      setData(null);
      setLoading(false);
      return;
    }

    const fetchPropertyData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Single RPC call replaces 3-4 sequential queries
        const { data: result, error: rpcError } = await supabase.rpc('get_property_complete', {
          p_parcel_id: parcelId,
          p_county: county
        });

        if (rpcError) throw rpcError;

        // Parse JSON result
        const parsed = typeof result === 'string' ? JSON.parse(result) : result;

        setData({
          property: parsed.property,
          salesHistory: parsed.sales_history || [],
          taxCertificates: parsed.tax_certificates || [],
          navAssessments: parsed.nav_assessments || []
        });
      } catch (err) {
        console.error('Property data fetch error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchPropertyData();
  }, [parcelId, county]);

  return { data, loading, error };
}
```

---

### Step 3.3: Create Batch Property Hook (2 hours)

**New File**: `apps/web/src/hooks/useBatchProperties.ts`

```typescript
import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

interface BatchPropertyOptions {
  includeSales?: boolean;
}

export function useBatchProperties(
  parcelIds: string[],
  options: BatchPropertyOptions = {}
) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelIds || parcelIds.length === 0) {
      setData([]);
      return;
    }

    const fetchBatch = async () => {
      setLoading(true);
      setError(null);

      try {
        // Batch into groups of 100 (Supabase limit)
        const batches = chunkArray(parcelIds, 100);

        const results = await Promise.all(
          batches.map(batch =>
            supabase.rpc('get_properties_batch', {
              p_parcel_ids: batch,
              p_include_sales: options.includeSales || false
            })
          )
        );

        // Combine results
        const allData = results.flatMap(r => {
          const parsed = typeof r.data === 'string' ? JSON.parse(r.data) : r.data;
          return parsed || [];
        });

        setData(allData);
      } catch (err) {
        console.error('Batch fetch error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchBatch();
  }, [JSON.stringify(parcelIds), options.includeSales]);

  return { data, loading, error };
}

function chunkArray<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}
```

---

### Step 3.4: Update MiniPropertyCard to Use Batch Loading (3 hours)

**Update**: `apps/web/src/components/property/VirtualizedPropertyList.tsx`

```typescript
// Use batch hook for all visible properties
import { useBatchProperties } from '@/hooks/useBatchProperties';

export function VirtualizedPropertyList({ properties }) {
  const visibleParcelIds = properties.map(p => p.parcel_id);

  // Batch fetch all properties at once
  const { data: batchData, loading } = useBatchProperties(visibleParcelIds, {
    includeSales: true
  });

  // Create lookup map for fast access
  const propertyMap = useMemo(() => {
    const map = new Map();
    batchData.forEach(item => {
      map.set(item.property.parcel_id, item);
    });
    return map;
  }, [batchData]);

  return (
    <div>
      {properties.map(property => {
        const enrichedData = propertyMap.get(property.parcel_id) || property;
        return (
          <MiniPropertyCard
            key={property.parcel_id}
            data={enrichedData}
          />
        );
      })}
    </div>
  );
}
```

---

### Phase 3 Checkpoint: Test Frontend Integration (2 hours)

**Manual Testing Checklist**:
- [ ] Autocomplete works (type "main")
- [ ] Property detail page loads (click a property)
- [ ] Sales history displays
- [ ] Network tab shows RPC calls instead of multiple queries
- [ ] No console errors
- [ ] Performance feels faster

**Performance Test**:
```bash
# Run frontend performance test
npm run test:performance
```

**Commit Progress**:
```bash
git add apps/web/src/hooks apps/web/src/components
git commit -m "feat: Phase 3 complete - frontend using RPC functions"
git push
```

---

## 🚀 PHASE 4: SUNBIZ OPTIMIZATION (Week 3 - Days 9-12, ~16 hours)

**Goal**: Optimize Sunbiz matching before data load

**Why Now?**: Core system optimized, now prepare for Sunbiz data

---

### Step 4.1: Create Pre-Computed Matching Table Structure (2 hours)

**File**: `supabase/migrations/20250130_sunbiz_property_matches.sql`

```sql
-- =====================================================
-- PHASE 4.1: SUNBIZ-PROPERTY MATCHING TABLE
-- Pre-compute matches for instant lookups
-- =====================================================

CREATE TABLE IF NOT EXISTS sunbiz_property_matches (
  id BIGSERIAL PRIMARY KEY,
  parcel_id VARCHAR(20) NOT NULL,
  sunbiz_doc_number VARCHAR(12) NOT NULL,
  match_type VARCHAR(50) NOT NULL,
  match_confidence DECIMAL(3,2) NOT NULL CHECK (match_confidence BETWEEN 0 AND 1),
  matched_date TIMESTAMP DEFAULT NOW(),
  last_verified TIMESTAMP,
  is_verified BOOLEAN DEFAULT FALSE,
  verified_by VARCHAR(100),
  notes TEXT,

  UNIQUE(parcel_id, sunbiz_doc_number),
  FOREIGN KEY (parcel_id) REFERENCES florida_parcels(parcel_id) ON DELETE CASCADE,
  FOREIGN KEY (sunbiz_doc_number) REFERENCES sunbiz_corporate(doc_number) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_spm_parcel ON sunbiz_property_matches(parcel_id);
CREATE INDEX idx_spm_sunbiz ON sunbiz_property_matches(sunbiz_doc_number);
CREATE INDEX idx_spm_confidence ON sunbiz_property_matches(match_confidence DESC);
CREATE INDEX idx_spm_match_type ON sunbiz_property_matches(match_type);
CREATE INDEX idx_spm_verified ON sunbiz_property_matches(is_verified) WHERE is_verified = true;

-- RLS
ALTER TABLE sunbiz_property_matches ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read on matches" ON sunbiz_property_matches FOR SELECT USING (true);
```

---

### Step 4.2: Create Matching Functions (6 hours)

**File**: `supabase/migrations/20250130_matching_functions.sql`

```sql
-- =====================================================
-- PHASE 4.2: SUNBIZ MATCHING FUNCTIONS
-- =====================================================

-- Function 1: Populate exact address matches
CREATE OR REPLACE FUNCTION populate_address_matches()
RETURNS TABLE (matched_count BIGINT) AS $$
BEGIN
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

  GET DIAGNOSTICS matched_count = ROW_COUNT;
  RETURN QUERY SELECT matched_count;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Populate owner name matches
CREATE OR REPLACE FUNCTION populate_owner_matches()
RETURNS TABLE (matched_count BIGINT) AS $$
BEGIN
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

  GET DIAGNOSTICS matched_count = ROW_COUNT;
  RETURN QUERY SELECT matched_count;
END;
$$ LANGUAGE plpgsql;

-- Function 3: Populate fuzzy matches
CREATE OR REPLACE FUNCTION populate_fuzzy_matches(similarity_threshold DECIMAL DEFAULT 0.6)
RETURNS TABLE (matched_count BIGINT) AS $$
BEGIN
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
    AND similarity(fp.owner_name, sc.entity_name) > similarity_threshold
    AND NOT EXISTS (
      -- Don't create fuzzy match if exact match exists
      SELECT 1 FROM sunbiz_property_matches spm
      WHERE spm.parcel_id = fp.parcel_id
        AND spm.sunbiz_doc_number = sc.doc_number
    )
  LIMIT 1000000; -- Safety limit

  GET DIAGNOSTICS matched_count = ROW_COUNT;
  RETURN QUERY SELECT matched_count;
END;
$$ LANGUAGE plpgsql;

-- Function 4: Get matches for a parcel (frontend use)
CREATE OR REPLACE FUNCTION get_sunbiz_matches(p_parcel_id TEXT)
RETURNS JSON AS $$
BEGIN
  RETURN (
    SELECT COALESCE(json_agg(json_build_object(
      'doc_number', sc.doc_number,
      'entity_name', sc.entity_name,
      'entity_type', sc.entity_type,
      'status', sc.status,
      'filing_date', sc.filing_date,
      'registered_agent', sc.registered_agent,
      'match_type', spm.match_type,
      'match_confidence', spm.match_confidence
    ) ORDER BY spm.match_confidence DESC), '[]'::json)
    FROM sunbiz_property_matches spm
    JOIN sunbiz_corporate sc ON sc.doc_number = spm.sunbiz_doc_number
    WHERE spm.parcel_id = p_parcel_id
      AND spm.match_confidence >= 0.6
  );
END;
$$ LANGUAGE plpgsql STABLE;

GRANT EXECUTE ON FUNCTION get_sunbiz_matches TO anon, authenticated;
```

---

### Step 4.3: Disable Auto-Fetch in Sunbiz Components (2 hours)

**Update**: `apps/web/src/components/property/tabs/SunbizTab.tsx`

```typescript
// Comment out or disable ActiveCompaniesSection
{/*
<ActiveCompaniesSection
  ownerName={ownerName}
  propertyAddress={propertyAddress}
/>
*/}

// Update useSunbizData to NOT auto-fetch
const { corporate, fictitious, events, loading, error, refetch } = useSunbizData(
  ownerName,
  propertyAddress,
  propertyCity,
  false // autoFetch = false
);

// Add manual search button
<Button onClick={() => refetch()}>
  Search Sunbiz Records
</Button>
```

---

### Step 4.4: Create Sunbiz Data Loading Script (6 hours)

**File**: `scripts/load-sunbiz-and-match.js`

```javascript
// Script to load Sunbiz data and populate matches
// Run AFTER Sunbiz data is loaded from SFTP

const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function loadAndMatch() {
  console.log('🚀 Starting Sunbiz Matching Process\n');

  // Step 1: Verify Sunbiz data loaded
  console.log('Step 1: Verify Sunbiz data...');
  const { count } = await supabase
    .from('sunbiz_corporate')
    .select('*', { count: 'exact', head: true });
  console.log(`✅ Sunbiz records: ${count}\n`);

  if (count === 0) {
    console.error('❌ No Sunbiz data found. Load data first!');
    process.exit(1);
  }

  // Step 2: Populate exact address matches
  console.log('Step 2: Populate address matches...');
  const { data: addressMatches } = await supabase.rpc('populate_address_matches');
  console.log(`✅ Address matches: ${addressMatches[0].matched_count}\n`);

  // Step 3: Populate exact owner name matches
  console.log('Step 3: Populate owner name matches...');
  const { data: ownerMatches } = await supabase.rpc('populate_owner_matches');
  console.log(`✅ Owner matches: ${ownerMatches[0].matched_count}\n`);

  // Step 4: Populate fuzzy matches (LONG RUNNING - 8-12 hours)
  console.log('Step 4: Populate fuzzy matches (this will take hours)...');
  const { data: fuzzyMatches } = await supabase.rpc('populate_fuzzy_matches', {
    similarity_threshold: 0.65
  });
  console.log(`✅ Fuzzy matches: ${fuzzyMatches[0].matched_count}\n`);

  // Step 5: Summary
  const { count: totalMatches } = await supabase
    .from('sunbiz_property_matches')
    .select('*', { count: 'exact', head: true });

  console.log('\n📊 MATCHING SUMMARY:');
  console.log(`Total matches: ${totalMatches}`);
  console.log(`Address matches: ${addressMatches[0].matched_count}`);
  console.log(`Owner matches: ${ownerMatches[0].matched_count}`);
  console.log(`Fuzzy matches: ${fuzzyMatches[0].matched_count}`);
  console.log('\n✅ Matching complete!');
}

loadAndMatch().catch(console.error);
```

---

### Phase 4 Checkpoint: Test Sunbiz (2 hours)

**Test Plan**:
1. Load sample Sunbiz data (100 records)
2. Run matching script on sample
3. Verify matches created
4. Test frontend retrieval
5. Measure performance

---

## 📊 PHASE 5: FINAL OPTIMIZATIONS (Week 4 - Days 13-15, ~10 hours)

**Goal**: Polish, caching, monitoring

---

### Step 5.1: Implement Redis Caching (4 hours)
### Step 5.2: Add Frontend Query Caching (3 hours)
### Step 5.3: Performance Monitoring Dashboard (3 hours)

---

## ✅ FINAL VERIFICATION (Day 16 - 4 hours)

**Complete System Test**:
1. Run full performance baseline
2. Compare to Phase 0 baseline
3. Verify all features working
4. Document improvements
5. Create production deploy plan

---

## 📈 EXPECTED TIMELINE SUMMARY

| Phase | Duration | Cumulative | Key Deliverable |
|-------|----------|------------|-----------------|
| Phase 0 | 4 hours | Day 1 | Baseline established |
| Phase 1 | 8 hours | Day 2-3 | Database optimized |
| Phase 2 | 10 hours | Day 4-5 | RPC functions created |
| Phase 3 | 12 hours | Day 6-8 | Frontend integrated |
| Phase 4 | 16 hours | Day 9-12 | Sunbiz optimized |
| Phase 5 | 10 hours | Day 13-15 | Final polish |
| Verification | 4 hours | Day 16 | Production ready |
| **TOTAL** | **64 hours** | **~3-4 weeks** | **10-20x faster** |

---

## 🚨 CRITICAL SUCCESS FACTORS

1. **Test After Each Phase**: Don't move forward if phase fails
2. **Keep Backups**: Database backup before each phase
3. **Monitor Performance**: Measure before/after each phase
4. **Rollback Plan**: Know how to undo each change
5. **Incremental Commits**: Git commit after each step

---

**Generated**: 2025-10-29
**Status**: Ready to Execute
**Next Action**: Begin Phase 0 - Capture Baseline
