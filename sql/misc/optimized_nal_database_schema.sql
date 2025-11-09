-- ===================================================================
-- OPTIMIZED NAL DATABASE SCHEMA FOR SUPABASE POSTGRESQL
-- Complete 7-Table Normalized Structure for 165 NAL Fields
-- Target: 750K+ records with sub-second query performance
-- ===================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- ===================================================================
-- TABLE 1: FLORIDA_PROPERTIES_CORE (Main Entity - 20 Key Fields)
-- Most frequently queried fields for autocomplete and basic info
-- ===================================================================

DROP TABLE IF EXISTS florida_properties_core CASCADE;

CREATE TABLE florida_properties_core (
    -- Primary identification
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(30) UNIQUE NOT NULL,
    co_no INTEGER NOT NULL,
    county_code VARCHAR(5),
    assessment_year INTEGER NOT NULL DEFAULT 2025,
    file_type VARCHAR(5) NOT NULL DEFAULT 'R',
    
    -- Owner identification (for searches)
    owner_name TEXT,
    
    -- Physical location (most searched fields)
    physical_address_1 TEXT,
    physical_address_2 TEXT,
    physical_city VARCHAR(50),
    physical_state VARCHAR(2) DEFAULT 'FL',
    physical_zipcode VARCHAR(10),
    
    -- Core valuation (most filtered fields)
    just_value NUMERIC(15,2),
    assessed_value_school_district NUMERIC(15,2),
    assessed_value_non_school_district NUMERIC(15,2),
    taxable_value_school_district NUMERIC(15,2),
    taxable_value_non_school_district NUMERIC(15,2),
    land_value NUMERIC(15,2),
    
    -- Property classification
    dor_use_code INTEGER,
    property_appraiser_use_code INTEGER,
    neighborhood_code NUMERIC(10,1),
    
    -- Basic property characteristics
    year_built INTEGER,
    effective_year_built INTEGER,
    total_living_area NUMERIC(10,2),
    land_square_footage BIGINT,
    number_of_buildings INTEGER,
    
    -- System fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    source VARCHAR(20) DEFAULT 'florida_nal',
    
    -- Indexes will be created after all tables
    CONSTRAINT fk_co_no CHECK (co_no BETWEEN 1 AND 67),
    CONSTRAINT fk_assessment_year CHECK (assessment_year BETWEEN 2020 AND 2030),
    CONSTRAINT fk_just_value CHECK (just_value >= 0),
    CONSTRAINT fk_year_built CHECK (year_built IS NULL OR year_built BETWEEN 1800 AND 2030)
);

-- ===================================================================
-- TABLE 2: PROPERTY_VALUATIONS (Detailed Financial Data - 31 Fields)
-- All valuation and assessment fields for financial analysis
-- ===================================================================

DROP TABLE IF EXISTS property_valuations CASCADE;

CREATE TABLE property_valuations (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(30) NOT NULL,
    assessment_year INTEGER NOT NULL DEFAULT 2025,
    
    -- Base valuation data
    just_value NUMERIC(15,2),
    just_value_change_flag VARCHAR(1),
    just_value_change_code INTEGER,
    assessed_value_school_district NUMERIC(15,2),
    assessed_value_non_school_district NUMERIC(15,2),
    taxable_value_school_district NUMERIC(15,2),
    taxable_value_non_school_district NUMERIC(15,2),
    
    -- Homestead valuations
    just_value_homestead NUMERIC(15,2),
    assessed_value_homestead NUMERIC(15,2),
    
    -- Residential classifications
    just_value_non_homestead_residential NUMERIC(15,2),
    assessed_value_non_homestead_residential NUMERIC(15,2),
    just_value_residential_non_residential NUMERIC(15,2),
    assessed_value_residential_non_residential NUMERIC(15,2),
    
    -- Classification use values
    just_value_class_use NUMERIC(15,2),
    assessed_value_class_use NUMERIC(15,2),
    
    -- Special land categories
    just_value_water_recharge NUMERIC(15,2),
    assessed_value_water_recharge NUMERIC(15,2),
    just_value_conservation_land NUMERIC(15,2),
    assessed_value_conservation_land NUMERIC(15,2),
    just_value_historic_commercial_property NUMERIC(15,2),
    assessed_value_historic_commercial_property NUMERIC(15,2),
    just_value_historic_significant NUMERIC(15,2),
    assessed_value_historic_significant NUMERIC(15,2),
    just_value_working_waterfront NUMERIC(15,2),
    assessed_value_working_waterfront NUMERIC(15,2),
    
    -- Component values
    land_value NUMERIC(15,2),
    construction_value NUMERIC(15,2),
    deleted_value NUMERIC(15,2),
    special_features_value NUMERIC(15,2),
    year_value_transferred INTEGER,
    
    -- Administrative
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (parcel_id) REFERENCES florida_properties_core(parcel_id) ON DELETE CASCADE,
    UNIQUE(parcel_id, assessment_year)
);

