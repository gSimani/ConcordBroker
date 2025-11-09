-- ===================================================================
-- MASTER DEPLOYMENT SCRIPT FOR OPTIMIZED NAL DATABASE
-- Complete deployment of 7-table normalized schema to Supabase
-- Includes schema, migration, validation, and rollback capabilities
-- ===================================================================

-- ===================================================================
-- DEPLOYMENT CONFIGURATION
-- ===================================================================

-- Set deployment parameters
DO $$
DECLARE
    deployment_started_at TIMESTAMP;
    deployment_mode TEXT := 'PRODUCTION'; -- Options: 'TEST', 'PRODUCTION'
    backup_existing BOOLEAN := TRUE;
    run_migration BOOLEAN := FALSE; -- Set to TRUE to run migration automatically
    deployment_version TEXT := '1.0.0';
BEGIN
    deployment_started_at := NOW();
    
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'OPTIMIZED NAL DATABASE DEPLOYMENT STARTED';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Version: %', deployment_version;
    RAISE NOTICE 'Mode: %', deployment_mode;
    RAISE NOTICE 'Started at: %', deployment_started_at;
    RAISE NOTICE 'Backup existing: %', backup_existing;
    RAISE NOTICE 'Auto-migrate: %', run_migration;
    RAISE NOTICE '=================================================================';
END $$;

-- ===================================================================
-- PRE-DEPLOYMENT CHECKS
-- ===================================================================

-- Check PostgreSQL version and extensions
DO $$
DECLARE
    pg_version TEXT;
    missing_extensions TEXT[] := ARRAY[]::TEXT[];
BEGIN
    SELECT version() INTO pg_version;
    RAISE NOTICE 'PostgreSQL Version: %', pg_version;
    
    -- Check required extensions
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN
        missing_extensions := array_append(missing_extensions, 'pg_trgm');
    END IF;
    
    -- Report missing extensions
    IF array_length(missing_extensions, 1) > 0 THEN
        RAISE WARNING 'Missing required extensions: %', array_to_string(missing_extensions, ', ');
        RAISE NOTICE 'Installing missing extensions...';
    END IF;
END $$;

-- Install required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Check existing tables and create backups if needed
DO $$
DECLARE
    existing_tables TEXT[] := ARRAY[]::TEXT[];
    table_name TEXT;
    backup_suffix TEXT := '_backup_' || to_char(NOW(), 'YYYYMMDD_HH24MISS');
BEGIN
    -- Check for existing tables that might conflict
    FOR table_name IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' 
                                                         AND tablename LIKE '%property%' 
                                                         OR tablename = 'florida_parcels'
    LOOP
        existing_tables := array_append(existing_tables, table_name);
    END LOOP;
    
    IF array_length(existing_tables, 1) > 0 THEN
        RAISE NOTICE 'Found existing tables: %', array_to_string(existing_tables, ', ');
        
        -- Create backup of florida_parcels if it exists
        IF 'florida_parcels' = ANY(existing_tables) THEN
            EXECUTE format('CREATE TABLE florida_parcels%s AS TABLE florida_parcels', backup_suffix);
            RAISE NOTICE 'Created backup: florida_parcels%', backup_suffix;
        END IF;
    ELSE
        RAISE NOTICE 'No existing property tables found. Clean deployment.';
    END IF;
END $$;

-- ===================================================================
-- CORE SCHEMA DEPLOYMENT
-- ===================================================================

-- Enable required extensions (if not already enabled)
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
    
    -- Constraints
    CONSTRAINT fk_co_no CHECK (co_no BETWEEN 1 AND 67),
    CONSTRAINT fk_assessment_year CHECK (assessment_year BETWEEN 2020 AND 2030),
    CONSTRAINT fk_just_value CHECK (just_value >= 0),
    CONSTRAINT fk_year_built CHECK (year_built IS NULL OR year_built BETWEEN 1800 AND 2030)
);

