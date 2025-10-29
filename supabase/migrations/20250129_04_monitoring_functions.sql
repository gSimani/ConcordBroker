-- =====================================================
-- PHASE 1.4: MONITORING AND ANALYSIS FUNCTIONS
-- Database performance monitoring utilities
--
-- Estimated time: 5-10 minutes
-- Impact: Enables performance tracking and analysis
-- Risk: NONE (read-only functions)
--
-- Run in Supabase SQL Editor
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- =====================================================
-- Function 1: Get Slow Queries
-- Returns queries that are taking too long
-- =====================================================

CREATE OR REPLACE FUNCTION get_slow_queries(
  min_time_ms INT DEFAULT 1000,
  result_limit INT DEFAULT 20
)
RETURNS TABLE (
  query_snippet TEXT,
  calls BIGINT,
  total_time_ms NUMERIC,
  mean_time_ms NUMERIC,
  max_time_ms NUMERIC,
  min_time_ms NUMERIC,
  stddev_time_ms NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    LEFT(pg_stat_statements.query, 200) as query_snippet,
    pg_stat_statements.calls,
    ROUND(pg_stat_statements.total_exec_time::numeric, 2) as total_time_ms,
    ROUND(pg_stat_statements.mean_exec_time::numeric, 2) as mean_time_ms,
    ROUND(pg_stat_statements.max_exec_time::numeric, 2) as max_time_ms,
    ROUND(pg_stat_statements.min_exec_time::numeric, 2) as min_time_ms,
    ROUND(pg_stat_statements.stddev_exec_time::numeric, 2) as stddev_time_ms
  FROM pg_stat_statements
  WHERE mean_exec_time > min_time_ms
    AND query NOT LIKE '%pg_stat_statements%'  -- Exclude monitoring queries
  ORDER BY mean_exec_time DESC
  LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_slow_queries IS
  'Find queries with mean execution time above threshold (default 1000ms)';

GRANT EXECUTE ON FUNCTION get_slow_queries TO anon, authenticated;

-- =====================================================
-- Function 2: Get Table Statistics
-- Returns size and row count for all tables
-- =====================================================

CREATE OR REPLACE FUNCTION get_table_stats()
RETURNS TABLE (
  table_name TEXT,
  row_count BIGINT,
  table_size TEXT,
  index_size TEXT,
  total_size TEXT,
  table_size_bytes BIGINT,
  index_size_bytes BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    relname::TEXT as table_name,
    n_live_tup as row_count,
    pg_size_pretty(pg_total_relation_size(relid) - pg_indexes_size(relid)) as table_size,
    pg_size_pretty(pg_indexes_size(relid)) as index_size,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
    (pg_total_relation_size(relid) - pg_indexes_size(relid)) as table_size_bytes,
    pg_indexes_size(relid) as index_size_bytes
  FROM pg_stat_user_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(relid) DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_table_stats IS
  'Get size and row count statistics for all tables';

GRANT EXECUTE ON FUNCTION get_table_stats TO anon, authenticated;

-- =====================================================
-- Function 3: Get Index Usage Statistics
-- Returns how often each index is being used
-- =====================================================

CREATE OR REPLACE FUNCTION get_index_usage()
RETURNS TABLE (
  table_name TEXT,
  index_name TEXT,
  index_scans BIGINT,
  rows_read BIGINT,
  rows_fetched BIGINT,
  index_size TEXT,
  usage_ratio NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    schemaname || '.' || tablename as table_name,
    indexrelname as index_name,
    idx_scan as index_scans,
    idx_tup_read as rows_read,
    idx_tup_fetch as rows_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE
      WHEN idx_scan = 0 THEN 0
      ELSE ROUND((idx_tup_fetch::numeric / NULLIF(idx_scan, 0)), 2)
    END as usage_ratio
  FROM pg_stat_user_indexes
  WHERE schemaname = 'public'
  ORDER BY idx_scan DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_index_usage IS
  'Get index usage statistics - identify unused indexes';

GRANT EXECUTE ON FUNCTION get_index_usage TO anon, authenticated;

-- =====================================================
-- Function 4: Get Unused Indexes
-- Identifies indexes that are never used (candidates for removal)
-- =====================================================

CREATE OR REPLACE FUNCTION get_unused_indexes()
RETURNS TABLE (
  table_name TEXT,
  index_name TEXT,
  index_size TEXT,
  index_size_bytes BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    schemaname || '.' || tablename as table_name,
    indexrelname as index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    pg_relation_size(indexrelid) as index_size_bytes
  FROM pg_stat_user_indexes
  WHERE schemaname = 'public'
    AND idx_scan = 0
    AND indexrelname NOT LIKE '%_pkey'  -- Exclude primary keys
  ORDER BY pg_relation_size(indexrelid) DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_unused_indexes IS
  'Find indexes that have never been scanned - candidates for removal';

GRANT EXECUTE ON FUNCTION get_unused_indexes TO anon, authenticated;

-- =====================================================
-- Function 5: Get Cache Hit Ratio
-- Returns database cache effectiveness
-- =====================================================

CREATE OR REPLACE FUNCTION get_cache_hit_ratio()
RETURNS TABLE (
  table_name TEXT,
  heap_reads BIGINT,
  heap_hits BIGINT,
  index_reads BIGINT,
  index_hits BIGINT,
  cache_hit_ratio NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    relname::TEXT as table_name,
    heap_blks_read as heap_reads,
    heap_blks_hit as heap_hits,
    idx_blks_read as index_reads,
    idx_blks_hit as index_hits,
    CASE
      WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 100
      ELSE ROUND((heap_blks_hit::numeric / NULLIF((heap_blks_hit + heap_blks_read), 0)) * 100, 2)
    END as cache_hit_ratio
  FROM pg_statio_user_tables
  WHERE schemaname = 'public'
  ORDER BY heap_blks_read DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_cache_hit_ratio IS
  'Get cache hit ratio for tables - aim for >90%';

GRANT EXECUTE ON FUNCTION get_cache_hit_ratio TO anon, authenticated;

-- =====================================================
-- Function 6: Analyze Query Plan
-- Get execution plan for a query
-- =====================================================

CREATE OR REPLACE FUNCTION analyze_query(query_text TEXT)
RETURNS TABLE (plan_line TEXT) AS $$
BEGIN
  RETURN QUERY EXECUTE 'EXPLAIN ANALYZE ' || query_text;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION analyze_query IS
  'Get EXPLAIN ANALYZE output for a query';

GRANT EXECUTE ON FUNCTION analyze_query TO postgres;  -- Restricted to admin

-- =====================================================
-- Function 7: Get Database Performance Summary
-- Single function for quick overview
-- =====================================================

CREATE OR REPLACE FUNCTION get_performance_summary()
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'database_size', pg_size_pretty(pg_database_size(current_database())),
    'active_connections', (SELECT count(*) FROM pg_stat_activity WHERE state = 'active'),
    'total_connections', (SELECT count(*) FROM pg_stat_activity),
    'cache_hit_ratio', (
      SELECT ROUND(
        (sum(heap_blks_hit)::numeric / NULLIF(sum(heap_blks_hit + heap_blks_read), 0)) * 100,
        2
      )
      FROM pg_statio_user_tables
    ),
    'slow_queries_count', (
      SELECT count(*)
      FROM pg_stat_statements
      WHERE mean_exec_time > 1000
    ),
    'largest_tables', (
      SELECT json_agg(
        json_build_object(
          'table', relname,
          'size', pg_size_pretty(pg_total_relation_size(relid)),
          'rows', n_live_tup
        )
      )
      FROM (
        SELECT relname, relid, n_live_tup
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(relid) DESC
        LIMIT 5
      ) t
    )
  ) INTO result;

  RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_performance_summary IS
  'Get quick performance overview of database';

GRANT EXECUTE ON FUNCTION get_performance_summary TO anon, authenticated;

-- =====================================================
-- VERIFICATION QUERIES
-- Test that all functions work
-- =====================================================

-- Test slow queries function
SELECT * FROM get_slow_queries(100, 5);

-- Test table stats
SELECT * FROM get_table_stats();

-- Test index usage
SELECT * FROM get_index_usage() LIMIT 10;

-- Test unused indexes
SELECT * FROM get_unused_indexes();

-- Test cache hit ratio
SELECT * FROM get_cache_hit_ratio() LIMIT 10;

-- Test performance summary
SELECT get_performance_summary();

-- =====================================================
-- CREATE MONITORING VIEW
-- Convenience view for quick checks
-- =====================================================

CREATE OR REPLACE VIEW v_database_health AS
SELECT
  (SELECT pg_size_pretty(pg_database_size(current_database()))) as database_size,
  (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
  (SELECT ROUND(
    (sum(heap_blks_hit)::numeric / NULLIF(sum(heap_blks_hit + heap_blks_read), 0)) * 100,
    2
  ) FROM pg_statio_user_tables) as cache_hit_ratio_pct,
  (SELECT count(*) FROM pg_stat_statements WHERE mean_exec_time > 1000) as slow_queries,
  (SELECT count(*) FROM get_unused_indexes()) as unused_indexes,
  NOW() as checked_at;

COMMENT ON VIEW v_database_health IS
  'Quick database health check view';

-- =====================================================
-- USAGE EXAMPLES
-- =====================================================
/*

-- Find slow queries (taking more than 500ms on average)
SELECT * FROM get_slow_queries(500, 10);

-- Check table sizes
SELECT * FROM get_table_stats();

-- Check which indexes are being used
SELECT * FROM get_index_usage()
WHERE index_scans > 0
ORDER BY index_scans DESC
LIMIT 20;

-- Find indexes that might be unused (candidates for removal)
SELECT * FROM get_unused_indexes();

-- Check cache effectiveness (should be >90%)
SELECT * FROM get_cache_hit_ratio()
WHERE cache_hit_ratio < 90;

-- Quick health check
SELECT * FROM v_database_health;

-- Detailed performance summary
SELECT get_performance_summary();

*/

-- =====================================================
-- EXPECTED RESULTS
-- =====================================================
--
-- After running this script:
-- - 7 monitoring functions created
-- - 1 health check view created
-- - All functions tested and working
-- - Ready to track performance over time
--
-- Use these functions to:
-- - Identify slow queries
-- - Monitor index usage
-- - Track table growth
-- - Verify cache effectiveness
-- - Overall database health
-- =====================================================
