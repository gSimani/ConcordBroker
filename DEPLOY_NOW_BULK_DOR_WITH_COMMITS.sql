-- ==============================================================================
-- DEPLOY NOW: BULK DOR CODE ASSIGNMENT (WITH PER-COUNTY COMMITS)
-- ==============================================================================
-- VERSION: Per-county commits for better WAL management
-- This version splits into 20 separate statements for explicit commit control
-- Use this if you want partial success on failure (recommended by Supabase)
-- ==============================================================================

SET statement_timeout = '30min';
SET work_mem = '256MB';

-- ==============================================================================
-- PRE-FLIGHT: ENSURE REQUIRED INDEX EXISTS
-- ==============================================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_year_county
  ON public.florida_parcels(year, county);

SELECT '✓ Index ready' AS status;

-- ==============================================================================
-- PROCESSING: DADE COUNTY
-- ==============================================================================

DO $$
DECLARE
  v_start_time TIMESTAMPTZ := clock_timestamp();
  v_count INTEGER;
BEGIN
  UPDATE public.florida_parcels
  SET
    land_use_code = CASE
      WHEN building_value > 500000 AND building_value > land_value * 2 THEN '02'
      WHEN building_value > 1000000 AND land_value < 500000 THEN '24'
      WHEN just_value > 500000 AND building_value > 200000
           AND land_value * 0.3 <= building_value
           AND building_value <= COALESCE(NULLIF(land_value, 0), 1) * 4 THEN '17'
      WHEN land_value > building_value * 5 AND land_value > 100000 THEN '01'
      WHEN just_value BETWEEN 100000 AND 500000
           AND building_value BETWEEN 50000 AND 300000 THEN '03'
      WHEN land_value > 0 AND building_value < 1000 THEN '10'
      WHEN building_value > 50000 AND building_value > land_value
           AND just_value < 1000000 THEN '00'
      ELSE '00'
    END,
    property_use = CASE
      WHEN building_value > 500000 AND building_value > land_value * 2 THEN 'MF 10+'
      WHEN building_value > 1000000 AND land_value < 500000 THEN 'Industrial'
      WHEN just_value > 500000 AND building_value > 200000
           AND land_value * 0.3 <= building_value
           AND building_value <= COALESCE(NULLIF(land_value, 0), 1) * 4 THEN 'Commercial'
      WHEN land_value > building_value * 5 AND land_value > 100000 THEN 'Agriculture'
      WHEN just_value BETWEEN 100000 AND 500000
           AND building_value BETWEEN 50000 AND 300000 THEN 'Condo'
      WHEN land_value > 0 AND building_value < 1000 THEN 'Vacant Res'
      WHEN building_value > 50000 AND building_value > land_value
           AND just_value < 1000000 THEN 'SFR'
      ELSE 'SFR'
    END,
    updated_at = NOW()
  WHERE year = 2025 AND UPPER(county) = 'DADE'
    AND (land_use_code IS NULL OR land_use_code = ''
         OR property_use IS NULL OR property_use = '');

  GET DIAGNOSTICS v_count = ROW_COUNT;
  RAISE NOTICE '✓ DADE: % updated in %s',
    v_count,
    ROUND(EXTRACT(EPOCH FROM (clock_timestamp() - v_start_time))::NUMERIC, 2);
END $$;
-- Implicit COMMIT here

-- ==============================================================================
-- PROCESSING: BROWARD COUNTY
-- ==============================================================================

DO $$
DECLARE v_start_time TIMESTAMPTZ := clock_timestamp(); v_count INTEGER;
BEGIN
  UPDATE public.florida_parcels
  SET land_use_code = CASE
      WHEN building_value > 500000 AND building_value > land_value * 2 THEN '02'
      WHEN building_value > 1000000 AND land_value < 500000 THEN '24'
      WHEN just_value > 500000 AND building_value > 200000
           AND land_value * 0.3 <= building_value
           AND building_value <= COALESCE(NULLIF(land_value, 0), 1) * 4 THEN '17'
      WHEN land_value > building_value * 5 AND land_value > 100000 THEN '01'
      WHEN just_value BETWEEN 100000 AND 500000
           AND building_value BETWEEN 50000 AND 300000 THEN '03'
      WHEN land_value > 0 AND building_value < 1000 THEN '10'
      WHEN building_value > 50000 AND building_value > land_value
           AND just_value < 1000000 THEN '00'
      ELSE '00'
    END,
    property_use = CASE
      WHEN building_value > 500000 AND building_value > land_value * 2 THEN 'MF 10+'
      WHEN building_value > 1000000 AND land_value < 500000 THEN 'Industrial'
      WHEN just_value > 500000 AND building_value > 200000
           AND land_value * 0.3 <= building_value
           AND building_value <= COALESCE(NULLIF(land_value, 0), 1) * 4 THEN 'Commercial'
      WHEN land_value > building_value * 5 AND land_value > 100000 THEN 'Agriculture'
      WHEN just_value BETWEEN 100000 AND 500000
           AND building_value BETWEEN 50000 AND 300000 THEN 'Condo'
      WHEN land_value > 0 AND building_value < 1000 THEN 'Vacant Res'
      WHEN building_value > 50000 AND building_value > land_value
           AND just_value < 1000000 THEN 'SFR'
      ELSE 'SFR'
    END,
    updated_at = NOW()
  WHERE year = 2025 AND UPPER(county) = 'BROWARD'
    AND (land_use_code IS NULL OR land_use_code = ''
         OR property_use IS NULL OR property_use = '');

  GET DIAGNOSTICS v_count = ROW_COUNT;
  RAISE NOTICE '✓ BROWARD: % updated in %s', v_count,
    ROUND(EXTRACT(EPOCH FROM (clock_timestamp() - v_start_time))::NUMERIC, 2);
END $$;

-- [Continue for all 20 counties...]

-- ==============================================================================
-- NOTE: This file would be VERY long with all 20 counties
-- For production, I recommend using DEPLOY_NOW_BULK_DOR_FIXED.sql instead
-- which processes all counties in a single transaction.
--
-- Per-county commits provide:
-- - Partial success on failure
-- - Better WAL management
-- - Progress visibility
--
-- But require:
-- - 20x longer SQL file
-- - More complex to maintain
-- ==============================================================================

SELECT '⚠ This is a template showing per-county pattern' AS note,
       'Use DEPLOY_NOW_BULK_DOR_FIXED.sql for actual deployment' AS recommendation;

-- Continue with remaining 18 counties following same pattern...
-- PALM BEACH, HILLSBOROUGH, ORANGE, PINELLAS, DUVAL, LEE, POLK,
-- BREVARD, VOLUSIA, PASCO, SEMINOLE, COLLIER, SARASOTA, MANATEE,
-- LAKE, MARION, OSCEOLA, ESCAMBIA

-- ==============================================================================
-- POST-UPDATE: VACUUM ANALYZE
-- ==============================================================================

VACUUM ANALYZE public.florida_parcels;

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

SELECT COUNT(*) AS total,
       COUNT(*) FILTER (WHERE land_use_code IS NOT NULL) AS coded,
       ROUND(100.0 * COUNT(*) FILTER (WHERE land_use_code IS NOT NULL) / COUNT(*), 2) AS pct
FROM public.florida_parcels WHERE year = 2025;
