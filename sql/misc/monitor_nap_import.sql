-- =====================================================
-- NAP IMPORT MONITORING QUERIES
-- Real-time monitoring of florida_parcels data import
-- =====================================================

-- 1. OVERALL IMPORT STATUS
SELECT 
    'FLORIDA PARCELS OVERVIEW' as section,
    '========================' as divider;

SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN data_source = 'NAP' THEN 1 END) as nap_records,
    COUNT(CASE WHEN data_source = 'SDF' THEN 1 END) as sdf_records,
    COUNT(CASE WHEN data_source IS NULL THEN 1 END) as legacy_records,
    ROUND(
        COUNT(CASE WHEN data_source = 'NAP' THEN 1 END) * 100.0 / COUNT(*), 2
    ) as nap_percentage
FROM florida_parcels;

-- 2. DATA COMPLETENESS CHECK
SELECT 
    'DATA COMPLETENESS' as section,
    '==================' as divider;

SELECT 
    COUNT(*) as total_records,
    COUNT(parcel_id) as has_parcel_id,
    COUNT(owner_name) as has_owner_name,
    COUNT(phy_addr1) as has_address,
    COUNT(phy_city) as has_city,
    COUNT(just_value) as has_just_value,
    COUNT(assessed_value) as has_assessed_value,
    COUNT(sale_date) as has_sale_date,
    -- Completion percentages
    ROUND(COUNT(owner_name) * 100.0 / COUNT(*), 1) as owner_completion_pct,
    ROUND(COUNT(phy_addr1) * 100.0 / COUNT(*), 1) as address_completion_pct,
    ROUND(COUNT(just_value) * 100.0 / COUNT(*), 1) as value_completion_pct
FROM florida_parcels;

-- 3. IMPORT TIMELINE
SELECT 
    'IMPORT TIMELINE' as section,
    '===============' as divider;

SELECT 
    DATE(import_date) as import_day,
    COUNT(*) as records_imported,
    COUNT(DISTINCT import_batch_id) as batches,
    data_source,
    MIN(import_date) as first_import,
    MAX(import_date) as last_import
FROM florida_parcels
WHERE import_date IS NOT NULL
GROUP BY DATE(import_date), data_source
ORDER BY import_day DESC, data_source;

-- 4. COUNTY DISTRIBUTION
SELECT 
    'COUNTY DISTRIBUTION' as section,
    '====================' as divider;

SELECT 
    county,
    COUNT(*) as record_count,
    COUNT(CASE WHEN data_source = 'NAP' THEN 1 END) as nap_records,
    ROUND(AVG(just_value), 0) as avg_just_value,
    MAX(import_date) as latest_import
FROM florida_parcels
WHERE county IS NOT NULL
GROUP BY county
ORDER BY record_count DESC
LIMIT 20;

-- 5. VALUE STATISTICS BY SOURCE
SELECT 
    'VALUE STATISTICS' as section,
    '=================' as divider;

SELECT 
    COALESCE(data_source, 'LEGACY') as source,
    COUNT(*) as records,
    COUNT(CASE WHEN just_value > 0 THEN 1 END) as with_values,
    ROUND(MIN(just_value), 0) as min_value,
    ROUND(AVG(just_value), 0) as avg_value,
    ROUND(MAX(just_value), 0) as max_value,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY just_value), 0) as median_value
FROM florida_parcels
WHERE just_value > 0
GROUP BY data_source
ORDER BY records DESC;

-- 6. TOP CITIES BY RECORD COUNT
SELECT 
    'TOP CITIES' as section,
    '==========' as divider;

SELECT 
    phy_city,
    COUNT(*) as properties,
    COUNT(CASE WHEN data_source = 'NAP' THEN 1 END) as nap_count,
    ROUND(AVG(just_value), 0) as avg_value,
    MAX(import_date) as latest_import
FROM florida_parcels
WHERE phy_city IS NOT NULL
GROUP BY phy_city
ORDER BY properties DESC
LIMIT 15;

-- 7. RECENT IMPORT ACTIVITY (Last 24 hours)
SELECT 
    'RECENT ACTIVITY (24hrs)' as section,
    '=======================' as divider;

SELECT 
    EXTRACT(HOUR FROM import_date) as import_hour,
    COUNT(*) as records_imported,
    data_source,
    COUNT(DISTINCT import_batch_id) as batches
FROM florida_parcels
WHERE import_date > NOW() - INTERVAL '24 hours'
GROUP BY EXTRACT(HOUR FROM import_date), data_source
ORDER BY import_hour DESC, data_source;

-- 8. BATCH IMPORT STATUS
SELECT 
    'BATCH STATUS' as section,
    '============' as divider;

SELECT 
    import_batch_id,
    data_source,
    COUNT(*) as records_in_batch,
    MIN(import_date) as batch_start,
    MAX(import_date) as batch_end,
    EXTRACT(EPOCH FROM (MAX(import_date) - MIN(import_date))) as duration_seconds
