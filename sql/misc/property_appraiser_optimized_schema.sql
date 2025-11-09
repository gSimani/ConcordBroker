-- ============================================================================
-- FLORIDA PROPERTY APPRAISER DATABASE SCHEMA (Supabase-optimized)
-- ============================================================================

-- 1) PROPERTY ASSESSMENTS (NAL)
create table if not exists public.property_assessments (
  id bigint primary key generated always as identity,
  parcel_id text not null,
  county_code text,
  county_name text,
  
  owner_name text,
  owner_address text,
  owner_city text,
  owner_state text,
  owner_zip text,
  
  property_address text,
  property_city text,
  property_zip text,
  property_use_code text,
  tax_district text,
  subdivision text,
  
  just_value numeric,
  assessed_value numeric,
  taxable_value numeric,
  land_value numeric,
  building_value numeric,
  
  total_sq_ft integer,
  living_area integer,
  year_built integer,
  bedrooms integer,
  bathrooms numeric(3,1),
  pool boolean default false,
  
  tax_year integer default 2025,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  
  constraint property_assessments_unique unique (parcel_id, county_code, tax_year)
);

-- 2) PROPERTY OWNERS (NAP)
create table if not exists public.property_owners (
  id bigint primary key generated always as identity,
  parcel_id text not null,
  county_code text,
  county_name text,
  
  owner_sequence integer default 1,
  owner_name text,
  owner_type text,
  
  mailing_address_1 text,
  mailing_address_2 text,
  mailing_city text,
  mailing_state text,
  mailing_zip text,
  mailing_country text default 'USA',
  
  ownership_percentage numeric(5,2) default 100.00,
  
  tax_year integer default 2025,
  created_at timestamp with time zone default now(),
  
  constraint property_owners_unique unique (parcel_id, county_code, owner_sequence, tax_year)
);

-- 3) PROPERTY SALES (SDF)
create table if not exists public.property_sales (
  id bigint primary key generated always as identity,
  parcel_id text not null,
  county_code text,
  county_name text,
  
  sale_date date,
  sale_price numeric,
  sale_type text,
  deed_type text,
  
  grantor_name text,
  grantee_name text,
  
  qualified_sale boolean default false,
  vacant_at_sale boolean default false,
  multi_parcel_sale boolean default false,
  
  book_page text,
  instrument_number text,
  verification_code text,
  
  tax_year integer default 2025,
  created_at timestamp with time zone default now()
);

-- 4) NAV SUMMARIES (NAV N)
create table if not exists public.nav_summaries (
  id bigint primary key generated always as identity,
  parcel_id text not null,
  county_code text,
  county_name text,
  
  tax_account_number text,
  roll_type text,
  tax_year integer default 2024,
  total_assessments numeric,
  num_assessments integer,
  tax_roll_sequence integer,
  
  created_at timestamp with time zone default now(),
  
  constraint nav_summaries_unique unique (parcel_id, county_code, tax_year)
);

-- 5) NAV DETAILS (NAV D)
create table if not exists public.nav_details (
  id bigint primary key generated always as identity,
  parcel_id text not null,
  county_code text,
  county_name text,
  
  levy_id text,
  levy_name text,
  local_gov_code text,
  function_code text,
  assessment_amount numeric,
  tax_roll_sequence integer,
  
  tax_year integer default 2024,
  created_at timestamp with time zone default now()
);

-- 6) MASTER PROPERTIES (Unified, materialized table for fast site reads)
create table if not exists public.properties_master (
  id bigint primary key generated always as identity,
  parcel_id text unique not null,
  folio_number text,
  county_code text,
  county_name text,
  
  property_address text,
  property_city text,
  property_state text default 'FL',
  property_zip text,
  latitude numeric(10,8),
  longitude numeric(11,8),
  
  owner_name text,
  owner_type text,
  owner_address text,
  owner_city text,
  owner_state text,
  owner_zip text,
  
  just_value numeric,
  assessed_value numeric,
  taxable_value numeric,
  land_value numeric,
  building_value numeric,
  
  property_use_code text,
  property_type text,
  total_sq_ft integer,
  living_area integer,
  lot_size numeric(10,2),
  year_built integer,
  bedrooms integer,
  bathrooms numeric(3,1),
  pool boolean default false,
  
  tax_amount numeric,
  nav_total numeric,
  homestead_exemption boolean default false,
  
  cap_rate numeric(5,2),
  price_per_sqft numeric(10,2),
  rental_estimate numeric(10,2),
  investment_score integer,
  
  last_sale_date date,
  last_sale_price numeric,
  days_on_market integer,
  
  has_corporate_owner boolean default false,
  sunbiz_entity_id text,
  
  data_quality_score integer,
  last_updated timestamp with time zone default now(),
  created_at timestamp with time zone default now()
);

