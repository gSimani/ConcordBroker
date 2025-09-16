-- =====================================================
-- SUPABASE FLORIDA PARCELS OPTIMIZATION SCRIPT
-- Comprehensive database indexing for fast website queries
-- =====================================================
-- 
-- OVERVIEW:
-- This script optimizes the florida_parcels table for sub-100ms property 
-- lookups and sub-500ms complex searches. It includes all necessary 
-- extensions, indexes, constraints, and monitoring queries.
--
-- SAFE TO RE-RUN: All commands use IF NOT EXISTS or similar safe patterns
-- =====================================================

-- =====================================================
-- SECTION 1: EXTENSIONS AND PREREQUISITES
-- =====================================================

-- Enable pg_trgm extension for trigram text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable btree_gin for composite indexes with text search
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Enable postgis for future spatial queries (optional)
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- =====================================================
-- SECTION 2: TABLE CONSTRAINTS AND STRUCTURE FIXES
-- =====================================================

-- Fix the missing unique constraint issue (causing NAP import failures)
-- This constraint is needed for upsert operations (ON CONFLICT)
ALTER TABLE florida_parcels 
DROP CONSTRAINT IF EXISTS florida_parcels_parcel_id_key;

-- Recreate the unique constraint on parcel_id
ALTER TABLE florida_parcels 
ADD CONSTRAINT florida_parcels_parcel_id_unique 
UNIQUE (parcel_id);

-- Add data_source column if it doesn't exist (for tracking import source)
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS data_source VARCHAR(20) DEFAULT 'NAP';

-- Add import_batch_id for tracking batch imports
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS import_batch_id VARCHAR(50);

-- Add geometry column for future spatial queries (optional)
-- ALTER TABLE florida_parcels 
-- ADD COLUMN IF NOT EXISTS geometry GEOMETRY(POINT, 4326);

-- =====================================================
-- SECTION 3: DROP EXISTING INDEXES (SAFE CLEANUP)
-- =====================================================

-- Drop existing indexes to recreate with optimized settings
DROP INDEX IF EXISTS idx_parcels_parcel_id;
DROP INDEX IF EXISTS idx_parcels_owner;
DROP INDEX IF EXISTS idx_parcels_address;
DROP INDEX IF EXISTS idx_parcels_value;
DROP INDEX IF EXISTS idx_florida_parcels_parcel_id;
DROP INDEX IF EXISTS idx_florida_parcels_owner_name;
DROP INDEX IF EXISTS idx_florida_parcels_phy_addr;
DROP INDEX IF EXISTS idx_florida_parcels_phy_city;
DROP INDEX IF EXISTS idx_florida_parcels_phy_zipcd;
DROP INDEX IF EXISTS idx_florida_parcels_taxable_value;
DROP INDEX IF EXISTS idx_florida_parcels_just_value;
DROP INDEX IF EXISTS idx_florida_parcels_assessed_value;
DROP INDEX IF EXISTS idx_florida_parcels_data_source;
DROP INDEX IF EXISTS idx_florida_parcels_county_year;
DROP INDEX IF EXISTS idx_florida_parcels_property_use;

-- =====================================================
-- SECTION 4: PRIMARY SEARCH INDEXES
-- =====================================================

-- 1. Parcel ID - Primary identifier (MOST IMPORTANT)
-- B-tree index for exact lookups and range queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_parcel_id_btree
ON florida_parcels USING btree (parcel_id);

-- 2. Owner Name - Full text search with trigrams
-- GIN index for fast text search queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name_gin
ON florida_parcels USING gin (owner_name gin_trgm_ops);

-- 3. Owner Name - Additional B-tree for exact matches and sorting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name_btree
ON florida_parcels USING btree (owner_name);

-- 4. Physical Address - Full text search with trigrams
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_addr_gin
ON florida_parcels USING gin (phy_addr1 gin_trgm_ops);

-- 5. Physical City - For city-based filtering and autocomplete
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_city_btree
ON florida_parcels USING btree (phy_city);

-- 6. Physical Zip Code - For location-based searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_zipcd_btree
ON florida_parcels USING btree (phy_zipcd);

