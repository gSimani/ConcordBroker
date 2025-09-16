-- Property Search Database Optimization
-- Creates optimized indexes for fast property filtering
-- Covers Min Value to Sub-Usage Code filters and beyond

-- =====================================================
-- PROPERTY VALUE INDEXES (Most important for filtering)
-- =====================================================

-- Primary value index for min/max value filters
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_just_value
ON florida_parcels (just_value)
WHERE just_value IS NOT NULL AND just_value > 0;

-- Assessed value index for assessment filters
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_assessed_value
ON florida_parcels (assessed_value)
WHERE assessed_value IS NOT NULL AND assessed_value > 0;

-- Combined value and location index (very common filter combination)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_value_county
ON florida_parcels (county, just_value)
WHERE just_value IS NOT NULL AND just_value > 0;

-- =====================================================
-- SIZE AND SQUARE FOOTAGE INDEXES
-- =====================================================

-- Building square footage index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_building_sqft
ON florida_parcels (building_sqft)
WHERE building_sqft IS NOT NULL AND building_sqft > 0;

-- Land square footage index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_land_sqft
ON florida_parcels (land_sqft)
WHERE land_sqft IS NOT NULL AND land_sqft > 0;

-- Combined size index for range queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_sqft_range
ON florida_parcels (building_sqft, land_sqft)
WHERE building_sqft IS NOT NULL AND land_sqft IS NOT NULL;

-- =====================================================
-- PROPERTY TYPE AND USE CODE INDEXES
-- =====================================================

-- Property use code index (essential for type filtering)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_use_code
ON florida_parcels (property_use_code)
WHERE property_use_code IS NOT NULL;

-- Sub-usage code index (final filter in the range)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_sub_usage_code
ON florida_parcels (sub_usage_code)
WHERE sub_usage_code IS NOT NULL;

-- Combined property type index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_type_codes
ON florida_parcels (property_use_code, sub_usage_code)
WHERE property_use_code IS NOT NULL;

-- =====================================================
-- LOCATION-BASED INDEXES
-- =====================================================

-- County index (most common location filter)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_county
ON florida_parcels (UPPER(county));

-- City index with case-insensitive search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_city
ON florida_parcels (UPPER(city))
WHERE city IS NOT NULL;

-- ZIP code index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_zip
ON florida_parcels (zip_code)
WHERE zip_code IS NOT NULL;

-- Combined location index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_location
ON florida_parcels (county, city, zip_code);

-- =====================================================
-- TEMPORAL INDEXES (Year Built, Sale Dates)
-- =====================================================

-- Year built index for age filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_year_built
ON florida_parcels (year_built)
WHERE year_built IS NOT NULL AND year_built > 1800;

-- Sale date index for recent sales
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_sale_date
ON florida_parcels (sale_date)
WHERE sale_date IS NOT NULL;

-- Combined year and value index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_year_value
ON florida_parcels (year_built, just_value)
WHERE year_built IS NOT NULL AND just_value IS NOT NULL;

-- =====================================================
-- COMPOSITE INDEXES FOR COMMON FILTER COMBINATIONS
-- =====================================================

-- Most common search: County + Value Range + Property Type
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_common_search
ON florida_parcels (county, property_use_code, just_value)
WHERE county IS NOT NULL AND property_use_code IS NOT NULL AND just_value > 0;

-- Size and value combination
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_size_value
ON florida_parcels (building_sqft, just_value)
WHERE building_sqft IS NOT NULL AND just_value IS NOT NULL;

-- Location and type combination
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_location_type
ON florida_parcels (county, city, property_use_code)
WHERE county IS NOT NULL AND property_use_code IS NOT NULL;

-- =====================================================
-- PARTIAL INDEXES FOR SPECIFIC SCENARIOS
-- =====================================================

-- High-value properties index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_high_value
ON florida_parcels (just_value, building_sqft, county)
WHERE just_value >= 500000;

-- Recently built properties
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_recent
ON florida_parcels (year_built, just_value, county)
WHERE year_built >= 2000;

-- Large properties index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_large
ON florida_parcels (building_sqft, land_sqft, just_value)
WHERE building_sqft >= 2000 OR land_sqft >= 10000;

-- =====================================================
-- BOOLEAN AND SPECIAL FEATURE INDEXES
-- =====================================================

-- Tax exempt properties
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_tax_exempt
ON florida_parcels (tax_exempt, county)
WHERE tax_exempt IS NOT NULL;

-- Properties with pools (if column exists)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_pool
-- ON florida_parcels (pool, county)
-- WHERE pool = true;

-- Waterfront properties (if column exists)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_waterfront
-- ON florida_parcels (waterfront, county)
-- WHERE waterfront = true;

