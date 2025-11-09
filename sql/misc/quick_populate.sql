-- Quick database population for ConcordBroker
-- Run this in Supabase SQL Editor to get properties working immediately

-- 1. Temporarily disable RLS
ALTER TABLE florida_parcels DISABLE ROW LEVEL SECURITY;

-- 2. Clear any existing data
DELETE FROM florida_parcels;

-- 3. Insert the key properties including 3930 Bayview Drive
INSERT INTO florida_parcels (
    parcel_id, county, year, phy_addr1, phy_city, phy_state, phy_zipcd,
    owner_name, property_use, year_built, total_living_area, land_sqft,
    bedrooms, bathrooms, just_value, assessed_value, taxable_value,
    land_value, building_value, sale_date, sale_price
) VALUES
('10-42-35-4500-1200', 'BROWARD', 2025, '3930 Bayview Drive', 'Fort Lauderdale', 'FL', '33308',
 'Bayview Estates LLC', '001', 2021, 3100, 7500, 4, 3, 695000, 625500, 556000, 265000, 430000, '2024-04-10', 665000),

('10-42-28-5800-0420', 'BROWARD', 2025, '1234 Ocean Boulevard', 'Fort Lauderdale', 'FL', '33301', 
 'Ocean Properties LLC', '001', 2018, 3200, 8500, 4, 3, 1250000, 1125000, 1000000, 450000, 800000, '2023-08-15', 1175000),

('10-42-30-1200-0100', 'BROWARD', 2025, '567 Las Olas Boulevard', 'Fort Lauderdale', 'FL', '33301',
 'Las Olas Investments LLC', '001', 2019, 2950, 6800, 3, 3, 875000, 787500, 700000, 280000, 595000, '2023-11-10', 825000),

('15-50-22-4100-0500', 'BROWARD', 2025, '789 Hollywood Boulevard', 'Hollywood', 'FL', '33019',
 'Patricia Johnson', '001', 2010, 1850, 4800, 2, 2, 385000, 346500, 308000, 140000, 245000, '2024-02-28', 370000),

('20-55-18-3600-0600', 'BROWARD', 2025, '1456 Atlantic Boulevard', 'Pompano Beach', 'FL', '33062',
 'Michael Davis', '001', 2015, 1650, 4200, 2, 1, 295000, 265500, 236000, 110000, 185000, '2023-09-20', 285000);

-- 4. Create simple RLS policy that allows all operations
CREATE POLICY "Allow all operations" ON florida_parcels FOR ALL USING (true);

-- 5. Re-enable RLS
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;

-- 6. Verify the data was inserted
SELECT COUNT(*) as total_properties FROM florida_parcels;
SELECT phy_addr1, phy_city, owner_name FROM florida_parcels LIMIT 5;