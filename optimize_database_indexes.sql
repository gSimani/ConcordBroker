-- ConcordBroker Database Optimization Indexes
-- These indexes will significantly improve query performance

-- ============================================
-- FLORIDA PARCELS INDEXES
-- ============================================

-- Critical index for city and value range searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city_value 
ON florida_parcels(phy_city, jv);

-- Index for owner name searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner 
ON florida_parcels(owner_name);

-- Index for address searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_address 
ON florida_parcels(phy_addr1);

-- Composite index for property type and city
CREATE INDEX IF NOT EXISTS idx_florida_parcels_type_city
ON florida_parcels(dor_uc, phy_city);

-- Index for parcel ID lookups
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id
ON florida_parcels(parcel_id);

-- Index for zip code searches
CREATE INDEX IF NOT EXISTS idx_florida_parcels_zip
ON florida_parcels(phy_zipcd);

-- ============================================
-- SUNBIZ CORPORATE INDEXES
-- ============================================

-- Index for entity name searches
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_entity 
ON sunbiz_corporate(entity_name);

-- Index for principal address searches
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_address 
ON sunbiz_corporate(prin_addr1);

-- Partial index for active entities only
CREATE INDEX IF NOT EXISTS idx_sunbiz_active 
ON sunbiz_corporate(entity_name) 
WHERE status = 'ACTIVE';

-- Index for document number lookups
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_doc_num
ON sunbiz_corporate(document_number);

-- Index for filing date range queries
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_filing_date
ON sunbiz_corporate(filing_date);

-- ============================================
-- PROPERTY SALES HISTORY INDEXES
-- ============================================

-- Index for parcel ID joins
CREATE INDEX IF NOT EXISTS idx_sales_history_parcel_id
ON property_sales_history(parcel_id);

-- Index for sale date range queries
CREATE INDEX IF NOT EXISTS idx_sales_history_sale_date
ON property_sales_history(sale_date DESC);

-- Composite index for parcel and date
CREATE INDEX IF NOT EXISTS idx_sales_history_parcel_date
ON property_sales_history(parcel_id, sale_date DESC);

-- Index for sale price searches
CREATE INDEX IF NOT EXISTS idx_sales_history_price
ON property_sales_history(sale_price);

-- ============================================
-- BUILDING PERMITS INDEXES
-- ============================================

-- Index for address searches
CREATE INDEX IF NOT EXISTS idx_building_permits_address
ON building_permits(address);

-- Index for permit date searches
CREATE INDEX IF NOT EXISTS idx_building_permits_date
ON building_permits(permit_date DESC);

-- Index for permit type
CREATE INDEX IF NOT EXISTS idx_building_permits_type
ON building_permits(permit_type);

-- Composite index for address and date
CREATE INDEX IF NOT EXISTS idx_building_permits_address_date
ON building_permits(address, permit_date DESC);

-- ============================================
-- TAX CERTIFICATES INDEXES
-- ============================================

-- Index for parcel ID
CREATE INDEX IF NOT EXISTS idx_tax_certificates_parcel
ON tax_certificates(parcel_id);

-- Index for certificate year
CREATE INDEX IF NOT EXISTS idx_tax_certificates_year
ON tax_certificates(certificate_year DESC);

-- ============================================
-- PROPERTY TRACKED INDEXES (for user tracking)
-- ============================================

-- Index for user ID
CREATE INDEX IF NOT EXISTS idx_property_tracked_user
ON property_tracked(user_id);

-- Index for property ID
CREATE INDEX IF NOT EXISTS idx_property_tracked_property
ON property_tracked(property_id);

-- Composite index for user and property (unique constraint)
CREATE UNIQUE INDEX IF NOT EXISTS idx_property_tracked_user_property
ON property_tracked(user_id, property_id);

-- ============================================
-- MATERIALIZED VIEW FOR PROPERTY SUMMARIES
-- ============================================

-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS property_summary CASCADE;

-- Create materialized view for fast property summaries
CREATE MATERIALIZED VIEW property_summary AS
SELECT 
    p.parcel_id,
    p.phy_addr1,
    p.phy_city,
    p.phy_zipcd,
    p.owner_name,
    p.jv as market_value,
    p.dor_uc as use_code,
    p.acres,
    p.year_built,
    COUNT(DISTINCT s.id) as sale_count,
    MAX(s.sale_date) as last_sale_date,
    MAX(s.sale_price) as last_sale_price,
    COUNT(DISTINCT sc.id) as business_count,
    COUNT(DISTINCT bp.id) as permit_count,
    COUNT(DISTINCT tc.id) as tax_certificate_count
FROM florida_parcels p
LEFT JOIN property_sales_history s ON p.parcel_id = s.parcel_id
LEFT JOIN sunbiz_corporate sc ON p.phy_addr1 = sc.prin_addr1
LEFT JOIN building_permits bp ON p.phy_addr1 = bp.address
LEFT JOIN tax_certificates tc ON p.parcel_id = tc.parcel_id
GROUP BY 
    p.parcel_id, p.phy_addr1, p.phy_city, p.phy_zipcd, 
    p.owner_name, p.jv, p.dor_uc, p.acres, p.year_built;

-- Create indexes on the materialized view
CREATE INDEX idx_property_summary_city ON property_summary(phy_city);
CREATE INDEX idx_property_summary_value ON property_summary(market_value);
CREATE INDEX idx_property_summary_owner ON property_summary(owner_name);
CREATE INDEX idx_property_summary_parcel ON property_summary(parcel_id);

-- Create function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_property_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY property_summary;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- PERFORMANCE MONITORING
-- ============================================

-- Create extension for monitoring if not exists
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Function to analyze table statistics
CREATE OR REPLACE FUNCTION analyze_all_tables()
RETURNS void AS $$
DECLARE
    tbl RECORD;
BEGIN
    FOR tbl IN 
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ANALYZE %I.%I', tbl.schemaname, tbl.tablename);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Run ANALYZE on all tables to update statistics
SELECT analyze_all_tables();

-- ============================================
-- QUERY PERFORMANCE VIEWS
-- ============================================

-- View to identify slow queries
CREATE OR REPLACE VIEW slow_queries AS
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    rows
FROM pg_stat_statements
WHERE mean_exec_time > 100 -- queries taking more than 100ms
ORDER BY mean_exec_time DESC
LIMIT 20;

-- View to identify missing indexes
CREATE OR REPLACE VIEW missing_indexes AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
    AND n_distinct > 100
    AND correlation < 0.1
ORDER BY n_distinct DESC;

-- ============================================
-- MAINTENANCE COMMANDS
-- ============================================

-- Vacuum and analyze all tables
VACUUM ANALYZE;

-- Reindex all indexes for optimal performance
REINDEX DATABASE postgres;

-- Update table statistics
ANALYZE florida_parcels;
ANALYZE sunbiz_corporate;
ANALYZE property_sales_history;
ANALYZE building_permits;
ANALYZE tax_certificates;

-- ============================================
-- MONITORING QUERIES
-- ============================================

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database optimization complete!';
    RAISE NOTICE 'Created % indexes', (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public');
    RAISE NOTICE 'Created materialized view for fast property summaries';
    RAISE NOTICE 'Updated table statistics for query optimizer';
END $$;