# 🚀 APPLY DATABASE INDEXES - DO THIS NOW

**Status**: Ready to execute
**Time Required**: 60-90 minutes
**Risk**: LOW (indexes can be dropped if needed)

---

## ⚠️ BEFORE YOU START

### **STEP 0: Create Database Backup** (15 minutes)

**IMPORTANT**: Do this FIRST before running any SQL!

1. Open your browser and go to: https://supabase.com/dashboard
2. Select your ConcordBroker project
3. Click: **Settings** (left sidebar, bottom)
4. Click: **Database** (in settings menu)
5. Scroll down to "**Backups**" section
6. Click: **"Create Backup"** button
7. Enter name: `pre-optimization-backup-2025-10-29`
8. Click: **"Create Backup"**
9. **Wait for status** to show "Success" (~5-10 minutes)

✅ **Checkpoint**: Backup status shows "Success" in green

**If backup fails**: Your database might have auto-backups enabled. Check the backup list - if you see recent backups, you're covered.

---

## 📝 STEP 1: OPEN SUPABASE SQL EDITOR

1. In Supabase Dashboard, click **"SQL Editor"** (left sidebar)
2. Click **"New Query"** button (top right)
3. You'll see an empty SQL editor window

**Keep this tab open** - you'll paste SQL here in the next steps.

---

## 🗄️ STEP 2: APPLY FLORIDA_PARCELS INDEXES (45-60 min)

### **What This Does**:
- Creates 11 indexes on your florida_parcels table
- Fixes the 3.7-second autocomplete issue
- Fixes the 2-second address search issue
- Makes year built and other filters much faster

### **Instructions**:

1. **Open the SQL file**: `supabase/migrations/20250129_01_florida_parcels_indexes.sql`
2. **Copy ALL the SQL** (Ctrl+A, Ctrl+C)
3. **Paste into Supabase SQL Editor**
4. **Click "Run"** button (or press Ctrl+Enter)
5. **Wait for completion** (~30-45 minutes)

### **What You'll See**:

The SQL will execute line by line. You should see output like:
```
CREATE EXTENSION
CREATE INDEX
CREATE INDEX
CREATE INDEX
...
(continues for all 11 indexes)
```

**Progress indicator**: Supabase shows "Running..." at the top. **Don't close the tab!**

### **When Complete**:

Scroll to the bottom of the results. You should see the verification query output showing 11 rows (one for each index).

Example:
```
 schemaname | tablename        | indexname              | index_size
------------+------------------+------------------------+------------
 public     | florida_parcels  | idx_fp_county_year     | 78 MB
 public     | florida_parcels  | idx_fp_address_trgm    | 245 MB
 ...
(11 rows)
```

✅ **Success**: All 11 indexes listed

❌ **Error**: If you see an error:
- Check the error message
- Most common: "index already exists" → This is OK, means index was already there
- If timeout: Run the SQL again (it will skip existing indexes)

---

## 💾 STEP 3: APPLY SALES_HISTORY INDEXES (10-15 min)

### **What This Does**:
- Creates 5 indexes on property_sales_history table
- Makes sales data loading 10-20x faster

### **Instructions**:

1. Click **"New Query"** in Supabase SQL Editor
2. Open: `supabase/migrations/20250129_02_sales_history_indexes.sql`
3. Copy all SQL
4. Paste into editor
5. Click "Run"
6. Wait ~10-15 minutes

### **Verification**:

You should see 5 rows in the verification output:
```
 schemaname | tablename               | indexname            | index_size
------------+-------------------------+----------------------+------------
 public     | property_sales_history  | idx_sales_date       | 3.2 MB
 ...
(5 rows)
```

✅ **Success**: All 5 indexes listed

---

## 🏢 STEP 4: APPLY SUNBIZ INDEXES (15-20 min)

### **What This Does**:
- Creates sunbiz_officers table (currently missing!)
- Creates 18 indexes on Sunbiz tables
- **CRITICAL**: Prevents 30-60 second timeouts when you load Sunbiz data

**Note**: Since Sunbiz tables are empty, indexes create instantly!

### **Instructions**:

1. Click **"New Query"**
2. Open: `supabase/migrations/20250129_03_sunbiz_indexes_and_tables.sql`
3. Copy all SQL
4. Paste into editor
5. Click "Run"
6. Wait ~5-10 minutes (faster because tables are empty)

