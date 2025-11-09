-- ============================================================================
-- FINAL DOR ASSIGNMENT - WITH TIMEOUT PREVENTION
-- Execute this entire script in Supabase SQL Editor
-- ============================================================================

-- STEP 1: Increase timeouts for this session
SET statement_timeout = '45min';
SET lock_timeout = '5min';

-- STEP 2: Check BEFORE status
SELECT
    'BEFORE' as status,
    COUNT(*) as total_properties,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' AND land_use_code != '99' THEN 1 END) as with_code,
    COUNT(CASE WHEN land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99' THEN 1 END) as need_update,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' AND land_use_code != '99' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025;

-- STEP 3: Execute the main UPDATE
-- This will assign DOR codes to all properties needing them
-- Expected time: 15-45 minutes depending on database load
UPDATE florida_parcels
SET
    land_use_code = CASE
        -- Multi-Family 10+ (Priority 1)
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN '02'

        -- Industrial (Priority 2)
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN '24'

        -- Commercial (Priority 3)
        WHEN (just_value > 500000
              AND building_value > 200000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN '17'

        -- Agricultural (Priority 4)
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5
              AND land_value > 100000) THEN '01'

        -- Condominium (Priority 5)
        WHEN (just_value BETWEEN 100000 AND 500000
              AND building_value BETWEEN 50000 AND 300000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN '03'

        -- Vacant Residential (Priority 6)
        WHEN (COALESCE(land_value, 0) > 0
              AND (building_value IS NULL OR building_value < 1000)) THEN '10'

        -- Single Family (Priority 7)
        WHEN (building_value > 50000
              AND building_value > COALESCE(land_value, 0)
              AND just_value < 1000000) THEN '00'

        -- Default to Single Family (Priority 8)
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

-- STEP 4: Check AFTER status
SELECT
    'AFTER' as status,
    COUNT(*) as total_properties,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' AND land_use_code != '99' THEN 1 END) as with_code,
    COUNT(CASE WHEN land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99' THEN 1 END) as still_need_update,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' AND land_use_code != '99' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025;

-- STEP 5: Distribution Analysis
SELECT
    land_use_code,
    property_use,
    COUNT(*) as count,
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM florida_parcels WHERE year = 2025) * 100, 2) as percentage
FROM florida_parcels
WHERE year = 2025
    AND land_use_code IS NOT NULL
    AND land_use_code != ''
GROUP BY land_use_code, property_use
ORDER BY count DESC
LIMIT 20;

-- STEP 6: Check for any remaining gaps by county
SELECT
    county,
    COUNT(*) as properties_still_missing_code
FROM florida_parcels
WHERE year = 2025
    AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
GROUP BY county
HAVING COUNT(*) > 0
ORDER BY COUNT(*) DESC;

-- ============================================================================
-- EXECUTION INSTRUCTIONS:
-- ============================================================================
-- 1. Open Supabase SQL Editor: https://app.supabase.com
-- 2. Select your project: pmispwtdngkcmsrsjwbp
-- 3. Copy this ENTIRE file into the SQL Editor
-- 4. Click "Run" (or Ctrl+Enter)
-- 5. Keep the browser tab open for 15-45 minutes
-- 6. Review results from STEP 2 (BEFORE), STEP 4 (AFTER), STEP 5 (Distribution)
--
-- EXPECTED RESULTS:
-- - BEFORE: Coverage ~34.69%
-- - AFTER: Coverage ≥99.5%
-- - Distribution: Majority SFR (00), significant Vacant (10), rest spread
-- - Gaps: Should be 0 or minimal
--
-- If UPDATE times out despite increased timeout:
-- - Contact Supabase support to temporarily increase limits, OR
-- - Use BATCH_UPDATE_BY_COUNTY.sql to process counties one at a time
-- ============================================================================