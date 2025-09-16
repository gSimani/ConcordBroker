# Supabase Sunbiz Integration - Complete Implementation Plan

## Executive Summary
Transform Supabase into a high-performance business entity search engine with 10+ million Florida corporation records, enabling real-time fuzzy matching, entity relationship mapping, and property ownership tracking.

## 1. DATA LOADING (Currently In Progress)
### Current Status
- **Loading**: 16GB Sunbiz dataset (3,757 files)
- **Progress**: 55,437+ corporations loaded (26 of 3,757 files)
- **Target**: ~10 million corporations, 500k+ fictitious names, 100k+ agents

### Data Sources Being Loaded
```
C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\
├── cor/     # 16GB - Corporation files (main dataset)
├── fic/     # 13MB - Fictitious names  
├── AG/      # 666MB - Registered agents
├── lien/    # Liens (if available)
└── part/    # Partnerships (if available)
```

## 2. DATABASE SCHEMA REQUIREMENTS

### Core Tables (Already Created)
```sql
-- SUNBIZ_CORPORATE (Main entity table)
CREATE TABLE sunbiz_corporate (
    doc_number VARCHAR(12) PRIMARY KEY,  -- Unique identifier
    entity_name VARCHAR(255) NOT NULL,   -- Corporation name
    status VARCHAR(10),                  -- ACTIVE/INACTIVE
    filing_date DATE,                     -- Date incorporated
    state_country VARCHAR(2),            -- State of incorporation
    prin_addr1 VARCHAR(100),             -- Principal address
    prin_city VARCHAR(50),
    prin_state VARCHAR(2),
    prin_zip VARCHAR(10),
    mail_addr1 VARCHAR(100),             -- Mailing address
    mail_city VARCHAR(50),
    mail_state VARCHAR(2),
    mail_zip VARCHAR(10),
    ein VARCHAR(20),                     -- Federal EIN
    registered_agent VARCHAR(100),       -- Agent name
    file_type VARCHAR(10),               -- Corporation type
    subtype VARCHAR(50),
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW()
);

-- SUNBIZ_FICTITIOUS (DBA names)
CREATE TABLE sunbiz_fictitious (
    doc_number VARCHAR(12) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,          -- Fictitious name
    owner_name VARCHAR(100),             -- Actual owner
    owner_city VARCHAR(50),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    filing_date DATE,
    expiration_date DATE,
    status VARCHAR(10),
    import_date TIMESTAMP DEFAULT NOW()
);

-- SUNBIZ_AGENTS (Registered agents)
CREATE TABLE sunbiz_agents (
    agent_id SERIAL PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    agent_address VARCHAR(255),
    agent_city VARCHAR(50),
    agent_state VARCHAR(2),
    agent_zip VARCHAR(10),
    entity_count INTEGER DEFAULT 0,      -- Number of entities represented
    import_date TIMESTAMP DEFAULT NOW()
);
```

### Relationship Tables
```sql
-- ENTITY_PROPERTY_MATCHES (Links corporations to properties)
CREATE TABLE entity_property_matches (
    match_id SERIAL PRIMARY KEY,
    doc_number VARCHAR(12),              -- Sunbiz entity
    property_id VARCHAR(50),             -- Property parcel ID
    match_type VARCHAR(20),              -- EXACT/FUZZY/PARTIAL
    match_score DECIMAL(3,2),            -- Confidence 0.00-1.00
    match_field VARCHAR(50),             -- Which field matched
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (doc_number) REFERENCES sunbiz_corporate(doc_number)
);

-- ENTITY_RELATIONSHIPS (Corporate connections)
CREATE TABLE entity_relationships (
    relationship_id SERIAL PRIMARY KEY,
    parent_doc VARCHAR(12),              -- Parent entity
    child_doc VARCHAR(12),               -- Child/related entity
    relationship_type VARCHAR(50),       -- SUBSIDIARY/DBA/AGENT/OFFICER
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 3. SEARCH & INDEXING REQUIREMENTS

### Text Search Extensions
```sql
-- Enable fuzzy matching capabilities
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- Trigram similarity
CREATE EXTENSION IF NOT EXISTS unaccent;     -- Accent removal
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch; -- Soundex, Levenshtein
```

### Performance Indexes Needed
```sql
-- PRIMARY SEARCH INDEXES (GIN for text search)
CREATE INDEX idx_corporate_name_trgm 
    ON sunbiz_corporate USING gin(entity_name gin_trgm_ops);

CREATE INDEX idx_corporate_agent_trgm 
    ON sunbiz_corporate USING gin(registered_agent gin_trgm_ops);

CREATE INDEX idx_fictitious_name_trgm 
    ON sunbiz_fictitious USING gin(name gin_trgm_ops);

CREATE INDEX idx_fictitious_owner_trgm 
    ON sunbiz_fictitious USING gin(owner_name gin_trgm_ops);

