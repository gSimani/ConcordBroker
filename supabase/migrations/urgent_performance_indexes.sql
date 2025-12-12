-- URGENT PERFORMANCE INDEXES
-- Created: 2025-11-09
-- Purpose: Fix search timeouts on florida_parcels and florida_entities tables
-- Estimated execution time: 10-30 minutes (depends on table size)

-- ============================================================================
-- FLORIDA_PARCELS INDEXES
-- ============================================================================

-- Index for county filtering (most common search)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county
  ON florida_parcels(county);

-- Index for owner name search with trigram similarity
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name_gin
  ON florida_parcels USING gin(owner_name gin_trgm_ops);

-- Index for parcel_id lookups (primary identifier)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id
  ON florida_parcels(parcel_id);

-- Index for property use code filtering
CREATE INDEX IF NOT EXISTS idx_florida_parcels_property_use
  ON florida_parcels(property_use_desc);

-- Composite index for county + property use searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_property_use
  ON florida_parcels(county, property_use_desc);

-- Index for DOR code searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_dor_code
  ON florida_parcels(dor_code);

-- Index for city searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city
  ON florida_parcels(city_state_zip);

-- Index for situs address searches with trigram
CREATE INDEX IF NOT EXISTS idx_florida_parcels_situs_address_gin
  ON florida_parcels USING gin(situs_address gin_trgm_ops);

-- Index for just value range queries (value filtering)
CREATE INDEX IF NOT EXISTS idx_florida_parcels_just_value
  ON florida_parcels(just_value) WHERE just_value > 0;

-- ============================================================================
-- FLORIDA_ENTITIES INDEXES (if table exists)
-- ============================================================================

-- Index for entity name searches
CREATE INDEX IF NOT EXISTS idx_florida_entities_name_gin
  ON florida_entities USING gin(name gin_trgm_ops);

-- Index for entity type filtering
CREATE INDEX IF NOT EXISTS idx_florida_entities_type
  ON florida_entities(entity_type);

-- Index for entity ID lookups
CREATE INDEX IF NOT EXISTS idx_florida_entities_entity_id
  ON florida_entities(entity_id);

-- ============================================================================
-- SUNBIZ_CORPORATE INDEXES (bonus optimization)
-- ============================================================================

-- Index for corporate name searches (2M+ records)
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_name_gin
  ON sunbiz_corporate USING gin(name gin_trgm_ops);

-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_status
  ON sunbiz_corporate(status) WHERE status = 'ACTIVE';

-- ============================================================================
-- PROPERTY_SALES_HISTORY INDEXES (bonus optimization)
-- ============================================================================

-- Index for parcel_id lookups in sales history
CREATE INDEX IF NOT EXISTS idx_property_sales_history_parcel_id
  ON property_sales_history(parcel_id);

-- Index for sale date range queries
CREATE INDEX IF NOT EXISTS idx_property_sales_history_sale_date
  ON property_sales_history(sale_date DESC);

-- Composite index for parcel + date
CREATE INDEX IF NOT EXISTS idx_property_sales_history_parcel_date
  ON property_sales_history(parcel_id, sale_date DESC);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Run this query to verify all indexes were created successfully:
--
-- SELECT
--   schemaname,
--   tablename,
--   indexname,
--   indexdef
-- FROM pg_indexes
-- WHERE tablename IN ('florida_parcels', 'florida_entities', 'sunbiz_corporate', 'property_sales_history')
-- ORDER BY tablename, indexname;
