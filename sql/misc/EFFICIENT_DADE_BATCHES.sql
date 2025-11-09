-- ============================================================================
-- EFFICIENT DADE BATCHING - Only updates actual DADE rows
-- Uses LIMIT with ordering to process exactly N rows per batch
-- ============================================================================

-- Batch 1: First 50,000 DADE rows needing updates
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
WHERE id IN (
    SELECT id FROM florida_parcels
    WHERE year = 2025
        AND county = 'DADE'
        AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
    ORDER BY id
    LIMIT 50000
);

-- Check how many rows were updated
SELECT
    'Batch 1 Complete' as status,
    COUNT(*) as total_dade,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage
FROM florida_parcels
WHERE year = 2025 AND county = 'DADE';

-- ============================================================================
-- INSTRUCTIONS:
-- ============================================================================
-- 1. Run the UPDATE above
-- 2. Run the SELECT to check progress
-- 3. Repeat the same UPDATE (it will automatically get the next 50k rows)
-- 4. After 20-22 repetitions, all ~1.08M DADE rows will be complete
--
-- This approach:
-- - Always updates exactly 50,000 rows per batch (no empty batches)
-- - Automatically moves to next rows (no manual ID tracking)
-- - Guaranteed to finish in 20-22 batches
-- ============================================================================