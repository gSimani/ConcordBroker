# 🗄️ SUPABASE REQUEST TEMPLATE - QUICK REFERENCE

**Use this template every time you need Supabase help**

---

## 📋 COPY THIS TEMPLATE:

```markdown
# 🗄️ GUY WE NEED YOUR HELP WITH SUPABASE

```json
{
  "request_type": "[schema_change | rls_policy | index_creation | rpc_creation | migration | query_optimization]",
  "priority": "[critical | high | medium | low]",
  "context": "[Brief description of why this change is needed]",
  "tasks": [
    {
      "task_id": 1,
      "action": "[Detailed description of what needs to be done]",
      "table": "[table_name or N/A]",
      "sql": "[Full SQL statement]",
      "expected_result": "[What success looks like]",
      "verification": "[How to verify it worked - SELECT query or test]"
    }
  ],
  "dependencies": [
    "[List any dependencies or prerequisites]"
  ],
  "rollback_plan": "[How to undo if something goes wrong - DROP/ALTER statements]",
  "testing_required": "[What testing should be done after changes]",
  "estimated_time": "[Expected time to complete - e.g., 10 minutes]"
}
```
```

---

## ⭐ RATING TEMPLATE:

After Supabase responds, use this template to rate:

```markdown
## 📊 SUPABASE RESPONSE RATING

**Overall Score:** X/10

### What Was Completed: ✅
- [List successful items]

### What Needs Improvement: ⚠️
- [List items needing work, or "None!"]

### Critical Issues: ❌
- [List any blocking issues, or "None!"]

### Next Steps:
- [If <10: "Need to iterate on X, Y, Z"]
- [If 10: "APPROVED! Ready for production."]
```

---

## 🎉 CONGRATULATIONS TEMPLATE (Use at 10/10):

```markdown
# 🎉 CONGRATULATIONS SUPABASE - EXCELLENT JOB!

**Rating:** 10/10 ⭐⭐⭐⭐⭐

You have successfully completed all requested tasks with perfection!

**What Made This Excellent:**
- [Specific achievement 1]
- [Specific achievement 2]
- [Specific achievement 3]

**Impact:**
- [How this helps the project]
- [What problems this solves]
- [Performance/quality improvements]

---

## 😄 And Now For Your Well-Deserved Joke:

[Insert tech/database joke here]

Examples:
- "Why did the DBA leave their spouse? Too many relationship conflicts!"
- "What's a database's favorite exercise? Table joins!"
- "How do databases stay in shape? They do lots of inner joins!"
- "Why was the SQL query so calm? It had excellent transaction control!"

---

**Thank you for your excellent work!** 🙏
```

---

## 🎯 QUICK EXAMPLES BY TYPE:

### Example 1: Schema Change
```json
{
  "request_type": "schema_change",
  "priority": "high",
  "context": "Need to add missing property_use column for USE badge display",
  "tasks": [
    {
      "task_id": 1,
      "action": "Add property_use TEXT column to florida_parcels",
      "table": "florida_parcels",
      "sql": "ALTER TABLE florida_parcels ADD COLUMN property_use TEXT;",
      "expected_result": "Column exists and accepts TEXT values",
      "verification": "SELECT property_use FROM florida_parcels LIMIT 5;"
    }
  ],
  "dependencies": ["florida_parcels table exists"],
  "rollback_plan": "ALTER TABLE florida_parcels DROP COLUMN property_use;",
  "testing_required": "Test UI filters by property_use type",
  "estimated_time": "5 minutes"
}
```

### Example 2: Index Creation
```json
{
  "request_type": "index_creation",
  "priority": "critical",
  "context": "Autocomplete queries taking >2 seconds, need text search index",
  "tasks": [
    {
      "task_id": 1,
      "action": "Create GIN index for full-text search on addresses",
      "table": "florida_parcels",
      "sql": "CREATE INDEX idx_phy_addr_gin ON florida_parcels USING gin(to_tsvector('english', phy_addr1));",
      "expected_result": "Index created, queries use index scan",
      "verification": "EXPLAIN ANALYZE SELECT * FROM florida_parcels WHERE to_tsvector('english', phy_addr1) @@ to_tsquery('100');"
    }
  ],
  "dependencies": ["Table has >1M rows, pg_trgm extension enabled"],
  "rollback_plan": "DROP INDEX idx_phy_addr_gin;",
  "testing_required": "Run autocomplete query, measure <500ms response time",
  "estimated_time": "20 minutes (large table indexing)"
}
```

