# ConcordBroker Data Architecture & Optimization Plan

## Executive Summary

The ConcordBroker database is currently empty and requires a complete initialization with proper data architecture to handle large-scale Florida property data efficiently. This document outlines the complete data architecture, partitioning strategy, and implementation plan.

## Current State Analysis

### Database Status
- **Database Provider**: Supabase (PostgreSQL)
- **URL**: https://mogulpssjdlxjvstqfee.supabase.co
- **Current State**: EMPTY (0 tables exist)
- **Expected Data Volume**: 
  - ~600,000 Broward properties
  - ~1M+ Florida parcels
  - Millions of sales records
  - Extensive permit and business entity data

### Identified Issues
1. No tables currently exist in the database
2. Large data volumes require partitioning strategy
3. Need proper indexing for performance
4. Require materialized views for complex queries

## Data Architecture Strategy

### 1. Table Partitioning Strategy

#### Large Table Partitioning Plan

**PARCELS Table** (Expected: 1M+ records)
```sql
-- Partition by county_code (range partitioning)
CREATE TABLE parcels (
    id BIGSERIAL,
    parcel_id VARCHAR(50) NOT NULL,
    county_code VARCHAR(10) NOT NULL,
    -- other columns
) PARTITION BY RANGE (county_code);

-- Create partitions for major counties
CREATE TABLE parcels_broward PARTITION OF parcels 
    FOR VALUES FROM ('06') TO ('07');  -- Broward County

CREATE TABLE parcels_miami_dade PARTITION OF parcels 
    FOR VALUES FROM ('13') TO ('14');  -- Miami-Dade

CREATE TABLE parcels_palm_beach PARTITION OF parcels 
    FOR VALUES FROM ('50') TO ('51');  -- Palm Beach

CREATE TABLE parcels_other PARTITION OF parcels 
    DEFAULT;  -- All other counties
```

**SALES_HISTORY Table** (Expected: Millions of records)
```sql
-- Partition by sale_date (monthly partitions)
CREATE TABLE sales_history (
    id BIGSERIAL,
    parcel_id VARCHAR(50),
    sale_date DATE NOT NULL,
    -- other columns
) PARTITION BY RANGE (sale_date);

-- Create monthly partitions (automated via pg_partman)
-- Example for 2025:
CREATE TABLE sales_history_2025_01 PARTITION OF sales_history
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

**BUILDING_PERMITS Table** (Expected: 500K+ records)
```sql
-- Partition by issue_date (yearly)
CREATE TABLE building_permits (
    id BIGSERIAL,
    permit_number VARCHAR(50),
    issue_date DATE NOT NULL,
    -- other columns
) PARTITION BY RANGE (issue_date);
```

### 2. Indexing Strategy

#### Primary Indexes (Critical for Performance)
```sql
-- Parcels table indexes
CREATE INDEX idx_parcels_parcel_id ON parcels(parcel_id);
CREATE INDEX idx_parcels_county_owner ON parcels(county_code, owner_name);
CREATE INDEX idx_parcels_address ON parcels USING GIN(to_tsvector('english', property_address));
CREATE INDEX idx_parcels_value_range ON parcels(total_value) WHERE total_value > 0;

-- Sales history indexes
CREATE INDEX idx_sales_parcel_date ON sales_history(parcel_id, sale_date DESC);
CREATE INDEX idx_sales_price_range ON sales_history(sale_price) WHERE qualified_sale = true;
CREATE INDEX idx_sales_buyer ON sales_history(buyer_name) WHERE buyer_name IS NOT NULL;

-- Geographic indexes (for map searches)
CREATE INDEX idx_properties_location ON properties USING GIST(
    ST_MakePoint(longitude, latitude)
);
```

### 3. Materialized Views for Performance

```sql
-- Market summary view (refresh daily)
CREATE MATERIALIZED VIEW mv_market_summary AS
SELECT 
    county_code,
    DATE_TRUNC('month', sale_date) as month,
    COUNT(*) as total_sales,
    AVG(sale_price) as avg_price,
    MEDIAN(sale_price) as median_price,
    COUNT(CASE WHEN buyer_name LIKE '%BANK%' THEN 1 END) as bank_sales