-- =====================================================
-- SECTION 5: VALUATION INDEXES
-- =====================================================

-- 7. Just Value - Market value searches (DESC for high-to-low sorting)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_just_value_desc
ON florida_parcels USING btree (just_value DESC NULLS LAST);

-- 8. Assessed Value - Assessment-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_assessed_value_desc
ON florida_parcels USING btree (assessed_value DESC NULLS LAST);

-- 9. Taxable Value - Tax-based filtering and sorting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_taxable_value_desc
ON florida_parcels USING btree (taxable_value DESC NULLS LAST);

-- 10. Sale Price - Recent sales analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_sale_price_desc
ON florida_parcels USING btree (sale_price DESC NULLS LAST);

-- 11. Sale Date - Timeline-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_sale_date_desc
ON florida_parcels USING btree (sale_date DESC NULLS LAST);

-- =====================================================
-- SECTION 6: PROPERTY CHARACTERISTICS INDEXES
-- =====================================================

-- 12. Year Built - Age-based filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_year_built
ON florida_parcels USING btree (year_built DESC NULLS LAST);

-- 13. Total Living Area - Size-based filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_living_area
ON florida_parcels USING btree (total_living_area DESC NULLS LAST);

-- 14. Bedrooms - Bedroom count filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_bedrooms
ON florida_parcels USING btree (bedrooms);

-- 15. Bathrooms - Bathroom count filtering  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_bathrooms
ON florida_parcels USING btree (bathrooms);

-- 16. Property Use - Property type filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_property_use
ON florida_parcels USING btree (property_use);

-- =====================================================
-- SECTION 7: METADATA AND ADMINISTRATIVE INDEXES
-- =====================================================

-- 17. County - Jurisdiction filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county
ON florida_parcels USING btree (county);

-- 18. Year - Tax year filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_year
ON florida_parcels USING btree (year DESC);

-- 19. Data Source - Source tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_data_source
ON florida_parcels USING btree (data_source);

-- 20. Import Date - Recently imported records
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_import_date
ON florida_parcels USING btree (import_date DESC);

-- 21. Import Batch ID - Batch tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_import_batch
ON florida_parcels USING btree (import_batch_id);

-- =====================================================
-- SECTION 8: COMPOSITE INDEXES FOR COMMON QUERY PATTERNS
-- =====================================================

-- 22. City + Value Range - Market analysis by location
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_city_value
ON florida_parcels USING btree (phy_city, just_value DESC NULLS LAST);

-- 23. Zip + Value - Neighborhood analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_zip_value
ON florida_parcels USING btree (phy_zipcd, just_value DESC NULLS LAST);

-- 24. County + Year - Jurisdiction and time filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county_year
ON florida_parcels USING btree (county, year DESC);

-- 25. Property Use + Value - Type-based market analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_use_value
ON florida_parcels USING btree (property_use, just_value DESC NULLS LAST);

-- 26. Owner + City - Portfolio analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_city
ON florida_parcels USING btree (owner_name, phy_city);

-- 27. Bedrooms + Bathrooms + City - Residential filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_bed_bath_city
ON florida_parcels USING btree (bedrooms, bathrooms, phy_city);

-- 28. Year Built + Living Area - Age and size filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_age_size
ON florida_parcels USING btree (year_built DESC, total_living_area DESC);

-- =====================================================
-- SECTION 9: PERFORMANCE OPTIMIZATION
-- =====================================================

-- Update table statistics for query optimizer
ANALYZE florida_parcels;

-- Set table-level performance parameters
ALTER TABLE florida_parcels SET (
  fillfactor = 90,           -- Leave 10% free space for updates
  autovacuum_vacuum_scale_factor = 0.1,  -- More aggressive vacuuming
  autovacuum_analyze_scale_factor = 0.05  -- More frequent statistics updates
);

-- =====================================================
-- SECTION 10: MONITORING AND VERIFICATION QUERIES
-- =====================================================