-- FILTERING INDEXES (B-tree for exact matches)
CREATE INDEX idx_corporate_status ON sunbiz_corporate(status);
CREATE INDEX idx_corporate_filing_date ON sunbiz_corporate(filing_date DESC);
CREATE INDEX idx_corporate_state ON sunbiz_corporate(state_country);
CREATE INDEX idx_corporate_zip ON sunbiz_corporate(prin_zip);
CREATE INDEX idx_corporate_city ON sunbiz_corporate(prin_city);

-- COMPOSITE INDEXES (Common query patterns)
CREATE INDEX idx_corporate_active_recent 
    ON sunbiz_corporate(status, filing_date DESC) 
    WHERE status = 'ACTIVE';

CREATE INDEX idx_corporate_fl_active 
    ON sunbiz_corporate(state_country, status) 
    WHERE state_country = 'FL' AND status = 'ACTIVE';
```

## 4. SEARCH FUNCTIONS & PROCEDURES

### Fuzzy Entity Search Function
```sql
CREATE OR REPLACE FUNCTION search_entities(
    search_term TEXT,
    threshold FLOAT DEFAULT 0.3,
    max_results INT DEFAULT 100
)
RETURNS TABLE (
    doc_number VARCHAR,
    entity_name VARCHAR,
    entity_type VARCHAR,
    status VARCHAR,
    match_score FLOAT,
    match_source VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    -- Search corporations
    SELECT 
        c.doc_number,
        c.entity_name,
        'CORPORATION' as entity_type,
        c.status,
        similarity(c.entity_name, search_term) as match_score,
        'entity_name' as match_source
    FROM sunbiz_corporate c
    WHERE c.entity_name % search_term
    
    UNION ALL
    
    -- Search fictitious names
    SELECT 
        f.doc_number,
        f.name as entity_name,
        'FICTITIOUS' as entity_type,
        f.status,
        similarity(f.name, search_term) as match_score,
        'fictitious_name' as match_source
    FROM sunbiz_fictitious f
    WHERE f.name % search_term
    
    UNION ALL
    
    -- Search by registered agent
    SELECT 
        c.doc_number,
        c.entity_name,
        'CORPORATION' as entity_type,
        c.status,
        similarity(c.registered_agent, search_term) as match_score,
        'registered_agent' as match_source
    FROM sunbiz_corporate c
    WHERE c.registered_agent % search_term
    
    ORDER BY match_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
```

### Property-Entity Matching Function
```sql
CREATE OR REPLACE FUNCTION match_property_to_entities(
    property_owner TEXT,
    property_address TEXT
)
RETURNS TABLE (
    doc_number VARCHAR,
    entity_name VARCHAR,
    match_type VARCHAR,
    confidence FLOAT
) AS $$
BEGIN
    RETURN QUERY
    -- Exact name match
    SELECT 
        c.doc_number,
        c.entity_name,
        'EXACT_NAME' as match_type,
        1.0 as confidence
    FROM sunbiz_corporate c
    WHERE UPPER(c.entity_name) = UPPER(property_owner)
    
    UNION ALL
    
    -- Fuzzy name match
    SELECT 
        c.doc_number,
        c.entity_name,
        'FUZZY_NAME' as match_type,
        similarity(c.entity_name, property_owner) as confidence
    FROM sunbiz_corporate c
    WHERE c.entity_name % property_owner
    AND similarity(c.entity_name, property_owner) > 0.6
    
    UNION ALL
    
    -- Address match
    SELECT 
        c.doc_number,
        c.entity_name,
        'ADDRESS' as match_type,
        0.8 as confidence
    FROM sunbiz_corporate c
    WHERE c.prin_addr1 ILIKE '%' || property_address || '%'
    
    ORDER BY confidence DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;
```

## 5. MATERIALIZED VIEWS FOR PERFORMANCE

### Active Florida Corporations View
```sql
CREATE MATERIALIZED VIEW mv_active_fl_corporations AS
SELECT 
    doc_number,
    entity_name,
    status,
    filing_date,
    prin_city,
    prin_zip,
    registered_agent,
    ein
FROM sunbiz_corporate
WHERE status = 'ACTIVE' 
    AND state_country = 'FL'
WITH DATA;

CREATE INDEX idx_mv_active_name ON mv_active_fl_corporations(entity_name);
CREATE INDEX idx_mv_active_city ON mv_active_fl_corporations(prin_city);
```

### Entity Statistics View
```sql
CREATE MATERIALIZED VIEW mv_entity_statistics AS
SELECT 
    DATE_TRUNC('month', filing_date) as month,
    status,
    state_country,
    COUNT(*) as entity_count,
    COUNT(DISTINCT registered_agent) as unique_agents
FROM sunbiz_corporate
WHERE filing_date IS NOT NULL
GROUP BY DATE_TRUNC('month', filing_date), status, state_country
WITH DATA;
```

## 6. ROW-LEVEL SECURITY POLICIES

### Public Read Access
```sql
-- Enable RLS
ALTER TABLE sunbiz_corporate ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_fictitious ENABLE ROW LEVEL SECURITY;

-- Public read for all authenticated users
CREATE POLICY "Public read access" ON sunbiz_corporate
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Public read access" ON sunbiz_fictitious
    FOR SELECT TO authenticated
    USING (true);

-- Admin write access
CREATE POLICY "Admin write access" ON sunbiz_corporate
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);
```

## 7. API ENDPOINTS NEEDED

### RESTful Endpoints via PostgREST
```javascript
// Search entities
GET /rest/v1/rpc/search_entities?search_term=CONCORD&threshold=0.3

