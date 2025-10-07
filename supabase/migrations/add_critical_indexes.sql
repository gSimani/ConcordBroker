-- Critical Performance Indexes for florida_parcels
-- These indexes will dramatically improve search and query performance
-- CONCURRENTLY ensures no table locking during creation

-- Parcel ID index (primary lookup)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_parcel_id
ON florida_parcels(parcel_id);

-- County index (filtering by county)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county
ON florida_parcels(county);

-- Owner name index (search by owner)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name
ON florida_parcels(owner_name);

-- Physical address indexes (property search)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_addr1
ON florida_parcels(phy_addr1);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_city
ON florida_parcels(phy_city);

-- Just value index (filtering by value)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_just_value
ON florida_parcels(just_value);

-- DOR use code index (property type filtering)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_dor_uc
ON florida_parcels(dor_uc);

-- Composite index for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county_parcel
ON florida_parcels(county, parcel_id);

-- Year index (filtering by year)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_year
ON florida_parcels(year);

-- Analyze table after index creation
ANALYZE florida_parcels;

-- Indexes for florida_entities (if table exists and needs indexes)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_entities_entity_id
ON florida_entities(entity_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_entities_business_name
ON florida_entities(business_name);

-- Analyze entities table
ANALYZE florida_entities;

-- Success message
SELECT
    'Critical indexes created successfully!' as status,
    'Performance should improve dramatically' as note,
    NOW() as completed_at;
