-- =====================================================
-- STEP 1: TABLE PARTITIONING IMPLEMENTATION
-- Expected Performance Gain: 50x for location-based queries
-- =====================================================

-- Chain of Thought:
-- 1. Create partitioned table structure
-- 2. Create partitions for each Florida county
-- 3. Migrate data safely with verification
-- 4. Swap tables atomically
-- 5. Verify performance improvement

BEGIN;

-- Step 1.1: Create the partitioned table structure
CREATE TABLE IF NOT EXISTS florida_parcels_new (
    LIKE florida_parcels INCLUDING ALL
) PARTITION BY LIST (county);

-- Step 1.2: Create function to automatically create partitions
CREATE OR REPLACE FUNCTION create_county_partition(county_name TEXT)
RETURNS void AS $$
DECLARE
    partition_name TEXT;
BEGIN
    -- Sanitize county name for table name
    partition_name := 'florida_parcels_' || lower(regexp_replace(county_name, '[^a-zA-Z0-9]', '_', 'g'));

    -- Create partition if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_class
        WHERE relname = partition_name
    ) THEN
        EXECUTE format('CREATE TABLE %I PARTITION OF florida_parcels_new FOR VALUES IN (%L)',
            partition_name, county_name);

        -- Create indexes on partition
        EXECUTE format('CREATE INDEX %I ON %I (parcel_id)',
            partition_name || '_parcel_idx', partition_name);
        EXECUTE format('CREATE INDEX %I ON %I (year)',
            partition_name || '_year_idx', partition_name);
        EXECUTE format('CREATE INDEX %I ON %I (sale_date) WHERE sale_date IS NOT NULL',
            partition_name || '_sale_idx', partition_name);

        RAISE NOTICE 'Created partition for county: %', county_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Step 1.3: Get all counties and create partitions
DO $$
DECLARE
    county_record RECORD;
    total_counties INTEGER := 0;
BEGIN
    FOR county_record IN
        SELECT DISTINCT county
        FROM florida_parcels
        WHERE county IS NOT NULL
        ORDER BY county
    LOOP
        PERFORM create_county_partition(county_record.county);
        total_counties := total_counties + 1;
    END LOOP;

    RAISE NOTICE 'Created % county partitions', total_counties;
END $$;

-- Step 1.4: Create partition for NULL counties (if any)
CREATE TABLE IF NOT EXISTS florida_parcels_unknown
PARTITION OF florida_parcels_new FOR VALUES IN (NULL);

COMMIT;

-- =====================================================
-- STEP 2: DATA MIGRATION (Run separately to monitor progress)
-- =====================================================

-- Chain of Thought:
-- - Migrate in batches to avoid locking
-- - Verify row counts match
-- - Use CONCURRENTLY where possible

-- Step 2.1: Create migration function with progress tracking
CREATE OR REPLACE FUNCTION migrate_to_partitioned_table()
RETURNS TABLE(status TEXT, rows_migrated BIGINT, total_rows BIGINT) AS $$
DECLARE
    batch_size INTEGER := 50000;
    offset_val INTEGER := 0;
    total_count BIGINT;
    migrated_count BIGINT := 0;
    batch_count INTEGER;
BEGIN
    -- Get total row count
    SELECT COUNT(*) INTO total_count FROM florida_parcels;

    -- Migrate in batches
    LOOP
        -- Insert batch
        EXECUTE format('
            INSERT INTO florida_parcels_new
            SELECT * FROM florida_parcels
            ORDER BY id
            LIMIT %s OFFSET %s
            ON CONFLICT DO NOTHING',
            batch_size, offset_val);

        GET DIAGNOSTICS batch_count = ROW_COUNT;

        migrated_count := migrated_count + batch_count;
        offset_val := offset_val + batch_size;

        -- Progress update
        IF migrated_count % 100000 = 0 THEN
            RETURN QUERY SELECT
                'IN_PROGRESS'::TEXT,
                migrated_count,
                total_count;
        END IF;

        -- Exit when done
        EXIT WHEN batch_count = 0;
    END LOOP;

    RETURN QUERY SELECT
        'COMPLETED'::TEXT,
        migrated_count,
        total_count;
END;
$$ LANGUAGE plpgsql;

-- Step 2.2: Run migration (monitor progress)
-- SELECT * FROM migrate_to_partitioned_table();

-- =====================================================
-- STEP 3: VERIFICATION AND SWAP
-- =====================================================

-- Step 3.1: Verify data integrity
CREATE OR REPLACE FUNCTION verify_partition_migration()
RETURNS TABLE(check_name TEXT, result TEXT, details TEXT) AS $$
BEGIN
    -- Check row counts
    RETURN QUERY
    SELECT
        'Row Count Match'::TEXT,
        CASE
            WHEN (SELECT COUNT(*) FROM florida_parcels) =
                 (SELECT COUNT(*) FROM florida_parcels_new)
            THEN 'PASSED'::TEXT
            ELSE 'FAILED'::TEXT
        END,
        format('Original: %s, New: %s',
            (SELECT COUNT(*) FROM florida_parcels),
            (SELECT COUNT(*) FROM florida_parcels_new))::TEXT;

    -- Check data sampling
    RETURN QUERY
    SELECT
        'Data Integrity Sample'::TEXT,
        CASE
            WHEN EXISTS (
                SELECT 1 FROM florida_parcels o
                JOIN florida_parcels_new n ON o.id = n.id
                WHERE o.parcel_id != n.parcel_id
                LIMIT 1
            )
            THEN 'FAILED'::TEXT
            ELSE 'PASSED'::TEXT
        END,
        'Sample comparison of records'::TEXT;

    -- Check partition distribution
    RETURN QUERY
    SELECT
        'Partition Distribution'::TEXT,
        'INFO'::TEXT,
        (
            SELECT string_agg(
                format('%s: %s rows', county, cnt), ', '
            )
            FROM (
                SELECT county, COUNT(*) as cnt
                FROM florida_parcels_new
                GROUP BY county
                ORDER BY cnt DESC
                LIMIT 5
            ) t
        )::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Step 3.2: Atomic table swap
-- DO $$
-- BEGIN
--     -- Only proceed if verification passed
--     IF EXISTS (
--         SELECT 1 FROM verify_partition_migration()
--         WHERE check_name = 'Row Count Match' AND result = 'PASSED'
--     ) THEN
--         -- Rename tables atomically
--         ALTER TABLE florida_parcels RENAME TO florida_parcels_old;
--         ALTER TABLE florida_parcels_new RENAME TO florida_parcels;
--
--         -- Update any dependent views
--         -- Note: May need to recreate views that depend on florida_parcels
--
--         RAISE NOTICE 'Table swap completed successfully';
--     ELSE
--         RAISE EXCEPTION 'Migration verification failed';
--     END IF;
-- END $$;

-- =====================================================
-- STEP 4: PERFORMANCE TEST QUERIES
-- =====================================================

-- Test query performance improvement
-- Before partitioning (on florida_parcels_old):
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT COUNT(*) FROM florida_parcels_old
-- WHERE county = 'BROWARD' AND year = 2024;

-- After partitioning (on florida_parcels):
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT COUNT(*) FROM florida_parcels
-- WHERE county = 'BROWARD' AND year = 2024;

-- Expected: Partition pruning should show only scanning relevant partition
-- Performance gain: 50-100x for filtered queries