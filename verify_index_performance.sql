-- ============================================================================
-- INDEX PERFORMANCE VERIFICATION SCRIPT
-- ============================================================================
--
-- PURPOSE: Verify that newly created indexes are being used correctly
-- USAGE: Run in Supabase SQL Editor or via psql
--
-- Expected: All queries should show "Index Scan" or "Bitmap Index Scan"
-- Bad signs: "Seq Scan" on large tables means index not being used
-- ============================================================================

\timing on

\echo '============================================================================'
\echo 'INDEX PERFORMANCE VERIFICATION'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- TEST 1: florida_parcels - County + Value Range
-- ============================================================================

\echo 'TEST 1: County + Value Range Query'
\echo 'Expected: Index Scan using idx_parcels_county_just_value'
\echo ''

EXPLAIN ANALYZE
SELECT parcel_id, phy_addr1, phy_city, county, just_value, owner_name
FROM public.florida_parcels
WHERE county = 'MIAMI-DADE'
  AND just_value BETWEEN 500000 AND 1000000
ORDER BY just_value DESC
LIMIT 100;

\echo ''
\echo '============================================================================'

-- ============================================================================
-- TEST 2: florida_parcels - Owner Name Contains
-- ============================================================================

\echo ''
\echo 'TEST 2: Owner Name Contains Query (ILIKE)'
\echo 'Expected: Bitmap Index Scan using idx_parcels_owner_name_trgm'
\echo ''

EXPLAIN ANALYZE
SELECT parcel_id, owner_name, phy_addr1, phy_city, just_value
FROM public.florida_parcels
WHERE owner_name ILIKE '%LLC%'
ORDER BY owner_name
LIMIT 50;

\echo ''
\echo '============================================================================'

-- ============================================================================
-- TEST 3: florida_parcels - Address Prefix (Autocomplete)
-- ============================================================================

\echo ''
\echo 'TEST 3: Address Prefix Search (Autocomplete)'
\echo 'Expected: Index Scan using idx_parcels_phy_addr1_low'
\echo ''

EXPLAIN ANALYZE
SELECT parcel_id, phy_addr1, phy_city, phy_zipcd
FROM public.florida_parcels
WHERE lower(phy_addr1) >= lower('123 MAIN')
  AND lower(phy_addr1) < lower('123 MAIN' || 'z')
ORDER BY phy_addr1
LIMIT 10;

\echo ''
\echo '============================================================================'

-- ============================================================================
-- TEST 4: florida_parcels - City Search
-- ============================================================================

\echo ''
\echo 'TEST 4: City Search (Trigram)'
\echo 'Expected: Bitmap Index Scan using idx_parcels_phy_city_trgm'
\echo ''

EXPLAIN ANALYZE
SELECT parcel_id, phy_addr1, phy_city, county, just_value
FROM public.florida_parcels
WHERE phy_city ILIKE '%MIAMI%'
ORDER BY phy_city
LIMIT 50;

\echo ''
\echo '============================================================================'

-- ============================================================================
-- TEST 5: property_sales_history - Parcel Sales History
-- ============================================================================

\echo ''
\echo 'TEST 5: Sales History by Parcel ID'
\echo 'Expected: Index Scan using idx_sales_parcel_id_sale_date_desc'
\echo ''

EXPLAIN ANALYZE
SELECT parcel_id, sale_date, sale_price, quality_code, or_book, or_page
FROM public.property_sales_history
WHERE parcel_id = '514228131130'  -- Example parcel with known sales
ORDER BY sale_date DESC
LIMIT 10;

\echo ''
\echo '============================================================================'

-- ============================================================================
-- TEST 6: property_sales_history - Qualified Sales Filter
-- ============================================================================

\echo ''
\echo 'TEST 6: Qualified Sales with Price Filter'
\echo 'Expected: Bitmap Index Scan using idx_sales_quality_price'
\echo ''

EXPLAIN ANALYZE
SELECT parcel_id, sale_date, sale_price, quality_code
FROM public.property_sales_history
WHERE quality_code = 'Q'
  AND sale_price > 10000000  -- $100,000 (stored in cents)
ORDER BY sale_price DESC
LIMIT 50;

\echo ''
\echo '============================================================================'

-- ============================================================================
-- TEST 7: florida_entities - Business Name Search (Trigram)
-- ============================================================================

\echo ''
\echo 'TEST 7: Entity Business Name Search (Trigram)'
\echo 'Expected: Bitmap Index Scan using idx_entities_business_name_trgm'
\echo 'NOTE: Only run this after optimize_florida_entities_indexes.sql completes'
\echo ''

EXPLAIN ANALYZE
SELECT entity_id, business_name, entity_status, entity_type
FROM public.florida_entities
WHERE business_name ILIKE '%HOLDINGS%'
ORDER BY similarity(business_name, 'HOLDINGS') DESC
LIMIT 50;

