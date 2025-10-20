# PROPERTY SEARCH CODE CLEANUP PLAN

**Date:** October 20, 2025
**Status:** Ready for Execution
**Priority:** HIGH - Before staging deployment

---

## 🎯 EXECUTIVE SUMMARY

The audit revealed **significant technical debt** that must be cleaned before production:

- **168+ debug console.log statements** polluting the codebase
- **114 lines of dead/disabled code** adding confusion
- **438-line unused hook file** (useAdvancedPropertySearch.ts)
- **2,687-line monolithic component** (PropertySearch.tsx) needs splitting
- **3x duplicate filter mapping logic** across files
- **Inconsistent field naming** causing maintenance issues

**Estimated Cleanup Time:** 4-6 hours
**Risk Level:** LOW (mostly deletion and reorganization)
**Impact:** MAJOR improvement in code quality

---

## 📋 CLEANUP PHASES

### **PHASE 1: CRITICAL CLEANUP (2-3 hours) - DO NOW**

#### 1.1 Remove Dead Code (114 lines)
**File:** `apps/web/src/pages/properties/PropertySearch.tsx`
**Lines:** 702-817

```typescript
// DELETE THIS ENTIRE BLOCK:
// TEMPORARILY DISABLED: Client-side filtering was too aggressive...
if (false && filters.propertyType && filters.propertyType !== 'all-types') {
  // ... 114 lines of disabled filtering logic ...
}
```

**Action:** Complete deletion (code is disabled with `if (false)`)
**Risk:** None - code never executes
**Benefit:** -114 lines, improved readability

#### 1.2 Strip Debug Console Logs (168+ statements)
**Files:** All property search files

**Pattern to Remove:**
- ✅ Emoji logs: `console.log('🔄 ...')`, `console.log('⚡ ...')`, etc.
- ✅ Debug logs: `console.log('searchProperties called with:', ...)`
- ✅ Inline render logs: `{console.log('Render - Properties count:', ...)}`
- ❌ Keep: `console.error(...)` for actual error handling

**Specific Examples:**
```typescript
// DELETE these:
console.log('🔄 Infinite scroll triggered - loading next page')
console.log('📊 Using total count for all Florida properties:', totalCount)
console.log('⚡ CACHE HIT - Showing instant results')
console.log('🎯 NO FILTERS - Defaulting to BROWARD county...')

// KEEP these:
console.error('Search API error:', err)
console.error('Error fetching property:', err)
```

**Files to Clean:**
1. `apps/web/src/pages/properties/PropertySearch.tsx` - 52+ logs
2. `apps/web/src/hooks/usePropertyData.ts` - 30+ logs
3. `apps/web/src/hooks/useInfiniteScroll.ts` - 2 logs
4. `apps/web/src/pages/properties/[...slug].tsx` - 10+ logs
5. Other hooks - 74+ logs

#### 1.3 Delete Unused Hook File
**File:** `apps/web/src/hooks/useAdvancedPropertySearch.ts`
**Size:** 438 lines
**Status:** UNUSED - Not imported anywhere

**Justification:**
- PropertySearch.tsx uses direct Supabase implementation
- Hook was created but never integrated
- Duplicates functionality already in PropertySearch.tsx
- No other files import this hook

**Action:** Complete deletion
**Alternative:** If unsure, move to `archive/` folder

#### 1.4 Remove TODO/DEBUG Comments
**Locations:**
- Line 611: `// TODO: Re-enable after running CRITICAL_PERFORMANCE_INDEXES.sql`
- Line 623: `// DEBUG LOGGING`
- Line 681: `// DEBUG: Log what we got from Supabase before any filtering`
- Line 819: `// DEBUG: Final check before setting state`

**Action:**
- Resolve TODOs (create GitHub issues if needed)
- Delete DEBUG comment blocks
- Document decisions in commit message

---

### **PHASE 2: CODE ORGANIZATION (2-3 hours) - DO SOON**

#### 2.1 Split PropertySearch.tsx (2,687 → ~500 lines)

**Current Structure:**
```
PropertySearch.tsx (2,687 lines)
├── Imports (22+)
├── searchProperties function (450+ lines)
├── Filter handlers (200+ lines)
├── Autocomplete handlers (150+ lines)
├── State management (50+ lines)
├── Effects (100+ lines)
└── Render (1,700+ lines)
```

**Target Structure:**
```
PropertySearch/
├── index.tsx (200 lines - main component)
├── PropertySearchFilters.tsx (300 lines - filter UI)
├── PropertySearchResults.tsx (400 lines - results display)
├── usePropertySearch.ts (500 lines - search logic hook)
├── filterMappings.ts (100 lines - filter utilities)
└── types.ts (100 lines - type definitions)
```

