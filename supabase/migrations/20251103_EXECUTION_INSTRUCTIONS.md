# Property Use Standardization Migration - Execution Instructions

## Overview
This migration standardizes ~1.4M properties (14% of database) that have DOR property_use codes but no standardized property_use_assignment records.

## Files Created
1. **20251103_add_missing_subuse_taxonomy.sql** - Adds CONDOMINIUM subuse category (REQUIRED FIRST)
2. **20251103_standardize_null_property_use.sql** - Main migration (REQUIRED SECOND)
3. **20251103_rollback_standardize_null_property_use.sql** - Rollback script (EMERGENCY ONLY)

## Pre-Execution Checklist

### 1. Verify Database State
```sql
-- Check current coverage
SELECT * FROM public.get_use_coverage_stats();

-- Expected: ~86% with_main_use (1.4M properties without assignments)

-- Check properties needing assignment
SELECT
  COUNT(*) as total,
  COUNT(pul.property_id) as has_assignment,
  COUNT(*) - COUNT(pul.property_id) as needs_assignment
FROM public.florida_parcels fp
LEFT JOIN public.mv_property_use_latest pul ON pul.property_id = fp.id;
```

### 2. Backup Current State (CRITICAL)
```bash
# Create backup before migration
pg_dump -h $SUPABASE_HOST -U postgres -d postgres \
  --table=public.property_use_assignment \
  --table=public.use_taxonomy \
  --table=public.mv_property_use_latest \
  --table=public.mv_use_counts_by_geo \
  > backup_property_use_$(date +%Y%m%d_%H%M%S).sql

# Or use Supabase dashboard: Database → Backups → Create Backup
```

### 3. Verify Schema is Deployed
```sql
-- Ensure M0 schema exists
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
  'dor_use_codes',
  'use_taxonomy',
  'property_use_assignment',
  'mv_property_use_latest'
);

-- Should return 4 tables
```

## Execution Steps

### Step 1: Add Missing Taxonomy (1 minute)
```bash
# Run via Supabase CLI
supabase db execute -f supabase/migrations/20251103_add_missing_subuse_taxonomy.sql

# Or via psql
psql $DATABASE_URL -f supabase/migrations/20251103_add_missing_subuse_taxonomy.sql
```

**Expected Output:**
```
BEGIN
INSERT 0 1
 checkpoint | code | name | level | parent_code
------------+------+------+-------+-------------
 SUBUSE TAXONOMY VERIFICATION | CONDOMINIUM | Condominium | 2 | RESIDENTIAL
COMMIT
```

**Verification:**
```sql
SELECT * FROM public.use_taxonomy WHERE code = 'CONDOMINIUM';
```

### Step 2: Run Main Migration (15-30 minutes)
```bash
# Run via Supabase CLI
supabase db execute -f supabase/migrations/20251103_standardize_null_property_use.sql

# Or via psql (recommended for progress monitoring)
psql $DATABASE_URL -f supabase/migrations/20251103_standardize_null_property_use.sql
```

**Expected Progress (via NOTICE messages):**
```
NOTICE:  Safety check passed: 1400000 properties will be updated
NOTICE:  Batch 1 complete: Residential properties assigned
NOTICE:  Batch 2 complete: Commercial properties assigned
NOTICE:  Batch 3 complete: Industrial properties assigned
NOTICE:  Batch 4 complete: Agricultural properties assigned
NOTICE:  Batch 5 complete: Institutional properties assigned
NOTICE:  Batch 6 complete: Government properties assigned
NOTICE:  Batch 7 complete: Miscellaneous/Centrally Assessed properties assigned
NOTICE:  DOR use code integers updated
NOTICE:  Materialized views refreshed
```

**Expected Timeline:**
- Pre-migration stats: 10 seconds
- Safety checks: 5 seconds
- Batch 1 (Residential): 5-8 minutes (~900K records)
- Batch 2 (Commercial): 2-3 minutes (~250K records)
- Batch 3 (Industrial): 30 seconds (~40K records)
- Batch 4 (Agricultural): 1 minute (~80K records)
- Batch 5 (Institutional): 20 seconds (~25K records)
- Batch 6 (Government): 20 seconds (~25K records)
- Batch 7 (Misc/Central): 20 seconds (~30K records)
- Update dor_use_code_int: 2-3 minutes
- Refresh MVs: 2-3 minutes
- Post-migration stats: 30 seconds

