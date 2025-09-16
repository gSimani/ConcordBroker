-- Supabase Schema for Florida Sunbiz Data
-- Run this in your Supabase SQL Editor

-- Corporate Entities Table
CREATE TABLE IF NOT EXISTS sunbiz_corporate (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(12) NOT NULL,
    entity_name VARCHAR(200),
    status VARCHAR(10),
    filing_date DATE,
    state_country VARCHAR(50),
    
    -- Principal Address
    prin_addr1 VARCHAR(100),
    prin_addr2 VARCHAR(100),
    prin_city VARCHAR(50),
    prin_state VARCHAR(2),
    prin_zip VARCHAR(10),
    
    -- Mailing Address
    mail_addr1 VARCHAR(100),
    mail_addr2 VARCHAR(100),
    mail_city VARCHAR(50),
    mail_state VARCHAR(2),
    mail_zip VARCHAR(10),
    
    -- Additional Info
    ein VARCHAR(10),
    registered_agent VARCHAR(100),
    
    -- Metadata
    file_type VARCHAR(20),
    subtype VARCHAR(20),
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    update_date TIMESTAMP,
    
    -- Indexes
    UNIQUE(doc_number)
);

CREATE INDEX idx_corp_name ON sunbiz_corporate(entity_name);
CREATE INDEX idx_corp_status ON sunbiz_corporate(status);
CREATE INDEX idx_corp_date ON sunbiz_corporate(filing_date);
CREATE INDEX idx_corp_agent ON sunbiz_corporate(registered_agent);

-- Corporate Events Table
CREATE TABLE IF NOT EXISTS sunbiz_corporate_events (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(12) NOT NULL,
    event_date DATE,
    event_type VARCHAR(50),
    detail VARCHAR(200),
    
    -- Metadata
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (doc_number) REFERENCES sunbiz_corporate(doc_number)
);

CREATE INDEX idx_corp_event_doc ON sunbiz_corporate_events(doc_number);
CREATE INDEX idx_corp_event_date ON sunbiz_corporate_events(event_date);

-- Fictitious Names (DBA) Table
CREATE TABLE IF NOT EXISTS sunbiz_fictitious (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(12) NOT NULL,
    name VARCHAR(200),
    owner_name VARCHAR(200),
    
    -- Owner Address
    owner_addr1 VARCHAR(100),
    owner_addr2 VARCHAR(100),
    owner_city VARCHAR(50),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    
    -- Dates
    filed_date DATE,
    expires_date DATE,
    county VARCHAR(50),
    
    -- Metadata
    file_type VARCHAR(20),
    subtype VARCHAR(20),
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(doc_number)
);

CREATE INDEX idx_fic_name ON sunbiz_fictitious(name);
CREATE INDEX idx_fic_owner ON sunbiz_fictitious(owner_name);
CREATE INDEX idx_fic_county ON sunbiz_fictitious(county);
CREATE INDEX idx_fic_expires ON sunbiz_fictitious(expires_date);

-- Fictitious Name Events
CREATE TABLE IF NOT EXISTS sunbiz_fictitious_events (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(12) NOT NULL,
    event_date DATE,
    event_type VARCHAR(50),
    
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (doc_number) REFERENCES sunbiz_fictitious(doc_number)
);

-- Federal Tax Liens Table
CREATE TABLE IF NOT EXISTS sunbiz_liens (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(12) NOT NULL,
    lien_type VARCHAR(20),
    filed_date DATE,
    lapse_date DATE,
    amount DECIMAL(15,2),
    
    -- Metadata
    file_type VARCHAR(20),
    subtype VARCHAR(20),
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(doc_number)
);

CREATE INDEX idx_lien_type ON sunbiz_liens(lien_type);
CREATE INDEX idx_lien_amount ON sunbiz_liens(amount);
CREATE INDEX idx_lien_date ON sunbiz_liens(filed_date);

-- Lien Debtors Table
CREATE TABLE IF NOT EXISTS sunbiz_lien_debtors (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(12) NOT NULL,
    debtor_name VARCHAR(200),
    debtor_addr VARCHAR(200),
    
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (doc_number) REFERENCES sunbiz_liens(doc_number)
);

CREATE INDEX idx_debtor_name ON sunbiz_lien_debtors(debtor_name);

