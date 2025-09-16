-- Fix Remaining Database Tables for ConcordBroker
-- Skips tables that already exist

-- 1. Create view to fix broward_parcels reference issue (CRITICAL FIX)
CREATE OR REPLACE VIEW broward_parcels AS 
SELECT * FROM florida_parcels 
WHERE UPPER(county) = 'BROWARD';

-- 2. Create missing Properties table (CRITICAL - frontend needs this)
CREATE TABLE IF NOT EXISTS properties (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE,
    owner_name VARCHAR(255),
    property_address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2) DEFAULT 'FL',
    zip_code VARCHAR(10),
    property_type VARCHAR(50),
    year_built INTEGER,
    living_area INTEGER,
    lot_size INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    assessed_value DECIMAL(15,2),
    market_value DECIMAL(15,2),
    last_sale_date DATE,
    last_sale_price DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Create Property Sales History table
CREATE TABLE IF NOT EXISTS property_sales_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    sale_date DATE,
    sale_price DECIMAL(15,2),
    sale_type VARCHAR(100),
    buyer_name VARCHAR(255),
    seller_name VARCHAR(255),
    book_page VARCHAR(50),
    doc_stamps DECIMAL(15,2),
    qualified_sale VARCHAR(1),
    vacant_at_sale VARCHAR(1),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Create Sunbiz tables (CRITICAL - tab not working)
