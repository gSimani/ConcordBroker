-- Create server-side function to backfill property_use_desc in batches
-- This avoids web timeout limits by running inside PostgreSQL

CREATE OR REPLACE FUNCTION backfill_property_use_desc_batch(
  p_county TEXT DEFAULT NULL,
  p_batch_size INT DEFAULT 10000
)
RETURNS TABLE (
  batch_number INT,
  rows_updated BIGINT,
  total_processed BIGINT,
  duration_seconds NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_batch_num INT := 0;
  v_rows_updated BIGINT;
  v_total_processed BIGINT := 0;
  v_start_time TIMESTAMP;
  v_batch_start TIMESTAMP;
  v_last_ctid TID := '(0,0)'::tid;
BEGIN
  v_start_time := clock_timestamp();

  LOOP
    v_batch_start := clock_timestamp();
    v_batch_num := v_batch_num + 1;

    -- Update batch with ctid pagination
    WITH batch_to_update AS (
      SELECT ctid, id, property_use, county
      FROM florida_parcels
      WHERE ctid > v_last_ctid
        AND property_use IS NOT NULL
        AND (property_use_desc IS NULL OR property_use_desc = '')
        AND (p_county IS NULL OR county = p_county)
      ORDER BY ctid
      LIMIT p_batch_size
    ),
    updated AS (
      UPDATE florida_parcels fp
      SET property_use_desc = COALESCE(
        -- Try exact mapping via dor_code_mappings_std
        (SELECT duc.description
         FROM dor_code_mappings_std dcm
         JOIN dor_use_codes_std duc ON dcm.standard_full_code = duc.full_code
         WHERE dcm.legacy_code = fp.property_use::text
         AND (dcm.county IS NULL OR dcm.county = fp.county)
         LIMIT 1),
        -- Fallback to category-based description
        CASE
          WHEN fp.property_use::int BETWEEN 0 AND 9 THEN 'Residential Property'
          WHEN fp.property_use::int BETWEEN 10 AND 39 THEN 'Commercial Property'
          WHEN fp.property_use::int BETWEEN 40 AND 49 THEN 'Industrial Property'
          WHEN fp.property_use::int BETWEEN 50 AND 69 THEN 'Agricultural Property'
          WHEN fp.property_use::int BETWEEN 70 AND 79 THEN 'Institutional Property'
          WHEN fp.property_use::int BETWEEN 80 AND 89 THEN 'Government Property'
          WHEN fp.property_use::int BETWEEN 90 AND 99 THEN 'Vacant Land'
          ELSE 'Unknown Property Type'
        END
      )
      FROM batch_to_update
      WHERE fp.ctid = batch_to_update.ctid
      RETURNING fp.ctid
    )
    SELECT COUNT(*), MAX(ctid)
    INTO v_rows_updated, v_last_ctid
    FROM updated;

    -- Exit if no more rows to update
    EXIT WHEN v_rows_updated = 0;

    v_total_processed := v_total_processed + v_rows_updated;

    -- Return batch statistics
    batch_number := v_batch_num;
    rows_updated := v_rows_updated;
    total_processed := v_total_processed;
    duration_seconds := EXTRACT(EPOCH FROM (clock_timestamp() - v_start_time));

    RETURN NEXT;

    -- Small delay to avoid overwhelming the database
    PERFORM pg_sleep(0.1);
  END LOOP;

  RETURN;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION backfill_property_use_desc_batch(TEXT, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION backfill_property_use_desc_batch(TEXT, INT) TO service_role;

COMMENT ON FUNCTION backfill_property_use_desc_batch IS
'Backfills property_use_desc column in batches to avoid timeouts.
Usage: SELECT * FROM backfill_property_use_desc_batch(''BROWARD'', 10000);';
