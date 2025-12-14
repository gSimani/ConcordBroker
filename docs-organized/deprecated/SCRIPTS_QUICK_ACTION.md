# ⚡ Analysis Scripts - Quick Action Guide

**Read this first**: See `ANALYSIS_SCRIPTS_COMPLETE_REVIEW.md` for full details

---

## 🚨 URGENT: Security Issue

**4 scripts have hardcoded database credentials!**

**Files with exposed passwords**:
1. analyze_supabase_complete.py (line 51)
2. analyze_supabase_tables.py (lines 13-14)
3. analyze_tax_deed_status.py (lines 7-8)
4. analyze_property_use_comprehensive.py (lines 12-13)

**Risk**: 🔴 **CRITICAL** - Anyone with access to these files can access your database

---

## ✅ Quick Fix (5 minutes)

### Option A: I'll Fix Them
Say "yes" and I'll edit all 4 files to use environment variables from `.env.mcp`

### Option B: Manual Fix
For each file, replace hardcoded credentials with:

```python
import os
from dotenv import load_dotenv

load_dotenv('.env.mcp')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
```

---

## 📊 What You Have (11 scripts total)

### ✅ **KEEP (6 scripts)**:
1. **analyze_supabase_complete.py** ⭐ - ML analysis (FIX NEEDED)
2. **analyze_supabase_tables.py** - Simple analyzer (FIX NEEDED)
3. **analyze_tax_deed_status.py** 🚨 - Business-critical (FIX NEEDED)
4. **analyze_property_use_comprehensive.py** ⭐ - Best property analyzer (FIX NEEDED)
5. **analyze_large_properties.py** ✅ - Already secure
6. **analyze_sales_tables.py** ✅ - Already secure

### 📦 **ARCHIVE (4 scripts)**:
Move to `archive/` folder (still useful as reference):
- analyze_website_structure.py → `archive/website-analysis/`
- analyze_property_use_values.py → `archive/property-analysis/`
- analyze_proformas_simple.py → `archive/financial-analysis/`
- analyze_missing_data.py → `archive/data-gap-analysis/`

### ❌ **DELETE (1 script)**:
- analyze-sales-tables.js (duplicate, Python version is better)

---

## 🎯 One-Command Fix

```bash
# Delete duplicate
rm analyze-sales-tables.js

# Create archive structure
mkdir -p archive/{website-analysis,property-analysis,financial-analysis,data-gap-analysis}

# Move to archive
mv analyze_website_structure.py archive/website-analysis/
mv analyze_property_use_values.py archive/property-analysis/
mv analyze_proformas_simple.py archive/financial-analysis/
mv analyze_missing_data.py archive/data-gap-analysis/

# List what's left (should be 6 scripts)
ls analyze*.py
```

---

## 📖 What Each Script Does

### 🌟 **Your Top 3 Scripts**:

1. **analyze_supabase_complete.py** (607 lines) ⭐⭐⭐
   - ML-powered deep analysis
   - PCA, clustering, anomaly detection
   - Generates charts and recommendations
   - Most sophisticated tool

2. **analyze_property_use_comprehensive.py** (303 lines) ⭐⭐
   - Complete Florida DOR property codes
   - Categorizes all property types
   - Generates frontend mappings

3. **analyze_tax_deed_status.py** (144 lines) 🚨
   - Critical for tax deed auctions
   - Finds why items don't show on website
   - Data quality checks

### 📊 **Useful Analysis Scripts**:

4. **analyze_supabase_tables.py** (233 lines)
   - Quick database overview
   - Table categorization
   - Simple and effective

5. **analyze_large_properties.py** (256 lines)
   - Analyzes luxury properties (7,500+ sqft)
   - No database needed (reads local CSVs)
   - Already secure ✅

6. **analyze_sales_tables.py** (260 lines)
   - Sales data analyzer
   - Tests specific parcels
   - Already secure ✅

---

## ⏱️ Time Estimate

| Task | Time |
|------|------|
| Security fix (4 files) | 5 min |
| Delete duplicate | 10 sec |
| Create archive structure | 30 sec |
| Move 4 files to archive | 1 min |
| **TOTAL** | **~7 minutes** |

---

## 🎬 Ready to Execute?

**Say:**
- **"fix security"** - I'll edit the 4 files
- **"do cleanup"** - I'll delete duplicate and create archives
- **"do everything"** - I'll fix security AND do cleanup

Or do it manually using commands above!

---

**Priority**: 🔴 **URGENT** (exposed credentials)
**Difficulty**: 🟢 **EASY** (simple find & replace)
**Impact**: ✅ **HIGH** (secure your database)
