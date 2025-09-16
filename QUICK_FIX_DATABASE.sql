-- QUICK DATABASE SETUP FOR CONCORDBROKER
-- Run this entire script in Supabase SQL Editor to get data showing on localhost

-- Step 1: Create the main table
CREATE TABLE IF NOT EXISTS florida_parcels (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    county VARCHAR(50),
    year INTEGER,
    owner_name VARCHAR(255),
    owner_addr1 VARCHAR(255),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    phy_addr1 VARCHAR(255),
    phy_city VARCHAR(100),
    phy_state VARCHAR(2) DEFAULT 'FL',
    phy_zipcd VARCHAR(10),
    just_value FLOAT,
    assessed_value FLOAT,
    taxable_value FLOAT,
    land_value FLOAT,
    building_value FLOAT,
    year_built INTEGER,
    total_living_area FLOAT,
    bedrooms INTEGER,
    bathrooms FLOAT,
    land_sqft FLOAT,
    sale_date TIMESTAMP,
    sale_price FLOAT,
    property_use VARCHAR(10),
    import_date TIMESTAMP DEFAULT NOW()
);

-- Step 2: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_parcels_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_parcels_owner ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_parcels_city ON florida_parcels(phy_city);

-- Step 3: Insert 100 sample properties with realistic Florida data
INSERT INTO florida_parcels (
    parcel_id, county, year, owner_name, owner_addr1, owner_city, owner_state, owner_zip,
    phy_addr1, phy_city, phy_zipcd, just_value, assessed_value, taxable_value,
    land_value, building_value, year_built, total_living_area, bedrooms, bathrooms,
    land_sqft, sale_date, sale_price, property_use
) VALUES
-- Fort Lauderdale Properties
('494204010010', 'Broward', 2025, 'JOHNSON ROBERT & MARY', '123 OCEAN BLVD', 'FORT LAUDERDALE', 'FL', '33301', '123 OCEAN BLVD', 'FORT LAUDERDALE', '33301', 850000, 765000, 680000, 350000, 500000, 2015, 2800, 4, 3, 8500, '2023-03-15', 825000, '0100'),
('494204010020', 'Broward', 2025, 'SMITH FAMILY TRUST', '456 LAS OLAS BLVD', 'FORT LAUDERDALE', 'FL', '33301', '456 LAS OLAS BLVD', 'FORT LAUDERDALE', '33301', 1250000, 1125000, 1000000, 500000, 750000, 2018, 3500, 5, 4, 10000, '2022-11-20', 1200000, '0100'),
('494204010030', 'Broward', 2025, 'WILLIAMS DAVID', '789 BEACH DR', 'FORT LAUDERDALE', 'FL', '33304', '789 BEACH DR', 'FORT LAUDERDALE', '33304', 650000, 585000, 520000, 250000, 400000, 2010, 2200, 3, 2.5, 7000, '2023-06-10', 640000, '0100'),
('494204010040', 'Broward', 2025, 'GARCIA INVESTMENTS LLC', '321 SUNRISE BLVD', 'FORT LAUDERDALE', 'FL', '33304', '321 SUNRISE BLVD', 'FORT LAUDERDALE', '33304', 450000, 405000, 360000, 150000, 300000, 2005, 1800, 3, 2, 6000, '2024-01-15', 460000, '0100'),
('494204010050', 'Broward', 2025, 'BROWN JENNIFER', '654 BAYVIEW DR', 'FORT LAUDERDALE', 'FL', '33301', '654 BAYVIEW DR', 'FORT LAUDERDALE', '33301', 950000, 855000, 760000, 400000, 550000, 2020, 3200, 4, 3.5, 9000, NULL, NULL, '0100'),

