-- ==============================================================================
-- TRIGRAM TEXT SEARCH OPTIMIZATION
-- ==============================================================================
-- Purpose: Optimize ILIKE queries with pg_trgm indexes for 3-5x speedup
-- Author: Claude Code - Advanced Filter Optimization
-- Created: 2025-10-01
-- ==============================================================================

-- Install pg_trgm extension if not already installed
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ==============================================================================
-- DROP EXISTING INDEXES (if they exist)
-- ==============================================================================

DROP INDEX IF EXISTS idx_parcels_owner_trigram;
DROP INDEX IF EXISTS idx_parcels_addr_trigram;
DROP INDEX IF EXISTS idx_parcels_city_trigram;
DROP INDEX IF EXISTS idx_parcels_owner_name;
DROP INDEX IF EXISTS idx_parcels_address;

-- ==============================================================================
-- CREATE TRIGRAM GIN INDEXES
-- ==============================================================================

-- Owner name trigram index (for partial matching)
CREATE INDEX CONCURRENTLY idx_parcels_owner_trigram
ON florida_parcels USING gin (owner_name gin_trgm_ops)
WHERE owner_name IS NOT NULL AND owner_name != '';

-- Physical address trigram index
CREATE INDEX CONCURRENTLY idx_parcels_addr_trigram
ON florida_parcels USING gin (phy_addr1 gin_trgm_ops)
WHERE phy_addr1 IS NOT NULL AND phy_addr1 != '';

-- City trigram index
CREATE INDEX CONCURRENTLY idx_parcels_city_trigram
ON florida_parcels USING gin (city gin_trgm_ops)
WHERE city IS NOT NULL AND city != '';

-- Combined address trigram index (for full address search)
CREATE INDEX CONCURRENTLY idx_parcels_full_addr_trigram
ON florida_parcels USING gin (
    (COALESCE(phy_addr1, '') || ' ' ||
     COALESCE(phy_addr2, '') || ' ' ||
     COALESCE(city, '')) gin_trgm_ops
)
WHERE phy_addr1 IS NOT NULL;

-- ==============================================================================
-- SIMILARITY THRESHOLD CONFIGURATION
-- ==============================================================================

-- Set similarity threshold (0.0 to 1.0, lower = more matches)
-- 0.3 is a good balance between precision and recall
SET pg_trgm.similarity_threshold = 0.3;

-- For more strict matching, use 0.5:
-- SET pg_trgm.similarity_threshold = 0.5;

-- ==============================================================================
-- PERFORMANCE TESTING QUERIES
-- ==============================================================================

-- Test 1: Owner name search (ILIKE with trigram)
EXPLAIN ANALYZE
SELECT parcel_id, owner_name, phy_addr1, city, just_value
FROM florida_parcels
WHERE owner_name ILIKE '%LLC%'
  AND county = 'BROWARD'
LIMIT 100;

-- Test 2: Owner name search (similarity operator)
EXPLAIN ANALYZE
SELECT parcel_id, owner_name, phy_addr1, city, just_value
FROM florida_parcels
WHERE owner_name % 'Property Holdings LLC'
  AND county = 'BROWARD'
ORDER BY similarity(owner_name, 'Property Holdings LLC') DESC
LIMIT 100;

-- Test 3: Address search with trigram
EXPLAIN ANALYZE
SELECT parcel_id, owner_name, phy_addr1, city, just_value
FROM florida_parcels
WHERE phy_addr1 ILIKE '%Main Street%'
  AND city ILIKE 'Fort Lauderdale'
LIMIT 100;

-- Test 4: Full address search
EXPLAIN ANALYZE
SELECT parcel_id, owner_name, phy_addr1, city, just_value
FROM florida_parcels
WHERE (COALESCE(phy_addr1, '') || ' ' || COALESCE(city, ''))
      ILIKE '%123 Ocean%'
LIMIT 100;

-- ==============================================================================
-- HELPER FUNCTIONS FOR OPTIMIZED TEXT SEARCH
-- ==============================================================================

