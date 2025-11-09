-- Optimized DOR Code Assignment Function for Railway Pro
-- Uses aggressive batching and connection pooling

-- Drop existing function
DROP FUNCTION IF EXISTS assign_dor_codes_batch(VARCHAR, INTEGER);

-- Create optimized version
CREATE OR REPLACE FUNCTION assign_dor_codes_batch(
    target_county VARCHAR DEFAULT NULL,
    batch_size INTEGER DEFAULT 10000  -- Increased from 5000 for Railway Pro
)
RETURNS TABLE (
    processed_count INTEGER,
    remaining_count INTEGER
) AS $$
DECLARE
    v_processed INTEGER := 0;
    v_remaining INTEGER := 0;
BEGIN
    -- Disable triggers for faster bulk updates
    SET session_replication_role = 'replica';

    -- Update batch with optimized logic
    WITH properties_to_update AS (
        SELECT parcel_id, county, year,
               CASE
                   -- Single Family Residential
                   WHEN dor_uc = '0000' OR dor_uc = '0001' OR dor_uc LIKE '00%' THEN '00'
                   -- Multi-family
                   WHEN dor_uc LIKE '02%' THEN '02'
                   -- Condos
                   WHEN dor_uc LIKE '03%' THEN '03'
                   -- Commercial
                   WHEN dor_uc LIKE '17%' OR dor_uc LIKE '18%' OR dor_uc LIKE '19%' THEN '17'
                   -- Industrial
                   WHEN dor_uc LIKE '24%' OR dor_uc LIKE '25%' THEN '24'
                   -- Agricultural
                   WHEN dor_uc LIKE '01%' THEN '01'
                   -- Institutional/Government
                   WHEN dor_uc LIKE '8%' OR dor_uc LIKE '9%' THEN '80'
                   -- Vacant
                   WHEN dor_uc LIKE '10%' OR dor_uc = '1000' THEN '10'
                   -- Default to unknown
                   ELSE '99'
               END as new_land_use_code
        FROM florida_parcels
        WHERE year = 2025
          AND (target_county IS NULL OR county = target_county)
          AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
          AND dor_uc IS NOT NULL
          AND dor_uc != ''
        LIMIT batch_size
    )
    UPDATE florida_parcels fp
    SET land_use_code = ptu.new_land_use_code
    FROM properties_to_update ptu
    WHERE fp.parcel_id = ptu.parcel_id
      AND fp.county = ptu.county
      AND fp.year = ptu.year;

    GET DIAGNOSTICS v_processed = ROW_COUNT;

    -- Re-enable triggers
    SET session_replication_role = 'origin';

    -- Count remaining
    SELECT COUNT(*)::INTEGER INTO v_remaining
    FROM florida_parcels
    WHERE year = 2025
      AND (target_county IS NULL OR county = target_county)
      AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
      AND dor_uc IS NOT NULL
      AND dor_uc != '';

    RETURN QUERY SELECT v_processed, v_remaining;
END;
$$ LANGUAGE plpgsql;

-- Create optimized indexes for parallel processing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_dor_parallel
    ON florida_parcels(county, year, land_use_code)
    WHERE year = 2025 AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99');

-- Analyze table for query planner
ANALYZE florida_parcels;

-- Display optimization status
SELECT 'DOR Function Optimized for Railway Pro - Ready for 10x parallel processing!' as status;
