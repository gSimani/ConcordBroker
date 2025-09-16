-- ConcordBroker Complete Database Initialization Script
-- Run this entire script in Supabase SQL Editor
-- This creates all tables with exact names and fields expected by the UI

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- ============================================================================
-- CORE PROPERTY TABLES
-- ============================================================================

-- 1. Main Florida Parcels Table (Primary data source for UI)
CREATE TABLE IF NOT EXISTS florida_parcels (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Physical Address (UI expects these exact field names)
    phy_addr1 TEXT,
    phy_city VARCHAR(100),
    phy_state VARCHAR(2) DEFAULT 'FL',
    phy_zipcd VARCHAR(10),
    
    -- Owner Information
    owner_name TEXT,
    owner_addr1 TEXT,
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    
    -- Values (UI expects these exact names)
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    just_value DECIMAL(15,2),
    market_value DECIMAL(15,2),
    land_value DECIMAL(15,2),
    building_value DECIMAL(15,2),
    improvement_value DECIMAL(15,2),
    
    -- Building Details
    year_built INTEGER,
    eff_year_built INTEGER,
    total_living_area INTEGER,
    living_area INTEGER,
    heated_area INTEGER,
    land_sqft DECIMAL(12,2),
    lot_size DECIMAL(12,2),
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    units INTEGER,
    total_units INTEGER,
    
    -- Property Classification
    property_use VARCHAR(20),
    usage_code VARCHAR(20),
    use_code VARCHAR(20),
    property_use_desc TEXT,
    property_type VARCHAR(100),
    use_description TEXT,
    
    -- Tax Information
    tax_amount DECIMAL(15,2),
    homestead_exemption VARCHAR(1),
    homestead VARCHAR(1),
    other_exemptions TEXT,
    exemption_codes TEXT,
    
    -- Sale Information
    sale_price DECIMAL(15,2),
    sale_date DATE,
    sale_type VARCHAR(50),
    deed_type VARCHAR(50),
    or_book VARCHAR(20),
    or_page VARCHAR(20),
    book_page VARCHAR(50),
    recording_book_page VARCHAR(50),
    cin VARCHAR(50),
    clerk_instrument_number VARCHAR(50),
    
    -- Additional Fields
    sketch_url TEXT,
    record_link TEXT,
    vi_code VARCHAR(10),
    is_distressed BOOLEAN DEFAULT FALSE,
    is_bank_sale BOOLEAN DEFAULT FALSE,
    land_factors JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Properties Table (Fallback for UI)
CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    property_address TEXT,
    city VARCHAR(100),
    state VARCHAR(2) DEFAULT 'FL',
    zip_code VARCHAR(10),
    owner_name TEXT,
    
    -- Values
    assessed_value DECIMAL(15,2),
    market_value DECIMAL(15,2),
    
    -- Building Info
    year_built INTEGER,
    total_sqft INTEGER,
    lot_size_sqft DECIMAL(12,2),
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    property_type VARCHAR(100),
    
    -- Sale Info
    last_sale_price DECIMAL(15,2),
    last_sale_date DATE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Property Sales History
CREATE TABLE IF NOT EXISTS property_sales_history (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    sale_date DATE,
    sale_price VARCHAR(20), -- UI expects string
    sale_type VARCHAR(100),
    qualified_sale BOOLEAN DEFAULT TRUE,
    is_distressed BOOLEAN DEFAULT FALSE,
    is_bank_sale BOOLEAN DEFAULT FALSE,
    is_cash_sale BOOLEAN DEFAULT FALSE,
    book VARCHAR(20),
    page VARCHAR(20),
    document_type VARCHAR(100),
    grantor_name TEXT,
    grantee_name TEXT,
    vi_code VARCHAR(10),
    sale_reason TEXT,
    book_page VARCHAR(50),
    cin VARCHAR(50),
    record_link TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TAX AND ASSESSMENT TABLES
-- ============================================================================

-- 4. NAV Assessments
CREATE TABLE IF NOT EXISTS nav_assessments (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    assessment_year INTEGER,
    district_name VARCHAR(200),
    assessment_type VARCHAR(100),
    total_assessment DECIMAL(15,2),
    unit_amount DECIMAL(15,2),
    units INTEGER,
    description TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Property Tax Info
CREATE TABLE IF NOT EXISTS property_tax_info (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    tax_year INTEGER,
    millage_rate DECIMAL(8,4),
    taxable_value DECIMAL(15,2),
    exemptions DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    paid_amount DECIMAL(15,2),
    payment_status VARCHAR(20),
    due_date DATE,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- BUSINESS ENTITY TABLES
-- ============================================================================

-- 6. Sunbiz Corporate Data
CREATE TABLE IF NOT EXISTS sunbiz_corporate (
    id SERIAL PRIMARY KEY,
    corporate_name TEXT,
    entity_type VARCHAR(100),
    status VARCHAR(50),
    filing_date DATE,
    principal_address TEXT,
    mailing_address TEXT,
    registered_agent TEXT,
    officers TEXT, -- UI searches within this field
    document_number VARCHAR(50),
    fei_number VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 7. Property-Entity Relationships
CREATE TABLE IF NOT EXISTS property_entities (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    entity_id INTEGER,
    relationship_type VARCHAR(50),
    confidence_score DECIMAL(3,2),
    match_details JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- USER TRACKING TABLES
-- ============================================================================

-- 8. Tracked Properties
CREATE TABLE IF NOT EXISTS tracked_properties (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    parcel_id VARCHAR(50),
    tracking_type VARCHAR(50),
    alert_preferences JSONB,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 9. User Alerts
CREATE TABLE IF NOT EXISTS user_alerts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    alert_type VARCHAR(50),
    message TEXT,
    property_id VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- 10. Property Searches
CREATE TABLE IF NOT EXISTS property_searches (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    search_criteria JSONB,
    search_results INTEGER,
    search_timestamp TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- SUPPLEMENTARY TABLES
-- ============================================================================

-- 11. Building Permits
CREATE TABLE IF NOT EXISTS building_permits (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    permit_number VARCHAR(50),
    permit_type VARCHAR(100),
    description TEXT,
    issue_date DATE,
    completion_date DATE,
    status VARCHAR(50),
    contractor_name TEXT,
    estimated_value DECIMAL(15,2),
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- 12. Property Profiles (Aggregated data)
CREATE TABLE IF NOT EXISTS property_profiles (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE,
    profile_data JSONB,
    market_analysis JSONB,
    investment_score DECIMAL(3,2),
    
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 13. Florida Data Updates (Track data pipeline)
CREATE TABLE IF NOT EXISTS fl_data_updates (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(100),
    update_type VARCHAR(50),
    records_processed INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB
);

-- 14. Florida Agent Status (Pipeline monitoring)
CREATE TABLE IF NOT EXISTS fl_agent_status (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100),
    last_run TIMESTAMP,
    status VARCHAR(50),
    records_updated INTEGER,
    next_scheduled_run TIMESTAMP,
    error_count INTEGER DEFAULT 0
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Florida Parcels indexes
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_address ON florida_parcels(phy_addr1);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city ON florida_parcels(phy_city);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_type ON florida_parcels(property_type);

-- Properties indexes
CREATE INDEX IF NOT EXISTS idx_properties_parcel ON properties(parcel_id);
CREATE INDEX IF NOT EXISTS idx_properties_address ON properties(property_address);

-- Sales History indexes
CREATE INDEX IF NOT EXISTS idx_sales_history_parcel ON property_sales_history(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sales_history_date ON property_sales_history(sale_date DESC);

-- NAV Assessments indexes
CREATE INDEX IF NOT EXISTS idx_nav_parcel ON nav_assessments(parcel_id);
CREATE INDEX IF NOT EXISTS idx_nav_year ON nav_assessments(assessment_year);

-- Sunbiz indexes
CREATE INDEX IF NOT EXISTS idx_sunbiz_name ON sunbiz_corporate(corporate_name);
CREATE INDEX IF NOT EXISTS idx_sunbiz_officers ON sunbiz_corporate USING GIN(to_tsvector('english', officers));
CREATE INDEX IF NOT EXISTS idx_sunbiz_principal_addr ON sunbiz_corporate(principal_address);
CREATE INDEX IF NOT EXISTS idx_sunbiz_mailing_addr ON sunbiz_corporate(mailing_address);

-- Tracking indexes
CREATE INDEX IF NOT EXISTS idx_tracked_user ON tracked_properties(user_id);
CREATE INDEX IF NOT EXISTS idx_tracked_parcel ON tracked_properties(parcel_id);

-- Permits indexes
CREATE INDEX IF NOT EXISTS idx_permits_parcel ON building_permits(parcel_id);
CREATE INDEX IF NOT EXISTS idx_permits_date ON building_permits(issue_date);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE nav_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_tax_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_corporate ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracked_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE building_permits ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_profiles ENABLE ROW LEVEL SECURITY;

-- Create public read policies for property data
CREATE POLICY "Public read access" ON florida_parcels FOR SELECT USING (true);
CREATE POLICY "Public read access" ON properties FOR SELECT USING (true);
CREATE POLICY "Public read access" ON property_sales_history FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nav_assessments FOR SELECT USING (true);
CREATE POLICY "Public read access" ON property_tax_info FOR SELECT USING (true);
CREATE POLICY "Public read access" ON sunbiz_corporate FOR SELECT USING (true);
CREATE POLICY "Public read access" ON property_entities FOR SELECT USING (true);
CREATE POLICY "Public read access" ON building_permits FOR SELECT USING (true);
CREATE POLICY "Public read access" ON property_profiles FOR SELECT USING (true);

-- User-specific policies for tracking tables
CREATE POLICY "Users can view own tracked properties" 
    ON tracked_properties FOR SELECT 
    USING (auth.uid()::text = user_id OR true); -- Allow all for now

CREATE POLICY "Users can view own alerts" 
    ON user_alerts FOR SELECT 
    USING (auth.uid()::text = user_id OR true); -- Allow all for now

-- ============================================================================
-- REAL-TIME SUBSCRIPTIONS
-- ============================================================================

-- Enable real-time for critical tables
ALTER PUBLICATION supabase_realtime ADD TABLE florida_parcels;
ALTER PUBLICATION supabase_realtime ADD TABLE property_sales_history;
ALTER PUBLICATION supabase_realtime ADD TABLE nav_assessments;
ALTER PUBLICATION supabase_realtime ADD TABLE user_alerts;

-- ============================================================================
-- SAMPLE DATA INSERTION
-- ============================================================================

-- Insert sample Florida parcels
INSERT INTO florida_parcels (
    parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name,
    assessed_value, taxable_value, just_value, year_built,
    bedrooms, bathrooms, living_area, property_type
) VALUES
    ('064210010010', '3930 INVERRARY BLVD', 'LAUDERHILL', '33319', 'INVERRARY HOLDINGS LLC',
     450000, 425000, 475000, 1985, 3, 2, 2100, 'SINGLE FAMILY'),
    ('064210010020', '123 MAIN ST', 'FORT LAUDERDALE', '33301', 'SMITH JOHN & MARY',
     325000, 300000, 350000, 1992, 4, 3, 2500, 'SINGLE FAMILY'),
    ('064210010030', '456 OCEAN BLVD', 'HOLLYWOOD', '33019', 'BEACH PROPERTIES LLC',
     1250000, 1200000, 1300000, 2010, 5, 4, 4500, 'CONDO'),
    ('064210010040', '789 SUNSET DR', 'PEMBROKE PINES', '33024', 'JOHNSON FAMILY TRUST',
     550000, 525000, 575000, 2005, 4, 3, 3200, 'TOWNHOUSE'),
    ('064210010050', '321 PALM AVE', 'DAVIE', '33314', 'INVESTMENT GROUP FLORIDA',
     275000, 250000, 300000, 1978, 3, 2, 1800, 'SINGLE FAMILY');

-- Insert sample sales history
INSERT INTO property_sales_history (
    parcel_id, sale_date, sale_price, sale_type, is_bank_sale
) VALUES
    ('064210010010', '2023-06-15', '450000', 'Warranty Deed', false),
    ('064210010010', '2020-03-20', '385000', 'Warranty Deed', false),
    ('064210010020', '2022-11-30', '325000', 'Warranty Deed', false),
    ('064210010030', '2024-01-15', '1250000', 'Warranty Deed', false),
    ('064210010040', '2023-08-22', '550000', 'Quit Claim Deed', false);

-- Insert sample NAV assessments
INSERT INTO nav_assessments (
    parcel_id, assessment_year, district_name, total_assessment
) VALUES
    ('064210010010', 2024, 'INVERRARY CDD', 1850.00),
    ('064210010020', 2024, 'CITY SPECIAL ASSESSMENT', 450.00),
    ('064210010030', 2024, 'BEACH EROSION DISTRICT', 2200.00);

-- Insert sample Sunbiz corporate data
INSERT INTO sunbiz_corporate (
    corporate_name, entity_type, status, officers, principal_address
) VALUES
    ('INVERRARY HOLDINGS LLC', 'Limited Liability Company', 'Active', 
     'SMITH, JOHN - Manager; DOE, JANE - Member', '3930 INVERRARY BLVD, LAUDERHILL, FL 33319'),
    ('BEACH PROPERTIES LLC', 'Limited Liability Company', 'Active',
     'JOHNSON, ROBERT - Manager', '456 OCEAN BLVD, HOLLYWOOD, FL 33019'),
    ('INVESTMENT GROUP FLORIDA', 'Corporation', 'Active',
     'WILLIAMS, MICHAEL - President; BROWN, SARAH - Secretary', '321 PALM AVE, DAVIE, FL 33314');

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check table creation
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check sample data
SELECT COUNT(*) as florida_parcels_count FROM florida_parcels;
SELECT COUNT(*) as sales_history_count FROM property_sales_history;
SELECT COUNT(*) as nav_assessments_count FROM nav_assessments;
SELECT COUNT(*) as sunbiz_count FROM sunbiz_corporate;

-- Test a typical UI query
SELECT 
    fp.*,
    (SELECT COUNT(*) FROM property_sales_history WHERE parcel_id = fp.parcel_id) as sale_count,
    (SELECT SUM(total_assessment) FROM nav_assessments WHERE parcel_id = fp.parcel_id) as total_nav
FROM florida_parcels fp
WHERE fp.parcel_id = '064210010010';

-- Success message
SELECT 'Database initialization complete! Tables created and sample data loaded.' as status;