-- Function to search owners with ranking
CREATE OR REPLACE FUNCTION search_owners_ranked(
    search_term TEXT,
    county_filter TEXT DEFAULT NULL,
    result_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    parcel_id TEXT,
    owner_name TEXT,
    full_address TEXT,
    just_value BIGINT,
    similarity_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.parcel_id,
        p.owner_name,
        TRIM(
            COALESCE(p.phy_addr1, '') || ' ' ||
            COALESCE(p.phy_addr2, '') || ', ' ||
            COALESCE(p.city, '') || ', ' ||
            COALESCE(p.state, '') || ' ' ||
            COALESCE(p.zip_code, '')
        ) as full_address,
        p.just_value,
        similarity(p.owner_name, search_term) as similarity_score
    FROM florida_parcels p
    WHERE p.owner_name % search_term
      AND (county_filter IS NULL OR p.county = county_filter)
    ORDER BY similarity(p.owner_name, search_term) DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to search addresses with ranking
CREATE OR REPLACE FUNCTION search_addresses_ranked(
    search_term TEXT,
    county_filter TEXT DEFAULT NULL,
    result_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    parcel_id TEXT,
    owner_name TEXT,
    full_address TEXT,
    just_value BIGINT,
    similarity_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.parcel_id,
        p.owner_name,
        TRIM(
            COALESCE(p.phy_addr1, '') || ' ' ||
            COALESCE(p.phy_addr2, '') || ', ' ||
            COALESCE(p.city, '') || ', ' ||
            COALESCE(p.state, '') || ' ' ||
            COALESCE(p.zip_code, '')
        ) as full_address,
        p.just_value,
        similarity(p.phy_addr1, search_term) as similarity_score
    FROM florida_parcels p
    WHERE p.phy_addr1 % search_term
      AND (county_filter IS NULL OR p.county = county_filter)
    ORDER BY similarity(p.phy_addr1, search_term) DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- AUTOCOMPLETE FUNCTIONS
-- ==============================================================================

-- Autocomplete for owner names
CREATE OR REPLACE FUNCTION autocomplete_owners(
    partial_name TEXT,
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    owner_name TEXT,
    property_count BIGINT,
    avg_value NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.owner_name,
        COUNT(*) as property_count,
        ROUND(AVG(p.just_value)::numeric, 0) as avg_value
    FROM florida_parcels p
    WHERE p.owner_name ILIKE partial_name || '%'
      AND p.owner_name IS NOT NULL
    GROUP BY p.owner_name
    ORDER BY COUNT(*) DESC, p.owner_name
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Autocomplete for addresses
CREATE OR REPLACE FUNCTION autocomplete_addresses(
    partial_address TEXT,
    county_filter TEXT DEFAULT NULL,
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    full_address TEXT,
    parcel_id TEXT,
    owner_name TEXT,
    just_value BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        TRIM(
            COALESCE(p.phy_addr1, '') || ' ' ||
            COALESCE(p.phy_addr2, '') || ', ' ||
            COALESCE(p.city, '') || ', ' ||
            COALESCE(p.state, '') || ' ' ||
            COALESCE(p.zip_code, '')
        ) as full_address,
        p.parcel_id,
        p.owner_name,
        p.just_value
    FROM florida_parcels p
    WHERE p.phy_addr1 ILIKE partial_address || '%'
      AND (county_filter IS NULL OR p.county = county_filter)
      AND p.phy_addr1 IS NOT NULL
    ORDER BY p.phy_addr1
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Autocomplete for cities
CREATE OR REPLACE FUNCTION autocomplete_cities(
    partial_city TEXT,
    county_filter TEXT DEFAULT NULL,
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    city TEXT,
    property_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.city,
        COUNT(*) as property_count
    FROM florida_parcels p
    WHERE p.city ILIKE partial_city || '%'
      AND (county_filter IS NULL OR p.county = county_filter)
      AND p.city IS NOT NULL
    GROUP BY p.city
    ORDER BY COUNT(*) DESC, p.city
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- STATISTICS & MONITORING
-- ==============================================================================

-- Increase statistics for text columns
ALTER TABLE florida_parcels ALTER COLUMN owner_name SET STATISTICS 1000;
ALTER TABLE florida_parcels ALTER COLUMN phy_addr1 SET STATISTICS 1000;
ALTER TABLE florida_parcels ALTER COLUMN city SET STATISTICS 500;

-- Analyze table with new indexes
ANALYZE florida_parcels;

-- Check index sizes
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'florida_parcels'
  AND indexname LIKE '%trigram%'
ORDER BY pg_relation_size(indexrelid) DESC;

-- ==============================================================================
-- USAGE EXAMPLES
-- ==============================================================================

/*
-- Example 1: Search owners with ranking
SELECT * FROM search_owners_ranked('Smith Properties', 'BROWARD', 50);

-- Example 2: Search addresses with ranking
SELECT * FROM search_addresses_ranked('Ocean Drive', 'MIAMI-DADE', 50);

-- Example 3: Autocomplete owner names
SELECT * FROM autocomplete_owners('Prop', 10);

-- Example 4: Autocomplete addresses
SELECT * FROM autocomplete_addresses('123', 'BROWARD', 10);

-- Example 5: Autocomplete cities
SELECT * FROM autocomplete_cities('Fort', NULL, 10);

-- Example 6: Direct ILIKE query (now uses trigram index automatically)
SELECT parcel_id, owner_name, phy_addr1, just_value
FROM florida_parcels
WHERE owner_name ILIKE '%LLC%'
  AND county = 'BROWARD'
  AND just_value > 500000
LIMIT 100;

-- Example 7: Similarity search with threshold
SELECT
    parcel_id,
    owner_name,
    similarity(owner_name, 'ABC Properties LLC') as score
FROM florida_parcels
WHERE owner_name % 'ABC Properties LLC'
  AND county = 'BROWARD'
ORDER BY score DESC
LIMIT 50;
*/

-- ==============================================================================
-- PERFORMANCE TIPS
-- ==============================================================================

/*
1. Use leading wildcard carefully:
   - FAST:  owner_name ILIKE 'Smith%'     (can use B-tree index)
   - SLOW:  owner_name ILIKE '%Smith%'    (requires trigram index)
   - MEDIUM: owner_name % 'Smith'          (uses trigram, ranked results)

2. Combine with other filters:
   - Always add county, value range, or other indexed filters
   - This reduces the search space before text matching

3. Limit results:
   - Always use LIMIT for text searches
   - 100 results is usually sufficient for user interfaces

4. Use similarity for ranking:
   - ORDER BY similarity(column, 'search_term') DESC
   - Provides better user experience than ILIKE

5. Adjust similarity threshold:
   - Lower threshold (0.2-0.3): More matches, less precise
   - Higher threshold (0.5-0.7): Fewer matches, more precise
   - Set per-query: SET LOCAL pg_trgm.similarity_threshold = 0.4;
*/
