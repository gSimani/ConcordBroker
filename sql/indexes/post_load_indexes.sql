-- Post-Load Performance Indexes for Florida Parcels
-- Run after bulk data upload completes

-- Primary indexes for searching and filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county_parcel 
ON public.florida_parcels(county, parcel_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name_gin 
ON public.florida_parcels USING gin(owner_name gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_addr1_gin 
ON public.florida_parcels USING gin(phy_addr1 gin_trgm_ops);

-- Value-based searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_just_value 
ON public.florida_parcels(just_value) 
WHERE just_value IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_sale_price 
ON public.florida_parcels(sale_price) 
WHERE sale_price IS NOT NULL;

-- Location indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_city 
ON public.florida_parcels(phy_city);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_zipcd 
ON public.florida_parcels(phy_zipcd);

-- Property type filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_land_use_code 
ON public.florida_parcels(land_use_code);

-- Performance monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_import_date 
ON public.florida_parcels(import_date DESC);

-- Composite index for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county_city_value 
ON public.florida_parcels(county, phy_city, just_value);

-- Update table statistics for query planner
ANALYZE public.florida_parcels;

-- Create materialized view for county summaries (optional - for dashboard)
CREATE MATERIALIZED VIEW IF NOT EXISTS public.florida_parcels_county_summary AS
SELECT 
    county,
    COUNT(*) AS total_properties,
    AVG(just_value) AS avg_value,
    MEDIAN(just_value) AS median_value,
    SUM(just_value) AS total_value,
    COUNT(DISTINCT phy_city) AS unique_cities,
    MAX(import_date) AS last_updated
FROM public.florida_parcels
GROUP BY county
WITH DATA;

-- Index the materialized view
CREATE UNIQUE INDEX ON public.florida_parcels_county_summary(county);

-- Refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_county_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.florida_parcels_county_summary;
END;
$$ LANGUAGE plpgsql;

-- Clean up any duplicate indexes (run after checking existing indexes)
-- SELECT indexname, indexdef FROM pg_indexes 
-- WHERE tablename = 'florida_parcels' 
-- ORDER BY indexname;