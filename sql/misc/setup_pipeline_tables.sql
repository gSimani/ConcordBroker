-- Create missing data pipeline tables for agents
-- These tables store the actual data collected by each agent

-- TPP (Tangible Personal Property) Accounts
CREATE TABLE IF NOT EXISTS fl_tpp_accounts (
    id BIGSERIAL PRIMARY KEY,
    account_number VARCHAR(100) NOT NULL,
    owner_name VARCHAR(255),
    business_name VARCHAR(255),
    
    -- Address information
    mailing_addr1 VARCHAR(255),
    mailing_addr2 VARCHAR(255),
    mailing_city VARCHAR(100),
    mailing_state VARCHAR(2),
    mailing_zip VARCHAR(10),
    
    -- Physical location
    physical_addr1 VARCHAR(255),
    physical_addr2 VARCHAR(255),
    physical_city VARCHAR(100),
    physical_state VARCHAR(2) DEFAULT 'FL',
    physical_zip VARCHAR(10),
    
    -- Property details
    property_type VARCHAR(50),
    property_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    
    -- Business details
    business_type VARCHAR(100),
    naics_code VARCHAR(10),
    employee_count INTEGER,
    
    -- Tax information
    tax_year INTEGER,
    tax_amount DECIMAL(10,2),
    tax_status VARCHAR(20),
    
    -- Metadata
    county VARCHAR(50),
    data_source VARCHAR(50),
    import_date TIMESTAMP DEFAULT NOW(),
    update_date TIMESTAMP,
    
    UNIQUE(account_number, tax_year, county)
);

-- NAV (Non-Ad Valorem) Assessments
CREATE TABLE IF NOT EXISTS fl_nav_parcel_summary (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50),
    tax_year INTEGER,
    
    -- Property identification
    owner_name VARCHAR(255),
    property_address VARCHAR(255),
    
    -- Assessment totals
    total_nav_amount DECIMAL(10,2),
    total_assessments INTEGER,
    
    -- Common assessment types
    cdd_amount DECIMAL(10,2),
    hoa_amount DECIMAL(10,2),
    special_district_amount DECIMAL(10,2),
    
    -- Status
    payment_status VARCHAR(20),
    delinquent_amount DECIMAL(10,2),
    
    -- Metadata
    import_date TIMESTAMP DEFAULT NOW(),
    update_date TIMESTAMP,
    
    UNIQUE(parcel_id, tax_year, county)
);

CREATE TABLE IF NOT EXISTS fl_nav_assessment_detail (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50),
    tax_year INTEGER,
    
    -- Assessment details
    assessment_type VARCHAR(100),
    assessment_description TEXT,
    levying_authority VARCHAR(255),
    
    -- Amounts
    assessment_amount DECIMAL(10,2),
    paid_amount DECIMAL(10,2),
    balance_due DECIMAL(10,2),
    
    -- Dates
    levy_date DATE,
    due_date DATE,
    paid_date DATE,
    
    -- Metadata
    import_date TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (parcel_id, tax_year, county) 
        REFERENCES fl_nav_parcel_summary(parcel_id, tax_year, county)
);

-- SDF (Sales Data File) Sales
CREATE TABLE IF NOT EXISTS fl_sdf_sales (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50),
    
    -- Sale information
    sale_date DATE,
    sale_price DECIMAL(15,2),
    sale_type VARCHAR(50),
    qualification_code VARCHAR(10),
    
    -- Parties
    grantor_name VARCHAR(255),
    grantee_name VARCHAR(255),
    
    -- Property at time of sale
    property_address VARCHAR(255),
    property_use_code VARCHAR(10),
    
    -- Valuation at time of sale
    just_value_at_sale DECIMAL(15,2),
    assessed_value_at_sale DECIMAL(15,2),
    
    -- Sale analysis
    price_per_sqft DECIMAL(10,2),
    sale_ratio DECIMAL(5,3), -- sale price / just value
    
    -- Flags
    is_qualified_sale BOOLEAN,
    is_arms_length BOOLEAN,
    is_foreclosure BOOLEAN,
    is_reo_sale BOOLEAN,
    is_short_sale BOOLEAN,
    
    -- Related entities
    is_corporate_buyer BOOLEAN,
    is_corporate_seller BOOLEAN,
    buyer_entity_type VARCHAR(50),
    seller_entity_type VARCHAR(50),
    
    -- Metadata
    or_book VARCHAR(20),
    or_page VARCHAR(20),
    instrument_number VARCHAR(30),
    import_date TIMESTAMP DEFAULT NOW(),
    update_date TIMESTAMP,
    
    UNIQUE(parcel_id, sale_date, instrument_number)
);

