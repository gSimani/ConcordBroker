-- ============================================================================
-- FIXED DATABASE OPTIMIZATION FOR CONCORDBROKER
-- This version works in Supabase SQL Editor without transaction block errors
-- Run each section separately by selecting and running with Ctrl+Enter
-- ============================================================================

-- SECTION 1: Create indexes WITHOUT CONCURRENTLY (run this section first)
-- Select all lines in this section and run with Ctrl+Enter

CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id 
    ON florida_parcels(parcel_id);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_addr1 
    ON florida_parcels(phy_addr1);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_city 
    ON florida_parcels(phy_city);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name 
    ON florida_parcels(owner_name);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_county 
    ON florida_parcels(county);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_assessed_value 
    ON florida_parcels(assessed_value);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_year_built 
    ON florida_parcels(year_built);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_filters 
    ON florida_parcels(county, assessed_value, year_built);

-- Full text search indexes
CREATE INDEX IF NOT EXISTS idx_florida_parcels_addr_search 
    ON florida_parcels USING gin(to_tsvector('english', COALESCE(phy_addr1, '') || ' ' || COALESCE(phy_city, '')));

CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_search 
    ON florida_parcels USING gin(to_tsvector('english', COALESCE(owner_name, '')));

-- Sales history indexes
CREATE INDEX IF NOT EXISTS idx_sales_history_parcel 
    ON property_sales_history(parcel_id);

CREATE INDEX IF NOT EXISTS idx_sales_history_date 
    ON property_sales_history(sale_date DESC);

CREATE INDEX IF NOT EXISTS idx_sales_history_price 
    ON property_sales_history(sale_price);

-- NAV assessments indexes
CREATE INDEX IF NOT EXISTS idx_nav_assessments_parcel 
    ON nav_assessments(parcel_id);

CREATE INDEX IF NOT EXISTS idx_nav_assessments_amount 
    ON nav_assessments(total_assessment);

-- Sunbiz corporate indexes (if table exists)
CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_name 
    ON sunbiz_corporate(corporate_name);

CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_address 
    ON sunbiz_corporate(principal_address);

-- ============================================================================
-- SECTION 2: Create materialized view (run this section after indexes)
-- Select all lines in this section and run with Ctrl+Enter
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS property_search_fast CASCADE;

CREATE MATERIALIZED VIEW property_search_fast AS
SELECT 
    p.parcel_id,
    p.phy_addr1,
    p.phy_city,
    p.phy_state,
    p.phy_zipcd,
    -- Create full address for easy searching
    COALESCE(p.phy_addr1, '') || ', ' || 
    COALESCE(p.phy_city, '') || ', FL ' || 
    COALESCE(p.phy_zipcd, '') as full_address,
    p.owner_name,
    p.assessed_value,
    p.taxable_value,
    p.just_value,
    p.land_value,
    p.building_value,
    p.year_built,
    p.total_living_area,
    p.bedrooms,
    p.bathrooms,
    p.property_use,
    p.property_use_desc,
    -- Get latest sale info
    s.last_sale_price,
    s.last_sale_date,
    -- Get total NAV assessments
    n.total_nav_assessment,
    -- Search vector for full text search
    to_tsvector('english', 
        COALESCE(p.phy_addr1, '') || ' ' || 
        COALESCE(p.phy_city, '') || ' ' || 
        COALESCE(p.owner_name, '') || ' ' ||
        COALESCE(p.property_use_desc, '')
    ) as search_vector
FROM florida_parcels p
-- Get most recent sale
LEFT JOIN LATERAL (
    SELECT 
        sale_price as last_sale_price,
        sale_date as last_sale_date
    FROM property_sales_history
    WHERE parcel_id = p.parcel_id
    ORDER BY sale_date DESC
    LIMIT 1
) s ON true
-- Get total NAV assessments
LEFT JOIN LATERAL (
    SELECT SUM(total_assessment) as total_nav_assessment
    FROM nav_assessments
    WHERE parcel_id = p.parcel_id
) n ON true
WHERE p.parcel_id IS NOT NULL;

-- Create indexes on the materialized view
CREATE INDEX idx_search_fast_parcel ON property_search_fast(parcel_id);
CREATE INDEX idx_search_fast_address ON property_search_fast(full_address);
CREATE INDEX idx_search_fast_owner ON property_search_fast(owner_name);
CREATE INDEX idx_search_fast_value ON property_search_fast(assessed_value);
CREATE INDEX idx_search_fast_vector ON property_search_fast USING gin(search_vector);

-- ============================================================================
-- SECTION 3: Create search functions (run this section after materialized view)
-- Select all lines in this section and run with Ctrl+Enter
-- ============================================================================

