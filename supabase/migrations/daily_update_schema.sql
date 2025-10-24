-- ============================================================================
-- Daily Property Update System - Complete Database Schema
-- Includes all tables for property data and change tracking
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ============================================================================
-- 1. FLORIDA PARCELS TABLE (Main Property Table - matches existing structure)
-- ============================================================================
CREATE TABLE IF NOT EXISTS florida_parcels (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,

    -- Owner Information
    owner_name VARCHAR(500),
    owner_addr1 VARCHAR(255),
    owner_addr2 VARCHAR(255),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),

    -- Property Location
    phy_addr1 VARCHAR(255),
    phy_addr2 VARCHAR(255),
    city VARCHAR(100),
    zip_code VARCHAR(10),

    -- Valuation
    just_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    land_value DECIMAL(15,2),
    building_value DECIMAL(15,2),
    land_sqft DECIMAL(15,2),

    -- Property Details
    dor_uc VARCHAR(10),  -- Property use code
    property_use VARCHAR(100),
    year_built INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),

    -- Metadata
    data_source VARCHAR(20) DEFAULT 'NAL',
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT unique_parcel_year UNIQUE(parcel_id, county, year)
);

-- Critical indexes for performance
CREATE INDEX IF NOT EXISTS idx_parcels_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_parcels_county ON florida_parcels(county);
CREATE INDEX IF NOT EXISTS idx_parcels_owner_name ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_parcels_city ON florida_parcels(city);
CREATE INDEX IF NOT EXISTS idx_parcels_last_updated ON florida_parcels(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_parcels_just_value ON florida_parcels(just_value);

-- ============================================================================
-- 2. PROPERTY SALES HISTORY TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS property_sales_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,

    -- Sale Details
    sale_date DATE,
    sale_price DECIMAL(15,2),
    sale_type VARCHAR(50),

    -- Parties
    seller_name VARCHAR(500),
    buyer_name VARCHAR(500),

    -- Recording
    deed_book VARCHAR(50),
    deed_page VARCHAR(50),
    or_book VARCHAR(50),  -- Official Record Book
    or_page VARCHAR(50),  -- Official Record Page
    instrument_number VARCHAR(50),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(20) DEFAULT 'SDF',

    CONSTRAINT unique_sale UNIQUE(parcel_id, county, sale_date, or_book, or_page)
);

