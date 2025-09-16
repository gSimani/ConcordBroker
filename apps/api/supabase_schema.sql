-- Supabase Schema for Florida Parcel Data
-- Run this in your Supabase SQL Editor

-- Enable PostGIS extension for spatial data
CREATE EXTENSION IF NOT EXISTS postgis;

-- Main parcels table
CREATE TABLE IF NOT EXISTS florida_parcels (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    
    -- Geometry stored as GeoJSON
    geometry JSONB,
    centroid JSONB,
    area_sqft FLOAT,
    perimeter_ft FLOAT,
    
    -- NAL attributes - Ownership
    owner_name VARCHAR(255),
    owner_addr1 VARCHAR(255),
    owner_addr2 VARCHAR(255),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    
    -- Physical address
    phy_addr1 VARCHAR(255),
    phy_addr2 VARCHAR(255),
    phy_city VARCHAR(100),
    phy_state VARCHAR(2) DEFAULT 'FL',
    phy_zipcd VARCHAR(10),
    
    -- Legal description
    legal_desc TEXT,
    subdivision VARCHAR(255),
    lot VARCHAR(50),
    block VARCHAR(50),
    
    -- Property characteristics
    property_use VARCHAR(10),
    property_use_desc VARCHAR(255),
    land_use_code VARCHAR(10),
    zoning VARCHAR(50),
    
    -- Valuations
    just_value FLOAT,
    assessed_value FLOAT,
    taxable_value FLOAT,
    land_value FLOAT,
    building_value FLOAT,
    
    -- Property details
    year_built INTEGER,
    total_living_area FLOAT,
    bedrooms INTEGER,
    bathrooms FLOAT,
    stories FLOAT,
    units INTEGER,
    
    -- Land measurements
    land_sqft FLOAT,
    land_acres FLOAT,
    
    -- Sales information
    sale_date TIMESTAMP,
    sale_price FLOAT,
    sale_qualification VARCHAR(10),
    
    -- Data quality flags
    match_status VARCHAR(20),
    discrepancy_reason VARCHAR(100),
    is_redacted BOOLEAN DEFAULT FALSE,
    data_source VARCHAR(20),
    
    -- Metadata
    import_date TIMESTAMP DEFAULT NOW(),
    update_date TIMESTAMP,
    data_hash VARCHAR(64),
    
    -- Unique constraint
    UNIQUE(parcel_id, county, year)
);

-- Indexes for performance
CREATE INDEX idx_parcels_county ON florida_parcels(county);
CREATE INDEX idx_parcels_year ON florida_parcels(year);
CREATE INDEX idx_parcels_owner ON florida_parcels(owner_name);
CREATE INDEX idx_parcels_address ON florida_parcels(phy_addr1, phy_city);
CREATE INDEX idx_parcels_value ON florida_parcels(taxable_value);
CREATE INDEX idx_parcels_sale ON florida_parcels(sale_date, sale_price);
CREATE INDEX idx_parcels_geometry ON florida_parcels USING GIN(geometry);

-- Condo units table
CREATE TABLE IF NOT EXISTS florida_condo_units (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    county VARCHAR(50),
    unit_number VARCHAR(50),
    floor INTEGER,
    building VARCHAR(50),
    unit_sqft FLOAT,
    unit_bedrooms INTEGER,
    unit_bathrooms FLOAT,
    unit_owner VARCHAR(255),
    unit_assessed_value FLOAT,
    unit_taxable_value FLOAT,
    import_date TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (parcel_id, county, year) REFERENCES florida_parcels(parcel_id, county, year)
);

