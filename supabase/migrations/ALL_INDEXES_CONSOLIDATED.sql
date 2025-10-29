-- =====================================================
-- CONSOLIDATED INDEX CREATION SCRIPT
-- Run this entire file to create ALL optimization indexes
--
-- Total: 34 indexes + 1 table + 7 functions
-- Estimated time: 60-90 minutes
-- Risk: LOW (can be rolled back)
--
-- IMPORTANT: Create database backup BEFORE running!
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Set timeout for long-running index creation
SET statement_timeout = '60min';

-- =====================================================
-- PART 1: FLORIDA_PARCELS INDEXES (11 indexes)
-- Estimated time: 30-45 minutes
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '=== PART 1: Creating florida_parcels indexes ===';
    RAISE NOTICE 'Estimated time: 30-45 minutes';
    RAISE NOTICE 'Started at: %', clock_timestamp();
END $$;

-- Index 1: County + Year
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_county_year
  ON florida_parcels(county, year)
  WHERE year = 2025;

-- Index 2: Parcel ID
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_parcel_id
  ON florida_parcels(parcel_id)
  WHERE parcel_id IS NOT NULL;

-- Index 3: Address Prefix
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_address_prefix
  ON florida_parcels(LEFT(phy_addr1, 10))
  WHERE phy_addr1 IS NOT NULL;

-- Index 4: Address Fuzzy (Trigram)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_address_trgm
  ON florida_parcels USING gist(phy_addr1 gist_trgm_ops);

-- Index 5: Owner Name Exact
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_owner_name
  ON florida_parcels(owner_name)
  WHERE owner_name IS NOT NULL;

-- Index 6: Owner Name Fuzzy (Trigram)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_owner_trgm
  ON florida_parcels USING gist(owner_name gist_trgm_ops);

-- Index 7: City Lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_city
  ON florida_parcels(phy_city)
  WHERE phy_city IS NOT NULL;

-- Index 8: Value Range
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_just_value
  ON florida_parcels(just_value)
  WHERE just_value IS NOT NULL;

-- Index 9: Year Built Range
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_year_built
  ON florida_parcels(year_built)
  WHERE year_built IS NOT NULL;

-- Index 10: Property Use
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_property_use
  ON florida_parcels(property_use)
  WHERE property_use IS NOT NULL;

-- Index 11: Composite Advanced Filter
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_county_value_year
  ON florida_parcels(county, just_value, year_built)
  WHERE year = 2025 AND just_value IS NOT NULL;

DO $$
BEGIN
    RAISE NOTICE 'Part 1 Complete: florida_parcels indexes created';
    RAISE NOTICE 'Completed at: %', clock_timestamp();
END $$;

-- =====================================================
-- PART 2: PROPERTY_SALES_HISTORY INDEXES (5 indexes)
-- Estimated time: 10-15 minutes
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== PART 2: Creating property_sales_history indexes ===';
    RAISE NOTICE 'Estimated time: 10-15 minutes';
    RAISE NOTICE 'Started at: %', clock_timestamp();
END $$;

-- Index 1: Parcel + Date Composite
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_parcel_date
  ON property_sales_history(parcel_id, sale_date DESC)
  WHERE sale_date IS NOT NULL;

-- Index 2: Sale Date Range
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_date
  ON property_sales_history(sale_date DESC)
  WHERE sale_date IS NOT NULL;

-- Index 3: Sale Price
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_price
  ON property_sales_history(sale_price)
  WHERE sale_price IS NOT NULL;

-- Index 4: Qualified Sales
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_qualified
  ON property_sales_history(qualified_sale, sale_date DESC)
  WHERE qualified_sale = true;

-- Index 5: Sale Type
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_type
  ON property_sales_history(sale_type)
  WHERE sale_type IS NOT NULL;

DO $$
BEGIN
    RAISE NOTICE 'Part 2 Complete: property_sales_history indexes created';
    RAISE NOTICE 'Completed at: %', clock_timestamp();
END $$;

-- =====================================================
-- PART 3: SUNBIZ TABLES AND INDEXES (18 indexes + 1 table)
-- Estimated time: 15-20 minutes (fast because tables empty)
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== PART 3: Creating sunbiz_officers table and indexes ===';
    RAISE NOTICE 'Estimated time: 15-20 minutes';
    RAISE NOTICE 'Started at: %', clock_timestamp();
END $$;

