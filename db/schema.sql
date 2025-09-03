-- ConcordBroker Database Schema
-- PostgreSQL/Supabase compatible
-- Version 0.1.0

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create schema
CREATE SCHEMA IF NOT EXISTS concordbroker;
SET search_path TO concordbroker, public;

-- ================================
-- Core Tables
-- ================================

-- Parcels table (main property records)
CREATE TABLE IF NOT EXISTS parcels (
    folio VARCHAR(20) PRIMARY KEY,
    county_code VARCHAR(3) NOT NULL DEFAULT '16', -- Broward
    city VARCHAR(50) NOT NULL,
    main_use VARCHAR(2) NOT NULL,
    sub_use VARCHAR(4),
    situs_addr TEXT,
    mailing_addr TEXT,
    owner_raw TEXT,
    owner_entity_id UUID,
    land_value DECIMAL(12,2),
    just_value DECIMAL(12,2),
    assessed_soh DECIMAL(12,2),
    taxable DECIMAL(12,2),
    living_area INTEGER,
    land_sf INTEGER,
    bldg_sf INTEGER,
    units INTEGER,
    beds INTEGER,
    baths INTEGER,
    eff_year INTEGER,
    act_year INTEGER,
    taxing_auth_code VARCHAR(10),
    last_roll_year INTEGER,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional fields for enhanced tracking
    zoning VARCHAR(20),
    lot_size INTEGER,
    property_type VARCHAR(50),
    score DECIMAL(5,2),
    score_updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    data_source VARCHAR(20),
    raw_data JSONB
);

-- Sales table (property sales history)
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(20) NOT NULL,
    sale_date DATE NOT NULL,
    price DECIMAL(12,2),
    sale_type VARCHAR(20),
    book_page VARCHAR(20),
    instrument_no VARCHAR(20),
    qualified_flag BOOLEAN DEFAULT false,
    multi_parcel_flag BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional fields
    deed_type VARCHAR(50),
    grantor_name TEXT,
    grantee_name TEXT,
    
    CONSTRAINT fk_sales_parcel FOREIGN KEY (folio) 
        REFERENCES parcels(folio) ON DELETE CASCADE
);

-- Recorded documents table
CREATE TABLE IF NOT EXISTS recorded_docs (
    instrument_no VARCHAR(20) PRIMARY KEY,
    doc_type VARCHAR(50),
    rec_datetime TIMESTAMP WITH TIME ZONE,
    consideration DECIMAL(12,2),
    first_parcel VARCHAR(20),
    legal_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    page_count INTEGER,
    party1_name TEXT,
    party2_name TEXT,
    doc_stamps DECIMAL(10,2),
    intangible_tax DECIMAL(10,2),
    
    -- Full text search
    search_vector tsvector
);

-- Document-parcel junction table
CREATE TABLE IF NOT EXISTS doc_parcels (
    instrument_no VARCHAR(20) NOT NULL,
    folio VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (instrument_no, folio),
    CONSTRAINT fk_doc_parcels_doc FOREIGN KEY (instrument_no) 
        REFERENCES recorded_docs(instrument_no) ON DELETE CASCADE,
    CONSTRAINT fk_doc_parcels_parcel FOREIGN KEY (folio) 
        REFERENCES parcels(folio) ON DELETE CASCADE
);

-- Entities table (corporate entities)
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    fei_ein VARCHAR(20),
    status VARCHAR(20),
    principal_addr TEXT,
    reg_agent_id UUID,
    created_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional fields
    entity_type VARCHAR(50),
    state_of_inc VARCHAR(2),
    mailing_addr TEXT,
    email VARCHAR(255),
    phone VARCHAR(20),
    website VARCHAR(255),
    
    -- Sunbiz specific
    document_number VARCHAR(20),
    filing_type VARCHAR(50),
    
    -- Search optimization
    name_tsv tsvector,
    UNIQUE(fei_ein)
);

