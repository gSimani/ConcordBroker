-- Rollback Migration: Standardize NULL Property Use Values
-- Date: 2025-11-03
-- Purpose: Safely remove property use assignments created by migration 20251103
-- Impact: Removes ~1.4M assignments created by the standardization migration

-- Safety: Run in transaction
begin;

-- === STEP 1: Pre-rollback Verification ===
-- Record current state before rollback
select
  'PRE-ROLLBACK STATISTICS' as checkpoint,
  count(*) as total_assignments,
  count(*) filter (
    where method = 'DOR'
    and source like 'Migration 20251103%'
    and created_at >= '2025-11-03'::date
  ) as migration_assignments,
  count(*) filter (
    where method != 'DOR' or source not like 'Migration 20251103%'
  ) as other_assignments
from public.property_use_assignment;

-- === STEP 2: Safety Check ===
-- Prevent accidental deletion of non-migration data
do $$
declare
  assignments_to_delete bigint;
  total_assignments bigint;
begin
  -- Count migration-created assignments
  select count(*) into assignments_to_delete
  from public.property_use_assignment
  where method = 'DOR'
    and source like 'Migration 20251103%'
    and created_at >= '2025-11-03'::date;

  -- Count total assignments
  select count(*) into total_assignments
  from public.property_use_assignment;

  -- Prevent rollback if it would delete >80% of all assignments
  if assignments_to_delete > (total_assignments * 0.8) then
    raise exception 'Safety check failed: Would delete % of % total assignments (>80%%)',
      assignments_to_delete, total_assignments;
  end if;

  -- Prevent rollback if count is suspicious
  if assignments_to_delete = 0 then
    raise exception 'Safety check failed: No migration assignments found to rollback';
  end if;

  if assignments_to_delete > 2000000 then
    raise exception 'Safety check failed: % assignments to delete exceeds safety limit of 2M',
      assignments_to_delete;
  end if;

  raise notice 'Safety check passed: % assignments will be deleted', assignments_to_delete;
end $$;

-- === STEP 3: Delete Migration Assignments ===
-- Remove only assignments created by this migration
delete from public.property_use_assignment
where method = 'DOR'
  and source like 'Migration 20251103%'
  and created_at >= '2025-11-03'::date;

raise notice 'Migration assignments deleted';

-- === STEP 4: Clear dor_use_code_int for affected properties ===
-- Optional: Only clear if you want to completely reverse the migration
-- Comment out if you want to keep the parsed integer codes
update public.florida_parcels
set dor_use_code_int = null
where dor_use_code_int is not null
  and id not in (
    select property_id
    from public.property_use_assignment
  );

raise notice 'Orphaned dor_use_code_int values cleared';

-- === STEP 5: Refresh Materialized Views ===
-- Update views to reflect rollback
refresh materialized view public.mv_property_use_latest;
refresh materialized view public.mv_use_counts_by_geo;

raise notice 'Materialized views refreshed';

-- === STEP 6: Post-rollback Verification ===
-- Verify rollback completed successfully
select
  'POST-ROLLBACK STATISTICS' as checkpoint,
  count(*) as total_assignments,
  count(*) filter (
    where method = 'DOR'
    and source like 'Migration 20251103%'
    and created_at >= '2025-11-03'::date
  ) as remaining_migration_assignments,
  count(*) filter (
    where method != 'DOR' or source not like 'Migration 20251103%'
  ) as other_assignments
from public.property_use_assignment;

-- Check coverage stats
select
  'COVERAGE AFTER ROLLBACK' as checkpoint,
  count(*) as total_properties,
  count(pul.property_id) as has_assignment,
  count(*) - count(pul.property_id) as unassigned,
  round(100.0 * count(pul.property_id) / count(*), 2) as coverage_pct
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id;

-- Show distribution of remaining assignments
select
  'REMAINING ASSIGNMENT DISTRIBUTION' as checkpoint,
  method,
  count(*) as count,
  round(100.0 * count(*) / sum(count(*)) over (), 2) as percentage
from public.property_use_assignment
group by method
order by count desc;

commit;

-- === ROLLBACK VERIFICATION ===
/*
Expected Results:
- Migration assignments: ~1.4M → 0
- Coverage: ~95% → ~14% (back to pre-migration state)
- Remaining assignments: Only non-migration assignments (MANUAL, RULES, RAG_LLM, etc.)
- No errors or warnings

If rollback fails:
1. Check transaction log for errors
2. Verify date filter: created_at >= '2025-11-03'::date
3. Check source pattern: 'Migration 20251103%'
4. Ensure materialized views are refreshed
*/

-- === POST-ROLLBACK ACTIONS ===
/*
1. Verify data integrity:
   SELECT * FROM public.get_use_coverage_stats();

2. Check for orphaned records:
   SELECT COUNT(*) FROM public.florida_parcels fp
   LEFT JOIN public.mv_property_use_latest pul ON pul.property_id = fp.id
   WHERE pul.property_id IS NULL AND fp.property_use IS NOT NULL;

3. Clear application caches:
   - Clear Redis cache for property filters
   - Clear any cached property counts
   - Update search indexes if needed

4. If you need to re-run the migration:
   - Review any errors from the original migration
   - Adjust DOR code mappings if needed
   - Re-run: 20251103_standardize_null_property_use.sql
*/
