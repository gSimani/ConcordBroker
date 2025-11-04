# 🗄️ GUY WE NEED YOUR HELP WITH SUPABASE

**Date:** 2025-11-03
**Priority:** CRITICAL
**Project:** pmispwtdngkcmsrsjwbp.supabase.co

---

## Problem Summary

pg_cron **Job 27** (runid 17073) has been stuck for **124+ minutes** with **ZERO rows updated**. The job is executing `populate_all_dor_int()` and holding `ShareUpdateExclusiveLock` on `florida_parcels` table, **blocking all M0 progress**.

- **Expected Duration:** 5-10 minutes
- **Actual State:** Indefinite hang, 0 progress
- **Impact:** Final M0 milestone blocked (DOR INT population for 5.7M properties)

We have deployed the safe replacement function `populate_dor_int_safe()` and attempted to clear locks, but **lack permissions to terminate PIDs or disable cron jobs**.

---

## What We've Tried (All Failed Due to Permissions)

### ❌ Attempted Task 1: Terminate Lock Holders
```sql
-- FAILED: permission denied to terminate process
WITH target_rel AS (
  SELECT oid FROM pg_class WHERE relname = 'florida_parcels' AND relnamespace = 'public'::regnamespace
),
lock_pids AS (
  SELECT DISTINCT l.pid FROM pg_locks l JOIN target_rel t ON l.relation = t.oid
)
SELECT pg_terminate_backend(a.pid) AS terminated, a.pid, a.query
FROM pg_stat_activity a JOIN lock_pids lp ON lp.pid = a.pid
WHERE a.pid <> pg_backend_pid();
```

**Error:** `permission denied to terminate process`

### ❌ Attempted Task 2: Disable pg_cron Job 27
```sql
-- FAILED: permission denied for table job
UPDATE cron.job SET active = false WHERE jobid = 27;
```

**Error:** `permission denied for table job`

---

## What We Need Supabase Support To Do

Please execute the following tasks **with elevated privileges**:

### ✅ Task 1: Terminate Lock Holders on florida_parcels

```sql
WITH target_rel AS (
  SELECT oid FROM pg_class WHERE relname = 'florida_parcels' AND relnamespace = 'public'::regnamespace
),
lock_pids AS (
  SELECT DISTINCT l.pid
  FROM pg_locks l
  JOIN target_rel t ON l.relation = t.oid
)
SELECT pg_terminate_backend(a.pid) AS terminated, a.pid, a.query
FROM pg_stat_activity a
JOIN lock_pids lp ON lp.pid = a.pid
WHERE a.pid <> pg_backend_pid();
```

**Verification:**
```sql
SELECT count(*) FROM pg_locks l JOIN pg_class c ON c.oid = l.relation WHERE c.relname = 'florida_parcels';
-- Expected: 0 (no locks remaining)
```

---

### ✅ Task 2: Hard-Stop Any Remaining UPDATEs (Failsafe)

```sql
SELECT pg_terminate_backend(pid) AS terminated, pid, query
FROM pg_stat_activity
WHERE pid <> pg_backend_pid()
  AND state = 'active'
  AND query ILIKE '%UPDATE public.florida_parcels%';
```

**Verification:**
```sql
SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND query ILIKE '%UPDATE public.florida_parcels%';
-- Expected: 0 (no active updates)
```

---

### ✅ Task 3: Disable pg_cron Job 27

```sql
UPDATE cron.job SET active = false WHERE jobid = 27;
```

**Verification:**
```sql
SELECT jobid, jobname, active, schedule FROM cron.job WHERE jobid = 27;
-- Expected: active = false
```

---

### ✅ Task 4: Verify Complete Clearance

```sql
SELECT
  a.pid, a.state, a.wait_event_type, a.wait_event, a.query_start, left(a.query, 200) AS query_snippet
FROM pg_locks l
JOIN pg_class c ON c.oid = l.relation
JOIN pg_stat_activity a ON a.pid = l.pid
WHERE c.relname = 'florida_parcels'
ORDER BY a.query_start;
```