-- Data source monitoring
CREATE TABLE IF NOT EXISTS data_source_monitor (
    id BIGSERIAL PRIMARY KEY,
    source_url TEXT NOT NULL UNIQUE,
    source_type VARCHAR(20),
    county VARCHAR(50),
    year INTEGER,
    file_name VARCHAR(255),
    file_size BIGINT,
    file_hash VARCHAR(64),
    last_modified TIMESTAMP,
    last_checked TIMESTAMP DEFAULT NOW(),
    last_downloaded TIMESTAMP,
    status VARCHAR(20),
    change_detected BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- Update history
CREATE TABLE IF NOT EXISTS parcel_update_history (
    id BIGSERIAL PRIMARY KEY,
    county VARCHAR(50),
    update_type VARCHAR(50),
    records_added INTEGER,
    records_updated INTEGER,
    records_deleted INTEGER,
    processing_time_seconds FLOAT,
    success BOOLEAN,
    error_message TEXT,
    update_date TIMESTAMP DEFAULT NOW()
);

-- Monitoring agents configuration
CREATE TABLE IF NOT EXISTS monitoring_agents (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL UNIQUE,
    agent_type VARCHAR(50),
    monitoring_urls JSONB,
    check_frequency_hours INTEGER DEFAULT 24,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    enabled BOOLEAN DEFAULT TRUE,
    notification_settings JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent activity logs
CREATE TABLE IF NOT EXISTS agent_activity_logs (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(100),
    activity_type VARCHAR(50),
    status VARCHAR(20),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE florida_condo_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_source_monitor ENABLE ROW LEVEL SECURITY;
ALTER TABLE parcel_update_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitoring_agents ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Public can read non-redacted parcels
CREATE POLICY "Public read non-redacted parcels" ON florida_parcels
    FOR SELECT
    USING (is_redacted = FALSE);

-- Authenticated users can read all parcels
CREATE POLICY "Authenticated read all parcels" ON florida_parcels
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Admin full access
CREATE POLICY "Admin full access parcels" ON florida_parcels
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'admin');

-- Public read access to monitoring status
CREATE POLICY "Public read monitoring" ON data_source_monitor
    FOR SELECT
    USING (true);

-- Admin can manage monitoring
CREATE POLICY "Admin manage monitoring" ON data_source_monitor
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'admin');

-- Create useful views

-- Latest parcel data per county
CREATE OR REPLACE VIEW latest_parcels AS
SELECT DISTINCT ON (parcel_id, county)
    *
FROM florida_parcels
ORDER BY parcel_id, county, year DESC;

-- Recent property sales
CREATE OR REPLACE VIEW recent_sales AS
SELECT 
    parcel_id,
    county,
    phy_addr1,
    phy_city,
    sale_date,
    sale_price,
    owner_name,
    taxable_value
FROM florida_parcels
WHERE sale_date >= CURRENT_DATE - INTERVAL '6 months'
    AND sale_price > 0
    AND is_redacted = FALSE
ORDER BY sale_date DESC;

-- High value properties
CREATE OR REPLACE VIEW high_value_properties AS
SELECT 
    parcel_id,
    county,
    phy_addr1,
    phy_city,
    owner_name,
    taxable_value,
    land_value,
    building_value,
    total_living_area
FROM florida_parcels
WHERE taxable_value > 1000000
    AND is_redacted = FALSE
ORDER BY taxable_value DESC;

-- Data quality dashboard
CREATE OR REPLACE VIEW data_quality_dashboard AS
SELECT 
    county,
    year,
    COUNT(*) as total_parcels,
    COUNT(CASE WHEN match_status = 'matched' THEN 1 END) as matched_count,
    COUNT(CASE WHEN match_status = 'polygon_only' THEN 1 END) as polygon_only_count,
    COUNT(CASE WHEN is_redacted THEN 1 END) as redacted_count,
    AVG(taxable_value) as avg_taxable_value,
    MAX(update_date) as last_updated
FROM florida_parcels
GROUP BY county, year
ORDER BY county, year DESC;

-- Monitoring status view
CREATE OR REPLACE VIEW monitoring_status AS
SELECT 
    ma.agent_name,
    ma.agent_type,
    ma.enabled,
    ma.last_run,
    ma.next_run,
    COUNT(dsm.id) as monitored_sources,
    SUM(CASE WHEN dsm.change_detected THEN 1 ELSE 0 END) as changes_detected
FROM monitoring_agents ma
LEFT JOIN data_source_monitor dsm ON true
GROUP BY ma.id, ma.agent_name, ma.agent_type, ma.enabled, ma.last_run, ma.next_run;

-- Create functions for monitoring

-- Function to check for data updates
CREATE OR REPLACE FUNCTION check_for_updates()
RETURNS TABLE(
    county VARCHAR,
    updates_available BOOLEAN,
    last_check TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dsm.county,
        dsm.change_detected as updates_available,
        dsm.last_checked as last_check
    FROM data_source_monitor dsm
    WHERE dsm.source_type = 'PAR'
    ORDER BY dsm.county;
END;
$$;

-- Function to get update statistics
CREATE OR REPLACE FUNCTION get_update_stats(p_county VARCHAR DEFAULT NULL)
RETURNS TABLE(
    total_updates INTEGER,
    successful_updates INTEGER,
    failed_updates INTEGER,
    total_records_added INTEGER,
    total_records_updated INTEGER,
    avg_processing_time FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_updates,
        SUM(CASE WHEN success THEN 1 ELSE 0 END)::INTEGER as successful_updates,
        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END)::INTEGER as failed_updates,
        SUM(records_added)::INTEGER as total_records_added,
        SUM(records_updated)::INTEGER as total_records_updated,
        AVG(processing_time_seconds)::FLOAT as avg_processing_time
    FROM parcel_update_history
    WHERE (p_county IS NULL OR county = p_county);
END;
$$;

-- Trigger to update the update_date on row changes
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_date = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_parcels_modtime 
    BEFORE UPDATE ON florida_parcels 
    FOR EACH ROW 
    EXECUTE FUNCTION update_modified_column();

-- Insert initial monitoring agents
INSERT INTO monitoring_agents (agent_name, agent_type, enabled, check_frequency_hours, notification_settings)
VALUES 
    ('Florida_PTO_Monitor', 'data_source', true, 24, 
     '{"email": "admin@westbocaexecutiveoffice.com", "on_change": true, "on_error": true}'::jsonb),
    
    ('Data_Quality_Agent', 'quality_check', true, 6,
     '{"thresholds": {"unmatched_ratio": 0.1, "invalid_geometry_ratio": 0.05}}'::jsonb),
    
    ('Update_Scheduler', 'scheduler', true, 1,
     '{"scheduled_times": ["02:00", "14:00"]}'::jsonb)
ON CONFLICT (agent_name) DO NOTHING;

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO authenticated;