-- ============================================================================
-- TEMP TABLE APPROACH - MOST RELIABLE, NO TIMEOUTS
-- Step 1: Create temp table (run once)
-- Step 2: Run batch UPDATE (run 20-22 times)
-- ============================================================================

-- STEP 1: Create temp table with all DADE rows needing updates (RUN ONCE)
CREATE TEMP TABLE dade_targets (
    id bigint PRIMARY KEY
) ON COMMIT PRESERVE ROWS;

INSERT INTO dade_targets (id)
SELECT id
FROM florida_parcels
WHERE year = 2025
    AND county = 'DADE'
    AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
ORDER BY id;

-- Check how many rows we'll process
SELECT COUNT(*) as rows_to_process FROM dade_targets;

-- ============================================================================
-- STEP 2: Run this batch UPDATE 20-22 times (50k per batch)
-- ============================================================================

WITH batch AS (
    SELECT id
    FROM dade_targets
    ORDER BY id
    LIMIT 50000
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
WHERE fp.id IN (SELECT id FROM batch);

-- Remove processed rows from temp table
DELETE FROM dade_targets WHERE id IN (
    SELECT id FROM dade_targets ORDER BY id LIMIT 50000
);

-- Check progress
SELECT COUNT(*) as remaining FROM dade_targets;
SELECT COUNT(*) as total, COUNT(CASE WHEN land_use_code IS NOT NULL THEN 1 END) as with_code, ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage FROM florida_parcels WHERE year = 2025 AND county = 'DADE';

-- ============================================================================
-- BENEFITS:
-- - No ORDER BY during UPDATE (fast)
-- - Exact 50k rows per batch (no empty batches)
-- - Auto-tracking (DELETE removes processed rows)
-- - When dade_targets is empty, DADE is 100% complete
-- ============================================================================