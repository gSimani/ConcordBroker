-- ============================================================================
-- FINAL OPTIMIZED TEMP TABLE APPROACH - PRODUCTION READY
-- Incorporates: transactions, proper labels, indexes, safety checks
-- ============================================================================

-- STEP 1: Setup (run once per session)
-- ============================================================================

-- Create temp table
CREATE TEMP TABLE dade_targets (id bigint PRIMARY KEY) ON COMMIT PRESERVE ROWS;

-- Populate with DADE rows needing updates
INSERT INTO dade_targets (id)
SELECT id FROM florida_parcels
WHERE year = 2025
    AND county = 'DADE'
    AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
ORDER BY id;

-- Verify setup
SELECT COUNT(*) as rows_to_process FROM dade_targets;
-- Expected: ~1,084,021 rows (from your earlier count)

-- ============================================================================
-- STEP 2: Batch Update (run this 20-22 times until remaining = 0)
-- ============================================================================

BEGIN;

WITH batch AS (
    SELECT id FROM dade_targets ORDER BY id LIMIT 50000
)
UPDATE florida_parcels fp
SET
    land_use_code = CASE
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN '02'
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN '24'
        WHEN (just_value > 500000 AND building_value > 200000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN '17'
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN '01'
        WHEN (just_value BETWEEN 100000 AND 500000
              AND building_value BETWEEN 50000 AND 300000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN '03'
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN '10'
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN '00'
        ELSE '00'
    END,
    property_use = CASE
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN 'MF 10+'
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN 'Industrial'
        WHEN (just_value > 500000 AND building_value > 200000) THEN 'Commercial'
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN 'Agricultur'
        WHEN (just_value BETWEEN 100000 AND 500000 AND building_value BETWEEN 50000 AND 300000) THEN 'Condo'
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN 'Vacant Res'
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN 'SFR'
        ELSE 'SFR'
    END
WHERE fp.id IN (SELECT id FROM batch);

-- Remove processed rows (only if UPDATE succeeded)
DELETE FROM dade_targets
WHERE id IN (SELECT id FROM dade_targets ORDER BY id LIMIT 50000);

COMMIT;

-- Check remaining work
SELECT COUNT(*) AS remaining FROM dade_targets;

-- Check DADE coverage progress
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025 AND county = 'DADE';

-- ============================================================================
-- NOTES ON LABELS (property_use varchar(10) constraint):
-- ============================================================================
-- These labels are optimized to maximize clarity within the 10-character limit:
-- - 'Industrial' (10 chars) ✓ Full word, fits perfectly
-- - 'Commercial' (10 chars) ✓ Full word, fits perfectly
-- - 'Agricultur' (10 chars) ✓ Agricultural truncated (12 chars too long)
-- - 'Vacant Res' (10 chars) ✓ Vacant Residential truncated
-- - 'MF 10+'     (6 chars)  ✓ Multi-Family 10+ units
-- - 'Condo'      (5 chars)  ✓ Condominium
-- - 'SFR'        (3 chars)  ✓ Single Family Residential
--
-- All labels fit within the varchar(10) constraint.
-- ============================================================================

-- ============================================================================
-- EXECUTION PLAN:
-- ============================================================================
-- 1. Run STEP 1 once to create and populate dade_targets
-- 2. Run STEP 2 repeatedly (20-22 times) until "remaining = 0"
-- 3. Each batch:
--    - Updates 50,000 properties
--    - Takes 10-30 seconds
--    - Wrapped in transaction for safety
--    - Auto-removes processed IDs
--
-- EXPECTED TIMELINE:
-- - 1,084,021 rows / 50,000 per batch = ~22 batches
-- - ~22 × 20 seconds = ~7-10 minutes total
--
-- WHEN COMPLETE:
-- - remaining = 0
-- - DADE coverage ≈ 100%
-- - Move to next county (LEE, ORANGE, etc.)
-- ============================================================================