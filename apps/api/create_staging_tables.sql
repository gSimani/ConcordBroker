-- ==============================================================================
-- STAGING TABLES FOR EFFICIENT BULK LOADING
-- ==============================================================================
-- Purpose: Create staging tables for safe, fast bulk data imports
-- Benefits:
--   - No RLS overhead during import
--   - No constraint checking during load
--   - Minimal indexes for speed
--   - Rollback capability
--   - No production table locking
-- ==============================================================================
-- Author: Claude Code - Database Optimization
-- Created: 2025-10-01
-- ==============================================================================

-- ==============================================================================
-- DROP EXISTING STAGING TABLES (if they exist)
-- ==============================================================================

DROP TABLE IF EXISTS florida_parcels_staging CASCADE;
DROP TABLE IF EXISTS florida_entities_staging CASCADE;
DROP TABLE IF EXISTS property_sales_staging CASCADE;
DROP TABLE IF EXISTS sunbiz_corporate_staging CASCADE;
DROP TABLE IF EXISTS documents_staging CASCADE;

-- ==============================================================================
-- FLORIDA_PARCELS_STAGING
-- ==============================================================================

CREATE TABLE florida_parcels_staging (
    LIKE florida_parcels INCLUDING DEFAULTS
);

-- Add staging metadata
ALTER TABLE florida_parcels_staging
ADD COLUMN IF NOT EXISTS batch_id TEXT,
ADD COLUMN IF NOT EXISTS loaded_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE;

-- Minimal index (only for deduplication during merge)
CREATE INDEX idx_staging_parcels_natural_key
ON florida_parcels_staging (parcel_id, county, year);

CREATE INDEX idx_staging_parcels_batch
ON florida_parcels_staging (batch_id)
WHERE batch_id IS NOT NULL;

COMMENT ON TABLE florida_parcels_staging IS
'Staging table for bulk parcel imports. No RLS, minimal constraints for fast loading.';

-- ==============================================================================
-- FLORIDA_ENTITIES_STAGING
-- ==============================================================================

CREATE TABLE florida_entities_staging (
    LIKE florida_entities INCLUDING DEFAULTS
);

ALTER TABLE florida_entities_staging
ADD COLUMN IF NOT EXISTS batch_id TEXT,
ADD COLUMN IF NOT EXISTS loaded_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE;

-- Minimal indexes
CREATE INDEX idx_staging_entities_id
ON florida_entities_staging (entity_id);

CREATE INDEX idx_staging_entities_batch
ON florida_entities_staging (batch_id)
WHERE batch_id IS NOT NULL;

COMMENT ON TABLE florida_entities_staging IS
'Staging table for bulk entity imports.';

-- ==============================================================================
-- PROPERTY_SALES_STAGING
-- ==============================================================================

CREATE TABLE property_sales_staging (
    LIKE property_sales_history INCLUDING DEFAULTS
);

ALTER TABLE property_sales_staging
ADD COLUMN IF NOT EXISTS batch_id TEXT,
ADD COLUMN IF NOT EXISTS loaded_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE;

CREATE INDEX idx_staging_sales_parcel
ON property_sales_staging (parcel_id);

CREATE INDEX idx_staging_sales_batch
ON property_sales_staging (batch_id)
WHERE batch_id IS NOT NULL;

COMMENT ON TABLE property_sales_staging IS
'Staging table for bulk sales history imports.';

-- ==============================================================================
-- SUNBIZ_CORPORATE_STAGING
-- ==============================================================================

CREATE TABLE sunbiz_corporate_staging (
    LIKE sunbiz_corporate INCLUDING DEFAULTS
);

ALTER TABLE sunbiz_corporate_staging
ADD COLUMN IF NOT EXISTS batch_id TEXT,
ADD COLUMN IF NOT EXISTS loaded_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE;

CREATE INDEX idx_staging_sunbiz_doc
ON sunbiz_corporate_staging (doc_number);

CREATE INDEX idx_staging_sunbiz_batch
ON sunbiz_corporate_staging (batch_id)
WHERE batch_id IS NOT NULL;

COMMENT ON TABLE sunbiz_corporate_staging IS
'Staging table for bulk Sunbiz corporate entity imports.';

-- ==============================================================================
-- DOCUMENTS_STAGING
-- ==============================================================================

CREATE TABLE documents_staging (
    LIKE documents INCLUDING DEFAULTS
);

ALTER TABLE documents_staging
ADD COLUMN IF NOT EXISTS batch_id TEXT,
ADD COLUMN IF NOT EXISTS loaded_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE;

CREATE INDEX idx_staging_docs_batch
ON documents_staging (batch_id)
WHERE batch_id IS NOT EXISTS;

COMMENT ON TABLE documents_staging IS
'Staging table for bulk document imports.';

-- ==============================================================================
-- HELPER FUNCTIONS
-- ==============================================================================