-- 7) INDEXES
-- Trigram GIN indexes rely on pg_trgm (already installed in your project).
-- Assessments
create index if not exists idx_assessment_parcel on public.property_assessments(parcel_id);
create index if not exists idx_assessment_county on public.property_assessments(county_code);
create index if not exists idx_assessment_owner on public.property_assessments using gin (owner_name gin_trgm_ops);
create index if not exists idx_assessment_value on public.property_assessments(taxable_value);
create index if not exists idx_assessment_city on public.property_assessments(property_city);
create index if not exists idx_assessment_zip on public.property_assessments(property_zip);

-- Owners
create index if not exists idx_owner_parcel on public.property_owners(parcel_id);
create index if not exists idx_owner_name on public.property_owners using gin (owner_name gin_trgm_ops);
create index if not exists idx_owner_type on public.property_owners(owner_type);

-- Sales
create index if not exists idx_sale_parcel on public.property_sales(parcel_id);
create index if not exists idx_sale_date on public.property_sales(sale_date desc);
create index if not exists idx_sale_price on public.property_sales(sale_price);
create index if not exists idx_sale_buyer on public.property_sales using gin (grantee_name gin_trgm_ops);
create index if not exists idx_sale_seller on public.property_sales using gin (grantor_name gin_trgm_ops);

-- NAV
create index if not exists idx_nav_summary_parcel on public.nav_summaries(parcel_id);
create index if not exists idx_nav_detail_parcel on public.nav_details(parcel_id);
create index if not exists idx_nav_detail_amount on public.nav_details(assessment_amount);

-- Master
create index if not exists idx_master_parcel on public.properties_master(parcel_id);
create index if not exists idx_master_county on public.properties_master(county_code);
create index if not exists idx_master_owner on public.properties_master using gin (owner_name gin_trgm_ops);
create index if not exists idx_master_value on public.properties_master(taxable_value);
create index if not exists idx_master_location on public.properties_master(property_city, property_zip);
create index if not exists idx_master_investment on public.properties_master(investment_score) where investment_score is not null;

-- 8) RLS: enable and open read for anon+authenticated; writes via service_role (bypasses RLS)
alter table public.property_assessments enable row level security;
alter table public.property_owners enable row level security;
alter table public.property_sales enable row level security;
alter table public.nav_summaries enable row level security;
alter table public.nav_details enable row level security;
alter table public.properties_master enable row level security;

-- Public/Authenticated read policies (explicit TO roles; one operation per policy)
create policy "Read all" on public.property_assessments for select to anon, authenticated using (true);
create policy "Read all" on public.property_owners for select to anon, authenticated using (true);
create policy "Read all" on public.property_sales for select to anon, authenticated using (true);
create policy "Read all" on public.nav_summaries for select to anon, authenticated using (true);
create policy "Read all" on public.nav_details for select to anon, authenticated using (true);
create policy "Read all" on public.properties_master for select to anon, authenticated using (true);

-- No INSERT/UPDATE/DELETE policy needed for service_role; it bypasses RLS.

-- 9) Helper trigger to maintain updated_at where present
create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists trg_set_updated_at_assessments on public.property_assessments;
create trigger trg_set_updated_at_assessments
  before update on public.property_assessments
  for each row execute function public.set_updated_at();

drop trigger if exists trg_set_updated_at_master on public.properties_master;
create trigger trg_set_updated_at_master
  before update on public.properties_master
  for each row execute function public.set_updated_at();

-- 10) Verification query
SELECT 'Schema deployment complete!' as status;