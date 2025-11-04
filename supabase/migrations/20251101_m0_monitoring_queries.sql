-- M0 Observability - Monitoring Queries
-- PDR: FL-USETAX-PDR-001 v1.0.0
-- Purpose: Real-time monitoring dashboards for USE/SUBUSE system
-- Date: 2025-11-01

-- ===================================================================
-- 1. COVERAGE DASHBOARD - Real-time coverage metrics
-- ===================================================================

-- Overall coverage summary
create or replace view public.v_use_coverage_summary as
select
  count(*) as total_properties,
  count(pul.main_code) as with_main_use,
  count(pul.subuse_code) as with_subuse,
  count(*) - count(pul.main_code) as unresolved,
  round(100.0 * count(pul.main_code) / nullif(count(*), 0), 2) as coverage_pct,
  round(100.0 * count(pul.subuse_code) / nullif(count(*), 0), 2) as subuse_pct,
  round(100.0 * (count(*) - count(pul.main_code)) / nullif(count(*), 0), 2) as unresolved_pct,
  now() as last_updated
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
where fp.year = 2025;

grant select on public.v_use_coverage_summary to anon, authenticated;

-- Coverage by county
create or replace view public.v_use_coverage_by_county as
select
  fp.county,
  count(*) as total_properties,
  count(pul.main_code) as with_main_use,
  count(pul.subuse_code) as with_subuse,
  round(100.0 * count(pul.main_code) / nullif(count(*), 0), 2) as coverage_pct,
  round(100.0 * count(pul.subuse_code) / nullif(count(*), 0), 2) as subuse_pct
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
where fp.year = 2025 and fp.county is not null
group by fp.county
order by total_properties desc;

grant select on public.v_use_coverage_by_county to anon, authenticated;

-- ===================================================================
-- 2. METHOD DISTRIBUTION DASHBOARD - Classification method tracking
-- ===================================================================

create or replace view public.v_use_method_distribution as
select
  coalesce(pua.method, 'UNASSIGNED') as method,
  count(*) as assignment_count,
  round(100.0 * count(*) / sum(count(*)) over(), 2) as percentage,
  round(avg(pua.confidence), 3) as avg_confidence,
  min(pua.created_at) as first_assignment,
  max(pua.created_at) as last_assignment
from public.florida_parcels fp
left join public.property_use_assignment pua on pua.property_id = fp.id
where fp.year = 2025
group by pua.method
order by assignment_count desc;

grant select on public.v_use_method_distribution to anon, authenticated;

-- ===================================================================
-- 3. REVIEW QUEUE DASHBOARD - Quality control monitoring
-- ===================================================================

create or replace view public.v_use_review_queue as
select
  coalesce(pua.review_state, 'unassigned') as review_state,
  count(*) as count,
  round(100.0 * count(*) / sum(count(*)) over(), 2) as percentage,
  round(avg(pua.confidence), 3) as avg_confidence,
  count(*) filter (where pua.created_at < now() - interval '7 days') as aged_over_7_days
from public.florida_parcels fp
left join public.property_use_assignment pua on pua.property_id = fp.id
where fp.year = 2025
group by pua.review_state
order by count desc;

grant select on public.v_use_review_queue to anon, authenticated;

-- ===================================================================
-- 4. MAIN USE DISTRIBUTION - Taxonomy breakdown
-- ===================================================================

create or replace view public.v_main_use_distribution as
select
  coalesce(pul.main_code, 'UNASSIGNED') as main_use,
  ut.name as use_name,
  count(*) as property_count,
  round(100.0 * count(*) / sum(count(*)) over(), 2) as percentage,
  round(avg(pul.confidence), 3) as avg_confidence
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
left join public.use_taxonomy ut on ut.code = pul.main_code
where fp.year = 2025
group by pul.main_code, ut.name
order by property_count desc;

grant select on public.v_main_use_distribution to anon, authenticated;

-- ===================================================================
-- 5. SUBUSE DISTRIBUTION - Detailed classification breakdown
-- ===================================================================

create or replace view public.v_subuse_distribution as
select
  pul.main_code,
  coalesce(pul.subuse_code, 'NO_SUBUSE') as subuse_code,
  ut.name as subuse_name,
  count(*) as property_count,
  round(100.0 * count(*) / sum(count(*)) over (partition by pul.main_code), 2) as pct_within_main,
  round(avg(pul.confidence), 3) as avg_confidence
from public.florida_parcels fp
left join public.mv_property_use_latest pul on pul.property_id = fp.id
left join public.use_taxonomy ut on ut.code = pul.subuse_code
where fp.year = 2025 and pul.main_code is not null
group by pul.main_code, pul.subuse_code, ut.name
order by pul.main_code, property_count desc;

grant select on public.v_subuse_distribution to anon, authenticated;

-- ===================================================================
-- 6. DATA QUALITY DASHBOARD - DOR code normalization tracking
-- ===================================================================