-- ===================================================================
-- TABLE 3: PROPERTY_EXEMPTIONS (Tax Exemptions - 50+ Fields as JSONB)
-- Efficient storage for 48 exemption fields plus common exemption flags
-- ===================================================================

DROP TABLE IF EXISTS property_exemptions CASCADE;

CREATE TABLE property_exemptions (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(30) NOT NULL,
    assessment_year INTEGER NOT NULL DEFAULT 2025,
    
    -- Common exemptions as separate columns for fast filtering
    homestead_exemption NUMERIC(12,2),
    senior_exemption NUMERIC(12,2),
    disability_exemption NUMERIC(12,2),
    veteran_exemption NUMERIC(12,2),
    agricultural_exemption NUMERIC(12,2),
    
    -- Boolean flags for common exemption types (fast WHERE clauses)
    has_homestead BOOLEAN DEFAULT FALSE,
    has_senior BOOLEAN DEFAULT FALSE,
    has_disability BOOLEAN DEFAULT FALSE,
    has_veteran BOOLEAN DEFAULT FALSE,
    has_agricultural BOOLEAN DEFAULT FALSE,
    has_any_exemption BOOLEAN DEFAULT FALSE,
    
    -- All 48 exemption fields stored as JSONB for flexibility
    all_exemptions JSONB,
    
    -- Summary calculations
    total_exemption_amount NUMERIC(12,2),
    exemption_count INTEGER DEFAULT 0,
    
    -- Previous homestead information
    previous_homestead_owner VARCHAR(10),
    previous_homestead_parcel_id VARCHAR(30),
    county_number_previous_homestead INTEGER,
    
    -- Administrative
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (parcel_id) REFERENCES florida_properties_core(parcel_id) ON DELETE CASCADE,
    UNIQUE(parcel_id, assessment_year)
);

-- ===================================================================
-- TABLE 4: PROPERTY_CHARACTERISTICS (Building & Land Details)
-- Physical property characteristics and construction details
-- ===================================================================

DROP TABLE IF EXISTS property_characteristics CASCADE;

CREATE TABLE property_characteristics (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(30) NOT NULL,
    assessment_year INTEGER NOT NULL DEFAULT 2025,
    
    -- Building details
    number_of_buildings INTEGER,
    number_of_residential_units INTEGER,
    total_living_area NUMERIC(10,2),
    improvement_quality NUMERIC(3,1),
    construction_class NUMERIC(3,1),
    
    -- Year information
    actual_year_built INTEGER,
    effective_year_built INTEGER,
    
    -- Land information
    land_square_footage BIGINT,
    land_units_code INTEGER,
    number_of_land_units INTEGER,
    public_land_code VARCHAR(1),
    
    -- Legal and location details
    short_legal_description TEXT,
    market_area VARCHAR(10),
    township VARCHAR(10),
    range_section VARCHAR(10),
    section_number INTEGER,
    census_block BIGINT,
    
    -- Inspection and administrative
    date_last_inspection INTEGER, -- MMYY format
    appraisal_status VARCHAR(10),
    county_appraisal_status VARCHAR(10),
    
    -- Classification codes
    special_circumstance_code VARCHAR(10),
    special_circumstance_year INTEGER,
    special_circumstance_text TEXT,
    district_code VARCHAR(10),
    district_year INTEGER,
    
    -- Alternative identifiers
    alternative_key VARCHAR(50),
    state_parcel_id VARCHAR(50),
    real_personal_status_id VARCHAR(10),
    multiple_parcel_id VARCHAR(10),
    
    -- Administrative
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (parcel_id) REFERENCES florida_properties_core(parcel_id) ON DELETE CASCADE,
    UNIQUE(parcel_id, assessment_year),
    
    CONSTRAINT fk_actual_year_built CHECK (actual_year_built IS NULL OR actual_year_built BETWEEN 1800 AND 2030),
    CONSTRAINT fk_effective_year_built CHECK (effective_year_built IS NULL OR effective_year_built BETWEEN 1800 AND 2030)
);

-- ===================================================================
-- TABLE 5: PROPERTY_SALES_ENHANCED (Sales History with Computed Fields)
-- Multiple sale records with computed fields for latest sales
-- ===================================================================

DROP TABLE IF EXISTS property_sales_enhanced CASCADE;

