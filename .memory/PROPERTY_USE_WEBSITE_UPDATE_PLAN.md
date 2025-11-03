# Property USE/SUBUSE Website-Wide Update Plan
**PERMANENT REFERENCE - Implementation Roadmap**
**Created:** October 24, 2025

---

## 🎯 OBJECTIVE

Add property USE and SUBUSE display to EVERY component in the ConcordBroker website where properties are shown.

**Principle:** If a user sees a property, they should see its USE type.

---

## 📋 COMPLETE COMPONENT INVENTORY

### ✅ Phase 1: COMPLETED
- [X] **OptimizedSearchBar** - Autocomplete suggestions
  - File: `apps/web/src/components/OptimizedSearchBar.tsx`
  - Status: ✅ Shows USE description below address
  - Lines: 569-572

---

### ✅ Phase 2: HIGH PRIORITY (COMPLETE)

#### 1. **MiniPropertyCard** (CRITICAL) ✅ COMPLETE
- **File:** `apps/web/src/components/property/MiniPropertyCard.tsx`
- **Status:** ✅ Implemented - Shows USE badge with icon
- **Impact:** HIGH - Used everywhere in property lists
- **Completed:** October 24, 2025

**Implementation:**
```typescript
// Add to imports
import { getDorCodeFromPropertyUse, getPropertyUseDescription } from '@/lib/propertyUseToDorCode';

// In component
const dorCode = getDorCodeFromPropertyUse(data.property_use);
const useDescription = getPropertyUseDescription(data.property_use);

// Add to JSX (in property header section)
<div className="flex items-center gap-2 mt-1">
  <Badge variant="outline" className="text-xs">
    {useDescription}
  </Badge>
</div>
```

#### 2. **VirtualizedPropertyList** (CRITICAL) ✅ COMPLETE
- **File:** `apps/web/src/components/property/VirtualizedPropertyList.tsx`
- **Status:** ✅ Automatic - Delegates to MiniPropertyCard
- **Impact:** HIGH - Main property browsing interface
- **Completed:** October 24, 2025

**Implementation:**
- No direct changes needed - uses MiniPropertyCard for rendering
- USE badges automatically display in both grid and list views
- Maintains performance with virtualization

#### 3. **Property Detail Header** (CRITICAL) ✅ COMPLETE
- **File:** `apps/web/src/components/property/PropertyCompleteView.tsx`
- **Status:** ✅ Implemented - Prominent USE display in header
- **Impact:** HIGH - Every property detail page
- **Completed:** October 24, 2025

**Implementation:**
```typescript
// Added prominent USE badge in header (lines 216-231)
{data.property?.property_use && (() => {
  const dorCode = getDorCodeFromPropertyUse(data.property.property_use);
  const useDescription = getPropertyUseDescription(data.property.property_use);
  const IconComponent = getPropertyIcon(dorCode);
  const iconColor = getPropertyIconColor(dorCode);
  return (
    <div className="flex items-center gap-3 mt-2">
      <IconComponent className={`w-6 h-6 ${iconColor}`} />
      <div>
        <span className="text-sm text-gray-500">Property Type</span>
        <h3 className="text-lg font-semibold text-blue-600">{useDescription}</h3>
      </div>
    </div>
  );
})()}
```

#### 4. **CorePropertyTab** (HIGH) ✅ COMPLETE
- **File:** `apps/web/src/components/property/tabs/CorePropertyTab.tsx`
- **Status:** ✅ Implemented - Dedicated Property Classification section
- **Impact:** HIGH - Property details tab
- **Completed:** October 24, 2025

**Implementation:**
```typescript
// Add dedicated section
<section className="mb-6">
  <h3 className="text-lg font-semibold mb-3">Property Classification</h3>
  <dl className="grid grid-cols-2 gap-4">
    <div>
      <dt className="text-sm text-gray-500">Primary Use</dt>
      <dd className="text-base font-medium">{useDescription}</dd>
    </div>
    <div>
      <dt className="text-sm text-gray-500">DOR Code</dt>
      <dd className="text-base font-medium">{dorCode}</dd>
    </div>
    <div>
      <dt className="text-sm text-gray-500">Category</dt>
      <dd className="text-base font-medium">{category}</dd>
    </div>
    <div>
      <dt className="text-sm text-gray-500">Land Use Code</dt>
      <dd className="text-base font-medium">{land_use_code}</dd>
    </div>
  </dl>
</section>
```

