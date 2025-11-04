# Property Use Standardization Migration - Complete Summary

## Executive Summary

**Objective:** Standardize ~1.4M properties (14% of database) with DOR property_use codes but no property_use_assignment records.

**Impact:** Increases property use coverage from ~86% to ~95-98%, enabling accurate property filtering and analysis.

**Risk Level:** Medium (large batch update, rollback available)

**Estimated Duration:** 25-40 minutes

**Status:** ✅ Ready for execution

## Files Delivered

### Migration Files (in order of execution)

| # | File | Purpose | Duration | Status |
|---|------|---------|----------|--------|
| 1 | `20251103_add_missing_subuse_taxonomy.sql` | Add CONDOMINIUM subuse | 1 min | Required First |
| 2 | `20251103_standardize_null_property_use.sql` | Main standardization migration | 15-30 min | Required Second |
| 3 | `20251103_rollback_standardize_null_property_use.sql` | Emergency rollback | 5 min | Emergency Only |

### Documentation Files

| File | Purpose |
|------|---------|
| `20251103_EXECUTION_INSTRUCTIONS.md` | Complete step-by-step execution guide |
| `20251103_DOR_CODE_MAPPINGS.md` | Detailed DOR code → USE/SUBUSE mappings |
| `PROPERTY_USE_STANDARDIZATION_SUMMARY.md` | This file - executive summary |

## What This Migration Does

### 1. Creates Helper Function
- **parse_dor_code(text)** - Normalizes various DOR code formats:
  - Handles numeric codes: '1', '01', '001' → 1
  - Maps text codes: 'SFR', 'CONDO', 'IND' → numeric
  - Returns NULL for invalid/unmapped codes

### 2. Batch Inserts Property Use Assignments
Creates assignments in 7 batches to prevent timeouts:

| Batch | Category | DOR Range | Estimated Count | Avg Confidence |
|-------|----------|-----------|-----------------|----------------|
| 1 | RESIDENTIAL | 00-09 | ~900K | 0.88 |
| 2 | COMMERCIAL | 10-39 | ~250K | 0.86 |
| 3 | INDUSTRIAL | 40-49 | ~40K | 0.85 |
| 4 | AGRICULTURAL | 50-69 | ~80K | 0.90 |
| 5 | INSTITUTIONAL | 70-79 | ~25K | 0.84 |
| 6 | GOVERNMENT | 80-89 | ~25K | 0.95 |
| 7 | MISC/CENTRAL/NONAG | 90-99 | ~30K | 0.85 |

### 3. Updates Integer DOR Codes
- Populates `dor_use_code_int` column for faster querying
- Enables efficient filtering by numeric DOR codes

### 4. Refreshes Materialized Views
- **mv_property_use_latest** - Latest assignment per property
- **mv_use_counts_by_geo** - Counts by county and use type

### 5. Comprehensive Verification
- Pre/post migration statistics
- Distribution by category and confidence
- Sample records for manual review
- Quality checks for low confidence or issues

## Expected Results

### Coverage Improvement
```
Before:  ~86% coverage (1.4M properties without assignments)
After:   ~95-98% coverage (~1.35M new assignments)
Remaining: Properties with NULL or invalid DOR codes
```

### Distribution by Category
```
RESIDENTIAL:         65-70% (~900K-1M properties)
COMMERCIAL:          15-20% (~210K-280K properties)
INDUSTRIAL:          2-3%   (~30K-40K properties)
AGRICULTURAL:        5-7%   (~70K-100K properties)
INSTITUTIONAL:       1-2%   (~15K-30K properties)
GOVERNMENT:          1-2%   (~15K-30K properties)
MISC/CENTRAL/NONAG:  2-3%   (~30K-40K properties)
```

### Confidence Scores
```
Excellent (95%+):  ~70% of assignments
Good (85-94%):     ~25% of assignments
Fair (70-84%):     ~5% of assignments
Low (<70%):        <1% of assignments (needs review)
```

## DOR Code Mapping Examples

### Residential Mappings
| Input Code | Parsed | Main Code | Subuse Code | Confidence |
|------------|--------|-----------|-------------|------------|
| '1', '01', '001', 'SFR' | 1 | RESIDENTIAL | NULL | 0.95 |
| '4', '04', 'CONDO' | 4 | RESIDENTIAL | CONDOMINIUM | 0.95 |
| '2', '02', 'MOBILE' | 2 | RESIDENTIAL | NULL | 0.90 |
| '3', '03', 'APARTMENT' | 3 | RESIDENTIAL | NULL | 0.90 |

