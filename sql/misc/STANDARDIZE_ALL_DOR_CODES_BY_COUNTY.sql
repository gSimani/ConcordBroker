-- ============================================================================
-- STANDARDIZE ALL DOR CODES - County by County Approach
-- This will OVERWRITE all existing codes with standardized classifications
-- Execute each county separately in Supabase SQL Editor to avoid timeouts
-- ============================================================================

-- BEFORE STARTING: Check current distribution
SELECT
    county,
    COUNT(*) as total,
    COUNT(CASE WHEN land_use_code IS NOT NULL THEN 1 END) as with_code,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage
FROM florida_parcels
WHERE year = 2025
GROUP BY county
ORDER BY total DESC
LIMIT 20;

-- ============================================================================
-- TEMPLATE: Copy and paste this for EACH county, changing county name
-- Start with largest counties first
-- ============================================================================

-- COUNTY: ALACHUA (example - replace with actual county name)
UPDATE florida_parcels
SET
    land_use_code = CASE
        -- Priority 1: Multi-Family 10+
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN '02'
        -- Priority 2: Industrial
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN '24'
        -- Priority 3: Commercial
        WHEN (just_value > 500000 AND building_value > 200000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN '17'
        -- Priority 4: Agricultural
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN '01'
        -- Priority 5: Condominium
        WHEN (just_value BETWEEN 100000 AND 500000
              AND building_value BETWEEN 50000 AND 300000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN '03'
        -- Priority 6: Vacant Residential
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN '10'
        -- Priority 7: Single Family
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN '00'
        -- Priority 8: Default
        ELSE '00'
    END,
    property_use = CASE
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN 'MF 10+'
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN 'Industria'
        WHEN (just_value > 500000 AND building_value > 200000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN 'Commercia'
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN 'Agricult.'
        WHEN (just_value BETWEEN 100000 AND 500000
              AND building_value BETWEEN 50000 AND 300000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN 'Condo'
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN 'Vacant Re'
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN 'SFR'
        ELSE 'SFR'
    END
WHERE year = 2025 AND county = 'ALACHUA';
-- Result: should return number of rows updated

-- Verify this county
SELECT
    land_use_code,
    property_use,
    COUNT(*) as count
FROM florida_parcels
WHERE year = 2025 AND county = 'ALACHUA'
GROUP BY land_use_code, property_use
ORDER BY count DESC;

-- ============================================================================
-- ALL 67 FLORIDA COUNTIES (Execute one at a time)
-- Copy the UPDATE template above and replace county name for each
-- ============================================================================

-- Priority Order (Largest counties first):
-- 1. DADE
-- 2. BROWARD
-- 3. PALM BEACH
-- 4. HILLSBOROUGH
-- 5. ORANGE
-- 6. PINELLAS
-- 7. DUVAL
-- 8. LEE
-- 9. POLK
-- 10. BREVARD
-- 11. VOLUSIA
-- 12. PASCO
-- 13. SEMINOLE
-- 14. COLLIER
-- 15. SARASOTA
-- 16. MANATEE
-- 17. LAKE
-- 18. MARION
-- 19. OSCEOLA
-- 20. ESCAMBIA
-- 21. ST LUCIE
-- 22. HERNANDO
-- 23. MARTIN
-- 24. CLAY
-- 25. ALACHUA
-- 26. CHARLOTTE
-- 27. SANTA ROSA
-- 28. OKALOOSA
-- 29. CITRUS
-- 30. BAY
-- 31. ST JOHNS
-- 32. INDIAN RIVER
-- 33. FLAGLER
-- 34. SUMTER
-- 35. COLUMBIA
-- 36. HIGHLANDS
-- 37. NASSAU
-- 38. PUTNAM
-- 39. LEON
-- 40. MONROE
-- 41. JACKSON
-- 42. HARDEE
-- 43. OKEECHOBEE
-- 44. DESOTO
-- 45. SUWANNEE
-- 46. HENDRY
-- 47. WALTON
-- 48. LEVY
-- 49. GADSDEN
-- 50. BAKER
-- 51. BRADFORD
-- 52. TAYLOR
-- 53. WAKULLA
-- 54. MADISON
-- 55. UNION
-- 56. GILCHRIST
-- 57. HAMILTON
-- 58. HOLMES
-- 59. DIXIE
-- 60. WASHINGTON
-- 61. JEFFERSON
-- 62. CALHOUN
-- 63. GULF
-- 64. FRANKLIN
-- 65. GLADES
-- 66. LAFAYETTE
-- 67. LIBERTY

-- ============================================================================
-- FINAL VERIFICATION - Run after all counties complete
-- ============================================================================

SELECT
    COUNT(*) as total_properties,
    COUNT(CASE WHEN land_use_code IN ('00','01','02','03','10','17','24') THEN 1 END) as standardized,
    ROUND(COUNT(CASE WHEN land_use_code IN ('00','01','02','03','10','17','24') THEN 1 END)::numeric / COUNT(*) * 100, 2) as standardized_pct
FROM florida_parcels
WHERE year = 2025;

-- Distribution of standardized codes
SELECT
    land_use_code,
    property_use,
    COUNT(*) as count,
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM florida_parcels WHERE year = 2025) * 100, 2) as percentage
FROM florida_parcels
WHERE year = 2025 AND land_use_code IN ('00','01','02','03','10','17','24')
GROUP BY land_use_code, property_use
ORDER BY count DESC;

-- ============================================================================
-- GRADING SCALE
-- ============================================================================
-- 10/10: 99.5-100% standardized (PERFECT)
-- 9/10:  95-99.4% standardized (EXCELLENT)
-- 8/10:  90-94.9% standardized (GOOD)
-- 7/10:  80-89.9% standardized (ACCEPTABLE)
