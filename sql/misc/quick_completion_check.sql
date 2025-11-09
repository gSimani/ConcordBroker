-- QUICK COMPLETION CHECK
-- =====================

-- 1. Total entities (should be millions)
SELECT 
    COUNT(*) as total_entities,
    COUNT(DISTINCT source_file) as unique_files
FROM public.florida_entities
WHERE source_file IS NOT NULL
LIMIT 1;

-- 2. Files processed summary  
SELECT 
    COUNT(DISTINCT source_file) as files_processed,
    8414 as total_expected,
    ROUND(COUNT(DISTINCT source_file) * 100.0 / 8414, 2) as percent_complete
FROM public.florida_entities
WHERE source_file IS NOT NULL;

-- 3. Quick agent breakdown
SELECT 
    CASE 
        WHEN COUNT(*) FILTER (WHERE entity_id LIKE 'B_%') > 0 THEN 'YES' 
        ELSE 'NO' 
    END as backward_agent_ran,
    CASE 
        WHEN COUNT(*) FILTER (WHERE entity_id LIKE 'GAP%') > 0 THEN 'YES' 
        ELSE 'NO' 
    END as gap_filler_ran,
    COUNT(*) FILTER (WHERE entity_id NOT LIKE 'B_%' AND entity_id NOT LIKE 'GAP%') as forward_agent_records
FROM public.florida_entities;

-- 4. FINAL STATUS
SELECT 
    CASE 
        WHEN COUNT(DISTINCT source_file) >= 8414 THEN '✅ 100% COMPLETE - ALL FILES UPLOADED!'
        WHEN COUNT(DISTINCT source_file) >= 8400 THEN '✅ 99.8%+ COMPLETE - ESSENTIALLY DONE!'
        WHEN COUNT(DISTINCT source_file) >= 8200 THEN '✅ 97.5%+ COMPLETE - READY FOR USE!'
        ELSE '⏳ IN PROGRESS'
    END as upload_status
FROM public.florida_entities
WHERE source_file IS NOT NULL;