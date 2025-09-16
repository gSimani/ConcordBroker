-- =====================================================
-- FLORIDA PARCELS PERFORMANCE VERIFICATION SCRIPT
-- Test queries to validate optimization results
-- =====================================================
-- 
-- Run these queries after optimization to ensure performance targets:
-- - Parcel ID lookups: < 1ms
-- - Text searches: < 100ms  
-- - Complex queries: < 500ms
-- =====================================================

-- =====================================================
-- TEST 1: EXACT PARCEL ID LOOKUP (Target: < 1ms)
-- =====================================================
SELECT 'TEST 1: Exact Parcel ID Lookup' as test_name;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    parcel_id,
    owner_name,
    phy_addr1,
    phy_city,
    just_value,
    assessed_value,
    taxable_value,
    year_built,
    total_living_area
FROM florida_parcels 
WHERE parcel_id = (
    SELECT parcel_id 
    FROM florida_parcels 
    WHERE parcel_id IS NOT NULL 
    LIMIT 1
);

-- =====================================================
-- TEST 2: OWNER NAME SEARCH (Target: < 100ms)
-- =====================================================
SELECT 'TEST 2: Owner Name Fuzzy Search' as test_name;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    parcel_id,
    owner_name,
    phy_addr1,
    phy_city,
    just_value
FROM florida_parcels 
WHERE owner_name ILIKE '%SMITH%'
ORDER BY just_value DESC NULLS LAST
LIMIT 20;

-- =====================================================
-- TEST 3: ADDRESS SEARCH (Target: < 100ms)
-- =====================================================
SELECT 'TEST 3: Address Search' as test_name;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    parcel_id,
    phy_addr1,
    phy_city,
    owner_name,
    just_value
FROM florida_parcels 
WHERE phy_addr1 ILIKE '%MAIN%'
ORDER BY just_value DESC NULLS LAST
LIMIT 20;

-- =====================================================
-- TEST 4: CITY AND VALUE RANGE (Target: < 200ms)
-- =====================================================
SELECT 'TEST 4: City and Value Range' as test_name;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    parcel_id,
    phy_addr1,
    owner_name,
    just_value,
    assessed_value
FROM florida_parcels 
WHERE phy_city = (
    SELECT phy_city 
    FROM florida_parcels 
    WHERE phy_city IS NOT NULL 
    GROUP BY phy_city 
    ORDER BY COUNT(*) DESC 
    LIMIT 1
)
AND just_value BETWEEN 100000 AND 500000
ORDER BY just_value DESC
LIMIT 50;

-- =====================================================
-- TEST 5: COMPLEX PROPERTY SEARCH (Target: < 500ms)
-- =====================================================
SELECT 'TEST 5: Complex Property Search' as test_name;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    parcel_id,
    phy_addr1,
    phy_city,
    owner_name,
    just_value,
    year_built,
    total_living_area,
    bedrooms,
    bathrooms
FROM florida_parcels 
WHERE phy_city IN (
    SELECT phy_city 
    FROM florida_parcels 
    WHERE phy_city IS NOT NULL 
    GROUP BY phy_city 
    ORDER BY COUNT(*) DESC 
    LIMIT 5
)
AND bedrooms >= 3 
AND bathrooms >= 2
AND year_built > 1990
AND just_value > 200000
ORDER BY just_value DESC
LIMIT 100;

-- =====================================================
-- TEST 6: PORTFOLIO ANALYSIS (Target: < 300ms)
-- =====================================================
SELECT 'TEST 6: Portfolio Analysis by Owner' as test_name;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    owner_name,
    COUNT(*) as property_count,
    SUM(just_value) as total_value,
    AVG(just_value) as avg_value,
    COUNT(DISTINCT phy_city) as cities,
    MIN(year_built) as oldest_property,
    MAX(year_built) as newest_property
FROM florida_parcels 
WHERE owner_name IS NOT NULL
AND just_value > 0
GROUP BY owner_name
HAVING COUNT(*) >= 5  -- Owners with 5+ properties
ORDER BY total_value DESC
LIMIT 25;

-- =====================================================
-- TEST 7: GEOGRAPHIC VALUE ANALYSIS (Target: < 400ms)
-- =====================================================
SELECT 'TEST 7: Geographic Value Analysis' as test_name;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    phy_city,
    phy_zipcd,
    COUNT(*) as property_count,
    ROUND(AVG(just_value), 0) as avg_value,
    ROUND(MIN(just_value), 0) as min_value,
    ROUND(MAX(just_value), 0) as max_value,
    COUNT(CASE WHEN year_built > 2000 THEN 1 END) as modern_properties,
    COUNT(CASE WHEN bedrooms >= 4 THEN 1 END) as large_properties
