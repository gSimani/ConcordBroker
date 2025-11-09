-- =====================================================
-- DUAL AGENT MONITORING DASHBOARD
-- Track both forward and backward agents in real-time
-- =====================================================

-- 1. OVERALL PROGRESS
WITH progress AS (
    SELECT 
        COUNT(*) as total_entities,
        COUNT(DISTINCT source_file) as unique_files,
        MIN(created_at) as upload_start,
        MAX(created_at) as latest_insert,
        COUNT(*) FILTER (WHERE entity_id LIKE 'B_%') as backward_entities,
        COUNT(*) FILTER (WHERE entity_id NOT LIKE 'B_%') as forward_entities
    FROM public.florida_entities
)
SELECT 
    total_entities as "Total Entities",
    unique_files as "Files Processed",
    ROUND(unique_files * 100.0 / 8414, 1) as "% Complete",
    forward_entities as "Forward Agent Records",
    backward_entities as "Backward Agent Records",
    EXTRACT(EPOCH FROM (NOW() - upload_start))/3600 as "Hours Running",
    latest_insert as "Last Activity"
FROM progress;

-- 2. AGENT VELOCITY COMPARISON
WITH agent_activity AS (
    SELECT 
        CASE 
            WHEN entity_id LIKE 'B_%' THEN 'Backward (Synergy)'
            ELSE 'Forward (Original)'
        END as agent_type,
        date_trunc('minute', created_at) as minute,
        COUNT(*) as records_per_minute
    FROM public.florida_entities
    WHERE created_at >= NOW() - INTERVAL '10 minutes'
    GROUP BY 1, 2
)
SELECT 
    agent_type,
    AVG(records_per_minute) as avg_records_per_min,
    MAX(records_per_minute) as peak_records_per_min,
    ROUND(AVG(records_per_minute) / 1000.0, 2) as "Est Files/Min"
FROM agent_activity
GROUP BY agent_type
ORDER BY avg_records_per_min DESC;

-- 3. LATEST FILES FROM EACH AGENT
WITH latest_files AS (
    SELECT DISTINCT ON (agent_type)
        CASE 
            WHEN entity_id LIKE 'B_%' THEN 'Backward'
            ELSE 'Forward'
        END as agent_type,
        source_file,
        MAX(created_at) as last_processed
    FROM public.florida_entities
    WHERE source_file IS NOT NULL
      AND created_at >= NOW() - INTERVAL '5 minutes'
    GROUP BY 1, 2
    ORDER BY agent_type, last_processed DESC
)
SELECT 
    agent_type as "Agent",
    source_file as "Current File",
    last_processed as "Processed At"
FROM latest_files;

-- 4. MEETING POINT ESTIMATION
WITH file_positions AS (
    SELECT 
        MIN(CASE WHEN source_file LIKE '2011%' THEN source_file END) as forward_position,
        MAX(CASE WHEN source_file LIKE '2025%' OR source_file LIKE '2024%' 
                 OR source_file LIKE '2023%' OR source_file LIKE '2022%' 
            THEN source_file END) as backward_position
    FROM public.florida_entities
    WHERE created_at >= NOW() - INTERVAL '30 minutes'
)
SELECT 
    forward_position as "Forward Agent At",
    backward_position as "Backward Agent At",
    'Agents will meet around file 4000-4500' as "Meeting Point Estimate"
FROM file_positions;

-- 5. COMPLETION TIME ESTIMATE
WITH rates AS (
    SELECT 
        COUNT(*) FILTER (WHERE entity_id NOT LIKE 'B_%') / 
            NULLIF(EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at)))/60, 0) as forward_rate,
        COUNT(*) FILTER (WHERE entity_id LIKE 'B_%') / 
            NULLIF(EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at)))/60, 0) as backward_rate
    FROM public.florida_entities
    WHERE created_at >= NOW() - INTERVAL '10 minutes'
)
SELECT 
    ROUND(forward_rate) as "Forward Records/Min",
    ROUND(backward_rate) as "Backward Records/Min",
    ROUND((4500 - 3662) / NULLIF(forward_rate/1000, 0) / 60, 1) as "Forward Hours to Middle",
    ROUND((8414 - 4500) / NULLIF(backward_rate/1000, 0) / 60, 1) as "Backward Hours to Middle",
    CASE 
        WHEN backward_rate > forward_rate * 2 
        THEN 'Synergy agent is ' || ROUND(backward_rate/NULLIF(forward_rate,0), 1) || 'x faster!'
        ELSE 'Both agents working well'
    END as "Performance Note"
FROM rates;