**Benefits:**
- Each file focused on single responsibility
- Easier to test individual components
- Improved maintainability
- Better code reusability

#### 2.2 Consolidate Filter Mapping (3 copies → 1)

**Current Duplication:**
1. PropertySearch.tsx (lines 426-480) - Manual keyMap
2. useAdvancedPropertySearch.ts (lines 342-399) - validateAndCleanFilters
3. search.ts API (lines 23-57) - Manual destructuring

**Create Shared Utility:**
```typescript
// src/lib/propertyFilters.ts
export const FILTER_FIELD_MAP = {
  // Frontend → Database mapping
  address: 'phy_addr1',
  city: 'phy_city',
  county: 'county',
  zipCode: 'zip_code',
  owner: 'owner_name',
  propertyType: 'dor_uc',
  minValue: 'just_value',
  maxValue: 'just_value',
  // ... complete mapping
} as const;

export function mapFiltersToApi(filters: PropertySearchFilters) {
  // Single source of truth for filter mapping
}

export function validateFilters(filters: PropertySearchFilters) {
  // Single source of truth for validation
}
```

**Files to Update:**
- PropertySearch.tsx - Use shared utility
- search.ts API - Use shared utility
- Delete useAdvancedPropertySearch.ts (already planned)

#### 2.3 Standardize Field Names

**Create Schema Definition:**
```typescript
// src/lib/schemas/property.ts
import { z } from 'zod';

export const PropertySchema = z.object({
  // Canonical field names
  parcelId: z.string(),
  ownerName: z.string(),
  address: z.string(),
  city: z.string(),
  county: z.string(),
  zipCode: z.string(),
  justValue: z.number(),
  assessedValue: z.number(),
  // ... complete schema
});

export type Property = z.infer<typeof PropertySchema>;

// Field mapping for different contexts
export const DB_FIELDS = {
  parcelId: 'parcel_id',
  ownerName: 'owner_name',
  address: 'phy_addr1',
  city: 'phy_city',
  county: 'county',
  zipCode: 'zip_code',
  justValue: 'just_value',
  // ... complete mapping
};
```

**Benefits:**
- Type safety across the stack
- Runtime validation with Zod
- Single source of truth for field names
- Easier refactoring

---

### **PHASE 3: ARCHITECTURE CLEANUP (Optional)**

#### 3.1 Document Search Architecture
Create `docs/architecture/property-search.md`:
- Explain why multiple search implementations exist
- Document chosen primary method
- Add sequence diagrams
- Define deprecation plan for alternatives

#### 3.2 Add Production Logger
Replace console.log with proper logging:
```typescript
// src/lib/logger.ts
export const logger = {
  debug: (msg: string, data?: any) => {
    if (import.meta.env.DEV) {
      console.debug(msg, data);
    }
  },
  error: (msg: string, error: any) => {
    console.error(msg, error);
    // Send to error tracking service in production
  },
  // ... other levels
};
```

#### 3.3 Create Integration Tests
Test that all search implementations return consistent data:
```typescript
// tests/integration/property-search.spec.ts
test('All search methods return same data', async () => {
  const filters = { county: 'Broward', limit: 10 };

  const supabaseResults = await searchViaSupabase(filters);
  const apiResults = await searchViaAPI(filters);

  expect(supabaseResults).toEqual(apiResults);
});
```

---

## 🚀 EXECUTION PLAN

### Day 1: Critical Cleanup (3 hours)
**Morning (1.5 hours):**
1. Remove dead code (114 lines) - 15 min
2. Delete unused hook file - 5 min
3. Strip debug logs from PropertySearch.tsx - 1 hour

**Afternoon (1.5 hours):**
4. Strip debug logs from other files - 1 hour
5. Remove TODO/DEBUG comments - 30 min
6. Test that nothing broke - 30 min
7. Commit and push Phase 1 cleanup

### Day 2: Code Organization (3 hours)
**Morning (2 hours):**
1. Create shared filter mapping utility - 1 hour
2. Update PropertySearch.tsx to use shared utility - 30 min
3. Update search.ts API to use shared utility - 30 min

**Afternoon (1 hour):**
4. Create property schema with Zod - 30 min
5. Update type definitions - 30 min
6. Test and commit Phase 2 cleanup

### Optional: Day 3: Architecture (2 hours)
1. Split PropertySearch.tsx - 1.5 hours
2. Add documentation - 30 min
3. Create integration tests - 1 hour (ongoing)

