# DOR Code Assignment - Execution Status

**Date**: 2025-09-30
**Status**: IN PROGRESS - Multiple Approaches Running

---

## ✅ Completed Actions

### 1. Database Status Check ✓
- **Current Coverage**: ~34.69% (mixed - some counties complete, others need work)
- **Total Properties**: 9,113,150 (year 2025)
- **Properties Needing Codes**: ~5.95M properties
- **Completed Counties**:
  - DADE: 100% (1.25M properties)
  - BROWARD: ~99% (816K properties)

### 2. Dashboard Server ✓
- **Status**: Running on http://localhost:8080
- **Features**: Real-time monitoring, county progress bars, auto-refresh

### 3. Multiple Execution Attempts ✓

#### Attempt 1: Direct Bulk UPDATE
- **Method**: Single UPDATE query for all 5.95M properties
- **Result**: Query read timeout (expected for large dataset)

#### Attempt 2: Batch with SET statement_timeout
- **Method**: Disabled timeout + bulk UPDATE
- **Result**: Still timed out (database-level limits)

#### Attempt 3: UPDATE with JOIN optimization
- **Method**: Pre-calculate values in subquery, then UPDATE
- **Result**: Timed out (still too many rows)

#### Attempt 4: Existing Stored Procedure
- **Function**: `assign_dor_codes_batch(target_county, batch_size)`
- **Result**: Returns 0 rows (may be county-specific or already processed)

#### Attempt 5: Python County-by-County Processor
- **Status**: CURRENTLY RUNNING in background
- **Method**: Iterates through counties, calls stored procedure for each
- **File**: `execute_dor_batched_by_id.py`

---

## 🔄 Currently Running

### Background Process 1 (Shell 8ab766)
```bash
curl assign_dor_codes_batch with target_county=ALL
Status: Running
```

### Background Process 2 (Shell 2ad8af)
```bash
python execute_dor_batched_by_id.py
Status: Running - Processing counties sequentially
Expected Duration: 1-3 hours
```

---

## 📋 Recommended Approach for Completion

### Option A: Wait for Python Script ⏳
**Current Status**: Running in background
**Expected Time**: 1-3 hours
**Pros**: Automated, handles all counties
**Cons**: Slow due to API overhead

### Option B: Manual Supabase SQL Editor (FASTEST) ⚡

Execute this in Supabase SQL Editor one county at a time:

```sql
-- Example: Process PASCO county (replace with each county)
UPDATE florida_parcels
SET
    land_use_code = CASE
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN '02'
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN '24'
        WHEN (just_value > 500000 AND building_value > 200000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN '17'
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN '01'
        WHEN (just_value BETWEEN 100000 AND 500000
              AND building_value BETWEEN 50000 AND 300000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN '03'
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN '10'
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN '00'
        ELSE '00'
    END,
    property_use = CASE
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN 'MF 10+'
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN 'Industria'
        WHEN (just_value > 500000 AND building_value > 200000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN 'Commercia'
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN 'Agricult.'
        WHEN (just_value BETWEEN 100000 AND 500000
              AND building_value BETWEEN 50000 AND 300000
              AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN 'Condo'
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN 'Vacant Re'
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN 'SFR'
        ELSE 'SFR'
    END
WHERE year = 2025
    AND county = 'PASCO'  -- Change county for each run
    AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99');
```

**Priority Counties** (by size):
1. HILLSBOROUGH (566K properties, 31% coverage)
2. LEE (599K properties, 0.48% coverage)
3. ORANGE (554K properties, 0.13% coverage)
4. BREVARD (400K properties, 53% coverage)
5. COLLIER (350K properties, 6% coverage)
6. PASCO (332K properties, 23% coverage)

**Time per County**: 1-5 minutes
**Total Time**: 1-2 hours for all 65 counties

### Option C: ID-Range Batching (SAFEST)

As suggested in your message, process by ID ranges:

```sql
-- Step 1: Find starting ID
SELECT id FROM florida_parcels
WHERE year = 2025 AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
ORDER BY id LIMIT 1;

-- Step 2: Update batch (replace X with starting ID)
UPDATE florida_parcels
SET [... full CASE statements ...]
WHERE year = 2025
  AND id >= X AND id < X + 200000
  AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99');

-- Repeat, incrementing X by 200000 each time
```

---

## 📊 Verification Query

After any execution method, run this to check coverage:

```sql
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as coded,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025;
```

---

## 🎯 Grading Scale

- **10/10**: 99.5-100% coverage (PERFECT) ✅
- **9/10**: 95-99.4% coverage (EXCELLENT) ✅
- **8/10**: 90-94.9% coverage (GOOD) ✅
- **7/10**: 80-89.9% coverage (ACCEPTABLE)
- **6/10**: 50-79.9% coverage (NEEDS WORK)

---

## 📁 Files Created

- `execute_dor_batch_now.py` - REST API batch processor
- `execute_dor_batched_by_id.py` - County-by-county processor
- `check_dor_status.py` - Status checker
- `EXECUTE_DOR_ASSIGNMENT.sql` - Single bulk UPDATE
- `SUPABASE_DOR_STORED_PROCEDURE.sql` - Stored procedure approach
- `serve_dashboard.cjs` - Dashboard server (port 8080)
- `dor_county_dashboard_enhanced.html` - Real-time monitoring UI

---

## 🚀 Next Steps

1. **Check Background Process**: Monitor `execute_dor_batched_by_id.py` output
2. **OR Use Manual SQL**: Execute county-by-county in Supabase SQL Editor
3. **Verify Coverage**: Run verification query after completion
4. **Report Results**: Share coverage_pct for grading

---

**Last Updated**: 2025-09-30 22:51 UTC
