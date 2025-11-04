# 🗄️ GUY WE NEED YOUR HELP WITH SUPABASE

## Request Overview

**PDR Reference:** FL-USETAX-PDR-001 v1.0.0
**Milestone:** M0 - Observability Dashboards
**Request Type:** Views + Functions + Indexes
**Priority:** HIGH
**Estimated Time:** 10-15 minutes
**Date:** 2025-11-01

## Context

Deploying **M0 Observability System** - real-time monitoring views and functions for the Property USE/SUBUSE classification system. This enables the dashboard at `apps/web/public/property-use-dashboard.html` and provides comprehensive SLO tracking.

**Key Objectives:**
- Create 10 monitoring views for coverage, quality, and performance tracking
- Add enhanced MV refresh function with logging
- Create dashboard summary RPC for single-call API access
- Enable real-time SLO monitoring (≥99.5% coverage target)

**Success Criteria:**
- ✅ All 10 views created successfully
- ✅ Enhanced refresh function with logging works
- ✅ Dashboard summary RPC returns complete JSON
- ✅ Indexes optimize dashboard queries
- ✅ All endpoints accessible via PostgREST

---

## JSON Request

```json
{
  "request_type": "views + functions + indexes",
  "priority": "high",
  "milestone": "M0_observability",
  "pdr_reference": "FL-USETAX-PDR-001 v1.0.0",
  "context": "Deploy monitoring system for real-time USE/SUBUSE classification tracking and SLO validation",
  "tasks": [
    {
      "task_id": 1,
      "action": "Run M0 Monitoring Queries - Create observability views and functions",
      "sql_file": "supabase/migrations/20251101_m0_monitoring_queries.sql",
      "description": "Creates 10 monitoring views (coverage, SLO status, data quality, method distribution, review queue), 1 enhanced refresh function with logging, 1 dashboard summary RPC, and performance indexes",
      "verification": "select count(*) from information_schema.views where table_schema='public' and table_name like 'v_use_%' or table_name like 'v_slo_%' or table_name like 'v_dor_%'; -- Should return 10"
    },
    {
      "task_id": 2,
      "action": "Verify monitoring views return data",
      "sql": "select * from public.v_use_coverage_summary;",
      "verification": "Should return 1 row with total_properties, coverage_pct, etc."
    },
    {
      "task_id": 3,
      "action": "Verify SLO status view works",
      "sql": "select * from public.v_slo_status;",
      "verification": "Should return 3 rows with SLO metrics (Coverage ≥99.5%, Unresolved ≤0.5%, LLM <5%)"
    },
    {
      "task_id": 4,
      "action": "Test enhanced MV refresh with logging",
      "sql": "select public.refresh_property_use_mvs_logged();",
      "verification": "Should complete successfully and insert 2 rows into mv_refresh_log"
    },
    {
      "task_id": 5,
      "action": "Test dashboard summary RPC",
      "sql": "select public.get_use_dashboard_summary();",
      "verification": "Should return complete JSON with coverage, method_distribution, review_queue, main_use_top5, data_quality, slo_status, last_refresh"
    },
    {
      "task_id": 6,
      "action": "Verify data quality view",
      "sql": "select * from public.v_dor_code_quality;",
      "verification": "Should return 1 row showing normalized_pct, needs_padding count, etc."
    },
    {
      "task_id": 7,
      "action": "Verify PostgREST endpoints accessible",
      "api_test": [
        "GET /rest/v1/v_use_coverage_summary",
        "GET /rest/v1/v_slo_status",
        "GET /rest/v1/v_dor_code_quality",
        "POST /rest/v1/rpc/get_use_dashboard_summary"
      ],
      "verification": "All endpoints should return 200 OK with expected data structure"
    },
    {
      "task_id": 8,
      "action": "Verify performance indexes created",
      "sql": "select indexname from pg_indexes where schemaname='public' and (indexname like 'idx_pua_%' or indexname like 'idx_fp_year_%' or indexname like 'idx_mv_%');",
      "verification": "Should return 4 new indexes for optimizing dashboard queries"
    }
  ],
  "rollback_plan": {
    "description": "Drop all M0 observability objects",
    "sql": "-- Drop views\ndrop view if exists public.v_use_coverage_summary cascade;\ndrop view if exists public.v_use_coverage_by_county cascade;\ndrop view if exists public.v_use_method_distribution cascade;\ndrop view if exists public.v_use_review_queue cascade;\ndrop view if exists public.v_main_use_distribution cascade;\ndrop view if exists public.v_subuse_distribution cascade;\ndrop view if exists public.v_dor_code_quality cascade;\ndrop view if exists public.v_slo_status cascade;\n\n-- Drop functions\ndrop function if exists public.refresh_property_use_mvs_logged() cascade;\ndrop function if exists public.get_use_dashboard_summary() cascade;\n\n-- Drop tables\ndrop table if exists public.mv_refresh_log cascade;\n\n-- Drop indexes\ndrop index if exists public.idx_pua_created_at;\ndrop index if exists public.idx_pua_confidence;\ndrop index if exists public.idx_fp_year_county;\ndrop index if exists public.idx_mv_refresh_log_completed;"
  },
  "dependencies": {
    "existing_objects": [
      "florida_parcels table",
      "property_use_assignment table",
      "use_taxonomy table",
      "mv_property_use_latest view",
      "mv_use_counts_by_geo view"
    ],
    "required_permissions": ["service_role", "authenticated", "anon"],
    "notes": "Requires M0 schema & seeds to be already deployed (completed)"
  },
  "expected_outcomes": {
    "new_views": 10,
    "new_functions": 2,
    "new_tables": 1,
    "new_indexes": 4,
    "dashboard_enabled": true,
    "slo_tracking": "active",
    "downtime": "None (read-only views)",
    "impact": "Zero impact on existing queries (new monitoring layer only)"
  }
}
```