CREATE OR REPLACE FUNCTION search_properties(
    search_term text,
    limit_count int DEFAULT 20,
    offset_count int DEFAULT 0
)
RETURNS TABLE (
    parcel_id varchar,
    full_address text,
    owner_name text,
    assessed_value numeric,
    bedrooms integer,
    bathrooms numeric,
    year_built integer,
    last_sale_price varchar,
    rank real
) 
LANGUAGE plpgsql
AS $$
BEGIN
    -- If search term looks like a parcel ID (starts with numbers)
    IF search_term ~ '^\d' THEN
        RETURN QUERY
        SELECT 
            p.parcel_id::varchar,
            p.full_address::text,
            p.owner_name::text,
            p.assessed_value::numeric,
            p.bedrooms::integer,
            p.bathrooms::numeric,
            p.year_built::integer,
            p.last_sale_price::varchar,
            1.0::real as rank
        FROM property_search_fast p
        WHERE p.parcel_id ILIKE search_term || '%'
        ORDER BY p.parcel_id
        LIMIT limit_count
        OFFSET offset_count;
    ELSE
        -- Full text search for addresses and owner names
        RETURN QUERY
        SELECT 
            p.parcel_id::varchar,
            p.full_address::text,
            p.owner_name::text,
            p.assessed_value::numeric,
            p.bedrooms::integer,
            p.bathrooms::numeric,
            p.year_built::integer,
            p.last_sale_price::varchar,
            ts_rank(p.search_vector, plainto_tsquery('english', search_term))::real as rank
        FROM property_search_fast p
        WHERE p.search_vector @@ plainto_tsquery('english', search_term)
           OR p.full_address ILIKE '%' || search_term || '%'
           OR p.owner_name ILIKE '%' || search_term || '%'
        ORDER BY rank DESC, p.assessed_value DESC
        LIMIT limit_count
        OFFSET offset_count;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION get_property_details(property_parcel_id varchar)
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    result json;
BEGIN
    SELECT json_build_object(
        'property', row_to_json(p.*),
        'sales', COALESCE(s.sales, '[]'::json),
        'assessments', COALESCE(n.assessments, '[]'::json),
        'entities', COALESCE(e.entities, '[]'::json)
    ) INTO result
    FROM florida_parcels p
    -- Get sales history
    LEFT JOIN LATERAL (
        SELECT json_agg(
            json_build_object(
                'sale_date', sale_date,
                'sale_price', sale_price,
                'sale_type', sale_type
            ) ORDER BY sale_date DESC
        ) as sales
        FROM property_sales_history
        WHERE parcel_id = property_parcel_id
    ) s ON true
    -- Get NAV assessments
    LEFT JOIN LATERAL (
        SELECT json_agg(
            json_build_object(
                'district_name', district_name,
                'total_assessment', total_assessment
            )
        ) as assessments
        FROM nav_assessments
        WHERE parcel_id = property_parcel_id
    ) n ON true
    -- Get related business entities
    LEFT JOIN LATERAL (
        SELECT json_agg(
            json_build_object(
                'corporate_name', corporate_name,
                'entity_type', entity_type,
                'status', status
            )
        ) as entities
        FROM sunbiz_corporate
        WHERE principal_address ILIKE '%' || p.phy_addr1 || '%'
           OR corporate_name ILIKE '%' || p.owner_name || '%'
        LIMIT 5
    ) e ON true
    WHERE p.parcel_id = property_parcel_id;
    
    RETURN result;
END;
$$;

-- ============================================================================
-- SECTION 4: Grant permissions and analyze (run this section last)
-- Select all lines in this section and run with Ctrl+Enter
-- ============================================================================

-- Grant permissions for public access
GRANT SELECT ON property_search_fast TO anon, authenticated;
GRANT EXECUTE ON FUNCTION search_properties TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_property_details TO anon, authenticated;

-- Update table statistics for query planner
ANALYZE florida_parcels;
ANALYZE property_sales_history;
ANALYZE nav_assessments;
ANALYZE sunbiz_corporate;

-- Refresh the materialized view with data
REFRESH MATERIALIZED VIEW property_search_fast;

-- ============================================================================
-- SECTION 5: Verify everything worked (run this to test)
-- Select each query separately and run with Ctrl+Enter
-- ============================================================================

-- Check that indexes were created
SELECT 
    tablename,
    indexname
FROM pg_indexes
WHERE tablename IN ('florida_parcels', 'property_sales_history', 'nav_assessments', 'sunbiz_corporate', 'property_search_fast')
ORDER BY tablename, indexname;

-- Test the search function (should be FAST now!)
SELECT * FROM search_properties('main street', 10, 0);

-- Test property details function
SELECT get_property_details('064210010010');

-- Check materialized view
SELECT COUNT(*) as total_properties FROM property_search_fast;

-- Success message
SELECT 
    'DATABASE OPTIMIZATION COMPLETE!' as status,
    'Run each section separately to avoid transaction errors' as instructions;