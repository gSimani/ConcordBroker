-- =============================================================================
-- PROPERTY APPRAISER DATABASE SCHEMA FOR SUPABASE
-- =============================================================================
-- INSTRUCTIONS:
-- 1. Copy this entire SQL file
-- 2. Go to your Supabase Dashboard > SQL Editor
-- 3. Paste and execute this SQL
-- 4. Then run the Python data loading scripts
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Drop existing table if needed (CAUTION: This deletes all data!)
-- DROP TABLE IF EXISTS florida_parcels CASCADE;

-- =============================================================================
-- MAIN FLORIDA PARCELS TABLE
-- =============================================================================
-- This table consolidates data from NAL, NAP, NAV, SDF files per CLAUDE.md specs
-- Supports all 67 Florida counties with ~9.7M expected records

CREATE TABLE IF NOT EXISTS florida_parcels (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,

    -- Core identifiers (REQUIRED - per CLAUDE.md)
    parcel_id VARCHAR(50) NOT NULL,           -- Primary property identifier
    county VARCHAR(50) NOT NULL,             -- County name (UPPERCASE)
    year INTEGER NOT NULL DEFAULT 2025,       -- Tax assessment year

    -- =======================================================================
    -- NAL FILE DATA (Names and Addresses)
    -- Critical mappings from CLAUDE.md:
    -- LND_SQFOOT → land_sqft (NOT land_square_footage)
    -- PHY_ADDR1/PHY_ADDR2 → phy_addr1/phy_addr2 (NOT property_address)
    -- OWN_ADDR1/OWN_ADDR2 → owner_addr1/owner_addr2 (NOT owner_address)
    -- OWN_STATE → owner_state (truncate to 2 chars - "FLORIDA" → "FL")
    -- JV → just_value (NOT total_value)
    -- =======================================================================

    -- Property owner information
    owner_name VARCHAR(255),
    owner_addr1 VARCHAR(255),                 -- From OWN_ADDR1
    owner_addr2 VARCHAR(255),                 -- From OWN_ADDR2
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),                   -- CRITICAL: 2 chars only
    owner_zip VARCHAR(10),

    -- Physical property address
    phy_addr1 VARCHAR(255),                   -- From PHY_ADDR1
    phy_addr2 VARCHAR(255),                   -- From PHY_ADDR2
    phy_city VARCHAR(100),
    phy_state VARCHAR(2) DEFAULT 'FL',
    phy_zipcd VARCHAR(10),

    -- Legal description
    legal_desc TEXT,
    subdivision VARCHAR(255),
    lot VARCHAR(50),
    block VARCHAR(50),

    -- =======================================================================
    -- NAP FILE DATA (Property Characteristics)
    -- =======================================================================
    property_use VARCHAR(10),                 -- From DOR_UC
    property_use_desc VARCHAR(255),
    land_use_code VARCHAR(10),               -- From LND_USE_CD
    zoning VARCHAR(50),

    -- Building characteristics
    year_built INTEGER,                      -- From ACT_YR_BLT
    total_living_area FLOAT,                 -- From TOT_LVG_AREA
    bedrooms INTEGER,
    bathrooms FLOAT,
    stories FLOAT,
    units INTEGER,

    -- =======================================================================
    -- NAV FILE DATA (Property Values)
    -- =======================================================================
    just_value FLOAT,                        -- From JV (market value)
    assessed_value FLOAT,                    -- From AV
    taxable_value FLOAT,                     -- From TV
    land_value FLOAT,                        -- From LND_VAL
    building_value FLOAT,                    -- Calculated: just_value - land_value

    -- Land measurements
    land_sqft FLOAT,                         -- From LND_SQFOOT (CRITICAL MAPPING)
    land_acres FLOAT,

    -- =======================================================================
    -- SDF FILE DATA (Sales History)
    -- sale_date → Build from SALE_YR1/SALE_MO1 as YYYY-MM-01T00:00:00 or NULL
    -- NEVER use empty string for sale_date - use NULL
    -- =======================================================================
    sale_date TIMESTAMP,                     -- From SALE_YR1/SALE_MO1
    sale_price FLOAT,                        -- From SALE_PRC1
    sale_qualification VARCHAR(10),          -- From QUAL_CD1

    -- =======================================================================
    -- DATA QUALITY AND METADATA
    -- =======================================================================
    match_status VARCHAR(20),
    discrepancy_reason VARCHAR(100),
    is_redacted BOOLEAN DEFAULT FALSE,
    is_anomaly BOOLEAN DEFAULT FALSE,        -- For ML anomaly detection
    data_source VARCHAR(20),                 -- NAL, NAP, NAV, SDF

    -- Audit fields
    import_date TIMESTAMP DEFAULT NOW(),
    update_date TIMESTAMP,
    data_hash VARCHAR(64),                   -- For deduplication

    -- Spatial data (optional)
    geometry JSONB,                          -- GeoJSON format
    centroid JSONB,
    area_sqft FLOAT,
    perimeter_ft FLOAT,

    -- =======================================================================
    -- CONSTRAINTS
    -- =======================================================================
    CONSTRAINT uq_parcel_county_year UNIQUE (parcel_id, county, year)
);

