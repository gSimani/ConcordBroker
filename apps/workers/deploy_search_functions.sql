-- ============================================================
-- SUNBIZ FUZZY SEARCH FUNCTIONS
-- High-performance search functions for entity matching
-- ============================================================

-- 1. MAIN ENTITY SEARCH FUNCTION
-- Searches across corporations, fictitious names, and agents
CREATE OR REPLACE FUNCTION search_entities(
    search_term TEXT,
    threshold FLOAT DEFAULT 0.3,
    max_results INT DEFAULT 100
)
RETURNS TABLE (
    doc_number VARCHAR,
    entity_name VARCHAR,
    entity_type VARCHAR,
    status VARCHAR,
    match_score FLOAT,
    match_source VARCHAR,
    city VARCHAR,
    state VARCHAR
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    -- Search corporations by name
    SELECT 
        c.doc_number,
        c.entity_name,
        'CORPORATION'::VARCHAR as entity_type,
        c.status,
        similarity(c.entity_name, search_term)::FLOAT as match_score,
        'entity_name'::VARCHAR as match_source,
        c.prin_city::VARCHAR as city,
        c.prin_state::VARCHAR as state
    FROM sunbiz_corporate c
    WHERE c.entity_name % search_term
    
    UNION ALL
    
    -- Search corporations by registered agent
    SELECT 
        c.doc_number,
        c.entity_name,
        'CORPORATION'::VARCHAR as entity_type,
        c.status,
        similarity(c.registered_agent, search_term)::FLOAT as match_score,
        'registered_agent'::VARCHAR as match_source,
        c.prin_city::VARCHAR as city,
        c.prin_state::VARCHAR as state
    FROM sunbiz_corporate c
    WHERE c.registered_agent IS NOT NULL 
        AND c.registered_agent % search_term
    
    UNION ALL
    
    -- Search fictitious names (if table exists)
    SELECT 
        f.doc_number,
        f.name as entity_name,
        'FICTITIOUS'::VARCHAR as entity_type,
        f.status,
        similarity(f.name, search_term)::FLOAT as match_score,
        'fictitious_name'::VARCHAR as match_source,
        NULL::VARCHAR as city,
        NULL::VARCHAR as state
    FROM sunbiz_fictitious f
    WHERE f.name % search_term
    
    ORDER BY match_score DESC
    LIMIT max_results;
END;
$$;

-- 2. PROPERTY-ENTITY MATCHING FUNCTION
-- Matches property owners to business entities
CREATE OR REPLACE FUNCTION match_property_to_entities(
    property_owner TEXT,
    property_address TEXT DEFAULT NULL,
    min_confidence FLOAT DEFAULT 0.6
)
RETURNS TABLE (
    doc_number VARCHAR,
    entity_name VARCHAR,
    match_type VARCHAR,
    confidence FLOAT,
    status VARCHAR,
    filing_date DATE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    -- Exact name match (highest confidence)
    SELECT 
        c.doc_number,
        c.entity_name,
        'EXACT_NAME'::VARCHAR as match_type,
        1.0::FLOAT as confidence,
        c.status,
        c.filing_date
    FROM sunbiz_corporate c
    WHERE UPPER(TRIM(c.entity_name)) = UPPER(TRIM(property_owner))
    
    UNION ALL
    
    -- Very high similarity match
    SELECT 
        c.doc_number,
        c.entity_name,
        'HIGH_SIMILARITY'::VARCHAR as match_type,
        similarity(c.entity_name, property_owner)::FLOAT as confidence,
        c.status,
        c.filing_date
    FROM sunbiz_corporate c
    WHERE c.entity_name % property_owner
        AND similarity(c.entity_name, property_owner) >= 0.8
        AND UPPER(TRIM(c.entity_name)) != UPPER(TRIM(property_owner))
    
    UNION ALL
    
    -- Fuzzy name match
    SELECT 
        c.doc_number,
        c.entity_name,
        'FUZZY_NAME'::VARCHAR as match_type,
        similarity(c.entity_name, property_owner)::FLOAT as confidence,
        c.status,
        c.filing_date
    FROM sunbiz_corporate c
    WHERE c.entity_name % property_owner
        AND similarity(c.entity_name, property_owner) >= min_confidence
        AND similarity(c.entity_name, property_owner) < 0.8
    
    UNION ALL
    
    -- Address match (if provided)
    SELECT 
        c.doc_number,
        c.entity_name,
        'ADDRESS_MATCH'::VARCHAR as match_type,
        0.7::FLOAT as confidence,
        c.status,
        c.filing_date
    FROM sunbiz_corporate c
    WHERE property_address IS NOT NULL
        AND c.prin_addr1 IS NOT NULL
        AND (
            c.prin_addr1 ILIKE '%' || property_address || '%'
            OR property_address ILIKE '%' || c.prin_addr1 || '%'
        )
    
    ORDER BY confidence DESC, filing_date DESC
    LIMIT 10;
END;
$$;

-- 3. ENTITY DETAILS FUNCTION
-- Get complete entity information with related entities
CREATE OR REPLACE FUNCTION get_entity_details(
    entity_doc_number VARCHAR
)
RETURNS TABLE (
    doc_number VARCHAR,
    entity_name VARCHAR,
    status VARCHAR,
    filing_date DATE,
    state_country VARCHAR,
    prin_address TEXT,
    mail_address TEXT,
    ein VARCHAR,
    registered_agent VARCHAR,
    file_type VARCHAR,
    related_entities JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.doc_number,
        c.entity_name,
        c.status,
        c.filing_date,
        c.state_country,
        CONCAT_WS(', ', c.prin_addr1, c.prin_city, c.prin_state, c.prin_zip) as prin_address,
        CONCAT_WS(', ', c.mail_addr1, c.mail_city, c.mail_state, c.mail_zip) as mail_address,
        c.ein,
        c.registered_agent,
        c.file_type,
        (
            -- Find related entities by agent
            SELECT jsonb_agg(jsonb_build_object(
                'doc_number', r.doc_number,
                'entity_name', r.entity_name,
                'relationship', 'SAME_AGENT'
            ))
            FROM sunbiz_corporate r
            WHERE r.registered_agent = c.registered_agent
                AND r.doc_number != c.doc_number
                AND r.registered_agent IS NOT NULL
            LIMIT 5
        ) as related_entities
    FROM sunbiz_corporate c
    WHERE c.doc_number = entity_doc_number;
END;
$$;

-- 4. ACTIVE FLORIDA CORPORATIONS SEARCH
-- Optimized search for active FL corporations
CREATE OR REPLACE FUNCTION search_active_fl_corporations(
    search_term TEXT,
    city_filter VARCHAR DEFAULT NULL,
    zip_filter VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    doc_number VARCHAR,
    entity_name VARCHAR,
    filing_date DATE,
    city VARCHAR,
    zip VARCHAR,
    registered_agent VARCHAR,
    match_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.doc_number,
        c.entity_name,
        c.filing_date,
        c.prin_city,
        c.prin_zip,
        c.registered_agent,
        similarity(c.entity_name, search_term) as match_score
    FROM sunbiz_corporate c
    WHERE c.status = 'ACTIVE'
        AND c.state_country = 'FL'
        AND c.entity_name % search_term
        AND (city_filter IS NULL OR c.prin_city ILIKE '%' || city_filter || '%')
        AND (zip_filter IS NULL OR c.prin_zip = zip_filter)
    ORDER BY match_score DESC, c.filing_date DESC
    LIMIT 100;
END;
$$;

-- 5. ENTITY NAME VARIATIONS FUNCTION
-- Find variations of entity names (DBAs, similar names)
CREATE OR REPLACE FUNCTION find_entity_variations(
    base_entity_name TEXT,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    doc_number VARCHAR,
    entity_name VARCHAR,
    entity_type VARCHAR,
    similarity_score FLOAT,
    status VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    -- Find similar corporation names
    SELECT 
        c.doc_number,
        c.entity_name,
        'CORPORATION'::VARCHAR as entity_type,
        similarity(c.entity_name, base_entity_name) as similarity_score,
        c.status
    FROM sunbiz_corporate c
    WHERE c.entity_name % base_entity_name
        AND similarity(c.entity_name, base_entity_name) >= similarity_threshold
    
    UNION ALL
    
    -- Find fictitious names
    SELECT 
        f.doc_number,
        f.name as entity_name,
        'FICTITIOUS/DBA'::VARCHAR as entity_type,
        similarity(f.name, base_entity_name) as similarity_score,
        f.status
    FROM sunbiz_fictitious f
    WHERE f.name % base_entity_name
        AND similarity(f.name, base_entity_name) >= similarity_threshold
    
    ORDER BY similarity_score DESC
    LIMIT 50;
END;
$$;

-- 6. BULK PROPERTY MATCHING FUNCTION
-- Match multiple properties to entities in one call
CREATE OR REPLACE FUNCTION bulk_match_properties(
    property_owners TEXT[]
)
RETURNS TABLE (
    property_owner TEXT,
    doc_number VARCHAR,
    entity_name VARCHAR,
    confidence FLOAT,
    status VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    owner TEXT;
BEGIN
    FOREACH owner IN ARRAY property_owners
    LOOP
        RETURN QUERY
        SELECT 
            owner as property_owner,
            c.doc_number,
            c.entity_name,
            similarity(c.entity_name, owner) as confidence,
            c.status
        FROM sunbiz_corporate c
        WHERE c.entity_name % owner
            AND similarity(c.entity_name, owner) >= 0.6
        ORDER BY similarity(c.entity_name, owner) DESC
        LIMIT 1;
    END LOOP;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION search_entities TO authenticated, anon;
GRANT EXECUTE ON FUNCTION match_property_to_entities TO authenticated, anon;
GRANT EXECUTE ON FUNCTION get_entity_details TO authenticated, anon;
GRANT EXECUTE ON FUNCTION search_active_fl_corporations TO authenticated, anon;
GRANT EXECUTE ON FUNCTION find_entity_variations TO authenticated, anon;
GRANT EXECUTE ON FUNCTION bulk_match_properties TO authenticated, anon;

-- Create indexes for function optimization (if not exists)
CREATE INDEX IF NOT EXISTS idx_corporate_upper_name 
    ON sunbiz_corporate(UPPER(entity_name));

CREATE INDEX IF NOT EXISTS idx_corporate_status_state 
    ON sunbiz_corporate(status, state_country) 
    WHERE status = 'ACTIVE' AND state_country = 'FL';

-- ============================================================
-- SAMPLE USAGE QUERIES
-- ============================================================

-- Search for entities
-- SELECT * FROM search_entities('CONCORD BROKER', 0.3, 50);

-- Match property to entities
-- SELECT * FROM match_property_to_entities('CONCORD BROKER LLC', '123 MAIN ST');

-- Get entity details
-- SELECT * FROM get_entity_details('P20000012345');

-- Search active Florida corporations
-- SELECT * FROM search_active_fl_corporations('REAL ESTATE', 'BOCA RATON', '33432');

-- Find entity variations
-- SELECT * FROM find_entity_variations('CONCORD HOLDINGS', 0.7);

-- Bulk match properties
-- SELECT * FROM bulk_match_properties(ARRAY['ABC CORP', 'XYZ LLC', 'SMITH HOLDINGS']);