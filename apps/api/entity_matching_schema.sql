-- Schema for Property-Entity Matching System
-- Links Florida Property Appraiser data with Sunbiz business entities

-- Property-Entity Match Table
CREATE TABLE IF NOT EXISTS property_entity_matches (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    owner_name VARCHAR(255),
    
    -- Matched entity information
    entity_doc_number VARCHAR(12) NOT NULL,
    entity_name VARCHAR(200),
    entity_type VARCHAR(20), -- corporate, fictitious, partnership, mark
    
    -- Match quality metrics
    confidence_score FLOAT, -- 0-100
    match_type VARCHAR(50), -- exact, fuzzy, pattern, address, agent, individual_owner
    match_metadata JSONB, -- Additional match details
    
    -- Verification status
    verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(100),
    verified_date TIMESTAMP,
    verification_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    
    -- Indexes
    UNIQUE(parcel_id, entity_doc_number)
);

CREATE INDEX idx_match_parcel ON property_entity_matches(parcel_id);
CREATE INDEX idx_match_entity ON property_entity_matches(entity_doc_number);
CREATE INDEX idx_match_confidence ON property_entity_matches(confidence_score DESC);
CREATE INDEX idx_match_type ON property_entity_matches(match_type);
CREATE INDEX idx_match_verified ON property_entity_matches(verified);

-- Entity Portfolio Summary Table (Materialized View)
CREATE MATERIALIZED VIEW IF NOT EXISTS entity_portfolio_summary AS
SELECT 
    pem.entity_doc_number,
    pem.entity_name,
    pem.entity_type,
    COUNT(DISTINCT fp.parcel_id) as property_count,
    COUNT(DISTINCT fp.phy_city) as city_count,
    SUM(fp.taxable_value) as total_portfolio_value,
    SUM(fp.land_value) as total_land_value,
    SUM(fp.building_value) as total_building_value,
    SUM(fp.total_living_area) as total_sqft,
    AVG(fp.taxable_value) as avg_property_value,
    MAX(fp.sale_date) as last_acquisition_date,
    MIN(fp.year_built) as oldest_property_year,
    MAX(fp.year_built) as newest_property_year,
    STRING_AGG(DISTINCT fp.phy_city, ', ' ORDER BY fp.phy_city) as cities,
    COUNT(CASE WHEN fp.property_use LIKE '0%' THEN 1 END) as residential_count,
    COUNT(CASE WHEN fp.property_use LIKE '1%' THEN 1 END) as commercial_count,
    MAX(pem.confidence_score) as max_confidence,
    AVG(pem.confidence_score) as avg_confidence
FROM property_entity_matches pem
JOIN florida_parcels fp ON pem.parcel_id = fp.parcel_id
WHERE pem.confidence_score >= 70 -- Only high-confidence matches
GROUP BY pem.entity_doc_number, pem.entity_name, pem.entity_type;

CREATE UNIQUE INDEX idx_portfolio_entity ON entity_portfolio_summary(entity_doc_number);
CREATE INDEX idx_portfolio_value ON entity_portfolio_summary(total_portfolio_value DESC);
CREATE INDEX idx_portfolio_count ON entity_portfolio_summary(property_count DESC);

-- Entity Relationship Network
CREATE TABLE IF NOT EXISTS entity_relationships (
    id BIGSERIAL PRIMARY KEY,
    entity1_doc_number VARCHAR(12) NOT NULL,
    entity1_name VARCHAR(200),
    entity2_doc_number VARCHAR(12) NOT NULL,
    entity2_name VARCHAR(200),
    relationship_type VARCHAR(50), -- same_agent, same_address, same_owner, subsidiary
    relationship_metadata JSONB,
    confidence_score FLOAT,
    discovered_date TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(entity1_doc_number, entity2_doc_number, relationship_type)
);

CREATE INDEX idx_rel_entity1 ON entity_relationships(entity1_doc_number);
CREATE INDEX idx_rel_entity2 ON entity_relationships(entity2_doc_number);
CREATE INDEX idx_rel_type ON entity_relationships(relationship_type);

