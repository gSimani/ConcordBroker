-- Sunbiz Optimized Database Schema for Supabase
-- Handles corporate entity data from Florida Division of Corporations
-- Designed for efficient property owner matching and entity searches

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy text matching
CREATE EXTENSION IF NOT EXISTS btree_gin; -- For composite GIN indexes

-- Drop existing tables (for clean overwrite)
DROP TABLE IF EXISTS sunbiz_property_matches CASCADE;
DROP TABLE IF EXISTS sunbiz_officers CASCADE;
DROP TABLE IF EXISTS sunbiz_entities CASCADE;
DROP TABLE IF EXISTS sunbiz_data_processing_log CASCADE;

-- ============================================================================
-- MAIN ENTITIES TABLE
-- ============================================================================
CREATE TABLE sunbiz_entities (
    entity_id VARCHAR(12) PRIMARY KEY,  -- Fixed 12-char ID from data
    entity_name TEXT NOT NULL,
    entity_type CHAR(1),  -- C = Corporation, P = Person, etc.
    record_status VARCHAR(10),
    file_source VARCHAR(50),  -- Which corprindata file
    
    -- Denormalized search columns for performance
    entity_name_search tsvector GENERATED ALWAYS AS (to_tsvector('english', entity_name)) STORED,
    entity_name_normalized TEXT GENERATED ALWAYS AS (upper(regexp_replace(entity_name, '[^A-Z0-9]', '', 'g'))) STORED,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Unique constraint for overwrite behavior
    CONSTRAINT unique_entity_source UNIQUE (entity_id, file_source)
);

-- ============================================================================
-- OFFICERS TABLE
-- ============================================================================
CREATE TABLE sunbiz_officers (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(12) NOT NULL,
    officer_type VARCHAR(10),  -- PRES, VP, SEC, TRES, MGR, etc.
    record_type CHAR(1),  -- P = Person, C = Corporation
    
    -- Name fields (fixed positions from data)
    last_name VARCHAR(100),
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    suffix VARCHAR(10),  -- Jr., Sr., III, Esq., etc.
    
    -- Address fields
    street_address TEXT,
    city VARCHAR(100),
    state CHAR(2),
    zip_code VARCHAR(10),
    
    -- Denormalized fields for fast searching
    full_name TEXT GENERATED ALWAYS AS (
        TRIM(CONCAT_WS(' ', first_name, middle_name, last_name, suffix))
    ) STORED,
    
    full_address TEXT GENERATED ALWAYS AS (
        TRIM(CONCAT_WS(', ', street_address, city, state || ' ' || zip_code))
    ) STORED,
    
    -- Search optimization
    name_search tsvector GENERATED ALWAYS AS (
        to_tsvector('english', COALESCE(first_name, '') || ' ' || COALESCE(last_name, ''))
    ) STORED,
    
    address_search tsvector GENERATED ALWAYS AS (
        to_tsvector('english', COALESCE(street_address, '') || ' ' || COALESCE(city, ''))
    ) STORED,
    
    -- Metadata
    file_source VARCHAR(50),
    line_number INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (entity_id) REFERENCES sunbiz_entities(entity_id) ON DELETE CASCADE
);

-- ============================================================================
-- PROPERTY MATCHING TABLE
-- ============================================================================
CREATE TABLE sunbiz_property_matches (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(12),
    officer_id INTEGER,
    parcel_id VARCHAR(50) NOT NULL,  -- Links to florida_properties_core
    
    -- Match details
    match_type VARCHAR(50),  -- EXACT_ENTITY, FUZZY_ENTITY, OFFICER_NAME, ADDRESS, etc.
    match_score DECIMAL(5,4),  -- 0.0000 to 1.0000
    confidence_score DECIMAL(5,4),  -- Combined confidence
    
    -- Match metadata
    matched_entity_name TEXT,
    matched_officer_name TEXT,
    matched_address TEXT,
    property_owner_name TEXT,
    property_address TEXT,
    
    -- Processing info
    match_algorithm VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    verification_status VARCHAR(20),  -- PENDING, VERIFIED, REJECTED
    
    FOREIGN KEY (entity_id) REFERENCES sunbiz_entities(entity_id) ON DELETE CASCADE,
    FOREIGN KEY (officer_id) REFERENCES sunbiz_officers(id) ON DELETE CASCADE,
    
    -- Prevent duplicate matches
    CONSTRAINT unique_property_match UNIQUE (entity_id, officer_id, parcel_id, match_type)
);