-- Officers table
CREATE TABLE IF NOT EXISTS officers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL,
    name TEXT NOT NULL,
    title VARCHAR(50),
    addr TEXT,
    is_manager BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional contact info
    email VARCHAR(255),
    phone VARCHAR(20),
    
    CONSTRAINT fk_officers_entity FOREIGN KEY (entity_id) 
        REFERENCES entities(id) ON DELETE CASCADE
);

-- Parcel-entity links table
CREATE TABLE IF NOT EXISTS parcel_entity_links (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(20) NOT NULL,
    entity_id UUID NOT NULL,
    match_method VARCHAR(50),
    confidence DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Audit fields
    verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(folio, entity_id),
    CONSTRAINT fk_links_parcel FOREIGN KEY (folio) 
        REFERENCES parcels(folio) ON DELETE CASCADE,
    CONSTRAINT fk_links_entity FOREIGN KEY (entity_id) 
        REFERENCES entities(id) ON DELETE CASCADE
);

-- Jobs tracking table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP WITH TIME ZONE,
    ok BOOLEAN,
    rows INTEGER,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional tracking
    error_message TEXT,
    duration_seconds INTEGER,
    data_source VARCHAR(50),
    parameters JSONB,
    stats JSONB
);

-- ================================
-- Additional Tables for Enhanced Features
-- ================================

-- Users table (for authentication)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    name VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Preferences
    preferences JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}'
);

-- Saved searches table
CREATE TABLE IF NOT EXISTS saved_searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    criteria JSONB NOT NULL,
    alert_enabled BOOLEAN DEFAULT false,
    alert_frequency VARCHAR(20), -- daily, weekly, immediate
    last_alert_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_searches_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
);

-- Watchlist table
CREATE TABLE IF NOT EXISTS watchlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    folio VARCHAR(20) NOT NULL,
    notes TEXT,
    alert_on_change BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, folio),
    CONSTRAINT fk_watchlist_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_watchlist_parcel FOREIGN KEY (folio) 
        REFERENCES parcels(folio) ON DELETE CASCADE
);

-- RAG documents table (for knowledge base)
CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    doc_type VARCHAR(50),
    source_url TEXT,
    metadata JSONB,
    embedding vector(1536), -- OpenAI embeddings dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI agent tasks table
CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL,
    task_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    payload JSONB,
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- Indexes
-- ================================

-- Parcels indexes
CREATE INDEX idx_parcels_city ON parcels(city);
CREATE INDEX idx_parcels_main_use ON parcels(main_use);
CREATE INDEX idx_parcels_sub_use ON parcels(sub_use);
CREATE INDEX idx_parcels_owner_entity ON parcels(owner_entity_id);
CREATE INDEX idx_parcels_score ON parcels(score DESC) WHERE score IS NOT NULL;
CREATE INDEX idx_parcels_city_use ON parcels(city, main_use, sub_use);
CREATE INDEX idx_parcels_owner_raw_trgm ON parcels USING gin(owner_raw gin_trgm_ops);
CREATE INDEX idx_parcels_updated ON parcels(updated_at DESC);

-- Sales indexes
CREATE INDEX idx_sales_folio ON sales(folio);
CREATE INDEX idx_sales_date ON sales(sale_date DESC);
CREATE INDEX idx_sales_price ON sales(price) WHERE price > 0;
CREATE INDEX idx_sales_instrument ON sales(instrument_no);

-- Recorded docs indexes
CREATE INDEX idx_docs_datetime ON recorded_docs(rec_datetime DESC);
CREATE INDEX idx_docs_type ON recorded_docs(doc_type);
CREATE INDEX idx_docs_search ON recorded_docs USING gin(search_vector);
CREATE INDEX idx_docs_first_parcel ON recorded_docs(first_parcel);

-- Entities indexes
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_name_tsv ON entities USING gin(name_tsv);
CREATE INDEX idx_entities_status ON entities(status);
CREATE INDEX idx_entities_fei ON entities(fei_ein);

-- Officers indexes
CREATE INDEX idx_officers_entity ON officers(entity_id);
CREATE INDEX idx_officers_name ON officers(name);