FROM florida_parcels 
WHERE phy_city IS NOT NULL
AND phy_zipcd IS NOT NULL
AND just_value > 50000
GROUP BY phy_city, phy_zipcd
HAVING COUNT(*) >= 10  -- Areas with 10+ properties
ORDER BY avg_value DESC
LIMIT 50;

-- =====================================================
-- TEST 8: SALES HISTORY ANALYSIS (Target: < 300ms)
-- =====================================================
SELECT 'TEST 8: Sales History Analysis' as test_name;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    EXTRACT(YEAR FROM sale_date) as sale_year,
    COUNT(*) as sales_count,
    ROUND(AVG(sale_price), 0) as avg_sale_price,
    ROUND(MIN(sale_price), 0) as min_sale_price,
    ROUND(MAX(sale_price), 0) as max_sale_price,
    COUNT(DISTINCT phy_city) as cities_with_sales
FROM florida_parcels 
WHERE sale_date IS NOT NULL
AND sale_price > 0
AND sale_date > '2015-01-01'
GROUP BY EXTRACT(YEAR FROM sale_date)
ORDER BY sale_year DESC;

-- =====================================================
-- TEST 9: PROPERTY TYPE ANALYSIS (Target: < 250ms)
-- =====================================================
SELECT 'TEST 9: Property Type Analysis' as test_name;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    property_use,
    property_use_desc,
    COUNT(*) as property_count,
    ROUND(AVG(just_value), 0) as avg_value,
    ROUND(AVG(total_living_area), 0) as avg_living_area,
    ROUND(AVG(year_built), 0) as avg_year_built,
    COUNT(CASE WHEN pool = true THEN 1 END) as properties_with_pool
FROM florida_parcels 
WHERE property_use IS NOT NULL
AND just_value > 0
GROUP BY property_use, property_use_desc
HAVING COUNT(*) >= 100  -- Property types with 100+ examples
ORDER BY property_count DESC;

-- =====================================================
-- TEST 10: AUTOCOMPLETE SIMULATION (Target: < 50ms)
-- =====================================================
SELECT 'TEST 10: Autocomplete Address Search' as test_name;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT DISTINCT
    phy_addr1,
    phy_city,
    COUNT(*) OVER (PARTITION BY phy_addr1, phy_city) as match_count
FROM florida_parcels 
WHERE phy_addr1 ILIKE '123%'  -- Simulating user typing "123"
AND phy_city IS NOT NULL
ORDER BY match_count DESC, phy_addr1
LIMIT 10;

-- =====================================================
-- PERFORMANCE SUMMARY QUERY
-- =====================================================
SELECT 'PERFORMANCE SUMMARY' as section;

-- Check index usage statistics
SELECT 
    'Index Usage Statistics' as metric_type,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    CASE 
        WHEN idx_scan > 0 
        THEN ROUND(idx_tup_read::NUMERIC / idx_scan, 2)
        ELSE 0
    END as avg_tuples_per_scan
FROM pg_stat_user_indexes 
WHERE schemaname = 'public' 
AND relname = 'florida_parcels'
ORDER BY idx_scan DESC;

-- Check table statistics
SELECT 
    'Table Statistics' as metric_type,
    schemaname,
    relname as table_name,
    seq_scan as sequential_scans,
    seq_tup_read as sequential_tuples_read,
    idx_scan as index_scans,
    idx_tup_fetch as index_tuples_fetched,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables 
WHERE relname = 'florida_parcels';

-- =====================================================
-- BENCHMARK REFERENCE TIMES
-- =====================================================
SELECT 'BENCHMARK TARGETS' as section;

SELECT 
    'Parcel ID Exact Match' as query_type,
    '< 1ms' as target_time,
    'Single record lookup by primary key' as description
UNION ALL
SELECT 
    'Owner Name Search',
    '< 100ms',
    'Text search with ILIKE, 20 results'
UNION ALL
SELECT 
    'Address Search',
    '< 100ms',
    'Address text search, 20 results'
UNION ALL
SELECT 
    'City + Value Range',
    '< 200ms',
    'Filter by city and value range, 50 results'
UNION ALL
SELECT 
    'Complex Property Search',
    '< 500ms',
    'Multi-criteria search with sorting, 100 results'
UNION ALL
SELECT 
    'Portfolio Analysis',
    '< 300ms',
    'Aggregate query with grouping, 25 results'
UNION ALL
SELECT 
    'Geographic Analysis',
    '< 400ms',
    'City/ZIP aggregation with statistics, 50 results'
UNION ALL
SELECT 
    'Sales History',
    '< 300ms',
    'Yearly sales aggregation with date filtering'
UNION ALL
SELECT 
    'Property Type Analysis',
    '< 250ms',
    'Property use aggregation with statistics'
UNION ALL
SELECT 
    'Autocomplete Simulation',
    '< 50ms',
    'Prefix search for address autocomplete, 10 results';

-- =====================================================
-- END OF PERFORMANCE TESTS
-- =====================================================