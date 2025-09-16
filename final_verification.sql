-- =====================================================
-- FINAL UPLOAD VERIFICATION
-- =====================================================

-- 1. TOTAL ENTITIES AND FILES
SELECT 
    COUNT(*) as total_entities,
    COUNT(DISTINCT source_file) as unique_source_files,
    ROUND(COUNT(DISTINCT source_file) * 100.0 / 8414, 2) as percent_complete
FROM public.florida_entities
WHERE source_file IS NOT NULL;

-- 2. BREAKDOWN BY AGENT
SELECT 
    CASE 
        WHEN entity_id LIKE 'B_%' THEN 'Backward Synergy Agent'
        WHEN entity_id LIKE 'GAP_%' THEN 'Gap Filler Agent'
        ELSE 'Forward Agent'
    END as upload_agent,
    COUNT(*) as entity_count,
    COUNT(DISTINCT source_file) as files_processed
FROM public.florida_entities
GROUP BY 1
ORDER BY 2 DESC;

-- 3. CHECK FOR RECENT ACTIVITY
SELECT 
    date_trunc('hour', created_at) as hour,
    COUNT(*) as entities_added,
    COUNT(DISTINCT source_file) as files_added
FROM public.florida_entities
WHERE created_at >= NOW() - INTERVAL '3 hours'
GROUP BY 1
ORDER BY 1 DESC;

-- 4. SAMPLE OF PROCESSED FILES
SELECT source_file, COUNT(*) as entity_count
FROM public.florida_entities
WHERE source_file IS NOT NULL
GROUP BY source_file
ORDER BY source_file DESC
LIMIT 20;

-- 5. COMPLETION SUMMARY
WITH stats AS (
    SELECT 
        COUNT(DISTINCT source_file) as files_processed,
        COUNT(*) as total_entities
    FROM public.florida_entities
    WHERE source_file IS NOT NULL
)
SELECT 
    files_processed,
    8414 as total_expected_files,
    8414 - files_processed as missing_files,
    CASE 
        WHEN files_processed >= 8414 THEN '✅ COMPLETE - All files uploaded!'
        WHEN files_processed >= 8400 THEN '✅ NEARLY COMPLETE - 99.8%+ uploaded'
        WHEN files_processed >= 8300 THEN '⚠️ ALMOST DONE - ' || ROUND(files_processed * 100.0 / 8414, 1) || '% complete'
        ELSE '⏳ IN PROGRESS - ' || ROUND(files_processed * 100.0 / 8414, 1) || '% complete'
    END as status,
    total_entities as total_entities_created
FROM stats;