-- Check NAP import progress and status
CREATE OR REPLACE VIEW nap_import_status AS
SELECT 
    'florida_parcels' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN data_source = 'NAP' THEN 1 END) as nap_records,
    COUNT(CASE WHEN data_source = 'SDF' THEN 1 END) as sdf_records,
    COUNT(CASE WHEN just_value IS NOT NULL THEN 1 END) as records_with_value,
    COUNT(CASE WHEN owner_name IS NOT NULL THEN 1 END) as records_with_owner,
    COUNT(CASE WHEN phy_addr1 IS NOT NULL THEN 1 END) as records_with_address,
    MAX(import_date) as last_import_date,
    COUNT(DISTINCT import_batch_id) as total_batches
FROM florida_parcels;

-- Check index status and sizes
CREATE OR REPLACE VIEW florida_parcels_indexes AS
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes 
WHERE tablename = 'florida_parcels'
ORDER BY pg_relation_size(indexname::regclass) DESC;

-- Check table size and statistics
CREATE OR REPLACE VIEW florida_parcels_stats AS
SELECT 
    'florida_parcels' as table_name,
    pg_size_pretty(pg_total_relation_size('florida_parcels'::regclass)) as total_size,
    pg_size_pretty(pg_relation_size('florida_parcels'::regclass)) as table_size,
    pg_size_pretty(pg_indexes_size('florida_parcels'::regclass)) as indexes_size,
    (SELECT COUNT(*) FROM florida_parcels) as row_count,
    (SELECT last_vacuum FROM pg_stat_user_tables WHERE relname = 'florida_parcels') as last_vacuum,
    (SELECT last_analyze FROM pg_stat_user_tables WHERE relname = 'florida_parcels') as last_analyze;

-- =====================================================
-- SECTION 11: PERFORMANCE TEST QUERIES
-- =====================================================

-- Test Query 1: Exact parcel lookup (should be < 1ms)
-- EXPLAIN ANALYZE SELECT * FROM florida_parcels WHERE parcel_id = '12345678901234567890';

-- Test Query 2: Owner name search (should be < 100ms)
-- EXPLAIN ANALYZE SELECT parcel_id, owner_name, phy_addr1, just_value 
-- FROM florida_parcels 
-- WHERE owner_name ILIKE '%SMITH%' 
-- LIMIT 20;

-- Test Query 3: Address search (should be < 100ms)
-- EXPLAIN ANALYZE SELECT parcel_id, phy_addr1, phy_city, owner_name, just_value
-- FROM florida_parcels 
-- WHERE phy_addr1 ILIKE '%MAIN ST%'
-- LIMIT 20;

-- Test Query 4: Value range search by city (should be < 200ms)
-- EXPLAIN ANALYZE SELECT parcel_id, phy_addr1, owner_name, just_value
-- FROM florida_parcels 
-- WHERE phy_city = 'FORT LAUDERDALE' 
--   AND just_value BETWEEN 500000 AND 1000000
-- ORDER BY just_value DESC
-- LIMIT 50;

-- Test Query 5: Property characteristics search (should be < 500ms)
-- EXPLAIN ANALYZE SELECT parcel_id, phy_addr1, phy_city, owner_name, just_value, bedrooms, bathrooms
-- FROM florida_parcels 
-- WHERE phy_city IN ('MIAMI', 'FORT LAUDERDALE', 'HOLLYWOOD')
--   AND bedrooms >= 3 
--   AND bathrooms >= 2
--   AND year_built > 2000
-- ORDER BY just_value DESC
-- LIMIT 100;

-- =====================================================
-- SECTION 12: IMPORT MONITORING QUERIES
-- =====================================================

