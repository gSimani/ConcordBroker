-- Add NAP physical property columns to florida_parcels table

-- Building characteristics
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS year_built INTEGER,
ADD COLUMN IF NOT EXISTS effective_year_built INTEGER,
ADD COLUMN IF NOT EXISTS total_living_area INTEGER,
ADD COLUMN IF NOT EXISTS adjusted_area INTEGER,
ADD COLUMN IF NOT EXISTS gross_area INTEGER,
ADD COLUMN IF NOT EXISTS heated_area INTEGER;

-- Bedroom/Bathroom data
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS bedrooms INTEGER,
ADD COLUMN IF NOT EXISTS bathrooms INTEGER,
ADD COLUMN IF NOT EXISTS half_bathrooms INTEGER;

-- Stories and units
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS stories VARCHAR(10),
ADD COLUMN IF NOT EXISTS units INTEGER,
ADD COLUMN IF NOT EXISTS buildings INTEGER;

-- Condition and quality
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS condition VARCHAR(50),
ADD COLUMN IF NOT EXISTS quality VARCHAR(50),
ADD COLUMN IF NOT EXISTS construction_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS exterior_wall VARCHAR(50),
ADD COLUMN IF NOT EXISTS roof_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS roof_cover VARCHAR(50);

-- Pool and features
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS pool BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS pool_type VARCHAR(50);

-- Heating/Cooling
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS heat_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS air_cond VARCHAR(50);

-- Other features
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS floor_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS foundation VARCHAR(50),
ADD COLUMN IF NOT EXISTS basement VARCHAR(50),
ADD COLUMN IF NOT EXISTS fireplace INTEGER;

-- Special features (as JSON array)
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS special_features JSONB;

-- Enhanced SDF sales fields
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS last_deed_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS last_grantor VARCHAR(255),
ADD COLUMN IF NOT EXISTS last_grantee VARCHAR(255),
ADD COLUMN IF NOT EXISTS last_mtg_amount BIGINT,
ADD COLUMN IF NOT EXISTS last_mtg_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS foreclosure_flag BOOLEAN DEFAULT false;

-- Create indexes for commonly searched fields
CREATE INDEX IF NOT EXISTS idx_parcels_bedrooms ON florida_parcels(bedrooms);
CREATE INDEX IF NOT EXISTS idx_parcels_bathrooms ON florida_parcels(bathrooms);
CREATE INDEX IF NOT EXISTS idx_parcels_year_built ON florida_parcels(year_built);
CREATE INDEX IF NOT EXISTS idx_parcels_living_area ON florida_parcels(total_living_area);
CREATE INDEX IF NOT EXISTS idx_parcels_pool ON florida_parcels(pool);

-- Create a view for property characteristics
CREATE OR REPLACE VIEW property_characteristics AS
SELECT 
    parcel_id,
    phy_addr1 as address,
    phy_city as city,
    owner_name,
    -- Valuations
    just_value,
    assessed_value,
    taxable_value,
    -- Physical
    year_built,
    total_living_area,
    bedrooms,
    bathrooms,
    half_bathrooms,
    stories,
    units,
    -- Features
    pool,
    pool_type,
    air_cond,
    heat_type,
    construction_type,
    -- Sales
    sale_price as last_sale_price,
    sale_date as last_sale_date,
    last_grantor as seller,
    last_grantee as buyer
FROM florida_parcels
WHERE is_redacted = false;

GRANT SELECT ON property_characteristics TO anon, authenticated;