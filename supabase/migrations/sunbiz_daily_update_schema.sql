-- ============================================================================
-- SUNBIZ DAILY UPDATE SCHEMA - CONSOLIDATED & PRODUCTION READY
-- ============================================================================
--
-- Purpose: Complete schema for Florida Sunbiz corporate entity data with
--          daily update tracking and change monitoring
--
-- Tables Created: 8 core tables
--   1. sunbiz_corporations       - Main corporate entities
--   2. sunbiz_fictitious_names   - DBA/fictitious name registrations
--   3. sunbiz_registered_agents  - Registered agent information
--   4. sunbiz_entity_search      - Fast entity lookup table
--   5. sunbiz_officers           - Corporate officers and directors
--   6. sunbiz_events             - Corporate events and filings
--   7. sunbiz_change_log         - Daily change tracking (NEW)
--   8. sunbiz_update_jobs        - Update job monitoring (NEW)
--
-- Expected Data Volumes:
--   - Corporations: ~3-4 million records
--   - Fictitious Names: ~1-2 million records
--   - Officers: ~5-10 million records
--   - Events: ~10-15 million records
--   - Change Log: ~50,000-100,000 per day
--
-- Update Frequency: Daily incremental updates at 2 AM EST
--
-- Dependencies:
--   - PostgreSQL 14+
--   - pg_trgm extension (for fuzzy search)
--   - btree_gin extension (for composite indexes)
--
-- Deployment Instructions:
--   1. Run this script in Supabase SQL Editor
--   2. Verify all tables created successfully
--   3. Check indexes are built
--   4. Test functions with sample queries
--   5. Configure daily update worker to use sunbiz_update_jobs
--
-- Author: Claude Code Consolidation
-- Date: 2025-10-24
-- Version: 1.0.0
-- ============================================================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- Trigram similarity for fuzzy text search
CREATE EXTENSION IF NOT EXISTS btree_gin;    -- GIN indexes for better composite index performance

-- ============================================================================
-- TABLE 1: SUNBIZ_CORPORATIONS - Main Corporate Entities
-- ============================================================================
CREATE TABLE IF NOT EXISTS sunbiz_corporations (
    -- Primary identifiers
    entity_id VARCHAR(50) PRIMARY KEY,           -- Increased from VARCHAR(12) to VARCHAR(50)
    entity_name VARCHAR(255) NOT NULL,
    doc_number VARCHAR(50),                      -- Document/filing number (VARCHAR(50) per fix)

    -- Entity status and classification
    status VARCHAR(20),                          -- ACTIVE, INACTIVE, DISSOLVED, etc.
    entity_type VARCHAR(50),                     -- Corporation type
    filing_date DATE,
    state_country VARCHAR(2),                    -- State of incorporation

    -- Principal address
    principal_address TEXT,
    principal_city VARCHAR(100),
    principal_state VARCHAR(2),
    principal_zip VARCHAR(10),

    -- Mailing address
    mailing_address TEXT,
    mailing_city VARCHAR(100),
    mailing_state VARCHAR(2),
    mailing_zip VARCHAR(10),

    -- Registered agent information
    registered_agent_name VARCHAR(255),
    registered_agent_address TEXT,
    registered_agent_city VARCHAR(100),
    registered_agent_state VARCHAR(2),
    registered_agent_zip VARCHAR(10),

    -- Additional identifiers
    fei_number VARCHAR(20),                      -- Federal Employer Identification Number

    -- Last event tracking
    last_event VARCHAR(50),
    event_date DATE,
    event_file_number VARCHAR(50),

    -- Search optimization (from optimized schema)
    entity_name_search tsvector GENERATED ALWAYS AS (
        to_tsvector('english', entity_name)
    ) STORED,
    entity_name_normalized TEXT GENERATED ALWAYS AS (
        upper(regexp_replace(entity_name, '[^A-Z0-9]', '', 'g'))
    ) STORED,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraints
    UNIQUE(doc_number)
);