-- Lien Secured Parties Table
CREATE TABLE IF NOT EXISTS sunbiz_lien_secured_parties (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(12) NOT NULL,
    party_name VARCHAR(200),
    party_addr VARCHAR(200),
    
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (doc_number) REFERENCES sunbiz_liens(doc_number)
);

-- General Partnerships Table
CREATE TABLE IF NOT EXISTS sunbiz_partnerships (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(12) NOT NULL,
    name VARCHAR(200),
    status VARCHAR(10),
    filed_date DATE,
    
    -- Address
    prin_addr1 VARCHAR(100),
    prin_city VARCHAR(50),
    prin_state VARCHAR(2),
    prin_zip VARCHAR(10),
    
    -- Metadata
    file_type VARCHAR(20),
    subtype VARCHAR(20),
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(doc_number)
);

CREATE INDEX idx_partner_name ON sunbiz_partnerships(name);
CREATE INDEX idx_partner_status ON sunbiz_partnerships(status);

-- Partnership Events
CREATE TABLE IF NOT EXISTS sunbiz_partnership_events (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(12) NOT NULL,
    event_date DATE,
    event_type VARCHAR(50),
    
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (doc_number) REFERENCES sunbiz_partnerships(doc_number)
);

-- Marks (Trademarks/Service Marks) Table
CREATE TABLE IF NOT EXISTS sunbiz_marks (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(12) NOT NULL,
    mark_text VARCHAR(200),
    mark_type VARCHAR(20),
    status VARCHAR(10),
    
    -- Dates
    filed_date DATE,
    registration_date DATE,
    expiration_date DATE,
    
    -- Owner
    owner_name VARCHAR(200),
    owner_addr VARCHAR(200),
    
    -- Metadata
    file_type VARCHAR(20),
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(doc_number)
);

CREATE INDEX idx_mark_text ON sunbiz_marks(mark_text);
CREATE INDEX idx_mark_owner ON sunbiz_marks(owner_name);
CREATE INDEX idx_mark_expires ON sunbiz_marks(expiration_date);

