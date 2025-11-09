-- ============================================================================
-- Property Appraiser Data Schema for Supabase
-- Complete schema for NAL, NAP, SDF, NAV N, and NAV D data
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. PROPERTY ASSESSMENTS TABLE (NAL Data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS property_assessments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county_code VARCHAR(5),
    county_name VARCHAR(50),
    
    -- Owner Information
    owner_name VARCHAR(255),
    owner_address VARCHAR(255),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    
    -- Property Location
    property_address VARCHAR(255),
    property_city VARCHAR(100),
    property_zip VARCHAR(10),
    property_use_code VARCHAR(20),
    tax_district VARCHAR(50),
    subdivision VARCHAR(100),
    
    -- Valuation
    just_value DECIMAL(12,2),
    assessed_value DECIMAL(12,2),
    taxable_value DECIMAL(12,2),
    land_value DECIMAL(12,2),
    building_value DECIMAL(12,2),
    
    -- Property Characteristics
    total_sq_ft INTEGER,
    living_area INTEGER,
    year_built INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    pool BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    tax_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_parcel_assessment UNIQUE(parcel_id, county_code, tax_year)
);

-- Indexes for performance
CREATE INDEX idx_assessment_parcel ON property_assessments(parcel_id);
CREATE INDEX idx_assessment_county ON property_assessments(county_code);
CREATE INDEX idx_assessment_owner ON property_assessments(owner_name);
CREATE INDEX idx_assessment_value ON property_assessments(taxable_value);

