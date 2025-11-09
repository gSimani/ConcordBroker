-- Broward County Daily Index Extract Tables
-- Create tables to store daily index records

-- Main records table for all daily index entries
CREATE TABLE IF NOT EXISTS broward_daily_records (
    id BIGSERIAL PRIMARY KEY,
    
    -- Document Information
    doc_type VARCHAR(50),
    doc_number VARCHAR(100) UNIQUE,
    book VARCHAR(20),
    page VARCHAR(20),
    recorded_date DATE,
    
    -- Party Information
    grantor TEXT,
    grantee TEXT,
    
    -- Property Information
    parcel_id VARCHAR(50),
    legal_desc TEXT,
    address TEXT,
    
    -- Transaction Information
    consideration DECIMAL(15,2),
    doc_stamps DECIMAL(10,2),
    record_type VARCHAR(100),
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'broward_daily_index',
    file_date DATE,
    file_name VARCHAR(255),
    parsed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_daily_parcel (parcel_id),
    INDEX idx_daily_date (recorded_date),
    INDEX idx_daily_type (doc_type),
    INDEX idx_daily_grantor (grantor),
    INDEX idx_daily_grantee (grantee)
);

-- Metadata table for tracking downloads and processing
CREATE TABLE IF NOT EXISTS broward_daily_metadata (
    id BIGSERIAL PRIMARY KEY,
    file_name VARCHAR(255) UNIQUE,
    file_date DATE,
    file_url TEXT,
    file_size BIGINT,
    download_date TIMESTAMP,
    parse_date TIMESTAMP,
    records_count INTEGER,
    status VARCHAR(50), -- downloaded, parsing, completed, failed
    error_message TEXT,
    checksum VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Properties table for linking daily records to properties
CREATE TABLE IF NOT EXISTS broward_daily_properties (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE,
    
    -- Latest transaction info
    latest_deed_date DATE,
    latest_deed_type VARCHAR(50),
    latest_sale_price DECIMAL(15,2),
    latest_mortgage_date DATE,
    latest_mortgage_amount DECIMAL(15,2),
    
    -- Counts
    total_transactions INTEGER DEFAULT 0,
    deed_count INTEGER DEFAULT 0,
    mortgage_count INTEGER DEFAULT 0,
    lien_count INTEGER DEFAULT 0,
    
    -- Parties
    current_owner TEXT,
    previous_owners JSONB, -- Array of previous owners
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_broward_daily_records_updated_at 
    BEFORE UPDATE ON broward_daily_records 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_broward_daily_properties_updated_at 
    BEFORE UPDATE ON broward_daily_properties 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON broward_daily_records TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON broward_daily_metadata TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON broward_daily_properties TO anon, authenticated;

-- Create RLS policies
ALTER TABLE broward_daily_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE broward_daily_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE broward_daily_properties ENABLE ROW LEVEL SECURITY;

-- Allow read access to all
CREATE POLICY "Allow read access to daily records" ON broward_daily_records
    FOR SELECT USING (true);

CREATE POLICY "Allow read access to daily metadata" ON broward_daily_metadata
    FOR SELECT USING (true);

CREATE POLICY "Allow read access to daily properties" ON broward_daily_properties
    FOR SELECT USING (true);

-- Allow insert/update for authenticated users
CREATE POLICY "Allow insert for authenticated users" ON broward_daily_records
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow update for authenticated users" ON broward_daily_records
    FOR UPDATE USING (true);

CREATE POLICY "Allow insert for authenticated metadata" ON broward_daily_metadata
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow insert for authenticated properties" ON broward_daily_properties
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow update for authenticated properties" ON broward_daily_properties
    FOR UPDATE USING (true);