-- Create sunbiz_officers table
CREATE TABLE IF NOT EXISTS sunbiz_officers (
  id BIGSERIAL PRIMARY KEY,
  doc_number VARCHAR(12) NOT NULL,
  officer_name VARCHAR(200) NOT NULL,
  officer_title VARCHAR(100),
  officer_address TEXT,
  officer_email VARCHAR(255),
  officer_phone VARCHAR(20),
  filing_date DATE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(doc_number, officer_name, officer_title),
  FOREIGN KEY (doc_number) REFERENCES sunbiz_corporate(doc_number) ON DELETE CASCADE
);

-- Enable RLS
ALTER TABLE sunbiz_officers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public read access on sunbiz_officers" ON sunbiz_officers;
CREATE POLICY "Public read access on sunbiz_officers"
  ON sunbiz_officers FOR SELECT
  USING (true);

-- SUNBIZ_CORPORATE INDEXES (9 indexes)

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_doc_number
  ON sunbiz_corporate(doc_number);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_prin_addr
  ON sunbiz_corporate(prin_addr1)
  WHERE prin_addr1 IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_mail_addr
  ON sunbiz_corporate(mail_addr1)
  WHERE mail_addr1 IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_entity_name
  ON sunbiz_corporate(entity_name)
  WHERE entity_name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_entity_trgm
  ON sunbiz_corporate USING gist(entity_name gist_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_agent
  ON sunbiz_corporate(registered_agent)
  WHERE registered_agent IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_agent_trgm
  ON sunbiz_corporate USING gist(registered_agent gist_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_status_date
  ON sunbiz_corporate(status, filing_date DESC)
  WHERE status = 'ACTIVE';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_entity_type
  ON sunbiz_corporate(entity_type)
  WHERE entity_type IS NOT NULL;

-- SUNBIZ_OFFICERS INDEXES (3 indexes)

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_officers_name
  ON sunbiz_officers(officer_name)
  WHERE officer_name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_officers_name_trgm
  ON sunbiz_officers USING gist(officer_name gist_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_officers_doc_number
  ON sunbiz_officers(doc_number);

-- SUNBIZ_FICTITIOUS INDEXES (6 indexes)

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_name
  ON sunbiz_fictitious(name)
  WHERE name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_name_trgm
  ON sunbiz_fictitious USING gist(name gist_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_name_gin
  ON sunbiz_fictitious USING gin(to_tsvector('english', name));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_owner
  ON sunbiz_fictitious(owner_name)
  WHERE owner_name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_owner_trgm
  ON sunbiz_fictitious USING gist(owner_name gist_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_owner_gin
  ON sunbiz_fictitious USING gin(to_tsvector('english', owner_name));

DO $$
BEGIN
    RAISE NOTICE 'Part 3 Complete: Sunbiz tables and indexes created';
    RAISE NOTICE 'Completed at: %', clock_timestamp();
END $$;

-- =====================================================
-- PART 4: MONITORING FUNCTIONS (7 functions)
-- Estimated time: 5-10 minutes
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== PART 4: Creating monitoring functions ===';
    RAISE NOTICE 'Estimated time: 5-10 minutes';
    RAISE NOTICE 'Started at: %', clock_timestamp();
END $$;

-- Function 1: Get Slow Queries
CREATE OR REPLACE FUNCTION get_slow_queries(
  min_time_ms INT DEFAULT 1000,
  result_limit INT DEFAULT 20
)
RETURNS TABLE (
  query_snippet TEXT,
  calls BIGINT,
  total_time_ms NUMERIC,
  mean_time_ms NUMERIC,
  max_time_ms NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    LEFT(pg_stat_statements.query, 200) as query_snippet,
    pg_stat_statements.calls,
    ROUND(pg_stat_statements.total_exec_time::numeric, 2) as total_time_ms,
    ROUND(pg_stat_statements.mean_exec_time::numeric, 2) as mean_time_ms,
    ROUND(pg_stat_statements.max_exec_time::numeric, 2) as max_time_ms
  FROM pg_stat_statements
  WHERE mean_exec_time > min_time_ms
    AND query NOT LIKE '%pg_stat_statements%'
  ORDER BY mean_exec_time DESC
  LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION get_slow_queries TO anon, authenticated;

-- Function 2: Get Table Statistics
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

GRANT EXECUTE ON FUNCTION get_table_stats TO anon, authenticated;

-- Function 3: Get Index Usage
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

GRANT EXECUTE ON FUNCTION get_index_usage TO anon, authenticated;

-- Function 4: Get Unused Indexes
CREATE OR REPLACE FUNCTION get_unused_indexes()
RETURNS TABLE (
  table_name TEXT,
  index_name TEXT,
  index_size TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    schemaname || '.' || tablename as table_name,
    indexrelname as index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
  FROM pg_stat_user_indexes
  WHERE schemaname = 'public'
    AND idx_scan = 0
    AND indexrelname NOT LIKE '%_pkey'
  ORDER BY pg_relation_size(indexrelid) DESC;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION get_unused_indexes TO anon, authenticated;

-- Function 5: Get Cache Hit Ratio
CREATE OR REPLACE FUNCTION get_cache_hit_ratio()
RETURNS TABLE (
  table_name TEXT,
  cache_hit_ratio NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    relname::TEXT as table_name,
    CASE
      WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 100
      ELSE ROUND((heap_blks_hit::numeric / NULLIF((heap_blks_hit + heap_blks_read), 0)) * 100, 2)
    END as cache_hit_ratio
  FROM pg_statio_user_tables
  WHERE schemaname = 'public'
  ORDER BY heap_blks_read DESC;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION get_cache_hit_ratio TO anon, authenticated;

-- Function 6: Get Performance Summary
CREATE OR REPLACE FUNCTION get_performance_summary()
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'database_size', pg_size_pretty(pg_database_size(current_database())),
    'active_connections', (SELECT count(*) FROM pg_stat_activity WHERE state = 'active'),
    'cache_hit_ratio', (
      SELECT ROUND(
        (sum(heap_blks_hit)::numeric / NULLIF(sum(heap_blks_hit + heap_blks_read), 0)) * 100,
        2
      )
      FROM pg_statio_user_tables
    )
  ) INTO result;
  RETURN result;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION get_performance_summary TO anon, authenticated;

-- Create Health Check View
CREATE OR REPLACE VIEW v_database_health AS
SELECT
  (SELECT pg_size_pretty(pg_database_size(current_database()))) as database_size,
  (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
  (SELECT ROUND(
    (sum(heap_blks_hit)::numeric / NULLIF(sum(heap_blks_hit + heap_blks_read), 0)) * 100,
    2
  ) FROM pg_statio_user_tables) as cache_hit_ratio_pct,
  NOW() as checked_at;

DO $$
BEGIN
    RAISE NOTICE 'Part 4 Complete: Monitoring functions created';
    RAISE NOTICE 'Completed at: %', clock_timestamp();
END $$;

-- =====================================================
-- FINAL VERIFICATION
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== ALL PARTS COMPLETE ===';
    RAISE NOTICE 'Completed at: %', clock_timestamp();
    RAISE NOTICE '';
    RAISE NOTICE 'Run verification queries below to confirm success.';
END $$;

-- Verification Query 1: Count all new indexes by table
SELECT
  tablename,
  COUNT(*) as index_count,
  pg_size_pretty(SUM(pg_relation_size(indexrelid))) as total_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
WHERE tablename IN ('florida_parcels', 'property_sales_history', 'sunbiz_corporate', 'sunbiz_fictitious', 'sunbiz_officers')
  AND (indexname LIKE 'idx_fp_%' OR indexname LIKE 'idx_sales_%' OR indexname LIKE 'idx_sunbiz_%' OR indexname LIKE 'idx_fict_%' OR indexname LIKE 'idx_officers_%')
GROUP BY tablename
ORDER BY tablename;

-- Verification Query 2: Test monitoring functions
SELECT * FROM v_database_health;

-- Verification Query 3: Show all monitoring functions
SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name LIKE 'get_%'
ORDER BY routine_name;

-- =====================================================
-- EXPECTED RESULTS
-- =====================================================
/*

Verification Query 1 should show:
 tablename               | index_count | total_size
-------------------------+-------------+------------
 florida_parcels         | 11          | ~600 MB
 property_sales_history  | 5           | ~15 MB
 sunbiz_corporate        | 9           | ~10 MB
 sunbiz_fictitious       | 6           | ~8 MB
 sunbiz_officers         | 3           | ~1 MB

Verification Query 2 should return database health data

Verification Query 3 should show 6 functions:
 - get_cache_hit_ratio
 - get_index_usage
 - get_performance_summary
 - get_slow_queries
 - get_table_stats
 - get_unused_indexes

TOTAL CREATED:
- 34 indexes
- 1 table (sunbiz_officers)
- 6 functions
- 1 view (v_database_health)

*/
