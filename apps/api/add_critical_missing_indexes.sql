-- ==============================================================================
-- CRITICAL MISSING INDEXES
-- ==============================================================================
-- Purpose: Add indexes recommended by Supabase analysis
-- Based on: Supabase performance advisor + filter system analysis
-- Impact: 5-10x improvement on common queries
-- ==============================================================================

-- County + Year (most common filter)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county_year
ON florida_parcels (county, year)
WHERE year = 2025;

-- Data hash for deduplication
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_data_hash
ON florida_parcels (data_hash)
WHERE data_hash IS NOT NULL;

-- Entity indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_entities_business_name_trgm
ON florida_entities USING gin (business_name gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_entities_last_update
ON florida_entities (last_update_date DESC);

-- Document indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_date_county
ON documents (document_date DESC, county)
WHERE document_date IS NOT NULL;

-- Job status indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nav_jobs_status
ON nav_jobs (status, created_at DESC)
WHERE status != 'completed';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sdf_jobs_status
ON sdf_jobs (status, created_at DESC)
WHERE status != 'completed';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tpp_jobs_status
ON tpp_jobs (status, created_at DESC)
WHERE status != 'completed';

-- Link table composite indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_property_links_both
ON document_property_links (document_id, parcel_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcel_entity_links_both
ON parcel_entity_links (parcel_id, entity_id);

ANALYZE florida_parcels;
ANALYZE florida_entities;
