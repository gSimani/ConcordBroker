-- Create florida_permits table for storing permit data
CREATE TABLE IF NOT EXISTS florida_permits (
    id BIGSERIAL PRIMARY KEY,
    permit_number VARCHAR(100) NOT NULL,
    county_code VARCHAR(2),
    county_name VARCHAR(100) NOT NULL,
    municipality VARCHAR(100),
    jurisdiction_type VARCHAR(50),
    permit_type VARCHAR(100),
    description TEXT,
    status VARCHAR(50),
    applicant_name VARCHAR(255),
    contractor_name VARCHAR(255),
    contractor_license VARCHAR(50),
    property_address VARCHAR(500),
    parcel_id VARCHAR(100),
    folio_number VARCHAR(50),
    issue_date DATE,
    expiration_date DATE,
    final_date DATE,
    valuation DECIMAL(15,2),
    permit_fee DECIMAL(10,2),
    source_system VARCHAR(50),
    source_url TEXT,
    raw_data JSONB,
    scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_florida_permits_parcel ON florida_permits(parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_permits_address ON florida_permits(property_address);
CREATE INDEX IF NOT EXISTS idx_florida_permits_county ON florida_permits(county_code, municipality);
CREATE INDEX IF NOT EXISTS idx_florida_permits_number ON florida_permits(permit_number);
CREATE INDEX IF NOT EXISTS idx_florida_permits_status ON florida_permits(status);
CREATE INDEX IF NOT EXISTS idx_florida_permits_issue_date ON florida_permits(issue_date DESC);

-- Add RLS (Row Level Security) policies
ALTER TABLE florida_permits ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Allow public read access" ON florida_permits
    FOR SELECT USING (true);

-- Allow authenticated users to insert/update
CREATE POLICY "Allow authenticated insert" ON florida_permits
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow authenticated update" ON florida_permits
    FOR UPDATE USING (true);

-- Create sub-permits table for tracking related permits
CREATE TABLE IF NOT EXISTS permit_sub_permits (
    id BIGSERIAL PRIMARY KEY,
    parent_permit_id BIGINT REFERENCES florida_permits(id) ON DELETE CASCADE,
    sub_permit_number VARCHAR(100),
    sub_permit_type VARCHAR(100),
    status VARCHAR(50),
    permit_date DATE,
    fees DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create inspections table
CREATE TABLE IF NOT EXISTS permit_inspections (
    id BIGSERIAL PRIMARY KEY,
    permit_id BIGINT REFERENCES florida_permits(id) ON DELETE CASCADE,
    inspection_type VARCHAR(100),
    inspection_date DATE,
    inspection_status VARCHAR(50),
    inspector_name VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for related tables
CREATE INDEX IF NOT EXISTS idx_sub_permits_parent ON permit_sub_permits(parent_permit_id);
CREATE INDEX IF NOT EXISTS idx_inspections_permit ON permit_inspections(permit_id);

-- Enable RLS on related tables
ALTER TABLE permit_sub_permits ENABLE ROW LEVEL SECURITY;
ALTER TABLE permit_inspections ENABLE ROW LEVEL SECURITY;

-- Allow public read access on related tables
CREATE POLICY "Allow public read access" ON permit_sub_permits
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON permit_inspections
    FOR SELECT USING (true);

-- Create view for easier querying with all permit details
CREATE OR REPLACE VIEW permit_details AS
SELECT 
    p.*,
    COUNT(DISTINCT sp.id) as sub_permit_count,
    COUNT(DISTINCT i.id) as inspection_count,
    MAX(i.inspection_date) as last_inspection_date
FROM florida_permits p
LEFT JOIN permit_sub_permits sp ON p.id = sp.parent_permit_id
LEFT JOIN permit_inspections i ON p.id = i.permit_id
GROUP BY p.id;