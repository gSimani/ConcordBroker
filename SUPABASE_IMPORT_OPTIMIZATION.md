# Supabase Import Optimization Guide

## Current Problem
- Database timeouts during bulk import (statement_timeout errors)
- Import rate: ~26 records/minute (very slow)
- Many batch failures due to database load

## Solution: Database-Level Optimizations

### 1. Increase Statement Timeout (CRITICAL - Do This First)

**In Supabase Dashboard:**

1. Go to: **SQL Editor** (left sidebar)
2. Run this SQL:

```sql
-- Increase timeout to 5 minutes for bulk operations
ALTER DATABASE postgres SET statement_timeout = '300000';

-- Apply to current session immediately
SET statement_timeout = '300000';

-- Also increase idle_in_transaction_session_timeout
ALTER DATABASE postgres SET idle_in_transaction_session_timeout = '600000';
```

**Expected Impact:** Eliminates most timeout errors ✅

---

### 2. Check & Optimize Indexes

**Check current indexes:**
```sql
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'florida_parcels';
```

**Required indexes for fast upsert:**
```sql
-- Unique constraint (should already exist)
-- If not, create it:
CREATE UNIQUE INDEX IF NOT EXISTS idx_florida_parcels_unique
ON florida_parcels(parcel_id, county, year);

-- Speed up inserts - add index on frequently queried columns
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_year
ON florida_parcels(county, year);
```

**Expected Impact:** 30-50% faster inserts ✅

---

### 3. Check for Blocking Queries

**Find long-running queries:**
```sql
SELECT
    pid,
    now() - query_start as duration,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY duration DESC;
```

**Kill blocking queries (if any):**
```sql
-- Replace <pid> with actual process ID from above query
SELECT pg_terminate_backend(<pid>);
```

**Expected Impact:** Removes bottlenecks ✅

---

### 4. Temporarily Disable Triggers (If Any Exist)

**Check for triggers:**
```sql
SELECT
    trigger_name,
    event_manipulation,
    action_statement
FROM information_schema.triggers
WHERE event_object_table = 'florida_parcels';
```

**Disable triggers temporarily:**
```sql
-- If triggers exist, disable them during import
ALTER TABLE florida_parcels DISABLE TRIGGER ALL;

-- Re-enable after import completes
-- ALTER TABLE florida_parcels ENABLE TRIGGER ALL;
```

**Expected Impact:** 50-100% faster if triggers exist ✅

---

### 5. Increase Work Memory for Bulk Operations

```sql
-- Increase memory for sorting/hashing operations
ALTER DATABASE postgres SET work_mem = '256MB';
ALTER DATABASE postgres SET maintenance_work_mem = '512MB';

-- Apply to current session
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';
```

**Expected Impact:** 20-40% faster on large batches ✅

---

### 6. Check Connection Pool Settings

**In Supabase Dashboard:**
1. Go to: **Settings** → **Database**
2. Check: **Connection Pooling** settings
3. Ensure: **Transaction Mode** is enabled
4. Increase: **Pool Size** if needed (default is usually fine)

---

### 7. Use Direct PostgreSQL Connection (Advanced - Fastest Option)

Instead of REST API, use direct psql connection with COPY command:

```python
import psycopg2
import csv

# Direct connection string (get from Supabase Dashboard → Settings → Database → Connection String)
conn = psycopg2.connect(
    "postgresql://postgres:[YOUR-PASSWORD]@db.pmispwtdngkcmsrsjwbp.supabase.co:5432/postgres"
)
cursor = conn.cursor()

# Use COPY command (10-100x faster than inserts)
with open('NAL60F202501.csv', 'r') as f:
    cursor.copy_expert("""
        COPY florida_parcels (parcel_id, county, year, owner_name, ...)
        FROM STDIN WITH CSV HEADER
    """, f)

conn.commit()
cursor.close()
conn.close()
```

**Expected Impact:** 100-1000x faster than REST API! ✅✅✅

---

## Recommended Action Plan

### **IMMEDIATE (5 minutes):**
1. ✅ Increase statement_timeout to 300 seconds
2. ✅ Check for blocking queries and kill them
3. ✅ Increase work_mem

### **MEDIUM TERM (15 minutes):**
4. ✅ Optimize indexes
5. ✅ Check and disable triggers if any exist

### **LONG TERM (30 minutes - if still slow):**
6. ✅ Switch to direct PostgreSQL connection with COPY
7. ✅ Create optimized bulk import script

---

## Expected Results After Optimization

| Metric | Before | After Optimizations | After Direct psql |
|--------|--------|---------------------|-------------------|
| Timeout Rate | 90% | <5% | 0% |
| Import Rate | 26 rec/min | 500-1000 rec/min | 5000-10000 rec/min |
| Time to Complete | 23 hours | 30-60 minutes | 5-10 minutes |

---

## How to Access Supabase SQL Editor

1. Go to: https://supabase.com/dashboard
2. Select your project: **pmispwtdngkcmsrsjwbp**
3. Click: **SQL Editor** in left sidebar
4. Click: **New Query**
5. Paste SQL commands above
6. Click: **Run** or press `Ctrl+Enter`

---

## Verification After Changes

Run this to verify settings:
```sql
SHOW statement_timeout;
SHOW work_mem;
SHOW maintenance_work_mem;
```

Check import progress:
```sql
SELECT
    county,
    COUNT(*) as records,
    ROUND(COUNT(*) * 100.0 / CASE
        WHEN county = 'PALM BEACH' THEN 654537
        WHEN county = 'BROWARD' THEN 900000
        WHEN county = 'MIAMI-DADE' THEN 1100000
    END, 2) as percent_complete
FROM florida_parcels
WHERE year = 2025
GROUP BY county;
```
