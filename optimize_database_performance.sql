-- CRITICAL PERFORMANCE INDEXES FOR FLORIDA_PARCELS TABLE
-- Run these in Supabase SQL Editor to dramatically improve query speed

-- 1. Primary composite index for most common queries
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_city
ON florida_parcels(county, phy_city);

-- 2. Index for address searches (most common user action)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_addr1
ON florida_parcels USING gin(phy_addr1 gin_trgm_ops);

-- 3. Index for owner name searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name
ON florida_parcels USING gin(owner_name gin_trgm_ops);

-- 4. Index for value-based filtering
CREATE INDEX IF NOT EXISTS idx_florida_parcels_taxable_value
ON florida_parcels(taxable_value)
WHERE taxable_value IS NOT NULL;

-- 5. Index for property type filtering
CREATE INDEX IF NOT EXISTS idx_florida_parcels_property_use
ON florida_parcels(property_use);

-- 6. Composite index for pagination with county filter
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_id
ON florida_parcels(county, id);

-- 7. Index for zip code searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_zipcd
ON florida_parcels(phy_zipcd);

-- 8. Partial index for properties with sales
CREATE INDEX IF NOT EXISTS idx_florida_parcels_sale_price
ON florida_parcels(sale_price)
WHERE sale_price > 0;

-- 9. Enable text search extension if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 10. Create materialized view for frequently accessed Broward data
CREATE MATERIALIZED VIEW IF NOT EXISTS broward_properties_cache AS
SELECT
    parcel_id,
    owner_name,
    phy_addr1,
    phy_city,
    phy_zipcd,
    taxable_value,
    just_value,
    land_value,
    year_built,
    sale_price,
    sale_date,
    property_use
FROM florida_parcels
WHERE county = 'BROWARD'
ORDER BY id;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_broward_cache_parcel
ON broward_properties_cache(parcel_id);

CREATE INDEX IF NOT EXISTS idx_broward_cache_city
ON broward_properties_cache(phy_city);

-- Refresh the materialized view (run periodically)
REFRESH MATERIALIZED VIEW CONCURRENTLY broward_properties_cache;

-- Analyze tables to update statistics
ANALYZE florida_parcels;

-- Show current indexes
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'florida_parcels'
ORDER BY indexname;