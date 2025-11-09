-- ==============================================================================
-- DEPLOY NOW: BULK DOR CODE ASSIGNMENT (SUPABASE-FIXED)
-- ==============================================================================
-- FIXED ISSUES:
-- 1. RAISE NOTICE only inside DO blocks
-- 2. CREATE INDEX CONCURRENTLY at top level (not in transaction)
-- 3. Removed COMMIT inside DO block (runs as single transaction)
-- 4. Added proper schema references
-- ==============================================================================

SET statement_timeout = '30min';
SET work_mem = '256MB';

-- ==============================================================================
-- PRE-FLIGHT: ENSURE REQUIRED INDEX EXISTS
-- ==============================================================================

-- Check if index exists and report
WITH idx AS (
  SELECT 1
  FROM pg_indexes
  WHERE schemaname = 'public'
    AND tablename = 'florida_parcels'
    AND indexname = 'idx_parcels_year_county'
)
SELECT
  CASE WHEN EXISTS (SELECT 1 FROM idx)
       THEN '✓ Required index idx_parcels_year_county already exists'
       ELSE '⚠ Creating required index idx_parcels_year_county...'
  END AS status;

-- Create the index at top level (CONCURRENTLY requires non-transaction context)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_year_county
  ON public.florida_parcels(year, county);

SELECT '✓ Index ready - starting bulk update' AS status;

-- ==============================================================================
-- PROCESSING ALL COUNTIES (SINGLE TRANSACTION)
-- ==============================================================================

DO $$
DECLARE
  v_start_time TIMESTAMPTZ;
  v_end_time   TIMESTAMPTZ;
  v_county_count INTEGER;
  v_total_updated INTEGER := 0;
  v_county TEXT;
  v_counties TEXT[] := ARRAY[
    'DADE','BROWARD','PALM BEACH','HILLSBOROUGH','ORANGE',
    'PINELLAS','DUVAL','LEE','POLK','BREVARD','VOLUSIA',
    'PASCO','SEMINOLE','COLLIER','SARASOTA','MANATEE',
    'LAKE','MARION','OSCEOLA','ESCAMBIA'
  ];
BEGIN
  RAISE NOTICE '========================================';
  RAISE NOTICE 'BULK DOR CODE ASSIGNMENT STARTED';
  RAISE NOTICE 'Started at: %', NOW();
  RAISE NOTICE 'Optimization: Direct UPDATE + IS DISTINCT FROM';
  RAISE NOTICE '========================================';
  RAISE NOTICE '';

  FOREACH v_county IN ARRAY v_counties LOOP
    v_start_time := clock_timestamp();
    RAISE NOTICE 'Processing: %', v_county;

    -- Direct UPDATE with IS DISTINCT FROM guard
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
    WHERE year = 2025
      AND UPPER(county) = UPPER(v_county)
      AND (
        -- Only update if values actually change (IS DISTINCT FROM)
        land_use_code IS DISTINCT FROM CASE
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
        END
        OR property_use IS DISTINCT FROM CASE
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
        END
        OR land_use_code IS NULL OR land_use_code = ''
        OR property_use IS NULL  OR property_use = ''
      );

    GET DIAGNOSTICS v_county_count = ROW_COUNT;
    v_end_time := clock_timestamp();
    v_total_updated := v_total_updated + v_county_count;

    RAISE NOTICE '  ✓ %: % properties updated in % seconds',
      RPAD(v_county, 15),
      LPAD(v_county_count::TEXT, 10),
      ROUND(EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC, 2);
  END LOOP;

  RAISE NOTICE '';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'BULK DOR CODE ASSIGNMENT COMPLETE!';
  RAISE NOTICE 'Total properties updated: %', v_total_updated;
  RAISE NOTICE 'Completed at: %', NOW();
  RAISE NOTICE '========================================';
END $$;

-- ==============================================================================
-- POST-UPDATE: VACUUM ANALYZE
-- ==============================================================================

SELECT 'Running VACUUM ANALYZE on florida_parcels...' AS status;

VACUUM ANALYZE public.florida_parcels;

SELECT '✓ VACUUM ANALYZE complete' AS status;

-- ==============================================================================
-- VERIFICATION QUERIES
-- ==============================================================================

SELECT 'Running verification queries...' AS status;

-- Summary by county
SELECT
  county,
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE land_use_code IS NOT NULL AND land_use_code <> '') AS coded,
  ROUND(100.0 *
        COUNT(*) FILTER (WHERE land_use_code IS NOT NULL AND land_use_code <> '')
        / NULLIF(COUNT(*), 0), 1) AS pct_coded
FROM public.florida_parcels
WHERE year = 2025
GROUP BY county
ORDER BY total DESC;

-- Summary by DOR code
SELECT
  land_use_code,
  property_use,
  COUNT(*) AS count,
  ROUND(AVG(just_value)) AS avg_value
FROM public.florida_parcels
WHERE year = 2025 AND land_use_code IS NOT NULL
GROUP BY land_use_code, property_use
ORDER BY COUNT(*) DESC;

-- Overall summary
SELECT
  COUNT(*) AS total_properties,
  COUNT(*) FILTER (WHERE land_use_code IS NOT NULL AND land_use_code <> '') AS coded_properties,
  COUNT(*) FILTER (WHERE land_use_code IS NULL OR land_use_code = '') AS uncoded_properties,
  ROUND(100.0 *
        COUNT(*) FILTER (WHERE land_use_code IS NOT NULL AND land_use_code <> '')
        / NULLIF(COUNT(*), 0), 2) AS pct_complete
FROM public.florida_parcels
WHERE year = 2025;

-- ==============================================================================
-- COMPLETION MESSAGE
-- ==============================================================================

DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'DEPLOYMENT COMPLETE!';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Review verification results above';
  RAISE NOTICE '2. Deploy remaining indexes (DEPLOY_2_CRITICAL_INDEXES.sql)';
  RAISE NOTICE '3. Deploy staging tables (DEPLOY_3_STAGING_TABLES.sql)';
  RAISE NOTICE '========================================';
END $$;