CREATE INDEX IF NOT EXISTS idx_sales_parcel ON property_sales_history(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sales_date ON property_sales_history(sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_sales_price ON property_sales_history(sale_price);
CREATE INDEX IF NOT EXISTS idx_sales_county ON property_sales_history(county);

-- ============================================================================
-- 3. PROPERTY CHANGE LOG (NEW - Tracks Daily Changes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS property_change_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,
    change_date DATE NOT NULL,
    change_type VARCHAR(50) NOT NULL,  -- OWNERSHIP, VALUE, TAX, SALE, ADDRESS, NEW

    -- Change details (JSONB for flexibility)
    old_value JSONB,
    new_value JSONB,
    change_summary TEXT,

    -- Metadata
    detected_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    notification_sent BOOLEAN DEFAULT FALSE,

    -- Optional link to job that detected this
    job_id UUID
);

CREATE INDEX IF NOT EXISTS idx_change_parcel ON property_change_log(parcel_id);
CREATE INDEX IF NOT EXISTS idx_change_date ON property_change_log(change_date DESC);
CREATE INDEX IF NOT EXISTS idx_change_type ON property_change_log(change_type);
CREATE INDEX IF NOT EXISTS idx_change_processed ON property_change_log(processed);
CREATE INDEX IF NOT EXISTS idx_change_county ON property_change_log(county);

-- ============================================================================
-- 4. DATA UPDATE JOBS (NEW - Monitors Daily Update Jobs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_update_jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    job_date DATE NOT NULL,
    county VARCHAR(50),
    file_type VARCHAR(10),  -- NAL, NAP, NAV, SDF

    -- Job Status
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, RUNNING, COMPLETED, FAILED
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Results
    records_processed INTEGER DEFAULT 0,
    records_changed INTEGER DEFAULT 0,
    records_new INTEGER DEFAULT 0,
    records_error INTEGER DEFAULT 0,
    error_message TEXT,

    -- File info
    file_url TEXT,
    file_checksum VARCHAR(64),
    file_size_bytes BIGINT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_date ON data_update_jobs(job_date DESC);
CREATE INDEX IF NOT EXISTS idx_job_status ON data_update_jobs(status);
CREATE INDEX IF NOT EXISTS idx_job_county ON data_update_jobs(county);
CREATE INDEX IF NOT EXISTS idx_job_created ON data_update_jobs(created_at DESC);

-- ============================================================================
-- 5. FILE CHECKSUMS (NEW - Tracks File Changes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS file_checksums (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    county VARCHAR(50) NOT NULL,
    file_type VARCHAR(10) NOT NULL,  -- NAL, NAP, NAV, SDF
    year INTEGER NOT NULL,

    -- File information
    file_url TEXT,
    checksum VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT,
    last_modified TIMESTAMP,

    -- Metadata
    checked_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_file UNIQUE(county, file_type, year)
);

CREATE INDEX IF NOT EXISTS idx_checksum_county ON file_checksums(county);
CREATE INDEX IF NOT EXISTS idx_checksum_checked ON file_checksums(checked_at DESC);

-- ============================================================================
-- 6. PROPERTY MASTER VIEW (Simplified)
-- ============================================================================
CREATE OR REPLACE VIEW property_master AS
SELECT
    fp.id,
    fp.parcel_id,
    fp.county,
    fp.year,
    fp.owner_name,
    fp.phy_addr1 AS property_address,
    fp.city,
    fp.zip_code,
    fp.property_use,
    fp.just_value,
    fp.assessed_value,
    fp.taxable_value,
    fp.land_value,
    fp.building_value,
    fp.land_sqft,
    fp.year_built,
    fp.bedrooms,
    fp.bathrooms,
    fp.last_updated,

    -- Recent sale info
    (
        SELECT json_build_object(
            'sale_date', psh.sale_date,
            'sale_price', psh.sale_price,
            'buyer_name', psh.buyer_name
        )
        FROM property_sales_history psh
        WHERE psh.parcel_id = fp.parcel_id
        AND psh.county = fp.county
        ORDER BY psh.sale_date DESC
        LIMIT 1
    ) AS recent_sale,

    -- Change count
    (
        SELECT COUNT(*)
        FROM property_change_log pcl
        WHERE pcl.parcel_id = fp.parcel_id
        AND pcl.county = fp.county
        AND pcl.change_date >= CURRENT_DATE - INTERVAL '30 days'
    ) AS recent_changes_count

FROM florida_parcels fp;

-- ============================================================================
-- 7. UTILITY FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for florida_parcels
DROP TRIGGER IF EXISTS update_florida_parcels_timestamp ON florida_parcels;
CREATE TRIGGER update_florida_parcels_timestamp
    BEFORE UPDATE ON florida_parcels
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to get daily update statistics
CREATE OR REPLACE FUNCTION get_daily_update_stats(p_date DATE DEFAULT CURRENT_DATE)
RETURNS TABLE (
    total_jobs INTEGER,
    completed_jobs INTEGER,
    failed_jobs INTEGER,
    total_records_processed BIGINT,
    total_records_changed BIGINT,
    total_records_new BIGINT,
    total_records_error BIGINT,
    counties_processed TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER AS total_jobs,
        COUNT(*) FILTER (WHERE status = 'COMPLETED')::INTEGER AS completed_jobs,
        COUNT(*) FILTER (WHERE status = 'FAILED')::INTEGER AS failed_jobs,
        COALESCE(SUM(records_processed), 0) AS total_records_processed,
        COALESCE(SUM(records_changed), 0) AS total_records_changed,
        COALESCE(SUM(records_new), 0) AS total_records_new,
        COALESCE(SUM(records_error), 0) AS total_records_error,
        ARRAY_AGG(DISTINCT county) FILTER (WHERE county IS NOT NULL) AS counties_processed
    FROM data_update_jobs
    WHERE job_date = p_date;
END;
$$ LANGUAGE plpgsql;

-- Function to get county statistics
CREATE OR REPLACE FUNCTION get_county_stats(p_county VARCHAR)
RETURNS TABLE (
    total_properties BIGINT,
    total_sales BIGINT,
    avg_just_value NUMERIC,
    median_just_value NUMERIC,
    total_value NUMERIC,
    last_update TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT fp.parcel_id)::BIGINT AS total_properties,
        COUNT(DISTINCT psh.id)::BIGINT AS total_sales,
        ROUND(AVG(fp.just_value), 2) AS avg_just_value,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fp.just_value) AS median_just_value,
        ROUND(SUM(fp.just_value), 2) AS total_value,
        MAX(fp.last_updated) AS last_update
    FROM florida_parcels fp
    LEFT JOIN property_sales_history psh
        ON fp.parcel_id = psh.parcel_id
        AND fp.county = psh.county
    WHERE fp.county = p_county
    GROUP BY fp.county;
END;
$$ LANGUAGE plpgsql;

-- Function to log property change
CREATE OR REPLACE FUNCTION log_property_change(
    p_parcel_id VARCHAR,
    p_county VARCHAR,
    p_change_type VARCHAR,
    p_old_value JSONB,
    p_new_value JSONB,
    p_summary TEXT,
    p_job_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_change_id UUID;
BEGIN
    INSERT INTO property_change_log (
        parcel_id,
        county,
        change_date,
        change_type,
        old_value,
        new_value,
        change_summary,
        job_id
    ) VALUES (
        p_parcel_id,
        p_county,
        CURRENT_DATE,
        p_change_type,
        p_old_value,
        p_new_value,
        p_summary,
        p_job_id
    )
    RETURNING id INTO v_change_id;

    RETURN v_change_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 8. ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on tables
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_change_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_update_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_checksums ENABLE ROW LEVEL SECURITY;

-- Public read access for all users
CREATE POLICY "Enable read access for all" ON florida_parcels
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all" ON property_sales_history
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all" ON property_change_log
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all" ON data_update_jobs
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all" ON file_checksums
    FOR SELECT USING (true);

-- Service role can write (for daily updates)
CREATE POLICY "Enable insert for service role" ON florida_parcels
    FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'authenticated');

CREATE POLICY "Enable update for service role" ON florida_parcels
    FOR UPDATE USING (auth.role() = 'service_role' OR auth.role() = 'authenticated');

CREATE POLICY "Enable insert for service role" ON property_sales_history
    FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'authenticated');

CREATE POLICY "Enable insert for service role" ON property_change_log
    FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'authenticated');

CREATE POLICY "Enable insert for service role" ON data_update_jobs
    FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'authenticated');

CREATE POLICY "Enable update for service role" ON data_update_jobs
    FOR UPDATE USING (auth.role() = 'service_role' OR auth.role() = 'authenticated');

CREATE POLICY "Enable insert for service role" ON file_checksums
    FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'authenticated');

