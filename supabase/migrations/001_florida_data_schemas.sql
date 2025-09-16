-- Supabase Migration: Florida Data Sources Schema
-- Optimized schemas for all Florida Revenue data agents

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search optimization
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- =====================================================
-- CORE TRACKING TABLES
-- =====================================================

-- Data source update tracking
CREATE TABLE IF NOT EXISTS fl_data_updates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    agent_name TEXT NOT NULL,
    source_url TEXT,
    last_checked TIMESTAMPTZ DEFAULT NOW(),
    last_modified TIMESTAMPTZ,
    file_hash TEXT,
    file_size BIGINT,
    status TEXT DEFAULT 'pending',
    records_processed INTEGER DEFAULT 0,
    new_records INTEGER DEFAULT 0,
    updated_records INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_name, source_url)
);

-- Agent monitoring and status
CREATE TABLE IF NOT EXISTS fl_agent_status (
    agent_name TEXT PRIMARY KEY,
    is_active BOOLEAN DEFAULT true,
    last_run TIMESTAMPTZ,
    next_run TIMESTAMPTZ,
    total_runs INTEGER DEFAULT 0,
    successful_runs INTEGER DEFAULT 0,
    failed_runs INTEGER DEFAULT 0,
    average_runtime_seconds FLOAT,
    last_error TEXT,
    configuration JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- TPP (TANGIBLE PERSONAL PROPERTY) TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS fl_tpp_accounts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    county_number TEXT NOT NULL,
    account_number TEXT NOT NULL,
    assessment_year INTEGER NOT NULL,
    owner_name TEXT,
    owner_name2 TEXT,
    mailing_address TEXT,
    mailing_address2 TEXT,
    mailing_address3 TEXT,
    mailing_city TEXT,
    mailing_state TEXT,
    mailing_zip TEXT,
    mailing_country TEXT,
    primary_site_address TEXT,
    primary_site_address2 TEXT,
    primary_site_city TEXT,
    primary_site_zip TEXT,
    business_name TEXT,
    business_name2 TEXT,
    fei_number TEXT,
    business_description TEXT,
    tangible_value DECIMAL,
    exemption_value DECIMAL,
    taxable_value DECIMAL,
    property_appraiser_value DECIMAL,
    dor_value_code TEXT,
    nac_code TEXT,
    employee_count INTEGER,
    parent_account_flag TEXT,
    parent_account_number TEXT,
    folio_number TEXT,
    source_file TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(county_number, account_number, assessment_year)
);

-- Create optimized indexes for TPP
CREATE INDEX idx_tpp_owner_search ON fl_tpp_accounts USING gin(owner_name gin_trgm_ops);
CREATE INDEX idx_tpp_business_search ON fl_tpp_accounts USING gin(business_name gin_trgm_ops);
CREATE INDEX idx_tpp_county_year ON fl_tpp_accounts(county_number, assessment_year);
CREATE INDEX idx_tpp_taxable_value ON fl_tpp_accounts(taxable_value) WHERE taxable_value > 0;
CREATE INDEX idx_tpp_large_owners ON fl_tpp_accounts(owner_name, taxable_value DESC);

-- =====================================================
-- NAV (NON AD VALOREM) ASSESSMENT TABLES
-- =====================================================

-- NAV N - Parcel level summaries
CREATE TABLE IF NOT EXISTS fl_nav_parcel_summary (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    county_number TEXT NOT NULL,
    parcel_id TEXT NOT NULL,
    assessment_year INTEGER NOT NULL,
    tax_year INTEGER NOT NULL,
    roll_type TEXT,
    total_nav_units DECIMAL,
    total_nav_assessment DECIMAL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(county_number, parcel_id, assessment_year, tax_year)
);