---

### ⚠️ Phase 3: MEDIUM PRIORITY

#### 5. **OverviewTab** (MEDIUM)
- **File:** `apps/web/src/components/property/tabs/OverviewTab.tsx`
- **Current:** Property overview with key metrics
- **Missing:** USE in summary
- **Impact:** MEDIUM - Summary information
- **Estimated Time:** 30 minutes

#### 6. **Advanced Filters** (MEDIUM)
- **File:** Various filter components
- **Current:** Filters by price, location, size
- **Missing:** Filter by USE category
- **Impact:** MEDIUM - Search functionality
- **Estimated Time:** 2 hours

**Implementation:**
```typescript
// Add USE category filter
<Select
  label="Property Type"
  options={[
    { value: 'Residential', label: 'Residential' },
    { value: 'Commercial', label: 'Commercial' },
    { value: 'Industrial', label: 'Industrial' },
    { value: 'Agricultural', label: 'Agricultural' },
    // etc...
  ]}
  onChange={handleUseFilter}
/>
```

#### 7. **Property Search API** (MEDIUM)
- **File:** `apps/web/api/properties/search.ts`
- **Current:** Searches by various criteria
- **Missing:** USE-based filtering
- **Impact:** MEDIUM - Backend support
- **Estimated Time:** 1 hour

**Implementation:**
```typescript
// Add USE filter support
if (propertyUse) {
  query = query.eq('property_use', propertyUse);
}

if (useCategory) {
  // Map category to property_use codes
  const useCodes = PROPERTY_TYPE_TO_DB_VALUES[useCategory];
  query = query.in('property_use', useCodes);
}
```

#### 8. **Property Comparison** (MEDIUM)
- **File:** Various comparison components
- **Current:** Compare property values/features
- **Missing:** USE comparison
- **Impact:** MEDIUM - Decision making
- **Estimated Time:** 1 hour

---

### 🔮 Phase 4: LOW PRIORITY (Future)

#### 9. **Map View** (LOW)
- **Current:** Properties on map
- **Missing:** Color-coded by USE
- **Impact:** LOW - Visual enhancement
- **Estimated Time:** 3 hours

#### 10. **Analytics Dashboard** (LOW)
- **Current:** Property statistics
- **Missing:** USE distribution charts
- **Impact:** LOW - Insights
- **Estimated Time:** 4 hours

#### 11. **Investment Calculator** (LOW)
- **Current:** ROI calculations
- **Missing:** USE-specific metrics
- **Impact:** LOW - Advanced features
- **Estimated Time:** 2 hours

#### 12. **Property Rankings** (LOW)
- **File:** `apps/web/src/lib/propertyRanking.ts`
- **Current:** Ranks properties
- **Missing:** USE-based scoring
- **Impact:** LOW - Refinement
- **Estimated Time:** 2 hours

#### 13. **Export/Reports** (LOW)
- **Current:** Export property data
- **Missing:** USE data in exports
- **Impact:** LOW - Data export
- **Estimated Time:** 1 hour

---

## 🗄️ DATABASE VERIFICATION

### Current Schema Check

```sql
-- Verify property_use column exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'florida_parcels'
  AND column_name IN ('property_use', 'land_use_code', 'property_use_desc');

-- Check data completeness
SELECT
  COUNT(*) as total_properties,
  COUNT(property_use) as has_property_use,
  COUNT(land_use_code) as has_land_use_code,
  COUNT(DISTINCT property_use) as distinct_uses
FROM florida_parcels;

-- Find properties missing USE
SELECT parcel_id, phy_addr1, phy_city
FROM florida_parcels
WHERE property_use IS NULL
LIMIT 100;
```

### Recommended Indexes

