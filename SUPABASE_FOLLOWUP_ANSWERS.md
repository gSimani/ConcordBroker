# Answers to Supabase's Follow-up Questions

## 🎯 Your Questions:

### 1. **Natural key for conflicts: (parcel_id, county, year)?**

✅ **YES, CONFIRMED**

This is the correct natural key for our use case:
- `parcel_id` - Unique within county (e.g., "44-11-31-4985-00000-0180")
- `county` - County name (e.g., "BROWARD", "MIAMI-DADE")
- `year` - Assessment year (2025 for current data)

**Reasoning**:
- Same parcel can appear in multiple counties? No, parcel IDs are county-specific
- Same parcel can have different years? Yes, for historical data
- This combination uniquely identifies a record ✅

---

### 2. **Proceed with creating the staging table and the unique constraint now?**

✅ **YES, PROCEED**

**Action Required**: Run `setup-staging-optimized.sql` in Supabase SQL Editor:
https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql/new

**What it creates**:
1. UNLOGGED staging table (no indexes)
2. UNIQUE constraint on `florida_parcels(parcel_id, county, year)`
3. Session configuration for 20-minute timeouts

**Why now**:
- We have 9.7M existing records to merge with
- Our CSV data uses (parcel_id, county, year) as natural key
- We want to start bulk loading immediately

---

### 3. **Should I prepare a list of non-critical indexes to drop/recreate?**

✅ **YES, PLEASE** - But defer for first run

**Recommendation**:
1. **First run**: Keep ALL indexes (test with real load first)
2. **Monitor**: Check upsert time and WAL size
3. **Second run**: If slow (>5 minutes for 500K records), drop indexes

**Query to identify droppable indexes**:
```sql
-- Find large, non-unique indexes that could be temporarily dropped
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    CASE
        WHEN idx_scan = 0 THEN 'NEVER USED - Safe to drop'
        WHEN idx_scan < 10 THEN 'RARELY USED - Consider dropping'
        ELSE 'FREQUENTLY USED - Keep'
    END as recommendation
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND tablename = 'florida_parcels'
    AND indexrelid NOT IN (
        -- Keep unique/PK indexes
        SELECT indexrelid
        FROM pg_index
        WHERE indisprimary OR indisunique
    )
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;
```

**Indexes to DEFINITELY KEEP**:
- Primary key index (surrogate `id`)
- UNIQUE constraint index `florida_parcels_unique_parcel_year`
- Any indexes used in ON CONFLICT logic

**Indexes SAFE TO DROP** (recreate after load):
- GIN indexes on text search columns (if any)
- BRIN indexes on rarely-queried columns
- Indexes with 0 usage (`idx_scan = 0`)
- Large indexes on optional fields (geometry, centroid)

---

## 🚀 Next Steps (Immediate)

### Step 1: Create Infrastructure (NOW)
Run `setup-staging-optimized.sql` in Supabase SQL Editor.

### Step 2: Test Load (5-10 minutes)
```bash
python bulk-load-county.py BROWARD
```

### Step 3: Evaluate Performance
- If <5 minutes for 500K records: ✅ Perfect, proceed with all counties
- If 5-10 minutes: ⚠️ Acceptable, but consider dropping indexes for larger loads
- If >10 minutes: 🔴 Too slow, run index analysis and drop heavy indexes

### Step 4: Production Load
Based on test results, either:
- **A)** Continue with all 67 counties (if fast enough)
- **B)** Drop 5-10 heaviest indexes, reload, recreate indexes

---

## 📊 Monitoring During Load

```sql
-- Real-time progress (run in another tab)
SELECT
    pid,
    application_name,
    state,
    wait_event_type,
    wait_event,
    LEFT(query, 80) as query
FROM pg_stat_activity
WHERE application_name = 'etl_florida_parcels_upsert';
```

---

## ✅ Confirmation Checklist

Before we run the first load:

- [x] Natural key confirmed: (parcel_id, county, year)
- [ ] Staging table SQL ready: `setup-staging-optimized.sql`
- [ ] Python bulk loader ready: `bulk-load-county.py`
- [ ] Will monitor first load performance
- [ ] Will decide on index strategy based on results

---

## 🎯 Your Clarification Needed

**Optional**: Should we also prepare a second staging approach using TEMP tables?

Supabase mentioned:
> "For each job, you can create a TEMP table instead of a persistent UNLOGGED table; it's even lighter."

**Pros of TEMP**:
- Even faster than UNLOGGED
- Auto-dropped after session
- Zero cross-session overhead

**Cons of TEMP**:
- Can't access across connections
- Must recreate per job

**Our choice**: Start with **UNLOGGED** (more flexible), optimize to TEMP later if needed.

---

**Ready to proceed?**

✅ YES - Run `setup-staging-optimized.sql` now
✅ YES - Test with Broward first
✅ YES - Monitor and optimize based on results

---

**All answers confirmed! Ready for immediate implementation!** 🚀
