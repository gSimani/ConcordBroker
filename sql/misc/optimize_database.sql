-- Database Optimization for Millions of Records
-- Run this in Supabase SQL Editor to enable fast queries

-- 1. Create indexes for fast searching
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county ON florida_parcels(county);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city ON florida_parcels(phy_city);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_zipcode ON florida_parcels(phy_zipcd);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_address ON florida_parcels(phy_addr1);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_taxable_value ON florida_parcels(taxable_value);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_sale_date ON florida_parcels(sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_property_use ON florida_parcels(property_use);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_year_built ON florida_parcels(year_built);

-- 2. Create composite indexes for common filter combinations
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_city ON florida_parcels(county, phy_city);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city_value ON florida_parcels(phy_city, taxable_value DESC);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_value ON florida_parcels(county, taxable_value DESC);

-- 3. Create full-text search index for addresses
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_florida_parcels_address_trgm ON florida_parcels USING gin (phy_addr1 gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_trgm ON florida_parcels USING gin (owner_name gin_trgm_ops);

-- 4. Create materialized view for high-value properties (faster for common queries)
CREATE MATERIALIZED VIEW IF NOT EXISTS high_value_properties AS
SELECT * FROM florida_parcels 
WHERE taxable_value > 1000000 
AND is_redacted = false
ORDER BY taxable_value DESC;

CREATE INDEX ON high_value_properties(county, phy_city);
CREATE INDEX ON high_value_properties(taxable_value);

-- 5. Create summary statistics table for fast counts
CREATE TABLE IF NOT EXISTS property_statistics (
    county VARCHAR(50),
    city VARCHAR(100),
    total_properties INTEGER,
    avg_value DECIMAL,
    median_value DECIMAL,
    total_value DECIMAL,
    last_updated TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (county, city)
);

-- 6. Function for efficient property search with filters
CREATE OR REPLACE FUNCTION search_properties(
    p_county VARCHAR DEFAULT NULL,
    p_city VARCHAR DEFAULT NULL,
    p_min_value INTEGER DEFAULT NULL,
    p_max_value INTEGER DEFAULT NULL,
    p_owner_search VARCHAR DEFAULT NULL,
    p_address_search VARCHAR DEFAULT NULL,
    p_property_use VARCHAR DEFAULT NULL,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    parcel_id VARCHAR,
    county VARCHAR,
    phy_addr1 VARCHAR,
    phy_city VARCHAR,
    phy_zipcd VARCHAR,
    owner_name VARCHAR,
    taxable_value INTEGER,
    sale_date DATE,
    sale_price INTEGER,
    year_built INTEGER,
    total_living_area INTEGER,
    property_use VARCHAR
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fp.parcel_id,
        fp.county,
        fp.phy_addr1,
        fp.phy_city,
        fp.phy_zipcd,
        fp.owner_name,
        fp.taxable_value,
        fp.sale_date,
        fp.sale_price,
        fp.year_built,
        fp.total_living_area,
        fp.property_use
    FROM florida_parcels fp
    WHERE 
        (p_county IS NULL OR fp.county = p_county)
        AND (p_city IS NULL OR fp.phy_city ILIKE '%' || p_city || '%')
        AND (p_min_value IS NULL OR fp.taxable_value >= p_min_value)
        AND (p_max_value IS NULL OR fp.taxable_value <= p_max_value)
        AND (p_owner_search IS NULL OR fp.owner_name ILIKE '%' || p_owner_search || '%')
        AND (p_address_search IS NULL OR fp.phy_addr1 ILIKE '%' || p_address_search || '%')
        AND (p_property_use IS NULL OR fp.property_use = p_property_use)
        AND fp.is_redacted = false
    ORDER BY fp.taxable_value DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

-- 7. Test the performance
EXPLAIN ANALYZE 
SELECT * FROM search_properties(
    p_county := 'BROWARD',
    p_city := 'Fort Lauderdale',
    p_min_value := 500000,
    p_max_value := 2000000,
    p_limit := 20
);