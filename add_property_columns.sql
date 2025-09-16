-- Add missing columns to florida_parcels table
-- Execute this in Supabase SQL Editor

-- Property characteristics
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS year_built INTEGER;
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS total_living_area INTEGER;
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS bedrooms INTEGER;
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS bathrooms DECIMAL(3,1);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS stories INTEGER;
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS units INTEGER;

-- Valuation fields
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS just_value DECIMAL(15,2);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS assessed_value DECIMAL(15,2);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS taxable_value DECIMAL(15,2);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS land_value DECIMAL(15,2);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS building_value DECIMAL(15,2);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS market_value DECIMAL(15,2);

-- Sales information
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS sale_date DATE;
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS sale_price DECIMAL(15,2);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS sale_qualification VARCHAR(10);

-- Property details
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS legal_desc TEXT;
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS subdivision VARCHAR(255);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS lot VARCHAR(50);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS block VARCHAR(50);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS zoning VARCHAR(50);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS property_use_desc VARCHAR(255);

-- Owner mailing address
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS owner_addr1 VARCHAR(255);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS owner_addr2 VARCHAR(255);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS owner_city VARCHAR(100);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS owner_state VARCHAR(2);
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS owner_zip VARCHAR(10);

-- Land measurements
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS land_sqft INTEGER;
ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS land_acres DECIMAL(10,4);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_florida_parcels_year_built ON florida_parcels(year_built);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_sale_date ON florida_parcels(sale_date);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_market_value ON florida_parcels(market_value);