**Total Time: 15-30 minutes**

### Step 3: Verify Migration Success
```sql
-- 1. Check coverage increase
SELECT * FROM public.get_use_coverage_stats();
-- Expected: ~95-98% coverage (up from ~86%)

-- 2. Check assignment distribution
SELECT
  main_code,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct
FROM public.property_use_assignment
WHERE created_at >= CURRENT_DATE
GROUP BY main_code
ORDER BY count DESC;

-- Expected distribution:
-- RESIDENTIAL: ~65-70% (900K-1M)
-- COMMERCIAL: ~15-20% (210K-280K)
-- INDUSTRIAL: ~2-3% (30K-40K)
-- AGRICULTURAL: ~5-7% (70K-100K)
-- INSTITUTIONAL: ~1-2% (15K-30K)
-- GOVERNMENT: ~1-2% (15K-30K)
-- MISC/CENTRAL/NONAG: ~2-3% (30K-40K)

-- 3. Check confidence scores
SELECT
  CASE
    WHEN confidence >= 0.95 THEN 'Excellent (95%+)'
    WHEN confidence >= 0.85 THEN 'Good (85-94%)'
    WHEN confidence >= 0.70 THEN 'Fair (70-84%)'
    ELSE 'Low (<70%)'
  END as confidence_range,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct
FROM public.property_use_assignment
WHERE created_at >= CURRENT_DATE
GROUP BY confidence_range
ORDER BY MIN(confidence) DESC;

-- Expected:
-- Excellent: ~70%
-- Good: ~25%
-- Fair: ~5%
-- Low: <1%

-- 4. Sample updated records
SELECT
  fp.parcel_id,
  fp.county,
  fp.property_use as dor_code,
  pua.main_code,
  pua.subuse_code,
  pua.confidence,
  ut_main.name as main_name,
  ut_sub.name as subuse_name
FROM public.florida_parcels fp
JOIN public.property_use_assignment pua ON pua.property_id = fp.id
LEFT JOIN public.use_taxonomy ut_main ON ut_main.code = pua.main_code
LEFT JOIN public.use_taxonomy ut_sub ON ut_sub.code = pua.subuse_code
WHERE pua.created_at >= CURRENT_DATE
ORDER BY RANDOM()
LIMIT 20;

-- 5. Check for issues
SELECT
  'Quality Checks' as checkpoint,
  COUNT(*) FILTER (WHERE confidence < 0.7) as low_confidence,
  COUNT(*) FILTER (WHERE main_code IS NULL) as null_main_code,
  COUNT(*) FILTER (WHERE review_state = 'needs_review') as needs_review
FROM public.property_use_assignment
WHERE created_at >= CURRENT_DATE;

-- Expected: All zeros (no quality issues)
```

### Step 4: Performance Verification
```sql
-- Test filter query performance (should use indexes)
EXPLAIN ANALYZE
SELECT COUNT(*)
FROM public.florida_parcels fp
JOIN public.mv_property_use_latest pul ON pul.property_id = fp.id
WHERE pul.main_code = 'RESIDENTIAL'
AND fp.county = 'MIAMI-DADE'
AND fp.just_value > 500000;

-- Expected: Index scan, execution time <100ms
```

## Post-Migration Actions

### 1. Clear Application Caches
```bash
# Clear Redis cache (if using)
redis-cli FLUSHDB

# Or specific keys
redis-cli DEL "property:counts:*"
redis-cli DEL "property:filters:*"
```

### 2. Update Frontend
- Refresh property filter dropdowns
- Clear any cached property counts
- Test all property filter combinations
- Verify property detail pages show USE/SUBUSE

### 3. Monitor Performance
```sql
-- Monitor slow queries
SELECT
  query,
  calls,
  mean_exec_time,
  total_exec_time
FROM pg_stat_statements
WHERE query LIKE '%property_use_assignment%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check materialized view refresh time
SELECT
  schemaname,
  matviewname,
  last_refresh
FROM pg_matviews
WHERE matviewname LIKE 'mv_property_use%';
```

## Rollback Procedure (EMERGENCY ONLY)

⚠️ **Only use if migration causes critical issues**

