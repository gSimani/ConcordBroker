-- Migration: Standardize NULL Property Use Values
-- Date: 2025-11-03
-- Purpose: Map ~1.4M properties with DOR codes to standardized USE/SUBUSE taxonomy
-- Impact: Properties with property_use values but no property_use_assignment records
-- PDR Reference: FL-USETAX-PDR-001 v1.0.0

-- Safety: Run in transaction
begin;

-- === STEP 1: Pre-migration Analysis ===
-- Record the current state for verification
create temp table pre_migration_stats as
select
  count(*) as total_properties,
  count(fp.id) filter (where pul.property_id is not null) as has_assignment,
  count(fp.id) filter (where pul.property_id is null and fp.property_use is not null) as needs_assignment,
  count(fp.id) filter (where fp.property_use is null) as no_dor_code
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id;

-- Display pre-migration stats
select
  'PRE-MIGRATION STATISTICS' as checkpoint,
  total_properties,
  has_assignment,
  needs_assignment,
  no_dor_code,
  round(100.0 * has_assignment / total_properties, 2) as coverage_pct
from pre_migration_stats;

-- === STEP 2: Safety Check ===
-- Prevent accidental overwrite if this script is run multiple times
do $$
declare
  properties_to_update bigint;
begin
  select count(*) into properties_to_update
  from public.florida_parcels fp
  left join public.mv_property_use_latest pul on pul.property_id = fp.id
  where pul.property_id is null
    and fp.property_use is not null;

  if properties_to_update > 2000000 then
    raise exception 'Safety check failed: % properties to update exceeds safety limit of 2M', properties_to_update;
  end if;

  raise notice 'Safety check passed: % properties will be updated', properties_to_update;
end $$;

-- === STEP 3: Create Helper Function to Parse DOR Codes ===
-- Normalizes various formats: '1', '01', '001', 'SFR', etc.
create or replace function parse_dor_code(raw_code text)
returns int
language plpgsql immutable as $$
declare
  normalized_code int;
begin
  -- Handle NULL or empty
  if raw_code is null or trim(raw_code) = '' then
    return null;
  end if;

  -- Try to parse as integer (handles '1', '01', '001')
  begin
    normalized_code := raw_code::int;
    -- Ensure it's in valid DOR range (0-99)
    if normalized_code >= 0 and normalized_code <= 99 then
      return normalized_code;
    end if;
  exception when others then
    -- Not a numeric code, try text mapping
    null;
  end;

  -- Map common text codes to DOR integers
  return case upper(trim(raw_code))
    -- Residential text codes
    when 'SFR' then 1
    when 'SINGLE FAMILY' then 1
    when 'RESIDENTIAL' then 1
    when 'CONDO' then 4
    when 'CONDOMINIUM' then 4
    when 'MOBILE HOME' then 2
    when 'MOBILE' then 2
    when 'MULTI-FAMILY' then 3
    when 'MULTIFAMILY' then 3
    when 'APARTMENT' then 3
    when 'VACANT RESIDENTIAL' then 0

    -- Commercial text codes
    when 'COM' then 11
    when 'COMMERCIAL' then 11
    when 'RETAIL' then 11
    when 'OFFICE' then 17
    when 'HOTEL' then 39
    when 'MOTEL' then 39
    when 'RESTAURANT' then 21

    -- Industrial text codes
    when 'IND' then 41
    when 'INDUSTRIAL' then 41
    when 'WAREHOUSE' then 48

    -- Agricultural text codes
    when 'AGR' then 50
    when 'AGRICULTURAL' then 50
    when 'FARM' then 50

    -- Vacant/Other
    when 'VAC' then 10
    when 'VACANT' then 10
    when 'VACANT LAND' then 10

    else null
  end;
end $$;

-- === STEP 4: Batch Insert Property Use Assignments ===
-- Map DOR codes to Main USE categories with confidence scoring
-- Process in batches to avoid timeouts and enable progress tracking