```sql
-- Add if not exists
CREATE INDEX IF NOT EXISTS idx_property_use
ON florida_parcels(property_use);

CREATE INDEX IF NOT EXISTS idx_land_use_code
ON florida_parcels(land_use_code);

CREATE INDEX IF NOT EXISTS idx_county_property_use
ON florida_parcels(county, property_use);

CREATE INDEX IF NOT EXISTS idx_use_value
ON florida_parcels(property_use, just_value);
```

### Foreign Key Relationships

```sql
-- Verify relationships exist
SELECT
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('florida_parcels', 'property_sales_history', 'tax_certificates');
```

---

## 📊 IMPLEMENTATION PRIORITY MATRIX

| Component | Impact | Effort | Priority | Status |
|-----------|--------|--------|----------|--------|
| MiniPropertyCard | HIGH | Low | 🔥 1 | ✅ COMPLETE |
| Property Detail Header | HIGH | Low | 🔥 2 | ✅ COMPLETE |
| VirtualizedPropertyList | HIGH | Medium | 🔥 3 | ✅ COMPLETE |
| CorePropertyTab | HIGH | Medium | 🔥 4 | ✅ COMPLETE |
| OverviewTab | MEDIUM | Low | ⚠️ 5 | ⏳ TODO |
| Advanced Filters | MEDIUM | High | ⚠️ 6 | ⏳ TODO |
| Search API | MEDIUM | Medium | ⚠️ 7 | ⏳ TODO |
| Property Comparison | MEDIUM | Medium | ⚠️ 8 | ⏳ TODO |
| Map View | LOW | High | 🔮 9 | ⏳ TODO |
| Analytics Dashboard | LOW | High | 🔮 10 | ⏳ TODO |

**Phase 2 Status:** ✅ 100% COMPLETE (4/4 HIGH PRIORITY components done)
**Updated:** October 24, 2025

---

## 🎯 SPRINT PLANNING

### Sprint 1: Critical Display (Est. 3 hours)
**Goal:** Show USE on all main property displays

- [ ] MiniPropertyCard - Add USE badge (30 min)
- [ ] Property Detail Header - Add USE section (30 min)
- [ ] VirtualizedPropertyList - Add USE column (45 min)
- [ ] CorePropertyTab - Add classification section (45 min)
- [ ] Testing & Bug fixes (30 min)

### Sprint 2: Filtering & Search (Est. 4 hours)
**Goal:** Enable USE-based filtering and search

- [ ] Advanced Filters - Add USE category filter (2 hours)
- [ ] Search API - Support USE queries (1 hour)
- [ ] OverviewTab - Add USE summary (30 min)
- [ ] Testing & Integration (30 min)

### Sprint 3: Enhancement & Polish (Est. 4 hours)
**Goal:** Improve USE-related features

- [ ] Property Comparison - USE comparison (1 hour)
- [ ] Property Rankings - USE-based scoring (2 hours)
- [ ] Export - Include USE data (1 hour)

### Sprint 4: Advanced Features (Est. 8 hours)
**Goal:** Advanced USE visualizations

- [ ] Map View - Color by USE (3 hours)
- [ ] Analytics - USE distribution (4 hours)
- [ ] Investment Calculator - USE metrics (1 hour)

---

## 🧪 TESTING CHECKLIST

### For Each Component Updated

- [ ] USE displays correctly
- [ ] Icon matches property type
- [ ] Description is human-readable (not codes)
- [ ] Handles NULL property_use gracefully
- [ ] Performance is acceptable
- [ ] Responsive design maintained
- [ ] Accessibility (screen readers work)
- [ ] No console errors
- [ ] Mapping functions work correctly
- [ ] Fallbacks work for unknown codes

### Integration Testing

- [ ] Search by USE returns correct results
- [ ] Filter by USE category works
- [ ] USE display consistent across all views
- [ ] USE data exports correctly
- [ ] Analytics show USE distribution
- [ ] Map colors match USE categories

---

## 📝 CODE PATTERNS TO FOLLOW

### Standard USE Implementation Pattern

