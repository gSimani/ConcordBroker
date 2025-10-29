# ✅ QUICK OPTIMIZATION CHECKLIST

**Goal**: Apply 34 database indexes to make your system 5-50x faster
**Time**: 60-90 minutes
**Status**: Baseline test complete, ready for index creation

---

## 📋 YOUR CHECKLIST (Do in Order)

### ☐ **STEP 1: Create Database Backup** (15 min)

1. Go to: https://supabase.com/dashboard
2. Your project → Settings → Database → Backups
3. Click "Create Backup"
4. Name: `pre-optimization-backup-2025-10-29`
5. Wait for "Success" status

✅ **Done when**: Backup shows "Success" in green

---

### ☐ **STEP 2: Apply ALL Indexes** (60-90 min)

**OPTION A - All at Once** (Recommended):

1. Open Supabase SQL Editor
2. Click "New Query"
3. Open file: `supabase/migrations/ALL_INDEXES_CONSOLIDATED.sql`
4. Copy ALL the SQL (Ctrl+A, Ctrl+C)
5. Paste into SQL Editor
6. Click "Run"
7. Wait ~60-90 minutes
8. Check verification output at bottom

**OPTION B - Step by Step**:

Follow instructions in: `APPLY_INDEXES_NOW.md`

✅ **Done when**: Verification query shows all 34 indexes created

---

### ☐ **STEP 3: Verify Success** (5 min)

Run this query in SQL Editor:

```sql
-- Should show 5 tables with index counts
SELECT
  tablename,
  COUNT(*) as index_count,
  pg_size_pretty(SUM(pg_relation_size(indexrelid))) as total_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
WHERE tablename IN ('florida_parcels', 'property_sales_history', 'sunbiz_corporate', 'sunbiz_fictitious', 'sunbiz_officers')
  AND (indexname LIKE 'idx_fp_%' OR indexname LIKE 'idx_sales_%' OR indexname LIKE 'idx_sunbiz_%' OR indexname LIKE 'idx_fict_%' OR indexname LIKE 'idx_officers_%')
GROUP BY tablename
ORDER BY tablename;
```

**Expected**:
- florida_parcels: 11 indexes
- property_sales_history: 5 indexes
- sunbiz_corporate: 9 indexes
- sunbiz_fictitious: 6 indexes
- sunbiz_officers: 3 indexes

✅ **Done when**: All counts match

---

### ☐ **STEP 4: Test Health Check** (2 min)

Run in SQL Editor:

```sql
SELECT * FROM v_database_health;
```

✅ **Done when**: Returns data without errors

---

### ☐ **STEP 5: Measure Performance Improvement** (10 min)

**I'll help you with this step!**

Let me know when Steps 1-4 are complete, and I'll run the comparison tests to show you the improvements.

---

## 🎯 WHAT TO EXPECT

### **Before Optimization** (Current):
- Autocomplete: 3,715ms 🔴
- Address search: 1,991ms 🔴
- Year built: 538ms 🟡

### **After Optimization** (Expected):
- Autocomplete: ~500ms ✅ (7x faster)
- Address search: ~150ms ✅ (13x faster)
- Year built: ~80ms ✅ (7x faster)

**Overall**: 4-6x faster system

---

## 📞 WHEN YOU'RE DONE

**Message me**: "Indexes applied"

And I'll help you:
1. Run the performance comparison
2. Show before/after results
3. Commit your progress to git
4. Plan next steps (Phase 2)

---

## 🆘 IF YOU NEED HELP

**Detailed guides available**:
- `APPLY_INDEXES_NOW.md` - Step-by-step with screenshots
- `PHASE_0_AND_1_EXECUTION_GUIDE.md` - Complete guide
- `ALL_INDEXES_CONSOLIDATED.sql` - All SQL in one file

**Common issues**: See troubleshooting section in `APPLY_INDEXES_NOW.md`

---

**Current Status**: ⏸️ Waiting for you to apply indexes
**Next Action**: Create database backup, then run the SQL

Good luck! 🚀
