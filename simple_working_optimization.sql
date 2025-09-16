-- SIMPLE WORKING OPTIMIZATION - Run each section separately

-- SECTION 1: Create basic indexes on florida_parcels (789K records)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_addr1 ON florida_parcels(phy_addr1);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_assessed_value ON florida_parcels(assessed_value);

-- SECTION 2: Create simplified materialized view (no joins)
DROP MATERIALIZED VIEW IF EXISTS property_search_fast CASCADE;

CREATE MATERIALIZED VIEW property_search_fast AS
SELECT
    parcel_id,
    phy_addr1,
    phy_city,
    phy_state,
    phy_zipcd,
    COALESCE(phy_addr1, '') || ', ' ||
    COALESCE(phy_city, '') || ', FL ' ||
    COALESCE(phy_zipcd, '') as full_address,
    owner_name,
    assessed_value,
    year_built,
    bedrooms,
    bathrooms,
    property_use_desc
FROM florida_parcels
WHERE parcel_id IS NOT NULL;

-- SECTION 3: Create indexes on the view
CREATE INDEX idx_search_fast_parcel ON property_search_fast(parcel_id);
CREATE INDEX idx_search_fast_owner ON property_search_fast(owner_name);

-- SECTION 4: Refresh and test
REFRESH MATERIALIZED VIEW property_search_fast;

-- Test it works
SELECT COUNT(*) as total_properties FROM property_search_fast;

-- Test search speed
SELECT * FROM property_search_fast 
WHERE full_address ILIKE '%main%' 
LIMIT 10;