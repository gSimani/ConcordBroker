# Sunbiz Database Architecture Deployment Guide

## Overview

This guide provides complete instructions for deploying the optimized Sunbiz corporate data architecture designed for processing fixed-width corprindata0-9.txt files with millions of records.

## Architecture Summary

### 1. **Database Schema**
- **sunbiz_entities**: Main entities table (corporations, partnerships, etc.)
- **sunbiz_officers**: Officers and directors with denormalized address data
- **sunbiz_entity_addresses**: Separate addresses for entities
- **sunbiz_property_matches**: Links to property records for owner matching
- **sunbiz_data_processing_log**: Tracks file processing history

### 2. **Performance Features**
- Full-text search with tsvector columns
- Trigram indexes for fuzzy name matching
- Materialized views for fast queries
- Optimized batch processing
- Duplicate detection and prevention

### 3. **Security**
- Row Level Security (RLS) policies
- Public read access with admin write permissions
- Service role access for data loading

## Deployment Steps

### Step 1: Database Schema Deployment

```bash
# Deploy the optimized schema to Supabase
psql -h your-supabase-host -U postgres -d your-database -f sunbiz_optimized_schema.sql

# Or use Supabase SQL Editor and paste the contents of sunbiz_optimized_schema.sql
```

### Step 2: Install Required Extensions

Ensure PostgreSQL extensions are available:

```sql
-- Required for fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Required for full-text search
CREATE EXTENSION IF NOT EXISTS unaccent;
```

### Step 3: Set Up Python Environment

```bash
# Install required Python packages
pip install psycopg2-binary fuzzywuzzy python-levenshtein

# Or install from requirements
pip install -r requirements-sunbiz.txt
```

Create `requirements-sunbiz.txt`:
```
psycopg2-binary>=2.9.0
fuzzywuzzy>=0.18.0
python-levenshtein>=0.12.0
```

### Step 4: Environment Configuration

Create `.env` file with Supabase credentials:
```bash
SUPABASE_DB_HOST=your-project-id.supabase.co
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-password
SUPABASE_DB_PORT=5432
```

## Data Loading Process

### Step 1: Prepare Data Files

Ensure your corprindata files are available:
```
sunbiz_data/
├── corprindata0.txt
├── corprindata1.txt
├── corprindata2.txt
├── ...
└── corprindata9.txt
```

### Step 2: Load Sunbiz Data

```bash
# Load all files in directory
python sunbiz_data_loader.py sunbiz_data/ --pattern "corprindata*.txt"

# Load single file
python sunbiz_data_loader.py sunbiz_data/corprindata0.txt

# Overwrite existing data
python sunbiz_data_loader.py sunbiz_data/ --overwrite

# Refresh materialized views after loading
python sunbiz_data_loader.py sunbiz_data/ --refresh-views
```

### Step 3: Property Matching

```bash
# Match Sunbiz data to property records
python sunbiz_property_matcher.py --batch-size 1000

# Process limited number of properties (for testing)
python sunbiz_property_matcher.py --max-properties 10000

# Generate detailed report
python sunbiz_property_matcher.py --report
```

## Usage Examples

### 1. Search Functions

```sql
-- Search all entities by name
SELECT * FROM search_sunbiz_entities('CORNELL', 'Corporate');

-- Find similar names using fuzzy matching
SELECT * FROM find_similar_names('MICHAEL CORNELL', 0.6, 20);

-- Search by address
SELECT * FROM find_by_address('LAKE ESTATES', 'BOCA RATON', 'FL');
```

### 2. Property Owner Queries

```sql
-- Find property matches for a specific entity
SELECT 
    p.parcel_id,
    fp.property_address,
    spm.match_type,
    spm.confidence_score,
    se.entity_name,
    so.full_name as officer_name
FROM sunbiz_property_matches spm
JOIN sunbiz_entities se ON spm.entity_id = se.entity_id
LEFT JOIN sunbiz_officers so ON spm.officer_id = so.id
LEFT JOIN florida_parcels fp ON spm.parcel_id = fp.parcel_id
WHERE se.entity_name ILIKE '%CORNELL%'
ORDER BY spm.confidence_score DESC;
```

### 3. Entity Details with Officers

```sql
-- Get complete entity information
SELECT json_pretty(get_entity_details('A11000000560'));

-- List all officers for an entity
SELECT 
    e.entity_name,
    o.full_name,
    o.officer_role,
    r.role_description,
    o.city,
    o.state
FROM sunbiz_entities e
JOIN sunbiz_officers o ON e.entity_id = o.entity_id
LEFT JOIN sunbiz_officer_roles r ON o.officer_role = r.role_code
WHERE e.entity_id = 'A11000000560';
```

### 4. Performance Analytics