create or replace view public.v_dor_code_quality as
select
  count(*) as total_properties,
  count(dor_use_code_int) as with_dor_code_int,
  count(*) filter (where property_use ~ '^[0-9]{3}$') as valid_3digit_format,
  count(*) filter (where property_use ~ '^[0-9]{1,2}$' and length(property_use) < 3) as needs_padding,
  count(*) filter (where property_use !~ '^[0-9]+$') as non_numeric,
  count(*) filter (where property_use is null) as null_values,
  round(100.0 * count(dor_use_code_int) / nullif(count(*), 0), 2) as dor_int_coverage_pct,
  round(100.0 * count(*) filter (where property_use ~ '^[0-9]{3}$') / nullif(count(*), 0), 2) as normalized_pct,
  now() as checked_at
from public.florida_parcels
where year = 2025;

grant select on public.v_dor_code_quality to anon, authenticated;

-- ===================================================================
-- 7. PERFORMANCE METRICS - API and ETL monitoring
-- ===================================================================

-- Track MV refresh performance
create table if not exists public.mv_refresh_log (
  id uuid primary key default gen_random_uuid(),
  mv_name text not null,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  duration_ms int,
  row_count bigint,
  success boolean default true,
  error_message text
);

grant select on public.mv_refresh_log to anon, authenticated;
grant insert on public.mv_refresh_log to service_role;

-- Enhanced MV refresh function with logging
create or replace function public.refresh_property_use_mvs_logged()
returns void
language plpgsql security definer as $$
declare
  start_time timestamptz;
  end_time timestamptz;
  duration_ms int;
  row_count bigint;
begin
  -- Refresh mv_property_use_latest
  start_time := clock_timestamp();
  refresh materialized view public.mv_property_use_latest;
  end_time := clock_timestamp();
  duration_ms := extract(epoch from (end_time - start_time)) * 1000;

  select count(*) into row_count from public.mv_property_use_latest;

  insert into public.mv_refresh_log (mv_name, started_at, completed_at, duration_ms, row_count, success)
  values ('mv_property_use_latest', start_time, end_time, duration_ms, row_count, true);

  -- Refresh mv_use_counts_by_geo
  start_time := clock_timestamp();
  refresh materialized view public.mv_use_counts_by_geo;
  end_time := clock_timestamp();
  duration_ms := extract(epoch from (end_time - start_time)) * 1000;

  select count(*) into row_count from public.mv_use_counts_by_geo;

  insert into public.mv_refresh_log (mv_name, started_at, completed_at, duration_ms, row_count, success)
  values ('mv_use_counts_by_geo', start_time, end_time, duration_ms, row_count, true);

exception when others then
  insert into public.mv_refresh_log (mv_name, started_at, success, error_message)
  values ('BOTH', start_time, false, sqlerrm);
  raise;
end;
$$;

grant execute on function public.refresh_property_use_mvs_logged() to service_role;

-- ===================================================================
-- 8. ALERT THRESHOLDS - SLO monitoring
-- ===================================================================

create or replace view public.v_slo_status as
select
  'Coverage SLO (≥99.5%)' as metric,
  cov.coverage_pct as current_value,
  99.5 as target_value,
  case when cov.coverage_pct >= 99.5 then '✅ PASS' else '❌ FAIL' end as status
from public.v_use_coverage_summary cov

union all

select
  'Unresolved Rate SLO (≤0.5%)' as metric,
  cov.unresolved_pct as current_value,
  0.5 as target_value,
  case when cov.unresolved_pct <= 0.5 then '✅ PASS' else '❌ FAIL' end as status
from public.v_use_coverage_summary cov

union all

select
  'LLM Usage Target (<5%)' as metric,
  coalesce(method.percentage, 0) as current_value,
  5.0 as target_value,
  case when coalesce(method.percentage, 0) < 5.0 then '✅ PASS' else '⚠️ HIGH' end as status
from public.v_use_method_distribution method
where method.method = 'RAG_LLM';

grant select on public.v_slo_status to anon, authenticated;

-- ===================================================================
-- 9. DASHBOARD SUMMARY - Single query for main dashboard
-- ===================================================================

create or replace function public.get_use_dashboard_summary()
returns json
language sql stable as $$
  select json_build_object(
    'coverage', (select row_to_json(t) from (select * from public.v_use_coverage_summary) t),
    'method_distribution', (select json_agg(t) from (select * from public.v_use_method_distribution) t),
    'review_queue', (select json_agg(t) from (select * from public.v_use_review_queue) t),
    'main_use_top5', (select json_agg(t) from (select * from public.v_main_use_distribution limit 5) t),
    'data_quality', (select row_to_json(t) from (select * from public.v_dor_code_quality) t),
    'slo_status', (select json_agg(t) from (select * from public.v_slo_status) t),
    'last_refresh', (select max(completed_at) from public.mv_refresh_log where success = true)
  );
$$;

grant execute on function public.get_use_dashboard_summary() to anon, authenticated, service_role;

-- ===================================================================
-- 10. MONITORING INDEXES - Optimize dashboard queries
-- ===================================================================

create index if not exists idx_pua_created_at on public.property_use_assignment(created_at desc);
create index if not exists idx_pua_confidence on public.property_use_assignment(confidence) where confidence < 0.8;
create index if not exists idx_fp_year_county on public.florida_parcels(year, county) where year = 2025;
create index if not exists idx_mv_refresh_log_completed on public.mv_refresh_log(completed_at desc) where success = true;
