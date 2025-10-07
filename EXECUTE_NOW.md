# 🚀 DOR Use Code Assignment - EXECUTE NOW

## ⚡ Quick Execution Guide

### **RECOMMENDED METHOD: Direct SQL Execution**
This is the fastest, most reliable method for assigning DOR use codes to all 9.1M properties.

---

## 📋 **Step-by-Step Instructions**

### **Step 1: Open Supabase SQL Editor**

1. Go to your Supabase Dashboard: https://supabase.com/dashboard/project/mogulpssjdlxjvstqfee
2. Click on "SQL Editor" in the left sidebar
3. Click "New Query"

### **Step 2: Copy and Execute SQL**

1. Open the file: `EXECUTE_DOR_ASSIGNMENT.sql`
2. Copy ALL the SQL content
3. Paste into Supabase SQL Editor
4. Click "RUN" button (or press Ctrl+Enter)

### **Step 3: Monitor Progress**

The SQL script will:
1. ✅ Show current status (BEFORE)
2. 🔄 Execute bulk assignment (2-5 minutes)
3. ✅ Show new status (AFTER)
4. 📊 Display distribution analytics
5. 📈 Show category breakdown
6. 🗺️ County coverage analysis
7. ✔️ Validate no invalid codes
8. 👀 Show sample properties

### **Step 4: Verify Results**

Expected results after execution:
```
BEFORE:
- Total Properties: ~9,100,000
- Coverage: ~X%

AFTER:
- Total Properties: ~9,100,000
- Coverage: ~100%
- All properties have valid DOR codes
```

---

## 🧠 **What Gets Assigned**

### For Each Property:
- **`dor_uc`**: 2-digit DOR code (00, 01, 02, 10, 17, 24, etc.)
- **`property_use`**: Human-readable description
- **`property_use_category`**: High-level category

### Assignment Logic:

| Value Range | Building | Land | Assigned Code | Use Type |
|-------------|----------|------|---------------|----------|
| $50k-$1M | > Land | Any | **00** | Single Family |
| > $500k | > Land×2 | Any | **02** | Multi-Family 10+ |
| > $500k | > $200k | Balanced | **17** | Commercial |
| > $1M building | High | < $500k | **24** | Industrial |
| > $100k land | Low | > Building×5 | **01** | Agricultural |
| Any | $0 | > $0 | **10** | Vacant Residential |

---

## 📊 **Expected Distribution**

After execution, you should see approximately:

| Category | Properties | Percentage |
|----------|-----------|------------|
| Residential | ~7.5M | ~82% |
| Commercial | ~800k | ~9% |
| Agricultural | ~500k | ~5% |
| Industrial | ~200k | ~2% |
| Other | ~100k | ~1% |

---

## ✅ **Verification Checklist**

After execution, verify:

- [ ] Coverage is 100% (all properties have dor_uc)
- [ ] No invalid use codes (Step 7 returns 0 rows)
- [ ] Distribution looks reasonable (Step 4 & 5)
- [ ] Sample properties have appropriate assignments (Step 8)
- [ ] All counties show high coverage (Step 6)

---

## 🎯 **Integration with MiniPropertyCards**

Once complete, MiniPropertyCards will automatically display:

```typescript
// Component: MiniPropertyCard.tsx
// Displays from florida_parcels table

property_use           → "Single Family"
property_use_category  → "Residential"
dor_uc                → "00"
```

The cards already query `florida_parcels`, so no frontend changes needed!

---

## 🔄 **Alternative Methods** (if SQL Editor unavailable)

### Method 2: Python Script via Supabase REST API
```bash
# Requires Supabase REST API access
python run_dor_use_code_assignment.py
```

### Method 3: FastAPI Service (port 5432 must be accessible)
```bash
python mcp-server/fastapi-endpoints/dor_use_code_api.py
curl -X POST http://localhost:8002/assign-bulk
```

### Method 4: PySpark for Advanced Analytics
```bash
python mcp-server/pyspark-processors/dor_use_code_spark_processor.py
```

### Method 5: Jupyter Notebook for Interactive Analysis
```bash
jupyter notebook mcp-server/notebooks/dor_use_code_analysis.ipynb
```

---

## ⏱️ **Performance Expectations**

| Method | Execution Time | Complexity | Monitoring |
|--------|---------------|------------|------------|
| **Direct SQL** | **2-5 min** | **Simple** | **Built-in** |
| REST API | 10-15 min | Medium | Custom |
| FastAPI | 5-10 min | Medium | API logs |
| PySpark | 10-15 min | Complex | Spark UI |
| Jupyter | Variable | Interactive | Visual |

---

## 🚨 **Troubleshooting**

### Query Timeout
- Supabase may timeout on long queries
- Solution: Execute in Supabase dashboard (higher limits)

### Port 5432 Blocked
- Direct PostgreSQL connections may be blocked
- Solution: Use SQL Editor method (uses HTTP)

### Memory Issues
- Very rare with optimized UPDATE query
- Solution: Add WHERE clause to batch by county

---

## 📈 **Post-Execution Actions**

After successful execution:

1. **Verify Frontend**
   - Open MiniPropertyCard component
   - Confirm use codes display correctly
   - Check all 9.1M properties have data

2. **Generate Analytics**
   - Run Jupyter notebook for visualizations
   - Export distribution reports
   - Create executive summary

3. **Update Documentation**
   - Document actual execution time
   - Note any adjustments made
   - Update coverage percentage

4. **Commit Changes**
   - Git commit the SQL script
   - Document the assignment logic
   - Tag release version

---

## 🎉 **Success Criteria**

The mission is complete when:

✅ **100% Coverage**: All 9.1M properties have `dor_uc`
✅ **Valid Codes**: All codes exist in `dor_use_codes` table
✅ **Categories Assigned**: All have `property_use_category`
✅ **Frontend Works**: MiniPropertyCards display correctly
✅ **Analytics Available**: Reports and visualizations ready

---

## 📞 **Need Help?**

- **Documentation**: `DOR_USE_CODE_ASSIGNMENT_COMPLETE_SYSTEM.md`
- **SQL Script**: `EXECUTE_DOR_ASSIGNMENT.sql`
- **AI Agents**: `mcp-server/ai-agents/`
- **FastAPI Docs**: http://localhost:8002/docs

---

## 🚀 **EXECUTE NOW!**

**Recommended**: Copy `EXECUTE_DOR_ASSIGNMENT.sql` into Supabase SQL Editor and click RUN.

**Estimated Time**: 2-5 minutes
**Expected Result**: 100% coverage across 9.1M properties

---

*Last Updated: 2025-09-29*
*System Status: ✅ Ready for Execution*