-- Fix property_use codes based on NAICS codes and property characteristics
-- Run this in Supabase SQL Editor

-- First, let's set property_use based on NAICS codes
-- NAICS codes give us industry classification which we can map to property types

-- Residential properties (NAICS codes for residential-related)
UPDATE florida_parcels 
SET property_use = '001'  -- Single Family Residential
WHERE property_use IS NULL 
AND (
    -- Residential rental (531110 is common for residential rentals)
    data_source LIKE '%531110%'
    -- Or based on value/size characteristics typical of residential
    OR (taxable_value < 2000000 AND taxable_value > 50000 AND total_living_area < 10000)
    -- Or owner names that indicate residential
    OR owner_name LIKE '%HOMES%'
    OR owner_name LIKE '%RESIDENCE%'
    OR owner_name LIKE '%FAMILY%'
    OR phy_addr1 LIKE '%DR'
    OR phy_addr1 LIKE '%CT'
    OR phy_addr1 LIKE '%LN'
    OR phy_addr1 LIKE '%WAY'
    OR phy_addr1 LIKE '%TER'
);

-- Commercial properties
UPDATE florida_parcels 
SET property_use = '200'  -- Commercial
WHERE property_use IS NULL 
AND (
    -- Commercial indicators
    owner_name LIKE '%LLC%'
    OR owner_name LIKE '%CORP%'
    OR owner_name LIKE '%INC%'
    OR owner_name LIKE '%COMPANY%'
    OR owner_name LIKE '%ASSOCIATES%'
    OR owner_name LIKE '%PARTNERS%'
    OR owner_name LIKE '%PROPERTIES%'
    OR owner_name LIKE '%INVESTMENT%'
    OR owner_name LIKE '%HOTEL%'
    OR owner_name LIKE '%RETAIL%'
    OR owner_name LIKE '%OFFICE%'
    OR owner_name LIKE '%PLAZA%'
    OR owner_name LIKE '%CENTER%'
    OR phy_addr1 LIKE '%BLVD%'
    OR phy_addr1 LIKE '%AVE%'
    OR phy_addr1 LIKE '%HIGHWAY%'
);

-- Industrial properties  
UPDATE florida_parcels 
SET property_use = '400'  -- Industrial
WHERE property_use IS NULL
AND (
    owner_name LIKE '%INDUSTRIAL%'
    OR owner_name LIKE '%WAREHOUSE%'
    OR owner_name LIKE '%DISTRIBUTION%'
    OR owner_name LIKE '%MANUFACTURING%'
    OR owner_name LIKE '%LOGISTICS%'
);

-- Utility properties (like Florida Power & Light)
UPDATE florida_parcels 
SET property_use = '901'  -- Utility
WHERE property_use IS NULL
AND (
    owner_name LIKE '%POWER%'
    OR owner_name LIKE '%ELECTRIC%'
    OR owner_name LIKE '%UTILITY%'
    OR owner_name LIKE '%WATER%'
    OR owner_name LIKE '%GAS%'
);

-- Government properties
UPDATE florida_parcels 
SET property_use = '800'  -- Government
WHERE property_use IS NULL
AND (
    owner_name LIKE '%COUNTY%'
    OR owner_name LIKE '%CITY OF%'
    OR owner_name LIKE '%STATE OF%'
    OR owner_name LIKE '%SCHOOL%'
    OR owner_name LIKE '%DISTRICT%'
    OR owner_name LIKE '%GOVERNMENT%'
);

-- Default remaining nulls to residential
UPDATE florida_parcels 
SET property_use = '001'
WHERE property_use IS NULL
AND taxable_value > 0;

-- Verify the distribution
SELECT 
    CASE 
        WHEN property_use BETWEEN '001' AND '099' THEN 'Residential'
        WHEN property_use BETWEEN '100' AND '199' THEN 'Mobile Home'
        WHEN property_use BETWEEN '200' AND '399' THEN 'Commercial'
        WHEN property_use BETWEEN '400' AND '499' THEN 'Industrial'
        WHEN property_use BETWEEN '500' AND '699' THEN 'Agricultural'
        WHEN property_use BETWEEN '700' AND '799' THEN 'Institutional'
        WHEN property_use BETWEEN '800' AND '899' THEN 'Government'
        WHEN property_use BETWEEN '900' AND '999' THEN 'Miscellaneous'
        ELSE 'Unknown'
    END as property_type,
    COUNT(*) as count,
    ROUND(AVG(taxable_value)) as avg_value
FROM florida_parcels
WHERE taxable_value > 0
GROUP BY property_type
ORDER BY count DESC;