-- ============================================================================
-- TABLE 2: SUNBIZ_FICTITIOUS_NAMES - DBA Registrations
-- ============================================================================
CREATE TABLE IF NOT EXISTS sunbiz_fictitious_names (
    -- Primary identifiers
    registration_id VARCHAR(50) PRIMARY KEY,     -- Increased from VARCHAR(20)
    doc_number VARCHAR(50),                      -- Document number (VARCHAR(50) per fix)
    name VARCHAR(255) NOT NULL,

    -- Owner information
    owner_name VARCHAR(255),
    owner_address TEXT,
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),

    -- Registration details
    registration_date DATE,
    expiration_date DATE,
    status VARCHAR(20),
    county VARCHAR(50),                          -- Florida county where registered

    -- Search optimization
    name_search tsvector GENERATED ALWAYS AS (
        to_tsvector('english', name)
    ) STORED,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(doc_number)
);

-- ============================================================================
-- TABLE 3: SUNBIZ_REGISTERED_AGENTS - Registered Agent Directory
-- ============================================================================
CREATE TABLE IF NOT EXISTS sunbiz_registered_agents (
    -- Primary identifiers
    agent_id VARCHAR(50) PRIMARY KEY,            -- Increased from VARCHAR(20)
    agent_name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50),                      -- Individual, Corporation, etc.

    -- Address information
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),

    -- Statistics
    entity_count INTEGER DEFAULT 0,              -- Number of entities using this agent

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLE 4: SUNBIZ_ENTITY_SEARCH - Fast Lookup Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS sunbiz_entity_search (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id VARCHAR(50),
    entity_name VARCHAR(255),
    normalized_name VARCHAR(255),                -- Uppercase, alphanumeric only
    entity_type VARCHAR(50),
    source_table VARCHAR(50),                    -- corporations, fictitious_names, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLE 5: SUNBIZ_OFFICERS - Corporate Officers and Directors (from optimized)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sunbiz_officers (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(50) NOT NULL,              -- Links to sunbiz_corporations

    -- Officer classification
    officer_type VARCHAR(10),                    -- PRES, VP, SEC, TRES, MGR, DIR, etc.
    record_type CHAR(1),                         -- P = Person, C = Corporation

    -- Name fields
    last_name VARCHAR(100),
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    suffix VARCHAR(10),                          -- Jr., Sr., III, Esq., etc.

    -- Address fields
    street_address TEXT,
    city VARCHAR(100),
    state CHAR(2),
    zip_code VARCHAR(10),

    -- Generated full name and address for fast searching
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (entity_id) REFERENCES sunbiz_corporations(entity_id) ON DELETE CASCADE
);

-- ============================================================================
-- TABLE 6: SUNBIZ_EVENTS - Corporate Events and Filings
-- ============================================================================
CREATE TABLE IF NOT EXISTS sunbiz_events (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(50) NOT NULL,              -- Links to sunbiz_corporations
    doc_number VARCHAR(50) NOT NULL,             -- Document number for this event

    -- Event details
    event_date DATE,
    event_type VARCHAR(50),                      -- ANNUAL REPORT, AMENDMENT, MERGER, etc.
    event_detail VARCHAR(200),                   -- Additional event information

    -- Metadata
    source_file VARCHAR(100),                    -- Which data file this came from
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (entity_id) REFERENCES sunbiz_corporations(entity_id) ON DELETE CASCADE
);

-- ============================================================================
-- TABLE 7: SUNBIZ_CHANGE_LOG - Daily Change Tracking (NEW)
-- ============================================================================
-- Tracks all detected changes to entities for daily updates
-- Models the property system's change tracking pattern
CREATE TABLE IF NOT EXISTS sunbiz_change_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id VARCHAR(50) NOT NULL,

    -- Change classification
    change_type VARCHAR(50) NOT NULL,            -- STATUS, ADDRESS, OFFICER, AGENT, NEW_ENTITY, NAME, etc.
    change_date DATE NOT NULL,

    -- Change details stored as JSONB for flexibility
    old_value JSONB,                             -- Previous state
    new_value JSONB,                             -- New state

    -- Processing tracking
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Optional notes
    notes TEXT
);

