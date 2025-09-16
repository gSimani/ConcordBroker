-- ============================================================================
-- SUPABASE VERIFICATION QUERIES FOR CONCORDBROKER
-- Run these queries in Supabase SQL Editor to verify data integrity
-- ============================================================================

-- ============================================================================
-- 1. CHECK TABLE EXISTENCE AND STRUCTURE
-- ============================================================================

-- List all property-related tables
SELECT 
    table_name,
    COUNT(*) as column_count
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name IN (
        'property_assessments',
        'property_owners', 
        'property_sales',
        'nav_summaries',
        'nav_details',
        'properties_master',
        'sunbiz_corporate',
        'property_corporate_links'
    )
GROUP BY table_name
ORDER BY table_name;

-- ============================================================================
-- 2. DATA COMPLETENESS CHECK
-- ============================================================================

-- Check record counts for each table
SELECT 
    'property_assessments' as table_name, 
    COUNT(*) as record_count,
    COUNT(DISTINCT county_code) as counties,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record
FROM property_assessments
UNION ALL
SELECT 
    'property_owners',
    COUNT(*),
    COUNT(DISTINCT county_code),
    MIN(created_at),
    MAX(created_at)
FROM property_owners
UNION ALL
SELECT 
    'property_sales',
    COUNT(*),
    COUNT(DISTINCT county_code),
    MIN(created_at),
    MAX(created_at)
FROM property_sales
UNION ALL
SELECT 
    'nav_summaries',
    COUNT(*),
    COUNT(DISTINCT county_code),
    MIN(created_at),
    MAX(created_at)
FROM nav_summaries
UNION ALL
SELECT 
    'nav_details',
    COUNT(*),
    COUNT(DISTINCT county_code),
    MIN(created_at),
    MAX(created_at)
FROM nav_details;

-- ============================================================================
-- 3. DATA QUALITY METRICS
-- ============================================================================

-- Check data quality by county
SELECT 
    county_name,
    county_code,
    COUNT(*) as total_properties,
    COUNT(owner_name) as has_owner,
    COUNT(property_address) as has_address,
    COUNT(taxable_value) as has_value,
    ROUND(AVG(taxable_value), 2) as avg_value,
    MIN(taxable_value) as min_value,
    MAX(taxable_value) as max_value,
    ROUND(100.0 * COUNT(owner_name) / COUNT(*), 2) as owner_completeness_pct,
    ROUND(100.0 * COUNT(taxable_value) / COUNT(*), 2) as value_completeness_pct
FROM property_assessments
GROUP BY county_name, county_code
ORDER BY total_properties DESC;

-- ============================================================================
-- 4. SALES DATA VERIFICATION
-- ============================================================================

-- Recent sales analysis
SELECT 
    DATE_TRUNC('month', sale_date) as sale_month,
    COUNT(*) as sale_count,
    ROUND(AVG(sale_price), 2) as avg_price,
    ROUND(MEDIAN(sale_price), 2) as median_price,
    MIN(sale_price) as min_price,
    MAX(sale_price) as max_price,
    COUNT(DISTINCT county_code) as counties_with_sales
FROM property_sales
WHERE sale_date >= CURRENT_DATE - INTERVAL '12 months'
    AND sale_price > 0
    AND qualified_sale = true
GROUP BY DATE_TRUNC('month', sale_date)
ORDER BY sale_month DESC;

-- ============================================================================
-- 5. NAV ASSESSMENT VERIFICATION
-- ============================================================================

-- NAV assessment summary by county
SELECT 
    ns.county_name,
    COUNT(DISTINCT ns.parcel_id) as parcels_with_nav,
    SUM(ns.num_assessments) as total_assessment_count,
    ROUND(AVG(ns.total_assessments), 2) as avg_nav_amount,
    ROUND(SUM(ns.total_assessments), 2) as total_nav_collected,
    MIN(ns.total_assessments) as min_nav,
    MAX(ns.total_assessments) as max_nav
FROM nav_summaries ns
GROUP BY ns.county_name
ORDER BY total_nav_collected DESC;

-- Top NAV assessment types
SELECT 
    levy_name,
    COUNT(DISTINCT parcel_id) as affected_properties,
    COUNT(*) as assessment_count,
    ROUND(AVG(assessment_amount), 2) as avg_amount,
    ROUND(SUM(assessment_amount), 2) as total_amount
FROM nav_details
GROUP BY levy_name
ORDER BY total_amount DESC
LIMIT 20;

-- ============================================================================
-- 6. OWNER TYPE ANALYSIS
-- ============================================================================

-- Property ownership by type
SELECT 
    owner_type,
    COUNT(*) as property_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage,
    ROUND(AVG(ownership_percentage), 2) as avg_ownership_pct
FROM property_owners
WHERE owner_type IS NOT NULL
GROUP BY owner_type
ORDER BY property_count DESC;

-- Corporate-owned properties
SELECT 
    po.owner_type,
    COUNT(DISTINCT po.parcel_id) as property_count,
    ROUND(AVG(pa.taxable_value), 2) as avg_value,
    ROUND(SUM(pa.taxable_value), 2) as total_value
FROM property_owners po
JOIN property_assessments pa ON po.parcel_id = pa.parcel_id
WHERE po.owner_type IN ('LLC', 'Corporation', 'LP', 'Trust')
GROUP BY po.owner_type
ORDER BY total_value DESC;

