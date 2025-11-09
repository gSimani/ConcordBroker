# DOR Use Code Assignment - Execution Guide

## 📊 Mission Overview

**Objective**: Assign DOR use codes to 5,952,048 Florida properties (currently at 34.69% coverage → target 99.5%+)

**Total Properties**: 9,113,150
**Already Coded**: 3,161,102 (34.69%)
**Need Assignment**: 5,952,048 (65.31%)

---

## 🚀 Execution Methods

### Method 1: Single Bulk UPDATE (RECOMMENDED)

**File**: `EXECUTE_DOR_ASSIGNMENT.sql`

**Pros**:
- Single query handles all 5.95M properties
- Fastest if no timeout (15-30 minutes estimated)
- Simplest execution

**Cons**:
- May timeout on large dataset
- Requires elevated database privileges

**Steps**:
1. Open Supabase SQL Editor (https://app.supabase.com)
2. Select service_role or postgres role
3. Copy content from `EXECUTE_DOR_ASSIGNMENT.sql`
4. Execute PHASE 1 to check current status
5. Execute PHASE 2 (THE MAIN UPDATE)
6. Execute PHASE 3 to verify results
7. Execute PHASE 4 for distribution analysis

**Expected Execution Time**: 15-30 minutes

---

### Method 2: County-Batched Execution (IF METHOD 1 TIMES OUT)

**File**: `BATCH_UPDATE_BY_COUNTY.sql`

**Pros**:
- No timeout risk (each county is small batch)
- Progress tracking per county
- Can resume if interrupted
- Works even with strict timeout limits

**Cons**:
- Requires running 67 separate UPDATEs
- Takes longer (30-60 minutes total)
- More manual steps

**Steps**:
1. Open Supabase SQL Editor
2. Run STEP 1 query to get county list
3. Copy the UPDATE template for each county
4. Execute top 10 counties first (Miami-Dade, Broward, Palm Beach, etc.)
5. Continue with remaining 57 counties
6. Run STEP 3 for final validation

**Expected Execution Time**: 30-60 minutes (67 counties × ~30 seconds each)

---

### Method 3: Python REST API (IF SQL ACCESS LIMITED)

**File**: `execute_dor_supabase_rest.py`

**Pros**:
- No direct SQL access needed
- Uses Supabase REST API
- Automatic progress tracking
- Detailed JSON report generated

**Cons**:
- Slower (REST API overhead)
- Requires Python environment
- May hit rate limits

**Steps**:
```bash
python execute_dor_supabase_rest.py
```

**Expected Execution Time**: 2-3 hours (REST API is slower)

---

### Method 4: Direct PostgreSQL Connection (IF NO NETWORK RESTRICTIONS)

**File**: `execute_dor_postgresql.py`

**Pros**:
- Fastest Python method
- Direct database connection
- Full transaction control

**Cons**:
- Requires PostgreSQL port 5432 access
- May be blocked by network/firewall

**Steps**:
```bash
python execute_dor_postgresql.py
```

**Expected Execution Time**: 20-40 minutes

---

## 🧠 Assignment Logic

Properties are classified in priority order:

### Priority 1: Multi-Family 10+ (Code: 02)
- `building_value > 500,000`
- `building_value > land_value * 2`
- **Label**: "MF 10+"

### Priority 2: Industrial (Code: 24)
- `building_value > 1,000,000`
- `land_value < 500,000`
- **Label**: "Industria" (10 char limit)

### Priority 3: Commercial (Code: 17)
- `just_value > 500,000`
- `building_value > 200,000`
- `building_value between land_value * 0.3 and land_value * 4`
- **Label**: "Commercia" (10 char limit)

### Priority 4: Agricultural (Code: 01)
- `land_value > building_value * 5`
- `land_value > 100,000`
- **Label**: "Agricult." (10 char limit)

### Priority 5: Condominium (Code: 03)
- `just_value between 100,000 and 500,000`
- `building_value between 50,000 and 300,000`
- `building_value between land_value * 0.8 and land_value * 1.5`
- **Label**: "Condo"

### Priority 6: Vacant Residential (Code: 10)
- `land_value > 0`
- `building_value < 1,000` or NULL
- **Label**: "Vacant Re" (10 char limit)

### Priority 7: Single Family (Code: 00)
- `building_value > 50,000`
- `building_value > land_value`
- `just_value < 1,000,000`
- **Label**: "SFR"

### Priority 8: Default (Code: 00)
- All other properties
- **Label**: "SFR"

---

## ✅ Validation Checklist

After execution, verify:

### 1. Coverage Percentage
```sql
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code,
    ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025;
```
**Target**: ≥ 99.5% coverage

### 2. Distribution Analysis
```sql
SELECT
    land_use_code,
    property_use,
    COUNT(*) as count,
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM florida_parcels WHERE year = 2025) * 100, 2) as pct
FROM florida_parcels
WHERE year = 2025 AND land_use_code IS NOT NULL
GROUP BY land_use_code, property_use
ORDER BY count DESC
LIMIT 10;
```
**Expect**: Majority will be "00" (SFR), significant "10" (Vacant), smaller "17"/"24"/"02"

### 3. Gap Analysis
```sql
SELECT county, COUNT(*) as missing
FROM florida_parcels
WHERE year = 2025
    AND (land_use_code IS NULL OR land_use_code = '')
GROUP BY county
HAVING COUNT(*) > 0
ORDER BY COUNT(*) DESC;
```
**Target**: 0 counties with gaps (or < 0.5% of properties)

---

## 📈 Expected Results

### Before Execution
- Total Properties: **9,113,150**
- With Code: **3,161,102**
- Coverage: **34.69%**

### After Execution (Target)
- Total Properties: **9,113,150**
- With Code: **≥ 9,067,584** (99.5%)
- Coverage: **≥ 99.5%**
- Properties Updated: **≥ 5,906,482**

### Distribution Estimates
- **00** (SFR): ~60-70% (5.5-6.4M properties)
- **10** (Vacant Res): ~15-20% (1.4-1.8M properties)
- **17** (Commercial): ~3-5% (270-450K properties)
- **02** (Multi-Family): ~2-3% (180-270K properties)
- **24** (Industrial): ~1-2% (90-180K properties)
- **01** (Agricultural): ~1-2% (90-180K properties)
- **03** (Condo): ~5-8% (450-730K properties)

---

## 🎯 Success Rating System

- **10/10**: 100.0% coverage, perfect distribution
- **9/10**: 99.5-99.9% coverage, excellent distribution
- **8/10**: 95.0-99.4% coverage, good distribution
- **7/10**: 90.0-94.9% coverage, acceptable distribution
- **6/10**: < 90.0% coverage, needs improvement

---

## 🔧 Troubleshooting

### Issue: Query Timeout
**Solution**: Use Method 2 (County-Batched) instead of Method 1

### Issue: Insufficient Privileges
**Solution**: Use service_role key in Supabase or grant UPDATE privileges

### Issue: Network Connection Failed
**Solution**: Use Method 3 (REST API) which works through HTTPS

### Issue: Some Properties Still Missing Codes
**Solution**: Check for NULL values in building_value, land_value, just_value fields

### Issue: Property_use Column Truncated
**Note**: Column has 10-character limit, labels are intentionally shortened:
- "Industrial" → "Industria"
- "Commercial" → "Commercia"
- "Agricultural" → "Agricult."
- "Vacant Residential" → "Vacant Re"

---

## 📝 Post-Execution Tasks

1. **Generate Final Report**:
   - Save coverage statistics
   - Document distribution
   - Record execution time
   - Note any gaps

2. **Verify Frontend Integration**:
   - Check MiniPropertyCard displays use codes
   - Test PropertySearch filters
   - Validate Core Property Tab shows correct codes

3. **Update Documentation**:
   - Mark DOR assignment as complete
   - Document final coverage achieved
   - Record lessons learned

4. **Monitor Performance**:
   - Check query performance on filtered searches
   - Verify indexes are used effectively
   - Monitor for any data quality issues

---

## 🚦 Recommended Execution Strategy

**STEP 1**: Try Method 1 (Single Bulk UPDATE)
- Fastest if it works
- If timeout occurs, proceed to Step 2

**STEP 2**: Use Method 2 (County-Batched)
- Guaranteed to work
- Process top 10 counties first for quick wins
- Complete remaining 57 counties

**STEP 3**: Validate Results
- Run all validation queries
- Verify distribution makes sense
- Check for gaps

**STEP 4**: Generate Reports
- Save execution report
- Document any issues
- Update project documentation

---

## 📊 Progress Tracking

### Phase 1: Discovery ✓
- [x] Analyzed county distribution
- [x] Identified 5.95M properties needing codes
- [x] Current coverage: 34.69%

### Phase 2: Top 10 Counties (Ready to Execute)
- [ ] Miami-Dade
- [ ] Broward
- [ ] Palm Beach
- [ ] Hillsborough
- [ ] Orange
- [ ] Pinellas
- [ ] Duval
- [ ] Lee
- [ ] Polk
- [ ] Pasco

### Phase 3: Remaining 57 Counties (Ready to Execute)
- [ ] Execute remaining county updates

### Phase 4: Validation & Analysis (After Execution)
- [ ] Verify 99.5%+ coverage
- [ ] Analyze distribution
- [ ] Check for gaps
- [ ] Generate final report

### Phase 5: Frontend Integration Verification
- [ ] Test MiniPropertyCard display
- [ ] Verify PropertySearch filters
- [ ] Check Core Property Tab
- [ ] Validate API responses

---

## 🎓 Key Learnings

1. **County-batching prevents timeouts** on large datasets
2. **Priority-ordered CASE statements** ensure intelligent classification
3. **COALESCE handles NULL values** gracefully
4. **10-character limit** requires abbreviated labels
5. **Service role key** required for bulk updates

---

## ✅ Completion Criteria

- [ ] Coverage ≥ 99.5%
- [ ] Distribution analysis complete
- [ ] No counties with >0.5% gaps
- [ ] Frontend displays codes correctly
- [ ] Final report generated
- [ ] Documentation updated

---

**Generated**: 2025-09-29
**Target Completion**: Immediate
**Priority**: CRITICAL
**Estimated Time**: 15-60 minutes (depending on method)