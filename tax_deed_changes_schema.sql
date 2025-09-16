-- Tax Deed Changes Tracking Table
-- Stores all detected changes in tax deed auctions for audit and notification purposes

CREATE TABLE IF NOT EXISTS tax_deed_changes (
    id SERIAL PRIMARY KEY,
    change_type VARCHAR(50) NOT NULL, -- status_change, bid_change, date_change, etc.
    auction_id VARCHAR(100) NOT NULL,
    parcel_id VARCHAR(100), -- For item-level changes
    old_value TEXT, -- JSON string of old value
    new_value TEXT, -- JSON string of new value
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    details JSONB, -- Additional change details
    priority INTEGER NOT NULL DEFAULT 3, -- 1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW
    alert_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tax_deed_changes_auction_id ON tax_deed_changes(auction_id);
CREATE INDEX IF NOT EXISTS idx_tax_deed_changes_change_type ON tax_deed_changes(change_type);
CREATE INDEX IF NOT EXISTS idx_tax_deed_changes_detected_at ON tax_deed_changes(detected_at);
CREATE INDEX IF NOT EXISTS idx_tax_deed_changes_priority ON tax_deed_changes(priority);
CREATE INDEX IF NOT EXISTS idx_tax_deed_changes_parcel_id ON tax_deed_changes(parcel_id) WHERE parcel_id IS NOT NULL;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_tax_deed_changes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tax_deed_changes_updated_at
    BEFORE UPDATE ON tax_deed_changes
    FOR EACH ROW
    EXECUTE FUNCTION update_tax_deed_changes_updated_at();

-- Tax Deed Monitoring Status Table
-- Tracks monitoring system status and performance
CREATE TABLE IF NOT EXISTS tax_deed_monitoring_status (
    id SERIAL PRIMARY KEY,
    monitor_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, -- running, stopped, error
    last_check TIMESTAMP WITH TIME ZONE,
    last_deep_check TIMESTAMP WITH TIME ZONE,
    checks_performed INTEGER DEFAULT 0,
    changes_detected INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    performance_metrics JSONB, -- Timing, success rates, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint on monitor_name
CREATE UNIQUE INDEX IF NOT EXISTS idx_tax_deed_monitoring_status_name ON tax_deed_monitoring_status(monitor_name);

-- Create updated_at trigger for monitoring status
CREATE TRIGGER update_tax_deed_monitoring_status_updated_at
    BEFORE UPDATE ON tax_deed_monitoring_status
    FOR EACH ROW
    EXECUTE FUNCTION update_tax_deed_changes_updated_at();

-- Tax Deed Data Sources Configuration
-- Stores configuration for different data sources
CREATE TABLE IF NOT EXISTS tax_deed_data_sources (
    id SERIAL PRIMARY KEY,
    county VARCHAR(100) NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- api, web_scraping, file_feed
    base_url VARCHAR(500),
    api_endpoints JSONB, -- API endpoint configurations
    scraping_config JSONB, -- Web scraping configurations
    update_frequency INTEGER DEFAULT 300, -- seconds
    priority INTEGER DEFAULT 3, -- monitoring priority
    active BOOLEAN DEFAULT TRUE,
    last_successful_check TIMESTAMP WITH TIME ZONE,
    last_error TIMESTAMP WITH TIME ZONE,
    error_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 100.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint on county + source_name
CREATE UNIQUE INDEX IF NOT EXISTS idx_tax_deed_data_sources_unique ON tax_deed_data_sources(county, source_name);

-- Create updated_at trigger for data sources
CREATE TRIGGER update_tax_deed_data_sources_updated_at
    BEFORE UPDATE ON tax_deed_data_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_tax_deed_changes_updated_at();

-- Insert default data sources
INSERT INTO tax_deed_data_sources (county, source_name, source_type, base_url, api_endpoints, scraping_config, update_frequency) 
VALUES 
(
    'broward',
    'broward_deed_auction',
    'web_scraping',
    'https://broward.deedauction.net',
    '{"auctions": "/api/auctions", "auction_detail": "/api/auction/{id}"}',
    '{"auction_list_selector": ".auction-card", "item_selector": ".auction-item", "status_selector": ".status"}',
    30
),
(
    'miami-dade',
    'miami_property_search',
    'web_scraping', 
    'https://www.miamidade.gov/propertysearch/',
    '{}',
    '{"auction_selector": ".tax-deed-auction"}',
    60
)
ON CONFLICT (county, source_name) DO NOTHING;

-- Create view for recent changes with priority
CREATE OR REPLACE VIEW tax_deed_recent_changes AS
SELECT 
    c.*,
    CASE 
        WHEN c.change_type IN ('cancelled', 'postponed') THEN 'CRITICAL'
        WHEN c.change_type IN ('status_change', 'date_change') THEN 'HIGH'
        WHEN c.change_type = 'bid_change' THEN 'MEDIUM'
        ELSE 'NORMAL'
    END as priority_label,
    a.description as auction_description,
    a.auction_date,
    EXTRACT(EPOCH FROM (NOW() - c.detected_at)) / 3600 as hours_since_detected
FROM tax_deed_changes c
LEFT JOIN tax_deed_auctions a ON a.id::text = c.auction_id
WHERE c.detected_at >= NOW() - INTERVAL '24 hours'
ORDER BY c.priority ASC, c.detected_at DESC;

-- Grant permissions
-- Note: Adjust these permissions based on your security requirements
GRANT SELECT, INSERT, UPDATE ON tax_deed_changes TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON tax_deed_monitoring_status TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON tax_deed_data_sources TO PUBLIC;
GRANT USAGE ON SEQUENCE tax_deed_changes_id_seq TO PUBLIC;
GRANT USAGE ON SEQUENCE tax_deed_monitoring_status_id_seq TO PUBLIC;
GRANT USAGE ON SEQUENCE tax_deed_data_sources_id_seq TO PUBLIC;