-- ============================================================================
-- TABLE 8: SUNBIZ_UPDATE_JOBS - Daily Update Job Monitoring (NEW)
-- ============================================================================
-- Tracks all daily update jobs for monitoring and debugging
-- Models the property system's job tracking pattern
CREATE TABLE IF NOT EXISTS sunbiz_update_jobs (
    job_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Job classification
    job_type VARCHAR(50) NOT NULL,               -- CORPORATE, FICTITIOUS, OFFICERS, EVENTS, AGENTS
    status VARCHAR(20) NOT NULL,                 -- RUNNING, COMPLETED, FAILED, PARTIAL

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER
    ) STORED,

    -- Statistics
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    changes_detected INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    -- Details
    error_details TEXT,
    file_processed VARCHAR(255),

    -- Additional metadata
    worker_id VARCHAR(50),                       -- Which worker process ran this job
    notes TEXT
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Corporations indexes
CREATE INDEX IF NOT EXISTS idx_corp_name ON sunbiz_corporations(entity_name);
CREATE INDEX IF NOT EXISTS idx_corp_name_search ON sunbiz_corporations USING GIN (entity_name_search);
CREATE INDEX IF NOT EXISTS idx_corp_name_trigram ON sunbiz_corporations USING GIN (entity_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_corp_normalized ON sunbiz_corporations(entity_name_normalized);
CREATE INDEX IF NOT EXISTS idx_corp_status ON sunbiz_corporations(status);
CREATE INDEX IF NOT EXISTS idx_corp_type ON sunbiz_corporations(entity_type) WHERE entity_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_corp_zip ON sunbiz_corporations(principal_zip);
CREATE INDEX IF NOT EXISTS idx_corp_filing_date ON sunbiz_corporations(filing_date);
CREATE INDEX IF NOT EXISTS idx_corp_agent ON sunbiz_corporations(registered_agent_name);
CREATE INDEX IF NOT EXISTS idx_corp_updated ON sunbiz_corporations(updated_at DESC);

-- Fictitious names indexes
CREATE INDEX IF NOT EXISTS idx_fic_name ON sunbiz_fictitious_names(name);
CREATE INDEX IF NOT EXISTS idx_fic_name_search ON sunbiz_fictitious_names USING GIN (name_search);
CREATE INDEX IF NOT EXISTS idx_fic_owner ON sunbiz_fictitious_names(owner_name);
CREATE INDEX IF NOT EXISTS idx_fic_county ON sunbiz_fictitious_names(county);
CREATE INDEX IF NOT EXISTS idx_fic_expires ON sunbiz_fictitious_names(expiration_date);
CREATE INDEX IF NOT EXISTS idx_fic_status ON sunbiz_fictitious_names(status);

-- Registered agents indexes
CREATE INDEX IF NOT EXISTS idx_agent_name ON sunbiz_registered_agents(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_city_state ON sunbiz_registered_agents(city, state);
CREATE INDEX IF NOT EXISTS idx_agent_count ON sunbiz_registered_agents(entity_count DESC);

-- Entity search indexes
CREATE INDEX IF NOT EXISTS idx_search_normalized ON sunbiz_entity_search(normalized_name);
CREATE INDEX IF NOT EXISTS idx_search_entity_id ON sunbiz_entity_search(entity_id);
CREATE INDEX IF NOT EXISTS idx_search_source ON sunbiz_entity_search(source_table);

-- Officers indexes
CREATE INDEX IF NOT EXISTS idx_officers_entity ON sunbiz_officers(entity_id);
CREATE INDEX IF NOT EXISTS idx_officers_name_search ON sunbiz_officers USING GIN (name_search);
CREATE INDEX IF NOT EXISTS idx_officers_address_search ON sunbiz_officers USING GIN (address_search);
CREATE INDEX IF NOT EXISTS idx_officers_full_name_trigram ON sunbiz_officers USING GIN (full_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_officers_last_first ON sunbiz_officers(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_officers_city_state ON sunbiz_officers(city, state);
CREATE INDEX IF NOT EXISTS idx_officers_type ON sunbiz_officers(officer_type) WHERE officer_type IS NOT NULL;

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_events_entity ON sunbiz_events(entity_id);
CREATE INDEX IF NOT EXISTS idx_events_doc ON sunbiz_events(doc_number);
CREATE INDEX IF NOT EXISTS idx_events_date ON sunbiz_events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_type ON sunbiz_events(event_type);

-- Change log indexes
CREATE INDEX IF NOT EXISTS idx_change_log_entity ON sunbiz_change_log(entity_id);
CREATE INDEX IF NOT EXISTS idx_change_log_date ON sunbiz_change_log(change_date);
CREATE INDEX IF NOT EXISTS idx_change_log_type ON sunbiz_change_log(change_type);
CREATE INDEX IF NOT EXISTS idx_change_log_processed ON sunbiz_change_log(processed) WHERE processed = FALSE;
CREATE INDEX IF NOT EXISTS idx_change_log_detected ON sunbiz_change_log(detected_at DESC);

-- Update jobs indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON sunbiz_update_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON sunbiz_update_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_date ON sunbiz_update_jobs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_duration ON sunbiz_update_jobs(duration_seconds) WHERE duration_seconds IS NOT NULL;

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function: Get daily update statistics
CREATE OR REPLACE FUNCTION get_sunbiz_update_stats(check_date DATE DEFAULT CURRENT_DATE)
RETURNS TABLE (
    job_type VARCHAR(50),
    total_jobs BIGINT,
    successful_jobs BIGINT,
    failed_jobs BIGINT,
    partial_jobs BIGINT,
    total_records INTEGER,
    total_changes INTEGER,
    avg_duration_seconds NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        j.job_type,
        COUNT(*) as total_jobs,
        COUNT(*) FILTER (WHERE j.status = 'COMPLETED') as successful_jobs,
        COUNT(*) FILTER (WHERE j.status = 'FAILED') as failed_jobs,
        COUNT(*) FILTER (WHERE j.status = 'PARTIAL') as partial_jobs,
        COALESCE(SUM(j.records_processed), 0)::INTEGER as total_records,
        COALESCE(SUM(j.changes_detected), 0)::INTEGER as total_changes,
        ROUND(AVG(j.duration_seconds), 2) as avg_duration_seconds
    FROM sunbiz_update_jobs j
    WHERE DATE(j.started_at) = check_date
    GROUP BY j.job_type;
END;
$$ LANGUAGE plpgsql;

-- Function: Log entity change
CREATE OR REPLACE FUNCTION log_sunbiz_change(
    p_entity_id VARCHAR(50),
    p_change_type VARCHAR(50),
    p_old_value JSONB,
    p_new_value JSONB,
    p_notes TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_change_id UUID;
BEGIN
    INSERT INTO sunbiz_change_log (
        entity_id,
        change_type,
        change_date,
        old_value,
        new_value,
        notes
    ) VALUES (
        p_entity_id,
        p_change_type,
        CURRENT_DATE,
        p_old_value,
        p_new_value,
        p_notes
    ) RETURNING id INTO v_change_id;

    RETURN v_change_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Search entities with fuzzy matching (from optimized schema)
CREATE OR REPLACE FUNCTION search_sunbiz_entities(
    search_term TEXT,
    search_type TEXT DEFAULT 'all',              -- 'all', 'entity', 'officer', 'fictitious'
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
        FROM sunbiz_corporations e
        WHERE e.entity_name % search_term
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
        JOIN sunbiz_corporations e ON o.entity_id = e.entity_id
        WHERE o.full_name % search_term
            AND similarity(o.full_name, search_term) >= similarity_threshold
        ORDER BY similarity_score DESC
        LIMIT 100;
    END IF;

    -- Fictitious name search
    IF search_type IN ('all', 'fictitious') THEN
        RETURN QUERY
        SELECT
            f.registration_id as entity_id,
            f.name as entity_name,
            'FICTITIOUS_NAME'::TEXT as match_type,
            similarity(f.name, search_term) as similarity_score,
            f.owner_name as officer_name,
            NULL::VARCHAR as officer_role
        FROM sunbiz_fictitious_names f
        WHERE f.name % search_term
            AND similarity(f.name, search_term) >= similarity_threshold
        ORDER BY similarity_score DESC
        LIMIT 100;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function: Find entities by address (from optimized schema)
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
    JOIN sunbiz_corporations e ON o.entity_id = e.entity_id
    WHERE
        (search_city IS NULL OR o.city ILIKE '%' || search_city || '%')
        AND o.state = search_state
        AND (o.street_address % search_address OR o.full_address % search_address)
    ORDER BY match_score DESC
    LIMIT 50;
END;
$$ LANGUAGE plpgsql;

-- Function: Get entity details with all related records
CREATE OR REPLACE FUNCTION get_entity_details(p_entity_id VARCHAR(50))
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'entity', (SELECT row_to_json(c) FROM sunbiz_corporations c WHERE c.entity_id = p_entity_id),
        'officers', (SELECT json_agg(o) FROM sunbiz_officers o WHERE o.entity_id = p_entity_id),
        'events', (SELECT json_agg(e) FROM sunbiz_events e WHERE e.entity_id = p_entity_id),
        'recent_changes', (
            SELECT json_agg(cl)
            FROM sunbiz_change_log cl
            WHERE cl.entity_id = p_entity_id
            ORDER BY cl.detected_at DESC
            LIMIT 20
        )
    ) INTO result;

    RETURN result;
END;
$$;

-- Function: Get unprocessed changes
CREATE OR REPLACE FUNCTION get_unprocessed_changes(
    p_change_type VARCHAR(50) DEFAULT NULL,
    p_limit INTEGER DEFAULT 1000
)
RETURNS TABLE (
    id UUID,
    entity_id VARCHAR(50),
    change_type VARCHAR(50),
    change_date DATE,
    old_value JSONB,
    new_value JSONB,
    detected_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cl.id,
        cl.entity_id,
        cl.change_type,
        cl.change_date,
        cl.old_value,
        cl.new_value,
        cl.detected_at
    FROM sunbiz_change_log cl
    WHERE cl.processed = FALSE
        AND (p_change_type IS NULL OR cl.change_type = p_change_type)
    ORDER BY cl.detected_at ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function: Mark changes as processed
CREATE OR REPLACE FUNCTION mark_changes_processed(p_change_ids UUID[])
RETURNS INTEGER AS $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE sunbiz_change_log
    SET processed = TRUE,
        processed_at = NOW()
    WHERE id = ANY(p_change_ids)
        AND processed = FALSE;

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update timestamps function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply timestamp triggers to all tables with updated_at
CREATE TRIGGER update_sunbiz_corporations_updated_at
    BEFORE UPDATE ON sunbiz_corporations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sunbiz_fictitious_names_updated_at
    BEFORE UPDATE ON sunbiz_fictitious_names
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sunbiz_registered_agents_updated_at
    BEFORE UPDATE ON sunbiz_registered_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sunbiz_officers_updated_at
    BEFORE UPDATE ON sunbiz_officers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE sunbiz_corporations ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_fictitious_names ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_registered_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_entity_search ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_officers ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_change_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_update_jobs ENABLE ROW LEVEL SECURITY;

-- Public read access for searching
CREATE POLICY "Public read access" ON sunbiz_corporations FOR SELECT USING (true);
CREATE POLICY "Public read access" ON sunbiz_fictitious_names FOR SELECT USING (true);
CREATE POLICY "Public read access" ON sunbiz_registered_agents FOR SELECT USING (true);
CREATE POLICY "Public read access" ON sunbiz_entity_search FOR SELECT USING (true);
CREATE POLICY "Public read access" ON sunbiz_officers FOR SELECT USING (true);
CREATE POLICY "Public read access" ON sunbiz_events FOR SELECT USING (true);

-- Admin/service role write access
CREATE POLICY "Service role all access" ON sunbiz_corporations FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service role all access" ON sunbiz_fictitious_names FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service role all access" ON sunbiz_registered_agents FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service role all access" ON sunbiz_entity_search FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service role all access" ON sunbiz_officers FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service role all access" ON sunbiz_events FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service role all access" ON sunbiz_change_log FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service role all access" ON sunbiz_update_jobs FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE sunbiz_corporations IS 'Main table for Florida corporate entities with full details and search optimization';
COMMENT ON TABLE sunbiz_fictitious_names IS 'DBA and fictitious name registrations in Florida';
COMMENT ON TABLE sunbiz_registered_agents IS 'Directory of registered agents serving Florida entities';
COMMENT ON TABLE sunbiz_entity_search IS 'Fast lookup table for entity searches across all Sunbiz data';
COMMENT ON TABLE sunbiz_officers IS 'Corporate officers, directors, and managers with fuzzy search capabilities';
COMMENT ON TABLE sunbiz_events IS 'Corporate events, filings, and amendments';
COMMENT ON TABLE sunbiz_change_log IS 'Daily change tracking for incremental updates - monitors status changes, address updates, officer changes, etc.';
COMMENT ON TABLE sunbiz_update_jobs IS 'Job monitoring for daily update processes - tracks success, failures, and performance metrics';

COMMENT ON FUNCTION get_sunbiz_update_stats IS 'Returns daily statistics for update jobs including success rate, record counts, and performance';
COMMENT ON FUNCTION log_sunbiz_change IS 'Logs a detected change to an entity for daily update tracking';
COMMENT ON FUNCTION search_sunbiz_entities IS 'Fuzzy search across entities, officers, and fictitious names with similarity scoring';
COMMENT ON FUNCTION find_sunbiz_by_address IS 'Find entities by address with fuzzy matching on street, city, and state';
COMMENT ON FUNCTION get_entity_details IS 'Returns complete entity details including officers, events, and recent changes';
COMMENT ON FUNCTION get_unprocessed_changes IS 'Returns unprocessed changes from the change log for batch processing';
COMMENT ON FUNCTION mark_changes_processed IS 'Marks a batch of changes as processed after successful application';

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Create initial update job to mark schema deployment
INSERT INTO sunbiz_update_jobs (
    job_type,
    status,
    started_at,
    completed_at,
    records_processed,
    notes
) VALUES (
    'SCHEMA_DEPLOYMENT',
    'COMPLETED',
    NOW(),
    NOW(),
    0,
    'Sunbiz daily update schema v1.0.0 deployed successfully'
);

-- ============================================================================
-- SCHEMA DEPLOYMENT COMPLETE
-- ============================================================================
--
-- Verification Steps:
--   1. SELECT COUNT(*) FROM sunbiz_update_jobs; -- Should return 1
--   2. SELECT get_sunbiz_update_stats(CURRENT_DATE); -- Should return schema deployment job
--   3. SELECT * FROM pg_indexes WHERE tablename LIKE 'sunbiz_%'; -- Verify indexes
--   4. \df search_sunbiz_entities -- Verify function exists
--
-- Next Steps:
--   1. Configure daily update worker to use sunbiz_update_jobs table
--   2. Import initial Sunbiz data using batch upload scripts
--   3. Set up daily monitoring of sunbiz_change_log for detected changes
--   4. Configure alerts for failed jobs in sunbiz_update_jobs
--
-- ============================================================================
