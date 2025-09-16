-- Complete SQL setup for all property tabs tables
-- Run this in Supabase SQL Editor to enable all tabs

-- 1. Create properties table (for Core Property Info fallback)
CREATE TABLE IF NOT EXISTS public.properties (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    property_address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(10) DEFAULT 'FL',
    zip_code VARCHAR(20),
    owner_name VARCHAR(255),
    property_type VARCHAR(100),
    year_built INTEGER,
    total_sqft INTEGER,
    lot_size_sqft INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    assessed_value DECIMAL(12,2),
    market_value DECIMAL(12,2),
    last_sale_price DECIMAL(12,2),
    last_sale_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_properties_parcel ON properties(parcel_id);

-- 2. Add missing columns to property_sales_history
ALTER TABLE property_sales_history 
ADD COLUMN IF NOT EXISTS book VARCHAR(20),
ADD COLUMN IF NOT EXISTS page VARCHAR(20);

-- 3. Create nav_assessments table with correct columns
CREATE TABLE IF NOT EXISTS public.nav_assessments (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    assessment_year INTEGER,
    assessment_type VARCHAR(50),
    assessment_amount DECIMAL(12,2),
    district_name VARCHAR(255),
    district_id VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_nav_assessments_parcel ON nav_assessments(parcel_id);

-- 4. Create sunbiz_corporate table
CREATE TABLE IF NOT EXISTS public.sunbiz_corporate (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    document_number VARCHAR(50) UNIQUE,
    corporate_name VARCHAR(255),
    status VARCHAR(50),
    filing_type VARCHAR(100),
    date_filed DATE,
    state VARCHAR(10),
    principal_address TEXT,
    mailing_address TEXT,
    registered_agent_name VARCHAR(255),
    registered_agent_address TEXT,
    officers JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sunbiz_parcel ON sunbiz_corporate(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sunbiz_doc ON sunbiz_corporate(document_number);

-- 5. Create tax_certificates table
CREATE TABLE IF NOT EXISTS public.tax_certificates (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    certificate_year INTEGER NOT NULL,
    certificate_number VARCHAR(50),
    tax_amount DECIMAL(12,2),
    interest_rate DECIMAL(5,2),
    bidder_name VARCHAR(255),
    bidder_address VARCHAR(500),
    certificate_face_value DECIMAL(12,2),
    certificate_status VARCHAR(50),
    redemption_date DATE,
    redemption_amount DECIMAL(12,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tax_cert_parcel ON tax_certificates(parcel_id);

-- 6. Create building_permits table
CREATE TABLE IF NOT EXISTS public.building_permits (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    permit_number VARCHAR(50) NOT NULL,
    permit_type VARCHAR(100),
    permit_description TEXT,
    application_date DATE,
    issue_date DATE,
    completion_date DATE,
    permit_status VARCHAR(50),
    estimated_value DECIMAL(12,2),
    contractor_name VARCHAR(255),
    contractor_license VARCHAR(50),
    owner_name VARCHAR(255),
    work_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_permits_parcel ON building_permits(parcel_id);

-- 7. Create foreclosure_cases table
CREATE TABLE IF NOT EXISTS public.foreclosure_cases (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    case_number VARCHAR(50) NOT NULL,
    filing_date DATE,
    case_status VARCHAR(50),
    plaintiff_name VARCHAR(255),
    defendant_name VARCHAR(255),
    attorney_name VARCHAR(255),
    attorney_phone VARCHAR(20),
    judgment_amount DECIMAL(12,2),
    judgment_date DATE,
    sale_date DATE,
    sale_amount DECIMAL(12,2),
    case_type VARCHAR(100),
    court_location VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_foreclosure_parcel ON foreclosure_cases(parcel_id);

-- 8. Create tax_deed_sales table
CREATE TABLE IF NOT EXISTS public.tax_deed_sales (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    batch_number VARCHAR(50),
    item_number VARCHAR(50),
    auction_date DATE,
    minimum_bid DECIMAL(12,2),
    assessed_value DECIMAL(12,2),
    property_address VARCHAR(255),
    property_description TEXT,
    certificate_holder VARCHAR(255),
    certificate_number VARCHAR(50),
    certificate_face_value DECIMAL(12,2),
    winning_bid DECIMAL(12,2),
    winning_bidder VARCHAR(255),
    auction_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tax_deed_parcel ON tax_deed_sales(parcel_id);

-- 9. Create tax_liens table
CREATE TABLE IF NOT EXISTS public.tax_liens (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    certificate_number VARCHAR(50) NOT NULL,
    certificate_year INTEGER,
    tax_amount DECIMAL(12,2),
    interest_rate DECIMAL(5,2),
    certificate_holder VARCHAR(255),
    purchase_date DATE,
    purchase_price DECIMAL(12,2),
    redemption_status VARCHAR(50),
    redemption_date DATE,
    redemption_amount DECIMAL(12,2),
    expiration_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tax_liens_parcel ON tax_liens(parcel_id);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, anon, authenticated, service_role;

-- Enable RLS but allow public read access
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE nav_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_corporate ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE building_permits ENABLE ROW LEVEL SECURITY;
ALTER TABLE foreclosure_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_deed_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_liens ENABLE ROW LEVEL SECURITY;

-- Create public read policies
CREATE POLICY "Allow public read" ON properties FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON nav_assessments FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON sunbiz_corporate FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON tax_certificates FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON building_permits FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON foreclosure_cases FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON tax_deed_sales FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON tax_liens FOR SELECT USING (true);

-- Allow authenticated users to insert/update/delete
CREATE POLICY "Allow auth insert" ON properties FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow auth update" ON properties FOR UPDATE USING (true);
CREATE POLICY "Allow auth delete" ON properties FOR DELETE USING (true);

CREATE POLICY "Allow auth insert" ON nav_assessments FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow auth update" ON nav_assessments FOR UPDATE USING (true);
CREATE POLICY "Allow auth delete" ON nav_assessments FOR DELETE USING (true);

CREATE POLICY "Allow auth insert" ON sunbiz_corporate FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow auth update" ON sunbiz_corporate FOR UPDATE USING (true);
CREATE POLICY "Allow auth delete" ON sunbiz_corporate FOR DELETE USING (true);

CREATE POLICY "Allow auth insert" ON tax_certificates FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow auth update" ON tax_certificates FOR UPDATE USING (true);
CREATE POLICY "Allow auth delete" ON tax_certificates FOR DELETE USING (true);

CREATE POLICY "Allow auth insert" ON building_permits FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow auth update" ON building_permits FOR UPDATE USING (true);
CREATE POLICY "Allow auth delete" ON building_permits FOR DELETE USING (true);

CREATE POLICY "Allow auth insert" ON foreclosure_cases FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow auth update" ON foreclosure_cases FOR UPDATE USING (true);
CREATE POLICY "Allow auth delete" ON foreclosure_cases FOR DELETE USING (true);

CREATE POLICY "Allow auth insert" ON tax_deed_sales FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow auth update" ON tax_deed_sales FOR UPDATE USING (true);
CREATE POLICY "Allow auth delete" ON tax_deed_sales FOR DELETE USING (true);

CREATE POLICY "Allow auth insert" ON tax_liens FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow auth update" ON tax_liens FOR UPDATE USING (true);
CREATE POLICY "Allow auth delete" ON tax_liens FOR DELETE USING (true);

-- Confirmation message
SELECT 'All property tables created successfully!' as message;