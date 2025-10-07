-- ============================================================================
-- DOR Use Code Assignment SQL - Direct Execution for 9.1M Properties
-- Execute in Supabase SQL Editor with service_role privileges
-- ============================================================================

-- PHASE 1: CHECK CURRENT STATUS BEFORE EXECUTION
-- ============================================================================
SELECT
    COUNT(*) as total_properties,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code,
    COUNT(CASE WHEN land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99' THEN 1 END) as need_update,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025;

-- PHASE 2: MAIN ASSIGNMENT - UPDATE ALL PROPERTIES
-- ============================================================================
-- This assigns DOR codes to all 5.95M properties that need them
-- Expected execution time: 15-30 minutes
-- ============================================================================

UPDATE florida_parcels
SET
    land_use_code = CASE
        -- Multi-Family 10+ (Priority 1)
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN '02'
        -- Industrial (Priority 2)
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN '24'
        -- Commercial (Priority 3)
        WHEN (just_value > 500000 AND building_value > 200000 AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN '17'
        -- Agricultural (Priority 4)
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN '01'
        -- Condominium (Priority 5)
        WHEN (just_value BETWEEN 100000 AND 500000 AND building_value BETWEEN 50000 AND 300000 AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN '03'
        -- Vacant Residential (Priority 6)
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN '10'
        -- Single Family (Priority 7)
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN '00'
        -- Default (Priority 8)
        ELSE '00'
    END,
    property_use = CASE
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN 'MF 10+'
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN 'Industria'
        WHEN (just_value > 500000 AND building_value > 200000 AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN 'Commercia'
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN 'Agricult.'
        WHEN (just_value BETWEEN 100000 AND 500000 AND building_value BETWEEN 50000 AND 300000 AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN 'Condo'
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN 'Vacant Re'
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN 'SFR'
        ELSE 'SFR'
    END
WHERE year = 2025
    AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99');

-- PHASE 3: VERIFY RESULTS
-- ============================================================================
SELECT
    COUNT(*) as total_properties,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025;

-- PHASE 4: DISTRIBUTION ANALYSIS
-- ============================================================================
SELECT
    land_use_code,
    property_use,
    COUNT(*) as count,
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM florida_parcels WHERE year = 2025) * 100, 2) as percentage
FROM florida_parcels
WHERE year = 2025 AND land_use_code IS NOT NULL
GROUP BY land_use_code, property_use
ORDER BY count DESC
LIMIT 20;
