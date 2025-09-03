# Database Setup Guide

## Overview

ConcordBroker uses PostgreSQL with Supabase for the database layer. The database includes tables for property parcels, sales, corporate entities, and supporting features like RAG documents and AI agent tasks.

## Quick Setup

### Supabase Setup

1. Create a new Supabase project at [supabase.com](https://supabase.com)

2. Once created, navigate to the SQL Editor

3. Run the schema creation script:
```sql
-- Run schema.sql first
```

4. Run the RLS policies script:
```sql
-- Run policies.sql second
```

5. Get your connection details from Settings → API:
   - `SUPABASE_URL`: Your project URL
   - `SUPABASE_ANON_KEY`: Your anon/public key
   - `SUPABASE_SERVICE_ROLE_KEY`: Your service role key (keep secret!)

### Local PostgreSQL Setup

If running PostgreSQL locally:

```bash
# Create database
createdb concordbroker

# Run schema
psql -d concordbroker -f schema.sql

# Run policies
psql -d concordbroker -f policies.sql
```

## Database Structure

### Core Tables

- **parcels**: Property records from DOR assessment rolls
- **sales**: Property sales history
- **recorded_docs**: Official recorded documents
- **entities**: Corporate entities from Sunbiz
- **officers**: Corporate officers and agents
- **parcel_entity_links**: Links between properties and entities

### Supporting Tables

- **users**: Authentication and user management
- **saved_searches**: User saved search criteria
- **watchlist**: Properties being monitored by users
- **jobs**: ETL job tracking
- **rag_documents**: Knowledge base with embeddings
- **agent_tasks**: AI agent task queue

## Security

### Row Level Security (RLS)

The database uses RLS to control access:

- **Anonymous users**: No access to any data
- **Authenticated users**: Read access to property data, full access to own data
- **Service role**: Full access (used by backend API)
- **Admin users**: Full access to all tables

### API Access Patterns

```javascript
// Frontend (using anon key)
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Backend (using service role key)
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
```

## Migrations

### Creating a New Migration

```bash
# Generate migration file
supabase migration new your_migration_name

# Edit the migration file in supabase/migrations/

# Apply migration
supabase db push
```

### Migration Naming Convention

- `YYYYMMDDHHMMSS_descriptive_name.sql`
- Example: `20250103120000_add_property_scoring.sql`

## Indexing Strategy

### Performance Indexes

- Composite indexes on frequently queried combinations (city + use code)
- GIN indexes for full-text search on names and documents
- B-tree indexes on foreign keys and date columns
- IVFFlat indexes for vector similarity search

### Monitoring Query Performance

```sql
-- Check slow queries
SELECT 
    query,
    calls,
    mean_exec_time,
    total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

## Backup and Recovery

### Supabase Backups

Supabase provides automatic daily backups. For manual backups:

```bash
# Export data
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Import data
psql $DATABASE_URL < backup.sql
```

### Point-in-Time Recovery

Available on Supabase Pro plan - allows recovery to any point within the retention window.

## Common Queries

### Find properties by city and use code
```sql
SELECT * FROM parcels
WHERE city = 'COCONUT CREEK'
AND main_use = '48'
ORDER BY score DESC;
```

### Get property with full details
```sql
SELECT 
    p.*,
    e.name as entity_name,
    array_agg(s.*) as sales_history
FROM parcels p
LEFT JOIN parcel_entity_links pel ON p.folio = pel.folio
LEFT JOIN entities e ON pel.entity_id = e.id
LEFT JOIN sales s ON p.folio = s.folio
WHERE p.folio = '123456789'
GROUP BY p.folio, e.name;
```

### Search entities by name
```sql
SELECT * FROM entities
WHERE name_tsv @@ plainto_tsquery('english', 'sunshine properties');
```

## Maintenance

### Regular Tasks

1. **Weekly**: Analyze tables for query optimization
```sql
ANALYZE parcels, sales, entities;
```

2. **Monthly**: Vacuum to reclaim space
```sql
VACUUM ANALYZE;
```

3. **Quarterly**: Reindex for performance
```sql
REINDEX SCHEMA concordbroker;
```

### Health Checks

```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'concordbroker'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check connection count
SELECT count(*) FROM pg_stat_activity;

-- Check long-running queries
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check RLS policies and user role
2. **Slow Queries**: Check indexes and run EXPLAIN ANALYZE
3. **Connection Limit**: Increase pool size or optimize connection usage
4. **Storage Full**: Clean up old jobs and audit logs

### Debug RLS Policies

```sql
-- Check current user
SELECT auth.uid();

-- Test policy directly
SET ROLE authenticated;
SELECT * FROM parcels LIMIT 1;
```

## Support

For database issues:
1. Check Supabase status page
2. Review logs in Supabase dashboard
3. Contact support with query plans and error messages