-- =====================================================
-- FLORIDA ENTITIES - COMPACT MONITORING QUERY PACK
-- Pin these in Supabase SQL Editor for real-time monitoring
-- =====================================================

-- 1) CURRENT STATUS OVERVIEW
-- Shows total count, recent activity, and upload health
WITH recent AS (
  SELECT count(*) as last_10m
  FROM public.florida_entities
  WHERE created_at >= now() - interval '10 minutes'
)
SELECT 
  (SELECT count(*) FROM public.florida_entities) as total_entities,
  recent.last_10m as "Last 10 Min",
  (SELECT max(created_at) FROM public.florida_entities) as latest_created_at,
  CASE 
    WHEN recent.last_10m > 0 THEN 'ACTIVE'
    ELSE 'STOPPED'
  END as status
FROM recent;

-- 2) UPLOAD VELOCITY (last 30m)
-- Inserts per minute to track speed
SELECT 
  date_trunc('minute', created_at) as minute, 
  count(*) as rows_inserted,
  ROUND(count(*)/60.0, 1) as per_second
FROM public.florida_entities
WHERE created_at >= now() - interval '30 minutes'
GROUP BY 1
ORDER BY 1 DESC;

-- 3) PROGRESS BY SOURCE FILE
-- Recent files being processed
SELECT 
  source_file, 
  count(*) as rows, 
  min(created_at) as first_seen, 
  max(created_at) as last_seen
FROM public.florida_entities
WHERE created_at >= now() - interval '2 hours'
  AND source_file IS NOT NULL
GROUP BY 1
ORDER BY last_seen DESC NULLS LAST
LIMIT 20;

-- 4) ENTITY STATUS BREAKDOWN
-- Distribution of entity statuses
SELECT 
  entity_status,
  count(*) as count,
  ROUND(100.0 * count(*) / sum(count(*)) OVER(), 2) as pct
FROM public.florida_entities
GROUP BY 1
ORDER BY 2 DESC;

-- 5) DUPLICATE CHECK
-- Ensures no duplicate entity_ids
SELECT 
  CASE 
    WHEN count(*) = 0 THEN 'No duplicates'
    ELSE 'DUPLICATES: ' || count(*)
  END as status
FROM (
  SELECT entity_id 
  FROM public.florida_entities 
  GROUP BY entity_id 
  HAVING count(*) > 1
) d;

-- 6) DATA QUALITY CHECK
-- Validates recent data integrity
SELECT 
  count(*) as recent_rows,
  count(*) FILTER (WHERE business_name IS NULL OR business_name = '') as missing_names,
  count(*) FILTER (WHERE entity_id IS NULL) as missing_ids,
  count(*) FILTER (WHERE length(entity_id) > 45) as oversized_ids
FROM public.florida_entities
WHERE created_at >= now() - interval '10 minutes';

-- 7) PERFORMANCE METRICS
-- Database and table sizes
SELECT 
  pg_size_pretty(pg_database_size(current_database())) as db_size,
  pg_size_pretty(pg_total_relation_size('public.florida_entities')) as table_size,
  (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections;

-- =====================================================
-- OPTIONAL: CREATE MONITORING INDEXES
-- Run once to optimize monitoring query performance
-- =====================================================

-- Index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_florida_entities_created_at 
ON public.florida_entities(created_at DESC);

-- Index on source_file for file progress tracking
CREATE INDEX IF NOT EXISTS idx_florida_entities_source_file 
ON public.florida_entities(source_file) 
WHERE source_file IS NOT NULL;

-- Index on entity_status for distribution queries
CREATE INDEX IF NOT EXISTS idx_florida_entities_status 
ON public.florida_entities(entity_status);

-- =====================================================
-- RLS CONSIDERATIONS
-- =====================================================
-- If RLS is enabled on florida_entities:
-- 1. Use service role key for monitoring (bypasses RLS)
-- 2. Or create a policy for admin users:
/*
CREATE POLICY "Admin users can view all entities" 
ON public.florida_entities
FOR SELECT 
TO authenticated
USING (
  auth.jwt() ->> 'email' IN (
    'admin@example.com'  -- Replace with your admin emails
  )
);
*/

-- =====================================================
-- ESTIMATED TIME TO COMPLETION
-- Based on current upload rate
-- =====================================================
WITH rate_calc AS (
  SELECT 
    count(*) as recent_count,
    EXTRACT(EPOCH FROM (max(created_at) - min(created_at)))/60 as minutes_elapsed
  FROM public.florida_entities
  WHERE created_at >= now() - interval '10 minutes'
)
SELECT 
  (SELECT count(*) FROM public.florida_entities) as current_total,
  recent_count,
  ROUND(recent_count / NULLIF(minutes_elapsed, 0)) as per_minute,
  ROUND((8414000 - (SELECT count(*) FROM public.florida_entities)) / 
        NULLIF(recent_count / NULLIF(minutes_elapsed, 0), 0) / 60) as hours_remaining
FROM rate_calc;