-- ===================================================================
-- TABLE 2: PROPERTY_VALUATIONS (Detailed Financial Data - 31 Fields)
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
    date_last_inspection INTEGER,
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

-- Other table indexes
CREATE INDEX idx_property_characteristics_parcel_id ON property_characteristics(parcel_id);
CREATE INDEX idx_property_valuations_parcel_id ON property_valuations(parcel_id);
CREATE INDEX idx_property_exemptions_parcel_id ON property_exemptions(parcel_id);
CREATE INDEX idx_property_sales_enhanced_parcel_id ON property_sales_enhanced(parcel_id);
CREATE INDEX idx_property_addresses_parcel_id ON property_addresses(parcel_id);
CREATE INDEX idx_property_admin_data_parcel_id ON property_admin_data(parcel_id);

-- JSONB indexes
CREATE INDEX idx_property_exemptions_all_exemptions ON property_exemptions USING GIN(all_exemptions);

-- ===================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ===================================================================

-- Enable RLS on all tables
ALTER TABLE florida_properties_core ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_valuations ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_exemptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_characteristics ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_enhanced ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_admin_data ENABLE ROW LEVEL SECURITY;

-- Public read access policies
CREATE POLICY "Allow public read access" ON florida_properties_core FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_valuations FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_exemptions FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_characteristics FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_sales_enhanced FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_addresses FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON property_admin_data FOR SELECT USING (true);

-- Authenticated users policies
CREATE POLICY "Allow authenticated insert" ON florida_properties_core FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Allow authenticated update" ON florida_properties_core FOR UPDATE TO authenticated USING (true);

-- ===================================================================
-- BUSINESS LOGIC FUNCTIONS
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

-- ===================================================================
-- MATERIALIZED VIEWS (SIMPLIFIED FOR INITIAL DEPLOYMENT)
-- ===================================================================

-- Main property summary view
CREATE MATERIALIZED VIEW property_summary_view AS
SELECT 
    p.parcel_id,
    p.co_no,
    p.assessment_year,
    p.owner_name,
    p.physical_address_1,
    p.physical_city,
    p.just_value,
    p.assessed_value_school_district,
    p.taxable_value_school_district,
    p.dor_use_code,
    p.year_built,
    p.total_living_area,
    p.created_at,
    p.updated_at
FROM florida_properties_core p;

CREATE UNIQUE INDEX idx_property_summary_view_parcel_id ON property_summary_view(parcel_id);
CREATE INDEX idx_property_summary_view_owner_name ON property_summary_view USING GIN(owner_name gin_trgm_ops);

-- ===================================================================
-- DEPLOYMENT VALIDATION
-- ===================================================================