### Commercial Mappings
| Input Code | Parsed | Main Code | Subuse Code | Confidence |
|------------|--------|-----------|-------------|------------|
| '11', 'RETAIL' | 11 | COMMERCIAL | RETAIL_STORE | 0.95 |
| '17', '18', 'OFFICE' | 17 | COMMERCIAL | OFFICE | 0.95 |
| '39', 'HOTEL', 'MOTEL' | 39 | COMMERCIAL | HOTEL | 0.95 |
| '21', '22', 'RESTAURANT' | 21 | COMMERCIAL | RESTAURANT | 0.95 |

### Industrial Mappings
| Input Code | Parsed | Main Code | Subuse Code | Confidence |
|------------|--------|-----------|-------------|------------|
| '41', 'IND' | 41 | INDUSTRIAL | LIGHT_MANUFACTURING | 0.90 |
| '48', 'WAREHOUSE' | 48 | INDUSTRIAL | WAREHOUSE | 0.90 |
| '42' | 42 | INDUSTRIAL | HEAVY_INDUSTRY | 0.90 |

## Safety Features

### Pre-Execution Safety Checks
1. ✅ Verifies ≤2M properties to update (prevents accidental mass update)
2. ✅ Checks for existing assignments (prevents duplicates)
3. ✅ Validates schema exists (ensures M0 deployed)
4. ✅ Runs in transaction (atomic - all or nothing)

### Rollback Protection
1. ✅ Marks all assignments with source: 'Migration 20251103'
2. ✅ Tracks creation date for easy identification
3. ✅ Rollback script deletes only migration assignments
4. ✅ Preserves manual/RAG/rule-based assignments

### Data Quality Safeguards
1. ✅ Confidence scoring (0.70-0.95) based on code specificity
2. ✅ Foreign key validation on USE taxonomy
3. ✅ NULL handling for missing codes
4. ✅ Post-migration verification queries

## Execution Checklist

### Pre-Execution (5 minutes)
- [ ] Backup database (pg_dump or Supabase dashboard)
- [ ] Verify M0 schema deployed
- [ ] Check current coverage (~86% expected)
- [ ] Review execution instructions
- [ ] Schedule during low-traffic period

### Execution (25-40 minutes)
- [ ] Run taxonomy migration (20251103_add_missing_subuse_taxonomy.sql)
- [ ] Verify CONDOMINIUM subuse created
- [ ] Run main migration (20251103_standardize_null_property_use.sql)
- [ ] Monitor NOTICE messages for batch progress
- [ ] Wait for COMMIT confirmation

### Post-Execution (10 minutes)
- [ ] Verify coverage increased to ~95-98%
- [ ] Check distribution by category
- [ ] Review confidence scores
- [ ] Test property filters in UI
- [ ] Clear application caches
- [ ] Monitor query performance

## Common Issues & Solutions

### Issue: Migration Timeout
**Solution:** Increase statement timeout before migration:
```sql
SET statement_timeout = '3600000'; -- 1 hour
```

### Issue: Safety Check Fails
**Cause:** More than 2M properties to update
**Solution:** Review data, increase limit if valid, or investigate why count is high

### Issue: Foreign Key Violation
**Cause:** CONDOMINIUM subuse doesn't exist
**Solution:** Run taxonomy migration first (20251103_add_missing_subuse_taxonomy.sql)

### Issue: Low Coverage After Migration
**Cause:** Many NULL or invalid property_use values
**Solution:** Expected - properties without DOR codes cannot be assigned

### Issue: Materialized View Refresh Slow
**Solution:** Use CONCURRENTLY option or increase work_mem

## Performance Expectations

### Query Performance (with indexes)
```sql
-- Property filter query
SELECT COUNT(*) FROM florida_parcels fp
JOIN mv_property_use_latest pul ON pul.property_id = fp.id
WHERE pul.main_code = 'RESIDENTIAL'
AND fp.county = 'MIAMI-DADE'
AND fp.just_value > 500000;

Expected: <100ms (using indexes)
```

### Materialized View Refresh
```sql
REFRESH MATERIALIZED VIEW mv_property_use_latest;
Expected: 2-3 minutes for ~1.4M new assignments
```

### Batch Insert Performance
```
Batch 1 (Residential): 5-8 min (~900K inserts, ~2000/sec)
Batch 2 (Commercial): 2-3 min (~250K inserts, ~1500/sec)
Batches 3-7: <5 min total (~150K inserts combined)
```

