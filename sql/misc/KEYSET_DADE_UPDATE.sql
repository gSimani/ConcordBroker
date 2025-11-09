-- ============================================================================
-- KEYSET PAGINATION DOR ASSIGNMENT - NO TIMEOUT, NO MANUAL TRACKING
-- Run this exact query 20-22 times to complete DADE county
-- Each run automatically processes the next 50,000 rows
-- ============================================================================

-- DADE County Update (Run this 20-22 times)
WITH next_id AS (
    SELECT MIN(id) AS start_id
    FROM florida_parcels
    WHERE year = 2025
        AND county = 'DADE'
        AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
)
UPDATE florida_parcels fp
SET
    land_use_code = CASE
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN '02'
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN '24'
        WHEN (just_value > 500000 AND building_value > 200000 AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN '17'
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN '01'
        WHEN (just_value BETWEEN 100000 AND 500000 AND building_value BETWEEN 50000 AND 300000 AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN '03'
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN '10'
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN '00'
        ELSE '00'
    END,
    property_use = CASE
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN 'MF 10+'
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN 'Industria'
        WHEN (just_value > 500000 AND building_value > 200000) THEN 'Commercia'
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN 'Agricult.'
        WHEN (just_value BETWEEN 100000 AND 500000 AND building_value BETWEEN 50000 AND 300000) THEN 'Condo'
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN 'Vacant Re'
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN 'SFR'
        ELSE 'SFR'
    END
FROM next_id n
WHERE fp.id >= n.start_id
    AND fp.id < n.start_id + 50000
    AND fp.year = 2025
    AND fp.county = 'DADE'
    AND (fp.land_use_code IS NULL OR fp.land_use_code = '' OR fp.land_use_code = '99');

-- Progress check
SELECT
    'DADE Progress' as status,
    COUNT(*) as total,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025 AND county = 'DADE';

-- ============================================================================
-- HOW IT WORKS:
-- 1. Finds the smallest id that still needs update (MIN)
-- 2. Updates a 50k id window starting from that id
-- 3. Next run automatically moves to the next batch
-- 4. No sorting, no manual tracking, fast execution
--
-- EXPECTED:
-- - ~1.08M DADE rows need updates
-- - 50k per batch = ~22 runs
-- - Each run: 10-30 seconds
-- - Total: 5-10 minutes
-- ============================================================================