-- NAV D - Assessment details
CREATE TABLE IF NOT EXISTS fl_nav_assessment_detail (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    county_number TEXT NOT NULL,
    parcel_id TEXT NOT NULL,
    assessment_year INTEGER NOT NULL,
    tax_year INTEGER NOT NULL,
    roll_type TEXT,
    nav_tax_code TEXT NOT NULL,
    nav_units DECIMAL,
    nav_assessment DECIMAL,
    authority_name TEXT,
    authority_type TEXT,
    district_name TEXT,
    is_cdd BOOLEAN DEFAULT FALSE,
    is_municipal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(county_number, parcel_id, assessment_year, tax_year, nav_tax_code)
);

-- Create optimized indexes for NAV
CREATE INDEX idx_nav_summary_parcel ON fl_nav_parcel_summary(parcel_id, assessment_year);
CREATE INDEX idx_nav_summary_county ON fl_nav_parcel_summary(county_number, assessment_year);
CREATE INDEX idx_nav_detail_parcel ON fl_nav_assessment_detail(parcel_id, assessment_year);
CREATE INDEX idx_nav_detail_tax_code ON fl_nav_assessment_detail(nav_tax_code);
CREATE INDEX idx_nav_detail_cdd ON fl_nav_assessment_detail(is_cdd) WHERE is_cdd = TRUE;
CREATE INDEX idx_nav_high_assessment ON fl_nav_assessment_detail(nav_assessment DESC);

-- =====================================================
-- SDF (SALES DATA FILE) TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS fl_sdf_sales (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    county_number TEXT NOT NULL,
    parcel_id TEXT NOT NULL,
    assessment_year INTEGER NOT NULL,
    active_start INTEGER,
    group_number INTEGER,
    dor_use_code TEXT,
    neighborhood_code TEXT,
    market_area TEXT,
    census_block TEXT,
    sale_id_code TEXT,
    sale_change_code TEXT,
    validity_indicator TEXT,
    official_record_book TEXT,
    official_record_page TEXT,
    clerk_number TEXT,
    qualification_code TEXT NOT NULL,
    qualification_description TEXT,
    sale_year INTEGER NOT NULL,
    sale_month INTEGER,
    sale_date DATE GENERATED ALWAYS AS (
        CASE 
            WHEN sale_year IS NOT NULL AND sale_month IS NOT NULL 
            THEN DATE(sale_year || '-' || LPAD(sale_month::TEXT, 2, '0') || '-01')
            ELSE NULL
        END
    ) STORED,
    sale_price DECIMAL,
    multi_parcel_sale TEXT,
    real_estate_id TEXT,
    map_id TEXT,
    state_parcel_id TEXT,
    is_qualified_sale BOOLEAN DEFAULT FALSE,
    is_distressed_sale BOOLEAN DEFAULT FALSE,
    is_bank_sale BOOLEAN DEFAULT FALSE,
    price_per_sqft DECIMAL,
    days_on_market INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(county_number, parcel_id, sale_id_code)
);

-- Create optimized indexes for SDF
CREATE INDEX idx_sdf_parcel_sales ON fl_sdf_sales(parcel_id, sale_date DESC);
CREATE INDEX idx_sdf_sale_date ON fl_sdf_sales(sale_date DESC);
CREATE INDEX idx_sdf_qual_code ON fl_sdf_sales(qualification_code);
CREATE INDEX idx_sdf_distressed ON fl_sdf_sales(is_distressed_sale) WHERE is_distressed_sale = TRUE;
CREATE INDEX idx_sdf_bank_sales ON fl_sdf_sales(is_bank_sale) WHERE is_bank_sale = TRUE;
CREATE INDEX idx_sdf_price_range ON fl_sdf_sales(sale_price) WHERE sale_price > 0;
CREATE INDEX idx_sdf_neighborhood ON fl_sdf_sales(neighborhood_code, sale_date DESC);
CREATE INDEX idx_sdf_qualified ON fl_sdf_sales(is_qualified_sale, sale_date DESC) WHERE is_qualified_sale = TRUE;

-- =====================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- =====================================================