CREATE TABLE property_sales_enhanced (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(30) NOT NULL,
    assessment_year INTEGER NOT NULL DEFAULT 2025,
    
    -- Sale 1 (Most recent sale)
    sale_1_is_multi_parcel VARCHAR(1),
    sale_1_qualification_code NUMERIC(3,1),
    sale_1_validity_code VARCHAR(1),
    sale_1_price NUMERIC(15,2),
    sale_1_year INTEGER,
    sale_1_month INTEGER,
    sale_1_date DATE GENERATED ALWAYS AS (
        CASE 
            WHEN sale_1_year IS NOT NULL AND sale_1_month IS NOT NULL 
            THEN MAKE_DATE(sale_1_year::int, sale_1_month::int, 1)
            ELSE NULL 
        END
    ) STORED,
    sale_1_or_book INTEGER,
    sale_1_or_page INTEGER,
    sale_1_clerk_number BIGINT,
    sale_1_change_code INTEGER,
    
    -- Sale 2 (Previous sale)
    sale_2_is_multi_parcel VARCHAR(1),
    sale_2_qualification_code NUMERIC(3,1),
    sale_2_validity_code VARCHAR(1),
    sale_2_price NUMERIC(15,2),
    sale_2_year INTEGER,
    sale_2_month INTEGER,
    sale_2_date DATE GENERATED ALWAYS AS (
        CASE 
            WHEN sale_2_year IS NOT NULL AND sale_2_month IS NOT NULL 
            THEN MAKE_DATE(sale_2_year::int, sale_2_month::int, 1)
            ELSE NULL 
        END
    ) STORED,
    sale_2_or_book INTEGER,
    sale_2_or_page INTEGER,
    sale_2_clerk_number BIGINT,
    sale_2_change_code INTEGER,
    
    -- Computed fields for quick access
    latest_sale_price NUMERIC(15,2) GENERATED ALWAYS AS (
        COALESCE(sale_1_price, sale_2_price)
    ) STORED,
    latest_sale_date DATE GENERATED ALWAYS AS (
        COALESCE(sale_1_date, sale_2_date)
    ) STORED,
    latest_sale_year INTEGER GENERATED ALWAYS AS (
        COALESCE(sale_1_year, sale_2_year)
    ) STORED,
    
    -- Price change analysis
    price_change_amount NUMERIC(15,2) GENERATED ALWAYS AS (
        CASE WHEN sale_1_price IS NOT NULL AND sale_2_price IS NOT NULL 
             THEN sale_1_price - sale_2_price
             ELSE NULL END
    ) STORED,
    price_change_percent NUMERIC(8,4) GENERATED ALWAYS AS (
        CASE WHEN sale_1_price IS NOT NULL AND sale_2_price IS NOT NULL AND sale_2_price > 0
             THEN (sale_1_price - sale_2_price) / sale_2_price * 100
             ELSE NULL END
    ) STORED,
    
    -- Time between sales (months)
    months_between_sales INTEGER GENERATED ALWAYS AS (
        CASE WHEN sale_1_year IS NOT NULL AND sale_1_month IS NOT NULL 
                  AND sale_2_year IS NOT NULL AND sale_2_month IS NOT NULL
             THEN (sale_1_year - sale_2_year) * 12 + (sale_1_month - sale_2_month)
             ELSE NULL END
    ) STORED,
    
    -- Administrative
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (parcel_id) REFERENCES florida_properties_core(parcel_id) ON DELETE CASCADE,
    UNIQUE(parcel_id, assessment_year)
);

-- ===================================================================
-- TABLE 6: PROPERTY_ADDRESSES (Alternative Addresses)
-- Owner addresses, fiduciary addresses, and alternative contacts
-- ===================================================================

DROP TABLE IF EXISTS property_addresses CASCADE;

CREATE TABLE property_addresses (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(30) NOT NULL,
    assessment_year INTEGER NOT NULL DEFAULT 2025,
    
    -- Owner address (mailing address)
    owner_address_1 TEXT,
    owner_address_2 TEXT,
    owner_city VARCHAR(50),
    owner_state VARCHAR(20),
    owner_zipcode VARCHAR(10),
    owner_state_domicile VARCHAR(20),
    
    -- Fiduciary information (trustees, estate managers, etc.)
    fiduciary_code VARCHAR(1),
    fiduciary_name TEXT,
    fiduciary_address_1 TEXT,
    fiduciary_address_2 TEXT,
    fiduciary_city VARCHAR(50),
    fiduciary_state VARCHAR(20),
    fiduciary_zipcode VARCHAR(10),
    fiduciary_state_domicile VARCHAR(20),
    
    -- Previous owner information
    previous_owner_name TEXT,
    
    -- Address flags and indicators
    vacancy_indicator VARCHAR(1),
    
    -- Administrative
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (parcel_id) REFERENCES florida_properties_core(parcel_id) ON DELETE CASCADE,
    UNIQUE(parcel_id, assessment_year)
);

-- ===================================================================
-- TABLE 7: PROPERTY_ADMIN_DATA (System/Administrative Data)
-- System fields, sequence numbers, and administrative codes
-- ===================================================================

DROP TABLE IF EXISTS property_admin_data CASCADE;

CREATE TABLE property_admin_data (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(30) NOT NULL,
    assessment_year INTEGER NOT NULL DEFAULT 2025,
    
    -- System identifiers
    base_strata INTEGER,
    active_strata NUMERIC(3,1),
    group_number NUMERIC(3,1),
    sequence_number INTEGER,
    
    -- Parcel management
    parcel_split NUMERIC(8,1),
    
    -- Status and classification codes
    special_assessment_pass_code VARCHAR(10),
    class_use_code VARCHAR(10),
    taxing_district VARCHAR(10),
    tax_authority_code INTEGER,
    land_units_code INTEGER,
    
    -- Transfer and assessment flags
    assessment_transfer_flag VARCHAR(1),
    assessment_difference_transfer NUMERIC(15,2),
    
    -- Administrative
    import_batch_id VARCHAR(50),
    data_quality_score NUMERIC(3,2),
    validation_errors JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (parcel_id) REFERENCES florida_properties_core(parcel_id) ON DELETE CASCADE,
    UNIQUE(parcel_id, assessment_year)
);