### **Verification**:

You should see:
1. **Table created**: `sunbiz_officers` with 10 columns
2. **Index counts**:
   - sunbiz_corporate: 9 indexes
   - sunbiz_fictitious: 6 indexes
   - sunbiz_officers: 3 indexes

✅ **Success**: All counts match

---

## 📊 STEP 5: APPLY MONITORING FUNCTIONS (10-15 min)

### **What This Does**:
- Creates 7 functions to monitor database performance
- Creates 1 health check view
- Helps you track performance over time

### **Instructions**:

1. Click **"New Query"**
2. Open: `supabase/migrations/20250129_04_monitoring_functions.sql`
3. Copy all SQL
4. Paste into editor
5. Click "Run"
6. Wait ~5 minutes

### **Verification**:

Run this test query in SQL Editor:
```sql
SELECT * FROM v_database_health;
```

You should see output like:
```
 database_size | active_connections | cache_hit_ratio_pct | slow_queries | unused_indexes | checked_at
---------------+--------------------+---------------------+--------------+----------------+-------------------------
 2.8 GB        | 3                  | 94.23               | 2            | 0              | 2025-10-29 18:30:00.000
```

✅ **Success**: Query returns data without errors

---

## ✅ COMPLETION CHECKLIST

After completing all 4 steps, verify:

- [ ] **Backup created** (confirmed in Supabase dashboard)
- [ ] **11 florida_parcels indexes** created
- [ ] **5 sales_history indexes** created
- [ ] **18 Sunbiz indexes** created
- [ ] **sunbiz_officers table** created
- [ ] **7 monitoring functions** working
- [ ] **Total: 34 indexes + 1 table + 7 functions**

### **Quick Verification**:

Run this in SQL Editor to see all your new indexes:

```sql
-- Count all new indexes
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

**Expected output**:
```
 tablename               | index_count | total_size
-------------------------+-------------+------------
 florida_parcels         | 11          | ~600 MB
 property_sales_history  | 5           | ~15 MB
 sunbiz_corporate        | 9           | ~10 MB
 sunbiz_fictitious       | 6           | ~8 MB
 sunbiz_officers         | 3           | ~1 MB

(5 rows)
```

✅ **All indexes created successfully!**

---

## 🚀 NEXT STEP: MEASURE IMPROVEMENT

Once all indexes are applied, let me know and I'll help you run the performance comparison to see the improvements!

You should expect:
- Autocomplete: **3,715ms → ~500ms** (7x faster)
- Address search: **1,991ms → ~150ms** (13x faster)
- Year built: **538ms → ~80ms** (7x faster)

---

## 🆘 TROUBLESHOOTING

### **Issue: "Extension pg_trgm does not exist"**

**Fix**: Run this first:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```
Then run the index creation SQL again.

### **Issue: "Index already exists"**

**This is OK!** It means the index was already there. The SQL will skip it and continue.

### **Issue: Query timeout**

**Fix**: Increase timeout and run again:
```sql
SET statement_timeout = '60min';
-- Then paste the index creation SQL
```

### **Issue: "Table or column does not exist"**

**Possible causes**:
1. Table name is different in your database
2. Column name is different

**Fix**: Check your actual table structure:
```sql
\d florida_parcels
```

Then adjust the index creation SQL to match your column names.

### **Issue: Supabase SQL Editor disconnects**

**This can happen with long-running queries**. If it disconnects:
1. Refresh the page
2. Run the verification query to see which indexes were created
3. Re-run the SQL (it will skip existing indexes)

---

## 💡 TIPS

1. **Keep the browser tab open** during index creation
2. **Don't worry if it takes a while** - 45 minutes is normal for 2M records
3. **Check verification queries** after each step to confirm success
4. **If unsure**, run verification before moving to next step

---

## 📞 WHEN YOU'RE DONE

Let me know when you've completed all 4 steps, and I'll help you:
1. Run the performance test again
2. Compare before/after results
3. Commit your progress to git
4. Plan next steps (Phase 2)

**Remember**: This is the foundation. Once these indexes are in place, everything else becomes easier and faster!

---

**Ready to start?** Begin with Step 0 (create backup), then proceed through Steps 1-5 in order.

Good luck! 🚀
