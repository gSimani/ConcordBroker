-- =====================================================
-- PERFORMANCE INDEXES FOR FLORIDA_PARCELS TABLE
-- NAP Data Import Optimization for Fast Website Queries
-- =====================================================

-- Drop existing indexes if they exist (in case of re-run)
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
-- PRIMARY SEARCH INDEXES
-- =====================================================

-- 1. Parcel ID - Primary identifier for property lookups
CREATE INDEX CONCURRENTLY idx_florida_parcels_parcel_id 
ON florida_parcels USING btree (parcel_id);

-- 2. Owner Name - For owner/entity searches  
CREATE INDEX CONCURRENTLY idx_florida_parcels_owner_name 
ON florida_parcels USING gin (to_tsvector('english', owner_name));

-- 3. Physical Address - For address searches
CREATE INDEX CONCURRENTLY idx_florida_parcels_phy_addr 
ON florida_parcels USING gin (to_tsvector('english', phy_addr1));

-- 4. Physical City - For city-based filtering
CREATE INDEX CONCURRENTLY idx_florida_parcels_phy_city 
ON florida_parcels USING btree (phy_city);

-- 5. Physical Zip Code - For location-based searches
CREATE INDEX CONCURRENTLY idx_florida_parcels_phy_zipcd 
ON florida_parcels USING btree (phy_zipcd);

-- =====================================================
-- VALUATION INDEXES
-- =====================================================

-- 6. Taxable Value - For value-based filtering and sorting
CREATE INDEX CONCURRENTLY idx_florida_parcels_taxable_value 
ON florida_parcels USING btree (taxable_value DESC NULLS LAST);

-- 7. Just Value - For market value searches
CREATE INDEX CONCURRENTLY idx_florida_parcels_just_value 
ON florida_parcels USING btree (just_value DESC NULLS LAST);

-- 8. Assessed Value - For assessment-based queries
CREATE INDEX CONCURRENTLY idx_florida_parcels_assessed_value 
ON florida_parcels USING btree (assessed_value DESC NULLS LAST);

-- =====================================================
-- METADATA INDEXES
-- =====================================================

-- 9. Data Source - For filtering by data source (NAP, etc.)
CREATE INDEX CONCURRENTLY idx_florida_parcels_data_source 
ON florida_parcels USING btree (data_source);

-- 10. County and Year - For jurisdiction/time filtering
CREATE INDEX CONCURRENTLY idx_florida_parcels_county_year 
ON florida_parcels USING btree (county, year);

-- 11. Property Use - For property type filtering
CREATE INDEX CONCURRENTLY idx_florida_parcels_property_use 
ON florida_parcels USING btree (property_use);

-- =====================================================
-- COMPOSITE INDEXES FOR COMMON QUERY PATTERNS
-- =====================================================

-- 12. City + Value Range queries (common for market analysis)
CREATE INDEX CONCURRENTLY idx_florida_parcels_city_value 
ON florida_parcels USING btree (phy_city, taxable_value DESC NULLS LAST);

-- 13. Owner + City (for portfolio analysis)
CREATE INDEX CONCURRENTLY idx_florida_parcels_owner_city 
ON florida_parcels USING btree (owner_name, phy_city);

-- 14. Zip + Value (for neighborhood analysis)  
CREATE INDEX CONCURRENTLY idx_florida_parcels_zip_value
ON florida_parcels USING btree (phy_zipcd, just_value DESC NULLS LAST);

-- =====================================================
-- SPATIAL INDEX (if geometry columns are populated)
-- =====================================================

-- 15. Geometry index for mapping queries (if geometry data exists)
CREATE INDEX CONCURRENTLY idx_florida_parcels_geometry 
ON florida_parcels USING gist (geometry) 
WHERE geometry IS NOT NULL;

-- =====================================================
-- STATISTICS UPDATE
-- =====================================================

-- Update table statistics for query optimizer
ANALYZE florida_parcels;

-- =====================================================
-- INDEX STATUS VERIFICATION
-- =====================================================

-- Query to check index status
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'florida_parcels'
ORDER BY indexname;