```sql
-- Entity summary with officer counts
SELECT * FROM sunbiz_entity_summary 
WHERE officer_count > 5 
ORDER BY officer_count DESC;

-- Officer search with entity context
SELECT * FROM sunbiz_officer_search 
WHERE full_name ILIKE '%SMITH%' 
AND city = 'MIAMI';

-- Processing statistics
SELECT 
    file_name,
    records_processed,
    entities_created,
    officers_created,
    processing_time_seconds,
    success
FROM sunbiz_data_processing_log
ORDER BY processing_start DESC;
```

## Performance Optimization

### 1. **Index Management**

```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND tablename LIKE 'sunbiz%'
ORDER BY idx_scan DESC;

-- Reindex if needed
REINDEX TABLE sunbiz_officers;
REINDEX TABLE sunbiz_entities;
```

### 2. **Materialized View Maintenance**

```sql
-- Refresh views after data updates
SELECT refresh_sunbiz_views();

-- Schedule automatic refresh (use pg_cron extension)
SELECT cron.schedule('refresh-sunbiz-views', '0 2 * * *', 'SELECT refresh_sunbiz_views();');
```

### 3. **Query Optimization**

```sql
-- Analyze tables for better query planning
ANALYZE sunbiz_entities;
ANALYZE sunbiz_officers;
ANALYZE sunbiz_property_matches;

-- Check slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
WHERE query LIKE '%sunbiz%'
ORDER BY mean_time DESC;
```

## Maintenance Tasks

### Daily Tasks
- Monitor processing logs for errors
- Check data loading statistics
- Verify property matching performance

### Weekly Tasks
- Refresh materialized views
- Analyze table statistics
- Review slow query performance

### Monthly Tasks
- Update officer role codes if needed
- Archive old processing logs
- Review and optimize indexes

## Monitoring Queries

```sql
-- Data volume statistics
SELECT 
    'sunbiz_entities' as table_name,
    COUNT(*) as record_count,
    pg_size_pretty(pg_total_relation_size('sunbiz_entities')) as table_size
FROM sunbiz_entities
UNION ALL
SELECT 
    'sunbiz_officers',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('sunbiz_officers'))
FROM sunbiz_officers
UNION ALL
SELECT 
    'sunbiz_property_matches',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('sunbiz_property_matches'))
FROM sunbiz_property_matches;

-- Match quality distribution
SELECT 
    match_type,
    COUNT(*) as matches,
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM sunbiz_property_matches
GROUP BY match_type
ORDER BY matches DESC;

-- Recent processing activity
SELECT 
    DATE(processing_start) as processing_date,
    COUNT(*) as files_processed,
    SUM(records_processed) as total_records,
    SUM(entities_created) as total_entities,
    SUM(officers_created) as total_officers,
    AVG(processing_time_seconds) as avg_processing_time
FROM sunbiz_data_processing_log
WHERE processing_start >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(processing_start)
ORDER BY processing_date DESC;
```

## Troubleshooting

### Common Issues

1. **Memory Issues During Loading**
   - Reduce batch size in loader script
   - Increase PostgreSQL work_mem setting
   - Process files one at a time

2. **Slow Property Matching**
   - Ensure pg_trgm extension is installed
   - Verify trigram indexes are created
   - Check query plans with EXPLAIN ANALYZE

3. **Duplicate Records**
   - Review duplicate detection logic
   - Check file processing logs
   - Use overwrite flag carefully

4. **RLS Permission Errors**
   - Verify service role permissions
   - Check RLS policies
   - Use authenticated user for data loading

### Performance Tuning

```sql
-- Adjust PostgreSQL settings for large data processing
SET work_mem = '256MB';
SET maintenance_work_mem = '1GB';
SET effective_cache_size = '4GB';
SET random_page_cost = 1.1;

-- Monitor long-running queries
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

## API Integration

The schema is designed to work seamlessly with your existing API structure. Example FastAPI endpoints:

```python
# Add to your FastAPI app
@app.get("/api/sunbiz/search/{search_term}")
async def search_sunbiz(search_term: str):
    # Use search_sunbiz_entities function
    pass

@app.get("/api/sunbiz/property/{parcel_id}/matches")
async def get_property_sunbiz_matches(parcel_id: str):
    # Query sunbiz_property_matches table
    pass

@app.get("/api/sunbiz/entity/{entity_id}")
async def get_entity_details(entity_id: str):
    # Use get_entity_details function
    pass
```

## Security Considerations

1. **Data Privacy**: Ensure compliance with data protection regulations
2. **Access Control**: Use RLS policies to restrict data access as needed
3. **Audit Trail**: Processing logs provide complete audit trail
4. **Backup Strategy**: Regular backups of processed data
5. **Monitoring**: Track access patterns and performance metrics

## Conclusion

This optimized architecture provides:

- **High Performance**: Optimized for millions of records
- **Scalability**: Batch processing and materialized views
- **Flexibility**: Support for various matching algorithms
- **Maintainability**: Clear schema and comprehensive logging
- **Security**: RLS policies and proper permissions

The system is designed to handle the complete Florida Sunbiz dataset efficiently while providing fast search and matching capabilities for property owner identification.