FROM sales_history
WHERE qualified_sale = true
GROUP BY county_code, DATE_TRUNC('month', sale_date);

-- Top property owners view (refresh weekly)
CREATE MATERIALIZED VIEW mv_top_owners AS
SELECT 
    owner_name,
    COUNT(*) as property_count,
    SUM(total_value) as total_portfolio_value,
    AVG(total_value) as avg_property_value
FROM parcels
GROUP BY owner_name
HAVING COUNT(*) > 10
ORDER BY property_count DESC;

-- Property profiles aggregate (refresh on demand)
CREATE MATERIALIZED VIEW mv_property_profiles AS
SELECT 
    p.parcel_id,
    p.property_address,
    p.owner_name,
    p.total_value,
    COUNT(DISTINCT s.id) as sale_count,
    MAX(s.sale_date) as last_sale_date,
    MAX(s.sale_price) as last_sale_price,
    COUNT(DISTINCT bp.id) as permit_count,
    COUNT(DISTINCT pe.entity_id) as linked_entities
FROM parcels p
LEFT JOIN sales_history s ON p.parcel_id = s.parcel_id
LEFT JOIN building_permits bp ON p.parcel_id = bp.parcel_id
LEFT JOIN property_entities pe ON p.parcel_id = pe.parcel_id
GROUP BY p.parcel_id, p.property_address, p.owner_name, p.total_value;
```

### 4. Data Loading Strategy

#### Phase 1: Core Tables (Immediate)
1. Create base tables without partitioning
2. Load sample data (1000 records per table)
3. Test application functionality

#### Phase 2: Full Data Load (Week 1)
1. Implement partitioning
2. Load Florida parcels data by county
3. Import sales history (last 5 years)
4. Load current tax information

#### Phase 3: Enhancement Data (Week 2)
1. Import Sunbiz entity data
2. Load building permits
3. Create entity-property relationships
4. Build materialized views

#### Phase 4: Optimization (Week 3)
1. Analyze query patterns
2. Add missing indexes
3. Implement caching layer
4. Setup data refresh schedules

## Database Schema Design

### Core Tables Structure

```sql
-- 1. Main parcels table (partitioned by county)
CREATE TABLE parcels (
    id BIGSERIAL,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    county_code VARCHAR(10) NOT NULL,
    property_address TEXT,
    owner_name TEXT,
    owner_address TEXT,
    property_use_code VARCHAR(20),
    property_type VARCHAR(50),
    total_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    land_value DECIMAL(15,2),
    building_value DECIMAL(15,2),
    year_built INTEGER,
    living_area INTEGER,
    lot_size DECIMAL(10,2),
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    pool BOOLEAN DEFAULT FALSE,
    garage_spaces INTEGER,
    stories INTEGER,
    construction_type VARCHAR(50),
    roof_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id, county_code)
) PARTITION BY RANGE (county_code);

-- 2. Sales history (partitioned by date)
CREATE TABLE sales_history (
    id BIGSERIAL,
    parcel_id VARCHAR(50) NOT NULL,
    sale_date DATE NOT NULL,
    sale_price DECIMAL(15,2),
    seller_name TEXT,
    buyer_name TEXT,
    sale_type VARCHAR(50),
    qualified_sale BOOLEAN DEFAULT TRUE,
    deed_type VARCHAR(50),
    book_page VARCHAR(50),
    mortgage_amount DECIMAL(15,2),
    mortgage_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id, sale_date)
) PARTITION BY RANGE (sale_date);

