# Console Error Analysis - Commercial Filter Issues

**Date**: 2025-10-30
**Status**: 🔍 INVESTIGATION COMPLETE

---

## Console Errors Discovered

### Error #1: 404 Not Found - useOptimizedSearch Hook
**Location**: `useOptimizedSearch.ts:197`

```
GET http://localhost:5193/api/properties/search?use_index=true&optimize_for_speed=true&include_total=true 404 (Not Found)
Search error: Error: Search failed: 404
```

**Root Cause**:
- `useOptimizedSearch.ts` tries to fetch from `/api/properties/search` endpoint
- This endpoint doesn't exist (no backend API at this path)
- The hook was designed for an API-based search but PropertySearch now queries Supabase directly

**Impact**:
- Initial search fails
- Falls back to direct Supabase query (which works)
- User sees brief error but functionality continues

**Solution Options**:
1. Remove `useOptimizedSearch` hook entirely (not used by PropertySearch)
2. Create the `/api/properties/search` endpoint in the backend
3. Update PropertySearch to not call this hook

**Recommendation**: Remove unused hook or disable its auto-initialization

---

### Error #2: React Icon Warning (24+ occurrences)
**Location**: `MiniPropertyCard.tsx:339`

```
Warning: <Home /> is using incorrect casing. Use PascalCase for React components, or lowercase for HTML elements.
    at Home
    at div
    at Badge
```

**Root Cause**:
- Icon component is being passed as a string `'Home'` instead of the actual component `Home`
- Conditional rendering fix (`CategoryIconComponent &&`) didn't solve it
- The issue is HOW the icon is stored/passed, not just rendering

**Current Code (Line 347)**:
```typescript
{CategoryIconComponent && <CategoryIconComponent className="w-3 h-3 mr-1" />}
```

**Actual Problem**:
```typescript
const CategoryIconComponent = categoryStyle.icon;  // Returns 'Home' string, not component
```

**Fix Required**:
Check how `getCategoryStyle()` returns the icon. It should return the component reference, not a string.

---

### Error #3: Infinite Query Loop (30+ redundant queries)
**Location**: `PropertySearch.tsx` - useEffect

```
PropertySearch.tsx:562 [FILTER DEBUG] Applying property_use filter... (repeated 30+ times)
PropertySearch.tsx:655 [FILTER DEBUG] Query returned properties... (repeated 30+ times)
```

**Root Cause**:
- useEffect at line 302 triggers `searchProperties(1)` when filters change
- `searchProperties` updates state (setProperties, setTotalResults, etc.)
- State updates trigger re-render
- Re-render triggers useEffect again (if dependencies include updated state)
- Infinite loop

**Evidence**:
- Filter applied identically 30+ times with same parameters
- All queries return same 500 properties
- Performance impact: Multiple unnecessary database queries

**Investigation Needed**:
```typescript
// Line 302-346
useEffect(() => {
  // ...
}, [filters]); // ⚠️ Check if 'filters' object changes on every render
```

**Likely Issues**:
1. `filters` object is recreated on every render (reference changes)
2. `searchProperties` is in useEffect dependencies (line 739)
3. Missing memoization on filter objects

---

### Error #4: Mixed Property Types (CONFIRMED from Debug Logs)
**Evidence from Console**:

```
PropertySearch.tsx:655 [FILTER DEBUG] Query returned properties: {count: 500, firstFive: Array(5)}
```

**What we need to see** (expand firstFive array):
```json
{
  "count": 500,
  "firstFive": [
    { "parcel_id": "...", "property_use": "COMM", "address": "..." },
    { "parcel_id": "...", "property_use": "SFR", "address": "..." },  // ❌ WRONG
    { "parcel_id": "...", "property_use": "VAC", "address": "..." },  // ❌ WRONG
  ]
}
```

**To Debug**:
Need to expand the `firstFive` array in console to see actual `property_use` values being returned.

---

## Debug Commands to Run

