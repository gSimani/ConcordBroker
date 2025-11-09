# TypeScript Strict Mode Enablement Plan

**Date**: November 9, 2025
**Current State**: 307 TypeScript errors (strict mode: OFF)
**Goal**: Enable strict mode and achieve 0 errors

---

## Error Analysis

### Current Error Breakdown
```
Total Errors: 307

By Type:
  TS2339 (171 errors) - Property does not exist on type
  TS2551 (44 errors)  - Property does not exist (with suggestion)
  TS2345 (25 errors)  - Argument type not assignable
  TS2322 (18 errors)  - Type not assignable to type
  TS2304 (11 errors)  - Cannot find name
  TS2552 (8 errors)   - Cannot find name (with suggestion)
  TS2305 (5 errors)   - Module has no exported member
  Other  (25 errors)  - Various type errors
```

### Root Causes

**1. Inconsistent Field Names (215 errors - 70%)**
   - Database returns `property_use` but types expect `propertyUse`
   - Database returns `tv_nsd` but types expect `tv_sd`
   - Units field has 3+ variations: `units`, `no_res_unts`, `no_units`
   - **Solution**: Implement field name standardization (from audit recommendation #6)

**2. Missing Type Definitions (11 errors - 4%)**
   - `WifiOff` icon not imported
   - Missing dependencies: `react-virtualized-auto-sizer`
   - Duplicate imports

**3. Missing Package Exports (5 errors - 2%)**
   - `formatCurrency`, `formatNumber` not exported from `@/lib/utils`
   - `VariableSizeList` not in `react-window`

**4. Type Mismatches (73 errors - 24%)**
   - Property types don't match interface definitions
   - Function argument type mismatches
   - Enum/union type incompatibilities

---

## Implementation Roadmap

### Phase 1: Pre-Strict Mode Fixes (Recommended Before Enabling Strict)

#### Step 1.1: Fix Field Name Inconsistencies
**Priority**: CRITICAL
**Estimated Time**: 4-6 hours
**Errors Fixed**: ~215 errors

**Actions**:
1. Implement `normalizePropertyData()` utility (create `apps/web/src/lib/propertyFieldMapping.ts`)
2. Update `MiniPropertyCard.tsx` to use normalized fields
3. Update `FastPropertySearch.tsx` property references
4. Update all property tabs to use normalized data

**Files to modify**:
```
apps/web/src/lib/propertyFieldMapping.ts (NEW)
apps/web/src/components/property/MiniPropertyCard.tsx
apps/web/src/components/FastPropertySearch.tsx
apps/web/src/components/property/tabs/*.tsx (8 files)
apps/web/src/hooks/usePropertyData.ts
```

#### Step 1.2: Fix Missing Imports
**Priority**: HIGH
**Estimated Time**: 30 minutes
**Errors Fixed**: ~15 errors

**Actions**:
1. Add `WifiOff` import to `RealtimeMonitoringDashboard.tsx`
2. Fix duplicate `LineChart` imports
3. Install missing package: `npm install react-virtualized-auto-sizer`
4. Export `formatCurrency` and `formatNumber` from `lib/utils.ts`

#### Step 1.3: Fix Type Definition Issues
**Priority**: MEDIUM
**Estimated Time**: 2 hours
**Errors Fixed**: ~40 errors

**Actions**:
1. Create proper `PropertyData` interface in `apps/web/src/types/property.ts`
2. Fix `FloridaParcelData` interface to include all required fields
3. Update `Suggestion` type to include `"county"` option
4. Fix `useSunbizMatch` hook type definitions

#### Step 1.4: Fix Component Props
**Priority**: MEDIUM
**Estimated Time**: 1-2 hours
**Errors Fixed**: ~30 errors

**Actions**:
1. Fix `LineChart` component - not using correct recharts component
2. Fix lazy load import in `App.tsx` (PerformanceTest missing default export)
3. Update `ElegantPropertyTabs.tsx` to pass complete property data

**Estimated Total**: 8-11 hours to fix all 307 existing errors

---

### Phase 2: Enable Strict Mode Gradually

#### Step 2.1: Enable `noImplicitAny`
```json
{
  "noImplicitAny": true
}
```

Run: `npx tsc --noEmit` and fix any new errors (estimated: 20-30 new errors)

#### Step 2.2: Enable `strictNullChecks`
```json
{
  "strictNullChecks": true
}
```

Run: `npx tsc --noEmit` and fix any new errors (estimated: 40-60 new errors)

#### Step 2.3: Enable Full Strict Mode
```json
{
  "strict": true,
  "noUnusedLocals": true,
  "noUnusedParameters": true
}
```

Run: `npx tsc --noEmit` and fix all remaining errors (estimated: 50-80 new errors)

---

### Phase 3: Verification

1. Run full type check: `npx tsc --noEmit`
2. Verify no build errors: `npm run build`
3. Test application functionality
4. Commit changes

---

## Quick Start Commands

```bash
# Check current errors
cd apps/web
npx tsc --noEmit

# Count errors by type
npx tsc --noEmit 2>&1 | grep "error TS" | sed 's/.*error //' | sed 's/:.*//' | sort | uniq -c | sort -rn

# Find all property field references
grep -r "property_use" src/
grep -r "tv_nsd" src/
grep -r "no_res_unts" src/

# Test build
npm run build
```

---

## Files That Need Attention

### High Priority (Most Errors)
1. `src/components/property/MiniPropertyCard.tsx` - 40+ errors
2. `src/components/FastPropertySearch.tsx` - 20+ errors
3. `src/components/property/tabs/CorePropertyTab.tsx` - 15+ errors
4. `src/components/property/tabs/AnalysisTab.tsx` - 15+ errors
5. `src/components/monitoring/RealtimeMonitoringDashboard.tsx` - 12+ errors

### Medium Priority
6. `src/components/OptimizedPropertyList.tsx` - 5 errors
7. `src/components/OptimizedSearchBar.tsx` - 2 errors
8. `src/components/property/ElegantPropertyTabs.tsx` - 3 errors

---

## Recommended Approach

### Option A: Full Fix (Recommended)
1. Fix all 307 existing errors first (Phase 1)
2. Then enable strict mode gradually (Phase 2)
3. Fix new strict mode errors as they appear

**Timeline**: 2-3 days of focused work
**Result**: Clean, type-safe codebase

### Option B: Gradual Approach
1. Fix critical errors only (~100 errors)
2. Suppress remaining errors with `// @ts-ignore` comments
3. Enable strict mode for new files only

**Timeline**: 1 day
**Result**: Partial type safety, technical debt remains

### Option C: File-by-File Strict Mode
1. Add `// @ts-strict` comment to individual files
2. Fix errors file-by-file over time
3. Enable strict mode globally when all files are clean

**Timeline**: Ongoing (2-4 weeks)
**Result**: Incremental improvement

---

## Next Steps

### Immediate (Do Now)
1. Create `propertyFieldMapping.ts` utility for field name normalization
2. Fix the 15 import errors (quick wins)
3. Install missing package: `react-virtualized-auto-sizer`

### This Week
1. Implement field standardization across all components
2. Fix type definitions for `PropertyData` and `FloridaParcelData`
3. Run type check to verify progress

### Next Week
1. Enable `noImplicitAny` and fix new errors
2. Enable `strictNullChecks` and fix new errors
3. Enable full strict mode

### Goal
**Zero TypeScript errors with strict mode enabled by end of Week 2**

---

## Success Metrics

- ✅ 0 TypeScript errors
- ✅ Strict mode enabled
- ✅ Build succeeds without warnings
- ✅ All components properly typed
- ✅ No `any` types (except where truly necessary)
- ✅ No `// @ts-ignore` comments

---

*Generated by Claude Code - November 9, 2025*
