-- ============================================================================
-- CRITICAL: Performance Indexes for INSTANT Property Search
-- ============================================================================
-- Run this IMMEDIATELY in Supabase SQL Editor:
-- https://app.supabase.com/project/pmispwtdngkcmsrsjwbp/sql
-- ============================================================================

-- Drop old indexes first (if they exist)
DROP INDEX CONCURRENTLY IF EXISTS idx_florida_parcels_fast_search;
DROP INDEX CONCURRENTLY IF EXISTS idx_florida_parcels_county_value;

-- INDEX 1: ULTRA-FAST - Main search query (no filters)
-- Makes initial page load INSTANT (<50ms)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_ultra_fast
ON public.florida_parcels (just_value DESC)
WHERE is_redacted = false AND just_value > 0;

-- INDEX 2: COUNTY + VALUE - For county filtering
-- Makes county searches INSTANT
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county_fast
ON public.florida_parcels (county, just_value DESC)
WHERE is_redacted = false AND just_value > 0;

-- INDEX 3: CITY TEXT SEARCH - For city autocomplete/filtering
-- Enables fast city searches using trigram matching
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_city_trgm
ON public.florida_parcels USING gin (phy_city gin_trgm_ops)
WHERE is_redacted = false AND just_value > 0;

-- INDEX 4: ADDRESS TEXT SEARCH - For address autocomplete/filtering
-- Enables fast address searches using trigram matching
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_addr_trgm
ON public.florida_parcels USING gin (phy_addr1 gin_trgm_ops)
WHERE is_redacted = false AND just_value > 0;

-- INDEX 5: OWNER TEXT SEARCH - For owner autocomplete/filtering
-- Enables fast owner searches using trigram matching
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_trgm
ON public.florida_parcels USING gin (owner_name gin_trgm_ops)
WHERE is_redacted = false AND just_value > 0;

-- INDEX 6: PROPERTY USE - For property type filtering
-- Makes property type filters INSTANT
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_use_value
ON public.florida_parcels (property_use, just_value DESC)
WHERE is_redacted = false AND just_value > 0;

-- INDEX 7: BUILDING SIZE - For building sqft range filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_building_value
ON public.florida_parcels (total_living_area, just_value DESC)
WHERE is_redacted = false AND just_value > 0 AND total_living_area IS NOT NULL;

-- INDEX 8: LAND SIZE - For land sqft range filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_land_value
ON public.florida_parcels (land_sqft, just_value DESC)
WHERE is_redacted = false AND just_value > 0 AND land_sqft IS NOT NULL;

-- INDEX 9: PARCEL LOOKUP - For property detail page
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_parcel_fast
ON public.florida_parcels (parcel_id)
WHERE is_redacted = false;

-- ============================================================================
-- ENABLE TRIGRAM EXTENSION (if not already enabled)
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- VERIFY ALL INDEXES CREATED
-- ============================================================================
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes
WHERE tablename = 'florida_parcels'
  AND indexname LIKE 'idx_florida_parcels_%'
ORDER BY indexname;

-- ============================================================================
-- TEST QUERY PERFORMANCE
-- ============================================================================

-- Test 1: Initial load (should be <50ms)
EXPLAIN ANALYZE
SELECT parcel_id,county,owner_name,phy_addr1,phy_city,phy_zipcd,just_value,taxable_value,land_value,building_value,total_living_area,land_sqft,units,property_use,year_built
FROM public.florida_parcels
WHERE is_redacted = false AND just_value > 0
ORDER BY just_value DESC
LIMIT 20;

-- Test 2: County filter (should be <100ms)
EXPLAIN ANALYZE
SELECT parcel_id,county,owner_name,phy_addr1,phy_city,just_value
FROM public.florida_parcels
WHERE is_redacted = false AND just_value > 0 AND county = 'MIAMI-DADE'
ORDER BY just_value DESC
LIMIT 20;

-- Test 3: City search (should be <200ms)
EXPLAIN ANALYZE
SELECT parcel_id,county,owner_name,phy_addr1,phy_city,just_value
FROM public.florida_parcels
WHERE is_redacted = false AND just_value > 0 AND phy_city ILIKE '%miami%'
ORDER BY just_value DESC
LIMIT 20;

-- Test 4: Address search (should be <300ms)
EXPLAIN ANALYZE
SELECT parcel_id,county,owner_name,phy_addr1,phy_city,just_value
FROM public.florida_parcels
WHERE is_redacted = false AND just_value > 0 AND phy_addr1 ILIKE '%ocean%'
ORDER BY just_value DESC
LIMIT 20;

-- ============================================================================
-- EXPECTED RESULTS
-- ============================================================================
-- After running these indexes:
-- - Initial page load: <50ms (was 5-10 seconds)
-- - County filter: <100ms (was 3-5 seconds)
-- - City search: <200ms (was 5+ seconds)
-- - Address search: <300ms (was 10+ seconds)
-- - Owner search: <300ms (was 10+ seconds)
-- - Property type filter: <100ms (was 2-3 seconds)
-- ============================================================================
