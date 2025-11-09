-- IMMEDIATE PERFORMANCE FIX FOR CONCORDBROKER

-- 1. Critical indexes for 789K parcels table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fl_parcels_parcel ON florida_parcels(parcel_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fl_parcels_county ON florida_parcels(county);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fl_parcels_city ON florida_parcels(phy_city);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fl_parcels_addr ON florida_parcels(phy_addr1);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fl_parcels_owner ON florida_parcels(owner_name);

-- 2. Create limited view for fast queries
CREATE OR REPLACE VIEW florida_parcels_fast AS
SELECT 
    parcel_id,
    phy_addr1,
    phy_city,
    phy_zipcd,
    owner_name,
    assessed_value,
    year_built,
    bedrooms,
    bathrooms
FROM florida_parcels
LIMIT 10000;  -- Only show first 10K for fast loading

-- 3. Update statistics
ANALYZE florida_parcels;

SELECT 'Indexes created - queries should be faster now!' as status;