-- Batch 1: Residential (00-09)
insert into public.property_use_assignment (
  property_id,
  main_code,
  subuse_code,
  method,
  confidence,
  source,
  effective_date,
  review_state
)
select
  fp.id as property_id,
  'RESIDENTIAL' as main_code,
  case parse_dor_code(fp.property_use)
    when 4 then 'CONDOMINIUM'  -- We'll add this SUBUSE if needed
    else null
  end as subuse_code,
  'DOR' as method,
  case
    when parse_dor_code(fp.property_use) in (1,4) then 0.95  -- High confidence: Single Family, Condo
    when parse_dor_code(fp.property_use) in (2,3,8) then 0.90  -- High confidence: Mobile, Multi-family
    when parse_dor_code(fp.property_use) in (0,5,6,7,9) then 0.85  -- Medium confidence: Vacant, misc
    else 0.80
  end as confidence,
  'Migration 20251103: DOR code ' || fp.property_use as source,
  current_date as effective_date,
  'accepted' as review_state
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
where pul.property_id is null  -- No existing assignment
  and fp.property_use is not null
  and parse_dor_code(fp.property_use) between 0 and 9;

raise notice 'Batch 1 complete: Residential properties assigned';

-- Batch 2: Commercial (10-39)
insert into public.property_use_assignment (
  property_id,
  main_code,
  subuse_code,
  method,
  confidence,
  source,
  effective_date,
  review_state
)
select
  fp.id as property_id,
  'COMMERCIAL' as main_code,
  case parse_dor_code(fp.property_use)
    when 39 then 'HOTEL'
    when 21, 22 then 'RESTAURANT'
    when 17, 18, 19 then 'OFFICE'
    when 11, 12, 13, 14 then 'RETAIL_STORE'
    when 15, 16 then 'SHOPPING_CENTER'
    when 27 then 'AUTO_SALES_SERVICE'
    when 38 then 'GOLF'
    when 37 then 'RACETRACK'
    when 36 then 'CAMP'
    else null
  end as subuse_code,
  'DOR' as method,
  case
    when parse_dor_code(fp.property_use) in (11,17,21,39) then 0.95  -- High confidence: common types
    when parse_dor_code(fp.property_use) = 10 then 0.70  -- Lower: vacant commercial
    else 0.85
  end as confidence,
  'Migration 20251103: DOR code ' || fp.property_use as source,
  current_date as effective_date,
  'accepted' as review_state
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
where pul.property_id is null
  and fp.property_use is not null
  and parse_dor_code(fp.property_use) between 10 and 39;

raise notice 'Batch 2 complete: Commercial properties assigned';

-- Batch 3: Industrial (40-49)
insert into public.property_use_assignment (
  property_id,
  main_code,
  subuse_code,
  method,
  confidence,
  source,
  effective_date,
  review_state
)
select
  fp.id as property_id,
  'INDUSTRIAL' as main_code,
  case parse_dor_code(fp.property_use)
    when 48 then 'WAREHOUSE'
    when 41 then 'LIGHT_MANUFACTURING'
    when 42 then 'HEAVY_INDUSTRY'
    when 43 then 'LUMBER'
    when 44 then 'PACKING_PLANT'
    else null
  end as subuse_code,
  'DOR' as method,
  case
    when parse_dor_code(fp.property_use) = 40 then 0.70  -- Lower: vacant industrial
    else 0.90
  end as confidence,
  'Migration 20251103: DOR code ' || fp.property_use as source,
  current_date as effective_date,
  'accepted' as review_state
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
where pul.property_id is null
  and fp.property_use is not null
  and parse_dor_code(fp.property_use) between 40 and 49;

raise notice 'Batch 3 complete: Industrial properties assigned';