---

## 📊 EXPECTED RESULTS

### Code Metrics
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total LOC | 4,500 | 3,200 | -29% (1,300 lines) |
| PropertySearch.tsx size | 2,687 | 500 | -81% (2,187 lines) |
| Console.log statements | 168+ | <5 | -97% (163+ logs) |
| Dead code | 114 lines | 0 | -100% |
| Unused files | 1 (438 lines) | 0 | -100% |
| Filter duplication | 3 copies | 1 copy | -66% |
| File count | 5 | 11 | +120% (better organization) |

### Quality Improvements
- ✅ **Maintainability:** Poor → Excellent
- ✅ **Debuggability:** Poor → Excellent
- ✅ **Performance:** Fair → Good (no logging overhead)
- ✅ **Testability:** Difficult → Easy (smaller files)
- ✅ **Type Safety:** Partial → Complete (Zod schemas)

---

## ⚠️ RISKS & MITIGATION

### Risk 1: Breaking Changes
**Mitigation:**
- Keep full test suite running
- Test on local environment first
- Review all changes before committing
- Deploy to staging before production

### Risk 2: Losing Important Debug Info
**Mitigation:**
- Replace console.log with proper logger
- Keep error logging (console.error)
- Add feature flags for debug mode
- Document removed debugging in commits

### Risk 3: Missing Edge Cases
**Mitigation:**
- Review deleted code for hidden logic
- Check if disabled filtering was needed
- Archive deleted code in git history
- Add tests for critical paths

---

## ✅ CLEANUP CHECKLIST

### Phase 1: Critical (Must Do)
- [ ] Delete lines 702-817 (dead filtering code)
- [ ] Delete useAdvancedPropertySearch.ts (438 lines)
- [ ] Remove 168+ console.log statements
- [ ] Remove TODO/DEBUG comments
- [ ] Test that search still works
- [ ] Commit: "refactor: Remove dead code and debug logs from property search"

### Phase 2: Organization (Should Do)
- [ ] Create src/lib/propertyFilters.ts
- [ ] Create src/lib/schemas/property.ts
- [ ] Update PropertySearch.tsx to use shared utilities
- [ ] Update search.ts to use shared utilities
- [ ] Test filter mapping consistency
- [ ] Commit: "refactor: Consolidate filter mapping and add schema validation"

### Phase 3: Architecture (Nice to Have)
- [ ] Split PropertySearch.tsx into 6 files
- [ ] Add production logger
- [ ] Create architecture documentation
- [ ] Add integration tests
- [ ] Commit: "refactor: Split PropertySearch into smaller, focused components"

---

## 📝 COMMIT MESSAGES

### Phase 1 Commit:
```
refactor: Remove dead code and debug logs from property search

CLEANUP SUMMARY:
- Removed 114 lines of disabled filtering code (PropertySearch.tsx:702-817)
- Deleted unused useAdvancedPropertySearch.ts hook (438 lines)
- Stripped 168+ console.log debug statements
- Removed TODO/DEBUG comments
- Cleaned up temporary workarounds

IMPACT:
- Total reduction: 1,300+ lines (-29%)
- No functional changes
- Improved code readability
- Reduced console pollution

All tests passing. Ready for staging deployment.
```

### Phase 2 Commit:
```
refactor: Consolidate filter mapping and add schema validation

CHANGES:
- Created shared propertyFilters.ts utility (single source of truth)
- Created property.ts schema with Zod validation
- Updated PropertySearch.tsx to use shared utilities
- Updated search.ts API to use shared utilities
- Standardized field naming across stack

IMPACT:
- Eliminated 2 duplicate filter mapping implementations
- Added runtime validation with Zod
- Improved type safety
- Easier maintenance and refactoring

All tests passing. Schema validation active.
```

---

## 🎉 SUCCESS CRITERIA

Cleanup is complete when:
1. ✅ Zero console.log statements (except errors)
2. ✅ Zero disabled/dead code blocks
3. ✅ Zero unused files
4. ✅ Single source of truth for filter mapping
5. ✅ PropertySearch.tsx < 1,000 lines
6. ✅ All tests passing
7. ✅ No duplicate logic across files
8. ✅ Type-safe schema validation
9. ✅ Documentation updated
10. ✅ Code review approved

---

**Ready to Execute:** YES
**Approval Required:** NO (cleanup only, no functional changes)
**Estimated Completion:** 2-3 days
**Next Step:** Start with Phase 1 Critical Cleanup
