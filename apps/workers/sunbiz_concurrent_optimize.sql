-- ============================================================
-- SUNBIZ CONCURRENT OPTIMIZATION (Safe to run during loading)
-- ============================================================

-- 1. ENABLE SEARCH EXTENSIONS (instant, no locks)
CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS unaccent SCHEMA extensions;

-- 2. CREATE INDEXES CONCURRENTLY (no table locks, slower build)
-- ============================================================

-- SUNBIZ_CORPORATE INDEXES (build without blocking inserts)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_status 
    ON sunbiz_corporate(status) 
    WHERE status IN ('ACTIVE', 'INACTIVE');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_filing_date 
    ON sunbiz_corporate(filing_date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_entity_name_trgm 
    ON sunbiz_corporate USING gin (entity_name gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_registered_agent_trgm 
    ON sunbiz_corporate USING gin (registered_agent gin_trgm_ops)
    WHERE registered_agent IS NOT NULL;

-- More indexes can be added after initial ones complete
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_prin_city 
    ON sunbiz_corporate(prin_city)
    WHERE prin_city IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_prin_zip 
    ON sunbiz_corporate(prin_zip)
    WHERE prin_zip IS NOT NULL;

-- 3. PARTIAL ANALYZE (quick statistics update)
ANALYZE sunbiz_corporate;

-- 4. TEST FUZZY SEARCH (should work even with partial data)
-- Quick smoke test
SELECT COUNT(*) as available_records FROM sunbiz_corporate;

-- Test fuzzy search (will be slow without index, fast with index)
EXPLAIN (ANALYZE, BUFFERS)
SELECT doc_number, entity_name, status
FROM sunbiz_corporate
WHERE entity_name ILIKE '%ACME%'
LIMIT 10;