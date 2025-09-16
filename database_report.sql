-- COMPREHENSIVE DATABASE REPORT FOR CONCORDBROKER
-- Generated: 2025-09-08
-- ================================================

-- 1. LIST ALL TABLES IN THE DATABASE
-- -----------------------------------
SELECT 
    table_schema AS schema,
    table_name AS table,
    table_type AS type
FROM 
    information_schema.tables 
WHERE 
    table_schema NOT IN ('pg_catalog', 'information_schema')
    AND table_schema NOT LIKE 'pg_toast%'
    AND table_type = 'BASE TABLE'
ORDER BY 
    table_schema, table_name;

-- 2. TABLE ROW COUNTS AND SIZES
-- ------------------------------
WITH table_stats AS (
    SELECT 'florida_parcels' AS table_name, COUNT(*) AS row_count FROM florida_parcels
    UNION ALL
    SELECT 'properties', COUNT(*) FROM properties
    UNION ALL
    SELECT 'property_sales_history', COUNT(*) FROM property_sales_history
    UNION ALL
    SELECT 'nav_assessments', COUNT(*) FROM nav_assessments
    UNION ALL
    SELECT 'sunbiz_corporate', COUNT(*) FROM sunbiz_corporate
    UNION ALL
    SELECT 'sunbiz_fictitious', COUNT(*) FROM sunbiz_fictitious
    UNION ALL
    SELECT 'sunbiz_corporate_events', COUNT(*) FROM sunbiz_corporate_events
)
SELECT 
    table_name,
    row_count,
    CASE 
        WHEN row_count = 0 THEN 'EMPTY - Needs Data'
        WHEN row_count < 100 THEN 'Low Data'
        WHEN row_count < 1000 THEN 'Moderate Data'
        ELSE 'Good Data'
    END AS status
FROM table_stats
ORDER BY row_count DESC;

-- 3. FLORIDA_PARCELS TABLE STRUCTURE
-- -----------------------------------
SELECT 
    column_name,
    data_type,
    character_maximum_length AS max_length,
    is_nullable,
    column_default
FROM 
    information_schema.columns
WHERE 
    table_name = 'florida_parcels'
    AND table_schema = 'public'
ORDER BY 
    ordinal_position
LIMIT 20;

-- 4. FLORIDA_PARCELS DATA STATISTICS
-- -----------------------------------
SELECT
    'Total Properties' AS metric,
    COUNT(*)::text AS value
FROM florida_parcels
UNION ALL
SELECT
    'Unique Cities',
    COUNT(DISTINCT phy_city)::text
FROM florida_parcels
UNION ALL
SELECT
    'Unique ZIP Codes',
    COUNT(DISTINCT phy_zipcd)::text
FROM florida_parcels
UNION ALL
SELECT
    'Properties with Owner Name',
    COUNT(CASE WHEN owner_name IS NOT NULL THEN 1 END)::text
FROM florida_parcels
UNION ALL
SELECT
    'Properties with Taxable Value',
    COUNT(CASE WHEN taxable_value > 0 THEN 1 END)::text
FROM florida_parcels
UNION ALL
SELECT
    'Average Taxable Value',
    COALESCE(ROUND(AVG(taxable_value))::text, '0')
FROM florida_parcels
WHERE taxable_value > 0
UNION ALL
SELECT
    'Properties with Year Built',
    COUNT(CASE WHEN year_built > 0 THEN 1 END)::text
FROM florida_parcels
UNION ALL
SELECT
    'Properties with Living Area',
    COUNT(CASE WHEN total_living_area > 0 THEN 1 END)::text
FROM florida_parcels;

-- 5. CITY DISTRIBUTION
-- --------------------
SELECT 
    phy_city AS city,
    COUNT(*) AS property_count,
    ROUND(AVG(taxable_value)) AS avg_value,
    MIN(year_built) AS oldest_property,
    MAX(year_built) AS newest_property
FROM florida_parcels
WHERE phy_city IS NOT NULL
GROUP BY phy_city
ORDER BY property_count DESC
LIMIT 15;

-- 6. PROPERTY TYPE DISTRIBUTION
-- ------------------------------
SELECT 
    property_use AS use_code,
    property_use_desc AS description,
    COUNT(*) AS count,
    ROUND(AVG(taxable_value)) AS avg_value
