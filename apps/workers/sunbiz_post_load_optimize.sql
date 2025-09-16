-- ============================================================
-- SUNBIZ POST-LOAD OPTIMIZATION SCRIPT
-- Run after data loading completes
-- ============================================================

-- 1. ENABLE SEARCH EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS unaccent SCHEMA extensions;

-- 2. CREATE HIGH-PERFORMANCE INDEXES
-- ============================================================

-- SUNBIZ_CORPORATE INDEXES
-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_status 
    ON sunbiz_corporate(status) 
    WHERE status IN ('ACTIVE', 'INACTIVE');

CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_filing_date 
    ON sunbiz_corporate(filing_date DESC);

CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_state_country 
    ON sunbiz_corporate(state_country) 
    WHERE state_country = 'FL';

-- Fuzzy text search (using pg_trgm)
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_entity_name_trgm 
    ON sunbiz_corporate USING gin (entity_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_registered_agent_trgm 
    ON sunbiz_corporate USING gin (registered_agent gin_trgm_ops)
    WHERE registered_agent IS NOT NULL;

-- Address searches
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_prin_city 
    ON sunbiz_corporate(prin_city)
    WHERE prin_city IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_prin_zip 
    ON sunbiz_corporate(prin_zip)
    WHERE prin_zip IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_status_filing 
    ON sunbiz_corporate(status, filing_date DESC);

-- SUNBIZ_FICTITIOUS INDEXES
-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_sunbiz_fictitious_status 
    ON sunbiz_fictitious(status);

CREATE INDEX IF NOT EXISTS idx_sunbiz_fictitious_filing_date 
    ON sunbiz_fictitious(filing_date DESC)
    WHERE filing_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sunbiz_fictitious_expiration_date 
    ON sunbiz_fictitious(expiration_date DESC)
    WHERE expiration_date IS NOT NULL;

-- Fuzzy text search
CREATE INDEX IF NOT EXISTS idx_sunbiz_fictitious_name_trgm 
    ON sunbiz_fictitious USING gin (name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_sunbiz_fictitious_owner_name_trgm 
    ON sunbiz_fictitious USING gin (owner_name gin_trgm_ops)
    WHERE owner_name IS NOT NULL;

-- SUNBIZ_LIENS INDEXES (if table exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_schema = 'public' 
               AND table_name = 'sunbiz_liens') THEN
        
        CREATE INDEX IF NOT EXISTS idx_sunbiz_liens_filed_date 
            ON sunbiz_liens(filed_date DESC)
            WHERE filed_date IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_sunbiz_liens_lapse_date 
            ON sunbiz_liens(lapse_date DESC)
            WHERE lapse_date IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_sunbiz_liens_type_trgm 
            ON sunbiz_liens USING gin (lien_type gin_trgm_ops)
            WHERE lien_type IS NOT NULL;
    END IF;
END $$;

-- SUNBIZ_PARTNERSHIPS INDEXES (if table exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_schema = 'public' 
               AND table_name = 'sunbiz_partnerships') THEN
        
        CREATE INDEX IF NOT EXISTS idx_sunbiz_partnerships_filed_date 
            ON sunbiz_partnerships(filed_date DESC)
            WHERE filed_date IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_sunbiz_partnerships_status 
            ON sunbiz_partnerships(status);
        
        CREATE INDEX IF NOT EXISTS idx_sunbiz_partnerships_name_trgm 
            ON sunbiz_partnerships USING gin (name gin_trgm_ops);
    END IF;
END $$;

-- 3. UPDATE TABLE STATISTICS
-- ============================================================
ANALYZE sunbiz_corporate;
ANALYZE sunbiz_fictitious;
ANALYZE sunbiz_liens;
ANALYZE sunbiz_partnerships;

-- 4. VERIFY INDEXES AND COUNTS
-- ============================================================
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public' 
    AND tablename LIKE 'sunbiz%'
ORDER BY tablename, indexname;

-- Show table sizes and row counts
SELECT 
    schemaname,
    tablename,
    n_live_tup AS row_count,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
FROM pg_stat_user_tables
WHERE schemaname = 'public' 
    AND tablename LIKE 'sunbiz%'
ORDER BY n_live_tup DESC;

-- 5. SAMPLE FUZZY SEARCH QUERIES
-- ============================================================
-- Test fuzzy entity name search (should be < 100ms with GIN index)
EXPLAIN ANALYZE
SELECT doc_number, entity_name, status, filing_date,
       similarity(entity_name, 'CONCORD BROKER') AS sim_score
FROM sunbiz_corporate
WHERE entity_name % 'CONCORD BROKER'  -- pg_trgm similarity operator
ORDER BY sim_score DESC
LIMIT 10;

-- Test fuzzy registered agent search
EXPLAIN ANALYZE
SELECT doc_number, entity_name, registered_agent,
       similarity(registered_agent, 'JOHN SMITH') AS sim_score
FROM sunbiz_corporate
WHERE registered_agent % 'JOHN SMITH'
ORDER BY sim_score DESC
LIMIT 10;

-- Test date range with status filter (should use composite index)
EXPLAIN ANALYZE
SELECT COUNT(*)
FROM sunbiz_corporate
WHERE status = 'ACTIVE'
    AND filing_date >= '2024-01-01'
    AND filing_date < '2025-01-01';

-- Show search operators available
SELECT 
    '% operator' AS operator,
    'Similarity search (default threshold 0.3)' AS description
UNION ALL
SELECT 
    '<-> operator',
    'Distance operator for ORDER BY (KNN search)'
UNION ALL
SELECT 
    'similarity() function',
    'Returns similarity score (0-1)'
UNION ALL
SELECT 
    'show_trgm() function',
    'Shows trigrams for debugging';

-- ============================================================
-- END OF POST-LOAD OPTIMIZATION
-- ============================================================