-- ============================================================================
-- 7. MASTER TABLE VERIFICATION
-- ============================================================================

-- Check master table population
SELECT 
    COUNT(*) as total_properties,
    COUNT(owner_name) as has_owner,
    COUNT(last_sale_date) as has_sale,
    COUNT(nav_total) as has_nav,
    COUNT(CASE WHEN has_corporate_owner THEN 1 END) as corporate_owned,
    ROUND(AVG(data_quality_score), 2) as avg_quality_score,
    ROUND(AVG(investment_score), 2) as avg_investment_score
FROM properties_master;

-- Top properties by investment score
SELECT 
    parcel_id,
    property_address,
    property_city,
    owner_name,
    taxable_value,
    last_sale_price,
    last_sale_date,
    investment_score,
    data_quality_score
FROM properties_master
WHERE investment_score IS NOT NULL
ORDER BY investment_score DESC
LIMIT 20;

-- ============================================================================
-- 8. CROSS-TABLE CONSISTENCY
-- ============================================================================

-- Check for orphaned records
SELECT 
    'Sales without assessment' as issue,
    COUNT(*) as count
FROM property_sales ps
WHERE NOT EXISTS (
    SELECT 1 FROM property_assessments pa 
    WHERE pa.parcel_id = ps.parcel_id
)
UNION ALL
SELECT 
    'NAV without assessment',
    COUNT(*)
FROM nav_summaries ns
WHERE NOT EXISTS (
    SELECT 1 FROM property_assessments pa 
    WHERE pa.parcel_id = ns.parcel_id
)
UNION ALL
SELECT 
    'Owners without assessment',
    COUNT(*)
FROM property_owners po
WHERE NOT EXISTS (
    SELECT 1 FROM property_assessments pa 
    WHERE pa.parcel_id = po.parcel_id
);

-- ============================================================================
-- 9. WEBSITE READINESS CHECK
-- ============================================================================

-- Check if data is ready for website queries
WITH website_check AS (
    SELECT 
        CASE 
            WHEN COUNT(*) > 0 THEN 'YES' 
            ELSE 'NO' 
        END as has_data,
        COUNT(*) as record_count
    FROM properties_master
    WHERE data_quality_score >= 50
)
SELECT 
    'Properties Ready for Display' as check_item,
    has_data as status,
    record_count as count
FROM website_check
UNION ALL
SELECT 
    'Recent Sales Available',
    CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END,
    COUNT(*)
FROM property_sales
WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
UNION ALL
SELECT 
    'NAV Assessments Loaded',
    CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END,
    COUNT(*)
FROM nav_summaries
UNION ALL
SELECT 
    'Corporate Links Available',
    CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END,
    COUNT(*)
FROM property_corporate_links;

-- ============================================================================
-- 10. SAMPLE PROPERTY QUERY (What website will see)
-- ============================================================================

-- Get complete data for a sample property (like website would)
WITH sample_property AS (
    SELECT parcel_id 
    FROM properties_master 
    WHERE data_quality_score >= 75
    LIMIT 1
)
SELECT 
    pm.*,
    ps.sale_date,
    ps.sale_price,
    ps.buyer_name,
    ps.seller_name,
    ns.total_assessments as nav_total,
    ns.num_assessments as nav_count
FROM properties_master pm
LEFT JOIN property_sales ps ON pm.parcel_id = ps.parcel_id
LEFT JOIN nav_summaries ns ON pm.parcel_id = ns.parcel_id
WHERE pm.parcel_id IN (SELECT parcel_id FROM sample_property);

-- ============================================================================
-- 11. PERFORMANCE CHECK
-- ============================================================================

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND tablename IN ('property_assessments', 'property_sales', 'properties_master')
ORDER BY idx_scan DESC;

-- Check table sizes
SELECT 
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
    pg_size_pretty(pg_relation_size(relid)) as table_size,
    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as indexes_size
FROM pg_stat_user_tables
WHERE schemaname = 'public'
    AND relname IN ('property_assessments', 'property_sales', 'nav_summaries', 'nav_details', 'properties_master')
ORDER BY pg_total_relation_size(relid) DESC;

-- ============================================================================
-- 12. QUICK HEALTH CHECK SUMMARY
-- ============================================================================

-- Overall system health
SELECT 
    'SYSTEM HEALTH CHECK' as report_title,
    CURRENT_TIMESTAMP as check_time,
    (SELECT COUNT(*) FROM property_assessments) as total_properties,
    (SELECT COUNT(*) FROM property_sales) as total_sales,
    (SELECT COUNT(*) FROM nav_summaries) as total_nav_records,
    (SELECT COUNT(DISTINCT county_code) FROM property_assessments) as counties_loaded,
    (SELECT ROUND(AVG(data_quality_score), 2) FROM properties_master) as avg_data_quality,
    CASE 
        WHEN (SELECT COUNT(*) FROM properties_master) > 1000 
        THEN 'READY' 
        ELSE 'NOT READY' 
    END as website_status;

-- ============================================================================
-- END OF VERIFICATION QUERIES
-- 
-- If all checks pass, your database is ready for the website!
-- Expected results:
-- - Multiple counties with data
-- - Thousands of properties loaded
-- - Sales data available
-- - NAV assessments present
-- - Master table populated
-- - Average data quality > 50
-- ============================================================================