FROM florida_parcels
WHERE property_use IS NOT NULL
GROUP BY property_use, property_use_desc
ORDER BY count DESC
LIMIT 20;

-- 7. SAMPLE PROPERTIES FOR TESTING
-- ---------------------------------
SELECT 
    parcel_id,
    phy_addr1 AS address,
    phy_city AS city,
    owner_name,
    taxable_value,
    year_built,
    total_living_area AS sqft
FROM florida_parcels
WHERE 
    phy_addr1 IS NOT NULL 
    AND phy_city IS NOT NULL
    AND owner_name IS NOT NULL
    AND taxable_value > 0
ORDER BY RANDOM()
LIMIT 10;

-- 8. CHECK EMPTY TABLES (SUNBIZ)
-- -------------------------------
SELECT 
    'sunbiz_corporate' AS table_name,
    COUNT(*) AS records,
    CASE 
        WHEN COUNT(*) = 0 THEN 'NEEDS DATA LOAD'
        ELSE 'HAS DATA'
    END AS status
FROM sunbiz_corporate
UNION ALL
SELECT 
    'sunbiz_fictitious',
    COUNT(*),
    CASE 
        WHEN COUNT(*) = 0 THEN 'NEEDS DATA LOAD'
        ELSE 'HAS DATA'
    END
FROM sunbiz_fictitious
UNION ALL
SELECT 
    'sunbiz_corporate_events',
    COUNT(*),
    CASE 
        WHEN COUNT(*) = 0 THEN 'NEEDS DATA LOAD'
        ELSE 'HAS DATA'
    END
FROM sunbiz_corporate_events
UNION ALL
SELECT 
    'property_sales_history',
    COUNT(*),
    CASE 
        WHEN COUNT(*) = 0 THEN 'NEEDS DATA LOAD'
        ELSE 'HAS DATA'
    END
FROM property_sales_history
UNION ALL
SELECT 
    'nav_assessments',
    COUNT(*),
    CASE 
        WHEN COUNT(*) = 0 THEN 'NEEDS DATA LOAD'
        ELSE 'HAS DATA'
    END
FROM nav_assessments;

-- 9. SPECIFIC PROPERTY LOOKUP (YOUR EXAMPLE)
-- -------------------------------------------
SELECT 
    parcel_id,
    phy_addr1 AS address,
    phy_city AS city,
    phy_zipcd AS zip,
    owner_name,
    just_value,
    taxable_value,
    land_value,
    year_built,
    total_living_area
FROM florida_parcels
WHERE 
    phy_addr1 LIKE '%3930%SW%53%'
    OR owner_name LIKE '%SIMANI%'
LIMIT 5;

-- 10. DATABASE HEALTH SUMMARY
-- ----------------------------
WITH health_check AS (
    SELECT 
        (SELECT COUNT(*) FROM florida_parcels) AS florida_parcels_count,
        (SELECT COUNT(*) FROM properties) AS properties_count,
        (SELECT COUNT(*) FROM sunbiz_corporate) AS sunbiz_corp_count,
        (SELECT COUNT(*) FROM property_sales_history) AS sales_history_count
)
SELECT 
    'Florida Parcels' AS component,
    florida_parcels_count AS records,
    CASE 
        WHEN florida_parcels_count > 0 THEN 'OPERATIONAL'
        ELSE 'NEEDS DATA'
    END AS status
FROM health_check
UNION ALL
SELECT 
    'Properties Table',
    properties_count,
    CASE 
        WHEN properties_count > 0 THEN 'OPERATIONAL'
        ELSE 'NEEDS DATA'
    END
FROM health_check
UNION ALL
SELECT 
    'Sunbiz Corporate',
    sunbiz_corp_count,
    CASE 
        WHEN sunbiz_corp_count > 0 THEN 'OPERATIONAL'
        ELSE 'NEEDS DATA'
    END
FROM health_check
UNION ALL
SELECT 
    'Sales History',
    sales_history_count,
    CASE 
        WHEN sales_history_count > 0 THEN 'OPERATIONAL'
        ELSE 'NEEDS DATA'
    END
FROM health_check;