### 1. Check firstFive Array Contents
In browser console, run:
```javascript
// Expand the logged object
console.table(
  document.querySelectorAll('[class*="badge"]')
    .forEach(b => console.log(b.textContent))
);
```

### 2. Check Filter State
```javascript
// Check if filters object is stable
let prevFilters = null;
setInterval(() => {
  const filters = /* get from React DevTools */;
  if (prevFilters && JSON.stringify(filters) !== JSON.stringify(prevFilters)) {
    console.log('Filters changed:', filters);
  }
  prevFilters = filters;
}, 100);
```

### 3. Count Re-renders
```javascript
// In PropertySearch component
const renderCount = useRef(0);
useEffect(() => {
  renderCount.current += 1;
  console.log(`[RENDER COUNT] PropertySearch rendered ${renderCount.current} times`);
});
```

---

## Verification Steps

### Step 1: Expand firstFive in Console
**Current Output**:
```
PropertySearch.tsx:655 [FILTER DEBUG] Query returned properties: {count: 500, firstFive: Array(5)}
```

**Need to see**:
```javascript
// Click the Array(5) in console to expand it
// Should show 5 objects with property_use values
// ALL should be commercial codes (COMM, 011, 12, etc.)
```

### Step 2: Check Cache Key
**Add logging**:
```typescript
console.log('[CACHE DEBUG] Cache key:', cacheKey);
console.log('[CACHE DEBUG] API Filters:', JSON.stringify(apiFilters));
```

**Expected**:
- Cache key should include "Commercial" or property type
- Different cache key for filtered vs unfiltered

---

## Priority Fixes

### HIGH PRIORITY:
1. **Fix infinite query loop** (30+ redundant queries)
   - Add render count logging
   - Memoize filter objects
   - Check useEffect dependencies

2. **Verify firstFive contents** (confirm filter actually works)
   - Expand array in console
   - Check if ALL returned properties are commercial

### MEDIUM PRIORITY:
3. **Fix icon warning** (24+ warnings cluttering console)
   - Check `getCategoryStyle()` icon storage
   - Ensure icon is component reference, not string

### LOW PRIORITY:
4. **Remove 404 error** (useOptimizedSearch hook)
   - Disable or remove unused hook
   - Or create the missing API endpoint

---

## Analysis Summary

**What's Working**:
- ✅ Filter is being applied (75 DOR codes, correct samples)
- ✅ Query returns 500 properties
- ✅ Cache clearing triggers
- ✅ Debug logging shows filter activation

**What's Broken**:
- ❌ Infinite query loop (30+ redundant queries)
- ❌ Mixed property types visible in UI (screenshot evidence)
- ❌ Icon warnings (24+ console errors)
- ❌ 404 error on initial load

**What's Unknown**:
- ❓ Are the returned properties ACTUALLY commercial? (need to expand firstFive)
- ❓ Why does UI show mixed types if query returns filtered results?
- ❓ Is the issue client-side filtering AFTER the query?

---

## Next Investigation Steps

1. **Expand `firstFive` array** in browser console to see actual property_use values
2. **Add render count** to identify infinite loop source
3. **Check MiniPropertyCard** client-side filtering logic
4. **Verify sortByPropertyRank** isn't mixing in wrong properties

**Files to Investigate**:
- `PropertySearch.tsx:685-687` - `sortByPropertyRank()` function
- `PropertySearch.tsx:302-346` - useEffect dependencies
- `MiniPropertyCard.tsx` - How badges are determined
- `VirtualizedPropertyList.tsx` - How properties are passed to cards

---

## Conclusion

The filter IS being applied at the database level (confirmed by debug logs), but either:
1. The returned properties include non-commercial types (need to verify with firstFive expansion)
2. Client-side sorting/filtering is adding non-commercial properties after the query
3. The UI is displaying stale/cached data despite the query running

**Critical Next Step**: Expand `firstFive` array in console to see actual database results.
