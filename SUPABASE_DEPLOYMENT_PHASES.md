# SUPABASE PROPERTY APPRAISER DEPLOYMENT - PHASE EXECUTION

## Current Status
Supabase has already queued optimization phases. We need to proceed with the existing queue system.

## PHASE 1: PREFLIGHT VALIDATION (Execute These First)

**COMMAND TO SUPABASE:** Execute these preflight queries and report results:

```sql
-- Check if florida_parcels table exists
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'florida_parcels') as column_count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_name = 'florida_parcels';
```

```sql
-- Check current indexes
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'florida_parcels'
ORDER BY indexname;
```

```sql
-- Verify pg_trgm extension (already confirmed available)
SELECT * FROM pg_extension WHERE extname = 'pg_trgm';
```

**SUPABASE ACTION REQUIRED:**
1. Execute each query above
2. Report the exact results
3. Confirm table exists before proceeding to Phase 2

---

## PHASE 2: EXECUTE QUEUED OPTIMIZATIONS

Since Supabase has already queued these phases, execute them in order:

### PHASE 2.1: Disable Timeouts
```sql
-- Phase 2.1: Disable timeouts during maintenance
ALTER ROLE authenticator SET statement_timeout = '0';
ALTER ROLE anon SET statement_timeout = '0';
ALTER ROLE authenticated SET statement_timeout = '0';
ALTER ROLE service_role SET statement_timeout = '0';
```

**SUPABASE:** Execute this and confirm with message "Timeouts disabled for all roles"

### PHASE 2.2: Create Performance Indexes (Execute Each Separately)

**Index 1: City Index**
```sql
-- Phase 2.2: Create index (city)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_city_btree
ON public.florida_parcels(phy_city) WHERE phy_city IS NOT NULL;
```

**Index 2: County Index**
```sql
-- Phase 2.2: Create index (county)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county
ON public.florida_parcels(county) WHERE county IS NOT NULL;
```

**Index 3: Parcel Year Index**
```sql
-- Phase 2.2: Create index (parcel_id, year)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_parcel_year
ON public.florida_parcels(parcel_id, year) WHERE parcel_id IS NOT NULL;
```

**Index 4: Just Value Index**
```sql
-- Phase 2.2: Create index (just_value)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_just_value
ON public.florida_parcels(just_value) WHERE just_value IS NOT NULL;
```

**SUPABASE:** Execute each index creation separately and report:
- "Index [name] created successfully" OR
- "Index [name] already exists" OR
- "Error creating index [name]: [error message]"

---

## PHASE 3: VERIFICATION AND TESTING

After Phase 2 completion, execute verification:

```sql
-- Verify all indexes created
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'florida_parcels'
AND indexname LIKE 'idx_florida_parcels_%'
ORDER BY indexname;
```

```sql
-- Test table readiness with sample insert
INSERT INTO florida_parcels (
    parcel_id,
    county,
    year,
    owner_name,
    phy_addr1,
    phy_city,
    just_value
) VALUES (
    'SUPABASE_TEST_001',
    'BROWARD',
    2025,
    'Supabase Verification Record',
    '123 Database Street',
    'Fort Lauderdale',
    250000
) ON CONFLICT (parcel_id) DO UPDATE
SET updated_at = COALESCE(updated_at, NOW())
RETURNING parcel_id, created_at;
```

**SUPABASE:** Report the results of both queries.

---

## PHASE 4: READY STATE CONFIRMATION

**SUPABASE:** After successful completion of all phases, provide this exact response format:

```
SUPABASE DEPLOYMENT STATUS REPORT
=================================
Timestamp: [current timestamp]
Database: Connected

PHASE 1 - PREFLIGHT: ✅ COMPLETED
- florida_parcels table: EXISTS ([X] columns)
- pg_trgm extension: AVAILABLE
- Current indexes: [X] found

PHASE 2 - OPTIMIZATION: ✅ COMPLETED
- Timeouts: DISABLED
- City index: CREATED
- County index: CREATED
- Parcel year index: CREATED
- Just value index: CREATED

PHASE 3 - VERIFICATION: ✅ COMPLETED
- All indexes: CONFIRMED
- Test insert: SUCCESS
- Table readiness: VERIFIED

STATUS: READY FOR DATA LOADING

Awaiting next command:
- Load BROWARD sample data (100 records)
- OR Load full dataset (9.7M records)
- OR Run additional optimizations
```

---

## CRITICAL EXECUTION NOTES

**SUPABASE:** Follow these requirements exactly:

1. **Execute Phase 1 first** - Do not proceed to Phase 2 until Phase 1 results are reported
2. **Execute indexes one at a time** - Wait for each CREATE INDEX to complete
3. **Report all errors** - Include exact error messages if any command fails
4. **Confirm each step** - Provide confirmation message after each successful execution
5. **Stop on errors** - Do not continue if any phase fails

## ERROR HANDLING

If any command fails:
1. **Stop execution immediately**
2. **Report the exact error message**
3. **Indicate which phase and step failed**
4. **Wait for corrective instructions**

## NEXT STEPS AFTER COMPLETION

Once Supabase reports "STATUS: READY FOR DATA LOADING", I will provide the data loading commands to populate the database with Property Appraiser records.

**SUPABASE:** Confirm you understand these instructions and begin Phase 1 execution immediately.