CREATE TABLE IF NOT EXISTS sunbiz_corporate (
    id BIGSERIAL PRIMARY KEY,
    corp_number VARCHAR(50) UNIQUE,
    corp_name VARCHAR(255),
    status VARCHAR(50),
    filing_type VARCHAR(100),
    file_date DATE,
    state VARCHAR(2),
    principal_addr VARCHAR(255),
    principal_city VARCHAR(100),
    principal_state VARCHAR(2),
    principal_zip VARCHAR(10),
    mailing_addr VARCHAR(255),
    mailing_city VARCHAR(100),
    mailing_state VARCHAR(2),
    mailing_zip VARCHAR(10),
    registered_agent_name VARCHAR(255),
    registered_agent_addr TEXT,
    parcel_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sunbiz_fictitious (
    id BIGSERIAL PRIMARY KEY,
    registration_number VARCHAR(50) UNIQUE,
    name VARCHAR(255),
    owner_name VARCHAR(255),
    owner_address TEXT,
    file_date DATE,
    status VARCHAR(50),
    expiration_date DATE,
    parcel_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sunbiz_corporate_events (
    id BIGSERIAL PRIMARY KEY,
    corp_number VARCHAR(50),
    event_date DATE,
    event_type VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Create TPP Tangible Property table
CREATE TABLE IF NOT EXISTS tpp_tangible (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    account_number VARCHAR(50),
    owner_name VARCHAR(255),
    business_name VARCHAR(255),
    business_address VARCHAR(255),
    just_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    tax_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Create Property Tax Records tables
CREATE TABLE IF NOT EXISTS property_tax_records (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    tax_year INTEGER NOT NULL,
    millage_rate DECIMAL(10,6),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    paid_amount DECIMAL(15,2),
    balance_due DECIMAL(15,2),
    payment_status VARCHAR(50),
    due_date DATE,
    paid_date DATE,
    delinquent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parcel_id, tax_year)
);

CREATE TABLE IF NOT EXISTS tax_certificates (
    id BIGSERIAL PRIMARY KEY,
    certificate_number VARCHAR(50) UNIQUE,
    parcel_id VARCHAR(50),
    tax_year INTEGER,
    face_value DECIMAL(15,2),
    interest_rate DECIMAL(5,2),
    certificate_status VARCHAR(50),
    sale_date DATE,
    buyer_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tax_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    tax_year INTEGER,
    tax_type VARCHAR(50),
    amount DECIMAL(15,2),
    status VARCHAR(50),
    transaction_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assessed_values (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    assessment_year INTEGER,
    land_value DECIMAL(15,2),
    building_value DECIMAL(15,2),
    total_value DECIMAL(15,2),
    just_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    exemptions DECIMAL(15,2),
    exemption_types TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parcel_id, assessment_year)
);

-- 7. Create Foreclosure tables
CREATE TABLE IF NOT EXISTS foreclosure_cases (
    id BIGSERIAL PRIMARY KEY,
    case_number VARCHAR(50) UNIQUE,
    parcel_id VARCHAR(50),
    property_address VARCHAR(255),
    filing_date DATE,
    case_status VARCHAR(50),
    plaintiff VARCHAR(255),
    defendant VARCHAR(255),
    auction_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS foreclosure_history (
    id BIGSERIAL PRIMARY KEY,
    case_number VARCHAR(50),
    parcel_id VARCHAR(50),
    event_date DATE,
    event_type VARCHAR(100),
    event_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lis_pendens (
    id BIGSERIAL PRIMARY KEY,
    document_number VARCHAR(50) UNIQUE,
    parcel_id VARCHAR(50),
    recording_date DATE,
    plaintiff VARCHAR(255),
    defendant VARCHAR(255),
    case_number VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 8. Create Tax Deed tables
CREATE TABLE IF NOT EXISTS tax_deed_sales (
    id BIGSERIAL PRIMARY KEY,
    sale_number VARCHAR(50) UNIQUE,
    parcel_id VARCHAR(50),
    sale_date DATE,
    minimum_bid DECIMAL(15,2),
    winning_bid DECIMAL(15,2),
    winner_name VARCHAR(255),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tax_deed_auctions (
    id BIGSERIAL PRIMARY KEY,
    auction_number VARCHAR(50),
    auction_date DATE,
    parcel_id VARCHAR(50),
    opening_bid DECIMAL(15,2),
    sold_amount DECIMAL(15,2),
    bidder_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tax_deed_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    event_date DATE,
    event_type VARCHAR(100),
    description TEXT,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 9. Create Tax Lien tables
CREATE TABLE IF NOT EXISTS tax_liens (
    id BIGSERIAL PRIMARY KEY,
    lien_number VARCHAR(50) UNIQUE,
    parcel_id VARCHAR(50),
    lien_date DATE,
    lien_amount DECIMAL(15,2),
    interest_rate DECIMAL(5,2),
    lien_holder VARCHAR(255),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tax_lien_sales (
    id BIGSERIAL PRIMARY KEY,
    sale_number VARCHAR(50),
    lien_number VARCHAR(50),
    parcel_id VARCHAR(50),
    sale_date DATE,
    sale_amount DECIMAL(15,2),
    buyer_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 10. Create Analysis tables
CREATE TABLE IF NOT EXISTS investment_analysis (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    analysis_date DATE,
    roi_percentage DECIMAL(5,2),
    cap_rate DECIMAL(5,2),
    cash_flow_monthly DECIMAL(15,2),
    market_value DECIMAL(15,2),
    rental_estimate DECIMAL(15,2),
    investment_score INTEGER,
    risk_level VARCHAR(20),
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_comparables (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    comp_parcel_id VARCHAR(50),
    comp_address VARCHAR(255),
    sale_date DATE,
    sale_price DECIMAL(15,2),
    price_per_sqft DECIMAL(10,2),
    distance_miles DECIMAL(5,2),
    similarity_score INTEGER,
    property_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS property_metrics (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    metric_date DATE,
    price_per_sqft DECIMAL(10,2),
    lot_size_acres DECIMAL(10,4),
    building_age INTEGER,
    effective_age INTEGER,
    condition_score INTEGER,
    location_score INTEGER,
    school_rating DECIMAL(3,1),
    crime_index INTEGER,
    walkability_score INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 11. Create Permit extension tables
CREATE TABLE IF NOT EXISTS permit_sub_permits (
    id BIGSERIAL PRIMARY KEY,
    parent_permit_number VARCHAR(50),
    sub_permit_number VARCHAR(50) UNIQUE,
    parcel_id VARCHAR(50),
    permit_type VARCHAR(100),
    description TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS permit_inspections (
    id BIGSERIAL PRIMARY KEY,
    permit_number VARCHAR(50),
    inspection_number VARCHAR(50),
    inspection_type VARCHAR(100),
    inspection_date DATE,
    inspector_name VARCHAR(255),
    result VARCHAR(50),
    comments TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 12. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_properties_parcel ON properties(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sales_history_parcel ON property_sales_history(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sunbiz_parcel ON sunbiz_corporate(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tpp_parcel ON tpp_tangible(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_records_parcel ON property_tax_records(parcel_id);
CREATE INDEX IF NOT EXISTS idx_investment_parcel ON investment_analysis(parcel_id);

-- 13. Enable RLS and create policies for new tables
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_corporate ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_fictitious ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_tax_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE investment_analysis ENABLE ROW LEVEL SECURITY;

-- Create public read policies
CREATE POLICY "public_read_properties" ON properties FOR SELECT USING (true);
CREATE POLICY "public_read_sales" ON property_sales_history FOR SELECT USING (true);
CREATE POLICY "public_read_sunbiz_corp" ON sunbiz_corporate FOR SELECT USING (true);
CREATE POLICY "public_read_sunbiz_fict" ON sunbiz_fictitious FOR SELECT USING (true);
CREATE POLICY "public_read_tax_records" ON property_tax_records FOR SELECT USING (true);
CREATE POLICY "public_read_investment" ON investment_analysis FOR SELECT USING (true);

-- 14. Insert sample data to get started
INSERT INTO properties (parcel_id, owner_name, property_address, city, state, zip_code, property_type, year_built, living_area, assessed_value, market_value)
VALUES 
    ('504231242720', 'RODRIGUEZ MARIA', '3920 SW 53 CT', 'DAVIE', 'FL', '33314', 'SINGLE FAMILY', 1995, 2150, 325000, 375000),
    ('064210010010', 'SUNRISE HOLDINGS GROUP', '4321 NW 88 AVE', 'SUNRISE', 'FL', '33351', 'COMMERCIAL', 2005, 5500, 525000, 575000),
    ('494210190120', 'SAMPLE PROPERTY LLC', '1234 SAMPLE ST', 'FORT LAUDERDALE', 'FL', '33301', 'SINGLE FAMILY', 2000, 1800, 285000, 320000)
ON CONFLICT (parcel_id) DO NOTHING;

INSERT INTO sunbiz_corporate (corp_number, corp_name, status, filing_type, file_date, state, principal_addr, principal_city, principal_state, principal_zip, registered_agent_name, parcel_id)
VALUES 
    ('P20000045678', 'FLORIDA INVESTMENT PROPERTIES LLC', 'ACTIVE', 'Florida Limited Liability', '2020-06-15', 'FL', '3920 SW 53 CT', 'DAVIE', 'FL', '33314', 'RODRIGUEZ MARIA', '504231242720'),
    ('L19000234567', 'SUNRISE HOLDINGS GROUP INC', 'ACTIVE', 'Florida Profit Corporation', '2019-03-20', 'FL', '4321 NW 88 AVE', 'SUNRISE', 'FL', '33351', 'CORPORATE AGENTS INC', '064210010010')
ON CONFLICT (corp_number) DO NOTHING;

INSERT INTO property_sales_history (parcel_id, sale_date, sale_price, sale_type, buyer_name, seller_name)
VALUES 
    ('504231242720', '2020-06-15', 320000, 'WARRANTY DEED', 'RODRIGUEZ MARIA', 'PREVIOUS OWNER LLC'),
    ('504231242720', '2015-03-20', 245000, 'WARRANTY DEED', 'PREVIOUS OWNER LLC', 'ORIGINAL OWNER'),
    ('064210010010', '2019-03-20', 500000, 'WARRANTY DEED', 'SUNRISE HOLDINGS GROUP', 'COMMERCIAL PROPERTIES INC')
ON CONFLICT DO NOTHING;

-- Success message
SELECT 'Database structure fixed successfully! All missing tables created.' as status;