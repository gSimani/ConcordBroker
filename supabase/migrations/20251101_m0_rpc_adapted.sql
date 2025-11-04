-- M0 Helper RPCs (Adapted for florida_parcels)
-- PDR: FL-USETAX-PDR-001 v1.0.0
-- Date: 2025-11-01

-- === Get properties without USE assignment ===
-- ADAPTED: References florida_parcels instead of properties
create or replace function public.get_properties_without_assignment()
returns setof public.florida_parcels
language sql stable security definer as $$
  select fp.*
  from public.florida_parcels fp
  left join public.mv_property_use_latest pul on pul.property_id = fp.id
  where pul.property_id is null
  limit 10000;
$$;

-- === Refresh materialized views ===
create or replace function public.refresh_property_use_mvs()
returns void
language sql security definer as $$
  refresh materialized view public.mv_property_use_latest;
  refresh materialized view public.mv_use_counts_by_geo;
$$;

-- === Get USE/SUBUSE coverage stats ===
create or replace function public.get_use_coverage_stats()
returns table (
  total_properties bigint,
  with_main_use bigint,
  with_subuse bigint,
  coverage_pct numeric,
  subuse_pct numeric
)
language sql stable as $$
  select
    count(*) as total_properties,
    count(pul.main_code) as with_main_use,
    count(pul.subuse_code) as with_subuse,
    round(100.0 * count(pul.main_code) / nullif(count(*), 0), 2) as coverage_pct,
    round(100.0 * count(pul.subuse_code) / nullif(count(*), 0), 2) as subuse_pct
  from public.florida_parcels fp
  left join public.mv_property_use_latest pul on pul.property_id = fp.id;
$$;

-- === Get method distribution stats ===
create or replace function public.get_use_method_stats()
returns table (
  method text,
  assignment_count bigint,
  percentage numeric
)
language sql stable as $$
  select
    pua.method,
    count(*) as assignment_count,
    round(100.0 * count(*) / sum(count(*)) over(), 2) as percentage
  from public.property_use_assignment pua
  group by pua.method
  order by assignment_count desc;
$$;

-- === Get review queue stats ===
create or replace function public.get_use_review_queue_stats()
returns table (
  review_state text,
  count bigint,
  percentage numeric
)
language sql stable as $$
  select
    pua.review_state,
    count(*) as count,
    round(100.0 * count(*) / sum(count(*)) over(), 2) as percentage
  from public.property_use_assignment pua
  group by pua.review_state
  order by count desc;
$$;

-- Grant execute permissions to service_role and authenticated users
grant execute on function public.get_properties_without_assignment() to service_role;
grant execute on function public.refresh_property_use_mvs() to service_role;
grant execute on function public.get_use_coverage_stats() to anon, authenticated, service_role;
grant execute on function public.get_use_method_stats() to anon, authenticated, service_role;
grant execute on function public.get_use_review_queue_stats() to anon, authenticated, service_role;
