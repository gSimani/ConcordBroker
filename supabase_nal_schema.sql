
-- Execute this SQL in your Supabase SQL Editor:

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. Core properties table
CREATE TABLE IF NOT EXISTS florida_properties_core (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    co_no INTEGER,
    assessment_year INTEGER DEFAULT 2025,
    owner_name TEXT,
    owner_state VARCHAR(50),
    physical_address TEXT,
    physical_city VARCHAR(100),
    physical_zipcode VARCHAR(10),
    just_value DECIMAL(15,2),
    assessed_value_sd DECIMAL(15,2),
    assessed_value_nsd DECIMAL(15,2),
    taxable_value_sd DECIMAL(15,2),
    taxable_value_nsd DECIMAL(15,2),
    land_value DECIMAL(15,2),
    dor_use_code VARCHAR(10),
    pa_use_code VARCHAR(10),
    neighborhood_code VARCHAR(20),
    land_sqft BIGINT,
    tax_authority_code VARCHAR(10),
    market_area VARCHAR(10),
    township VARCHAR(10),
    range_val VARCHAR(10),
    section_val VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Property valuations
CREATE TABLE IF NOT EXISTS property_valuations (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    just_value DECIMAL(15,2),
    just_value_change DECIMAL(15,2),
    assessed_value_sd DECIMAL(15,2),
    assessed_value_nsd DECIMAL(15,2),
    taxable_value_sd DECIMAL(15,2),
    taxable_value_nsd DECIMAL(15,2),
    just_value_homestead DECIMAL(15,2),
    assessed_value_homestead DECIMAL(15,2),
    just_value_non_homestead_res DECIMAL(15,2),
    assessed_value_non_homestead_res DECIMAL(15,2),
    just_value_conservation_land DECIMAL(15,2),
    assessed_value_conservation_land DECIMAL(15,2),
    land_value DECIMAL(15,2),
    new_construction_value DECIMAL(15,2),
    deleted_value DECIMAL(15,2),
    special_features_value DECIMAL(15,2),
    year_value_transferred INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Property exemptions (JSONB for flexibility)
CREATE TABLE IF NOT EXISTS property_exemptions (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    homestead_exemption DECIMAL(15,2),
    senior_exemption DECIMAL(15,2),
    disability_exemption DECIMAL(15,2),
    veteran_exemption DECIMAL(15,2),
    widow_exemption DECIMAL(15,2),
    all_exemptions JSONB,
    previous_homestead_owner VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Property characteristics
CREATE TABLE IF NOT EXISTS property_characteristics (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    actual_year_built INTEGER,
    effective_year_built INTEGER,
    total_living_area INTEGER,
    land_units BIGINT,
    land_units_code VARCHAR(5),
    number_of_buildings INTEGER,
    number_of_residential_units INTEGER,
    improvement_quality VARCHAR(10),
    construction_class VARCHAR(10),
    public_land_code VARCHAR(5),
    census_block VARCHAR(20),
    inspection_date VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Sales history enhanced
CREATE TABLE IF NOT EXISTS property_sales_enhanced (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    sale_date_1 DATE,
    sale_price_1 DECIMAL(15,2),
    sale_year_1 INTEGER,
    sale_month_1 INTEGER,
    qualification_code_1 VARCHAR(10),
    validity_code_1 VARCHAR(5),
    clerk_number_1 BIGINT,
    multi_parcel_sale_1 VARCHAR(5),
    sale_date_2 DATE,
    sale_price_2 DECIMAL(15,2),
    sale_year_2 INTEGER,
    sale_month_2 INTEGER,
    qualification_code_2 VARCHAR(10),
    validity_code_2 VARCHAR(5),
    clerk_number_2 BIGINT,
    multi_parcel_sale_2 VARCHAR(5),
    latest_sale_date DATE,
    latest_sale_price DECIMAL(15,2),
    price_change_percent DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Property addresses
CREATE TABLE IF NOT EXISTS property_addresses (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    owner_address_1 TEXT,
    owner_address_2 TEXT,
    owner_city VARCHAR(100),
    owner_zipcode VARCHAR(10),
    fiduciary_name VARCHAR(255),
    fiduciary_address_1 TEXT,
    fiduciary_address_2 TEXT,
    fiduciary_city VARCHAR(100),
    fiduciary_zipcode VARCHAR(10),
    fiduciary_state VARCHAR(50),
    fiduciary_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. Administrative data
CREATE TABLE IF NOT EXISTS property_admin_data (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    file_type VARCHAR(5),
    group_number DECIMAL(10,2),
    base_street INTEGER,
    active_street DECIMAL(8,2),
    parcel_split DECIMAL(10,2),
    special_assessment_code VARCHAR(10),
    district_code VARCHAR(10),
    district_year INTEGER,
    legal_description TEXT,
    sequence_number INTEGER,
    rs_id VARCHAR(10),
    mp_id VARCHAR(20),
    state_parcel_id VARCHAR(50),
    special_circumstance_year INTEGER,
    special_circumstance_text TEXT,
    application_status VARCHAR(10),
    county_application_status VARCHAR(10),
    assessment_transfer_flag VARCHAR(5),
    assessment_difference_transfer DECIMAL(15,2),
    alternate_key VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_properties_core_parcel_id ON florida_properties_core(parcel_id);
CREATE INDEX IF NOT EXISTS idx_properties_core_owner_name ON florida_properties_core USING GIN (owner_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_properties_core_address ON florida_properties_core USING GIN (physical_address gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_properties_core_city ON florida_properties_core(physical_city);
CREATE INDEX IF NOT EXISTS idx_properties_core_just_value ON florida_properties_core(just_value) WHERE just_value > 0;
CREATE INDEX IF NOT EXISTS idx_properties_core_use_code ON florida_properties_core(dor_use_code);
CREATE INDEX IF NOT EXISTS idx_properties_core_neighborhood ON florida_properties_core(neighborhood_code);

-- Valuation indexes
CREATE INDEX IF NOT EXISTS idx_valuations_parcel_id ON property_valuations(parcel_id);
CREATE INDEX IF NOT EXISTS idx_valuations_just_value ON property_valuations(just_value) WHERE just_value > 0;

-- Sales indexes
CREATE INDEX IF NOT EXISTS idx_sales_parcel_id ON property_sales_enhanced(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sales_latest_date ON property_sales_enhanced(latest_sale_date) WHERE latest_sale_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sales_latest_price ON property_sales_enhanced(latest_sale_price) WHERE latest_sale_price > 0;

-- Exemption indexes
CREATE INDEX IF NOT EXISTS idx_exemptions_parcel_id ON property_exemptions(parcel_id);
CREATE INDEX IF NOT EXISTS idx_exemptions_homestead ON property_exemptions(homestead_exemption) WHERE homestead_exemption > 0;

-- Enable RLS
ALTER TABLE florida_properties_core ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_valuations ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_exemptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_characteristics ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_enhanced ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_admin_data ENABLE ROW LEVEL SECURITY;

-- Public read policies
CREATE POLICY IF NOT EXISTS "Public read access" ON florida_properties_core FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_valuations FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_exemptions FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_characteristics FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_sales_enhanced FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_addresses FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_admin_data FOR SELECT USING (true);