-- Import Log Table
CREATE TABLE IF NOT EXISTS sunbiz_import_log (
    id BIGSERIAL PRIMARY KEY,
    file_type VARCHAR(20),
    source_file VARCHAR(100),
    records_imported INTEGER,
    import_date TIMESTAMP DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

CREATE INDEX idx_import_date ON sunbiz_import_log(import_date);
CREATE INDEX idx_import_type ON sunbiz_import_log(file_type);

-- Monitoring Agents Table
CREATE TABLE IF NOT EXISTS sunbiz_monitoring_agents (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL UNIQUE,
    agent_type VARCHAR(50),
    last_check TIMESTAMP,
    next_check TIMESTAMP,
    files_found INTEGER DEFAULT 0,
    files_processed INTEGER DEFAULT 0,
    last_error TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent Notifications Table
CREATE TABLE IF NOT EXISTS agent_notifications (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(100),
    message TEXT,
    is_error BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Processed Files Tracking
CREATE TABLE IF NOT EXISTS sunbiz_processed_files (
    id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(100) UNIQUE,
    file_hash VARCHAR(64),
    file_size BIGINT,
    processed_date TIMESTAMP DEFAULT NOW(),
    records_count INTEGER,
    processing_time_seconds FLOAT
);

-- Enable Row Level Security
ALTER TABLE sunbiz_corporate ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_fictitious ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_liens ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_partnerships ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_marks ENABLE ROW LEVEL SECURITY;

-- RLS Policies - Public read access
CREATE POLICY "Public read corporate" ON sunbiz_corporate
    FOR SELECT USING (true);

CREATE POLICY "Public read fictitious" ON sunbiz_fictitious
    FOR SELECT USING (true);

CREATE POLICY "Public read liens" ON sunbiz_liens
    FOR SELECT USING (true);

CREATE POLICY "Public read partnerships" ON sunbiz_partnerships
    FOR SELECT USING (true);

CREATE POLICY "Public read marks" ON sunbiz_marks
    FOR SELECT USING (true);

-- Admin write access
CREATE POLICY "Admin write corporate" ON sunbiz_corporate
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Admin write fictitious" ON sunbiz_fictitious
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

-- Create useful views

-- Active Corporations View
CREATE OR REPLACE VIEW active_corporations AS
SELECT 
    c.*,
    COUNT(e.id) as event_count,
    MAX(e.event_date) as last_event_date
FROM sunbiz_corporate c
LEFT JOIN sunbiz_corporate_events e ON c.doc_number = e.doc_number
WHERE c.status = 'ACTIVE'
GROUP BY c.id;

-- Recent Filings View
CREATE OR REPLACE VIEW recent_filings AS
SELECT 
    'Corporate' as entity_type,
    doc_number,
    entity_name as name,
    filing_date,
    status
FROM sunbiz_corporate
WHERE filing_date >= CURRENT_DATE - INTERVAL '30 days'
UNION ALL
SELECT 
    'Fictitious' as entity_type,
    doc_number,
    name,
    filed_date as filing_date,
    'ACTIVE' as status
FROM sunbiz_fictitious
WHERE filed_date >= CURRENT_DATE - INTERVAL '30 days'
UNION ALL
SELECT 
    'Partnership' as entity_type,
    doc_number,
    name,
    filed_date as filing_date,
    status
FROM sunbiz_partnerships
WHERE filed_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY filing_date DESC;

-- Search All Entities View
CREATE OR REPLACE VIEW all_entities AS
SELECT 
    'Corporate' as entity_type,
    doc_number,
    entity_name as name,
    prin_city as city,
    prin_state as state,
    status,
    filing_date
FROM sunbiz_corporate
UNION ALL
SELECT 
    'Fictitious' as entity_type,
    doc_number,
    name,
    owner_city as city,
    owner_state as state,
    'ACTIVE' as status,
    filed_date as filing_date
FROM sunbiz_fictitious
UNION ALL
SELECT 
    'Partnership' as entity_type,
    doc_number,
    name,
    prin_city as city,
    prin_state as state,
    status,
    filed_date as filing_date
FROM sunbiz_partnerships;

-- Import Statistics View
CREATE OR REPLACE VIEW import_statistics AS
SELECT 
    DATE(import_date) as import_day,
    file_type,
    COUNT(*) as files_processed,
    SUM(records_imported) as total_records,
    AVG(records_imported) as avg_records_per_file,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_imports,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_imports
FROM sunbiz_import_log
GROUP BY DATE(import_date), file_type
ORDER BY import_day DESC;

-- Functions for data management

-- Function to search entities across all tables
CREATE OR REPLACE FUNCTION search_sunbiz_entities(
    search_term TEXT,
    entity_type TEXT DEFAULT NULL
)
RETURNS TABLE(
    entity_type TEXT,
    doc_number VARCHAR,
    name TEXT,
    city TEXT,
    state TEXT,
    status TEXT,
    filing_date DATE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM all_entities
    WHERE 
        (name ILIKE '%' || search_term || '%' OR 
         doc_number = search_term)
        AND (entity_type IS NULL OR entity_type = $2)
    LIMIT 100;
END;
$$;

-- Function to get entity details with all related records
CREATE OR REPLACE FUNCTION get_entity_details(p_doc_number VARCHAR)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'corporate', (SELECT row_to_json(c) FROM sunbiz_corporate c WHERE c.doc_number = p_doc_number),
        'events', (SELECT json_agg(e) FROM sunbiz_corporate_events e WHERE e.doc_number = p_doc_number),
        'fictitious', (SELECT row_to_json(f) FROM sunbiz_fictitious f WHERE f.doc_number = p_doc_number),
        'liens', (SELECT row_to_json(l) FROM sunbiz_liens l WHERE l.doc_number = p_doc_number),
        'partnerships', (SELECT row_to_json(p) FROM sunbiz_partnerships p WHERE p.doc_number = p_doc_number),
        'marks', (SELECT row_to_json(m) FROM sunbiz_marks m WHERE m.doc_number = p_doc_number)
    ) INTO result;
    
    RETURN result;
END;
$$;

-- Insert initial monitoring agent
INSERT INTO sunbiz_monitoring_agents (
    agent_name, 
    agent_type, 
    enabled
)
VALUES (
    'Sunbiz_Daily_Monitor',
    'daily_check',
    true
), (
    'Sunbiz_Quarterly_Monitor',
    'quarterly_download',
    true
)
ON CONFLICT (agent_name) DO NOTHING;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;