-- Data Updates Tracking
CREATE TABLE IF NOT EXISTS fl_data_updates (
    id BIGSERIAL PRIMARY KEY,
    source_type VARCHAR(50), -- TPP, NAV, SDF, SUNBIZ, etc.
    source_name VARCHAR(100),
    
    -- Update details
    update_date TIMESTAMP DEFAULT NOW(),
    records_processed INTEGER,
    records_added INTEGER,
    records_updated INTEGER,
    records_failed INTEGER,
    
    -- File information
    source_file VARCHAR(255),
    file_size BIGINT,
    file_hash VARCHAR(64),
    
    -- Processing details
    processing_time_seconds FLOAT,
    status VARCHAR(20),
    error_message TEXT,
    
    -- Metadata
    agent_name VARCHAR(100),
    agent_version VARCHAR(20)
);

-- Agent Status Tracking
CREATE TABLE IF NOT EXISTS fl_agent_status (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL UNIQUE,
    agent_type VARCHAR(50),
    
    -- Status
    is_enabled BOOLEAN DEFAULT TRUE,
    is_running BOOLEAN DEFAULT FALSE,
    current_status VARCHAR(50),
    
    -- Schedule
    schedule_type VARCHAR(20), -- daily, weekly, monthly
    schedule_time TIME,
    schedule_day INTEGER, -- day of week (1-7) or day of month (1-31)
    
    -- Last run information
    last_run_start TIMESTAMP,
    last_run_end TIMESTAMP,
    last_run_status VARCHAR(20),
    last_run_records INTEGER,
    last_error TEXT,
    
    -- Next run
    next_scheduled_run TIMESTAMP,
    
    -- Configuration
    config JSONB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tpp_owner ON fl_tpp_accounts(owner_name);
CREATE INDEX IF NOT EXISTS idx_tpp_business ON fl_tpp_accounts(business_name);
CREATE INDEX IF NOT EXISTS idx_tpp_county_year ON fl_tpp_accounts(county, tax_year);

CREATE INDEX IF NOT EXISTS idx_nav_parcel ON fl_nav_parcel_summary(parcel_id);
CREATE INDEX IF NOT EXISTS idx_nav_county_year ON fl_nav_parcel_summary(county, tax_year);
CREATE INDEX IF NOT EXISTS idx_nav_delinquent ON fl_nav_parcel_summary(delinquent_amount) WHERE delinquent_amount > 0;

CREATE INDEX IF NOT EXISTS idx_sdf_parcel ON fl_sdf_sales(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sdf_date ON fl_sdf_sales(sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_sdf_price ON fl_sdf_sales(sale_price);
CREATE INDEX IF NOT EXISTS idx_sdf_qualified ON fl_sdf_sales(is_qualified_sale) WHERE is_qualified_sale = TRUE;
CREATE INDEX IF NOT EXISTS idx_sdf_foreclosure ON fl_sdf_sales(is_foreclosure) WHERE is_foreclosure = TRUE;

CREATE INDEX IF NOT EXISTS idx_updates_source ON fl_data_updates(source_type, update_date DESC);
CREATE INDEX IF NOT EXISTS idx_agent_status_name ON fl_agent_status(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_next_run ON fl_agent_status(next_scheduled_run);

-- Initialize agent status records
INSERT INTO fl_agent_status (agent_name, agent_type, schedule_type, schedule_time, is_enabled)
VALUES 
    ('tpp_agent', 'property', 'weekly', '05:00', TRUE),
    ('nav_agent', 'assessment', 'weekly', '05:30', TRUE),
    ('sdf_agent', 'sales', 'daily', '06:00', TRUE),
    ('sunbiz_agent', 'business', 'daily', '02:00', TRUE),
    ('bcpa_agent', 'property', 'daily', '03:00', TRUE),
    ('official_records_agent', 'records', 'daily', '04:00', TRUE),
    ('dor_agent', 'tax', 'monthly', '01:00', TRUE)
ON CONFLICT (agent_name) 
DO UPDATE SET 
    is_enabled = EXCLUDED.is_enabled,
    updated_at = NOW();

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;