-- =============================================================================
-- PERFORMANCE INDEXES (CRITICAL FOR 9.7M RECORDS)
-- =============================================================================

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_parcels_county ON florida_parcels(county);
CREATE INDEX IF NOT EXISTS idx_parcels_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_parcels_county_parcel ON florida_parcels(county, parcel_id);

-- Owner searches
CREATE INDEX IF NOT EXISTS idx_parcels_owner ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_parcels_owner_trigram ON florida_parcels USING gin(owner_name gin_trgm_ops);

-- Address searches
CREATE INDEX IF NOT EXISTS idx_parcels_phy_address ON florida_parcels(phy_addr1, phy_city);
CREATE INDEX IF NOT EXISTS idx_parcels_owner_address ON florida_parcels(owner_addr1, owner_city);

-- Value queries
CREATE INDEX IF NOT EXISTS idx_parcels_just_value ON florida_parcels(just_value) WHERE just_value > 0;
CREATE INDEX IF NOT EXISTS idx_parcels_taxable_value ON florida_parcels(taxable_value) WHERE taxable_value > 0;
CREATE INDEX IF NOT EXISTS idx_parcels_value_range ON florida_parcels(county, just_value) WHERE just_value > 0;

-- Sales queries
CREATE INDEX IF NOT EXISTS idx_parcels_sale_date ON florida_parcels(sale_date) WHERE sale_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_parcels_sale_price ON florida_parcels(sale_price) WHERE sale_price > 0;
CREATE INDEX IF NOT EXISTS idx_parcels_recent_sales ON florida_parcels(sale_date, sale_price) WHERE sale_date > '2020-01-01';

-- Property characteristics
CREATE INDEX IF NOT EXISTS idx_parcels_property_use ON florida_parcels(property_use);
CREATE INDEX IF NOT EXISTS idx_parcels_year_built ON florida_parcels(year_built) WHERE year_built > 1800;

-- Spatial indexes (if using geometry)
CREATE INDEX IF NOT EXISTS idx_parcels_geometry ON florida_parcels USING gin(geometry) WHERE geometry IS NOT NULL;

-- Data quality indexes
CREATE INDEX IF NOT EXISTS idx_parcels_import_date ON florida_parcels(import_date);
CREATE INDEX IF NOT EXISTS idx_parcels_data_source ON florida_parcels(data_source);

-- =============================================================================
-- SUPPORTING TABLES FOR ENHANCED FUNCTIONALITY
-- =============================================================================

-- Property use code lookup
CREATE TABLE IF NOT EXISTS property_use_codes (
    use_code VARCHAR(10) PRIMARY KEY,
    description VARCHAR(255),
    category VARCHAR(50),
    is_residential BOOLEAN DEFAULT FALSE,
    is_commercial BOOLEAN DEFAULT FALSE
);

-- County information
CREATE TABLE IF NOT EXISTS florida_counties (
    county_name VARCHAR(50) PRIMARY KEY,
    county_code VARCHAR(3),
    population INTEGER,
    area_sqmi FLOAT,
    property_appraiser_url VARCHAR(255),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Sales history (normalized from SDF data)
CREATE TABLE IF NOT EXISTS sales_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,
    sale_date DATE,
    sale_price FLOAT,
    qualification_code VARCHAR(10),
    deed_book VARCHAR(20),
    deed_page VARCHAR(20),
    grantor VARCHAR(255),
    grantee VARCHAR(255),
    sale_type VARCHAR(50),

    CONSTRAINT fk_sales_parcel FOREIGN KEY (parcel_id, county)
        REFERENCES florida_parcels(parcel_id, county)
);

