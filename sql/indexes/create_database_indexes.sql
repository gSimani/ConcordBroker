-- Database Performance Indexes for ConcordBroker Real Estate Platform
-- Run this SQL in your Supabase SQL Editor to optimize website performance

-- 1. Primary parcel ID index for fast property lookups
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id 
ON florida_parcels(parcel_id);

-- 2. City index for property search by location
CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_city 
ON florida_parcels(phy_city);

-- 3. ZIP code index for geographic filtering
CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_zipcd 
ON florida_parcels(phy_zipcd);

-- 4. Just value index for value-based filtering and market analysis
CREATE INDEX IF NOT EXISTS idx_florida_parcels_just_value 
ON florida_parcels(just_value);

-- 5. Assessed value index for tax analysis
CREATE INDEX IF NOT EXISTS idx_florida_parcels_assessed_value 
ON florida_parcels(assessed_value);

-- 6. Year built index for property age filtering
CREATE INDEX IF NOT EXISTS idx_florida_parcels_year_built 
ON florida_parcels(year_built);

-- 7. Owner name full-text search index for business intelligence
-- First install pg_trgm extension if not exists
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name_gin 
ON florida_parcels USING gin(owner_name gin_trgm_ops);

-- 8. Property address full-text search
CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_addr1_gin 
ON florida_parcels USING gin(phy_addr1 gin_trgm_ops);

-- 9. Composite index for city + value range queries (market analysis)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city_value 
ON florida_parcels(phy_city, just_value);

-- 10. Composite index for city + year built (property age analysis)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city_year 
ON florida_parcels(phy_city, year_built);

-- 11. Composite index for bedrooms/bathrooms filtering
CREATE INDEX IF NOT EXISTS idx_florida_parcels_bed_bath 
ON florida_parcels(bedrooms, bathrooms);

-- 12. Living area index for size-based filtering
CREATE INDEX IF NOT EXISTS idx_florida_parcels_living_area 
ON florida_parcels(total_living_area);

-- 13. Sales history table indexes (if it exists)
CREATE INDEX IF NOT EXISTS idx_property_sales_history_parcel_id 
ON property_sales_history(parcel_id);

CREATE INDEX IF NOT EXISTS idx_property_sales_history_sale_date 
ON property_sales_history(sale_date);

CREATE INDEX IF NOT EXISTS idx_property_sales_history_sale_price 
ON property_sales_history(sale_price);

-- Performance monitoring query
-- Run this to check query performance after creating indexes
/*
EXPLAIN ANALYZE 
SELECT parcel_id, owner_name, phy_addr1, just_value 
FROM florida_parcels 
WHERE phy_city = 'PARKLAND' 
AND just_value BETWEEN 400000 AND 800000 
LIMIT 10;
*/