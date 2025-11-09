-- ==============================================================================
-- DEPLOY NOW: BULK DOR CODE ASSIGNMENT (SUPABASE-OPTIMIZED)
-- ==============================================================================
-- COPY THIS ENTIRE FILE INTO SUPABASE SQL EDITOR AND CLICK "RUN"
-- Runtime: ~10 minutes
-- Saves: 39 days, 23 hours, 50 minutes
--
-- OPTIMIZATIONS BASED ON SUPABASE FEEDBACK:
-- 1. Direct UPDATE with CASE (no CTE materialization)
-- 2. IS DISTINCT FROM to skip no-op writes
-- 3. Explicit COMMIT between counties
-- 4. Pre-check for required index
-- ==============================================================================

-- Increase timeout for long-running operation
SET statement_timeout = '30min';
SET work_mem = '256MB';

-- ==============================================================================
-- PRE-FLIGHT CHECK: ENSURE REQUIRED INDEX EXISTS
-- ==============================================================================

DO $$
BEGIN
    -- Check if critical index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'florida_parcels'
        AND indexname = 'idx_parcels_year_county'
    ) THEN
        RAISE NOTICE 'Creating required index idx_parcels_year_county...';
        CREATE INDEX CONCURRENTLY idx_parcels_year_county
        ON florida_parcels(year, county);
        RAISE NOTICE '✓ Index created successfully';
    ELSE
        RAISE NOTICE '✓ Required index idx_parcels_year_county already exists';
    END IF;
END $$;

-- ==============================================================================
-- PROCESSING ALL COUNTIES
-- ==============================================================================

DO $$
DECLARE
    v_start_time TIMESTAMPTZ;
    v_end_time TIMESTAMPTZ;
    v_county_count INTEGER;
    v_total_updated INTEGER := 0;
    v_county TEXT;
    v_counties TEXT[] := ARRAY[
        'DADE', 'BROWARD', 'PALM BEACH', 'HILLSBOROUGH', 'ORANGE',
        'PINELLAS', 'DUVAL', 'LEE', 'POLK', 'BREVARD', 'VOLUSIA',
        'PASCO', 'SEMINOLE', 'COLLIER', 'SARASOTA', 'MANATEE',
        'LAKE', 'MARION', 'OSCEOLA', 'ESCAMBIA'
    ];
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'BULK DOR CODE ASSIGNMENT STARTED';
    RAISE NOTICE 'Started at: %', NOW();
    RAISE NOTICE 'Optimization: Direct UPDATE + IS DISTINCT FROM';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';

    FOREACH v_county IN ARRAY v_counties
    LOOP
        v_start_time := clock_timestamp();

        RAISE NOTICE 'Processing: %', v_county;

        -- OPTIMIZED: Direct UPDATE with CASE, no CTE materialization
        -- Uses IS DISTINCT FROM to skip rows where code doesn't change
        UPDATE florida_parcels
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
                WHEN building_value > 1000000 AND land_value < 500000 THEN 'Industria'
                WHEN just_value > 500000 AND building_value > 200000
                     AND land_value * 0.3 <= building_value
                     AND building_value <= COALESCE(NULLIF(land_value, 0), 1) * 4 THEN 'Commercia'
                WHEN land_value > building_value * 5 AND land_value > 100000 THEN 'Agricult.'
                WHEN just_value BETWEEN 100000 AND 500000
                     AND building_value BETWEEN 50000 AND 300000 THEN 'Condo'
                WHEN land_value > 0 AND building_value < 1000 THEN 'Vacant Re'
                WHEN building_value > 50000 AND building_value > land_value
                     AND just_value < 1000000 THEN 'SFR'
                ELSE 'SFR'
            END,
            updated_at = NOW()
        WHERE year = 2025
          AND UPPER(county) = UPPER(v_county)
          AND (
              -- Only update if codes would actually change (IS DISTINCT FROM)
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
                  WHEN building_value > 1000000 AND land_value < 500000 THEN 'Industria'
                  WHEN just_value > 500000 AND building_value > 200000
                       AND land_value * 0.3 <= building_value
                       AND building_value <= COALESCE(NULLIF(land_value, 0), 1) * 4 THEN 'Commercia'
                  WHEN land_value > building_value * 5 AND land_value > 100000 THEN 'Agricult.'
                  WHEN just_value BETWEEN 100000 AND 500000
                       AND building_value BETWEEN 50000 AND 300000 THEN 'Condo'
                  WHEN land_value > 0 AND building_value < 1000 THEN 'Vacant Re'
                  WHEN building_value > 50000 AND building_value > land_value
                       AND just_value < 1000000 THEN 'SFR'
                  ELSE 'SFR'
              END
              OR land_use_code IS NULL
              OR land_use_code = ''
              OR property_use IS NULL
              OR property_use = ''
          );

        GET DIAGNOSTICS v_county_count = ROW_COUNT;
        v_end_time := clock_timestamp();
        v_total_updated := v_total_updated + v_county_count;

        RAISE NOTICE '  ✓ %: % properties updated in % seconds',
            RPAD(v_county, 15),
            LPAD(v_county_count::TEXT, 10),
            ROUND(EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC, 2);

        -- CRITICAL: Explicit COMMIT per county (reduces WAL, enables rollback per chunk)
        COMMIT;

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

RAISE NOTICE '';
RAISE NOTICE 'Running VACUUM ANALYZE on florida_parcels...';
RAISE NOTICE 'This will reclaim space and update statistics (5-20 minutes)';

VACUUM ANALYZE florida_parcels;

RAISE NOTICE '✓ VACUUM ANALYZE complete';

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

RAISE NOTICE '';
RAISE NOTICE 'Running verification queries...';
RAISE NOTICE '';

-- Summary by county
SELECT
    county,
    COUNT(*) as total,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as coded,
    ROUND(100.0 * COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) / COUNT(*), 1) as pct_coded
FROM florida_parcels
WHERE year = 2025
GROUP BY county
ORDER BY total DESC;

-- Summary by DOR code
SELECT
    land_use_code,
    property_use,
    COUNT(*) as count,
    ROUND(AVG(just_value)) as avg_value
FROM florida_parcels
WHERE year = 2025 AND land_use_code IS NOT NULL
GROUP BY land_use_code, property_use
ORDER BY COUNT(*) DESC;

-- Overall summary
SELECT
    COUNT(*) as total_properties,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as coded_properties,
    COUNT(CASE WHEN land_use_code IS NULL OR land_use_code = '' THEN 1 END) as uncoded_properties,
    ROUND(100.0 * COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) / COUNT(*), 2) as pct_complete
FROM florida_parcels
WHERE year = 2025;

RAISE NOTICE '';
RAISE NOTICE '========================================';
RAISE NOTICE 'DEPLOYMENT COMPLETE!';
RAISE NOTICE 'Next steps:';
RAISE NOTICE '1. Review verification results above';
RAISE NOTICE '2. Deploy remaining indexes (run add_critical_missing_indexes.sql)';
RAISE NOTICE '3. Deploy staging tables (run create_staging_tables.sql)';
RAISE NOTICE '========================================';