-- Batch 4: Agricultural (50-69)
insert into public.property_use_assignment (
  property_id,
  main_code,
  subuse_code,
  method,
  confidence,
  source,
  effective_date,
  review_state
)
select
  fp.id as property_id,
  'AGRICULTURAL' as main_code,
  case
    when parse_dor_code(fp.property_use) between 60 and 65 then 'AG_GRAZING'
    when parse_dor_code(fp.property_use) between 51 and 53 then 'AG_CROPLAND'
    when parse_dor_code(fp.property_use) between 54 and 59 then 'AG_TIMBER'
    else null
  end as subuse_code,
  'DOR' as method,
  0.90 as confidence,
  'Migration 20251103: DOR code ' || fp.property_use as source,
  current_date as effective_date,
  'accepted' as review_state
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
where pul.property_id is null
  and fp.property_use is not null
  and parse_dor_code(fp.property_use) between 50 and 69;

raise notice 'Batch 4 complete: Agricultural properties assigned';

-- Batch 5: Institutional (70-79)
insert into public.property_use_assignment (
  property_id,
  main_code,
  subuse_code,
  method,
  confidence,
  source,
  effective_date,
  review_state
)
select
  fp.id as property_id,
  'INSTITUTIONAL' as main_code,
  case parse_dor_code(fp.property_use)
    when 71 then 'RELIGIOUS'
    when 72 then 'SCHOOL_PRIVATE'
    when 73 then 'PRIVATE_HOSPITAL'
    else null
  end as subuse_code,
  'DOR' as method,
  case
    when parse_dor_code(fp.property_use) = 70 then 0.70  -- Lower: vacant institutional
    else 0.90
  end as confidence,
  'Migration 20251103: DOR code ' || fp.property_use as source,
  current_date as effective_date,
  'accepted' as review_state
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
where pul.property_id is null
  and fp.property_use is not null
  and parse_dor_code(fp.property_use) between 70 and 79;

raise notice 'Batch 5 complete: Institutional properties assigned';

-- Batch 6: Government (80-89)
insert into public.property_use_assignment (
  property_id,
  main_code,
  subuse_code,
  method,
  confidence,
  source,
  effective_date,
  review_state
)
select
  fp.id as property_id,
  'GOVERNMENT' as main_code,
  case parse_dor_code(fp.property_use)
    when 83 then 'PUBLIC_SCHOOL'
    when 84 then 'PUBLIC_COLLEGE'
    when 85 then 'PUBLIC_HOSPITAL'
    else null
  end as subuse_code,
  'DOR' as method,
  0.95 as confidence,  -- High confidence: government records are accurate
  'Migration 20251103: DOR code ' || fp.property_use as source,
  current_date as effective_date,
  'accepted' as review_state
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
where pul.property_id is null
  and fp.property_use is not null
  and parse_dor_code(fp.property_use) between 80 and 89;

raise notice 'Batch 6 complete: Government properties assigned';

-- Batch 7: Miscellaneous/Centrally Assessed (90-99)
insert into public.property_use_assignment (
  property_id,
  main_code,
  subuse_code,
  method,
  confidence,
  source,
  effective_date,
  review_state
)
select
  fp.id as property_id,
  case
    when parse_dor_code(fp.property_use) = 98 then 'CENTRAL'
    when parse_dor_code(fp.property_use) = 99 then 'NONAG'
    else 'MISC'
  end as main_code,
  null as subuse_code,
  'DOR' as method,
  0.85 as confidence,
  'Migration 20251103: DOR code ' || fp.property_use as source,
  current_date as effective_date,
  'accepted' as review_state
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
where pul.property_id is null
  and fp.property_use is not null
  and parse_dor_code(fp.property_use) between 90 and 99;

raise notice 'Batch 7 complete: Miscellaneous/Centrally Assessed properties assigned';

-- === STEP 5: Update dor_use_code_int column ===
-- Populate the integer DOR code column for faster querying
update public.florida_parcels fp
set dor_use_code_int = parse_dor_code(fp.property_use)
where fp.dor_use_code_int is null
  and fp.property_use is not null;

raise notice 'DOR use code integers updated';