-- ===================================================================
-- COMPREHENSIVE INDEXING STRATEGY
-- High-performance indexes for all common query patterns
-- ===================================================================

-- Core table indexes (most critical for performance)
CREATE UNIQUE INDEX idx_florida_properties_core_parcel_id ON florida_properties_core(parcel_id);
CREATE INDEX idx_florida_properties_core_county ON florida_properties_core(co_no);
CREATE INDEX idx_florida_properties_core_assessment_year ON florida_properties_core(assessment_year);

-- Text search indexes using GIN trigram for autocomplete
CREATE INDEX idx_florida_properties_core_owner_name_trgm ON florida_properties_core USING GIN(owner_name gin_trgm_ops);
CREATE INDEX idx_florida_properties_core_address_trgm ON florida_properties_core USING GIN(physical_address_1 gin_trgm_ops);
CREATE INDEX idx_florida_properties_core_city_trgm ON florida_properties_core USING GIN(physical_city gin_trgm_ops);

-- Value range indexes with partial indexes for non-null values
CREATE INDEX idx_florida_properties_core_just_value ON florida_properties_core(just_value) WHERE just_value > 0;
CREATE INDEX idx_florida_properties_core_assessed_value ON florida_properties_core(assessed_value_school_district) WHERE assessed_value_school_district > 0;
CREATE INDEX idx_florida_properties_core_taxable_value ON florida_properties_core(taxable_value_school_district) WHERE taxable_value_school_district > 0;

-- Composite indexes for common query patterns
CREATE INDEX idx_florida_properties_core_county_use_value ON florida_properties_core(co_no, dor_use_code, just_value);
CREATE INDEX idx_florida_properties_core_city_value ON florida_properties_core(physical_city, just_value);
CREATE INDEX idx_florida_properties_core_year_built_value ON florida_properties_core(year_built, just_value);

-- Property characteristics indexes
CREATE INDEX idx_property_characteristics_parcel_id ON property_characteristics(parcel_id);
CREATE INDEX idx_property_characteristics_year_built ON property_characteristics(actual_year_built) WHERE actual_year_built IS NOT NULL;
CREATE INDEX idx_property_characteristics_living_area ON property_characteristics(total_living_area) WHERE total_living_area > 0;
CREATE INDEX idx_property_characteristics_land_sqft ON property_characteristics(land_square_footage) WHERE land_square_footage > 0;

-- Valuation indexes
CREATE INDEX idx_property_valuations_parcel_id ON property_valuations(parcel_id);
CREATE INDEX idx_property_valuations_just_value ON property_valuations(just_value) WHERE just_value > 0;
CREATE INDEX idx_property_valuations_homestead_value ON property_valuations(just_value_homestead) WHERE just_value_homestead > 0;

-- Exemption indexes
CREATE INDEX idx_property_exemptions_parcel_id ON property_exemptions(parcel_id);
CREATE INDEX idx_property_exemptions_has_homestead ON property_exemptions(has_homestead) WHERE has_homestead = true;
CREATE INDEX idx_property_exemptions_has_any ON property_exemptions(has_any_exemption) WHERE has_any_exemption = true;
CREATE INDEX idx_property_exemptions_total_amount ON property_exemptions(total_exemption_amount) WHERE total_exemption_amount > 0;

-- JSONB indexes for exemptions
CREATE INDEX idx_property_exemptions_all_exemptions ON property_exemptions USING GIN(all_exemptions);

-- Sales indexes
CREATE INDEX idx_property_sales_enhanced_parcel_id ON property_sales_enhanced(parcel_id);
CREATE INDEX idx_property_sales_enhanced_latest_sale_date ON property_sales_enhanced(latest_sale_date) WHERE latest_sale_date IS NOT NULL;
CREATE INDEX idx_property_sales_enhanced_latest_price ON property_sales_enhanced(latest_sale_price) WHERE latest_sale_price > 0;
CREATE INDEX idx_property_sales_enhanced_price_change ON property_sales_enhanced(price_change_percent) WHERE price_change_percent IS NOT NULL;

-- Address indexes for mailing/contact searches
CREATE INDEX idx_property_addresses_parcel_id ON property_addresses(parcel_id);
CREATE INDEX idx_property_addresses_owner_city ON property_addresses(owner_city);
CREATE INDEX idx_property_addresses_owner_zipcode ON property_addresses(owner_zipcode);
CREATE INDEX idx_property_addresses_fiduciary_name ON property_addresses(fiduciary_name) WHERE fiduciary_name IS NOT NULL;

