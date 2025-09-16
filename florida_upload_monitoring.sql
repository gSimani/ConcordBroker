-- =====================================================
-- FLORIDA ENTITIES UPLOAD MONITORING DASHBOARD
-- =====================================================
-- Pin these queries in your Supabase SQL editor for real-time monitoring

-- 1. CURRENT STATUS OVERVIEW
-- Shows total count, recent activity, and last insert time
WITH status AS (
    SELECT 
        COUNT(*) as total_entities,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 minute') as last_minute,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '10 minutes') as last_10_min,
        MAX(created_at) as last_insert,
        EXTRACT(EPOCH FROM (NOW() - MAX(created_at))) as seconds_since_last
    FROM public.florida_entities
)
SELECT 
    total_entities,
    last_minute as "Last Minute",
    last_10_min as "Last 10 Min",
    last_insert as "Latest Insert",
    CASE 
        WHEN seconds_since_last < 60 THEN 'ACTIVE ✓'
        WHEN seconds_since_last < 300 THEN 'SLOW'
        ELSE 'STOPPED'
    END as upload_status
FROM status;

-- 2. UPLOAD VELOCITY (LAST 10 MINUTES)
-- Shows inserts per minute to track upload speed
SELECT 
    date_trunc('minute', created_at) as minute, 
    COUNT(*) as rows_inserted,
    ROUND(COUNT(*) / 60.0, 1) as rows_per_second
FROM public.florida_entities
WHERE created_at >= NOW() - INTERVAL '10 minutes'
GROUP BY 1
ORDER BY 1 DESC;

-- 3. ENTITY STATUS DISTRIBUTION
-- Shows breakdown by entity_status field
SELECT 
    entity_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM public.florida_entities
GROUP BY entity_status
ORDER BY count DESC;

-- 4. UPLOAD PROGRESS BY SOURCE FILE
-- Shows which files have been processed
SELECT 
    source_file,
    COUNT(*) as entities_from_file,
    MIN(created_at) as first_insert,
    MAX(created_at) as last_insert
FROM public.florida_entities
WHERE source_file IS NOT NULL
GROUP BY source_file
ORDER BY last_insert DESC
LIMIT 20;

-- 5. HOURLY UPLOAD STATS
-- Shows upload rate by hour
SELECT 
    date_trunc('hour', created_at) as hour,
    COUNT(*) as entities_uploaded,
    ROUND(COUNT(*) / 3600.0, 1) as avg_per_second
FROM public.florida_entities
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1 DESC;

-- 6. DUPLICATE CHECK
-- Verifies no duplicate entity_ids exist
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN 'No Duplicates ✓'
        ELSE 'DUPLICATES FOUND: ' || COUNT(*)
    END as duplicate_status
FROM (
    SELECT entity_id
    FROM public.florida_entities
    GROUP BY entity_id
    HAVING COUNT(*) > 1
) dupes;

-- 7. ESTIMATED TIME TO COMPLETION
-- Based on average upload rate
WITH upload_rate AS (
    SELECT 
        COUNT(*) / NULLIF(EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) / 60, 0) as entities_per_minute
    FROM public.florida_entities
    WHERE created_at >= NOW() - INTERVAL '10 minutes'
)
SELECT 
    218735 as current_total,
    8414 * 1000 as estimated_total_entities, -- Rough estimate based on file count
    ROUND(upload_rate.entities_per_minute) as current_rate_per_min,
    ROUND((8414 * 1000 - 218735) / NULLIF(upload_rate.entities_per_minute, 0)) as minutes_remaining,
    ROUND((8414 * 1000 - 218735) / NULLIF(upload_rate.entities_per_minute, 0) / 60) as hours_remaining
FROM upload_rate;

-- 8. PERFORMANCE METRICS
-- Database performance indicators
SELECT 
    pg_size_pretty(pg_database_size(current_database())) as database_size,
    pg_size_pretty(pg_total_relation_size('public.florida_entities')) as table_size,
    pg_size_pretty(pg_indexes_size('public.florida_entities')) as indexes_size,
    (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_connections;

-- 9. RECENT ERRORS CHECK
-- Looks for any potential issues in recent data
SELECT 
    COUNT(*) FILTER (WHERE business_name IS NULL OR business_name = '') as missing_names,
    COUNT(*) FILTER (WHERE entity_id IS NULL) as missing_ids,
    COUNT(*) FILTER (WHERE LENGTH(entity_id) > 45) as oversized_ids,
    COUNT(*) FILTER (WHERE created_at > NOW()) as future_timestamps
FROM public.florida_entities
WHERE created_at >= NOW() - INTERVAL '10 minutes';

-- 10. CONTACT EXTRACTION STATS (if florida_contacts table exists)
-- Shows phone/email extraction success
SELECT 
    'Entities with contacts' as metric,
    COUNT(DISTINCT entity_id) as count
FROM public.florida_contacts
UNION ALL
SELECT 
    'Phone numbers extracted',
    COUNT(*) FILTER (WHERE contact_type = 'phone')
FROM public.florida_contacts
UNION ALL
SELECT 
    'Email addresses extracted',
    COUNT(*) FILTER (WHERE contact_type = 'email')
FROM public.florida_contacts;