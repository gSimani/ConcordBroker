-- ==============================================================================
-- DEPLOY 3: STAGING TABLES (SUPABASE-OPTIMIZED)
-- ==============================================================================
-- Purpose: Create staging infrastructure for bulk imports
-- Strategy: Separate schema, minimal indexes, batch tracking
-- Runtime: ~30 seconds
-- Impact: 50x faster bulk imports (50K+ rows/sec vs 1K rows/sec)
--
-- Based on Supabase feedback:
-- - Use separate staging schema for isolation
-- - No RLS, no triggers, minimal indexes
-- - Bulk insert → merge to production pattern
-- ==============================================================================

DO $$ BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'STAGING TABLES DEPLOYMENT STARTED';
    RAISE NOTICE 'Started at: %', NOW();
    RAISE NOTICE '========================================';
END $$;

-- ==============================================================================
-- CREATE STAGING SCHEMA
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS staging;

DO $$ BEGIN RAISE NOTICE '✓ Staging schema created'; END $$;

-- ==============================================================================
-- STAGING TABLE: florida_parcels_staging
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE 'Creating florida_parcels_staging...'; END $$;

CREATE TABLE IF NOT EXISTS staging.florida_parcels_staging (
    LIKE florida_parcels INCLUDING DEFAULTS
);

-- Add batch tracking columns
ALTER TABLE staging.florida_parcels_staging
ADD COLUMN IF NOT EXISTS batch_id TEXT,
ADD COLUMN IF NOT EXISTS loaded_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Minimal index: Only natural key for deduplication
CREATE INDEX IF NOT EXISTS idx_staging_parcels_natural_key
ON staging.florida_parcels_staging (parcel_id, county, year);

-- Batch tracking index
CREATE INDEX IF NOT EXISTS idx_staging_parcels_batch
ON staging.florida_parcels_staging (batch_id, processed);

DO $$ BEGIN RAISE NOTICE '  ✓ florida_parcels_staging created'; END $$;

-- ==============================================================================
-- STAGING TABLE: florida_entities_staging
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE 'Creating florida_entities_staging...'; END $$;

CREATE TABLE IF NOT EXISTS staging.florida_entities_staging (
    LIKE florida_entities INCLUDING DEFAULTS
);

ALTER TABLE staging.florida_entities_staging
ADD COLUMN IF NOT EXISTS batch_id TEXT,
ADD COLUMN IF NOT EXISTS loaded_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS error_message TEXT;

CREATE INDEX IF NOT EXISTS idx_staging_entities_natural_key
ON staging.florida_entities_staging (fei_number, filing_date);

CREATE INDEX IF NOT EXISTS idx_staging_entities_batch
ON staging.florida_entities_staging (batch_id, processed);

DO $$ BEGIN RAISE NOTICE '  ✓ florida_entities_staging created'; END $$;

-- ==============================================================================
-- STAGING TABLE: sunbiz_corporate_staging
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE 'Creating sunbiz_corporate_staging...'; END $$;

CREATE TABLE IF NOT EXISTS staging.sunbiz_corporate_staging (
    LIKE sunbiz_corporate INCLUDING DEFAULTS
);

ALTER TABLE staging.sunbiz_corporate_staging
ADD COLUMN IF NOT EXISTS batch_id TEXT,
ADD COLUMN IF NOT EXISTS loaded_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS error_message TEXT;

CREATE INDEX IF NOT EXISTS idx_staging_sunbiz_natural_key
ON staging.sunbiz_corporate_staging (document_number);

CREATE INDEX IF NOT EXISTS idx_staging_sunbiz_batch
ON staging.sunbiz_corporate_staging (batch_id, processed);

DO $$ BEGIN RAISE NOTICE '  ✓ sunbiz_corporate_staging created'; END $$;

-- ==============================================================================
-- HELPER FUNCTIONS
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE 'Creating helper functions...'; END $$;

-- Generate batch ID
CREATE OR REPLACE FUNCTION staging.generate_batch_id()
RETURNS TEXT AS $$
BEGIN
    RETURN 'BATCH_' || TO_CHAR(NOW(), 'YYYYMMDD_HH24MISS') || '_' ||
           SUBSTRING(MD5(RANDOM()::TEXT), 1, 8);
END;
$$ LANGUAGE plpgsql;