-- Administrative data indexes
CREATE INDEX idx_property_admin_data_parcel_id ON property_admin_data(parcel_id);
CREATE INDEX idx_property_admin_data_batch_id ON property_admin_data(import_batch_id);
CREATE INDEX idx_property_admin_data_created_at ON property_admin_data(created_at);

-- ===================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Flexible security that can be enabled/disabled as needed
-- ===================================================================

-- Enable RLS on all tables
ALTER TABLE florida_properties_core ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_valuations ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_exemptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_characteristics ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_enhanced ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_admin_data ENABLE ROW LEVEL SECURITY;

-- Public read access policies (can be modified as needed)
CREATE POLICY "Allow public read access" ON florida_properties_core FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_valuations FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_exemptions FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_characteristics FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_sales_enhanced FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_addresses FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_admin_data FOR SELECT USING (true);

-- Authenticated users can insert/update (adjust as needed)
CREATE POLICY "Allow authenticated insert" ON florida_properties_core FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Allow authenticated update" ON florida_properties_core FOR UPDATE TO authenticated USING (true);

-- Apply similar policies to other tables
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOR table_name IN SELECT unnest(ARRAY['property_valuations', 'property_exemptions', 'property_characteristics', 'property_sales_enhanced', 'property_addresses', 'property_admin_data'])
    LOOP
        EXECUTE format('CREATE POLICY "Allow authenticated insert" ON %I FOR INSERT TO authenticated WITH CHECK (true)', table_name);
        EXECUTE format('CREATE POLICY "Allow authenticated update" ON %I FOR UPDATE TO authenticated USING (true)', table_name);
    END LOOP;
END $$;

-- ===================================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- Pre-computed views for common complex queries
-- ===================================================================

-- Main property summary view (most commonly used data)
DROP MATERIALIZED VIEW IF EXISTS property_summary_view CASCADE;

CREATE MATERIALIZED VIEW property_summary_view AS
SELECT 
    p.parcel_id,
    p.co_no,
    p.county_code,
    p.assessment_year,
    p.owner_name,
    p.physical_address_1,
    p.physical_address_2,
    p.physical_city,
    p.physical_state,
    p.physical_zipcode,
    p.just_value,
    p.assessed_value_school_district,
    p.taxable_value_school_district,
    p.land_value,
    p.dor_use_code,
    p.property_appraiser_use_code,
    p.neighborhood_code,
    p.year_built,
    p.total_living_area,
    p.land_square_footage,
    
    -- From property_characteristics
    c.actual_year_built,
    c.effective_year_built,
    c.number_of_buildings,
    c.number_of_residential_units,
    c.improvement_quality,
    c.construction_class,
    
    -- From property_exemptions
    e.homestead_exemption,
    e.has_homestead,
    e.has_any_exemption,
    e.total_exemption_amount,
    
    -- From property_sales_enhanced
    s.latest_sale_price,
    s.latest_sale_date,
    s.latest_sale_year,
    s.price_change_percent,
    
    -- From property_addresses
    a.owner_address_1,
    a.owner_city AS owner_mailing_city,
    a.owner_state AS owner_mailing_state,
    a.owner_zipcode AS owner_mailing_zipcode,
    
    -- Computed fields
    CASE WHEN p.just_value > 0 AND s.latest_sale_price > 0 
         THEN ROUND(((p.just_value - s.latest_sale_price) / s.latest_sale_price * 100)::numeric, 2)
         ELSE NULL END as assessed_vs_sale_percent,
    
    CASE WHEN p.total_living_area > 0 AND p.just_value > 0
         THEN ROUND((p.just_value / p.total_living_area)::numeric, 2)
         ELSE NULL END as value_per_sqft,
         
    CASE WHEN p.land_square_footage > 0 AND p.land_value > 0
         THEN ROUND((p.land_value / p.land_square_footage)::numeric, 2)
         ELSE NULL END as land_value_per_sqft

FROM florida_properties_core p
LEFT JOIN property_characteristics c ON p.parcel_id = c.parcel_id AND p.assessment_year = c.assessment_year
LEFT JOIN property_exemptions e ON p.parcel_id = e.parcel_id AND p.assessment_year = e.assessment_year
LEFT JOIN property_sales_enhanced s ON p.parcel_id = s.parcel_id AND p.assessment_year = s.assessment_year
LEFT JOIN property_addresses a ON p.parcel_id = a.parcel_id AND p.assessment_year = a.assessment_year;

-- Create indexes on materialized view
CREATE UNIQUE INDEX idx_property_summary_view_parcel_id ON property_summary_view(parcel_id);
CREATE INDEX idx_property_summary_view_owner_name ON property_summary_view USING GIN(owner_name gin_trgm_ops);
CREATE INDEX idx_property_summary_view_address ON property_summary_view USING GIN(physical_address_1 gin_trgm_ops);
CREATE INDEX idx_property_summary_view_city ON property_summary_view USING GIN(physical_city gin_trgm_ops);
CREATE INDEX idx_property_summary_view_just_value ON property_summary_view(just_value) WHERE just_value > 0;
CREATE INDEX idx_property_summary_view_county_use ON property_summary_view(co_no, dor_use_code);

