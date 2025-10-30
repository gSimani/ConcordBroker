-- ================================================================
-- DATABASE INDEX FOR OWNER_NAME SEARCH OPTIMIZATION
-- ================================================================
-- Purpose: Improve performance of owner name searches in florida_parcels table
-- Impact: Reduces query time from seconds to milliseconds for owner searches
-- Table: florida_parcels (9.1M+ records)
-- Column: owner_name (TEXT)
-- ================================================================

-- Create GIN index for fast text searches on owner_name
-- GIN (Generalized Inverted Index) is optimal for text search operations
-- This enables fast LIKE '%search%' queries on owner names
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name_gin
ON florida_parcels USING gin(owner_name gin_trgm_ops);

-- Alternative: Create B-tree index for exact matches and prefix searches
-- Use this if GIN index creation fails or if you primarily do prefix searches (owner_name LIKE 'Smith%')
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name_btree
-- ON florida_parcels(owner_name);

-- Verify index was created
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'florida_parcels'
    AND indexname LIKE '%owner_name%';

-- ================================================================
-- PERFORMANCE VERIFICATION QUERIES
-- ================================================================

-- Test query performance BEFORE index (should be slow)
EXPLAIN ANALYZE
SELECT parcel_id, owner_name, county, just_value
FROM florida_parcels
WHERE owner_name ILIKE '%SMITH%'
LIMIT 100;

-- Expected improvement:
-- BEFORE: Seq Scan on florida_parcels (cost=0.00..X rows=Y) (actual time=2000-5000ms)
-- AFTER:  Bitmap Heap Scan using idx_florida_parcels_owner_name_gin (actual time=50-200ms)

-- ================================================================
-- ROLLBACK (if needed)
-- ================================================================
-- DROP INDEX CONCURRENTLY IF EXISTS idx_florida_parcels_owner_name_gin;
