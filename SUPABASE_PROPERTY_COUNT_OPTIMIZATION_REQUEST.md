# 🗄️ GUY WE NEED YOUR HELP WITH SUPABASE

## Request Overview
We need to identify and count 3.97M "unclassified" properties (43.5% of database) but all count queries are timing out. This is blocking critical data integrity work.

## Detailed Request

```json
{
  "request_type": "performance_optimization",
  "priority": "critical",
  "context": "Need to query 9,113,150 properties grouped by standardized_property_use to identify missing categories. Currently ALL count queries timeout after 120 seconds. This blocks understanding of 43.5% of our property data.",
  "business_impact": "Cannot accurately report property counts to users, cannot identify data quality issues, cannot map missing property types to UI filters",
  "tasks": [
    {
      "task_id": 1,
      "action": "Increase statement timeout globally for counting operations",
      "rationale": "Current timeout (120s) insufficient for 9.1M row aggregations",
      "sql": "ALTER DATABASE postgres SET statement_timeout = '300s';",
      "verification": "SHOW statement_timeout; -- Should show 300s",
      "rollback": "ALTER DATABASE postgres SET statement_timeout = '120s';"
    },
    {
      "task_id": 2,
      "action": "Check if materialized view property_type_counts exists and is current",
      "rationale": "Materialized view would provide instant counts without full table scan",
      "sql": "SELECT schemaname, matviewname, last_refresh FROM pg_matviews WHERE matviewname = 'property_type_counts';",
      "verification": "If exists and recent (< 7 days), skip to task 5. If stale or missing, proceed to task 3.",
      "expected_result": "View should exist with recent refresh timestamp"
    },
    {
      "task_id": 3,
      "action": "Create or refresh materialized view for property counts (ONLY if task 2 shows missing/stale)",
      "rationale": "Pre-compute counts for instant access",
      "sql": "-- If view exists:\nREFRESH MATERIALIZED VIEW CONCURRENTLY property_type_counts;\n\n-- If view doesn't exist:\nCREATE MATERIALIZED VIEW property_type_counts AS\nSELECT\n  county,\n  standardized_property_use,\n  COUNT(*) as total_count,\n  COUNT(*) FILTER (WHERE just_value > 0) as valued_count,\n  SUM(just_value) FILTER (WHERE just_value > 0) as total_value,\n  AVG(just_value) FILTER (WHERE just_value > 0) as avg_value\nFROM florida_parcels\nWHERE standardized_property_use IS NOT NULL\nGROUP BY county, standardized_property_use\nUNION ALL\nSELECT\n  'ALL' as county,\n  standardized_property_use,\n  COUNT(*) as total_count,\n  COUNT(*) FILTER (WHERE just_value > 0) as valued_count,\n  SUM(just_value) FILTER (WHERE just_value > 0) as total_value,\n  AVG(just_value) FILTER (WHERE just_value > 0) as avg_value\nFROM florida_parcels\nWHERE standardized_property_use IS NOT NULL\nGROUP BY standardized_property_use;\n\nCREATE UNIQUE INDEX idx_property_counts_unique ON property_type_counts(county, standardized_property_use);",
      "verification": "SELECT * FROM property_type_counts WHERE county = 'ALL' ORDER BY total_count DESC LIMIT 10;",
      "expected_result": "Should see top 10 property types with counts"
    },
    {
      "task_id": 4,
      "action": "Add index on standardized_property_use for faster filtering (if missing)",
      "rationale": "Speeds up COUNT(*) GROUP BY queries on this column",
      "sql": "-- Check if index exists first:\nSELECT indexname FROM pg_indexes WHERE tablename = 'florida_parcels' AND indexdef LIKE '%standardized_property_use%';\n\n-- If missing, create:\nCREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_std_use ON florida_parcels(standardized_property_use) WHERE standardized_property_use IS NOT NULL;",
      "verification": "\\d florida_parcels -- Check indexes section",
      "expected_result": "Index idx_parcels_std_use should appear in index list"
    },
    {
      "task_id": 5,
      "action": "Query property counts from optimized source",
      "rationale": "Get actual counts to replace estimates",
      "sql": "-- From materialized view (instant):\nSELECT\n  standardized_property_use,\n  total_count,\n  ROUND(100.0 * total_count / SUM(total_count) OVER(), 2) as percentage\nFROM property_type_counts\nWHERE county = 'ALL'\nORDER BY total_count DESC;\n\n-- Also get NULL count:\nSELECT COUNT(*) as null_count FROM florida_parcels WHERE standardized_property_use IS NULL;\n\n-- And grand total:\nSELECT COUNT(*) as grand_total FROM florida_parcels;",
      "verification": "Counts should sum to 9,113,150 (or close)",
      "expected_result": "List of all property types with exact counts"
    },
    {
      "task_id": 6,
      "action": "Export results as JSON for code integration",
      "rationale": "Need structured data to update TypeScript constants",
      "sql": "-- Export as JSON:\nSELECT json_agg(\n  json_build_object(\n    'property_type', standardized_property_use,\n    'count', total_count,\n    'percentage', ROUND(100.0 * total_count / SUM(total_count) OVER(), 2)\n  ) ORDER BY total_count DESC\n) as property_counts\nFROM property_type_counts\nWHERE county = 'ALL';",
      "verification": "Should output valid JSON array",
      "expected_result": "JSON array with all property types and counts"
    }
  ],
  "rollback_plan": {
    "description": "All changes are safe and reversible",
    "steps": [
      "Timeout: ALTER DATABASE postgres SET statement_timeout = '120s';",
      "Materialized view: DROP MATERIALIZED VIEW property_type_counts;",
      "Index: DROP INDEX CONCURRENTLY idx_parcels_std_use;"
    ],
    "risk_level": "LOW",
    "notes": "Materialized view and index are performance enhancements only - no data modification"
  },
  "success_criteria": [
    "Query completes in < 5 seconds (using materialized view)",
    "All property types identified with exact counts",
    "NULL count determined",
    "Total adds up to 9,113,150 ± 1000"
  ]
}
```

## Why This Is Critical

**Data Integrity Issue:**
- Users see counts that don't add up (5M shown, 9.1M in database)
- 43.5% of properties are "unclassified" with no explanation
- Cannot identify NULL values vs. unknown types vs. missing mappings

**User Impact:**
- Filters show incomplete data
- Search results missing 4M properties
- Trust in platform data accuracy damaged

**Technical Debt:**
- No way to audit property type distribution
- Cannot monitor data quality over time
- Cannot identify which property types need mapping

## Expected Output

Please provide JSON results from Task 5 showing:
```json
{
  "property_counts": [
    {"property_type": "Single Family Residential", "count": 3300000, "percentage": 36.2},
    {"property_type": "Condominium", "count": 958000, "percentage": 10.5},
    ...
  ],
  "null_count": 1400000,
  "grand_total": 9113150
}
```

## Timeline

**Urgency:** High - blocking user-facing data integrity work

**Estimated Time:**
- Tasks 1-4: 15-20 minutes
- Task 5-6: 2-3 minutes
- **Total: ~25 minutes**

---

**Note:** Once you provide the results, I will rate the response 1-10 based on completeness and accuracy, then iterate if needed until we reach 10/10. ⭐