-- Property value statistics view
DROP MATERIALIZED VIEW IF EXISTS property_value_statistics CASCADE;

CREATE MATERIALIZED VIEW property_value_statistics AS
SELECT 
    co_no,
    physical_city,
    dor_use_code,
    COUNT(*) as property_count,
    AVG(just_value) as avg_just_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY just_value) as median_just_value,
    MIN(just_value) as min_just_value,
    MAX(just_value) as max_just_value,
    AVG(CASE WHEN total_living_area > 0 THEN just_value/total_living_area END) as avg_value_per_sqft,
    AVG(CASE WHEN latest_sale_date >= CURRENT_DATE - INTERVAL '2 years' THEN latest_sale_price END) as avg_recent_sale_price,
    COUNT(CASE WHEN has_homestead THEN 1 END) as homestead_count,
    COUNT(CASE WHEN latest_sale_date >= CURRENT_DATE - INTERVAL '1 year' THEN 1 END) as recent_sales_count
FROM property_summary_view
WHERE just_value > 0
GROUP BY co_no, physical_city, dor_use_code
HAVING COUNT(*) >= 5;  -- Only include groups with at least 5 properties

CREATE INDEX idx_property_value_statistics_county ON property_value_statistics(co_no);
CREATE INDEX idx_property_value_statistics_city ON property_value_statistics(physical_city);
CREATE INDEX idx_property_value_statistics_use_code ON property_value_statistics(dor_use_code);

-- ===================================================================
-- DATABASE FUNCTIONS FOR COMPLEX OPERATIONS
-- Custom functions for common business logic
-- ===================================================================

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_property_views()
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY property_summary_view;
    REFRESH MATERIALIZED VIEW CONCURRENTLY property_value_statistics;
    
    -- Update statistics
    ANALYZE florida_properties_core;
    ANALYZE property_valuations;
    ANALYZE property_exemptions;
    ANALYZE property_characteristics;
    ANALYZE property_sales_enhanced;
    ANALYZE property_addresses;
    ANALYZE property_admin_data;
    
    RAISE NOTICE 'All property views refreshed and statistics updated';
END;
$$;

-- Function for property search with ranking
CREATE OR REPLACE FUNCTION search_properties(
    search_term TEXT,
    limit_count INTEGER DEFAULT 10,
    county_filter INTEGER DEFAULT NULL
)
RETURNS TABLE (
    parcel_id VARCHAR(30),
    owner_name TEXT,
    physical_address_1 TEXT,
    physical_city VARCHAR(50),
    just_value NUMERIC(15,2),
    match_rank REAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.parcel_id,
        p.owner_name,
        p.physical_address_1,
        p.physical_city,
        p.just_value,
        (
            COALESCE(similarity(p.owner_name, search_term), 0) * 0.4 +
            COALESCE(similarity(p.physical_address_1, search_term), 0) * 0.4 +
            COALESCE(similarity(p.physical_city, search_term), 0) * 0.2
        ) as match_rank
    FROM florida_properties_core p
    WHERE 
        (county_filter IS NULL OR p.co_no = county_filter)
        AND (
            p.owner_name ILIKE '%' || search_term || '%' OR
            p.physical_address_1 ILIKE '%' || search_term || '%' OR
            p.physical_city ILIKE '%' || search_term || '%' OR
            p.parcel_id ILIKE '%' || search_term || '%'
        )
    ORDER BY match_rank DESC, p.just_value DESC
    LIMIT limit_count;
END;
$$;

-- Function to get comprehensive property details
CREATE OR REPLACE FUNCTION get_property_details(property_parcel_id VARCHAR(30))
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'property_core', row_to_json(p),
        'valuations', row_to_json(v),
        'exemptions', row_to_json(e),
        'characteristics', row_to_json(c),
        'sales', row_to_json(s),
        'addresses', row_to_json(a),
        'admin', row_to_json(ad)
    )
    INTO result
    FROM florida_properties_core p
    LEFT JOIN property_valuations v ON p.parcel_id = v.parcel_id
    LEFT JOIN property_exemptions e ON p.parcel_id = e.parcel_id  
    LEFT JOIN property_characteristics c ON p.parcel_id = c.parcel_id
    LEFT JOIN property_sales_enhanced s ON p.parcel_id = s.parcel_id
    LEFT JOIN property_addresses a ON p.parcel_id = a.parcel_id
    LEFT JOIN property_admin_data ad ON p.parcel_id = ad.parcel_id
    WHERE p.parcel_id = property_parcel_id;
    
    RETURN result;
END;
$$;

