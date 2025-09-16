-- =====================================================
-- CRITICAL DATABASE OPTIMIZATION SCRIPT
-- Performance Improvement: 10-100x expected
-- =====================================================

-- STEP 1: Add Missing Primary Keys
-- =====================================================

-- Check and add primary keys where missing
DO $$
BEGIN
    -- Add primary key to florida_parcels if missing
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'florida_parcels_pkey'
        AND conrelid = 'public.florida_parcels'::regclass
    ) THEN
        ALTER TABLE public.florida_parcels
        ADD CONSTRAINT florida_parcels_pkey PRIMARY KEY (id);
        RAISE NOTICE 'Added primary key to florida_parcels';
    END IF;

    -- Add composite unique constraint for business logic
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'florida_parcels_unique_parcel'
        AND conrelid = 'public.florida_parcels'::regclass
    ) THEN
        ALTER TABLE public.florida_parcels
        ADD CONSTRAINT florida_parcels_unique_parcel
        UNIQUE (parcel_id, county, year);
        RAISE NOTICE 'Added unique constraint to florida_parcels';
    END IF;
END $$;

-- STEP 2: Create High-Impact Indexes
-- =====================================================

-- Florida Parcels Indexes (Most Critical)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county
    ON public.florida_parcels(county);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_parcel_id
    ON public.florida_parcels(parcel_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_year
    ON public.florida_parcels(year);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name
    ON public.florida_parcels(owner_name)
    WHERE owner_name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_just_value
    ON public.florida_parcels(just_value)
    WHERE just_value > 0;

-- Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county_year
    ON public.florida_parcels(county, year);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_location
    ON public.florida_parcels(phy_city, phy_state)
    WHERE phy_city IS NOT NULL;

-- Performance index for value queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_value_range
    ON public.florida_parcels(just_value)
    WHERE just_value BETWEEN 100000 AND 1000000;

-- STEP 3: Optimize Florida Entities Table
-- =====================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_entities_name
    ON public.florida_entities(entity_name)
    WHERE entity_name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_entities_status
    ON public.florida_entities(status)
    WHERE status IN ('ACTIVE', 'INACTIVE');

-- STEP 4: Optimize Sunbiz Corporate Table
-- =====================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_number
    ON public.sunbiz_corporate(corp_number)
    WHERE corp_number IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_name
    ON public.sunbiz_corporate(corp_name)
    WHERE corp_name IS NOT NULL;

-- STEP 5: Create Partial Indexes for Better Performance
-- =====================================================

-- Index for recently sold properties
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_recent_sales
    ON public.florida_parcels(sale_date, sale_price)
    WHERE sale_date > '2020-01-01' AND sale_price > 0;

-- Index for residential properties
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_residential
    ON public.florida_parcels(bedrooms, bathrooms, total_living_area)
    WHERE property_use LIKE '%RESIDENTIAL%'
    AND bedrooms > 0;

-- STEP 6: Create GIN Indexes for JSONB Columns
-- =====================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_geometry_gin
    ON public.florida_parcels USING gin (geometry)
    WHERE geometry IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_centroid_gin
    ON public.florida_parcels USING gin (centroid)
    WHERE centroid IS NOT NULL;

-- STEP 7: Analyze Tables for Query Planner
-- =====================================================

ANALYZE public.florida_parcels;
ANALYZE public.florida_entities;
ANALYZE public.sunbiz_corporate;

-- STEP 8: Create Statistics for Better Query Planning
-- =====================================================

-- Create extended statistics for correlated columns
CREATE STATISTICS IF NOT EXISTS florida_parcels_stats (dependencies)
    ON county, year FROM public.florida_parcels;

CREATE STATISTICS IF NOT EXISTS florida_parcels_value_stats (dependencies)
    ON just_value, land_value, building_value FROM public.florida_parcels;

-- STEP 9: Create Monitoring View
-- =====================================================

CREATE OR REPLACE VIEW v_index_usage AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- STEP 10: Create Performance Monitoring Function
-- =====================================================

CREATE OR REPLACE FUNCTION check_index_performance()
RETURNS TABLE(
    table_name text,
    index_name text,
    index_size text,
    index_scans bigint,
    avg_tuples_per_scan numeric,
    recommendation text
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.tablename::text,
        i.indexname::text,
        pg_size_pretty(pg_relation_size(i.indexrelid))::text,
        i.idx_scan,
        CASE
            WHEN i.idx_scan > 0
            THEN round((i.idx_tup_fetch::numeric / i.idx_scan), 2)
            ELSE 0
        END as avg_tuples,
        CASE
            WHEN i.idx_scan = 0 THEN 'UNUSED - Consider dropping'
            WHEN i.idx_scan < 100 THEN 'RARELY USED - Monitor usage'
            WHEN i.idx_tup_fetch / GREATEST(i.idx_scan, 1) > 1000 THEN 'EFFICIENT - Good performance'
            ELSE 'ACTIVE - Normal usage'
        END::text as recommendation
    FROM pg_stat_user_indexes i
    WHERE i.schemaname = 'public'
    ORDER BY i.idx_scan DESC;
END;
$$ LANGUAGE plpgsql;

-- View current performance
-- SELECT * FROM check_index_performance();

-- COMPLETION MESSAGE
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'INDEX OPTIMIZATION COMPLETE';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Expected Performance Improvement: 10-100x';
    RAISE NOTICE 'Run SELECT * FROM check_index_performance() to monitor';
END $$;