-- 3. Fast search table (denormalized for speed)
CREATE TABLE property_search (
    parcel_id VARCHAR(50) PRIMARY KEY,
    search_vector tsvector,
    county_code VARCHAR(10),
    property_type VARCHAR(50),
    price_range INT, -- 1: <100k, 2: 100-250k, 3: 250-500k, 4: 500k-1M, 5: >1M
    year_built_decade INT, -- 1960, 1970, 1980, etc.
    json_data JSONB -- Full property data for quick retrieval
);
```

## UI Data Mapping

### Property Search Page
```javascript
// Required data
{
  source_tables: ['property_search', 'parcels'],
  filters: {
    location: 'county_code, city, zip',
    price: 'price_range or total_value',
    type: 'property_type',
    features: 'bedrooms, bathrooms, pool, garage_spaces'
  },
  display_fields: [
    'property_address',
    'total_value',
    'bedrooms',
    'bathrooms',
    'living_area',
    'thumbnail_url'
  ],
  pagination: {
    default_limit: 20,
    max_limit: 100
  }
}
```

### Property Profile Page
```javascript
{
  tabs: {
    overview: {
      tables: ['parcels', 'properties'],
      fields: ['all parcel fields', 'calculated_metrics']
    },
    sales_history: {
      tables: ['sales_history'],
      query: 'SELECT * FROM sales_history WHERE parcel_id = ? ORDER BY sale_date DESC'
    },
    tax_info: {
      tables: ['property_tax_info'],
      fields: ['tax_year', 'tax_amount', 'exemptions', 'payment_status']
    },
    permits: {
      tables: ['building_permits'],
      fields: ['permit_type', 'issue_date', 'status', 'estimated_value']
    },
    entities: {
      tables: ['sunbiz_entities', 'property_entities'],
      joins: 'property_entities -> sunbiz_entities on entity_id'
    },
    market_analysis: {
      tables: ['mv_property_profiles', 'mv_market_summary'],
      calculations: ['price_trends', 'comparable_sales', 'investment_score']
    }
  }
}
```

### Dashboard
```javascript
{
  widgets: {
    tracked_properties: {
      table: 'tracked_properties',
      join: 'parcels on parcel_id',
      limit: 10
    },
    recent_alerts: {
      table: 'user_alerts',
      order: 'created_at DESC',
      limit: 5
    },
    market_trends: {
      table: 'mv_market_summary',
      timeframe: 'last_12_months'
    },
    portfolio_value: {
      tables: ['tracked_properties', 'parcels'],
      aggregate: 'SUM(total_value)'
    }
  }
}
```

## Implementation Steps

### Immediate Actions (Today)

1. **Create Database Tables**
   ```bash
   # Run in Supabase SQL Editor
   create_all_tables.sql
   ```

2. **Load Sample Data**
   ```bash
   python load_sample_data.py --records=1000
   ```

3. **Test API Connections**
   ```bash
   python test_api_connections.py
   ```

### Week 1: Data Loading

1. **Monday**: Load Broward parcels
2. **Tuesday**: Load sales history
3. **Wednesday**: Load tax and permit data
4. **Thursday**: Import Sunbiz entities
5. **Friday**: Create relationships and test

### Week 2: Optimization

1. Implement partitioning for large tables
2. Create all indexes
3. Build materialized views
4. Setup refresh schedules
5. Performance testing

### Week 3: Production Ready

1. Data quality checks
2. Backup procedures
3. Monitoring setup
4. Documentation completion
5. Launch preparation

## Performance Targets

- Property search: <100ms for 95% of queries
- Property profile load: <200ms
- Dashboard refresh: <500ms
- Bulk operations: Process 10K records/minute
- Concurrent users: Support 1000+ simultaneous

## Monitoring & Maintenance

### Key Metrics to Track
- Query response times
- Table sizes and growth rates
- Index usage statistics
- Materialized view refresh times
- Error rates and types

### Maintenance Schedule
- **Daily**: Refresh market summary views
- **Weekly**: Analyze and vacuum tables
- **Monthly**: Review and update indexes
- **Quarterly**: Archive old data

## Risk Mitigation

### Data Volume Growth
- Implement automatic partitioning for new months/years
- Archive historical data >5 years old
- Use compression for large text fields

### Performance Degradation
- Monitor slow query log
- Implement query result caching
- Use read replicas for heavy read operations

### Data Integrity
- Implement foreign key constraints
- Add check constraints for data validation
- Regular data quality audits

## Next Steps

1. **Immediate**: Run `create_all_tables.sql` in Supabase
2. **Today**: Start loading sample data
3. **This Week**: Complete Phase 1 implementation
4. **Next Week**: Begin full data migration

## Success Criteria

- [ ] All tables created and indexed
- [ ] Sample data loaded and accessible
- [ ] API endpoints returning data
- [ ] UI components displaying correct data
- [ ] Search functionality working
- [ ] Performance targets met
- [ ] Documentation complete