-- =====================================================
-- TEXT SEARCH INDEXES FOR ADDRESSES AND NAMES
-- =====================================================

-- Owner name search index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_owner_name
ON florida_parcels USING gin(to_tsvector('english', owner_name))
WHERE owner_name IS NOT NULL;

-- Address search index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_address
ON florida_parcels USING gin(to_tsvector('english', phy_addr1 || ' ' || COALESCE(phy_addr2, '')))
WHERE phy_addr1 IS NOT NULL;

-- =====================================================
-- COVERING INDEXES FOR SELECT OPTIMIZATION
-- =====================================================

-- Covering index for basic property information
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_covering_basic
ON florida_parcels (county, property_use_code, just_value)
INCLUDE (parcel_id, owner_name, phy_addr1, city, building_sqft, year_built);

-- Covering index for detailed property search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_covering_detailed
ON florida_parcels (just_value, county)
INCLUDE (parcel_id, owner_name, phy_addr1, phy_addr2, city, state, zip_code,
         assessed_value, land_value, building_value, land_sqft, building_sqft,
         year_built, property_use_code, sub_usage_code, sale_date, sale_price);

-- =====================================================
-- STATISTICS UPDATE FOR QUERY OPTIMIZATION
-- =====================================================

-- Update table statistics for better query planning
ANALYZE florida_parcels;

-- Set statistics targets for frequently filtered columns
ALTER TABLE florida_parcels ALTER COLUMN just_value SET STATISTICS 1000;
ALTER TABLE florida_parcels ALTER COLUMN county SET STATISTICS 1000;
ALTER TABLE florida_parcels ALTER COLUMN property_use_code SET STATISTICS 500;
ALTER TABLE florida_parcels ALTER COLUMN building_sqft SET STATISTICS 500;
ALTER TABLE florida_parcels ALTER COLUMN year_built SET STATISTICS 500;

-- =====================================================
-- QUERY OPTIMIZATION SETTINGS
-- =====================================================

-- Ensure proper query planning for range queries
SET work_mem = '256MB';
SET random_page_cost = 1.1;
SET effective_cache_size = '4GB';

-- =====================================================
-- INDEX MONITORING QUERIES
-- =====================================================

-- Query to check index usage
-- SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
-- FROM pg_stat_user_indexes
-- WHERE tablename = 'florida_parcels'
-- ORDER BY idx_scan DESC;

-- Query to check index sizes
-- SELECT schemaname, tablename, indexname,
--        pg_size_pretty(pg_relation_size(indexrelid)) as size
-- FROM pg_stat_user_indexes
-- WHERE tablename = 'florida_parcels'
-- ORDER BY pg_relation_size(indexrelid) DESC;

-- =====================================================
-- MAINTENANCE RECOMMENDATIONS
-- =====================================================

-- Regular maintenance commands (run periodically)
-- REINDEX TABLE florida_parcels; -- Run monthly
-- VACUUM ANALYZE florida_parcels; -- Run weekly
--
-- Monitor slow queries:
-- SELECT query, calls, total_time, mean_time
-- FROM pg_stat_statements
-- WHERE query LIKE '%florida_parcels%'
-- ORDER BY total_time DESC LIMIT 10;

-- =====================================================
-- PERFORMANCE TESTING QUERIES
-- =====================================================

-- Test queries to verify index effectiveness:

-- 1. Value range query (should use idx_properties_just_value)
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT * FROM florida_parcels
-- WHERE just_value BETWEEN 200000 AND 500000
-- LIMIT 100;

-- 2. Location + value query (should use idx_properties_value_county)
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT * FROM florida_parcels
-- WHERE county = 'BROWARD' AND just_value BETWEEN 300000 AND 600000
-- LIMIT 100;

-- 3. Property type query (should use idx_properties_use_code)
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT * FROM florida_parcels
-- WHERE property_use_code = '01' AND sub_usage_code = '00'
-- LIMIT 100;

-- 4. Complex multi-filter query (should use idx_properties_common_search)
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT * FROM florida_parcels
-- WHERE county = 'BROWARD'
--   AND property_use_code = '01'
--   AND just_value BETWEEN 250000 AND 750000
--   AND building_sqft >= 1500
-- LIMIT 100;

-- =====================================================
-- SUCCESS VERIFICATION
-- =====================================================

-- Verify all indexes were created successfully
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'florida_parcels'
AND indexname LIKE 'idx_properties_%'
ORDER BY indexname;

COMMENT ON TABLE florida_parcels IS 'Optimized for property search with Min Value to Sub-Usage Code filters';

-- End of optimization script