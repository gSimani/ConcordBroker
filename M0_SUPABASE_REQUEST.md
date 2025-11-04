# 🗄️ GUY WE NEED YOUR HELP WITH SUPABASE

## Request Overview

**PDR Reference:** FL-USETAX-PDR-001 v1.0.0
**Milestone:** M0 - Schema & Seeds (Week 1)
**Gate Target:** Gate A
**Request Type:** Schema Change + Seed Data + RPC Creation
**Priority:** HIGH
**Estimated Time:** 15-20 minutes
**Date:** 2025-11-01

## Context

Implementing **M0 (Schema & Seeds)** from the Production Design Requirements for the Florida Property USE/SUBUSE system. This establishes the canonical taxonomy for classifying all 9.1M Florida properties using a deterministic-first approach (DOR codes → County crosswalks → Rules → LLM fallback).

**Key Objectives:**
- Create normalized schema for Main USE (9 categories) and SUBUSE (20+ categories)
- Seed 100 Florida DOR land use codes (00-99) with official mappings
- Establish materialized views for fast filtering and counting
- Enable RLS policies for security (service role for ETL, read-only MVs for app users)
- Support mixed-use properties with share_pct and temporal tracking

**Success Criteria (Gate A):**
- ✅ All tables created successfully
- ✅ 100 DOR codes inserted
- ✅ 9 Main USE + 23 SUBUSE in taxonomy
- ✅ MVs refresh without error
- ✅ RPCs return results
- ✅ PostgREST endpoints accessible

---

## JSON Request

```json
{
  "request_type": "schema_change + seed_data + rpc_creation",
  "priority": "high",
  "milestone": "M0_gate_a",
  "pdr_reference": "FL-USETAX-PDR-001 v1.0.0",
  "context": "Establish canonical USE/SUBUSE taxonomy for 9.1M Florida properties with deterministic-first classification pipeline",
  "tasks": [
    {
      "task_id": 1,
      "action": "Run M0 Schema Migration - Create tables and indexes",
      "sql_file": "supabase/migrations/20251101_m0_schema_adapted.sql",
      "description": "Creates 4 new tables (dor_use_codes, use_taxonomy, county_local_code_xwalk, property_use_assignment), adds 2 columns to florida_parcels (dor_use_code_int, text_embedding), creates 2 materialized views, and sets up RLS policies",
      "verification": "select count(*) from information_schema.tables where table_schema='public' and table_name in ('dor_use_codes','use_taxonomy','county_local_code_xwalk','property_use_assignment'); -- Should return 4"
    },
    {
      "task_id": 2,
      "action": "Run M0 Seed Data - Populate DOR codes and taxonomy",
      "sql_file": "supabase/migrations/20251101_m0_seed_dor_uses.sql",
      "description": "Inserts 100 Florida DOR land use codes (00-99), 9 Main USE categories, and 23 SUBUSE categories into the taxonomy",
      "verification": "select count(*) from dor_use_codes; -- Should return 100\nselect count(*) from use_taxonomy where level = 1; -- Should return 9\nselect count(*) from use_taxonomy where level = 2; -- Should return 23"
    },
    {
      "task_id": 3,
      "action": "Run M0 RPC Creation - Create helper stored procedures",
      "sql_file": "supabase/migrations/20251101_m0_rpc_adapted.sql",
      "description": "Creates 5 RPCs: get_properties_without_assignment(), refresh_property_use_mvs(), get_use_coverage_stats(), get_use_method_stats(), get_use_review_queue_stats()",
      "verification": "select count(*) from information_schema.routines where routine_schema='public' and routine_name like '%use%'; -- Should return 5"
    },
    {
      "task_id": 4,
      "action": "Verify Materialized Views are refreshable",
      "sql": "select public.refresh_property_use_mvs(); -- Should complete without error",
      "verification": "select count(*) from mv_property_use_latest; -- Should return 0 (empty until M1 backfill)\nselect count(*) from mv_use_counts_by_geo; -- Should return 0 (empty until M1 backfill)"
    },
    {
      "task_id": 5,
      "action": "Verify RLS policies are active",
      "sql": "select tablename, policyname from pg_policies where schemaname = 'public' and tablename in ('property_use_assignment','county_local_code_xwalk');",
      "verification": "Should return policies for service_role access on both tables"
    },
    {
      "task_id": 6,
      "action": "Verify PostgREST endpoints are accessible",
      "api_test": [
        "GET /rest/v1/dor_use_codes?select=code,group_main,label&limit=10",
        "GET /rest/v1/use_taxonomy?select=code,name,level&level=eq.1",
        "POST /rest/v1/rpc/get_use_coverage_stats"
      ],
      "verification": "All endpoints should return 200 OK with expected data structure"
    }
  ],
  "rollback_plan": {
    "description": "Drop all M0 objects in reverse order",
    "sql": "-- Drop materialized views\ndrop materialized view if exists public.mv_use_counts_by_geo cascade;\ndrop materialized view if exists public.mv_property_use_latest cascade;\n\n-- Drop functions\ndrop function if exists public.get_properties_without_assignment() cascade;\ndrop function if exists public.refresh_property_use_mvs() cascade;\ndrop function if exists public.get_use_coverage_stats() cascade;\ndrop function if exists public.get_use_method_stats() cascade;\ndrop function if exists public.get_use_review_queue_stats() cascade;\n\n-- Drop tables\ndrop table if exists public.property_use_assignment cascade;\ndrop table if exists public.county_local_code_xwalk cascade;\ndrop table if exists public.use_taxonomy cascade;\ndrop table if exists public.dor_use_codes cascade;\n\n-- Remove columns from florida_parcels\nalter table public.florida_parcels drop column if exists dor_use_code_int;\nalter table public.florida_parcels drop column if exists text_embedding;"
  },
  "dependencies": {
    "extensions": ["vector (pgvector)"],
    "existing_tables": ["florida_parcels"],
    "required_permissions": ["service_role"],
    "notes": "Ensure pgvector extension is enabled in Supabase dashboard before running migrations"
  },
  "expected_outcomes": {
    "new_tables": 4,
    "new_columns": 2,
    "new_views": 2,
    "new_functions": 5,
    "seed_records": 132,
    "downtime": "None (additive changes only)",
    "impact": "Zero impact on existing queries (new tables/columns only)"
  }
}
```