-- ============================================================================
-- DATA PROCESSING LOG
-- ============================================================================
CREATE TABLE sunbiz_data_processing_log (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64),  -- MD5 hash to detect changes
    processing_started TIMESTAMP NOT NULL,
    processing_completed TIMESTAMP,
    status VARCHAR(20),  -- SUCCESS, FAILED, IN_PROGRESS
    
    -- Statistics
    total_lines INTEGER,
    entities_processed INTEGER,
    officers_processed INTEGER,
    entities_created INTEGER,
    entities_updated INTEGER,
    officers_created INTEGER,
    officers_updated INTEGER,
    errors_count INTEGER,
    
    -- Error details
    error_details JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent reprocessing same file
    CONSTRAINT unique_file_hash UNIQUE (file_hash)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Entity indexes
CREATE INDEX idx_entities_name_search ON sunbiz_entities USING GIN (entity_name_search);
CREATE INDEX idx_entities_name_trigram ON sunbiz_entities USING GIN (entity_name gin_trgm_ops);
CREATE INDEX idx_entities_normalized ON sunbiz_entities (entity_name_normalized);
CREATE INDEX idx_entities_type ON sunbiz_entities (entity_type) WHERE entity_type IS NOT NULL;
CREATE INDEX idx_entities_updated ON sunbiz_entities (updated_at DESC);

-- Officer indexes
CREATE INDEX idx_officers_entity ON sunbiz_officers (entity_id);
CREATE INDEX idx_officers_name_search ON sunbiz_officers USING GIN (name_search);
CREATE INDEX idx_officers_address_search ON sunbiz_officers USING GIN (address_search);
CREATE INDEX idx_officers_full_name_trigram ON sunbiz_officers USING GIN (full_name gin_trgm_ops);
CREATE INDEX idx_officers_last_first ON sunbiz_officers (last_name, first_name);
CREATE INDEX idx_officers_city_state ON sunbiz_officers (city, state);
CREATE INDEX idx_officers_type ON sunbiz_officers (officer_type) WHERE officer_type IS NOT NULL;

-- Property match indexes
CREATE INDEX idx_matches_parcel ON sunbiz_property_matches (parcel_id);
CREATE INDEX idx_matches_entity ON sunbiz_property_matches (entity_id);
CREATE INDEX idx_matches_officer ON sunbiz_property_matches (officer_id);
CREATE INDEX idx_matches_score ON sunbiz_property_matches (confidence_score DESC);
CREATE INDEX idx_matches_type ON sunbiz_property_matches (match_type);
CREATE INDEX idx_matches_verified ON sunbiz_property_matches (verification_status) 
    WHERE verification_status = 'VERIFIED';

-- ============================================================================
-- MATERIALIZED VIEWS FOR FAST QUERIES
-- ============================================================================

-- Active entities with officer counts
CREATE MATERIALIZED VIEW sunbiz_entity_summary AS
SELECT 
    e.entity_id,
    e.entity_name,
    e.entity_type,
    COUNT(DISTINCT o.id) as officer_count,
    COUNT(DISTINCT o.city || ',' || o.state) as location_count,
    MAX(e.updated_at) as last_updated
FROM sunbiz_entities e
LEFT JOIN sunbiz_officers o ON e.entity_id = o.entity_id
GROUP BY e.entity_id, e.entity_name, e.entity_type;

CREATE UNIQUE INDEX idx_entity_summary_id ON sunbiz_entity_summary (entity_id);
CREATE INDEX idx_entity_summary_name ON sunbiz_entity_summary USING GIN (entity_name gin_trgm_ops);

-- ============================================================================
-- FUNCTIONS FOR EFFICIENT OPERATIONS
-- ============================================================================