-- Function to calculate property statistics
CREATE OR REPLACE FUNCTION get_county_statistics(county_number INTEGER)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    stats JSON;
BEGIN
    SELECT json_build_object(
        'total_properties', COUNT(*),
        'avg_just_value', ROUND(AVG(just_value), 2),
        'median_just_value', ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY just_value), 2),
        'total_assessed_value', ROUND(SUM(assessed_value_school_district), 2),
        'properties_with_homestead', COUNT(CASE WHEN e.has_homestead THEN 1 END),
        'properties_with_sales', COUNT(CASE WHEN s.latest_sale_price > 0 THEN 1 END),
        'avg_sale_price', ROUND(AVG(s.latest_sale_price), 2),
        'properties_by_use_code', json_object_agg(p.dor_use_code, property_count)
    )
    INTO stats
    FROM florida_properties_core p
    LEFT JOIN property_exemptions e ON p.parcel_id = e.parcel_id
    LEFT JOIN property_sales_enhanced s ON p.parcel_id = s.parcel_id
    LEFT JOIN (
        SELECT dor_use_code, COUNT(*) as property_count
        FROM florida_properties_core
        WHERE co_no = county_number
        GROUP BY dor_use_code
    ) use_counts ON p.dor_use_code = use_counts.dor_use_code
    WHERE p.co_no = county_number;
    
    RETURN stats;
END;
$$;

-- ===================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- Keep computed fields and statistics current
-- ===================================================================

-- Function to update computed exemption fields
CREATE OR REPLACE FUNCTION update_exemption_flags()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Update boolean flags based on JSONB data
    NEW.has_homestead := COALESCE(NEW.homestead_exemption > 0, false);
    NEW.has_senior := COALESCE(NEW.senior_exemption > 0, false);
    NEW.has_disability := COALESCE(NEW.disability_exemption > 0, false);
    NEW.has_veteran := COALESCE(NEW.veteran_exemption > 0, false);
    NEW.has_agricultural := COALESCE(NEW.agricultural_exemption > 0, false);
    
    NEW.has_any_exemption := (
        NEW.has_homestead OR NEW.has_senior OR NEW.has_disability OR 
        NEW.has_veteran OR NEW.has_agricultural OR
        (NEW.all_exemptions IS NOT NULL AND NEW.all_exemptions != '{}'::jsonb)
    );
    
    -- Calculate total exemption amount
    NEW.total_exemption_amount := COALESCE(
        COALESCE(NEW.homestead_exemption, 0) +
        COALESCE(NEW.senior_exemption, 0) +
        COALESCE(NEW.disability_exemption, 0) +
        COALESCE(NEW.veteran_exemption, 0) +
        COALESCE(NEW.agricultural_exemption, 0),
        0
    );
    
    -- Count exemptions
    NEW.exemption_count := (
        CASE WHEN NEW.homestead_exemption > 0 THEN 1 ELSE 0 END +
        CASE WHEN NEW.senior_exemption > 0 THEN 1 ELSE 0 END +
        CASE WHEN NEW.disability_exemption > 0 THEN 1 ELSE 0 END +
        CASE WHEN NEW.veteran_exemption > 0 THEN 1 ELSE 0 END +
        CASE WHEN NEW.agricultural_exemption > 0 THEN 1 ELSE 0 END
    );
    
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

-- Create trigger for exemption updates
CREATE TRIGGER trigger_update_exemption_flags
    BEFORE INSERT OR UPDATE ON property_exemptions
    FOR EACH ROW
    EXECUTE FUNCTION update_exemption_flags();

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

-- Create triggers for all tables to update modified timestamps
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOR table_name IN SELECT unnest(ARRAY['florida_properties_core', 'property_valuations', 'property_characteristics', 'property_sales_enhanced', 'property_addresses', 'property_admin_data'])
    LOOP
        EXECUTE format('CREATE TRIGGER trigger_update_%s_timestamp BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_modified_column()', table_name, table_name);
    END LOOP;
END $$;

-- ===================================================================
-- PERFORMANCE MONITORING VIEWS
-- Monitor query performance and database health
-- ===================================================================

-- View for monitoring slow queries
CREATE OR REPLACE VIEW slow_query_monitor AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs
FROM pg_stats 
WHERE schemaname = 'public' 
  AND tablename LIKE '%property%'
  AND n_distinct IS NOT NULL
ORDER BY tablename, attname;

-- View for index usage statistics
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    ROUND(idx_tup_read::numeric / NULLIF(idx_scan, 0), 2) as avg_tuples_per_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename LIKE '%property%'
ORDER BY idx_scan DESC;

-- View for table statistics
CREATE OR REPLACE VIEW table_statistics AS
SELECT 
    schemaname,
    relname as tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    ROUND(n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2) as dead_row_percent,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND relname LIKE '%property%'
ORDER BY n_live_tup DESC;

-- ===================================================================
-- MAINTENANCE PROCEDURES
-- Regular maintenance tasks for optimal performance
-- ===================================================================

-- Procedure for database maintenance
CREATE OR REPLACE FUNCTION perform_database_maintenance()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    maintenance_report TEXT := '';
    table_name TEXT;
    view_name TEXT;