-- Market summary by month
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_market_summary_monthly AS
SELECT 
    county_number,
    DATE_TRUNC('month', sale_date) as month,
    COUNT(*) as total_sales,
    COUNT(DISTINCT parcel_id) as unique_properties,
    SUM(CASE WHEN is_distressed_sale THEN 1 ELSE 0 END) as distressed_sales,
    SUM(CASE WHEN is_bank_sale THEN 1 ELSE 0 END) as bank_sales,
    AVG(sale_price) FILTER (WHERE sale_price > 1000) as avg_sale_price,
    MEDIAN(sale_price) FILTER (WHERE sale_price > 1000) as median_sale_price,
    SUM(sale_price) FILTER (WHERE sale_price > 1000) as total_volume,
    MAX(sale_price) as max_sale_price,
    MIN(sale_price) FILTER (WHERE sale_price > 1000) as min_sale_price
FROM fl_sdf_sales
WHERE sale_date IS NOT NULL
GROUP BY county_number, DATE_TRUNC('month', sale_date);

CREATE UNIQUE INDEX ON mv_market_summary_monthly(county_number, month);

-- Top property owners
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_property_owners AS
SELECT 
    owner_name,
    COUNT(*) as property_count,
    SUM(taxable_value) as total_taxable_value,
    AVG(taxable_value) as avg_taxable_value,
    MAX(taxable_value) as max_taxable_value,
    STRING_AGG(DISTINCT county_number, ',') as counties
FROM fl_tpp_accounts
WHERE owner_name IS NOT NULL
GROUP BY owner_name
HAVING COUNT(*) > 10
ORDER BY property_count DESC;

CREATE UNIQUE INDEX ON mv_top_property_owners(owner_name);

-- Distressed property pipeline
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_distressed_pipeline AS
SELECT 
    s.parcel_id,
    s.county_number,
    s.sale_date,
    s.sale_price,
    s.qualification_code,
    s.qualification_description,
    s.neighborhood_code,
    nav.total_nav_assessment,
    tpp.taxable_value as tpp_value
FROM fl_sdf_sales s
LEFT JOIN fl_nav_parcel_summary nav ON s.parcel_id = nav.parcel_id 
    AND s.assessment_year = nav.assessment_year
LEFT JOIN fl_tpp_accounts tpp ON s.parcel_id = tpp.folio_number
    AND s.assessment_year = tpp.assessment_year
WHERE s.is_distressed_sale = TRUE
    AND s.sale_date >= CURRENT_DATE - INTERVAL '6 months'
ORDER BY s.sale_date DESC;

CREATE UNIQUE INDEX ON mv_distressed_pipeline(parcel_id, sale_date);

-- =====================================================
-- ROW LEVEL SECURITY POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE fl_tpp_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE fl_nav_parcel_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE fl_nav_assessment_detail ENABLE ROW LEVEL SECURITY;
ALTER TABLE fl_sdf_sales ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your auth requirements)
CREATE POLICY "Enable read access for all users" ON fl_tpp_accounts FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON fl_nav_parcel_summary FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON fl_nav_assessment_detail FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON fl_sdf_sales FOR SELECT USING (true);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to all tables
CREATE TRIGGER update_fl_tpp_accounts_updated_at BEFORE UPDATE ON fl_tpp_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fl_nav_parcel_summary_updated_at BEFORE UPDATE ON fl_nav_parcel_summary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fl_nav_assessment_detail_updated_at BEFORE UPDATE ON fl_nav_assessment_detail
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fl_sdf_sales_updated_at BEFORE UPDATE ON fl_sdf_sales
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_market_summary_monthly;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_property_owners;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_distressed_pipeline;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for performance monitoring
CREATE INDEX idx_updates_agent_status ON fl_data_updates(agent_name, status);
CREATE INDEX idx_updates_last_checked ON fl_data_updates(last_checked);
CREATE INDEX idx_agent_next_run ON fl_agent_status(next_run) WHERE is_active = TRUE;