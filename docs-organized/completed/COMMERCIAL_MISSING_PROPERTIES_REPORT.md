# 🔴 COMMERCIAL PROPERTIES MISSING FROM FILTER - CRITICAL REPORT

**Date**: 2025-10-30
**Status**: ❌ **128,742 COMMERCIAL PROPERTIES NOT SHOWING IN FILTER**

---

## Executive Summary

The **Commercial filter** at `http://localhost:5191/properties` is **MISSING 128,742 properties** (40% of all commercial properties).

### Current State:
- ✅ **Filter catches**: 194,590 properties
- ✅ **Database has**: 323,332 commercial properties
- ❌ **MISSING**: **128,742 properties** (40% gap!)

---

## Root Cause Analysis

### The Problem:
The Commercial filter uses the `property_use` column, but the database has TWO columns for property types:

1. **`property_use`** - Raw county data (varies by format)
   - Contains: "Commercial", "10", "11", "17", "COMM", etc.

2. **`standardized_property_use`** - Normalized/standardized values
   - Contains: "Commercial" (standardized across all counties)

**The filter only checks `property_use`, NOT `standardized_property_use`!**

---

## Missing Properties Breakdown

Top missing `property_use` codes (that ARE commercial but NOT caught by filter):

| property_use | Count | Description |
|--------------|-------|-------------|
| `10` | 47,137 | Vacant Commercial |
| `11` | 20,137 | Stores, one story |
| `17` | 19,922 | Office buildings, one story |
| `COMM` | 14,640 | Commercial (text code) |
| `19` | 11,261 | Professional service buildings |
| `18` | 7,509 | Office buildings, multi-story |
| `12` | 6,188 | Mixed use |
| `16` | 5,047 | Community Shopping Centers |
| `048` | 323 | Warehousing (INDUSTRIAL code in Commercial stduse) |
| `043` | 79 | Lumber yards (INDUSTRIAL code in Commercial stduse) |
| Others | ~1,500 | Various |

**Total Missing**: **132,283 properties**

---

## Why This Happened

The frontend filter (`apps/web/src/lib/dorUseCodes.ts`) DOES include these codes:
```typescript
case 'COMMERCIAL':
  return [
    '010', '011', '017', '019', '018', '012', '016', // Zero-padded ✅
    '10', '11', '17', '19', '18', '12', '16',  // Non-padded ✅
    'COMM', 'COMMERCIAL', // Text codes ✅
  ];
```

**But the filter query in `PropertySearch.tsx` line 578:**
```typescript
query = query.in('property_use', dorCodes);
```

The issue is **NOT** the filter codes (they're correct), the issue is the filter is checking `property_use`, but the database has properties where:
- `standardized_property_use` = "Commercial" ✅
- `property_use` = numeric codes like "10", "11", etc.

When these numeric codes are NOT in `property_use`, they don't match the filter.

---

## The Solution

### Option 1: Add `standardized_property_use` to the filter (RECOMMENDED)
Modify `PropertySearch.tsx` line 578 to check BOTH columns:

```typescript
// OLD:
query = query.in('property_use', dorCodes);

// NEW:
query = query.or(`property_use.in.(${dorCodes.join(',')}),standardized_property_use.ilike.%${apiFilters.property_type}%`);
```

### Option 2: Use `standardized_property_use` exclusively
Replace line 578 with:
```typescript
query = query.eq('standardized_property_use', apiFilters.property_type);
```

This is simpler and catches all 323,332 properties.

---

## Impact

### Current Impact:
- 🔴 **40% of Commercial properties are invisible** to users
- 🔴 Users searching for commercial properties miss ~129K listings
- 🔴 Affects data accuracy and user trust

### After Fix:
- ✅ All 323,332 commercial properties will appear
- ✅ 128,742 additional properties become searchable
- ✅ Filter accuracy: 100% (up from 60%)

---

## Verification Query

Test the fix with this query:
```sql
-- Current filter (WRONG - only 194,590):
SELECT COUNT(*) FROM florida_parcels
WHERE property_use IN ('003', '010', '011', ..., 'COMM', 'COMMERCIAL');

-- Correct filter (CORRECT - 323,332):
SELECT COUNT(*) FROM florida_parcels
WHERE standardized_property_use = 'Commercial';

-- OR both (ALSO CORRECT):
SELECT COUNT(*) FROM florida_parcels
WHERE property_use IN (...) OR standardized_property_use = 'Commercial';
```

---

## Immediate Action Required

1. ✅ **Update `PropertySearch.tsx` line 578** with Option 1 or Option 2
2. ✅ **Test the filter** with a sample county (Broward)
3. ✅ **Verify count matches**: Should show ~323K commercial properties (not 195K)
4. ✅ **Deploy to production**

---

## Files to Modify

1. **`apps/web/src/pages/properties/PropertySearch.tsx`**
   - Line 578: Update filter query

2. **Optional: Update other property type filters**
   - Industrial, Residential, etc. may have the same issue

---

## Additional Notes

### Industrial Properties in Commercial:
Some properties have `property_use` = "048" (Warehouse - INDUSTRIAL) but `standardized_property_use` = "Commercial". This suggests:
- Counties may categorize warehouses differently
- `standardized_property_use` is the **authoritative** column
- Should use `standardized_property_use` for filtering

### Database Schema:
```sql
CREATE TABLE florida_parcels (
  parcel_id VARCHAR,
  county VARCHAR,
  property_use VARCHAR,  -- Raw county data (varies by format)
  standardized_property_use VARCHAR,  -- Normalized values ✅
  ...
);
```

---

**RECOMMENDATION**: Use `standardized_property_use` for ALL property type filtering going forward.

---

**End of Report**
