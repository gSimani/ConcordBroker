-- FIX TABLE STRUCTURES AND LOAD SAMPLE DATA
-- Run this in Supabase SQL Editor to fix tables and add sample data

-- STEP 1: Fix property_sales_history table
ALTER TABLE property_sales_history 
ADD COLUMN IF NOT EXISTS grantor_name TEXT,
ADD COLUMN IF NOT EXISTS grantee_name TEXT,
ADD COLUMN IF NOT EXISTS sale_type VARCHAR(10),
ADD COLUMN IF NOT EXISTS vi_code VARCHAR(10),
ADD COLUMN IF NOT EXISTS qualified_sale BOOLEAN;

-- STEP 2: Fix nav_assessments table (remove 'amount' column requirement)
ALTER TABLE nav_assessments
ADD COLUMN IF NOT EXISTS parcel_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS district_name VARCHAR(200),
ADD COLUMN IF NOT EXISTS total_assessment NUMERIC,
ADD COLUMN IF NOT EXISTS millage_rate NUMERIC;

-- STEP 3: Insert sample sales data
INSERT INTO property_sales_history (parcel_id, sale_date, sale_price, grantor_name, grantee_name, sale_type)
VALUES 
('064210010010', '2023-06-15', 450000, 'Smith John', 'Johnson Mary', 'WD'),
('064210010010', '2021-03-20', 380000, 'Brown David', 'Smith John', 'WD'),
('064210010010', '2019-08-10', 320000, 'Williams Robert', 'Brown David', 'QC'),
('064210010020', '2024-01-05', 525000, 'Davis Michael', 'Anderson Lisa', 'WD'),
('064210010020', '2022-07-12', 475000, 'Miller James', 'Davis Michael', 'WD'),
('064210010030', '2023-11-20', 680000, 'Wilson Patricia', 'Garcia Carlos', 'WD'),
('064210010040', '2023-09-08', 395000, 'Martinez Jose', 'Thompson Sarah', 'WD'),
('064210010050', '2024-02-14', 550000, 'Rodriguez Maria', 'Lee David', 'WD'),
('064210010060', '2023-12-01', 425000, 'Lewis Karen', 'Hall Christopher', 'QC'),
('064210010070', '2023-05-22', 490000, 'Walker Nancy', 'Young Brian', 'WD')
ON CONFLICT DO NOTHING;

-- STEP 4: Insert sample NAV assessments
INSERT INTO nav_assessments (parcel_id, district_name, total_assessment, millage_rate)
VALUES 
('064210010010', 'BROWARD COUNTY', 8500.00, 20.5),
('064210010010', 'SCHOOL BOARD', 4200.00, 10.2),
('064210010020', 'BROWARD COUNTY', 9800.00, 20.5),
('064210010020', 'SCHOOL BOARD', 4850.00, 10.2),
('064210010030', 'BROWARD COUNTY', 12000.00, 20.5),
('064210010040', 'BROWARD COUNTY', 7200.00, 20.5),
('064210010050', 'BROWARD COUNTY', 10500.00, 20.5),
('064210010060', 'BROWARD COUNTY', 8100.00, 20.5),
('064210010070', 'BROWARD COUNTY', 9400.00, 20.5),
('064210010080', 'BROWARD COUNTY', 6800.00, 20.5)
ON CONFLICT DO NOTHING;

-- STEP 5: Insert sample Sunbiz corporate entities
INSERT INTO sunbiz_corporate (corporate_name, entity_type, status, principal_address, filing_date, entity_id)
VALUES 
('SUNSHINE PROPERTIES LLC', 'LLC', 'ACTIVE', '123 MAIN ST FORT LAUDERDALE FL', '2019-05-15', 'L19000123456'),
('BEACH HOLDINGS INC', 'CORPORATION', 'ACTIVE', '456 OCEAN BLVD FORT LAUDERDALE FL', '2018-03-20', 'P18000098765'),
('FLORIDA INVESTMENTS LLC', 'LLC', 'ACTIVE', '789 PALM AVE MIAMI FL', '2020-01-10', 'L20000234567'),
('COASTAL DEVELOPMENT CORP', 'CORPORATION', 'ACTIVE', '321 BEACH RD BOCA RATON FL', '2017-11-25', 'P17000187654'),
('EVERGLADES REALTY LLC', 'LLC', 'ACTIVE', '654 GLADES WAY WESTON FL', '2021-06-30', 'L21000345678'),
('ATLANTIC PROPERTIES INC', 'CORPORATION', 'ACTIVE', '987 ATLANTIC AVE DELRAY BEACH FL', '2019-09-12', 'P19000276543'),
('MIAMI VENTURES LLC', 'LLC', 'ACTIVE', '246 BISCAYNE BLVD MIAMI FL', '2022-02-28', 'L22000456789'),
('BROWARD ESTATES CORP', 'CORPORATION', 'ACTIVE', '135 BROWARD BLVD FORT LAUDERDALE FL', '2020-07-15', 'P20000365432'),
('SUNRISE HOLDINGS LLC', 'LLC', 'ACTIVE', '579 SUNRISE BLVD PLANTATION FL', '2018-12-05', 'L18000567890'),
('PALM BEACH PROPERTIES INC', 'CORPORATION', 'ACTIVE', '864 PALM BEACH LAKES BLVD WEST PALM BEACH FL', '2021-04-18', 'P21000454321')
ON CONFLICT DO NOTHING;

-- STEP 6: Refresh materialized view with new data
REFRESH MATERIALIZED VIEW property_search_fast;

-- STEP 7: Verify data was loaded
SELECT 
    'property_sales_history' as table_name,
    COUNT(*) as record_count
FROM property_sales_history
UNION ALL
SELECT 
    'nav_assessments' as table_name,
    COUNT(*) as record_count
FROM nav_assessments
UNION ALL
SELECT 
    'sunbiz_corporate' as table_name,
    COUNT(*) as record_count
FROM sunbiz_corporate;

-- Test that search still works
SELECT * FROM property_search_fast LIMIT 5;