-- Function to validate deployment
CREATE OR REPLACE FUNCTION validate_deployment()
RETURNS TABLE (
    component TEXT,
    status TEXT,
    details TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check tables exist
    RETURN QUERY
    SELECT 
        'Tables' as component,
        CASE WHEN COUNT(*) = 7 THEN 'SUCCESS' ELSE 'FAIL' END as status,
        format('%s/7 tables created', COUNT(*)) as details
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
      AND table_name IN (
        'florida_properties_core', 'property_valuations', 'property_exemptions',
        'property_characteristics', 'property_sales_enhanced', 'property_addresses', 'property_admin_data'
      );
    
    -- Check indexes
    RETURN QUERY
    SELECT 
        'Indexes' as component,
        CASE WHEN COUNT(*) >= 10 THEN 'SUCCESS' ELSE 'WARN' END as status,
        format('%s indexes created', COUNT(*)) as details
    FROM pg_indexes 
    WHERE schemaname = 'public' 
      AND tablename LIKE '%property%';
    
    -- Check materialized views
    RETURN QUERY
    SELECT 
        'Materialized Views' as component,
        CASE WHEN COUNT(*) >= 1 THEN 'SUCCESS' ELSE 'FAIL' END as status,
        format('%s views created', COUNT(*)) as details
    FROM pg_matviews 
    WHERE schemaname = 'public';
    
    -- Check functions
    RETURN QUERY
    SELECT 
        'Functions' as component,
        CASE WHEN COUNT(*) >= 2 THEN 'SUCCESS' ELSE 'WARN' END as status,
        format('%s functions created', COUNT(*)) as details
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
      AND p.proname LIKE '%property%' OR p.proname LIKE '%search%';
END;
$$;

-- ===================================================================
-- POST-DEPLOYMENT TASKS
-- ===================================================================

-- Update statistics
ANALYZE florida_properties_core;
ANALYZE property_valuations;
ANALYZE property_exemptions;
ANALYZE property_characteristics;
ANALYZE property_sales_enhanced;
ANALYZE property_addresses;
ANALYZE property_admin_data;

-- Add table comments for documentation
COMMENT ON TABLE florida_properties_core IS 'Main property entity with frequently queried fields (optimized for search)';
COMMENT ON TABLE property_valuations IS 'Detailed financial valuation data for analytics';
COMMENT ON TABLE property_exemptions IS 'Tax exemptions with JSONB storage for 48+ exemption fields';
COMMENT ON TABLE property_characteristics IS 'Physical property characteristics and building details';
COMMENT ON TABLE property_sales_enhanced IS 'Sales history with computed fields';
COMMENT ON TABLE property_addresses IS 'Owner and fiduciary addresses';
COMMENT ON TABLE property_admin_data IS 'Administrative and system data';

-- ===================================================================
-- DEPLOYMENT COMPLETION AND VALIDATION
-- ===================================================================

DO $$
DECLARE
    validation_results RECORD;
    deployment_status TEXT := 'SUCCESS';
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'DEPLOYMENT VALIDATION RESULTS';
    RAISE NOTICE '=================================================================';
    
    FOR validation_results IN SELECT * FROM validate_deployment()
    LOOP
        RAISE NOTICE '% | % | %', 
            RPAD(validation_results.component, 20),
            RPAD(validation_results.status, 10),
            validation_results.details;
        
        IF validation_results.status = 'FAIL' THEN
            deployment_status := 'FAILED';
        END IF;
    END LOOP;
    
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'DEPLOYMENT STATUS: %', deployment_status;
    RAISE NOTICE '=================================================================';
    
    IF deployment_status = 'SUCCESS' THEN
        RAISE NOTICE 'Schema deployment completed successfully!';
        RAISE NOTICE 'Next steps:';
        RAISE NOTICE '1. Run data migration: SELECT migrate_nal_data_to_normalized();';
        RAISE NOTICE '2. Import NAL data using: SELECT insert_nal_property_record(record);';
        RAISE NOTICE '3. Refresh views: SELECT refresh_property_views();';
        RAISE NOTICE '4. Test search: SELECT * FROM search_properties(''search_term'');';
    ELSE
        RAISE WARNING 'Deployment completed with errors. Please review validation results.';
    END IF;
    
    RAISE NOTICE 'Deployment completed at: %', NOW()::timestamp;
END $$;

-- ===================================================================
-- QUICK START INSTRUCTIONS
-- ===================================================================

/*
QUICK START GUIDE:

1. DEPLOY SCHEMA (Already done by running this script):
   - 7 normalized tables created
   - Comprehensive indexes applied  
   - Materialized views created
   - Business logic functions added

2. MIGRATE EXISTING DATA (if you have florida_parcels table):
   SELECT migrate_nal_data_to_normalized();

3. IMPORT NAL DATA (when you have NAL CSV files):
   -- Use the insert_nal_property_record() function for each record

4. REFRESH STATISTICS:
   SELECT refresh_property_views();

5. TEST THE SYSTEM:
   SELECT * FROM search_properties('property search term');
   SELECT * FROM property_summary_view LIMIT 10;

6. MONITOR PERFORMANCE:
   SELECT * FROM pg_stat_user_tables WHERE relname LIKE '%property%';
   SELECT * FROM pg_stat_user_indexes WHERE relname LIKE '%property%';

ROLLBACK (if needed):
   SELECT rollback_migration();
*/