\echo ''
\echo '============================================================================'

-- ============================================================================
-- TEST 8: florida_entities - Full-Text Search
-- ============================================================================

\echo ''
\echo 'TEST 8: Entity Full-Text Search'
\echo 'Expected: Bitmap Index Scan using idx_entities_business_name_fts or idx_entities_business_name_tsv'
\echo 'NOTE: Only run this after optimize_florida_entities_indexes.sql completes'
\echo ''

EXPLAIN ANALYZE
SELECT entity_id, business_name, entity_status
FROM public.florida_entities
WHERE to_tsvector('simple', coalesce(business_name, ''))
      @@ plainto_tsquery('simple', 'FLORIDA CORPORATION')
LIMIT 50;

\echo ''
\echo '============================================================================'

-- ============================================================================
-- TEST 9: Complex Multi-Filter Query (Real-World Property Search)
-- ============================================================================

\echo ''
\echo 'TEST 9: Complex Property Search (Multiple Filters)'
\echo 'Expected: Multiple index usage with Bitmap AND/OR operations'
\echo ''

EXPLAIN ANALYZE
SELECT parcel_id, phy_addr1, phy_city, county, owner_name, just_value, land_sqft
FROM public.florida_parcels
WHERE county = 'BROWARD'
  AND just_value BETWEEN 300000 AND 800000
  AND phy_city ILIKE '%FORT LAUDERDALE%'
  AND land_sqft > 5000
ORDER BY just_value DESC
LIMIT 100;

\echo ''
\echo '============================================================================'

-- ============================================================================
-- TEST 10: Parcel with Sales Join (Tests FK relationship)
-- ============================================================================

\echo ''
\echo 'TEST 10: Property with Sales History (JOIN)'
\echo 'Expected: Index scans on both tables'
\echo ''

EXPLAIN ANALYZE
SELECT
  fp.parcel_id,
  fp.phy_addr1,
  fp.owner_name,
  fp.just_value,
  psh.sale_date,
  psh.sale_price,
  psh.quality_code
FROM public.florida_parcels fp
LEFT JOIN public.property_sales_history psh ON psh.parcel_id = fp.parcel_id
WHERE fp.county = 'MIAMI-DADE'
  AND fp.just_value > 1000000
ORDER BY psh.sale_date DESC NULLS LAST
LIMIT 50;

\echo ''
\echo '============================================================================'
\echo 'VERIFICATION COMPLETE'
\echo '============================================================================'
\echo ''
\echo 'INTERPRETING RESULTS:'
\echo '- "Index Scan" or "Bitmap Index Scan" = GOOD (index is being used)'
\echo '- "Seq Scan" on large tables = BAD (index not being used, check query pattern)'
\echo '- Execution time <100ms for most queries = EXCELLENT'
\echo '- Execution time >1s = Review query plan and consider additional indexes'
\echo ''
\echo 'COMMON ISSUES:'
\echo '1. Wrong case: Use lower() on both sides for case-insensitive exact match'
\echo '2. Wrong operator: ILIKE needs trigram index, = needs btree'
\echo '3. Type mismatch: Ensure filter value types match column types'
\echo '4. Missing ANALYZE: Run ANALYZE table_name to update statistics'
\echo ''

-- ============================================================================
-- QUICK INDEX HEALTH CHECK
-- ============================================================================

\echo '============================================================================'
\echo 'INDEX HEALTH CHECK'
\echo '============================================================================'
\echo ''

-- Show all indexes on critical tables
\echo 'Indexes on florida_parcels:'
SELECT
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size,
  idx_scan AS scans,
  idx_tup_read AS tuples_read,
  idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename = 'florida_parcels'
ORDER BY idx_scan DESC;

\echo ''
\echo 'Indexes on property_sales_history:'
SELECT
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size,
  idx_scan AS scans,
  idx_tup_read AS tuples_read,
  idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename = 'property_sales_history'
ORDER BY idx_scan DESC;

\echo ''
\echo 'Indexes on florida_entities:'
SELECT
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size,
  idx_scan AS scans,
  idx_tup_read AS tuples_read,
  idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename = 'florida_entities'
ORDER BY idx_scan DESC;

\echo ''
\echo '============================================================================'
\echo 'UNUSED INDEXES (Consider dropping if idx_scan = 0 after 1 week)'
\echo '============================================================================'
\echo ''

SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size,
  idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND idx_scan = 0
  AND indexrelid::regclass::text NOT LIKE '%_pkey'  -- Exclude primary keys
ORDER BY pg_relation_size(indexrelid) DESC;

\echo ''
\echo 'NOTE: Zero scans may be normal for newly created indexes.'
\echo 'Re-run this check after 1 week of production usage.'
\echo ''
