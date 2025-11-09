-- Create florida_parcels table for property autocomplete
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS florida_parcels (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    county VARCHAR(50),
    year INTEGER,
    
    -- Owner info
    owner_name VARCHAR(255),
    owner_addr1 VARCHAR(255),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    
    -- Physical address
    phy_addr1 VARCHAR(255),
    phy_addr2 VARCHAR(255),
    phy_city VARCHAR(100),
    phy_state VARCHAR(2) DEFAULT 'FL',
    phy_zipcd VARCHAR(10),
    
    -- Property details
    property_use VARCHAR(10),
    property_use_desc VARCHAR(255),
    year_built INTEGER,
    total_living_area FLOAT,
    bedrooms INTEGER,
    bathrooms FLOAT,
    
    -- Valuations
    just_value FLOAT,
    assessed_value FLOAT,
    taxable_value FLOAT,
    land_value FLOAT,
    building_value FLOAT,
    
    -- Sales info
    sale_date TIMESTAMP,
    sale_price FLOAT,
    
    -- Data flags
    is_redacted BOOLEAN DEFAULT FALSE,
    import_date TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better search performance
CREATE INDEX IF NOT EXISTS idx_parcels_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_parcels_owner ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_parcels_address ON florida_parcels(phy_addr1, phy_city);
CREATE INDEX IF NOT EXISTS idx_parcels_value ON florida_parcels(taxable_value);

-- Enable Row Level Security (optional)
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow public read access (optional)
CREATE POLICY "Allow public read access" ON florida_parcels
    FOR SELECT USING (true);