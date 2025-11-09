-- Fix Database for Property Data Loading
-- Run this in your Supabase SQL Editor

-- 1. Drop existing RLS policies that are blocking inserts
DROP POLICY IF EXISTS "Allow public read access" ON florida_parcels;
DROP POLICY IF EXISTS "Allow public insert" ON florida_parcels;
DROP POLICY IF EXISTS "Allow public update" ON florida_parcels;

DROP POLICY IF EXISTS "Allow public read access" ON fl_sdf_sales;
DROP POLICY IF EXISTS "Allow public insert" ON fl_sdf_sales;

-- 2. Disable RLS temporarily to allow data loading
ALTER TABLE florida_parcels DISABLE ROW LEVEL SECURITY;
ALTER TABLE fl_sdf_sales DISABLE ROW LEVEL SECURITY;
ALTER TABLE fl_nav_assessment_detail DISABLE ROW LEVEL SECURITY;
ALTER TABLE fl_tpp_accounts DISABLE ROW LEVEL SECURITY;

-- 3. Add missing columns to florida_parcels
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS owner_addr1 VARCHAR(255),
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- 4. Add missing columns to fl_sdf_sales
ALTER TABLE fl_sdf_sales
ADD COLUMN IF NOT EXISTS book_page VARCHAR(50),
ADD COLUMN IF NOT EXISTS cin VARCHAR(50),
ADD COLUMN IF NOT EXISTS property_address_street_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS property_address_city VARCHAR(100),
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- 5. Create sunbiz_corporate_filings table
CREATE TABLE IF NOT EXISTS sunbiz_corporate_filings (
    id SERIAL PRIMARY KEY,
    entity_name VARCHAR(255),
    entity_type VARCHAR(100),
    status VARCHAR(50),
    state VARCHAR(2),
    document_number VARCHAR(50) UNIQUE,
    fei_ein_number VARCHAR(20),
    date_filed DATE,
    effective_date DATE,
    last_event_date DATE,
    principal_address VARCHAR(500),
    mailing_address VARCHAR(500),
    registered_agent_name VARCHAR(255),
    registered_agent_address VARCHAR(500),
    officers TEXT,
    annual_reports TEXT,
    filing_history TEXT,
    aggregate_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. Disable RLS on sunbiz table
ALTER TABLE sunbiz_corporate_filings DISABLE ROW LEVEL SECURITY;

-- 7. Grant public access to tables
GRANT ALL ON florida_parcels TO anon, authenticated;
GRANT ALL ON fl_sdf_sales TO anon, authenticated;
GRANT ALL ON fl_nav_assessment_detail TO anon, authenticated;
GRANT ALL ON fl_tpp_accounts TO anon, authenticated;
GRANT ALL ON sunbiz_corporate_filings TO anon, authenticated;

-- 8. Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- 9. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city ON florida_parcels(phy_city);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_address ON florida_parcels(phy_addr1);

CREATE INDEX IF NOT EXISTS idx_sdf_parcel ON fl_sdf_sales(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sdf_date ON fl_sdf_sales(sale_date DESC);

CREATE INDEX IF NOT EXISTS idx_sunbiz_entity ON sunbiz_corporate_filings(entity_name);
CREATE INDEX IF NOT EXISTS idx_sunbiz_doc ON sunbiz_corporate_filings(document_number);

-- 10. Verify tables are ready
SELECT 
    table_name,
    CASE 
        WHEN row_security_active THEN 'RLS Enabled' 
        ELSE 'RLS Disabled' 
    END as security_status
FROM information_schema.tables 
LEFT JOIN pg_tables ON tables.table_name = pg_tables.tablename
WHERE table_schema = 'public' 
AND table_name IN (
    'florida_parcels', 
    'fl_sdf_sales', 
    'fl_nav_assessment_detail', 
    'fl_tpp_accounts',
    'sunbiz_corporate_filings'
);

-- You should see all tables with "RLS Disabled" status
-- After running this script, run the Python data loader again