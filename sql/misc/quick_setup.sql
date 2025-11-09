-- QUICK SETUP - Minimal tables to get the app working
-- Run this in Supabase SQL Editor if the full script is too large

-- 1. Create the main florida_parcels table (REQUIRED)
CREATE TABLE IF NOT EXISTS florida_parcels (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    phy_addr1 TEXT,
    phy_city VARCHAR(100),
    phy_state VARCHAR(2) DEFAULT 'FL',
    phy_zipcd VARCHAR(10),
    owner_name TEXT,
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    just_value DECIMAL(15,2),
    year_built INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    living_area INTEGER,
    property_type VARCHAR(100)
);

-- 2. Create sales history table
CREATE TABLE IF NOT EXISTS property_sales_history (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    sale_date DATE,
    sale_price VARCHAR(20),
    sale_type VARCHAR(100)
);

-- 3. Create nav assessments table
CREATE TABLE IF NOT EXISTS nav_assessments (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    total_assessment DECIMAL(15,2)
);

-- 4. Create sunbiz table
CREATE TABLE IF NOT EXISTS sunbiz_corporate (
    id SERIAL PRIMARY KEY,
    corporate_name TEXT,
    officers TEXT,
    principal_address TEXT
);

-- 5. Enable public access
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE nav_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_corporate ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read" ON florida_parcels FOR SELECT USING (true);
CREATE POLICY "Public read" ON property_sales_history FOR SELECT USING (true);
CREATE POLICY "Public read" ON nav_assessments FOR SELECT USING (true);
CREATE POLICY "Public read" ON sunbiz_corporate FOR SELECT USING (true);

-- 6. Insert test data
INSERT INTO florida_parcels (parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, assessed_value, property_type)
VALUES ('064210010010', '3930 INVERRARY BLVD', 'LAUDERHILL', '33319', 'TEST OWNER LLC', 450000, 'SINGLE FAMILY');

-- 7. Verify
SELECT 'Setup complete! Found ' || COUNT(*) || ' properties' as status FROM florida_parcels;