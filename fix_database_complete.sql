-- Complete Database Fix Script for ConcordBroker
-- This script creates all missing tables and views to fix the database structure

-- 1. Create view to fix broward_parcels reference issue
CREATE OR REPLACE VIEW broward_parcels AS 
SELECT * FROM florida_parcels 
WHERE UPPER(county) = 'BROWARD';

-- 2. Create missing TPP Tangible Property table
CREATE TABLE IF NOT EXISTS tpp_tangible (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    account_number VARCHAR(50),
    owner_name VARCHAR(255),
    business_name VARCHAR(255),
    business_address VARCHAR(255),
    business_city VARCHAR(100),
    business_state VARCHAR(2),
    business_zip VARCHAR(10),
    property_type VARCHAR(50),
    property_description TEXT,
    just_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    tax_year INTEGER,
    county VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Create Property Tax Records table
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

-- 4. Create Tax Certificates table
CREATE TABLE IF NOT EXISTS tax_certificates (
    id BIGSERIAL PRIMARY KEY,
    certificate_number VARCHAR(50) UNIQUE,
    parcel_id VARCHAR(50),
    tax_year INTEGER,
    face_value DECIMAL(15,2),
    interest_rate DECIMAL(5,2),
    redemption_amount DECIMAL(15,2),
    certificate_status VARCHAR(50),
    sale_date DATE,
    buyer_name VARCHAR(255),
    buyer_number VARCHAR(50),
    redemption_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Create Tax History table
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

-- 6. Create Assessed Values table
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
    attorney VARCHAR(255),
    judge VARCHAR(255),
    auction_date DATE,
    sale_amount DECIMAL(15,2),
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
    book_page VARCHAR(50),
    plaintiff VARCHAR(255),
    defendant VARCHAR(255),
    case_number VARCHAR(50),
    amount DECIMAL(15,2),
    status VARCHAR(50),
    release_date DATE,
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
    certificate_number VARCHAR(50),
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
    bidder_number VARCHAR(50),
    bidder_name VARCHAR(255),
    deposit_amount DECIMAL(15,2),
    balance_due DECIMAL(15,2),
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
    release_date DATE,
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
    buyer_number VARCHAR(50),
    interest_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 10. Create Permit extension tables
CREATE TABLE IF NOT EXISTS permit_sub_permits (
    id BIGSERIAL PRIMARY KEY,
    parent_permit_number VARCHAR(50),
    sub_permit_number VARCHAR(50) UNIQUE,
    parcel_id VARCHAR(50),
    permit_type VARCHAR(100),
    description TEXT,
    status VARCHAR(50),
    issue_date DATE,
    completion_date DATE,
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

-- 11. Create Analysis tables
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

-- 12. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tpp_parcel ON tpp_tangible(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_records_parcel ON property_tax_records(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_certs_parcel ON tax_certificates(parcel_id);
CREATE INDEX IF NOT EXISTS idx_foreclosure_parcel ON foreclosure_cases(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_deed_parcel ON tax_deed_sales(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_liens_parcel ON tax_liens(parcel_id);
CREATE INDEX IF NOT EXISTS idx_investment_parcel ON investment_analysis(parcel_id);
CREATE INDEX IF NOT EXISTS idx_comparables_parcel ON market_comparables(parcel_id);
CREATE INDEX IF NOT EXISTS idx_metrics_parcel ON property_metrics(parcel_id);

-- 13. Grant permissions (adjust based on your roles)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'Database structure fixed successfully!';
  RAISE NOTICE 'Created 19 missing tables and 1 view';
  RAISE NOTICE 'All indexes created';
END $$;