BEGIN
    -- Vacuum and analyze all property tables
    FOR table_name IN SELECT unnest(ARRAY['florida_properties_core', 'property_valuations', 'property_exemptions', 'property_characteristics', 'property_sales_enhanced', 'property_addresses', 'property_admin_data'])
    LOOP
        EXECUTE format('VACUUM ANALYZE %I', table_name);
        maintenance_report := maintenance_report || format('Vacuumed and analyzed %s' || chr(10), table_name);
    END LOOP;
    
    -- Refresh materialized views
    FOR view_name IN SELECT unnest(ARRAY['property_summary_view', 'property_value_statistics'])
    LOOP
        EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I', view_name);
        maintenance_report := maintenance_report || format('Refreshed materialized view %s' || chr(10), view_name);
    END LOOP;
    
    -- Reindex if needed (based on dead row percentage)
    FOR table_name IN 
        SELECT relname 
        FROM pg_stat_user_tables 
        WHERE schemaname = 'public' 
          AND relname LIKE '%property%'
          AND n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) > 0.1
    LOOP
        EXECUTE format('REINDEX TABLE %I', table_name);
        maintenance_report := maintenance_report || format('Reindexed table %s (high dead row ratio)' || chr(10), table_name);
    END LOOP;
    
    maintenance_report := maintenance_report || format('Maintenance completed at %s', NOW()::timestamp);
    
    RETURN maintenance_report;
END;
$$;

-- ===================================================================
-- DATABASE VALIDATION AND INTEGRITY CHECKS
-- Ensure data quality and consistency
-- ===================================================================

-- Function to validate data integrity
CREATE OR REPLACE FUNCTION validate_property_data()
RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    issue_count BIGINT,
    details TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check for orphaned records
    RETURN QUERY
    SELECT 
        'Orphaned Valuations' as check_name,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as status,
        COUNT(*) as issue_count,
        'Valuation records without matching core property' as details
    FROM property_valuations v
    LEFT JOIN florida_properties_core p ON v.parcel_id = p.parcel_id
    WHERE p.parcel_id IS NULL;
    
    -- Check for missing required fields
    RETURN QUERY
    SELECT 
        'Missing Owner Names' as check_name,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'WARN' END as status,
        COUNT(*) as issue_count,
        'Properties without owner names' as details
    FROM florida_properties_core
    WHERE owner_name IS NULL OR trim(owner_name) = '';
    
    -- Check for invalid values
    RETURN QUERY
    SELECT 
        'Invalid Just Values' as check_name,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as status,
        COUNT(*) as issue_count,
        'Properties with negative just values' as details
    FROM florida_properties_core
    WHERE just_value < 0;
    
    -- Check for data consistency
    RETURN QUERY
    SELECT 
        'Value Consistency' as check_name,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'WARN' END as status,
        COUNT(*) as issue_count,
        'Properties where assessed value exceeds just value significantly' as details
    FROM florida_properties_core
    WHERE assessed_value_school_district > just_value * 1.1
      AND just_value > 0;
END;
$$;

-- ===================================================================
-- FINAL COMMENTS AND DOCUMENTATION
-- ===================================================================

COMMENT ON TABLE florida_properties_core IS 'Main property entity table with most frequently queried fields (20 core fields)';
COMMENT ON TABLE property_valuations IS 'Detailed financial valuation data (31 fields) for analytics and reporting';
COMMENT ON TABLE property_exemptions IS 'Tax exemptions with JSONB storage for flexibility (50+ exemption fields)';
COMMENT ON TABLE property_characteristics IS 'Physical property characteristics and building details';
COMMENT ON TABLE property_sales_enhanced IS 'Sales history with computed fields for latest sale information';
COMMENT ON TABLE property_addresses IS 'Alternative addresses including owner and fiduciary addresses';
COMMENT ON TABLE property_admin_data IS 'System and administrative data for property management';

COMMENT ON MATERIALIZED VIEW property_summary_view IS 'Pre-computed view joining all property data for fast access';
COMMENT ON MATERIALIZED VIEW property_value_statistics IS 'Property value statistics by county, city, and use code';

COMMENT ON FUNCTION refresh_property_views() IS 'Refresh all materialized views and update table statistics';
COMMENT ON FUNCTION search_properties(TEXT, INTEGER, INTEGER) IS 'Search properties with similarity ranking';
COMMENT ON FUNCTION get_property_details(VARCHAR) IS 'Get comprehensive property details as JSON';
COMMENT ON FUNCTION perform_database_maintenance() IS 'Perform routine database maintenance tasks';
COMMENT ON FUNCTION validate_property_data() IS 'Validate data integrity and consistency';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'OPTIMIZED NAL DATABASE SCHEMA DEPLOYMENT COMPLETE';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Created 7 normalized tables for 165 NAL fields';
    RAISE NOTICE 'Applied comprehensive indexing strategy';
    RAISE NOTICE 'Created materialized views for performance';
    RAISE NOTICE 'Added business logic functions';
    RAISE NOTICE 'Configured Row Level Security policies';
    RAISE NOTICE 'Added triggers for data consistency';
    RAISE NOTICE 'Ready for data import and production use';
    RAISE NOTICE '=================================================================';
END $$;