// Get entity details
GET /rest/v1/sunbiz_corporate?doc_number=eq.P20000012345

// Get entities by address
GET /rest/v1/sunbiz_corporate?prin_city=eq.BOCA RATON&status=eq.ACTIVE

// Get fictitious names for entity
GET /rest/v1/sunbiz_fictitious?owner_name=ilike.%CONCORD%

// Match property to entities
POST /rest/v1/rpc/match_property_to_entities
{
    "property_owner": "CONCORD BROKER LLC",
    "property_address": "123 MAIN ST"
}
```

## 8. PERFORMANCE OPTIMIZATIONS

### Database Configuration
```sql
-- Optimize for read-heavy workload
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET work_mem = '256MB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';

-- Parallel query execution
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;

-- Optimize for SSD storage
ALTER SYSTEM SET random_page_cost = 1.1;
```

### Table Partitioning (for scale)
```sql
-- Partition corporations by year for better performance
CREATE TABLE sunbiz_corporate_partitioned (
    LIKE sunbiz_corporate INCLUDING ALL
) PARTITION BY RANGE (filing_date);

CREATE TABLE sunbiz_corporate_2025 
    PARTITION OF sunbiz_corporate_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE sunbiz_corporate_2024
    PARTITION OF sunbiz_corporate_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

## 9. MONITORING & MAINTENANCE

### Query Performance Monitoring
```sql
-- Track slow queries
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Monitor table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public' AND tablename LIKE 'sunbiz%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Maintenance Tasks
```sql
-- Weekly maintenance
VACUUM ANALYZE sunbiz_corporate;
VACUUM ANALYZE sunbiz_fictitious;

-- Monthly refresh of materialized views
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_active_fl_corporations;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_entity_statistics;

-- Quarterly REINDEX for optimal performance
REINDEX TABLE CONCURRENTLY sunbiz_corporate;
```

## 10. INTEGRATION WITH PROPERTY SYSTEM

### Cross-Database Queries
```sql
-- Find all properties owned by active corporations
SELECT 
    p.*,
    c.entity_name,
    c.status,
    c.filing_date
FROM florida_parcels p
JOIN entity_property_matches m ON p.parcel_id = m.property_id
JOIN sunbiz_corporate c ON m.doc_number = c.doc_number
WHERE c.status = 'ACTIVE'
    AND m.match_score > 0.8;

-- Find tax deed properties with corporate owners
SELECT 
    t.*,
    c.entity_name,
    c.registered_agent
FROM tax_deed_sales t
JOIN entity_property_matches m ON t.parcel_id = m.property_id
JOIN sunbiz_corporate c ON m.doc_number = c.doc_number
WHERE t.auction_date >= CURRENT_DATE
ORDER BY t.auction_date;
```

## IMMEDIATE NEXT STEPS

1. **Complete Data Loading** (In Progress)
   - Monitor current load: ~55k records loaded
   - Estimated completion: 4-6 hours for full dataset

2. **Run Post-Load Optimization** (Ready)
   - Execute `sunbiz_post_load_optimize.sql`
   - Creates all indexes and runs ANALYZE

3. **Test Search Performance**
   - Verify fuzzy search < 100ms
   - Test entity-property matching

4. **Create API Functions**
   - Deploy search functions
   - Set up materialized views

5. **Enable Production Access**
   - Configure RLS policies
   - Set up API endpoints

## SUCCESS METRICS

- **Search Performance**: < 100ms for fuzzy name searches
- **Data Completeness**: 10M+ corporations, 500k+ fictitious names
- **Match Accuracy**: > 90% accuracy on entity-property matching
- **API Response**: < 200ms for all endpoints
- **Uptime**: 99.9% availability

## ESTIMATED TIMELINE

- **Hour 1-6**: Complete data loading (current)
- **Hour 7**: Run post-load optimizations
- **Hour 8**: Test and validate search
- **Hour 9**: Deploy API functions
- **Hour 10**: Production ready

This comprehensive plan transforms your Supabase instance into a powerful business entity search engine with property matching capabilities.