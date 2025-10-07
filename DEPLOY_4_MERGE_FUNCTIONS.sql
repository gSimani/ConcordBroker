-- ==============================================================================
-- DEPLOY 4: MERGE FUNCTIONS (SUPABASE-OPTIMIZED)
-- ==============================================================================
-- Purpose: Safe upsert from staging to production with conflict resolution
-- Strategy: Per-county batches (100K-500K rows), ON CONFLICT with change detection
-- Runtime: ~30 seconds to deploy functions
-- Impact: Fast, safe merges with detailed reporting
--
-- Based on Supabase feedback:
-- - Use ON CONFLICT on natural/unique keys
-- - Process per-county or logical batches
-- - Change detection with IS DISTINCT FROM
-- ==============================================================================

DO $$ BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MERGE FUNCTIONS DEPLOYMENT STARTED';
    RAISE NOTICE 'Started at: %', NOW();
    RAISE NOTICE '========================================';
END $$;

-- ==============================================================================
-- MERGE FUNCTION: Florida Parcels
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE 'Creating merge_parcels_staging_to_production...'; END $$;

CREATE OR REPLACE FUNCTION merge_parcels_staging_to_production(
    p_batch_id TEXT DEFAULT NULL,
    p_county TEXT DEFAULT NULL
)
RETURNS TABLE (
    inserted_count BIGINT,
    updated_count BIGINT,
    skipped_count BIGINT,
    error_count BIGINT
) AS $$
DECLARE
    v_inserted BIGINT := 0;
    v_updated BIGINT := 0;
    v_skipped BIGINT := 0;
    v_error BIGINT := 0;
BEGIN
    -- Insert/Update from staging to production
    WITH staging_data AS (
        SELECT *
        FROM staging.florida_parcels_staging
        WHERE processed = FALSE
          AND (p_batch_id IS NULL OR batch_id = p_batch_id)
          AND (p_county IS NULL OR UPPER(county) = UPPER(p_county))
    ),
    upsert_result AS (
        INSERT INTO florida_parcels (
            parcel_id, county, year, owner_name, phy_addr1, phy_addr2,
            city, state, zip_code, just_value, assessed_value, land_value,
            building_value, building_sqft, land_sqft, year_built,
            property_use_code, sub_usage_code, land_use_code, property_use,
            sale_date, sale_price, qualified_sale, tax_exempt,
            updated_at, created_at
        )
        SELECT
            parcel_id, county, year, owner_name, phy_addr1, phy_addr2,
            city, state, zip_code, just_value, assessed_value, land_value,
            building_value, building_sqft, land_sqft, year_built,
            property_use_code, sub_usage_code, land_use_code, property_use,
            sale_date, sale_price, qualified_sale, tax_exempt,
            NOW() as updated_at,
            NOW() as created_at
        FROM staging_data
        ON CONFLICT (parcel_id, county, year)
        DO UPDATE SET
            owner_name = EXCLUDED.owner_name,
            phy_addr1 = EXCLUDED.phy_addr1,
            phy_addr2 = EXCLUDED.phy_addr2,
            city = EXCLUDED.city,
            state = EXCLUDED.state,
            zip_code = EXCLUDED.zip_code,
            just_value = EXCLUDED.just_value,
            assessed_value = EXCLUDED.assessed_value,
            land_value = EXCLUDED.land_value,
            building_value = EXCLUDED.building_value,
            building_sqft = EXCLUDED.building_sqft,
            land_sqft = EXCLUDED.land_sqft,
            year_built = EXCLUDED.year_built,
            property_use_code = EXCLUDED.property_use_code,
            sub_usage_code = EXCLUDED.sub_usage_code,
            land_use_code = EXCLUDED.land_use_code,
            property_use = EXCLUDED.property_use,
            sale_date = EXCLUDED.sale_date,
            sale_price = EXCLUDED.sale_price,
            qualified_sale = EXCLUDED.qualified_sale,
            tax_exempt = EXCLUDED.tax_exempt,
            updated_at = NOW()
        WHERE
            -- Only update if values actually changed
            florida_parcels.owner_name IS DISTINCT FROM EXCLUDED.owner_name
            OR florida_parcels.phy_addr1 IS DISTINCT FROM EXCLUDED.phy_addr1
            OR florida_parcels.just_value IS DISTINCT FROM EXCLUDED.just_value
            OR florida_parcels.building_sqft IS DISTINCT FROM EXCLUDED.building_sqft
            OR florida_parcels.land_value IS DISTINCT FROM EXCLUDED.land_value
            OR florida_parcels.sale_date IS DISTINCT FROM EXCLUDED.sale_date
        RETURNING
            (CASE WHEN xmax = 0 THEN 1 ELSE 0 END) as is_insert
    )
    SELECT
        COUNT(*) FILTER (WHERE is_insert = 1),
        COUNT(*) FILTER (WHERE is_insert = 0)
    INTO v_inserted, v_updated
    FROM upsert_result;

    -- Mark staging records as processed
    UPDATE staging.florida_parcels_staging
    SET processed = TRUE
    WHERE processed = FALSE
      AND (p_batch_id IS NULL OR batch_id = p_batch_id)
      AND (p_county IS NULL OR UPPER(county) = UPPER(p_county));

    -- Return stats
    inserted_count := v_inserted;
    updated_count := v_updated;
    skipped_count := v_skipped;
    error_count := v_error;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN RAISE NOTICE '  ✓ merge_parcels_staging_to_production created'; END $$;

