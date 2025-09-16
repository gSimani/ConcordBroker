# Supabase Support Request: Bulk Data Upload Configuration

## Project Details
- **Project URL**: https://pmispwtdngkcmsrsjwbp.supabase.co
- **Table**: `public.florida_parcels`
- **Current Status**: ~3.5M of 9.7M records loaded (REST API timeouts blocking completion)

## 1. IMMEDIATE NEED: Direct Database Connection

We need the **actual database password** (not JWT) for PostgreSQL COPY operations:
- From: Dashboard → Settings → Database → Connection string
- Format needed: `postgresql://postgres.pmispwtdngkcmsrsjwbp:[ACTUAL_PASSWORD]@db.pmispwtdngkcmsrsjwbp.supabase.co:5432/postgres`

## 2. CREATE STAGING TABLE (Please Run)

```sql
-- Create lean staging table (no indexes/constraints for fast loading)
CREATE TABLE IF NOT EXISTS public.florida_parcels_staging (
    LIKE public.florida_parcels INCLUDING DEFAULTS INCLUDING GENERATED
);

-- Grant minimal permissions (service_role only)
GRANT ALL ON public.florida_parcels_staging TO service_role;
REVOKE ALL ON public.florida_parcels_staging FROM anon, authenticated;
```

## 3. CREATE DEDICATED INGEST ROLE (Safer than ALTER DATABASE)

```sql
-- Create role with optimized settings for bulk loading
CREATE ROLE bulk_loader WITH LOGIN PASSWORD 'secure_password_here';
GRANT ALL ON SCHEMA public TO bulk_loader;
GRANT ALL ON public.florida_parcels_staging TO bulk_loader;
GRANT ALL ON public.florida_parcels TO bulk_loader;

-- Set role-specific optimizations (no global impact)
ALTER ROLE bulk_loader SET statement_timeout = 0;
ALTER ROLE bulk_loader SET lock_timeout = 0;
ALTER ROLE bulk_loader SET idle_in_transaction_session_timeout = 0;
ALTER ROLE bulk_loader SET synchronous_commit = off;
ALTER ROLE bulk_loader SET work_mem = '256MB';
ALTER ROLE bulk_loader SET maintenance_work_mem = '512MB';
```

## 4. VERIFICATION QUERIES (Please Run and Share Results)

```sql
-- 1. Exact current count
SELECT COUNT(*) as exact_count FROM public.florida_parcels;

-- 2. Check for active COPY operations
SELECT pid, relid::regclass as relation, command, type,
       bytes_processed, pg_size_pretty(bytes_processed) as processed,
       bytes_total, pg_size_pretty(bytes_total) as total,
       round(100.0 * bytes_processed / nullif(bytes_total,0), 2) as pct
FROM pg_stat_progress_copy
ORDER BY pid;

-- 3. Current table size
SELECT 
    pg_size_pretty(pg_total_relation_size('public.florida_parcels')) as total_size,
    pg_size_pretty(pg_relation_size('public.florida_parcels')) as table_size,
    pg_size_pretty(pg_indexes_size('public.florida_parcels')) as indexes_size,
    n_live_tup as estimated_rows
FROM pg_stat_user_tables
WHERE tablename = 'florida_parcels';

-- 4. Check for duplicate records
WITH dup_check AS (
    SELECT county, COUNT(DISTINCT parcel_id) as unique_parcels,
           COUNT(*) as total_rows,
           COUNT(*) - COUNT(DISTINCT parcel_id) as duplicates
    FROM public.florida_parcels
    WHERE county IN ('BROWARD', 'DUVAL', 'MARION')
    GROUP BY county
)
SELECT * FROM dup_check WHERE duplicates > 0;

-- 5. Current statement timeout settings
SHOW statement_timeout;
SELECT name, setting, unit, source
FROM pg_settings 
WHERE name LIKE '%timeout%';
```

## Our Loading Plan (Once We Have Credentials)

1. **COPY to staging** using psycopg with direct connection (bypassing PgBouncer)
2. **Migrate from staging to final table** with deduplication
3. **Create indexes CONCURRENTLY** after data is loaded
4. **ANALYZE** for query planner optimization

## Sample COPY Code We'll Use

```python
import psycopg
import os

# Direct connection (no PgBouncer)
dsn = f"postgresql://bulk_loader:{password}@db.pmispwtdngkcmsrsjwbp.supabase.co:5432/postgres"

with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
        # Session-level settings (not global)
        cur.execute("SET statement_timeout = '0';")
        cur.execute("SET lock_timeout = '0';")
        cur.execute("SET synchronous_commit = off;")
        
        # Stream CSV directly to staging
        with open(csv_path, "r", encoding="utf-8") as f:
            cur.copy("""
                COPY public.florida_parcels_staging 
                (parcel_id, county, year, owner_name, ...) 
                FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
            """, f)
```

## Post-Load Operations (We'll Handle)

```sql
-- 1. Migrate from staging to final (with ON CONFLICT for dedup)
INSERT INTO public.florida_parcels 
SELECT * FROM public.florida_parcels_staging
ON CONFLICT (parcel_id, county, year) DO UPDATE
SET import_date = EXCLUDED.import_date;

-- 2. Create indexes CONCURRENTLY (no table locks)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county 
    ON public.florida_parcels(county);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_parcel_id 
    ON public.florida_parcels(parcel_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_year 
    ON public.florida_parcels(year);

-- 3. Update statistics
ANALYZE public.florida_parcels;

-- 4. Clean up staging
TRUNCATE public.florida_parcels_staging;
```

## Questions

1. ✅ Can you create the staging table and bulk_loader role?
2. ✅ Can you provide the direct database password?
3. ✅ Is there a row limit/quota that might affect loading 9.7M records?
4. ✅ Should we handle the duplicates in BROWARD/DUVAL/MARION during migration?

## Expected Timeline

With proper COPY setup:
- **6.2M remaining records**: 2-4 hours to load
- **Index creation**: 30-60 minutes
- **Total completion**: Within 5 hours of receiving credentials

Please provide the verification query results and database credentials so we can complete the upload efficiently.

Thank you!