-- ============================================================================
-- 2. PROPERTY OWNERS TABLE (NAP Data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS property_owners (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county_code VARCHAR(5),
    county_name VARCHAR(50),
    
    -- Owner Details
    owner_sequence INTEGER DEFAULT 1,
    owner_name VARCHAR(255),
    owner_type VARCHAR(50), -- Individual, Corporation, Trust, LLC, etc.
    
    -- Mailing Address
    mailing_address_1 VARCHAR(255),
    mailing_address_2 VARCHAR(255),
    mailing_city VARCHAR(100),
    mailing_state VARCHAR(2),
    mailing_zip VARCHAR(10),
    mailing_country VARCHAR(50) DEFAULT 'USA',
    
    -- Ownership
    ownership_percentage DECIMAL(5,2) DEFAULT 100.00,
    
    -- Metadata
    tax_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_parcel_owner UNIQUE(parcel_id, county_code, owner_sequence, tax_year)
);

-- Indexes
CREATE INDEX idx_owner_parcel ON property_owners(parcel_id);
CREATE INDEX idx_owner_name ON property_owners(owner_name);
CREATE INDEX idx_owner_type ON property_owners(owner_type);

-- ============================================================================
-- 3. PROPERTY SALES TABLE (SDF Data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS property_sales (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county_code VARCHAR(5),
    county_name VARCHAR(50),
    
    -- Sale Information
    sale_date DATE,
    sale_price DECIMAL(12,2),
    sale_type VARCHAR(50),
    deed_type VARCHAR(50),
    
    -- Parties
    grantor_name VARCHAR(255), -- Seller
    grantee_name VARCHAR(255), -- Buyer
    
    -- Sale Characteristics
    qualified_sale BOOLEAN DEFAULT FALSE,
    vacant_at_sale BOOLEAN DEFAULT FALSE,
    multi_parcel_sale BOOLEAN DEFAULT FALSE,
    
    -- Recording Information
    book_page VARCHAR(50),
    instrument_number VARCHAR(50),
    verification_code VARCHAR(10),
    
    -- Metadata
    tax_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_sale_parcel ON property_sales(parcel_id);
CREATE INDEX idx_sale_date ON property_sales(sale_date DESC);
CREATE INDEX idx_sale_price ON property_sales(sale_price);
CREATE INDEX idx_sale_buyer ON property_sales(grantee_name);
CREATE INDEX idx_sale_seller ON property_sales(grantor_name);
CREATE INDEX idx_sale_qualified ON property_sales(qualified_sale);

-- ============================================================================
-- 4. NAV SUMMARIES TABLE (NAV N Data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nav_summaries (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county_code VARCHAR(5),
    county_name VARCHAR(50),
    
    -- Assessment Summary
    tax_account_number VARCHAR(50),
    roll_type VARCHAR(10),
    tax_year INTEGER,
    total_assessments DECIMAL(10,2),
    num_assessments INTEGER,
    tax_roll_sequence INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_nav_summary UNIQUE(parcel_id, county_code, tax_year)
);

-- Indexes
CREATE INDEX idx_nav_summary_parcel ON nav_summaries(parcel_id);
CREATE INDEX idx_nav_summary_county ON nav_summaries(county_code);
CREATE INDEX idx_nav_summary_total ON nav_summaries(total_assessments);

-- ============================================================================
-- 5. NAV DETAILS TABLE (NAV D Data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nav_details (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county_code VARCHAR(5),
    county_name VARCHAR(50),
    
    -- Assessment Detail
    levy_id VARCHAR(50),
    levy_name VARCHAR(255),
    local_gov_code VARCHAR(20),
    function_code VARCHAR(20),
    assessment_amount DECIMAL(10,2),
    tax_roll_sequence INTEGER,
    
    -- Metadata
    tax_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_nav_detail_parcel ON nav_details(parcel_id);
CREATE INDEX idx_nav_detail_levy ON nav_details(levy_id);
CREATE INDEX idx_nav_detail_amount ON nav_details(assessment_amount);

-- ============================================================================
-- 6. PROPERTY MASTER VIEW
-- Combines assessment, owner, and recent sale data
-- ============================================================================
CREATE OR REPLACE VIEW property_master AS
SELECT 
    pa.parcel_id,
    pa.county_code,
    pa.county_name,
    pa.owner_name,
    pa.property_address,
    pa.property_city,
    pa.property_zip,
    pa.property_use_code,
    pa.just_value,
    pa.assessed_value,
    pa.taxable_value,
    pa.year_built,
    pa.living_area,
    pa.bedrooms,
    pa.bathrooms,
    po.owner_type,
    po.mailing_address_1,
    po.mailing_city,
    po.mailing_state,
    po.mailing_zip,
    ps.sale_date AS last_sale_date,
    ps.sale_price AS last_sale_price,
    ps.grantee_name AS current_owner_from_sale,
    ns.total_assessments AS nav_total,
    ns.num_assessments AS nav_count
FROM property_assessments pa
LEFT JOIN property_owners po ON 
    pa.parcel_id = po.parcel_id 
    AND pa.county_code = po.county_code 
    AND po.owner_sequence = 1
LEFT JOIN LATERAL (
    SELECT *
    FROM property_sales
    WHERE parcel_id = pa.parcel_id
    AND county_code = pa.county_code
    ORDER BY sale_date DESC
    LIMIT 1
) ps ON true
LEFT JOIN nav_summaries ns ON 
    pa.parcel_id = ns.parcel_id 
    AND pa.county_code = ns.county_code;

-- ============================================================================
-- 7. FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for property_assessments
CREATE TRIGGER update_property_assessments_updated_at 
    BEFORE UPDATE ON property_assessments 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 8. ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on tables
ALTER TABLE property_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_owners ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE nav_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE nav_details ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access
CREATE POLICY "Enable read access for all users" ON property_assessments
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON property_owners
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON property_sales
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON nav_summaries
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON nav_details
    FOR SELECT USING (true);

-- Create policies for authenticated write access
CREATE POLICY "Enable insert for authenticated users" ON property_assessments
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable insert for authenticated users" ON property_owners
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable insert for authenticated users" ON property_sales
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable insert for authenticated users" ON nav_summaries
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable insert for authenticated users" ON nav_details
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- ============================================================================
-- 9. STATISTICS AND MONITORING
-- ============================================================================

-- Table to track data loads
CREATE TABLE IF NOT EXISTS property_data_loads (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    load_type VARCHAR(50), -- NAL, NAP, SDF, NAV_N, NAV_D
    county_code VARCHAR(5),
    county_name VARCHAR(50),
    records_loaded INTEGER,
    load_started_at TIMESTAMP,
    load_completed_at TIMESTAMP,
    status VARCHAR(20), -- success, failed, partial
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Function to get property statistics by county
CREATE OR REPLACE FUNCTION get_county_property_stats(p_county_code VARCHAR)
RETURNS TABLE (
    total_properties BIGINT,
    total_sales BIGINT,
    avg_taxable_value NUMERIC,
    total_nav_assessments NUMERIC,
    last_update TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT pa.parcel_id)::BIGINT as total_properties,
        COUNT(DISTINCT ps.id)::BIGINT as total_sales,
        ROUND(AVG(pa.taxable_value), 2) as avg_taxable_value,
        ROUND(SUM(ns.total_assessments), 2) as total_nav_assessments,
        MAX(pa.created_at) as last_update
    FROM property_assessments pa
    LEFT JOIN property_sales ps ON pa.parcel_id = ps.parcel_id AND pa.county_code = ps.county_code
    LEFT JOIN nav_summaries ns ON pa.parcel_id = ns.parcel_id AND pa.county_code = ns.county_code
    WHERE pa.county_code = p_county_code;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 10. SAMPLE QUERIES
-- ============================================================================

/*
-- Get all properties for a specific owner
SELECT * FROM property_assessments 
WHERE owner_name ILIKE '%SMITH%'
ORDER BY taxable_value DESC;

-- Get recent sales in a county
SELECT * FROM property_sales
WHERE county_code = '16' -- Broward
AND sale_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY sale_date DESC;

-- Get properties with high NAV assessments
SELECT 
    pa.parcel_id,
    pa.owner_name,
    pa.property_address,
    ns.total_assessments
FROM property_assessments pa
JOIN nav_summaries ns ON pa.parcel_id = ns.parcel_id
WHERE ns.total_assessments > 1000
ORDER BY ns.total_assessments DESC;

-- Get detailed NAV charges for a property
SELECT * FROM nav_details
WHERE parcel_id = '123456789'
ORDER BY assessment_amount DESC;
*/

-- ============================================================================
-- End of Property Appraiser Schema
-- ============================================================================