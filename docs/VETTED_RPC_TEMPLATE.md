# Vetted RPC Template (Supabase)

This template guides the creation of secure, parameterized RPCs with proper RLS.

## 1) Postgres Function (SQL)

```sql
-- Example: upsert_permit(record jsonb)
create or replace function public.upsert_permit(rec jsonb)
returns void
language plpgsql
security definer
as $$
begin
  -- validate required fields
  if rec ? 'permit_number' is false then
    raise exception 'permit_number is required';
  end if;

  insert into public.florida_permits (
    permit_number, county_code, status, description, raw_data, updated_at
  ) values (
    rec->>'permit_number',
    rec->>'county_code',
    coalesce(rec->>'status', 'unknown'),
    left(rec->>'description', 1000),
    rec,
    now()
  )
  on conflict (permit_number, county_code)
  do update set
    status = excluded.status,
    description = excluded.description,
    raw_data = excluded.raw_data,
    updated_at = now();
end;
$$;
```

Notes:
- SECURITY DEFINER: required when RLS would otherwise block; set function owner carefully.
- Validate inputs to avoid injection and ensure data integrity (e.g., length caps, required fields).

## 2) RLS Policy

```sql
alter table public.florida_permits enable row level security;

-- Read policy
create policy fp_read on public.florida_permits
for select
to authenticated
using (true);

-- Write policy via RPC only (optional)
-- Alternatively, use a service role for writes and keep client read-only.
```

## 3) Calling from Code

Use the safe helper's RPC call:

```py
from apps.common.supabase_helpers import SupabaseClient

sb = SupabaseClient()
sb.call_rpc('upsert_permit', { 'rec': permit_record_as_json })
```

## 4) Prohibitions

- Do not create generic `execute_sql` RPCs that accept arbitrary SQL strings.
- Do not bypass RLS or expose system catalogs.