CREATE INDEX IF NOT EXISTS idx_sales_parcel ON sales_history(parcel_id, county);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_history(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_price ON sales_history(sale_price) WHERE sale_price > 0;

-- =============================================================================
-- DATA VALIDATION FUNCTIONS
-- =============================================================================

-- Function to validate parcel ID format
CREATE OR REPLACE FUNCTION validate_parcel_id(pid VARCHAR(50))
RETURNS BOOLEAN AS $$
BEGIN
    -- Basic validation: not null, not empty, reasonable length
    RETURN pid IS NOT NULL AND LENGTH(TRIM(pid)) > 0 AND LENGTH(pid) <= 50;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate building value
CREATE OR REPLACE FUNCTION calculate_building_value()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate building_value = just_value - land_value (when both exist)
    IF NEW.just_value IS NOT NULL AND NEW.land_value IS NOT NULL THEN
        NEW.building_value = NEW.just_value - NEW.land_value;
        -- Ensure building value is not negative
        IF NEW.building_value < 0 THEN
            NEW.building_value = 0;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically calculate building value
CREATE TRIGGER trigger_calculate_building_value
    BEFORE INSERT OR UPDATE ON florida_parcels
    FOR EACH ROW
    EXECUTE FUNCTION calculate_building_value();

-- =============================================================================
-- ROW LEVEL SECURITY (Optional - enable if needed)
-- =============================================================================

-- Enable RLS on the table
-- ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users
-- CREATE POLICY "Allow authenticated users to view parcels" ON florida_parcels
--     FOR SELECT USING (auth.role() = 'authenticated');

-- =============================================================================
-- PERFORMANCE OPTIMIZATIONS FOR BULK LOADING
-- =============================================================================

-- Disable timeouts for bulk operations (temporary)
ALTER DATABASE postgres SET statement_timeout TO '0';

-- Increase work_mem for better sorting/indexing performance
ALTER DATABASE postgres SET work_mem TO '256MB';

-- Increase maintenance_work_mem for index creation
ALTER DATABASE postgres SET maintenance_work_mem TO '1GB';

-- =============================================================================
-- MONITORING AND ANALYTICS VIEWS
-- =============================================================================

-- County summary view
CREATE OR REPLACE VIEW county_property_summary AS
SELECT
    county,
    COUNT(*) as total_properties,
    COUNT(DISTINCT parcel_id) as unique_parcels,
    AVG(just_value) as avg_property_value,
    AVG(land_sqft) as avg_land_size,
    SUM(CASE WHEN sale_date IS NOT NULL THEN 1 ELSE 0 END) as properties_with_sales,
    MAX(import_date) as last_import_date
FROM florida_parcels
GROUP BY county
ORDER BY total_properties DESC;

-- Property value distribution view
CREATE OR REPLACE VIEW property_value_ranges AS
SELECT
    county,
    COUNT(CASE WHEN just_value < 100000 THEN 1 END) as under_100k,
    COUNT(CASE WHEN just_value BETWEEN 100000 AND 300000 THEN 1 END) as from_100k_300k,
    COUNT(CASE WHEN just_value BETWEEN 300000 AND 500000 THEN 1 END) as from_300k_500k,
    COUNT(CASE WHEN just_value BETWEEN 500000 AND 1000000 THEN 1 END) as from_500k_1m,
    COUNT(CASE WHEN just_value > 1000000 THEN 1 END) as over_1m
FROM florida_parcels
WHERE just_value > 0
GROUP BY county
ORDER BY county;

-- Data quality monitoring view
CREATE OR REPLACE VIEW data_quality_summary AS
SELECT
    county,
    COUNT(*) as total_records,
    ROUND(100.0 * SUM(CASE WHEN parcel_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_null_parcel_id,
    ROUND(100.0 * SUM(CASE WHEN owner_name IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_null_owner,
    ROUND(100.0 * SUM(CASE WHEN just_value IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_null_value,
    ROUND(100.0 * SUM(CASE WHEN phy_addr1 IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_null_address,
    MAX(import_date) as last_import
FROM florida_parcels
GROUP BY county
ORDER BY total_records DESC;

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'PROPERTY APPRAISER DATABASE SCHEMA DEPLOYMENT COMPLETE';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables Created:';
    RAISE NOTICE '• florida_parcels (main table for 9.7M properties)';
    RAISE NOTICE '• property_use_codes (lookup table)';
    RAISE NOTICE '• florida_counties (county metadata)';
    RAISE NOTICE '• sales_history (normalized sales data)';
    RAISE NOTICE '';
    RAISE NOTICE 'Indexes Created: 15+ performance indexes';
    RAISE NOTICE 'Views Created: 3 analytics/monitoring views';
    RAISE NOTICE 'Functions: 2 validation/calculation functions';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Run Python data loading scripts';
    RAISE NOTICE '2. Monitor import progress via views';
    RAISE NOTICE '3. Set up daily Florida Revenue portal monitoring';
    RAISE NOTICE '';
    RAISE NOTICE 'Expected Capacity: ~9,700,000 records from 67 counties';
    RAISE NOTICE 'File Types: NAL, NAP, NAV, SDF';
    RAISE NOTICE '';
    RAISE NOTICE '=================================================================';
END $$;

-- Verify table creation
SELECT
    table_name,
    CASE
        WHEN table_name = 'florida_parcels' THEN 'Main property data table - READY FOR LOADING'
        ELSE 'Supporting table'
    END as description
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('florida_parcels', 'property_use_codes', 'florida_counties', 'sales_history')
ORDER BY table_name;