## Integration Points

### Frontend Impact
- Property filter dropdowns will show accurate counts
- "Property Type" filter will work for 95-98% of properties
- Detail pages will display USE/SUBUSE taxonomy
- Search results will be more accurate

### Backend Impact
- `get_use_coverage_stats()` will show ~95-98% coverage
- `get_use_method_stats()` will show 'DOR' as primary method
- Materialized views will have 1.4M more records
- Query plans will use new indexes

### API Impact
- Property endpoints will return main_code and subuse_code
- Filter endpoints will support USE/SUBUSE filtering
- Stats endpoints will show updated distribution

## Monitoring & Maintenance

### Daily Monitoring
```sql
-- Check coverage stays high
SELECT * FROM get_use_coverage_stats();
-- Target: >95%

-- Check for review queue
SELECT COUNT(*) FROM property_use_assignment
WHERE review_state = 'needs_review';
-- Target: <100

-- Check materialized view freshness
SELECT matviewname, last_refresh
FROM pg_matviews
WHERE matviewname LIKE 'mv_property_use%';
-- Should be within 24 hours
```

### Weekly Review
```sql
-- Check low-confidence assignments
SELECT main_code, COUNT(*)
FROM property_use_assignment
WHERE confidence < 0.7
GROUP BY main_code;

-- Review unmapped codes
SELECT property_use, COUNT(*)
FROM florida_parcels
WHERE id NOT IN (
  SELECT property_id FROM mv_property_use_latest
)
AND property_use IS NOT NULL
GROUP BY property_use
ORDER BY COUNT(*) DESC
LIMIT 20;
```

### Monthly Refresh
```sql
-- Refresh materialized views
SELECT refresh_property_use_mvs();

-- Vacuum and analyze
VACUUM ANALYZE property_use_assignment;
VACUUM ANALYZE mv_property_use_latest;
```

## Success Criteria

✅ **Migration is successful if:**

1. **Coverage:** Increases from ~86% to ~95-98%
2. **Batch Completion:** All 7 batches complete without errors
3. **View Refresh:** Materialized views refresh successfully
4. **Data Quality:** No NULL main_code, <1% low confidence
5. **UI Functionality:** Property filters work correctly
6. **Performance:** Queries execute in <100ms with indexes
7. **No Errors:** No foreign key violations or constraint errors
8. **Rollback Ready:** Can rollback cleanly if needed

## Support Resources

### Documentation
- **Execution Guide:** `20251103_EXECUTION_INSTRUCTIONS.md`
- **DOR Mappings:** `20251103_DOR_CODE_MAPPINGS.md`
- **M0 Schema:** `20251101_m0_schema_adapted.sql`
- **M0 Seed Data:** `20251101_m0_seed_dor_uses.sql`

### Verification Queries
```sql
-- Overall stats
SELECT * FROM get_use_coverage_stats();

-- Method distribution
SELECT * FROM get_use_method_stats();

-- Sample assignments
SELECT * FROM property_use_assignment
WHERE created_at >= CURRENT_DATE
ORDER BY RANDOM()
LIMIT 10;
```

### Rollback Command
```bash
# EMERGENCY ONLY
psql $DATABASE_URL -f supabase/migrations/20251103_rollback_standardize_null_property_use.sql
```

## Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Pre-checks & Backup | 5 min | 5 min |
| Taxonomy Migration | 1 min | 6 min |
| Main Migration | 15-30 min | 21-36 min |
| Verification | 5 min | 26-41 min |
| Cache Clear | 2 min | 28-43 min |
| **Total** | **28-43 min** | - |

## Conclusion

This migration standardizes 1.4M properties using Florida DOR codes, creating high-quality property use assignments with confidence scoring, SUBUSE granularity, and comprehensive verification.

**Key Benefits:**
- 📊 95-98% property use coverage (up from 86%)
- 🎯 Accurate property filtering and analysis
- 🏆 High confidence (70% of assignments ≥0.95)
- 🔄 Safe rollback if issues arise
- 📈 Better user experience with filters
- 🚀 Foundation for future USE/SUBUSE features

**Ready to Execute:** All migration files created, tested logic, comprehensive documentation, and rollback plan in place.

---

**Migration ID:** 20251103_standardize_null_property_use
**PDR Reference:** FL-USETAX-PDR-001 v1.0.0
**Created:** 2025-11-03
**Estimated Impact:** ~1.4M properties standardized
**Risk Level:** Medium
**Rollback Available:** Yes
**Status:** ✅ Ready for Production