-- Hollywood Properties
('504205020010', 'Broward', 2025, 'MARTINEZ CARLOS & SOFIA', '100 HOLLYWOOD BLVD', 'HOLLYWOOD', 'FL', '33019', '100 HOLLYWOOD BLVD', 'HOLLYWOOD', '33019', 380000, 342000, 304000, 120000, 260000, 2000, 1600, 3, 2, 5500, '2023-09-12', 375000, '0100'),
('504205020020', 'Broward', 2025, 'DAVIS PROPERTIES INC', '200 OCEAN DR', 'HOLLYWOOD', 'FL', '33019', '200 OCEAN DR', 'HOLLYWOOD', '33019', 750000, 675000, 600000, 300000, 450000, 2012, 2600, 4, 3, 8000, '2022-07-25', 720000, '0100'),
('504205020030', 'Broward', 2025, 'THOMPSON MICHAEL', '300 BEACH WALK', 'HOLLYWOOD', 'FL', '33019', '300 BEACH WALK', 'HOLLYWOOD', '33019', 580000, 522000, 464000, 200000, 380000, 2008, 2000, 3, 2, 6500, '2024-02-28', 590000, '0100'),
('504205020040', 'Broward', 2025, 'WILSON ESTATE', '400 POLK ST', 'HOLLYWOOD', 'FL', '33020', '400 POLK ST', 'HOLLYWOOD', '33020', 420000, 378000, 336000, 140000, 280000, 1995, 1700, 3, 2, 5000, NULL, NULL, '0100'),
('504205020050', 'Broward', 2025, 'ANDERSON TRUST', '500 TYLER ST', 'HOLLYWOOD', 'FL', '33021', '500 TYLER ST', 'HOLLYWOOD', '33021', 520000, 468000, 416000, 180000, 340000, 2003, 1900, 3, 2.5, 6000, '2023-12-05', 515000, '0100'),

-- Pompano Beach Properties
('514206030010', 'Broward', 2025, 'RODRIGUEZ FAMILY', '111 ATLANTIC BLVD', 'POMPANO BEACH', 'FL', '33060', '111 ATLANTIC BLVD', 'POMPANO BEACH', '33060', 340000, 306000, 272000, 100000, 240000, 1998, 1500, 3, 2, 5000, '2023-04-20', 335000, '0100'),
('514206030020', 'Broward', 2025, 'THOMAS WILLIAM & LINDA', '222 BEACH RD', 'POMPANO BEACH', 'FL', '33062', '222 BEACH RD', 'POMPANO BEACH', '33062', 680000, 612000, 544000, 250000, 430000, 2016, 2400, 4, 3, 7500, '2022-10-15', 670000, '0100'),
('514206030030', 'Broward', 2025, 'CLARK INVESTMENTS', '333 OCEAN PKWY', 'POMPANO BEACH', 'FL', '33062', '333 OCEAN PKWY', 'POMPANO BEACH', '33062', 890000, 801000, 712000, 350000, 540000, 2019, 3000, 4, 3.5, 8500, NULL, NULL, '0100'),
('514206030040', 'Broward', 2025, 'WHITE JOHN', '444 CYPRESS RD', 'POMPANO BEACH', 'FL', '33064', '444 CYPRESS RD', 'POMPANO BEACH', '33064', 310000, 279000, 248000, 90000, 220000, 1992, 1400, 2, 2, 4500, '2024-01-30', 315000, '0100'),
('514206030050', 'Broward', 2025, 'LEWIS PROPERTIES LLC', '555 SAMPLE RD', 'POMPANO BEACH', 'FL', '33064', '555 SAMPLE RD', 'POMPANO BEACH', '33064', 450000, 405000, 360000, 150000, 300000, 2006, 1800, 3, 2, 6000, '2023-08-18', 445000, '0100'),

-- Coral Springs Properties
('524207040010', 'Broward', 2025, 'MOORE FAMILY TRUST', '100 CORAL RIDGE DR', 'CORAL SPRINGS', 'FL', '33071', '100 CORAL RIDGE DR', 'CORAL SPRINGS', '33071', 480000, 432000, 384000, 160000, 320000, 2004, 2100, 4, 2.5, 7000, '2023-05-22', 475000, '0100'),
('524207040020', 'Broward', 2025, 'TAYLOR ROBERT', '200 UNIVERSITY DR', 'CORAL SPRINGS', 'FL', '33071', '200 UNIVERSITY DR', 'CORAL SPRINGS', '33071', 550000, 495000, 440000, 180000, 370000, 2009, 2300, 4, 3, 7500, NULL, NULL, '0100'),
('524207040030', 'Broward', 2025, 'HARRIS DEVELOPMENT', '300 WILES RD', 'CORAL SPRINGS', 'FL', '33076', '300 WILES RD', 'CORAL SPRINGS', '33076', 620000, 558000, 496000, 200000, 420000, 2014, 2500, 4, 3, 8000, '2022-12-10', 615000, '0100'),
('524207040040', 'Broward', 2025, 'MARTIN SUSAN', '400 SAMPLE RD', 'CORAL SPRINGS', 'FL', '33065', '400 SAMPLE RD', 'CORAL SPRINGS', '33065', 390000, 351000, 312000, 130000, 260000, 2001, 1700, 3, 2, 5500, '2024-03-05', 395000, '0100'),
('524207040050', 'Broward', 2025, 'JACKSON ESTATES', '500 RIVERSIDE DR', 'CORAL SPRINGS', '33071', '500 RIVERSIDE DR', 'CORAL SPRINGS', '33071', 720000, 648000, 576000, 240000, 480000, 2017, 2800, 5, 3.5, 9000, '2023-07-14', 710000, '0100'),

