-- Florida Business Database Schema for Supabase
-- Optimized for business intelligence and contact management

-- Main business entities table
CREATE TABLE florida_entities (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(20) UNIQUE NOT NULL, -- Original Florida entity ID
    entity_type CHAR(1) NOT NULL, -- L=LLC, P=Corp, etc.
    business_name VARCHAR(255) NOT NULL,
    dba_name VARCHAR(255), -- Fictitious name if applicable
    entity_status VARCHAR(10) DEFAULT 'ACTIVE',
    
    -- Business address
    business_address_line1 VARCHAR(255),
    business_address_line2 VARCHAR(255), 
    business_city VARCHAR(100),
    business_state CHAR(2) DEFAULT 'FL',
    business_zip VARCHAR(10),
    business_county VARCHAR(50),
    
    -- Mailing address
    mailing_address_line1 VARCHAR(255),
    mailing_address_line2 VARCHAR(255),
    mailing_city VARCHAR(100),
    mailing_state CHAR(2),
    mailing_zip VARCHAR(10),
    
    -- Key dates
    formation_date DATE,
    registration_date DATE,
    last_update_date DATE,
    
    -- Data source tracking
    source_file VARCHAR(255),
    source_record_line INTEGER,
    processed_at TIMESTAMP DEFAULT NOW(),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Business contacts (phones, emails, principals)
CREATE TABLE florida_contacts (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(20) NOT NULL REFERENCES florida_entities(entity_id),
    
    -- Contact type: OFFICER, REGISTERED_AGENT, PRINCIPAL
    contact_type VARCHAR(20) NOT NULL,
    contact_role VARCHAR(50), -- CEO, President, Manager, etc.
    
    -- Person/Organization details
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    last_name VARCHAR(100),
    title VARCHAR(100),
    organization_name VARCHAR(255),
    
    -- Contact information
    phone VARCHAR(20),
    email VARCHAR(255),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state CHAR(2),
    zip_code VARCHAR(10),
    country CHAR(2) DEFAULT 'US',
    
    -- Metadata
    is_primary_contact BOOLEAN DEFAULT FALSE,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Registered agents (separate table for detailed tracking)
CREATE TABLE florida_registered_agents (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(20) NOT NULL REFERENCES florida_entities(entity_id),
    
    agent_name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(20), -- INDIVIDUAL, CORPORATION, LLC
    
    -- Agent address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state CHAR(2),
    zip_code VARCHAR(10),
    
    agent_phone VARCHAR(20),
    agent_email VARCHAR(255),
    
    effective_date DATE,
    termination_date DATE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Business activity/industry classification
CREATE TABLE florida_business_activities (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(20) NOT NULL REFERENCES florida_entities(entity_id),
    
    activity_description TEXT,
    naics_code VARCHAR(10),
    sic_code VARCHAR(10),
    industry_category VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- File tracking for processing status
CREATE TABLE florida_processing_log (
    id BIGSERIAL PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL UNIQUE,
    file_size BIGINT,
    records_processed INTEGER DEFAULT 0,
    records_successful INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    processing_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, FAILED
    error_details TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Raw records for full-text search and RAG
CREATE TABLE florida_raw_records (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(20) NOT NULL REFERENCES florida_entities(entity_id),
    raw_content TEXT NOT NULL,
    record_type VARCHAR(20), -- ENTITY, OFFICER, AMENDMENT, etc.
    file_source VARCHAR(255),
    embedding VECTOR(1536), -- For OpenAI embeddings
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_florida_entities_business_name ON florida_entities USING gin(to_tsvector('english', business_name));
CREATE INDEX idx_florida_entities_county ON florida_entities(business_county);
CREATE INDEX idx_florida_entities_entity_type ON florida_entities(entity_type);
CREATE INDEX idx_florida_entities_formation_date ON florida_entities(formation_date);

CREATE INDEX idx_florida_contacts_entity_id ON florida_contacts(entity_id);
CREATE INDEX idx_florida_contacts_phone ON florida_contacts(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_florida_contacts_email ON florida_contacts(email) WHERE email IS NOT NULL;
CREATE INDEX idx_florida_contacts_type_role ON florida_contacts(contact_type, contact_role);

CREATE INDEX idx_florida_registered_agents_entity_id ON florida_registered_agents(entity_id);
CREATE INDEX idx_florida_registered_agents_name ON florida_registered_agents USING gin(to_tsvector('english', agent_name));

-- Full-text search index for raw records
CREATE INDEX idx_florida_raw_records_content ON florida_raw_records USING gin(to_tsvector('english', raw_content));

-- Vector similarity index for RAG
CREATE INDEX idx_florida_raw_records_embedding ON florida_raw_records USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Row Level Security (RLS) policies
ALTER TABLE florida_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE florida_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE florida_registered_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE florida_business_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE florida_raw_records ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read all data
CREATE POLICY "Allow authenticated read access" ON florida_entities FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read access" ON florida_contacts FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read access" ON florida_registered_agents FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read access" ON florida_business_activities FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read access" ON florida_raw_records FOR SELECT TO authenticated USING (true);

-- Allow service role full access for data loading
CREATE POLICY "Allow service role full access" ON florida_entities FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role full access" ON florida_contacts FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role full access" ON florida_registered_agents FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role full access" ON florida_business_activities FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role full access" ON florida_raw_records FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role full access" ON florida_processing_log FOR ALL TO service_role USING (true);

-- Useful views for common queries
CREATE VIEW florida_active_entities_with_contacts AS
SELECT 
    e.entity_id,
    e.business_name,
    e.dba_name,
    e.business_city,
    e.business_county,
    e.entity_type,
    e.formation_date,
    STRING_AGG(DISTINCT c.phone, ', ') as phone_numbers,
    STRING_AGG(DISTINCT c.email, ', ') as email_addresses,
    COUNT(DISTINCT c.id) as contact_count
FROM florida_entities e
LEFT JOIN florida_contacts c ON e.entity_id = c.entity_id
WHERE e.entity_status = 'ACTIVE'
GROUP BY e.entity_id, e.business_name, e.dba_name, e.business_city, e.business_county, e.entity_type, e.formation_date;

CREATE VIEW florida_contact_summary AS
SELECT 
    business_county,
    entity_type,
    COUNT(*) as entity_count,
    COUNT(DISTINCT c.phone) as unique_phones,
    COUNT(DISTINCT c.email) as unique_emails
FROM florida_entities e
LEFT JOIN florida_contacts c ON e.entity_id = c.entity_id
WHERE e.entity_status = 'ACTIVE'
GROUP BY business_county, entity_type
ORDER BY entity_count DESC;