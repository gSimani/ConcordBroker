-- ==============================================================================
-- MERGE STAGING TO PRODUCTION
-- ==============================================================================
-- Purpose: Safely merge staging data into production tables with upsert logic
-- ==============================================================================

-- ==============================================================================
-- MERGE FLORIDA PARCELS
-- ==============================================================================

CREATE OR REPLACE FUNCTION merge_parcels_staging_to_production(
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
        FROM florida_parcels_staging
        WHERE processed = FALSE
          AND (p_batch_id IS NULL OR batch_id = p_batch_id)
    ),
    upsert_result AS (
        INSERT INTO florida_parcels
        SELECT
            id, parcel_id, county, year, owner_name, phy_addr1, phy_addr2,
            city, state, zip_code, just_value, assessed_value, land_value,
            building_value, building_sqft, land_sqft, year_built,
            property_use_code, sub_usage_code, land_use_code, property_use,
            sale_date, sale_price, qualified_sale, tax_exempt,
            md5(parcel_id || county || year::text)::uuid as data_hash,
            NOW() as updated_at,
            NOW() as created_at
        FROM staging_data
        ON CONFLICT (parcel_id, county, year)
        DO UPDATE SET
            owner_name = EXCLUDED.owner_name,
            phy_addr1 = EXCLUDED.phy_addr1,
            just_value = EXCLUDED.just_value,
            assessed_value = EXCLUDED.assessed_value,
            land_value = EXCLUDED.land_value,
            building_value = EXCLUDED.building_value,
            building_sqft = EXCLUDED.building_sqft,
            land_sqft = EXCLUDED.land_sqft,
            year_built = EXCLUDED.year_built,
            property_use_code = EXCLUDED.property_use_code,
            land_use_code = EXCLUDED.land_use_code,
            property_use = EXCLUDED.property_use,
            sale_date = EXCLUDED.sale_date,
            sale_price = EXCLUDED.sale_price,
            updated_at = NOW()
        WHERE
            florida_parcels.owner_name IS DISTINCT FROM EXCLUDED.owner_name
            OR florida_parcels.just_value IS DISTINCT FROM EXCLUDED.just_value
            OR florida_parcels.building_sqft IS DISTINCT FROM EXCLUDED.building_sqft
        RETURNING
            CASE WHEN florida_parcels.created_at = NOW() THEN 1 ELSE 0 END as is_insert
    )
    SELECT
        COUNT(*) FILTER (WHERE is_insert = 1),
        COUNT(*) FILTER (WHERE is_insert = 0)
    INTO v_inserted, v_updated
    FROM upsert_result;

    -- Mark staging records as processed
    UPDATE florida_parcels_staging
    SET processed = TRUE
    WHERE processed = FALSE
      AND (p_batch_id IS NULL OR batch_id = p_batch_id);

    inserted_count := v_inserted;
    updated_count := v_updated;
    skipped_count := v_skipped;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- USAGE
-- ==============================================================================

-- Merge all unprocessed
SELECT * FROM merge_parcels_staging_to_production();

-- Merge specific batch
-- SELECT * FROM merge_parcels_staging_to_production('BATCH_20251001_083000_abc123');