-- Pembroke Pines Properties
('534208050010', 'Broward', 2025, 'PEREZ ANTONIO', '111 PINES BLVD', 'PEMBROKE PINES', 'FL', '33024', '111 PINES BLVD', 'PEMBROKE PINES', '33024', 410000, 369000, 328000, 140000, 270000, 2002, 1800, 3, 2, 6000, '2023-11-08', 405000, '0100'),
('534208050020', 'Broward', 2025, 'WALKER INVESTMENTS', '222 SHERIDAN ST', 'PEMBROKE PINES', 'FL', '33025', '222 SHERIDAN ST', 'PEMBROKE PINES', '33025', 520000, 468000, 416000, 170000, 350000, 2007, 2200, 4, 2.5, 7000, '2022-09-30', 515000, '0100'),
('534208050030', 'Broward', 2025, 'YOUNG FAMILY LLC', '333 DYKES RD', 'PEMBROKE PINES', 'FL', '33025', '333 DYKES RD', 'PEMBROKE PINES', '33025', 650000, 585000, 520000, 220000, 430000, 2013, 2600, 4, 3, 8000, NULL, NULL, '0100'),
('534208050040', 'Broward', 2025, 'ALLEN RICHARD & PATRICIA', '444 FLAMINGO RD', 'PEMBROKE PINES', 'FL', '33027', '444 FLAMINGO RD', 'PEMBROKE PINES', '33027', 380000, 342000, 304000, 120000, 260000, 1999, 1600, 3, 2, 5500, '2024-02-14', 385000, '0100'),
('534208050050', 'Broward', 2025, 'WRIGHT PROPERTIES', '555 JOHNSON ST', 'PEMBROKE PINES', 'FL', '33029', '555 JOHNSON ST', 'PEMBROKE PINES', '33029', 470000, 423000, 376000, 160000, 310000, 2005, 2000, 3, 2.5, 6500, '2023-06-25', 465000, '0100'),

-- Additional Properties to reach 100
('544209060010', 'Broward', 2025, 'RIVERA HOLDINGS', '100 DAVIE BLVD', 'DAVIE', 'FL', '33314', '100 DAVIE BLVD', 'DAVIE', '33314', 580000, 522000, 464000, 200000, 380000, 2011, 2400, 4, 3, 10000, '2023-03-18', 575000, '0100'),
('544209060020', 'Broward', 2025, 'SCOTT ENTERPRISES', '200 GRIFFIN RD', 'DAVIE', 'FL', '33314', '200 GRIFFIN RD', 'DAVIE', '33314', 750000, 675000, 600000, 300000, 450000, 2015, 3000, 5, 3.5, 15000, NULL, NULL, '0100'),
('554210070010', 'Broward', 2025, 'CAMPBELL TRUST', '100 BROWARD BLVD', 'PLANTATION', 'FL', '33317', '100 BROWARD BLVD', 'PLANTATION', '33317', 490000, 441000, 392000, 170000, 320000, 2006, 2100, 3, 2.5, 7000, '2022-11-12', 485000, '0100'),
('554210070020', 'Broward', 2025, 'GREEN INVESTMENTS', '200 PETERS RD', 'PLANTATION', 'FL', '33324', '200 PETERS RD', 'PLANTATION', '33324', 620000, 558000, 496000, 210000, 410000, 2012, 2500, 4, 3, 8500, '2023-09-05', 615000, '0100'),
('564211080010', 'Broward', 2025, 'BAKER PROPERTIES', '100 SUNRISE LAKES', 'SUNRISE', 'FL', '33322', '100 SUNRISE LAKES', 'SUNRISE', '33322', 360000, 324000, 288000, 120000, 240000, 2000, 1500, 2, 2, 5000, '2024-01-22', 365000, '0100');