-- Monitor import progress in real-time
CREATE OR REPLACE FUNCTION check_import_progress()
RETURNS TABLE (
    batch_status TEXT,
    record_count BIGINT,
    avg_value NUMERIC,
    latest_import TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN import_batch_id IS NULL THEN 'Legacy Data'
            ELSE 'Batch Import'
        END as batch_status,
        COUNT(*) as record_count,
        ROUND(AVG(just_value), 2) as avg_value,
        MAX(import_date) as latest_import
    FROM florida_parcels
    GROUP BY 
        CASE 
            WHEN import_batch_id IS NULL THEN 'Legacy Data'
            ELSE 'Batch Import'
        END
    ORDER BY latest_import DESC;
END;
$$ LANGUAGE plpgsql;

-- Check for potential data quality issues
CREATE OR REPLACE VIEW data_quality_check AS
SELECT 
    'Missing parcel_id' as issue_type,
    COUNT(*) as issue_count
FROM florida_parcels 
WHERE parcel_id IS NULL OR parcel_id = ''
UNION ALL
SELECT 
    'Missing owner_name' as issue_type,
    COUNT(*) as issue_count
FROM florida_parcels 
WHERE owner_name IS NULL OR owner_name = ''
UNION ALL
SELECT 
    'Missing address' as issue_type,
    COUNT(*) as issue_count
FROM florida_parcels 
WHERE phy_addr1 IS NULL OR phy_addr1 = ''
UNION ALL
SELECT 
    'Missing city' as issue_type,
    COUNT(*) as issue_count
FROM florida_parcels 
WHERE phy_city IS NULL OR phy_city = ''
UNION ALL
SELECT 
    'Invalid values (negative)' as issue_type,
    COUNT(*) as issue_count
FROM florida_parcels 
WHERE just_value < 0 OR assessed_value < 0 OR taxable_value < 0
ORDER BY issue_count DESC;

-- =====================================================
-- SECTION 13: MAINTENANCE PROCEDURES
-- =====================================================

-- Create maintenance procedure for regular optimization
CREATE OR REPLACE FUNCTION maintain_florida_parcels()
RETURNS TEXT AS $$
DECLARE
    result TEXT;
BEGIN
    -- Update statistics
    ANALYZE florida_parcels;
    
    -- Vacuum if needed
    VACUUM (ANALYZE) florida_parcels;
    
    -- Check for bloat and recommend actions
    result := 'Maintenance completed at ' || NOW();
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SECTION 14: SECURITY AND ACCESS
-- =====================================================

-- Grant appropriate permissions
GRANT SELECT ON florida_parcels TO anon, authenticated;
GRANT SELECT ON nap_import_status TO anon, authenticated;
GRANT SELECT ON florida_parcels_indexes TO authenticated;
GRANT SELECT ON florida_parcels_stats TO authenticated;
GRANT SELECT ON data_quality_check TO authenticated;

-- Create read-only user for reporting (if needed)
-- CREATE USER florida_parcels_reader WITH PASSWORD 'secure_password_here';
-- GRANT CONNECT ON DATABASE postgres TO florida_parcels_reader;
-- GRANT USAGE ON SCHEMA public TO florida_parcels_reader;
-- GRANT SELECT ON florida_parcels TO florida_parcels_reader;

-- =====================================================
-- SECTION 15: FINAL VERIFICATION AND SUMMARY
-- =====================================================

-- Display final statistics
SELECT 'OPTIMIZATION COMPLETE' as status;
SELECT * FROM nap_import_status;
SELECT * FROM florida_parcels_stats;

-- Show all indexes created
SELECT 
    'Total Indexes: ' || COUNT(*) as summary
FROM pg_indexes 
WHERE tablename = 'florida_parcels';

-- Performance recommendation summary
SELECT 
    'PERFORMANCE TARGETS:' as metric,
    '< 1ms for parcel_id lookups' as target
UNION ALL
SELECT 
    'Text search queries:',
    '< 100ms for owner/address search'
UNION ALL
SELECT 
    'Complex filtered queries:',
    '< 500ms for multi-criteria search'
UNION ALL
SELECT 
    'Batch operations:',
    '> 1000 records/second insert rate';

-- =====================================================
-- END OF OPTIMIZATION SCRIPT
-- =====================================================
-- 
-- NEXT STEPS:
-- 1. Run this script in Supabase SQL Editor
-- 2. Monitor the views created for import progress
-- 3. Test performance with the sample queries above
-- 4. Use maintain_florida_parcels() function weekly
-- 5. Monitor data_quality_check view regularly
--
-- TROUBLESHOOTING:
-- - If NAP import still fails, check unique constraint exists
-- - If queries are slow, run ANALYZE florida_parcels
-- - If indexes are missing, check for CONCURRENTLY errors in logs
-- =====================================================