---

## SQL File Reference

**File:** `supabase/migrations/20251101_m0_monitoring_queries.sql`
**Lines:** ~350
**Purpose:** Complete observability system for USE/SUBUSE classification

### Objects Created:

**Monitoring Views (10):**
1. `v_use_coverage_summary` - Overall coverage metrics
2. `v_use_coverage_by_county` - Coverage by county breakdown
3. `v_use_method_distribution` - Classification method tracking
4. `v_use_review_queue` - Review queue status
5. `v_main_use_distribution` - Main USE distribution (top 10)
6. `v_subuse_distribution` - SUBUSE detail by Main USE
7. `v_dor_code_quality` - DOR code normalization tracking
8. `v_slo_status` - SLO compliance (Coverage ≥99.5%, Unresolved ≤0.5%, LLM <5%)

**Logging Table (1):**
9. `mv_refresh_log` - MV refresh performance tracking

**Functions/RPCs (2):**
10. `refresh_property_use_mvs_logged()` - Enhanced MV refresh with logging
11. `get_use_dashboard_summary()` - Single JSON endpoint for complete dashboard

**Performance Indexes (4):**
- `idx_pua_created_at` - property_use_assignment time-series queries
- `idx_pua_confidence` - Low-confidence filtering (<0.8)
- `idx_fp_year_county` - Year+county filtering
- `idx_mv_refresh_log_completed` - Successful refresh tracking

---

## Pre-Deployment Checklist

**Before running migration:**
- [x] Verify M0 schema deployed (tables created)
- [x] Verify M0 seeds loaded (100 DOR codes, 32 taxonomy)
- [x] Verify MVs exist (mv_property_use_latest, mv_use_counts_by_geo)
- [ ] Confirm normalization complete (optional, views work with or without data)

---

## Post-Deployment Verification Commands

```sql
-- 1. Verify all views created
select table_name
from information_schema.views
where table_schema = 'public'
  and (table_name like 'v_use_%' or table_name like 'v_slo_%' or table_name like 'v_dor_%')
order by table_name;
-- Expected: 8 views

-- 2. Test coverage summary
select * from v_use_coverage_summary;
-- Expected: 1 row with total_properties, coverage_pct, subuse_pct, etc.

-- 3. Test SLO status
select metric, current_value, target_value, status
from v_slo_status;
-- Expected: 3 rows (Coverage SLO, Unresolved Rate SLO, LLM Usage Target)

-- 4. Test data quality view
select total_properties, normalized_pct, needs_padding, non_numeric
from v_dor_code_quality;
-- Expected: 1 row showing normalization progress

-- 5. Test method distribution
select method, assignment_count, percentage
from v_use_method_distribution;
-- Expected: Rows showing UNASSIGNED, DOR, COUNTY_XWALK, etc. (initially all UNASSIGNED)

-- 6. Test review queue
select review_state, count, percentage
from v_use_review_queue;
-- Expected: Rows showing unassigned, accepted, needs_review, rejected

-- 7. Test enhanced MV refresh with logging
select refresh_property_use_mvs_logged();
-- Expected: Success

-- 8. Check MV refresh log
select mv_name, duration_ms, row_count, success
from mv_refresh_log
order by completed_at desc
limit 5;
-- Expected: 2 rows (one for each MV)

-- 9. Test dashboard summary RPC
select get_use_dashboard_summary();
-- Expected: Complete JSON object

-- 10. Verify indexes created
select indexname, tablename
from pg_indexes
where schemaname = 'public'
  and (indexname like 'idx_pua_%' or indexname like 'idx_fp_year_%' or indexname like 'idx_mv_%')
order by indexname;
-- Expected: 4 indexes

-- 11. Test PostgREST endpoints (via curl or browser)
-- GET https://pmispwtdngkcmsrsjwbp.supabase.co/rest/v1/v_use_coverage_summary
-- GET https://pmispwtdngkcmsrsjwbp.supabase.co/rest/v1/v_slo_status
-- POST https://pmispwtdngkcmsrsjwbp.supabase.co/rest/v1/rpc/get_use_dashboard_summary
```