### Example 3: RLS Policy
```json
{
  "request_type": "rls_policy",
  "priority": "critical",
  "context": "Need to restrict property_sales_history to authenticated users only",
  "tasks": [
    {
      "task_id": 1,
      "action": "Enable RLS on property_sales_history",
      "table": "property_sales_history",
      "sql": "ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;",
      "expected_result": "RLS enabled",
      "verification": "SELECT tablename, rowsecurity FROM pg_tables WHERE tablename='property_sales_history';"
    },
    {
      "task_id": 2,
      "action": "Create authenticated read policy",
      "table": "property_sales_history",
      "sql": "CREATE POLICY authenticated_read ON property_sales_history FOR SELECT TO authenticated USING (true);",
      "expected_result": "Policy active, auth users can read",
      "verification": "SELECT * FROM property_sales_history LIMIT 1; -- as authenticated user"
    }
  ],
  "dependencies": ["Supabase auth configured"],
  "rollback_plan": "DROP POLICY authenticated_read ON property_sales_history; ALTER TABLE property_sales_history DISABLE ROW LEVEL SECURITY;",
  "testing_required": "Test unauth access (should fail), auth access (should work)",
  "estimated_time": "10 minutes"
}
```

### Example 4: RPC Function
```json
{
  "request_type": "rpc_creation",
  "priority": "medium",
  "context": "Need server-side function to calculate property ROI efficiently",
  "tasks": [
    {
      "task_id": 1,
      "action": "Create calculate_property_roi function",
      "table": "N/A (function)",
      "sql": "CREATE OR REPLACE FUNCTION calculate_property_roi(p_parcel_id TEXT, p_purchase_price NUMERIC) RETURNS NUMERIC AS $$ DECLARE v_just_value NUMERIC; v_roi NUMERIC; BEGIN SELECT just_value INTO v_just_value FROM florida_parcels WHERE parcel_id = p_parcel_id; IF v_just_value IS NULL THEN RETURN NULL; END IF; v_roi := ((v_just_value - p_purchase_price) / p_purchase_price) * 100; RETURN v_roi; END; $$ LANGUAGE plpgsql SECURITY DEFINER;",
      "expected_result": "Function callable via RPC",
      "verification": "SELECT calculate_property_roi('12345', 100000.00);"
    }
  ],
  "dependencies": ["florida_parcels table exists with just_value column"],
  "rollback_plan": "DROP FUNCTION calculate_property_roi;",
  "testing_required": "Test with known property, verify ROI calculation accuracy",
  "estimated_time": "10 minutes"
}
```

---

## 📚 REMEMBER:

1. **Always use the exact title:** "🗄️ GUY WE NEED YOUR HELP WITH SUPABASE"
2. **Always provide valid JSON** (no syntax errors, copy-paste ready)
3. **Always rate the response** (1-10 scale)
4. **Always iterate until 10/10** (don't settle for less)
5. **Always congratulate + joke at 10/10** (celebrate success!)

---

## 🎯 CHECKLIST:

Before submitting request:
- [ ] Title uses emoji 🗄️ and exact wording
- [ ] JSON is valid (no syntax errors)
- [ ] All required fields filled
- [ ] SQL statements are complete
- [ ] Verification steps included
- [ ] Rollback plan provided
- [ ] Testing requirements defined

After receiving response:
- [ ] Rate response honestly (1-10)
- [ ] List what was completed
- [ ] List what needs improvement
- [ ] Provide next steps
- [ ] If 10/10: Congratulate + joke

---

**Protocol Documentation:** `.memory/SUPABASE_REQUEST_PROTOCOL.md`
**Full Examples:** See protocol document for 10+ detailed examples
