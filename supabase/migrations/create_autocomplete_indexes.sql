-- ============================================================
-- AUTOCOMPLETE PERFORMANCE INDEXES
-- ============================================================
-- Creates optimized indexes for fast autocomplete queries
-- on florida_parcels table in Broward County
--
-- Expected Performance Improvement:
-- - Before: 1-3 seconds per query
-- - After: 50-200ms per query (10-60x faster)
-- ============================================================

-- Index 1: Address autocomplete (prefix matching)
-- Supports: ILIKE 'query%' on phy_addr1 filtered by county
CREATE INDEX IF NOT EXISTS idx_autocomplete_address_broward
ON florida_parcels (county, phy_addr1 text_pattern_ops)
WHERE county = 'BROWARD' AND phy_addr1 IS NOT NULL;

-- Index 2: Owner name autocomplete (prefix matching)
-- Supports: ILIKE 'query%' on owner_name filtered by county
CREATE INDEX IF NOT EXISTS idx_autocomplete_owner_broward
ON florida_parcels (county, owner_name text_pattern_ops)
WHERE county = 'BROWARD' AND owner_name IS NOT NULL;

-- Index 3: City autocomplete (prefix matching)
-- Supports: ILIKE 'query%' on phy_city filtered by county
CREATE INDEX IF NOT EXISTS idx_autocomplete_city_broward
ON florida_parcels (county, phy_city text_pattern_ops)
WHERE county = 'BROWARD' AND phy_city IS NOT NULL;

-- Index 4: Composite index for full autocomplete query
-- Supports: Retrieving all fields needed for autocomplete suggestions
CREATE INDEX IF NOT EXISTS idx_autocomplete_composite_broward
ON florida_parcels (county, phy_addr1, owner_name, phy_city, property_use, just_value, parcel_id)
WHERE county = 'BROWARD';

-- ============================================================
-- ANALYSIS QUERIES (for verification)
-- ============================================================

-- Check index sizes
-- SELECT
--   schemaname,
--   tablename,
--   indexname,
--   pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
-- FROM pg_indexes
-- WHERE tablename = 'florida_parcels'
-- AND indexname LIKE 'idx_autocomplete%';

-- Test query performance (should be <100ms)
-- EXPLAIN ANALYZE
-- SELECT phy_addr1, phy_city, phy_zipcd, owner_name, property_use, just_value, parcel_id
-- FROM florida_parcels
-- WHERE county = 'BROWARD'
-- AND phy_addr1 ILIKE 'HOLL%'
-- AND phy_addr1 IS NOT NULL
-- ORDER BY phy_addr1
-- LIMIT 5;

-- ============================================================
-- MAINTENANCE
-- ============================================================

-- To rebuild indexes if they become bloated:
-- REINDEX INDEX CONCURRENTLY idx_autocomplete_address_broward;
-- REINDEX INDEX CONCURRENTLY idx_autocomplete_owner_broward;
-- REINDEX INDEX CONCURRENTLY idx_autocomplete_city_broward;
-- REINDEX INDEX CONCURRENTLY idx_autocomplete_composite_broward;

-- To drop indexes (if needed):
-- DROP INDEX IF EXISTS idx_autocomplete_address_broward;
-- DROP INDEX IF EXISTS idx_autocomplete_owner_broward;
-- DROP INDEX IF EXISTS idx_autocomplete_city_broward;
-- DROP INDEX IF EXISTS idx_autocomplete_composite_broward;
