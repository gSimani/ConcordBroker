-- ============================================================================
-- ID-RANGED BATCHED DOR ASSIGNMENT - NO TIMEOUT GUARANTEED
-- Process in 100k ID chunks per county
-- ============================================================================

-- STEP 1: Get ID ranges for DADE county
SELECT
    min(id) AS min_id,
    max(id) AS max_id,
    COUNT(*) AS total,
    CEIL(COUNT(*)::numeric / 100000) AS num_batches
FROM florida_parcels
WHERE year = 2025 AND county = 'DADE'
  AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99');

-- STEP 2: Based on the min_id and max_id from above, run batches
-- Replace XXXXX and YYYYY with actual values from STEP 1
-- Example: if min_id = 1000000 and max_id = 2000000, do:
--   Batch 1: 1000000 to 1100000
--   Batch 2: 1100001 to 1200000
--   etc.

-- DADE Batch 1 (adjust range based on your data)
UPDATE florida_parcels
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
WHERE year = 2025
    AND county = 'DADE'
    AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
    AND id >= 1000000 AND id < 1100000;  -- ADJUST THESE VALUES

-- Check progress after each batch
SELECT
    COUNT(*) AS total,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) AS with_code,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) AS coverage
FROM florida_parcels
WHERE year = 2025 AND county = 'DADE';

-- ============================================================================
-- AUTOMATION OPTION: Let me generate all batches for you
-- ============================================================================
-- Reply with the min_id and max_id from STEP 1 and I'll generate
-- all the individual UPDATE statements for DADE
-- ============================================================================