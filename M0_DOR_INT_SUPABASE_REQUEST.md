# 🗄️ GUY WE NEED YOUR HELP WITH SUPABASE

## M0 - DOR INT Population Function Execution Request

**Date:** 2025-11-02
**Priority:** HIGH
**Milestone:** M0 - Schema & Seeds
**PDR Reference:** FL-USETAX-PDR-001 v1.0.0

---

## Request Overview

Execute the `populate_all_dor_int()` function that's already created in the database. SQL Editor read-only mode is preventing client-side execution. Function exists and is ready to run with service_role permissions.

---

## JSON Request

```json
{
  "request_type": "function_execution",
  "priority": "high",
  "milestone": "M0_dor_int_population",
  "pdr_reference": "FL-USETAX-PDR-001 v1.0.0",
  "context": "Need to execute populate_all_dor_int() function that's already created. SQL Editor read-only mode is blocking client-side execution. Function exists and is ready to run.",
  "tasks": [
    {
      "task_id": 1,
      "action": "Execute the DOR INT population function",
      "sql": "SELECT * FROM public.populate_all_dor_int();",
      "description": "Executes batched DOR code INT population (57 batches × 100k rows), creates performance index, returns summary stats",
      "verification": "Function should return 1 row with: total_batches (~57), total_rows_updated (~5.7M), duration_seconds (~300-600), index_created (true)"
    },
    {
      "task_id": 2,
      "action": "Verify completion with coverage statistics",
      "sql": "SELECT \n  count(*) as total_properties,\n  count(dor_use_code_int) as with_dor_int,\n  round(100.0 * count(dor_use_code_int) / count(*), 2) as coverage_pct\nFROM florida_parcels\nWHERE year = 2025;",
      "verification": "Should show ~10.3M total_properties, ~5.7M with_dor_int, ~55% coverage_pct"
    }
  ],
  "rollback_plan": {
    "description": "Function is idempotent and safe. If needed, can revert by setting dor_use_code_int to NULL",
    "sql": "-- Only if rollback needed (unlikely)\nUPDATE florida_parcels SET dor_use_code_int = NULL WHERE year = 2025;\nDROP INDEX IF EXISTS idx_fp_year_dor;"
  },
  "dependencies": {
    "existing_objects": [
      "populate_all_dor_int() function (already created)",
      "populate_dor_int_batch() function (already created)",
      "florida_parcels table",
      "dor_use_code_int column",
      "normalized property_use values"
    ],
    "required_permissions": ["service_role"],
    "notes": "Both functions exist and are ready. Just need to execute with write permissions."
  },
  "expected_outcomes": {
    "rows_updated": "~5,700,000",
    "batches_executed": "~57",
    "index_created": true,
    "execution_time": "5-10 minutes",
    "downtime": "None (non-blocking UPDATE)",
    "function_output": "1 row with summary statistics"
  }
}
```

---

## Task 1: Execute Function

**SQL:**
```sql
SELECT * FROM public.populate_all_dor_int();
```

**Expected Output:**
```
total_batches | total_rows_updated | duration_seconds | index_created
--------------|--------------------|------------------|---------------
     57       |      5,707,000     |      324.56      |     true
```

---

## Task 2: Verification

**SQL:**
```sql
SELECT
  count(*) as total_properties,
  count(dor_use_code_int) as with_dor_int,
  round(100.0 * count(dor_use_code_int) / count(*), 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025;
```

**Expected Output:**
```
total_properties | with_dor_int | coverage_pct
-----------------|--------------|--------------
    10,304,043   |   5,707,000  |     55.38
```

---

## Function Details

**Created:** 2025-11-02
**Name:** `public.populate_all_dor_int()`
**Type:** PLPGSQL, SECURITY DEFINER
**Returns:** TABLE(total_batches INT, total_rows_updated BIGINT, duration_seconds NUMERIC, index_created BOOLEAN)

**What it does:**
1. Loops through batches calling `populate_dor_int_batch(100000)`
2. Logs progress every 10 batches via RAISE NOTICE
3. Creates index `idx_fp_year_dor` on `(year, dor_use_code_int) WHERE year = 2025`
4. Returns summary statistics

**Properties:**
- ✅ Idempotent (safe to run multiple times)
- ✅ Server-side execution (no HTTP timeout issues)
- ✅ Progress logging (RAISE NOTICE every 10 batches)
- ✅ Automatic index creation
- ✅ Error handling with rollback capability

---

## Pre-Execution Checklist

- [x] `populate_all_dor_int()` function created
- [x] `populate_dor_int_batch()` function created
- [x] `property_use` column normalized (zero-padded via pg_cron)
- [x] `dor_use_code_int` column exists in florida_parcels
- [x] Schema and seeds deployed (M0 complete)

---

## Rollback Plan (If Needed)

**Only if complete rollback is required:**
```sql
-- Revert all DOR INT values
UPDATE florida_parcels
SET dor_use_code_int = NULL
WHERE year = 2025;

-- Remove performance index
DROP INDEX IF EXISTS public.idx_fp_year_dor;
```

**Risk Level:** LOW (function is idempotent and safe)
**Data Loss Risk:** NONE (only populates NULL values)

---

## Alternative Execution Methods

If Supabase support prefers an alternative approach:

1. **Edge Function:** Deploy Deno edge function to execute server-side
2. **pg_cron Job:** Schedule as one-time background job
3. **Direct psql:** Execute via PostgreSQL command line with service_role

Function code is available if needed for review.

---

## Post-Execution Report Required

Please provide:
1. **Task 1 output** (4-column result from function)
2. **Task 2 output** (3-column verification statistics)
3. **Execution logs** (optional: RAISE NOTICE messages showing batch progress)

---

## Contact

**Project:** pmispwtdngkcmsrsjwbp.supabase.co
**Milestone:** M0 - Schema & Seeds
**PDR:** FL-USETAX-PDR-001 v1.0.0
**Date Submitted:** 2025-11-02

---

**STATUS:** ⏳ Awaiting Supabase execution
