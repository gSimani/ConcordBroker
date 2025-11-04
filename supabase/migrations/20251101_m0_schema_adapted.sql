-- M0 Schema Adaptation for ConcordBroker
-- PDR: FL-USETAX-PDR-001 v1.0.0
-- Adapted from implementation pack to work with florida_parcels table
-- Date: 2025-11-01

begin;

-- Enable pgvector extension (required for text embeddings)
create extension if not exists vector;

-- === Canonical DOR land use codes (00–99) ===
create table if not exists public.dor_use_codes (
  code int primary key,
  group_main text not null,   -- e.g., RESIDENTIAL, COMMERCIAL, INDUSTRIAL, ...
  label text not null,        -- compact label, e.g., "Stores, one story"
  summary text                -- optional longer summary
);

-- === Hierarchical use taxonomy ===
create table if not exists public.use_taxonomy (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,  -- e.g., 'COMMERCIAL', 'HOTEL'
  name text not null,
  level int not null check (level in (1,2)), -- 1=Main, 2=Subuse
  parent_code text references public.use_taxonomy(code) on delete cascade
);

-- === County-local code crosswalk ===
create table if not exists public.county_local_code_xwalk (
  county_no int not null,               -- 11..77 (Florida county numbers)
  local_code text not null,             -- county-specific code
  dor_code int null references public.dor_use_codes(code),
  main_code text null references public.use_taxonomy(code),
  subuse_code text null references public.use_taxonomy(code),
  source text null,                     -- 'county site', 'manual review', etc.
  updated_at timestamptz not null default now(),
  primary key (county_no, local_code)
);

-- === Augment existing florida_parcels table ===
-- CRITICAL: We use florida_parcels instead of properties
-- Add columns needed for USE/SUBUSE system

-- Add integer DOR code column (our property_use is VARCHAR)
alter table public.florida_parcels
  add column if not exists dor_use_code_int int null;

-- Add vector column for text embeddings (RAG/semantic search)
alter table public.florida_parcels
  add column if not exists text_embedding vector(768) null;

-- Create indexes for performance
create index if not exists idx_florida_parcels_dor_use_int
  on public.florida_parcels(dor_use_code_int)
  where dor_use_code_int is not null;

create index if not exists idx_florida_parcels_text_embedding
  on public.florida_parcels
  using ivfflat (text_embedding vector_cosine_ops)
  with (lists = 100);

-- === Property USE assignment (supports mixed-use + temporal) ===
-- ADAPTED: References florida_parcels instead of properties
create table if not exists public.property_use_assignment (
  id uuid primary key default gen_random_uuid(),
  property_id uuid not null references public.florida_parcels(id) on delete cascade,
  main_code text not null references public.use_taxonomy(code),
  subuse_code text null references public.use_taxonomy(code),
  method text not null check (method in ('DOR','COUNTY_XWALK','RULES','RAG_LLM','MANUAL')),
  confidence numeric not null check (confidence between 0 and 1),
  source text null,
  share_pct numeric null check (share_pct between 0 and 1),
  effective_date date not null default now()::date,
  review_state text not null default 'accepted' check (review_state in ('accepted','needs_review','rejected')),
  created_at timestamptz not null default now()
);

-- Indexes for fast queries
create index if not exists idx_pua_property on public.property_use_assignment(property_id);
create index if not exists idx_pua_main on public.property_use_assignment(main_code);
create index if not exists idx_pua_subuse on public.property_use_assignment(subuse_code) where subuse_code is not null;
create index if not exists idx_pua_method on public.property_use_assignment(method);
create index if not exists idx_pua_review on public.property_use_assignment(review_state) where review_state = 'needs_review';

-- === Latest assignment per property (materialized view) ===
-- CRITICAL: Avoid double-counting with DISTINCT ON
drop materialized view if exists public.mv_property_use_latest cascade;
create materialized view public.mv_property_use_latest as
select distinct on (pua.property_id)
  pua.property_id,
  pua.main_code,
  pua.subuse_code,
  pua.method,
  pua.confidence,
  pua.share_pct,
  pua.effective_date,
  pua.created_at
from public.property_use_assignment pua
order by pua.property_id, pua.created_at desc;

-- Unique index on property_id for fast lookups
create unique index if not exists idx_mv_pul_property_id
  on public.mv_property_use_latest(property_id);

-- Indexes for filtering by Main USE and SUBUSE
create index if not exists idx_mv_pul_main on public.mv_property_use_latest(main_code);
create index if not exists idx_mv_pul_subuse on public.mv_property_use_latest(subuse_code) where subuse_code is not null;

-- === Counts by geography ===
-- ADAPTED: References florida_parcels instead of properties
drop materialized view if exists public.mv_use_counts_by_geo cascade;
create materialized view public.mv_use_counts_by_geo as
select
  fp.county_no,
  pul.main_code,
  pul.subuse_code,
  count(*) as property_count
from public.mv_property_use_latest pul
join public.florida_parcels fp on fp.id = pul.property_id
where fp.county_no is not null
group by fp.county_no, pul.main_code, pul.subuse_code;

-- Index for fast county queries
create index if not exists idx_mv_counts_geo
  on public.mv_use_counts_by_geo(county_no, main_code, subuse_code);

-- === RLS policies ===
-- Service role (Railway ETL) can write to assignment table
alter table public.property_use_assignment enable row level security;

create policy "Service role full access on property_use_assignment"
  on public.property_use_assignment
  for all
  to service_role
  using (true)
  with check (true);

-- Authenticated users read via MVs only (no direct table access)
create policy "Authenticated read property_use_assignment denied"
  on public.property_use_assignment
  for select
  to authenticated
  using (false);  -- Force use of materialized views

-- County crosswalk RLS
alter table public.county_local_code_xwalk enable row level security;

create policy "Service role full access on county_local_code_xwalk"
  on public.county_local_code_xwalk
  for all
  to service_role
  using (true)
  with check (true);

-- Public/anon can read reference tables
grant select on public.dor_use_codes to anon, authenticated;
grant select on public.use_taxonomy to anon, authenticated;

-- Grant select on MVs to authenticated users
grant select on public.mv_property_use_latest to anon, authenticated;
grant select on public.mv_use_counts_by_geo to anon, authenticated;

commit;