---

## SQL Files Reference

All SQL files are located in: `C:\Users\gsima\Documents\MyProject\ConcordBroker\supabase\migrations\`

### File 1: 20251101_m0_schema_adapted.sql
**Purpose:** Create tables, indexes, materialized views, and RLS policies
**Lines:** ~180
**Tables Created:**
- `dor_use_codes` - Florida DOR codes (00-99)
- `use_taxonomy` - Hierarchical Main USE + SUBUSE
- `county_local_code_xwalk` - County-specific code mappings
- `property_use_assignment` - USE assignments per property

**Columns Added to florida_parcels:**
- `dor_use_code_int` (int) - Standardized DOR code as integer
- `text_embedding` (vector(768)) - For RAG/semantic search

**Materialized Views:**
- `mv_property_use_latest` - Latest assignment per property (avoids double counting)
- `mv_use_counts_by_geo` - Aggregated counts by county/Main/SUBUSE

### File 2: 20251101_m0_seed_dor_uses.sql
**Purpose:** Seed DOR codes and taxonomy
**Lines:** ~160
**Inserts:**
- 100 DOR codes (00-99) with group_main and label
- 9 Main USE categories (level 1)
- 23 SUBUSE categories (level 2)

### File 3: 20251101_m0_rpc_adapted.sql
**Purpose:** Create helper stored procedures
**Lines:** ~80
**Functions:**
1. `get_properties_without_assignment()` - Returns florida_parcels rows without USE assignment
2. `refresh_property_use_mvs()` - Refreshes both materialized views
3. `get_use_coverage_stats()` - Returns coverage metrics (total, with_main_use, with_subuse, percentages)
4. `get_use_method_stats()` - Returns method distribution (DOR, COUNTY_XWALK, RULES, RAG_LLM, MANUAL)
5. `get_use_review_queue_stats()` - Returns review_state distribution (accepted, needs_review, rejected)

---

## Pre-Deployment Checklist

**Before running migrations:**
- [ ] Verify pgvector extension is enabled: `select * from pg_available_extensions where name = 'vector';`
- [ ] Verify florida_parcels table exists: `select count(*) from florida_parcels;`
- [ ] Backup current schema (if needed): Supabase dashboard → Database → Backups
- [ ] Confirm service_role key is available for ETL operations

---

## Post-Deployment Verification Commands

```sql
-- 1. Verify tables created
select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in ('dor_use_codes', 'use_taxonomy', 'county_local_code_xwalk', 'property_use_assignment')
order by table_name;
-- Expected: 4 rows

-- 2. Verify DOR codes seeded
select code, group_main, label
from dor_use_codes
where code in (0, 1, 11, 39, 48, 99)
order by code;
-- Expected: 6 rows with correct labels

