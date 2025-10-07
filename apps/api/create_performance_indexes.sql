-- Performance indexes for florida_parcels table
-- These indexes optimize the MiniPropertyCard queries for 100% real data

-- Index for batch sales queries (fixes N+1 problem)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id_sales
ON florida_parcels(parcel_id, sale_price, sale_date, sale_qualification, or_book, or_page);

-- Index for county-based searches (most common filter)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_year
ON florida_parcels(county, year);

-- Index for property use categorization
CREATE INDEX IF NOT EXISTS idx_florida_parcels_property_use
ON florida_parcels(property_use, property_use_desc);

-- Index for address searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_address
ON florida_parcels(phy_addr1, phy_city, phy_zipcd);

-- Index for value-based queries
CREATE INDEX IF NOT EXISTS idx_florida_parcels_values
ON florida_parcels(just_value, assessed_value);

-- Index for owner name searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner
ON florida_parcels(owner_name);

-- Composite index for common MiniPropertyCard queries
CREATE INDEX IF NOT EXISTS idx_florida_parcels_minicard
ON florida_parcels(parcel_id, county, just_value, assessed_value, sale_price, property_use);

-- Analyze table to update statistics for query planner
ANALYZE florida_parcels;

-- Show index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE tablename = 'florida_parcels'
ORDER BY idx_scan DESC;