-- ==============================================================================
-- MERGE FUNCTION: Florida Entities
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE 'Creating merge_entities_staging_to_production...'; END $$;

CREATE OR REPLACE FUNCTION merge_entities_staging_to_production(
    p_batch_id TEXT DEFAULT NULL
)
RETURNS TABLE (
    inserted_count BIGINT,
    updated_count BIGINT,
    skipped_count BIGINT
) AS $$
DECLARE
    v_inserted BIGINT := 0;
    v_updated BIGINT := 0;
    v_skipped BIGINT := 0;
BEGIN
    WITH staging_data AS (
        SELECT *
        FROM staging.florida_entities_staging
        WHERE processed = FALSE
          AND (p_batch_id IS NULL OR batch_id = p_batch_id)
    ),
    upsert_result AS (
        INSERT INTO florida_entities (
            fei_number, business_name, filing_date, status,
            principal_address, mailing_address, last_update_date,
            updated_at, created_at
        )
        SELECT
            fei_number, business_name, filing_date, status,
            principal_address, mailing_address, last_update_date,
            NOW(), NOW()
        FROM staging_data
        ON CONFLICT (fei_number, filing_date)
        DO UPDATE SET
            business_name = EXCLUDED.business_name,
            status = EXCLUDED.status,
            principal_address = EXCLUDED.principal_address,
            mailing_address = EXCLUDED.mailing_address,
            last_update_date = EXCLUDED.last_update_date,
            updated_at = NOW()
        WHERE
            florida_entities.business_name IS DISTINCT FROM EXCLUDED.business_name
            OR florida_entities.status IS DISTINCT FROM EXCLUDED.status
            OR florida_entities.last_update_date IS DISTINCT FROM EXCLUDED.last_update_date
        RETURNING (CASE WHEN xmax = 0 THEN 1 ELSE 0 END) as is_insert
    )
    SELECT
        COUNT(*) FILTER (WHERE is_insert = 1),
        COUNT(*) FILTER (WHERE is_insert = 0)
    INTO v_inserted, v_updated
    FROM upsert_result;

    UPDATE staging.florida_entities_staging
    SET processed = TRUE
    WHERE processed = FALSE
      AND (p_batch_id IS NULL OR batch_id = p_batch_id);

    inserted_count := v_inserted;
    updated_count := v_updated;
    skipped_count := v_skipped;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN RAISE NOTICE '  ✓ merge_entities_staging_to_production created'; END $$;

