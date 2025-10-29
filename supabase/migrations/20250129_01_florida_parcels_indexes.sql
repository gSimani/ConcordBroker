-- =====================================================
-- PHASE 1.1: FLORIDA PARCELS INDEXES
-- Critical performance indexes for property queries
--
-- Estimated time: 30-45 minutes with CONCURRENTLY
-- Impact: 5-50x faster queries
-- Risk: LOW (indexes are additive, don't break existing queries)
--
-- Run in Supabase SQL Editor
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =====================================================
-- Index 1: County + Year (Most Common Filter)
-- Used in: Nearly ALL property queries
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_county_year
  ON florida_parcels(county, year)
  WHERE year = 2025;

COMMENT ON INDEX idx_fp_county_year IS
  'Composite index for county+year filtering - most common query pattern';

-- =====================================================
-- Index 2: Parcel ID (Unique Lookups)
-- Used in: Property detail pages, sales history joins
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_parcel_id
  ON florida_parcels(parcel_id)
  WHERE parcel_id IS NOT NULL;

COMMENT ON INDEX idx_fp_parcel_id IS
  'Single parcel lookups by parcel_id';

-- =====================================================
-- Index 3: Address Prefix Search (Autocomplete)
-- Used in: Autocomplete, address search
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_address_prefix
  ON florida_parcels(LEFT(phy_addr1, 10))
  WHERE phy_addr1 IS NOT NULL;

COMMENT ON INDEX idx_fp_address_prefix IS
  'Prefix index for fast autocomplete on addresses (first 10 chars)';

-- =====================================================
-- Index 4: Address Fuzzy Search (Trigram)
-- Used in: ILIKE searches, fuzzy address matching
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_address_trgm
  ON florida_parcels USING gist(phy_addr1 gist_trgm_ops);

COMMENT ON INDEX idx_fp_address_trgm IS
  'Trigram index for ILIKE searches on addresses';

-- =====================================================
-- Index 5: Owner Name Exact
-- Used in: Owner filters, exact name lookups
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_owner_name
  ON florida_parcels(owner_name)
  WHERE owner_name IS NOT NULL;

COMMENT ON INDEX idx_fp_owner_name IS
  'Exact match index for owner names';

-- =====================================================
-- Index 6: Owner Name Fuzzy (Trigram)
-- Used in: ILIKE searches, owner autocomplete
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_owner_trgm
  ON florida_parcels USING gist(owner_name gist_trgm_ops);

COMMENT ON INDEX idx_fp_owner_trgm IS
  'Trigram index for ILIKE searches on owner names';

-- =====================================================
-- Index 7: City Lookup
-- Used in: City filters, location searches
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_city
  ON florida_parcels(phy_city)
  WHERE phy_city IS NOT NULL;

COMMENT ON INDEX idx_fp_city IS
  'City name lookups and filtering';

-- =====================================================
-- Index 8: Value Range Queries
-- Used in: Min/max value filters
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_just_value
  ON florida_parcels(just_value)
  WHERE just_value IS NOT NULL;

COMMENT ON INDEX idx_fp_just_value IS
  'Property value range queries (just_value)';

-- =====================================================
-- Index 9: Year Built Range Queries
-- Used in: Year built filters
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_year_built
  ON florida_parcels(year_built)
  WHERE year_built IS NOT NULL;

COMMENT ON INDEX idx_fp_year_built IS
  'Year built range queries';

-- =====================================================
-- Index 10: Property Use Filtering
-- Used in: Property type filters
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_property_use
  ON florida_parcels(property_use)
  WHERE property_use IS NOT NULL;

COMMENT ON INDEX idx_fp_property_use IS
  'Property use/type filtering';

-- =====================================================
-- Index 11: Composite for Advanced Filters
-- Used in: Multi-filter queries (county + value + year built)
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fp_county_value_year
  ON florida_parcels(county, just_value, year_built)
  WHERE year = 2025 AND just_value IS NOT NULL;

COMMENT ON INDEX idx_fp_county_value_year IS
  'Composite index for advanced filtering (county + value + year built)';

-- =====================================================
-- VERIFICATION QUERIES
-- Run these to verify indexes were created successfully
-- =====================================================

-- Show all new indexes
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
WHERE tablename = 'florida_parcels'
  AND indexname LIKE 'idx_fp_%'
ORDER BY indexname;

-- Check index usage (run after some queries)
SELECT
  schemaname,
  tablename,
  indexrelname,
  idx_scan as index_scans,
  idx_tup_read as rows_read,
  idx_tup_fetch as rows_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'florida_parcels'
  AND indexrelname LIKE 'idx_fp_%'
ORDER BY idx_scan DESC;

-- Total size of all indexes
SELECT
  pg_size_pretty(SUM(pg_relation_size(indexrelid))) as total_index_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
WHERE tablename = 'florida_parcels'
  AND indexname LIKE 'idx_fp_%';

-- =====================================================
-- EXPECTED RESULTS
-- =====================================================
--
-- After running this script, you should see:
-- - 11 new indexes on florida_parcels
-- - Total index size: ~500-800 MB (depending on data volume)
-- - No errors in execution
--
-- Performance improvements expected:
-- - County searches: 2000ms → 50ms (40x faster)
-- - Address ILIKE: 3000ms → 200ms (15x faster)
-- - Owner ILIKE: 3000ms → 300ms (10x faster)
-- - Multi-filter: 3000ms → 300ms (10x faster)
-- =====================================================
