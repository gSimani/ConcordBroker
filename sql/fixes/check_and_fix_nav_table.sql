-- FIRST: Check what columns exist in nav_assessments
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'nav_assessments';

-- If the table is empty or missing columns, run this to add all needed columns:
ALTER TABLE nav_assessments 
ADD COLUMN IF NOT EXISTS parcel_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS district_name VARCHAR(200),
ADD COLUMN IF NOT EXISTS total_assessment NUMERIC,
ADD COLUMN IF NOT EXISTS amount NUMERIC;

-- Now run the simplified optimization without complex joins:
DROP MATERIALIZED VIEW IF EXISTS property_search_fast CASCADE;

CREATE MATERIALIZED VIEW property_search_fast AS
SELECT 
    p.parcel_id,
    p.phy_addr1,
    p.phy_city,
    p.phy_state,
    p.phy_zipcd,
    COALESCE(p.phy_addr1, '') || ', ' || 
    COALESCE(p.phy_city, '') || ', FL ' || 
    COALESCE(p.phy_zipcd, '') as full_address,
    p.owner_name,
    p.assessed_value,
    p.taxable_value,
    p.just_value,
    p.land_value,
    p.building_value,
    p.year_built,
    p.total_living_area,
    p.bedrooms,
    p.bathrooms,
    p.property_use,
    p.property_use_desc
FROM florida_parcels p
WHERE p.parcel_id IS NOT NULL;

-- Create basic indexes for fast search
CREATE INDEX IF NOT EXISTS idx_search_fast_parcel ON property_search_fast(parcel_id);
CREATE INDEX IF NOT EXISTS idx_search_fast_address ON property_search_fast(full_address);
CREATE INDEX IF NOT EXISTS idx_search_fast_owner ON property_search_fast(owner_name);
CREATE INDEX IF NOT EXISTS idx_search_fast_value ON property_search_fast(assessed_value);

-- Refresh the view
REFRESH MATERIALIZED VIEW property_search_fast;

-- Test it works
SELECT COUNT(*) as total_properties FROM property_search_fast;