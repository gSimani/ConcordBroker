-- =====================================================
-- UPLOAD PERFORMANCE ANALYSIS
-- Real-time metrics to diagnose slow upload speed
-- =====================================================

-- 1. CURRENT INSERT RATE (Last 5 minutes)
WITH recent_inserts AS (
    SELECT 
        date_trunc('minute', created_at) as minute,
        COUNT(*) as rows_per_minute
    FROM public.florida_entities
    WHERE created_at >= NOW() - INTERVAL '5 minutes'
    GROUP BY 1
    ORDER BY 1 DESC
)
SELECT 
    minute,
    rows_per_minute,
    ROUND(rows_per_minute / 60.0, 1) as rows_per_second,
    ROUND(rows_per_minute * 60.0 / 1000.0, 2) as "files_per_hour (est)"
FROM recent_inserts;

-- 2. BATCH SIZE ANALYSIS
-- Check if batches are too small
WITH batch_analysis AS (
    SELECT 
        source_file,
        COUNT(*) as records_in_file,
        MIN(created_at) as start_time,
        MAX(created_at) as end_time,
        EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) as seconds_to_process
    FROM public.florida_entities
    WHERE created_at >= NOW() - INTERVAL '30 minutes'
      AND source_file IS NOT NULL
    GROUP BY source_file
    HAVING COUNT(*) > 100
)
SELECT 
    AVG(records_in_file) as avg_records_per_file,
    AVG(seconds_to_process) as avg_seconds_per_file,
    ROUND(AVG(records_in_file / NULLIF(seconds_to_process, 0)), 1) as avg_records_per_second
FROM batch_analysis;

-- 3. DATABASE PERFORMANCE BOTTLENECKS
SELECT 
    COUNT(*) as active_queries,
    COUNT(*) FILTER (WHERE state = 'active') as running_queries,
    COUNT(*) FILTER (WHERE wait_event_type IS NOT NULL) as waiting_queries,
    COUNT(*) FILTER (WHERE wait_event_type = 'Lock') as lock_waits,
    COUNT(*) FILTER (WHERE wait_event_type = 'IO') as io_waits
FROM pg_stat_activity
WHERE datname = current_database();

-- 4. TABLE BLOAT CHECK
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    ROUND(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_percentage
FROM pg_stat_user_tables
WHERE schemaname = 'public' 
  AND tablename = 'florida_entities';

-- 5. INDEX PERFORMANCE
SELECT 
    indexrelname as index_name,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public' 
  AND tablename = 'florida_entities'
ORDER BY idx_scan DESC;

-- 6. OPTIMIZATION RECOMMENDATIONS
WITH performance_metrics AS (
    SELECT 
        (SELECT COUNT(*) FROM public.florida_entities) as total_rows,
        (SELECT COUNT(*) FROM public.florida_entities WHERE created_at >= NOW() - INTERVAL '10 minutes') as recent_inserts,
        (SELECT n_dead_tup FROM pg_stat_user_tables WHERE tablename = 'florida_entities') as dead_tuples
)
SELECT 
    CASE 
        WHEN recent_inserts < 1000 THEN '⚠️ VERY SLOW: Consider increasing batch size to 1000-2000 records'
        WHEN recent_inserts < 5000 THEN '⚠️ SLOW: Batch size could be increased'
        ELSE '✓ Good insert rate'
    END as batch_size_recommendation,
    CASE 
        WHEN dead_tuples > total_rows * 0.2 THEN '⚠️ Run VACUUM ANALYZE florida_entities;'
        ELSE '✓ Table maintenance OK'
    END as maintenance_recommendation,
    CASE 
        WHEN total_rows > 5000000 THEN '⚠️ Consider partitioning for better performance'
        ELSE '✓ Table size manageable'
    END as partitioning_recommendation
FROM performance_metrics;