### When to Rollback
- Coverage dropped instead of increased
- Application errors referencing property_use_assignment
- Query performance degraded significantly
- Data integrity issues detected

### Rollback Steps
```bash
# 1. Run rollback migration
psql $DATABASE_URL -f supabase/migrations/20251103_rollback_standardize_null_property_use.sql

# 2. Verify rollback
psql $DATABASE_URL -c "SELECT * FROM public.get_use_coverage_stats();"
# Expected: ~86% coverage (back to pre-migration state)

# 3. Restore from backup (if rollback script fails)
pg_restore -h $SUPABASE_HOST -U postgres -d postgres \
  backup_property_use_YYYYMMDD_HHMMSS.sql
```

## Troubleshooting

### Issue: Migration Timeout
**Solution:** Increase statement timeout before migration
```sql
-- Set longer timeout (1 hour)
SET statement_timeout = '3600000'; -- 1 hour in milliseconds

-- Then run migration
\i supabase/migrations/20251103_standardize_null_property_use.sql
```

### Issue: Safety Check Fails
**Error:** `Safety check failed: X properties to update exceeds safety limit of 2M`

**Solution:** Verify this is expected, then increase limit in migration file:
```sql
-- Line 43-44 in migration file
if properties_to_update > 2000000 then
  -- Change to: if properties_to_update > 3000000 then
```

### Issue: Foreign Key Violation on subuse_code
**Error:** `insert or update on table "property_use_assignment" violates foreign key constraint`

**Solution:** Run taxonomy migration first:
```bash
psql $DATABASE_URL -f supabase/migrations/20251103_add_missing_subuse_taxonomy.sql
```

### Issue: Materialized View Refresh Slow
**Solution:** Refresh views manually with CONCURRENTLY option:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_property_use_latest;
REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_use_counts_by_geo;
```

### Issue: Low Coverage After Migration
**Check:** Verify property_use column has data:
```sql
SELECT
  COUNT(*) as total,
  COUNT(property_use) as has_code,
  COUNT(*) - COUNT(property_use) as null_code
FROM public.florida_parcels;
```

## Success Criteria

✅ Migration is successful if:
1. Coverage increases from ~86% to ~95-98%
2. All 7 batches complete without errors
3. Materialized views refresh successfully
4. Post-migration verification queries return expected results
5. No low-confidence assignments (<0.7)
6. Property filters work in UI
7. Query performance is acceptable (<100ms for indexed queries)

## Support

If you encounter issues:
1. Check Supabase dashboard → Database → Logs
2. Review pg_stat_statements for slow queries
3. Verify M0 schema is fully deployed
4. Check foreign key constraints on use_taxonomy
5. Ensure materialized views exist and have data

## DOR Code Mapping Reference

| DOR Range | Category | Confidence | Example Codes |
|-----------|----------|------------|---------------|
| 00-09 | RESIDENTIAL | 0.80-0.95 | 1=SFR, 4=Condo, 8=Multi-family |
| 10-39 | COMMERCIAL | 0.70-0.95 | 11=Retail, 17=Office, 39=Hotel |
| 40-49 | INDUSTRIAL | 0.70-0.90 | 41=Light Mfg, 48=Warehouse |
| 50-69 | AGRICULTURAL | 0.90 | 51-53=Cropland, 60-65=Grazing |
| 70-79 | INSTITUTIONAL | 0.70-0.90 | 71=Church, 72=Private School |
| 80-89 | GOVERNMENT | 0.95 | 83=Public School, 85=Hospital |
| 90-99 | MISC/CENTRAL/NONAG | 0.85 | 98=Central, 99=Non-ag |

## Timeline Summary

| Task | Duration | Status |
|------|----------|--------|
| Pre-checks | 2 min | ⏳ Pending |
| Add Taxonomy | 1 min | ⏳ Pending |
| Main Migration | 15-30 min | ⏳ Pending |
| Verification | 5 min | ⏳ Pending |
| Cache Clear | 2 min | ⏳ Pending |
| **Total** | **25-40 min** | ⏳ Pending |

---

**Migration Date:** 2025-11-03
**PDR Reference:** FL-USETAX-PDR-001 v1.0.0
**Estimated Impact:** ~1.4M properties standardized
**Risk Level:** Medium (large batch update, rollback available)
