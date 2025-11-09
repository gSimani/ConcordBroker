-- STEP 1: Fix nav_assessments table structure (RUN THIS FIRST)
ALTER TABLE nav_assessments 
ADD COLUMN IF NOT EXISTS total_assessment NUMERIC;

-- Update total_assessment from existing columns if they exist
UPDATE nav_assessments 
SET total_assessment = COALESCE(amount, 0) 
WHERE total_assessment IS NULL;

-- STEP 2: Create all indexes (RUN THIS SECOND)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_addr1 ON florida_parcels(phy_addr1);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_city ON florida_parcels(phy_city);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county ON florida_parcels(county);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_assessed_value ON florida_parcels(assessed_value);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_year_built ON florida_parcels(year_built);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_filters ON florida_parcels(county, assessed_value, year_built);
CREATE INDEX IF NOT EXISTS idx_sales_history_parcel ON property_sales_history(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sales_history_date ON property_sales_history(sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_nav_assessments_parcel ON nav_assessments(parcel_id);

-- STEP 3: Create simplified materialized view (RUN THIS THIRD)
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

CREATE INDEX idx_search_fast_parcel ON property_search_fast(parcel_id);
CREATE INDEX idx_search_fast_address ON property_search_fast(full_address);
CREATE INDEX idx_search_fast_owner ON property_search_fast(owner_name);
CREATE INDEX idx_search_fast_value ON property_search_fast(assessed_value);

-- STEP 4: Refresh and verify (RUN THIS LAST)
REFRESH MATERIALIZED VIEW property_search_fast;

SELECT COUNT(*) as total_properties FROM property_search_fast;