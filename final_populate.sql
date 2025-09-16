-- Final database population - includes all required fields for React app
-- Run this in Supabase SQL Editor

-- 1. Disable RLS
ALTER TABLE florida_parcels DISABLE ROW LEVEL SECURITY;

-- 2. Clear existing data
DELETE FROM florida_parcels;

-- 3. Insert properties with ALL required fields including is_redacted
INSERT INTO florida_parcels (
    parcel_id, county, year, 
    phy_addr1, phy_city, phy_state, phy_zipcd,
    owner_name, property_use, year_built, 
    total_living_area, land_sqft, bedrooms, bathrooms,
    just_value, assessed_value, taxable_value,
    land_value, building_value, 
    sale_date, sale_price,
    is_redacted, data_source
) VALUES
-- Your searched property: 3930 Bayview Drive
('10-42-35-4500-1200', 'BROWARD', 2025, 
 '3930 Bayview Drive', 'Fort Lauderdale', 'FL', '33308',
 'Bayview Estates LLC', '001', 2021, 
 3100, 7500, 4, 3,
 695000, 625500, 556000,
 265000, 430000,
 '2024-04-10', 665000,
 false, 'manual_insert'),

-- Ocean Boulevard property
('10-42-28-5800-0420', 'BROWARD', 2025,
 '1234 Ocean Boulevard', 'Fort Lauderdale', 'FL', '33301', 
 'Ocean Properties LLC', '001', 2018,
 3200, 8500, 4, 3,
 1250000, 1125000, 1000000,
 450000, 800000,
 '2023-08-15', 1175000,
 false, 'manual_insert'),

-- Las Olas property
('10-42-30-1200-0100', 'BROWARD', 2025,
 '567 Las Olas Boulevard', 'Fort Lauderdale', 'FL', '33301',
 'Las Olas Investments LLC', '001', 2019,
 2950, 6800, 3, 3,
 875000, 787500, 700000,
 280000, 595000,
 '2023-11-10', 825000,
 false, 'manual_insert'),

-- Hollywood property
('15-50-22-4100-0500', 'BROWARD', 2025,
 '789 Hollywood Boulevard', 'Hollywood', 'FL', '33019',
 'Patricia Johnson', '001', 2010,
 1850, 4800, 2, 2,
 385000, 346500, 308000,
 140000, 245000,
 '2024-02-28', 370000,
 false, 'manual_insert'),

-- Pompano Beach property
('20-55-18-3600-0600', 'BROWARD', 2025,
 '1456 Atlantic Boulevard', 'Pompano Beach', 'FL', '33062',
 'Michael Davis', '001', 2015,
 1650, 4200, 2, 1,
 295000, 265500, 236000,
 110000, 185000,
 '2023-09-20', 285000,
 false, 'manual_insert');

-- 4. Create permissive RLS policy
DROP POLICY IF EXISTS "Allow all operations" ON florida_parcels;
CREATE POLICY "Allow all operations" ON florida_parcels FOR ALL USING (true);

-- 5. Re-enable RLS
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;

-- 6. Verify data
SELECT COUNT(*) as total_properties FROM florida_parcels WHERE is_redacted = false;
SELECT phy_addr1, phy_city, owner_name, is_redacted FROM florida_parcels ORDER BY phy_addr1;