-- Links indexes
CREATE INDEX idx_links_folio ON parcel_entity_links(folio);
CREATE INDEX idx_links_entity ON parcel_entity_links(entity_id);
CREATE INDEX idx_links_confidence ON parcel_entity_links(confidence DESC);

-- Jobs indexes
CREATE INDEX idx_jobs_type ON jobs(job_type);
CREATE INDEX idx_jobs_started ON jobs(started_at DESC);
CREATE INDEX idx_jobs_status ON jobs(ok, finished_at DESC);

-- RAG indexes
CREATE INDEX idx_rag_embedding ON rag_documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_rag_type ON rag_documents(doc_type);

-- Agent tasks indexes
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status, priority DESC, created_at);
CREATE INDEX idx_agent_tasks_type ON agent_tasks(agent_type, status);

-- ================================
-- Triggers
-- ================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to all tables with updated_at
CREATE TRIGGER update_parcels_updated_at BEFORE UPDATE ON parcels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sales_updated_at BEFORE UPDATE ON sales
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recorded_docs_updated_at BEFORE UPDATE ON recorded_docs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_updated_at BEFORE UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_officers_updated_at BEFORE UPDATE ON officers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Full text search trigger for recorded_docs
CREATE OR REPLACE FUNCTION update_docs_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.legal_summary, '') || ' ' || 
        COALESCE(NEW.party1_name, '') || ' ' || 
        COALESCE(NEW.party2_name, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_docs_search BEFORE INSERT OR UPDATE ON recorded_docs
    FOR EACH ROW EXECUTE FUNCTION update_docs_search_vector();

-- Full text search trigger for entities
CREATE OR REPLACE FUNCTION update_entities_name_tsv()
RETURNS TRIGGER AS $$
BEGIN
    NEW.name_tsv := to_tsvector('english', NEW.name);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_entities_search BEFORE INSERT OR UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_entities_name_tsv();

-- ================================
-- Views
-- ================================

-- Parcel summary view
CREATE OR REPLACE VIEW v_parcel_summary AS
SELECT 
    p.folio,
    p.city,
    p.main_use,
    p.sub_use,
    p.owner_raw,
    e.name as entity_name,
    p.just_value,
    p.taxable,
    p.score,
    MAX(s.sale_date) as last_sale_date,
    MAX(s.price) as last_sale_price,
    COUNT(DISTINCT s.id) as sale_count,
    p.updated_at
FROM parcels p
LEFT JOIN parcel_entity_links pel ON p.folio = pel.folio
LEFT JOIN entities e ON pel.entity_id = e.id
LEFT JOIN sales s ON p.folio = s.folio
GROUP BY 
    p.folio, p.city, p.main_use, p.sub_use, 
    p.owner_raw, e.name, p.just_value, 
    p.taxable, p.score, p.updated_at;

-- Recent activity view
CREATE OR REPLACE VIEW v_recent_activity AS
SELECT 
    'sale' as activity_type,
    folio,
    sale_date as activity_date,
    'Sale for $' || price as description
FROM sales
WHERE sale_date > CURRENT_DATE - INTERVAL '30 days'
UNION ALL
SELECT 
    'document' as activity_type,
    dp.folio,
    rd.rec_datetime as activity_date,
    rd.doc_type || ' recorded' as description
FROM recorded_docs rd
JOIN doc_parcels dp ON rd.instrument_no = dp.instrument_no
WHERE rd.rec_datetime > CURRENT_DATE - INTERVAL '30 days'
ORDER BY activity_date DESC;

-- ================================
-- Functions
-- ================================

-- Function to calculate property score
CREATE OR REPLACE FUNCTION calculate_property_score(p_folio VARCHAR)
RETURNS DECIMAL AS $$
DECLARE
    v_score DECIMAL := 50.0;
    v_parcel parcels%ROWTYPE;
    v_recent_sale_count INTEGER;
    v_price_deviation DECIMAL;
BEGIN
    -- Get parcel data
    SELECT * INTO v_parcel FROM parcels WHERE folio = p_folio;
    
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    
    -- Base score adjustments
    
    -- Use code scoring (higher for certain uses)
    CASE v_parcel.main_use
        WHEN '01' THEN v_score := v_score + 10; -- Single family
        WHEN '02' THEN v_score := v_score + 15; -- Mobile homes
        WHEN '03' THEN v_score := v_score + 20; -- Multi-family
        WHEN '04' THEN v_score := v_score + 25; -- Condos
        WHEN '48' THEN v_score := v_score + 30; -- Industrial
        ELSE v_score := v_score + 5;
    END CASE;
    
    -- Recent sales activity
    SELECT COUNT(*) INTO v_recent_sale_count 
    FROM sales 
    WHERE folio = p_folio 
    AND sale_date > CURRENT_DATE - INTERVAL '2 years';
    
    v_score := v_score + (v_recent_sale_count * 5);
    
    -- Value assessment ratio
    IF v_parcel.just_value > 0 AND v_parcel.assessed_soh > 0 THEN
        v_score := v_score + ((v_parcel.just_value - v_parcel.assessed_soh) / v_parcel.just_value * 20);
    END IF;
    
    -- Age factor (newer or very old can be opportunities)
    IF v_parcel.eff_year IS NOT NULL THEN
        IF v_parcel.eff_year < 1970 OR v_parcel.eff_year > 2020 THEN
            v_score := v_score + 10;
        END IF;
    END IF;
    
    -- Ensure score is between 0 and 100
    v_score := GREATEST(0, LEAST(100, v_score));
    
    -- Update the score in the table
    UPDATE parcels SET score = v_score, score_updated_at = CURRENT_TIMESTAMP
    WHERE folio = p_folio;
    
    RETURN v_score;
END;
$$ LANGUAGE plpgsql;

-- Function to match entity names
CREATE OR REPLACE FUNCTION match_entity_name(p_name1 TEXT, p_name2 TEXT)
RETURNS DECIMAL AS $$
DECLARE
    v_similarity DECIMAL;
    v_clean1 TEXT;
    v_clean2 TEXT;
BEGIN
    -- Clean and normalize names
    v_clean1 := UPPER(REGEXP_REPLACE(p_name1, '[^A-Z0-9 ]', '', 'g'));
    v_clean2 := UPPER(REGEXP_REPLACE(p_name2, '[^A-Z0-9 ]', '', 'g'));
    
    -- Remove common suffixes
    v_clean1 := REGEXP_REPLACE(v_clean1, '\s+(LLC|INC|CORP|CORPORATION|LP|LLP|PA|PC)$', '');
    v_clean2 := REGEXP_REPLACE(v_clean2, '\s+(LLC|INC|CORP|CORPORATION|LP|LLP|PA|PC)$', '');
    
    -- Calculate similarity
    v_similarity := similarity(v_clean1, v_clean2);
    
    RETURN v_similarity;
END;
$$ LANGUAGE plpgsql;

-- ================================
-- Comments
-- ================================

COMMENT ON SCHEMA concordbroker IS 'ConcordBroker real estate investment property acquisition system';
COMMENT ON TABLE parcels IS 'Core property parcel records from DOR assessment rolls';
COMMENT ON TABLE sales IS 'Property sales history from DOR and official records';
COMMENT ON TABLE recorded_docs IS 'Broward County official recorded documents';
COMMENT ON TABLE entities IS 'Corporate entities from Florida Sunbiz';
COMMENT ON TABLE officers IS 'Corporate officers and registered agents';
COMMENT ON TABLE parcel_entity_links IS 'Links between parcels and corporate entities';
COMMENT ON TABLE jobs IS 'ETL job tracking and monitoring';
COMMENT ON TABLE rag_documents IS 'Knowledge base documents with embeddings for RAG';
COMMENT ON TABLE agent_tasks IS 'AI agent task queue and results';

-- Grant schema usage to authenticated users (for Supabase)
GRANT USAGE ON SCHEMA concordbroker TO authenticated;
GRANT USAGE ON SCHEMA concordbroker TO service_role;