---

## Expected Results

### Views Created (10)
| View | Purpose | Rows (Post-Deploy) |
|------|---------|-------------------|
| v_use_coverage_summary | Overall metrics | 1 |
| v_use_coverage_by_county | County breakdown | 67 |
| v_use_method_distribution | Method tracking | 1-5 |
| v_use_review_queue | Queue status | 1-4 |
| v_main_use_distribution | Main USE dist | 1-10 |
| v_subuse_distribution | SUBUSE detail | 0-50 |
| v_dor_code_quality | Normalization | 1 |
| v_slo_status | SLO compliance | 3 |

### Functions Created (2)
| Function | Purpose |
|----------|---------|
| refresh_property_use_mvs_logged() | MV refresh with performance logging |
| get_use_dashboard_summary() | Single JSON for complete dashboard |

### Logging Table (1)
| Table | Purpose | Rows (Post-Deploy) |
|-------|---------|-------------------|
| mv_refresh_log | MV refresh performance | 0 (fills on refresh) |

### Indexes Created (4)
| Index | Table | Purpose |
|-------|-------|---------|
| idx_pua_created_at | property_use_assignment | Time-series queries |
| idx_pua_confidence | property_use_assignment | Low-confidence filtering |
| idx_fp_year_county | florida_parcels | Year+county filtering |
| idx_mv_refresh_log_completed | mv_refresh_log | Successful refresh tracking |

---

## Dashboard Access

**URL:** http://localhost:5191/property-use-dashboard.html

**Features (Enabled After Deployment):**
- ✅ Real-time coverage metrics
- ✅ SLO status indicators (PASS/FAIL)
- ✅ Classification method distribution charts
- ✅ Review queue breakdown
- ✅ Main USE/SUBUSE distribution
- ✅ DOR code normalization tracking
- ✅ Auto-refresh every 30 seconds

**API Endpoints:**
```
GET /rest/v1/v_use_coverage_summary
GET /rest/v1/v_slo_status
GET /rest/v1/v_dor_code_quality
GET /rest/v1/v_use_method_distribution
GET /rest/v1/v_use_review_queue
GET /rest/v1/v_main_use_distribution?limit=10
POST /rest/v1/rpc/get_use_dashboard_summary
POST /rest/v1/rpc/refresh_property_use_mvs_logged
```

---

## SLO Tracking (Post-Deployment)

**Production Targets:**
| Metric | Target | Tracking View |
|--------|--------|---------------|
| Coverage | ≥99.5% properties with Main USE | v_slo_status |
| Unresolved Rate | ≤0.5% in needs_review >7 days | v_slo_status |
| LLM Usage | <5% of assignments | v_slo_status |
| API Latency P95 | ≤150ms for MV filters | mv_refresh_log |

**Current Status (M0):**
- Coverage: 0% (M1 target: ≥95%)
- Unresolved: 100% (M1 will reduce)
- LLM Usage: 0% (deterministic-first approach)

---

## Next Steps After Deployment

Once Supabase completes deployment and provides verification results:

1. **Verify all 10 views accessible**
2. **Test dashboard summary RPC**
3. **Open dashboard UI** (http://localhost:5191/property-use-dashboard.html)
4. **Confirm SLO tracking active**
5. **Mark M0 Observability as COMPLETE**

Then proceed to:
- **Populate dor_use_code_int column** (INT conversion from normalized property_use)
- **Begin M1 DOR mapping** (Map 0-99 → Main USE categories)

---

## Questions for Guy

1. **Dashboard access:** Should the dashboard be accessible at the public URL or localhost only?
2. **MV refresh schedule:** Do you want to set up automatic MV refresh via pg_cron (e.g., hourly)?
3. **Alerts:** Should we add email/webhook alerts for SLO violations?
4. **Performance:** Are the 4 indexes sufficient, or should we add more for specific queries?

---

**Ready for your action, Guy!** Please run the migration file and report back the verification results. This will enable real-time monitoring of the USE/SUBUSE classification system.

---

**Estimated Completion Time:** 10-15 minutes
**Risk Level:** LOW (read-only views, no data modification)
**Impact:** ZERO (new monitoring layer only, no changes to existing queries)