CREATE POLICY "Enable update for service role" ON file_checksums
    FOR UPDATE USING (auth.role() = 'service_role' OR auth.role() = 'authenticated');

-- ============================================================================
-- 9. INITIAL DATA
-- ============================================================================

-- Insert Florida counties reference data
CREATE TABLE IF NOT EXISTS florida_counties (
    code VARCHAR(5) PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    population INTEGER,
    is_priority BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO florida_counties (code, name, is_priority) VALUES
    ('01', 'ALACHUA', false),
    ('02', 'BAKER', false),
    ('03', 'BAY', false),
    ('04', 'BRADFORD', false),
    ('05', 'BREVARD', false),
    ('06', 'BROWARD', true),
    ('07', 'CALHOUN', false),
    ('08', 'CHARLOTTE', false),
    ('09', 'CITRUS', false),
    ('10', 'CLAY', false),
    ('11', 'COLLIER', false),
    ('12', 'COLUMBIA', false),
    ('13', 'DESOTO', false),
    ('14', 'DIXIE', false),
    ('15', 'DUVAL', true),
    ('16', 'ESCAMBIA', false),
    ('17', 'FLAGLER', false),
    ('18', 'FRANKLIN', false),
    ('19', 'GADSDEN', false),
    ('20', 'GILCHRIST', false),
    ('21', 'GLADES', false),
    ('22', 'GULF', false),
    ('23', 'HAMILTON', false),
    ('24', 'HARDEE', false),
    ('25', 'HENDRY', false),
    ('26', 'HERNANDO', false),
    ('27', 'HIGHLANDS', false),
    ('28', 'HILLSBOROUGH', true),
    ('29', 'HOLMES', false),
    ('30', 'INDIAN RIVER', false),
    ('31', 'JACKSON', false),
    ('32', 'JEFFERSON', false),
    ('33', 'LAFAYETTE', false),
    ('34', 'LAKE', false),
    ('35', 'LEE', false),
    ('36', 'LEON', false),
    ('37', 'LEVY', false),
    ('38', 'LIBERTY', false),
    ('39', 'MADISON', false),
    ('40', 'MANATEE', false),
    ('41', 'MARION', false),
    ('42', 'MARTIN', false),
    ('43', 'MIAMI-DADE', true),
    ('44', 'MONROE', false),
    ('45', 'NASSAU', false),
    ('46', 'OKALOOSA', false),
    ('47', 'OKEECHOBEE', false),
    ('48', 'ORANGE', true),
    ('49', 'OSCEOLA', false),
    ('50', 'PALM BEACH', true),
    ('51', 'PASCO', false),
    ('52', 'PINELLAS', false),
    ('53', 'POLK', false),
    ('54', 'PUTNAM', false),
    ('55', 'SANTA ROSA', false),
    ('56', 'SARASOTA', false),
    ('57', 'SEMINOLE', false),
    ('58', 'ST. JOHNS', false),
    ('59', 'ST. LUCIE', false),
    ('60', 'SUMTER', false),
    ('61', 'SUWANNEE', false),
    ('62', 'TAYLOR', false),
    ('63', 'UNION', false),
    ('64', 'VOLUSIA', false),
    ('65', 'WAKULLA', false),
    ('66', 'WALTON', false),
    ('67', 'WASHINGTON', false)
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- 10. PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Analyze tables for query optimization
ANALYZE florida_parcels;
ANALYZE property_sales_history;
ANALYZE property_change_log;
ANALYZE data_update_jobs;

-- ============================================================================
-- End of Daily Update Schema
-- ============================================================================

-- Print success message
DO $$
BEGIN
    RAISE NOTICE 'Daily Property Update Schema deployed successfully!';
    RAISE NOTICE 'Tables created: florida_parcels, property_sales_history, property_change_log, data_update_jobs, file_checksums, florida_counties';
    RAISE NOTICE 'Views created: property_master';
    RAISE NOTICE 'Functions created: get_daily_update_stats, get_county_stats, log_property_change';
END $$;