-- === STEP 6: Refresh Materialized Views ===
-- Update the materialized views to reflect new assignments
refresh materialized view public.mv_property_use_latest;
refresh materialized view public.mv_use_counts_by_geo;

raise notice 'Materialized views refreshed';

-- === STEP 7: Post-migration Verification ===
-- Compare before and after
select
  'POST-MIGRATION STATISTICS' as checkpoint,
  count(*) as total_properties,
  count(pul.property_id) as has_assignment,
  count(*) - count(pul.property_id) as still_unassigned,
  round(100.0 * count(pul.property_id) / count(*), 2) as coverage_pct
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id;

-- Distribution by main USE category
select
  'ASSIGNMENT DISTRIBUTION' as checkpoint,
  main_code,
  count(*) as count,
  round(100.0 * count(*) / sum(count(*)) over (), 2) as percentage,
  round(avg(confidence), 3) as avg_confidence
from public.property_use_assignment
where created_at >= current_date  -- Today's assignments
group by main_code
order by count desc;

-- SUBUSE distribution (top 20)
select
  'TOP 20 SUBUSE CATEGORIES' as checkpoint,
  main_code,
  subuse_code,
  count(*) as count,
  round(avg(confidence), 3) as avg_confidence
from public.property_use_assignment
where created_at >= current_date
  and subuse_code is not null
group by main_code, subuse_code
order by count desc
limit 20;

-- Show sample of updated records
select
  'SAMPLE UPDATED RECORDS' as checkpoint,
  fp.parcel_id,
  fp.county,
  fp.property_use as original_dor_code,
  fp.dor_use_code_int as parsed_dor_int,
  pua.main_code,
  pua.subuse_code,
  pua.confidence,
  fp.just_value
from public.florida_parcels fp
join public.property_use_assignment pua on pua.property_id = fp.id
where pua.created_at >= current_date
order by random()
limit 10;

-- Check for potential issues
select
  'QUALITY CHECKS' as checkpoint,
  count(*) filter (where confidence < 0.7) as low_confidence_count,
  count(*) filter (where review_state = 'needs_review') as needs_review_count,
  count(*) filter (where main_code is null) as null_main_code_count
from public.property_use_assignment
where created_at >= current_date;

-- Drop helper function
drop function if exists parse_dor_code(text);

commit;

-- === EXPECTED RESULTS ===
/*
Coverage increase: ~14% → ~95%+
Total assignments created: ~1.4M
Distribution (approximate):
  - RESIDENTIAL: ~65-70% (900K-1M)
  - COMMERCIAL: ~15-20% (210K-280K)
  - INDUSTRIAL: ~2-3% (30K-40K)
  - AGRICULTURAL: ~5-7% (70K-100K)
  - INSTITUTIONAL: ~1-2% (15K-30K)
  - GOVERNMENT: ~1-2% (15K-30K)
  - MISC/CENTRAL/NONAG: ~2-3% (30K-40K)

Confidence scores:
  - 95%+ confidence: ~70% of assignments
  - 85-94% confidence: ~25% of assignments
  - 70-84% confidence: ~5% of assignments

Properties still unassigned:
  - NULL property_use: Expected (no DOR code available)
  - Invalid codes: <1% (will need manual review)
*/

-- === POST-MIGRATION ACTIONS ===
/*
1. Monitor performance:
   SELECT * FROM public.get_use_coverage_stats();

2. Check method distribution:
   SELECT * FROM public.get_use_method_stats();

3. Review low-confidence assignments:
   SELECT * FROM public.property_use_assignment
   WHERE confidence < 0.7 AND created_at >= CURRENT_DATE
   ORDER BY confidence ASC
   LIMIT 100;

4. Update any cached data in application:
   - Clear Redis cache for property filters
   - Refresh property type counts
   - Update search indexes if needed

5. Monitor query performance:
   - Check slow query logs
   - Ensure indexes are being used
   - Monitor materialized view refresh time
*/
