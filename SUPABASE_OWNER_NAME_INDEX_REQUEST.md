# 🗄️ GUY WE NEED YOUR HELP WITH SUPABASE

## Request Details

```json
{
  "request_type": "index_creation",
  "priority": "high",
  "context": "Owner name searches on florida_parcels table (9.1M records) are timing out due to lack of index. This is causing console errors and poor user experience when searching by owner name. Adding a GIN index will reduce query time from 2-5 seconds to 50-200ms.",
  "tasks": [
    {
      "task_id": 1,
      "action": "Enable pg_trgm extension (required for GIN text index)",
      "sql": "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
      "verification": "SELECT * FROM pg_extension WHERE extname = 'pg_trgm';"
    },
    {
      "task_id": 2,
      "action": "Create GIN index on owner_name column for fast text searches",
      "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name_gin ON florida_parcels USING gin(owner_name gin_trgm_ops);",
      "verification": "SELECT schemaname, tablename, indexname, indexdef FROM pg_indexes WHERE tablename = 'florida_parcels' AND indexname = 'idx_florida_parcels_owner_name_gin';"
    },
    {
      "task_id": 3,
      "action": "Verify index improves query performance",
      "sql": "EXPLAIN ANALYZE SELECT parcel_id, owner_name, county, just_value FROM florida_parcels WHERE owner_name ILIKE '%SMITH%' LIMIT 100;",
      "verification": "Check that execution plan shows 'Bitmap Heap Scan using idx_florida_parcels_owner_name_gin' instead of 'Seq Scan'"
    }
  ],
  "rollback_plan": "DROP INDEX CONCURRENTLY IF EXISTS idx_florida_parcels_owner_name_gin;",
  "estimated_duration": "5-10 minutes for index creation (CONCURRENTLY avoids table locks)",
  "impact": {
    "performance_improvement": "40-100x faster owner name searches",
    "affected_queries": "All ILIKE/LIKE searches on owner_name column",
    "table_size": "9,113,150 records",
    "downtime": "None (CONCURRENTLY flag prevents table locks)"
  }
}
```

## Why This Is Needed

**Current Problem**:
- Users searching by owner name experience timeouts
- Console shows "Search error: Error: Search failed: 404"
- Queries take 2-5 seconds on average
- Database performs full table scan on 9.1M records

**Solution**:
- GIN (Generalized Inverted Index) with trigram operators
- Optimized for `ILIKE '%search%'` queries
- Supports partial matches (beginning, middle, or end of owner name)

**Expected Results**:
- Query time: 2-5 seconds → 50-200ms (40-100x improvement)
- No more timeout errors
- Better user experience for owner searches

## After Completion

Once you've run these SQL commands in Supabase, please let me know the results and I'll rate the Supabase response!

---

**Note**: The `CONCURRENTLY` flag means this index will be built in the background without locking the table, so users can continue searching while it's being created.