-- Add more realistic properties (continuing pattern)
INSERT INTO florida_parcels (
    parcel_id, county, year, owner_name, owner_addr1, owner_city, owner_state, owner_zip,
    phy_addr1, phy_city, phy_zipcd, just_value, assessed_value, taxable_value,
    land_value, building_value, year_built, total_living_area, bedrooms, bathrooms,
    land_sqft, property_use
) 
SELECT 
    '60' || (4212080000 + generate_series)::text,
    'Broward',
    2025,
    CASE (generate_series % 10)
        WHEN 0 THEN 'OCEAN VIEW PROPERTIES LLC'
        WHEN 1 THEN 'SUNSHINE INVESTMENTS'
        WHEN 2 THEN 'COASTAL HOLDINGS INC'
        WHEN 3 THEN 'PALM TREE ESTATES'
        WHEN 4 THEN 'ATLANTIC TRUST'
        WHEN 5 THEN 'BEACH FRONT LLC'
        WHEN 6 THEN 'FLORIDA DREAM HOMES'
        WHEN 7 THEN 'TROPICAL PARADISE INC'
        WHEN 8 THEN 'SUNSET PROPERTIES'
        ELSE 'BAYVIEW DEVELOPMENT'
    END,
    (100 + generate_series)::text || ' MAIN ST',
    CASE (generate_series % 5)
        WHEN 0 THEN 'FORT LAUDERDALE'
        WHEN 1 THEN 'HOLLYWOOD'
        WHEN 2 THEN 'POMPANO BEACH'
        WHEN 3 THEN 'CORAL SPRINGS'
        ELSE 'PEMBROKE PINES'
    END,
    'FL',
    CASE (generate_series % 5)
        WHEN 0 THEN '33301'
        WHEN 1 THEN '33019'
        WHEN 2 THEN '33060'
        WHEN 3 THEN '33071'
        ELSE '33024'
    END,
    (100 + generate_series)::text || 
    CASE (generate_series % 8)
        WHEN 0 THEN ' OCEAN BLVD'
        WHEN 1 THEN ' BEACH DR'
        WHEN 2 THEN ' PALM AVE'
        WHEN 3 THEN ' SUNSET BLVD'
        WHEN 4 THEN ' BAY VIEW DR'
        WHEN 5 THEN ' CORAL WAY'
        WHEN 6 THEN ' ATLANTIC AVE'
        ELSE ' RIVERSIDE DR'
    END,
    CASE (generate_series % 5)
        WHEN 0 THEN 'FORT LAUDERDALE'
        WHEN 1 THEN 'HOLLYWOOD'
        WHEN 2 THEN 'POMPANO BEACH'
        WHEN 3 THEN 'CORAL SPRINGS'
        ELSE 'PEMBROKE PINES'
    END,
    CASE (generate_series % 5)
        WHEN 0 THEN '33301'
        WHEN 1 THEN '33019'
        WHEN 2 THEN '33060'
        WHEN 3 THEN '33071'
        ELSE '33024'
    END,
    350000 + (generate_series * 5000) + (random() * 100000)::int,
    315000 + (generate_series * 4500) + (random() * 90000)::int,
    280000 + (generate_series * 4000) + (random() * 80000)::int,
    100000 + (generate_series * 1500) + (random() * 50000)::int,
    250000 + (generate_series * 3500) + (random() * 50000)::int,
    1990 + (generate_series % 30),
    1500 + (generate_series * 10) + (random() * 500)::int,
    2 + (generate_series % 3),
    2 + (generate_series % 2),
    5000 + (generate_series * 50) + (random() * 2000)::int,
    '0100'
FROM generate_series(1, 70);

-- Step 4: Verify the data
SELECT COUNT(*) as total_properties FROM florida_parcels;

-- Step 5: Show sample data
SELECT 
    parcel_id,
    owner_name,
    phy_addr1 as address,
    phy_city as city,
    just_value,
    year_built
FROM florida_parcels 
LIMIT 10;

-- Success message
SELECT 'SUCCESS: Database populated with ' || COUNT(*) || ' properties!' as status 
FROM florida_parcels;