-- ==============================================================================
-- MERGE FUNCTION: Sunbiz Corporate
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE 'Creating merge_sunbiz_staging_to_production...'; END $$;

CREATE OR REPLACE FUNCTION merge_sunbiz_staging_to_production(
    p_batch_id TEXT DEFAULT NULL
)
RETURNS TABLE (
    inserted_count BIGINT,
    updated_count BIGINT
) AS $$
DECLARE
    v_inserted BIGINT := 0;
    v_updated BIGINT := 0;
BEGIN
    WITH staging_data AS (
        SELECT *
        FROM staging.sunbiz_corporate_staging
        WHERE processed = FALSE
          AND (p_batch_id IS NULL OR batch_id = p_batch_id)
    ),
    upsert_result AS (
        INSERT INTO sunbiz_corporate (
            document_number, name, status, filing_date,
            principal_address, mailing_address,
            updated_at, created_at
        )
        SELECT
            document_number, name, status, filing_date,
            principal_address, mailing_address,
            NOW(), NOW()
        FROM staging_data
        ON CONFLICT (document_number)
        DO UPDATE SET
            name = EXCLUDED.name,
            status = EXCLUDED.status,
            filing_date = EXCLUDED.filing_date,
            principal_address = EXCLUDED.principal_address,
            mailing_address = EXCLUDED.mailing_address,
            updated_at = NOW()
        WHERE
            sunbiz_corporate.name IS DISTINCT FROM EXCLUDED.name
            OR sunbiz_corporate.status IS DISTINCT FROM EXCLUDED.status
        RETURNING (CASE WHEN xmax = 0 THEN 1 ELSE 0 END) as is_insert
    )
    SELECT
        COUNT(*) FILTER (WHERE is_insert = 1),
        COUNT(*) FILTER (WHERE is_insert = 0)
    INTO v_inserted, v_updated
    FROM upsert_result;

    UPDATE staging.sunbiz_corporate_staging
    SET processed = TRUE
    WHERE processed = FALSE
      AND (p_batch_id IS NULL OR batch_id = p_batch_id);

    inserted_count := v_inserted;
    updated_count := v_updated;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN RAISE NOTICE '  ✓ merge_sunbiz_staging_to_production created'; END $$;

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

DO $$ BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MERGE FUNCTIONS DEPLOYMENT COMPLETE!';
    RAISE NOTICE 'Completed at: %', NOW();
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Testing functions...';
END $$;

-- Test merge functions with empty staging (should return 0/0/0)
SELECT
    'Test: merge_parcels_staging_to_production' as test_name,
    * FROM merge_parcels_staging_to_production();

SELECT
    'Test: merge_entities_staging_to_production' as test_name,
    * FROM merge_entities_staging_to_production();

SELECT
    'Test: merge_sunbiz_staging_to_production' as test_name,
    * FROM merge_sunbiz_staging_to_production();

DO $$ BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'USAGE EXAMPLES:';
    RAISE NOTICE '';
    RAISE NOTICE '-- Merge all unprocessed batches:';
    RAISE NOTICE 'SELECT * FROM merge_parcels_staging_to_production();';
    RAISE NOTICE '';
    RAISE NOTICE '-- Merge specific batch:';
    RAISE NOTICE 'SELECT * FROM merge_parcels_staging_to_production(''BATCH_20251001_120000_abc123'');';
    RAISE NOTICE '';
    RAISE NOTICE '-- Merge specific county from batch:';
    RAISE NOTICE 'SELECT * FROM merge_parcels_staging_to_production(''BATCH_20251001_120000_abc123'', ''DADE'');';
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'NEXT STEPS:';
    RAISE NOTICE '1. Update Python scripts to bulk insert to staging';
    RAISE NOTICE '2. Call merge functions after each bulk load';
    RAISE NOTICE '3. Monitor staging.get_staging_stats() for health';
    RAISE NOTICE '========================================';
END $$;