```typescript
// 1. Import mapping functions
import {
  getDorCodeFromPropertyUse,
  getPropertyUseDescription,
  getPropertyCategory
} from '@/lib/propertyUseToDorCode';
import { getPropertyIcon, getPropertyIconColor } from '@/lib/dorUseCodes';

// 2. Convert property_use to usable formats
const dorCode = getDorCodeFromPropertyUse(property.property_use);
const useDescription = getPropertyUseDescription(property.property_use);
const useCategory = getPropertyCategory(property.property_use);

// 3. Get icon components
const IconComponent = getPropertyIcon(dorCode);
const iconColorClass = getPropertyIconColor(dorCode);

// 4. Display in UI
<div className="property-use-display">
  <IconComponent className={`w-4 h-4 ${iconColorClass}`} />
  <span className="text-sm font-medium text-blue-600">
    {useDescription}
  </span>
</div>
```

### API Query Pattern

```typescript
// Include property_use in SELECT
const { data } = await supabase
  .from('florida_parcels')
  .select('parcel_id, phy_addr1, property_use, land_use_code, ...')
  .eq('county', 'BROWARD');

// Filter by USE if provided
if (useFilter) {
  query = query.eq('property_use', useFilter);
}

// Filter by category
if (categoryFilter) {
  const useCodes = getCategoryUseCodes(categoryFilter);
  query = query.in('property_use', useCodes);
}
```

---

## 🚨 COMMON PITFALLS TO AVOID

### ❌ DON'T: Use raw property_use for icons
```typescript
// WRONG - "SFR" doesn't match DOR code system
<PropertyIcon type={property.property_use} />
```

### ✅ DO: Convert to DOR code first
```typescript
// CORRECT
const dorCode = getDorCodeFromPropertyUse(property.property_use);
<PropertyIcon type={dorCode} />
```

### ❌ DON'T: Display raw codes to users
```typescript
// WRONG - Shows "SFR" or "MF_10PLUS"
<span>{property.property_use}</span>
```

### ✅ DO: Show human-readable descriptions
```typescript
// CORRECT - Shows "Single Family" or "Apartment Complex"
<span>{getPropertyUseDescription(property.property_use)}</span>
```

### ❌ DON'T: Forget NULL handling
```typescript
// WRONG - Will crash if property_use is NULL
const icon = getPropertyIcon(property.property_use.toString());
```

### ✅ DO: Always handle missing data
```typescript
// CORRECT - Safe handling
const icon = getPropertyIcon(property.property_use || undefined);
```

---

## 📦 DELIVERABLES PER COMPONENT

For each component update, deliver:

1. **Code Changes**
   - Import statements added
   - USE conversion logic
   - UI display code
   - Proper error handling

2. **Testing**
   - Unit tests (if applicable)
   - Manual testing completed
   - Edge cases verified

3. **Documentation**
   - Code comments
   - Component documentation updated
   - Screenshot of new UI

4. **Performance**
   - No performance regression
   - Mapping time <50ms
   - No unnecessary re-renders

---

## 🎉 SUCCESS CRITERIA

**The website-wide USE implementation is COMPLETE when:**

1. ✅ Every property display shows USE information
2. ✅ All icons match property types correctly
3. ✅ Users can filter by USE category
4. ✅ USE descriptions are human-readable
5. ✅ No console errors related to USE mapping
6. ✅ Performance is maintained (<100ms overhead)
7. ✅ Mobile responsive
8. ✅ Accessibility compliant
9. ✅ All tests pass
10. ✅ Documentation complete

---

## 📞 SUPPORT & RESOURCES

**Mapping System:** `apps/web/src/lib/propertyUseToDorCode.ts`
**Icon System:** `apps/web/src/lib/dorUseCodes.ts`
**Database Docs:** `BROWARD_NAL_DATA_DICTIONARY.md`
**Permanent Memory:** `.memory/PROPERTY_USE_SYSTEM_PERMANENT.md`
**Audit Report:** `PROPERTY_USE_COMPLETE_AUDIT_REPORT.md`

---

**Last Updated:** October 24, 2025
**Status:** 🔥 ACTIVE IMPLEMENTATION
**Next Review:** After Sprint 1 completion