FROM florida_parcels
WHERE import_batch_id IS NOT NULL
GROUP BY import_batch_id, data_source
ORDER BY batch_start DESC
LIMIT 20;

-- 9. DATA QUALITY ISSUES
SELECT 
    'DATA QUALITY ISSUES' as section,
    '===================' as divider;

SELECT 
    'Missing Parcel ID' as issue,
    COUNT(*) as count
FROM florida_parcels 
WHERE parcel_id IS NULL OR parcel_id = ''
UNION ALL
SELECT 
    'Missing Owner Name',
    COUNT(*)
FROM florida_parcels 
WHERE owner_name IS NULL OR owner_name = ''
UNION ALL
SELECT 
    'Missing Physical Address',
    COUNT(*)
FROM florida_parcels 
WHERE phy_addr1 IS NULL OR phy_addr1 = ''
UNION ALL
SELECT 
    'Missing City',
    COUNT(*)
FROM florida_parcels 
WHERE phy_city IS NULL OR phy_city = ''
UNION ALL
SELECT 
    'Zero or Negative Values',
    COUNT(*)
FROM florida_parcels 
WHERE just_value <= 0 OR assessed_value <= 0 OR taxable_value <= 0
UNION ALL
SELECT 
    'Duplicate Parcel IDs',
    COUNT(*) - COUNT(DISTINCT parcel_id)
FROM florida_parcels
ORDER BY count DESC;

-- 10. TABLE SIZE AND PERFORMANCE
SELECT 
    'TABLE PERFORMANCE' as section,
    '=================' as divider;

SELECT 
    'florida_parcels' as table_name,
    pg_size_pretty(pg_total_relation_size('florida_parcels'::regclass)) as total_size,
    pg_size_pretty(pg_relation_size('florida_parcels'::regclass)) as table_size,
    pg_size_pretty(pg_indexes_size('florida_parcels'::regclass)) as indexes_size,
    (SELECT reltuples::BIGINT FROM pg_class WHERE relname = 'florida_parcels') as estimated_rows;

-- 11. INDEX STATUS
SELECT 
    'INDEX STATUS' as section,
    '============' as divider;

SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_indexes 
JOIN pg_stat_user_indexes ON pg_indexes.indexname = pg_stat_user_indexes.indexrelname
WHERE tablename = 'florida_parcels'
ORDER BY pg_relation_size(indexname::regclass) DESC;

-- 12. CURRENT IMPORT RATE CALCULATION
SELECT 
    'IMPORT RATE ANALYSIS' as section,
    '====================' as divider;

WITH recent_imports AS (
    SELECT 
        import_date,
        COUNT(*) OVER (
            ORDER BY import_date 
            ROWS BETWEEN 999 PRECEDING AND CURRENT ROW
        ) as records_per_1000,
        EXTRACT(EPOCH FROM (
            import_date - LAG(import_date, 999) OVER (ORDER BY import_date)
        )) as time_for_1000
    FROM florida_parcels
    WHERE import_date > NOW() - INTERVAL '24 hours'
    ORDER BY import_date DESC
    LIMIT 1
)
SELECT 
    CASE 
        WHEN time_for_1000 IS NOT NULL 
        THEN ROUND(1000.0 / time_for_1000, 2)
        ELSE 0
    END as current_records_per_second,
    records_per_1000 as recent_batch_size
FROM recent_imports;

-- 13. ESTIMATED COMPLETION TIME
SELECT 
    'COMPLETION ESTIMATE' as section,
    '===================' as divider;

WITH import_stats AS (
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE WHEN import_date > NOW() - INTERVAL '1 hour' THEN 1 END) as recent_imports,
        EXTRACT(EPOCH FROM INTERVAL '1 hour') as seconds_in_hour
    FROM florida_parcels
)
SELECT 
    total_records,
    recent_imports,
    CASE 
        WHEN recent_imports > 0 
        THEN ROUND(recent_imports / seconds_in_hour, 4)
        ELSE 0
    END as current_rate_per_second,
    CASE 
        WHEN recent_imports > 0 
        THEN '~' || ROUND((1000000 - total_records) / (recent_imports / seconds_in_hour / 3600), 1) || ' hours'
        ELSE 'Cannot estimate - no recent imports'
    END as estimated_time_to_1M_records
FROM import_stats;

-- 14. SAMPLE RECENT RECORDS
SELECT 
    'SAMPLE RECENT DATA' as section,
    '==================' as divider;

SELECT 
    parcel_id,
    owner_name,
    phy_addr1,
    phy_city,
    just_value,
    data_source,
    import_date
FROM florida_parcels
WHERE import_date IS NOT NULL
ORDER BY import_date DESC
LIMIT 10;