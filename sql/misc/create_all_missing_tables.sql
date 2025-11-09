-- COMPREHENSIVE SCHEMA CREATION FOR ALL MISSING TABLES
-- This script creates all tables needed for the 8 property tabs
-- Run this in Supabase SQL Editor to fix the "no data" issue

-- ============================================================
-- CORE PROPERTY INFO TABLES
-- ============================================================

-- Main properties table
CREATE TABLE IF NOT EXISTS properties (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL UNIQUE,
    owner_name VARCHAR(255),
    property_address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(2) DEFAULT 'FL',
    zip_code VARCHAR(10),
    property_type VARCHAR(50),
    year_built INTEGER,
    total_sqft FLOAT,
    lot_size_sqft FLOAT,
    bedrooms INTEGER,
    bathrooms FLOAT,
    assessed_value DECIMAL(15,2),
    market_value DECIMAL(15,2),
    last_sale_date DATE,
    last_sale_price DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Broward parcels table
CREATE TABLE IF NOT EXISTS broward_parcels (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    folio_number VARCHAR(50),
    legal_description TEXT,
    subdivision VARCHAR(255),
    plat_book VARCHAR(20),
    plat_page VARCHAR(20),
    section VARCHAR(10),
    township VARCHAR(10),
    range VARCHAR(10),
    municipality VARCHAR(100),
    neighborhood VARCHAR(100),
    land_use_code VARCHAR(20),
    zoning VARCHAR(50),
    future_land_use VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- NAV assessments table
CREATE TABLE IF NOT EXISTS nav_assessments (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    tax_year INTEGER NOT NULL,
    just_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    land_value DECIMAL(15,2),
    building_value DECIMAL(15,2),
    misc_value DECIMAL(15,2),
    exemptions DECIMAL(15,2),
    exemption_types TEXT,
    millage_rate DECIMAL(8,4),
    taxes_due DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parcel_id, tax_year)
);

-- TPP tangible property table
CREATE TABLE IF NOT EXISTS tpp_tangible (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    account_number VARCHAR(50) NOT NULL,
    business_name VARCHAR(255),
    owner_name VARCHAR(255),
    mailing_address VARCHAR(500),
    property_address VARCHAR(500),
    tangible_value DECIMAL(15,2),
    machinery_value DECIMAL(15,2),
    furniture_value DECIMAL(15,2),
    equipment_value DECIMAL(15,2),
    tax_year INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Property sales history
CREATE TABLE IF NOT EXISTS property_sales_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    sale_date DATE NOT NULL,
    sale_price DECIMAL(15,2),
    sale_type VARCHAR(50),
    buyer_name VARCHAR(255),
    seller_name VARCHAR(255),
    deed_type VARCHAR(50),
    instrument_number VARCHAR(50),
    qualified_sale BOOLEAN DEFAULT TRUE,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- PROPERTY TAX INFO TABLES
-- ============================================================

-- Property tax records
CREATE TABLE IF NOT EXISTS property_tax_records (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    tax_year INTEGER NOT NULL,
    tax_amount DECIMAL(15,2),
    amount_paid DECIMAL(15,2),
    amount_due DECIMAL(15,2),
    payment_status VARCHAR(50),
    due_date DATE,
    last_payment_date DATE,
    delinquent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parcel_id, tax_year)
);

-- Tax certificates
CREATE TABLE IF NOT EXISTS tax_certificates (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    certificate_number VARCHAR(50) UNIQUE,
    tax_year INTEGER,
    certificate_date DATE,
    face_amount DECIMAL(15,2),
    interest_rate DECIMAL(5,2),
    redemption_amount DECIMAL(15,2),
    holder_name VARCHAR(255),
    status VARCHAR(50),
    redeemed_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tax history
CREATE TABLE IF NOT EXISTS tax_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    tax_year INTEGER NOT NULL,
    millage_code VARCHAR(20),
    millage_rate DECIMAL(8,4),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    taxes_levied DECIMAL(15,2),
    taxes_paid DECIMAL(15,2),
    payment_date DATE,
    receipt_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Assessed values
CREATE TABLE IF NOT EXISTS assessed_values (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    assessment_year INTEGER NOT NULL,
    land_value DECIMAL(15,2),
    building_value DECIMAL(15,2),
    total_value DECIMAL(15,2),
    market_value DECIMAL(15,2),
    agricultural_value DECIMAL(15,2),
    classification VARCHAR(50),
    assessment_ratio DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parcel_id, assessment_year)
);

-- ============================================================
-- PERMIT TABLES
-- ============================================================

-- Florida permits main table
CREATE TABLE IF NOT EXISTS florida_permits (
    id BIGSERIAL PRIMARY KEY,
    permit_number VARCHAR(50) NOT NULL UNIQUE,
    parcel_id VARCHAR(50),
    property_address VARCHAR(500),
    permit_type VARCHAR(100),
    permit_subtype VARCHAR(100),
    description TEXT,
    estimated_value DECIMAL(15,2),
    contractor_name VARCHAR(255),
    contractor_license VARCHAR(50),
    owner_name VARCHAR(255),
    application_date DATE,
    issue_date DATE,
    finaled_date DATE,
    expire_date DATE,
    status VARCHAR(50),
    status_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Permit sub-permits
CREATE TABLE IF NOT EXISTS permit_sub_permits (
    id BIGSERIAL PRIMARY KEY,
    parent_permit_number VARCHAR(50) NOT NULL,
    sub_permit_number VARCHAR(50) NOT NULL,
    sub_permit_type VARCHAR(100),
    description TEXT,
    contractor VARCHAR(255),
    issue_date DATE,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (parent_permit_number) REFERENCES florida_permits(permit_number)
);

-- Permit inspections
CREATE TABLE IF NOT EXISTS permit_inspections (
    id BIGSERIAL PRIMARY KEY,
    permit_number VARCHAR(50) NOT NULL,
    inspection_type VARCHAR(100),
    inspection_date DATE,
    inspector_name VARCHAR(255),
    result VARCHAR(50),
    comments TEXT,
    reinspection_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- FORECLOSURE TABLES
-- ============================================================

-- Foreclosure cases
CREATE TABLE IF NOT EXISTS foreclosure_cases (
    id BIGSERIAL PRIMARY KEY,
    case_number VARCHAR(50) NOT NULL UNIQUE,
    parcel_id VARCHAR(50),
    property_address VARCHAR(500),
    plaintiff VARCHAR(255),
    defendant VARCHAR(255),
    filing_date DATE,
    case_type VARCHAR(100),
    case_status VARCHAR(50),
    judgment_amount DECIMAL(15,2),
    judgment_date DATE,
    auction_date DATE,
    auction_status VARCHAR(50),
    sale_amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Foreclosure history
CREATE TABLE IF NOT EXISTS foreclosure_history (
    id BIGSERIAL PRIMARY KEY,
    case_number VARCHAR(50) NOT NULL,
    event_date DATE,
    event_type VARCHAR(100),
    description TEXT,
    party_name VARCHAR(255),
    document_type VARCHAR(100),
    document_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Lis pendens
CREATE TABLE IF NOT EXISTS lis_pendens (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    case_number VARCHAR(50),
    recording_date DATE,
    recording_number VARCHAR(50),
    book VARCHAR(20),
    page VARCHAR(20),
    plaintiff VARCHAR(255),
    defendant VARCHAR(255),
    property_description TEXT,
    release_date DATE,
    release_recording VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SALES TAX DEED TABLES
-- ============================================================

-- Tax deed sales
CREATE TABLE IF NOT EXISTS tax_deed_sales (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    sale_number VARCHAR(50) UNIQUE,
    sale_date DATE,
    opening_bid DECIMAL(15,2),
    winning_bid DECIMAL(15,2),
    winner_name VARCHAR(255),
    certificate_number VARCHAR(50),
    tax_years VARCHAR(100),
    redemption_period_end DATE,
    deed_issued BOOLEAN DEFAULT FALSE,
    deed_issue_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tax deed auctions
CREATE TABLE IF NOT EXISTS tax_deed_auctions (
    id BIGSERIAL PRIMARY KEY,
    auction_number VARCHAR(50) UNIQUE,
    auction_date DATE,
    parcel_id VARCHAR(50),
    property_address VARCHAR(500),
    assessed_value DECIMAL(15,2),
    minimum_bid DECIMAL(15,2),
    deposit_required DECIMAL(15,2),
    auction_status VARCHAR(50),
    bidder_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tax deed history
CREATE TABLE IF NOT EXISTS tax_deed_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    event_date DATE,
    event_type VARCHAR(100),
    description TEXT,
    amount DECIMAL(15,2),
    party_involved VARCHAR(255),
    document_reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TAX LIEN TABLES
-- ============================================================

-- Tax liens
CREATE TABLE IF NOT EXISTS tax_liens (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    lien_number VARCHAR(50) UNIQUE,
    tax_year INTEGER,
    lien_date DATE,
    lien_amount DECIMAL(15,2),
    interest_rate DECIMAL(5,2),
    certificate_holder VARCHAR(255),
    redemption_amount DECIMAL(15,2),
    status VARCHAR(50),
    redemption_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tax lien sales
CREATE TABLE IF NOT EXISTS tax_lien_sales (
    id BIGSERIAL PRIMARY KEY,
    sale_number VARCHAR(50) UNIQUE,
    sale_date DATE,
    parcel_id VARCHAR(50),
    certificate_number VARCHAR(50),
    tax_amount DECIMAL(15,2),
    interest_rate DECIMAL(5,2),
    buyer_name VARCHAR(255),
    buyer_number VARCHAR(50),
    premium_paid DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ANALYSIS TABLES
-- ============================================================

-- Investment analysis
CREATE TABLE IF NOT EXISTS investment_analysis (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    analysis_date DATE DEFAULT CURRENT_DATE,
    investment_score INTEGER,
    roi_estimate DECIMAL(5,2),
    cap_rate DECIMAL(5,2),
    cash_flow_monthly DECIMAL(15,2),
    market_rent_estimate DECIMAL(15,2),
    renovation_cost_estimate DECIMAL(15,2),
    arv_estimate DECIMAL(15,2),
    neighborhood_grade VARCHAR(10),
    risk_level VARCHAR(20),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Market comparables
CREATE TABLE IF NOT EXISTS market_comparables (
    id BIGSERIAL PRIMARY KEY,
    subject_parcel_id VARCHAR(50),
    comp_parcel_id VARCHAR(50),
    comp_address VARCHAR(500),
    distance_miles DECIMAL(5,2),
    sale_date DATE,
    sale_price DECIMAL(15,2),
    price_per_sqft DECIMAL(10,2),
    sqft INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    year_built INTEGER,
    similarity_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Property metrics
CREATE TABLE IF NOT EXISTS property_metrics (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    metric_date DATE DEFAULT CURRENT_DATE,
    price_per_sqft DECIMAL(10,2),
    lot_coverage_ratio DECIMAL(5,2),
    improvement_ratio DECIMAL(5,2),
    tax_to_value_ratio DECIMAL(5,4),
    appreciation_rate_1yr DECIMAL(5,2),
    appreciation_rate_3yr DECIMAL(5,2),
    appreciation_rate_5yr DECIMAL(5,2),
    days_on_market_avg INTEGER,
    rental_yield DECIMAL(5,2),
    occupancy_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Core property indexes
CREATE INDEX IF NOT EXISTS idx_properties_parcel ON properties(parcel_id);
CREATE INDEX IF NOT EXISTS idx_properties_owner ON properties(owner_name);
CREATE INDEX IF NOT EXISTS idx_properties_address ON properties(property_address);

-- Tax related indexes
CREATE INDEX IF NOT EXISTS idx_tax_records_parcel ON property_tax_records(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_certs_parcel ON tax_certificates(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_history_parcel ON tax_history(parcel_id);

-- Permit indexes
CREATE INDEX IF NOT EXISTS idx_permits_parcel ON florida_permits(parcel_id);
CREATE INDEX IF NOT EXISTS idx_permits_number ON florida_permits(permit_number);
CREATE INDEX IF NOT EXISTS idx_permits_status ON florida_permits(status);

-- Foreclosure indexes
CREATE INDEX IF NOT EXISTS idx_foreclosure_parcel ON foreclosure_cases(parcel_id);
CREATE INDEX IF NOT EXISTS idx_foreclosure_case ON foreclosure_cases(case_number);

-- Sales and deed indexes
CREATE INDEX IF NOT EXISTS idx_sales_history_parcel ON property_sales_history(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_deed_parcel ON tax_deed_sales(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_lien_parcel ON tax_liens(parcel_id);

-- Analysis indexes
CREATE INDEX IF NOT EXISTS idx_analysis_parcel ON investment_analysis(parcel_id);
CREATE INDEX IF NOT EXISTS idx_comparables_subject ON market_comparables(subject_parcel_id);
CREATE INDEX IF NOT EXISTS idx_metrics_parcel ON property_metrics(parcel_id);

-- ============================================================
-- ENABLE ROW LEVEL SECURITY (Optional but recommended)
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE broward_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE nav_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpp_tangible ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_tax_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessed_values ENABLE ROW LEVEL SECURITY;
ALTER TABLE florida_permits ENABLE ROW LEVEL SECURITY;
ALTER TABLE permit_sub_permits ENABLE ROW LEVEL SECURITY;
ALTER TABLE permit_inspections ENABLE ROW LEVEL SECURITY;
ALTER TABLE foreclosure_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE foreclosure_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE lis_pendens ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_deed_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_deed_auctions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_deed_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_liens ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_lien_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE investment_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_comparables ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_metrics ENABLE ROW LEVEL SECURITY;

-- Create a policy for public read access (adjust as needed)
CREATE POLICY "Allow public read access" ON properties FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON broward_parcels FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON nav_assessments FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON tpp_tangible FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_sales_history FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_tax_records FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON tax_certificates FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON tax_history FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON assessed_values FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON florida_permits FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON permit_sub_permits FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON permit_inspections FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON foreclosure_cases FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON foreclosure_history FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON lis_pendens FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON tax_deed_sales FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON tax_deed_auctions FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON tax_deed_history FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON tax_liens FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON tax_lien_sales FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON investment_analysis FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON market_comparables FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_metrics FOR SELECT USING (true);

-- ============================================================
-- SUCCESS MESSAGE
-- ============================================================
-- All tables created successfully!
-- The property tabs should now be able to connect to these tables.
-- Next step: Load data into these tables using the data loading scripts.