# DOR Assignment - Quick Start ⚡

## 🎯 Goal
Assign DOR use codes to **5.95M properties** (65% of 9.1M total)

---

## 🚀 Execute NOW (Choose One)

### Method 1: SQL Editor (FASTEST) ⭐⭐⭐
```
1. Open: https://app.supabase.com
2. Go to: SQL Editor
3. Copy: EXECUTE_DOR_ASSIGNMENT.sql
4. Run: All queries (PHASE 1, 2, 3, 4)
5. Time: 15-30 minutes
```

### Method 2: County Batches (SAFEST) ⭐⭐
```
1. Open: https://app.supabase.com
2. Go to: SQL Editor
3. Copy: BATCH_UPDATE_BY_COUNTY.sql
4. Run: Each county separately (67 total)
5. Time: 30-60 minutes
```

### Method 3: Python Script
```bash
python execute_dor_supabase_rest.py
# Time: 2-3 hours
```

---

## ✅ Verify Success

```sql
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN land_use_code IS NOT NULL THEN 1 END) as with_code,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage
FROM florida_parcels WHERE year = 2025;
```

**Target**: Coverage ≥ 99.5%

---

## 📚 Full Documentation

- **Execution Guide**: `DOR_ASSIGNMENT_EXECUTION_GUIDE.md`
- **Complete Summary**: `DOR_ASSIGNMENT_COMPLETE_SUMMARY.md`
- **SQL Files**: `EXECUTE_DOR_ASSIGNMENT.sql`, `BATCH_UPDATE_BY_COUNTY.sql`
- **Python Scripts**: `execute_dor_*.py`

---

## 🆘 If Something Goes Wrong

1. **Timeout Error**: Use Method 2 (County Batches) instead
2. **Network Error**: Use Python REST script
3. **Permission Error**: Check service_role key in Supabase
4. **Still Stuck**: Read `DOR_ASSIGNMENT_EXECUTION_GUIDE.md`

---

**Ready to Execute!** 🚀