**Expected:** 0 rows returned (empty result = clear to proceed)

---

### ✅ Task 5: Execute First 10 Batches (Safe Function)

```sql
DO $$
DECLARE
  i int := 0;
  r record;
BEGIN
  WHILE i < 10 LOOP
    SELECT * INTO r FROM public.populate_dor_int_safe();
    RAISE NOTICE 'Batch % -> rows_updated=%, batch_duration=%.1fs, remaining=%',
      i + 1, r.rows_updated, r.batch_duration_seconds, r.remaining_estimate;

    EXIT WHEN r.rows_updated = 0;
    i := i + 1;
  END LOOP;
END;
$$;
```

**Expected Output:** 10 NOTICE messages showing batch progress:
```
NOTICE: Batch 1 -> rows_updated=10000, batch_duration=3.2s, remaining=5697843
NOTICE: Batch 2 -> rows_updated=10000, batch_duration=3.1s, remaining=5687843
... (8 more batches)
```

---

### ✅ Task 6: Verify Progress After 10 Batches

```sql
SELECT
  COUNT(*) FILTER (WHERE year = 2025 AND dor_use_code_int IS NULL) AS remaining_nulls_2025,
  COUNT(*) FILTER (WHERE year = 2025 AND dor_use_code_int IS NOT NULL) AS updated_2025,
  ROUND(100.0 * COUNT(*) FILTER (WHERE year = 2025 AND dor_use_code_int IS NOT NULL) / COUNT(*), 2) AS coverage_pct
FROM florida_parcels
WHERE year = 2025;
```

**Expected:**
- `remaining_nulls_2025`: ~5,597,843 (decreased by 100,000)
- `updated_2025`: ~100,000 (increased from 0)
- `coverage_pct`: ~1.75%

---

## Safe Function Details (Already Deployed)

We've already deployed `populate_dor_int_safe()` with these safety features:
- ✅ **10k row batches** (not 100k like Job 27)
- ✅ **50-second statement timeout** (prevents hangs)
- ✅ **SKIP LOCKED** (concurrent-safe, no blocking)
- ✅ **Returns progress info** (rows_updated, duration, remaining)
- ✅ **Single batch per call** (incremental, resumable)

---

## Rollback Plan

If issues occur:

1. **Re-enable Job 27** (only if safe function fails completely):
   ```sql
   UPDATE cron.job SET active = true WHERE jobid = 27;
   ```

2. **No data rollback needed:**
   - All updates are idempotent (`dor_use_code_int = property_use::int`)
   - No data corruption risk

3. **If batches timeout:**
   - Reduce batch size in `populate_dor_int_safe()` from 10000 to 5000 or 2500
   - Function can be adjusted without data loss

---

## Timeline

**Expected execution time:** ~5-10 minutes total

- Task 1-3: < 1 minute (terminate processes)
- Task 4: < 10 seconds (verification)
- Task 5: 3-5 minutes (10 batches × 3-5 seconds each)
- Task 6: < 10 seconds (verification)

---

## Why This Is Safe

1. ✅ Each batch has 50-second timeout (prevents new hangs)
2. ✅ SKIP LOCKED prevents blocking (concurrent-safe)
3. ✅ Small batches (10k not 100k) reduce lock duration
4. ✅ Progress committed after each batch (no lost work)
5. ✅ Function already deployed and tested
6. ✅ Idempotent operation (safe to retry/resume)

---

## Contact

After executing Tasks 1-6, please provide:

1. **Termination results:** How many PIDs were killed
2. **Lock verification:** Confirmation table is clear
3. **Batch execution:** All 10 NOTICE messages from Task 5
4. **Final counts:** Results from Task 6 verification

We'll then proceed with the remaining ~560 batches to complete M0.

---

**Status:** ⏳ Waiting for Supabase Support assistance
**Confidence:** 🟢 High (safe design, proven patterns)
**Risk:** 🟡 Low (incremental, resumable, timeout-protected)