-- Function to search entities with fuzzy matching
CREATE OR REPLACE FUNCTION search_sunbiz_entities(
    search_term TEXT,
    search_type TEXT DEFAULT 'all',  -- 'all', 'entity', 'officer'
    similarity_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    entity_id VARCHAR,
    entity_name TEXT,
    match_type TEXT,
    similarity_score FLOAT,
    officer_name TEXT,
    officer_role VARCHAR
) AS $$
BEGIN
    -- Entity name search
    IF search_type IN ('all', 'entity') THEN
        RETURN QUERY
        SELECT 
            e.entity_id,
            e.entity_name,
            'ENTITY_NAME'::TEXT as match_type,
            similarity(e.entity_name, search_term) as similarity_score,
            NULL::TEXT as officer_name,
            NULL::VARCHAR as officer_role
        FROM sunbiz_entities e
        WHERE e.entity_name % search_term  -- Trigram similarity operator
            AND similarity(e.entity_name, search_term) >= similarity_threshold
        ORDER BY similarity_score DESC
        LIMIT 100;
    END IF;
    
    -- Officer name search
    IF search_type IN ('all', 'officer') THEN
        RETURN QUERY
        SELECT 
            o.entity_id,
            e.entity_name,
            'OFFICER_NAME'::TEXT as match_type,
            similarity(o.full_name, search_term) as similarity_score,
            o.full_name as officer_name,
            o.officer_type as officer_role
        FROM sunbiz_officers o
        JOIN sunbiz_entities e ON o.entity_id = e.entity_id
        WHERE o.full_name % search_term
            AND similarity(o.full_name, search_term) >= similarity_threshold
        ORDER BY similarity_score DESC
        LIMIT 100;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to find entities by address
CREATE OR REPLACE FUNCTION find_sunbiz_by_address(
    search_address TEXT,
    search_city TEXT DEFAULT NULL,
    search_state CHAR(2) DEFAULT 'FL'
)
RETURNS TABLE (
    entity_id VARCHAR,
    entity_name TEXT,
    officer_name TEXT,
    full_address TEXT,
    match_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.entity_id,
        e.entity_name,
        o.full_name as officer_name,
        o.full_address,
        CASE 
            WHEN search_city IS NOT NULL THEN
                similarity(o.street_address, search_address) * 0.6 +
                similarity(o.city, search_city) * 0.3 +
                CASE WHEN o.state = search_state THEN 0.1 ELSE 0 END
            ELSE
                similarity(o.full_address, search_address)
        END as match_score
    FROM sunbiz_officers o
    JOIN sunbiz_entities e ON o.entity_id = e.entity_id
    WHERE 
        (search_city IS NULL OR o.city ILIKE '%' || search_city || '%')
        AND o.state = search_state
        AND (o.street_address % search_address OR o.full_address % search_address)
    ORDER BY match_score DESC
    LIMIT 50;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_sunbiz_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY sunbiz_entity_summary;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE sunbiz_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_officers ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_property_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_data_processing_log ENABLE ROW LEVEL SECURITY;

-- Public read access for searching
CREATE POLICY "Public read access" ON sunbiz_entities FOR SELECT USING (true);
CREATE POLICY "Public read access" ON sunbiz_officers FOR SELECT USING (true);
CREATE POLICY "Public read access" ON sunbiz_property_matches FOR SELECT USING (true);

-- Admin/service role write access
CREATE POLICY "Service role write" ON sunbiz_entities FOR ALL 
    USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service role write" ON sunbiz_officers FOR ALL 
    USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service role write" ON sunbiz_property_matches FOR ALL 
    USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service role write" ON sunbiz_data_processing_log FOR ALL 
    USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================================
-- INITIAL SETUP
-- ============================================================================

-- Create initial processing log entry
INSERT INTO sunbiz_data_processing_log (
    file_name, 
    processing_started, 
    status,
    created_at
) VALUES (
    'INITIAL_SCHEMA_DEPLOYMENT',
    NOW(),
    'SUCCESS',
    NOW()
) ON CONFLICT DO NOTHING;