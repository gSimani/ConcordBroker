-- Optimize Property Search Performance with Indexes
-- Run this in Supabase SQL Editor

-- Create indexes for most common search patterns
-- These will significantly speed up property searches

-- 1. Index for city searches (most common)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city
ON florida_parcels(phy_city)
WHERE phy_city IS NOT NULL;

-- 2. Index for address searches with pattern matching
CREATE INDEX IF NOT EXISTS idx_florida_parcels_address_trgm
ON florida_parcels USING gin (phy_addr1 gin_trgm_ops);

-- 3. Index for owner name searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_trgm
ON florida_parcels USING gin (own_name gin_trgm_ops);

-- 4. Composite index for value range queries
CREATE INDEX IF NOT EXISTS idx_florida_parcels_just_value
ON florida_parcels(just_value)
WHERE just_value IS NOT NULL;

-- 5. Index for zip code searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_zip
ON florida_parcels(phy_zipcd)
WHERE phy_zipcd IS NOT NULL;

-- 6. Composite index for city + value range (common filter combination)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city_value
ON florida_parcels(phy_city, just_value)
WHERE phy_city IS NOT NULL AND just_value IS NOT NULL;

-- 7. Index for year built filters
CREATE INDEX IF NOT EXISTS idx_florida_parcels_year_built
ON florida_parcels(yr_blt)
WHERE yr_blt IS NOT NULL;

-- 8. Index for property type/usage code
CREATE INDEX IF NOT EXISTS idx_florida_parcels_dor_uc
ON florida_parcels(dor_uc)
WHERE dor_uc IS NOT NULL;

-- 9. Partial index for active/valid parcels
CREATE INDEX IF NOT EXISTS idx_florida_parcels_active
ON florida_parcels(parcel_id, county, year)
WHERE parcel_id IS NOT NULL;

-- 10. Index for pagination (ORDER BY and LIMIT)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_id
ON florida_parcels(id);

-- Enable trigram extension if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Analyze table to update statistics
ANALYZE florida_parcels;

-- Create a materialized view for top cities (cache popular queries)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_city_property_counts AS
SELECT
    phy_city,
    COUNT(*) as property_count,
    AVG(just_value) as avg_value,
    MIN(just_value) as min_value,
    MAX(just_value) as max_value
FROM florida_parcels
WHERE phy_city IS NOT NULL
GROUP BY phy_city
ORDER BY property_count DESC;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_city_property_counts
ON mv_city_property_counts(phy_city);

-- Refresh materialized view (run periodically)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_city_property_counts;

-- Function to search properties with optimized query
CREATE OR REPLACE FUNCTION search_properties_optimized(
    p_city TEXT DEFAULT NULL,
    p_address TEXT DEFAULT NULL,
    p_owner TEXT DEFAULT NULL,
    p_min_value NUMERIC DEFAULT NULL,
    p_max_value NUMERIC DEFAULT NULL,
    p_limit INT DEFAULT 100,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id BIGINT,
    parcel_id TEXT,
    phy_addr1 TEXT,
    phy_city TEXT,
    own_name TEXT,
    just_value NUMERIC,
    land_value NUMERIC,
    bldg_value NUMERIC,
    yr_blt INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        fp.id,
        fp.parcel_id,
        fp.phy_addr1,
        fp.phy_city,
        fp.own_name,
        fp.just_value,
        fp.land_value,
        fp.bldg_value,
        fp.yr_blt
    FROM florida_parcels fp
    WHERE
        (p_city IS NULL OR fp.phy_city ILIKE '%' || p_city || '%')
        AND (p_address IS NULL OR fp.phy_addr1 ILIKE '%' || p_address || '%')
        AND (p_owner IS NULL OR fp.own_name ILIKE '%' || p_owner || '%')
        AND (p_min_value IS NULL OR fp.just_value >= p_min_value)
        AND (p_max_value IS NULL OR fp.just_value <= p_max_value)
    ORDER BY fp.id
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION search_properties_optimized TO anon, authenticated;
GRANT SELECT ON mv_city_property_counts TO anon, authenticated;