-- Function to generate batch ID
CREATE OR REPLACE FUNCTION generate_batch_id()
RETURNS TEXT AS $$
BEGIN
    RETURN 'BATCH_' || TO_CHAR(NOW(), 'YYYYMMDD_HH24MISS') || '_' || SUBSTRING(MD5(RANDOM()::TEXT), 1, 8);
END;
$$ LANGUAGE plpgsql;

-- Function to clear processed staging records
CREATE OR REPLACE FUNCTION clear_processed_staging()
RETURNS TABLE (
    table_name TEXT,
    rows_deleted BIGINT
) AS $$
BEGIN
    -- Clear parcels
    DELETE FROM florida_parcels_staging WHERE processed = TRUE;
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    table_name := 'florida_parcels_staging';
    RETURN NEXT;

    -- Clear entities
    DELETE FROM florida_entities_staging WHERE processed = TRUE;
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    table_name := 'florida_entities_staging';
    RETURN NEXT;

    -- Clear sales
    DELETE FROM property_sales_staging WHERE processed = TRUE;
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    table_name := 'property_sales_staging';
    RETURN NEXT;

    -- Clear sunbiz
    DELETE FROM sunbiz_corporate_staging WHERE processed = TRUE;
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    table_name := 'sunbiz_corporate_staging';
    RETURN NEXT;

    -- Clear documents
    DELETE FROM documents_staging WHERE processed = TRUE;
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    table_name := 'documents_staging';
    RETURN NEXT;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Function to get staging table statistics
CREATE OR REPLACE FUNCTION get_staging_stats()
RETURNS TABLE (
    table_name TEXT,
    total_rows BIGINT,
    unprocessed_rows BIGINT,
    oldest_batch TIMESTAMPTZ,
    newest_batch TIMESTAMPTZ
) AS $$
BEGIN
    -- Parcels staging
    SELECT
        'florida_parcels_staging',
        COUNT(*),
        COUNT(*) FILTER (WHERE processed = FALSE),
        MIN(loaded_at),
        MAX(loaded_at)
    INTO table_name, total_rows, unprocessed_rows, oldest_batch, newest_batch
    FROM florida_parcels_staging;
    RETURN NEXT;

    -- Entities staging
    SELECT
        'florida_entities_staging',
        COUNT(*),
        COUNT(*) FILTER (WHERE processed = FALSE),
        MIN(loaded_at),
        MAX(loaded_at)
    INTO table_name, total_rows, unprocessed_rows, oldest_batch, newest_batch
    FROM florida_entities_staging;
    RETURN NEXT;

    -- Sales staging
    SELECT
        'property_sales_staging',
        COUNT(*),
        COUNT(*) FILTER (WHERE processed = FALSE),
        MIN(loaded_at),
        MAX(loaded_at)
    INTO table_name, total_rows, unprocessed_rows, oldest_batch, newest_batch
    FROM property_sales_staging;
    RETURN NEXT;

    -- Sunbiz staging
    SELECT
        'sunbiz_corporate_staging',
        COUNT(*),
        COUNT(*) FILTER (WHERE processed = FALSE),
        MIN(loaded_at),
        MAX(loaded_at)
    INTO table_name, total_rows, unprocessed_rows, oldest_batch, newest_batch
    FROM sunbiz_corporate_staging;
    RETURN NEXT;

    -- Documents staging
    SELECT
        'documents_staging',
        COUNT(*),
        COUNT(*) FILTER (WHERE processed = FALSE),
        MIN(loaded_at),
        MAX(loaded_at)
    INTO table_name, total_rows, unprocessed_rows, oldest_batch, newest_batch
    FROM documents_staging;
    RETURN NEXT;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- USAGE EXAMPLES
-- ==============================================================================

/*
-- 1. Load data to staging (from Python):
```python
import pandas as pd
from sqlalchemy import create_engine

# Generate batch ID
batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

# Load DataFrame to staging
df['batch_id'] = batch_id
df.to_sql('florida_parcels_staging', engine, if_exists='append', index=False, method='multi', chunksize=10000)
```

-- 2. Check staging status
SELECT * FROM get_staging_stats();

-- 3. Merge to production (see merge_staging_to_production.sql)

-- 4. Clear processed records
SELECT * FROM clear_processed_staging();

-- 5. Manual truncate (if needed)
TRUNCATE florida_parcels_staging;
TRUNCATE florida_entities_staging;
TRUNCATE property_sales_staging;
TRUNCATE sunbiz_corporate_staging;
TRUNCATE documents_staging;
*/

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

-- List all staging tables
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
FROM pg_tables
WHERE tablename LIKE '%_staging'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

RAISE NOTICE 'Staging tables created successfully!';
RAISE NOTICE 'Use get_staging_stats() to monitor staging data.';
RAISE NOTICE 'Use clear_processed_staging() to clean up after merges.';