-- Get staging stats
CREATE OR REPLACE FUNCTION staging.get_staging_stats()
RETURNS TABLE (
    table_name TEXT,
    total_rows BIGINT,
    unprocessed_rows BIGINT,
    processed_rows BIGINT,
    error_rows BIGINT,
    oldest_batch TEXT,
    newest_batch TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'florida_parcels_staging'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(*) FILTER (WHERE NOT processed)::BIGINT,
        COUNT(*) FILTER (WHERE processed)::BIGINT,
        COUNT(*) FILTER (WHERE error_message IS NOT NULL)::BIGINT,
        MIN(batch_id),
        MAX(batch_id)
    FROM staging.florida_parcels_staging
    UNION ALL
    SELECT
        'florida_entities_staging'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(*) FILTER (WHERE NOT processed)::BIGINT,
        COUNT(*) FILTER (WHERE processed)::BIGINT,
        COUNT(*) FILTER (WHERE error_message IS NOT NULL)::BIGINT,
        MIN(batch_id),
        MAX(batch_id)
    FROM staging.florida_entities_staging
    UNION ALL
    SELECT
        'sunbiz_corporate_staging'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(*) FILTER (WHERE NOT processed)::BIGINT,
        COUNT(*) FILTER (WHERE processed)::BIGINT,
        COUNT(*) FILTER (WHERE error_message IS NOT NULL)::BIGINT,
        MIN(batch_id),
        MAX(batch_id)
    FROM staging.sunbiz_corporate_staging;
END;
$$ LANGUAGE plpgsql;

-- Clean processed batches older than N days
CREATE OR REPLACE FUNCTION staging.cleanup_old_batches(days_old INTEGER DEFAULT 7)
RETURNS TABLE (
    table_name TEXT,
    deleted_count BIGINT
) AS $$
DECLARE
    v_parcels_deleted BIGINT;
    v_entities_deleted BIGINT;
    v_sunbiz_deleted BIGINT;
BEGIN
    DELETE FROM staging.florida_parcels_staging
    WHERE processed = TRUE AND loaded_at < NOW() - (days_old || ' days')::INTERVAL;
    GET DIAGNOSTICS v_parcels_deleted = ROW_COUNT;

    DELETE FROM staging.florida_entities_staging
    WHERE processed = TRUE AND loaded_at < NOW() - (days_old || ' days')::INTERVAL;
    GET DIAGNOSTICS v_entities_deleted = ROW_COUNT;

    DELETE FROM staging.sunbiz_corporate_staging
    WHERE processed = TRUE AND loaded_at < NOW() - (days_old || ' days')::INTERVAL;
    GET DIAGNOSTICS v_sunbiz_deleted = ROW_COUNT;

    RETURN QUERY
    SELECT 'florida_parcels_staging'::TEXT, v_parcels_deleted
    UNION ALL
    SELECT 'florida_entities_staging'::TEXT, v_entities_deleted
    UNION ALL
    SELECT 'sunbiz_corporate_staging'::TEXT, v_sunbiz_deleted;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN RAISE NOTICE '  ✓ Helper functions created'; END $$;

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

DO $$ BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'STAGING TABLES DEPLOYMENT COMPLETE!';
    RAISE NOTICE 'Completed at: %', NOW();
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Running verification...';
END $$;

-- Show staging tables
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'staging'
ORDER BY tablename;

-- Test batch ID generation
SELECT
    staging.generate_batch_id() as sample_batch_id,
    'Format: BATCH_YYYYMMDD_HHMMSS_xxxxxxxx' as format_description;

-- Show initial stats
SELECT * FROM staging.get_staging_stats();

DO $$ BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'USAGE EXAMPLE:';
    RAISE NOTICE '';
    RAISE NOTICE '-- Python: Bulk insert to staging';
    RAISE NOTICE 'batch_id = supabase.rpc("staging.generate_batch_id").execute()';
    RAISE NOTICE 'df.to_sql("florida_parcels_staging", engine, schema="staging")';
    RAISE NOTICE '';
    RAISE NOTICE '-- SQL: Merge to production';
    RAISE NOTICE 'SELECT * FROM merge_parcels_staging_to_production(batch_id);';
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'NEXT STEPS:';
    RAISE NOTICE '1. Deploy merge functions (run merge_staging_to_production.sql)';
    RAISE NOTICE '2. Update Python scripts to use staging pattern';
    RAISE NOTICE '3. Test with small batch before full deployment';
    RAISE NOTICE '========================================';
END $$;
