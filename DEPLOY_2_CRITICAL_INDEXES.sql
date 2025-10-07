-- ==============================================================================
-- DEPLOY 2: CRITICAL MISSING INDEXES (SUPABASE-OPTIMIZED)
-- ==============================================================================
-- Purpose: Add indexes recommended by Supabase analysis
-- Strategy: Sequential execution (per Supabase guidance)
-- Runtime: 15-25 minutes total
-- Impact: 5-10x improvement on common queries
--
-- IMPORTANT: Run this AFTER DEPLOY_NOW_BULK_DOR_OPTIMIZED.sql completes
-- ==============================================================================

SET maintenance_work_mem = '512MB';

-- ==============================================================================
-- PRE-FLIGHT CHECK
-- ==============================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'CRITICAL INDEX DEPLOYMENT STARTED';
    RAISE NOTICE 'Started at: %', NOW();
    RAISE NOTICE 'Strategy: Sequential CONCURRENTLY (no downtime)';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
END $$;

-- ==============================================================================
-- SECTION 1: FLORIDA PARCELS INDEXES
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE '[1/10] Creating idx_florida_parcels_county_year...'; END $$;

-- NOTE: This may already exist from bulk DOR deployment
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county_year
ON florida_parcels (county, year)
WHERE year = 2025;

DO $$ BEGIN RAISE NOTICE '  ✓ idx_florida_parcels_county_year complete'; END $$;

-- ==============================================================================

DO $$ BEGIN RAISE NOTICE '[2/10] Creating idx_florida_parcels_data_hash...'; END $$;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_data_hash
ON florida_parcels (data_hash)
WHERE data_hash IS NOT NULL;

DO $$ BEGIN RAISE NOTICE '  ✓ idx_florida_parcels_data_hash complete'; END $$;

-- ==============================================================================
-- SECTION 2: FLORIDA ENTITIES INDEXES
-- ==============================================================================

DO $$ BEGIN
    RAISE NOTICE '[3/10] Creating idx_florida_entities_business_name_trgm...';
    RAISE NOTICE '  (This is a GIN trigram index on 15M rows - may take 15-30 minutes)';
END $$;

-- Ensure pg_trgm extension exists
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_entities_business_name_trgm
ON florida_entities USING gin (business_name gin_trgm_ops);

DO $$ BEGIN RAISE NOTICE '  ✓ idx_florida_entities_business_name_trgm complete'; END $$;

-- ==============================================================================

DO $$ BEGIN RAISE NOTICE '[4/10] Creating idx_florida_entities_last_update...'; END $$;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_entities_last_update
ON florida_entities (last_update_date DESC);

DO $$ BEGIN RAISE NOTICE '  ✓ idx_florida_entities_last_update complete'; END $$;

-- ==============================================================================
-- SECTION 3: DOCUMENT INDEXES
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE '[5/10] Creating idx_documents_date_county...'; END $$;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_date_county
ON documents (document_date DESC, county)
WHERE document_date IS NOT NULL;

DO $$ BEGIN RAISE NOTICE '  ✓ idx_documents_date_county complete'; END $$;

-- ==============================================================================
-- SECTION 4: JOB STATUS INDEXES (Fast - partial indexes)
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE '[6/10] Creating idx_nav_jobs_status...'; END $$;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nav_jobs_status
ON nav_jobs (status, created_at DESC)
WHERE status != 'completed';

DO $$ BEGIN RAISE NOTICE '  ✓ idx_nav_jobs_status complete'; END $$;

-- ==============================================================================

DO $$ BEGIN RAISE NOTICE '[7/10] Creating idx_sdf_jobs_status...'; END $$;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sdf_jobs_status
ON sdf_jobs (status, created_at DESC)
WHERE status != 'completed';

DO $$ BEGIN RAISE NOTICE '  ✓ idx_sdf_jobs_status complete'; END $$;

-- ==============================================================================

DO $$ BEGIN RAISE NOTICE '[8/10] Creating idx_tpp_jobs_status...'; END $$;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tpp_jobs_status
ON tpp_jobs (status, created_at DESC)
WHERE status != 'completed';

DO $$ BEGIN RAISE NOTICE '  ✓ idx_tpp_jobs_status complete'; END $$;

-- ==============================================================================
-- SECTION 5: LINK TABLE INDEXES (Fast - small tables)
-- ==============================================================================

DO $$ BEGIN RAISE NOTICE '[9/10] Creating idx_document_property_links_both...'; END $$;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_property_links_both
ON document_property_links (document_id, parcel_id);

DO $$ BEGIN RAISE NOTICE '  ✓ idx_document_property_links_both complete'; END $$;

-- ==============================================================================

DO $$ BEGIN RAISE NOTICE '[10/10] Creating idx_parcel_entity_links_both...'; END $$;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcel_entity_links_both
ON parcel_entity_links (parcel_id, entity_id);

DO $$ BEGIN RAISE NOTICE '  ✓ idx_parcel_entity_links_both complete'; END $$;

-- ==============================================================================
-- POST-INDEX: ANALYZE TABLES
-- ==============================================================================

DO $$ BEGIN
    RAISE NOTICE '';
    RAISE NOTICE 'Running ANALYZE on indexed tables...';
END $$;

ANALYZE florida_parcels;
ANALYZE florida_entities;
ANALYZE documents;
ANALYZE nav_jobs;
ANALYZE sdf_jobs;
ANALYZE tpp_jobs;
ANALYZE document_property_links;
ANALYZE parcel_entity_links;

DO $$ BEGIN RAISE NOTICE '  ✓ ANALYZE complete'; END $$;

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

DO $$ BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'INDEX DEPLOYMENT COMPLETE!';
    RAISE NOTICE 'Completed at: %', NOW();
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Verification query running...';
END $$;

-- Show all indexes created
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan as times_used,
    idx_tup_read as tuples_read
FROM pg_stat_user_indexes
WHERE indexname IN (
    'idx_florida_parcels_county_year',
    'idx_florida_parcels_data_hash',
    'idx_florida_entities_business_name_trgm',
    'idx_florida_entities_last_update',
    'idx_documents_date_county',
    'idx_nav_jobs_status',
    'idx_sdf_jobs_status',
    'idx_tpp_jobs_status',
    'idx_document_property_links_both',
    'idx_parcel_entity_links_both'
)
ORDER BY tablename, indexname;

-- Summary by table
SELECT
    tablename,
    COUNT(*) as index_count,
    pg_size_pretty(SUM(pg_relation_size(indexrelid))) as total_index_size
FROM pg_stat_user_indexes
WHERE tablename IN ('florida_parcels', 'florida_entities', 'documents',
                    'nav_jobs', 'sdf_jobs', 'tpp_jobs',
                    'document_property_links', 'parcel_entity_links')
GROUP BY tablename
ORDER BY tablename;

DO $$ BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'NEXT STEPS:';
    RAISE NOTICE '1. Review index sizes above';
    RAISE NOTICE '2. Deploy staging tables (run create_staging_tables.sql)';
    RAISE NOTICE '3. Deploy materialized view (run create_filter_optimized_view.sql)';
    RAISE NOTICE '========================================';
END $$;