-- 3. Verify taxonomy structure
select level, count(*) as category_count
from use_taxonomy
group by level
order by level;
-- Expected: level 1 = 9, level 2 = 23

-- 4. Verify Main USE categories
select code, name
from use_taxonomy
where level = 1
order by code;
-- Expected: RESIDENTIAL, COMMERCIAL, INDUSTRIAL, AGRICULTURAL, INSTITUTIONAL, GOVERNMENT, MISC, CENTRAL, NONAG

-- 5. Verify SUBUSE examples
select code, name, parent_code
from use_taxonomy
where level = 2 and parent_code = 'COMMERCIAL'
order by code;
-- Expected: HOTEL, RETAIL_STORE, SHOPPING_CENTER, OFFICE, RESTAURANT, AUTO_SALES_SERVICE, GOLF, RACETRACK, CAMP

-- 6. Verify new columns on florida_parcels
select column_name, data_type
from information_schema.columns
where table_name = 'florida_parcels'
  and column_name in ('dor_use_code_int', 'text_embedding')
order by column_name;
-- Expected: 2 rows

-- 7. Verify materialized views
\dm
-- Expected: mv_property_use_latest, mv_use_counts_by_geo

-- 8. Test MV refresh
select public.refresh_property_use_mvs();
-- Expected: Success (even though MVs are empty)

-- 9. Verify RPCs
select routine_name
from information_schema.routines
where routine_schema = 'public'
  and routine_name like '%use%'
order by routine_name;
-- Expected: 5 functions

-- 10. Test coverage stats RPC
select * from public.get_use_coverage_stats();
-- Expected: Returns 1 row with total_properties = 9.1M, with_main_use = 0, coverage_pct = 0
```

---

## Expected Results

### Tables Created (4)
| Table | Rows (Post-M0) | Purpose |
|-------|----------------|---------|
| dor_use_codes | 100 | Florida DOR codes (00-99) |
| use_taxonomy | 32 | Main USE (9) + SUBUSE (23) |
| county_local_code_xwalk | 0 | County mappings (populated in M1) |
| property_use_assignment | 0 | USE assignments (populated in M1) |

### Columns Added to florida_parcels (2)
| Column | Type | Null? | Purpose |
|--------|------|-------|---------|
| dor_use_code_int | int | YES | Standardized DOR code (populated from property_use in M1) |
| text_embedding | vector(768) | YES | Text embedding for RAG/semantic search |

### Materialized Views (2)
| View | Rows (Post-M0) | Purpose |
|------|----------------|---------|
| mv_property_use_latest | 0 | Latest USE assignment per property (populated in M1) |
| mv_use_counts_by_geo | 0 | Aggregated counts by county/Main/SUBUSE (populated in M1) |

### Functions/RPCs (5)
| Function | Returns | Purpose |
|----------|---------|---------|
| get_properties_without_assignment() | setof florida_parcels | Find properties needing USE assignment |
| refresh_property_use_mvs() | void | Refresh both materialized views |
| get_use_coverage_stats() | table | Coverage metrics (total, with_use, percentages) |
| get_use_method_stats() | table | Method distribution (DOR, XWALK, RULES, LLM) |
| get_use_review_queue_stats() | table | Review state distribution |

---

## Next Steps After M0 Completion

Once Guy completes the Supabase deployment and all verification passes:

1. **Mark Gate A as PASSED** ✅
2. **Begin M1 (Deterministic Mapping - Week 2)**:
   - Populate `dor_use_code_int` from `property_use` (VARCHAR → INT conversion)
   - Import initial county crosswalks
   - Run ETL backfill for DOR-based Main USE assignment
   - Target: ≥95% coverage on 100k sample (Gate B)
3. **Create observability dashboards** for coverage, precision, drift monitoring
4. **Document any issues or blockers** in M0_COMPLETION_REPORT.md

---

## Questions for Guy

1. **pgvector status:** Is the pgvector extension already enabled, or do you need to enable it?
2. **RLS testing:** Do you want me to test the RLS policies with different role keys after deployment?
3. **MV refresh timing:** Should I set up a cron job to refresh MVs automatically, or manual refresh via RPC is sufficient for M0?
4. **Backup strategy:** Do you want a manual backup before running migrations, or rely on Supabase's automatic backups?

---

**Ready for your action, Guy!** Please run the three SQL migration files in order and report back the verification results. I'll be standing by to create the observability dashboards and begin M1 once Gate A is confirmed.

---

**Estimated Completion Time:** 15-20 minutes
**Risk Level:** LOW (additive changes only, no data modification, rollback plan available)
**Impact:** ZERO (no changes to existing tables or queries, new objects only)