-- Property Ownership History (tracking entity changes)
CREATE TABLE IF NOT EXISTS property_ownership_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    
    -- Previous owner
    prev_owner_name VARCHAR(255),
    prev_entity_doc_number VARCHAR(12),
    
    -- New owner
    new_owner_name VARCHAR(255),
    new_entity_doc_number VARCHAR(12),
    
    -- Transaction details
    change_date DATE,
    sale_price DECIMAL(15,2),
    deed_type VARCHAR(50),
    
    -- Source
    data_source VARCHAR(50),
    import_date TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_history_parcel ON property_ownership_history(parcel_id);
CREATE INDEX idx_history_date ON property_ownership_history(change_date DESC);

-- Match Audit Log
CREATE TABLE IF NOT EXISTS match_audit_log (
    id BIGSERIAL PRIMARY KEY,
    action VARCHAR(50), -- created, updated, verified, rejected
    parcel_id VARCHAR(50),
    entity_doc_number VARCHAR(12),
    old_confidence FLOAT,
    new_confidence FLOAT,
    old_match_type VARCHAR(50),
    new_match_type VARCHAR(50),
    user_id VARCHAR(100),
    notes TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Business Entity Cached Search
CREATE TABLE IF NOT EXISTS entity_search_cache (
    id BIGSERIAL PRIMARY KEY,
    normalized_name VARCHAR(500) UNIQUE,
    original_name VARCHAR(500),
    entity_doc_number VARCHAR(12),
    entity_type VARCHAR(20),
    is_active BOOLEAN,
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_search_normalized ON entity_search_cache(normalized_name);
CREATE INDEX idx_search_active ON entity_search_cache(is_active);

-- Functions for entity matching

-- Function to get entity portfolio
CREATE OR REPLACE FUNCTION get_entity_portfolio(p_doc_number VARCHAR)
RETURNS TABLE(
    parcel_id VARCHAR,
    address TEXT,
    city VARCHAR,
    value DECIMAL,
    sqft FLOAT,
    year_built INTEGER,
    confidence FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fp.parcel_id,
        fp.phy_addr1::TEXT as address,
        fp.phy_city,
        fp.taxable_value,
        fp.total_living_area,
        fp.year_built,
        pem.confidence_score
    FROM property_entity_matches pem
    JOIN florida_parcels fp ON pem.parcel_id = fp.parcel_id
    WHERE pem.entity_doc_number = p_doc_number
    AND pem.confidence_score >= 60
    ORDER BY fp.taxable_value DESC;
END;
$$;

-- Function to find property connections
CREATE OR REPLACE FUNCTION find_property_connections(p_parcel_id VARCHAR)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'primary_entity', (
            SELECT json_build_object(
                'doc_number', entity_doc_number,
                'name', entity_name,
                'type', entity_type,
                'confidence', confidence_score,
                'match_type', match_type
            )
            FROM property_entity_matches
            WHERE parcel_id = p_parcel_id
            ORDER BY confidence_score DESC
            LIMIT 1
        ),
        'all_matches', (
            SELECT json_agg(
                json_build_object(
                    'doc_number', entity_doc_number,
                    'name', entity_name,
                    'type', entity_type,
                    'confidence', confidence_score,
                    'match_type', match_type
                )
            )
            FROM property_entity_matches
            WHERE parcel_id = p_parcel_id
            AND confidence_score >= 50
            ORDER BY confidence_score DESC
        ),
        'related_properties', (
            SELECT json_agg(DISTINCT fp.phy_addr1)
            FROM property_entity_matches pem1
            JOIN property_entity_matches pem2 ON pem1.entity_doc_number = pem2.entity_doc_number
            JOIN florida_parcels fp ON pem2.parcel_id = fp.parcel_id
            WHERE pem1.parcel_id = p_parcel_id
            AND pem2.parcel_id != p_parcel_id
            LIMIT 10
        )
    ) INTO result;
    
    RETURN result;
END;
$$;

-- Function to calculate entity influence score
CREATE OR REPLACE FUNCTION calculate_entity_influence(p_doc_number VARCHAR)
RETURNS FLOAT
LANGUAGE plpgsql
AS $$
DECLARE
    influence_score FLOAT;
    property_value DECIMAL;
    property_count INTEGER;
    relationship_count INTEGER;
BEGIN
    -- Get portfolio metrics
    SELECT 
        COALESCE(SUM(fp.taxable_value), 0),
        COUNT(DISTINCT fp.parcel_id)
    INTO property_value, property_count
    FROM property_entity_matches pem
    JOIN florida_parcels fp ON pem.parcel_id = fp.parcel_id
    WHERE pem.entity_doc_number = p_doc_number;
    
    -- Get relationship count
    SELECT COUNT(*)
    INTO relationship_count
    FROM entity_relationships
    WHERE entity1_doc_number = p_doc_number
    OR entity2_doc_number = p_doc_number;
    
    -- Calculate influence score (0-100)
    influence_score := LEAST(100, 
        (property_count * 5) + -- Each property adds 5 points
        (property_value / 1000000) + -- Each million in value adds 1 point
        (relationship_count * 10) -- Each relationship adds 10 points
    );
    
    RETURN influence_score;
END;
$$;

-- Triggers

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_match_timestamp
    BEFORE UPDATE ON property_entity_matches
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Audit log trigger
CREATE OR REPLACE FUNCTION log_match_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO match_audit_log (
            action, parcel_id, entity_doc_number, 
            new_confidence, new_match_type
        ) VALUES (
            'created', NEW.parcel_id, NEW.entity_doc_number,
            NEW.confidence_score, NEW.match_type
        );
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.confidence_score != NEW.confidence_score OR OLD.match_type != NEW.match_type THEN
            INSERT INTO match_audit_log (
                action, parcel_id, entity_doc_number,
                old_confidence, new_confidence,
                old_match_type, new_match_type
            ) VALUES (
                'updated', NEW.parcel_id, NEW.entity_doc_number,
                OLD.confidence_score, NEW.confidence_score,
                OLD.match_type, NEW.match_type
            );
        END IF;
        
        IF OLD.verified != NEW.verified AND NEW.verified = TRUE THEN
            INSERT INTO match_audit_log (
                action, parcel_id, entity_doc_number,
                user_id, notes
            ) VALUES (
                'verified', NEW.parcel_id, NEW.entity_doc_number,
                NEW.verified_by, NEW.verification_notes
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_match_changes
    AFTER INSERT OR UPDATE ON property_entity_matches
    FOR EACH ROW
    EXECUTE FUNCTION log_match_changes();

-- Views for easy access

-- High confidence matches view
CREATE OR REPLACE VIEW high_confidence_matches AS
SELECT 
    pem.*,
    fp.phy_addr1,
    fp.phy_city,
    fp.taxable_value,
    sc.entity_name as sunbiz_entity_name,
    sc.status as entity_status
FROM property_entity_matches pem
JOIN florida_parcels fp ON pem.parcel_id = fp.parcel_id
LEFT JOIN sunbiz_corporate sc ON pem.entity_doc_number = sc.doc_number
WHERE pem.confidence_score >= 80
ORDER BY pem.confidence_score DESC;

-- Entity property network view
CREATE OR REPLACE VIEW entity_property_network AS
SELECT 
    e1.entity_doc_number,
    e1.entity_name,
    e1.property_count,
    e1.total_portfolio_value,
    COUNT(DISTINCT er.entity2_doc_number) as connected_entities,
    STRING_AGG(DISTINCT er.relationship_type, ', ') as relationship_types
FROM entity_portfolio_summary e1
LEFT JOIN entity_relationships er ON e1.entity_doc_number = er.entity1_doc_number
GROUP BY e1.entity_doc_number, e1.entity_name, e1.property_count, e1.total_portfolio_value
ORDER BY e1.total_portfolio_value DESC;

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Refresh materialized view periodically
-- Run this as a scheduled job
-- REFRESH MATERIALIZED VIEW CONCURRENTLY entity_portfolio_summary;