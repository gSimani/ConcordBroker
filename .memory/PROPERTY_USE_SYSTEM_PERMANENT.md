# PROPERTY USE SYSTEM - PERMANENT MEMORY
**CRITICAL SYSTEM COMPONENT - READ THIS IN EVERY SESSION**
**Last Updated:** October 24, 2025

---

## 🎯 CORE PRINCIPLE

**EVERY property in ConcordBroker MUST have a USE and SUBUSE.**

This is not optional - it's fundamental to:
- Property categorization
- Search filtering
- Icon display
- Market analysis
- Investment analysis
- User experience

---

## 📊 DATABASE SCHEMA (Supabase)

### Primary Table: `florida_parcels`

**Property Classification Columns:**
```sql
florida_parcels (
  -- PRIMARY USE FIELDS (CRITICAL)
  property_use VARCHAR(50),          -- TEXT code: "SFR", "MF_10PLUS", "COM", etc.
  property_use_desc TEXT,            -- Human-readable: "Single Family Residential"
  land_use_code VARCHAR(10),         -- 2-digit PA code: "00", "02", "11"

  -- DERIVED/COMPUTED FIELDS
  dor_uc VARCHAR(10),                -- ❌ DOES NOT EXIST (removed during import)

  -- OTHER IMPORTANT FIELDS
  parcel_id VARCHAR(30) PRIMARY KEY,
  county VARCHAR(50),
  year INTEGER,
  phy_addr1 VARCHAR(255),
  owner_name VARCHAR(255),
  just_value DECIMAL,
  ...
)
```

**CRITICAL FACTS:**
1. ❌ **DOR_UC column DOES NOT EXIST** in Supabase (though it exists in source NAL CSV files)
2. ✅ **property_use contains TEXT codes** ("SFR", "MF_10PLUS"), NOT numeric codes
3. ✅ **land_use_code contains 2-digit PA codes** ("00", "02", "11")
4. ⚠️ **property_use_desc is currently NULL** (populated by application layer)

---

## 🔄 DATA FLOW: Source → Database → Application

### Source Files (Florida DOR)
```
NAL CSV Files (from Florida Department of Revenue)
├── DOR_UC: "082"        ← 3-digit Department of Revenue Use Code
└── PA_UC:  "00"         ← 2-digit Property Appraiser Use Code
```

### Database (Supabase)
```
florida_parcels table
├── property_use: "SFR"         ← Transformed from DOR_UC during import
└── land_use_code: "00"         ← Direct from PA_UC
```

### Application Layer
```
UI Components
├── DOR Code: "0100"             ← Converted from "SFR" via mapping
├── Description: "Single Family" ← Generated from "SFR" via mapping
└── Icon: 🏠 Home                ← Selected based on DOR code "0100"
```

---

## 🗺️ MAPPING SYSTEM (PERMANENT)

**Location:** `apps/web/src/lib/propertyUseToDorCode.ts`

**Purpose:** Converts database TEXT codes → DOR codes → Icons & Descriptions

### Key Functions

```typescript
// Convert text code to DOR code
getDorCodeFromPropertyUse("SFR") → "0100"
getDorCodeFromPropertyUse("MF_10PLUS") → "0800"
getDorCodeFromPropertyUse("COM") → "1100"

// Get human-readable description
getPropertyUseDescription("SFR") → "Single Family"
getPropertyUseDescription("MF_10PLUS") → "Apartment Complex"
getPropertyUseDescription("COM") → "Commercial"

// Get category for filtering
getPropertyCategory("SFR") → "Residential"
getPropertyCategory("COM") → "Commercial"
getPropertyCategory("IND") → "Industrial"
```

### Complete Mapping Table

| property_use | land_use_code | DOR Code | Description | Icon | Category |
|--------------|---------------|----------|-------------|------|----------|
| **Residential** |
| SFR | 00 | 0100 | Single Family | 🏠 Home | Residential |
| CONDO | 00 | 0104 | Condominium | 🏢 Building2 | Residential |
| MOBILE | 00 | 0106 | Mobile Home | 🏠 Home | Residential |
| MF_2-9 | 02 | 0200 | Multi-Family | 🏢 Building2 | Residential |
| MF_10PLUS | 02 | 0800 | Apartment Complex | 🏢 Building2 | Residential |
| TIMESHARE | 00 | 0105 | Timeshare | 🏨 Hotel | Residential |
| **Vacant** |
| VAC_RES | 10 | 0000 | Vacant Residential | 🏗️ Wrench | Vacant |
| VAC | 90 | 9000 | Vacant Land | 🏗️ Wrench | Vacant |
| **Commercial** |
| COM | 11 | 1100 | Commercial | 🏪 Store | Commercial |
| STORE | 11 | 1100 | Retail Store | 🏪 Store | Commercial |
| OFFICE | 17 | 1700 | Office | 🏛️ Building | Commercial |
| REST | 21 | 2100 | Restaurant | 🍴 Utensils | Commercial |
| BANK | 23 | 2300 | Bank | 💵 Banknote | Commercial |
| HOTEL | 39 | 3900 | Hotel | 🏨 Hotel | Commercial |
| MALL | 14 | 1400 | Shopping Center | 🏪 Store | Commercial |
| PARKING | 10 | 1000 | Parking | 🏗️ Wrench | Commercial |
| **Industrial** |
| IND | 41 | 4100 | Industrial | 🏭 Factory | Industrial |
| FACTORY | 41 | 4100 | Factory | 🏭 Factory | Industrial |
| WAREHOUSE | 48 | 4800 | Warehouse | 🚚 Truck | Industrial |
| **Agricultural** |
| AGR | 60 | 6000 | Agricultural | 🌲 TreePine | Agricultural |
| FARM | 60 | 6000 | Farm | 🌲 TreePine | Agricultural |
| GROVE | 61 | 6100 | Grove | 🌲 TreePine | Agricultural |
| RANCH | 62 | 6200 | Ranch | 🌲 TreePine | Agricultural |
| **Institutional** |
| REL | 71 | 7100 | Religious | ⛪ Church | Institutional |
| CHURCH | 71 | 7100 | Church | ⛪ Church | Institutional |
| EDU | 72 | 7200 | Educational | 🎓 GraduationCap | Institutional |
| SCHOOL | 72 | 7200 | School | 🎓 GraduationCap | Institutional |
| HOSP | 73 | 7300 | Hospital | ✝️ Cross | Institutional |
| **Governmental** |
| GOV | 86 | 8600 | Government | 🏛️ Landmark | Governmental |
| MIL | 87 | 8700 | Military | 🏛️ Landmark | Governmental |
| PARK | 82 | 8200 | Park | 🌲 TreePine | Governmental |
| **Special** |
| UTIL | 91 | 9100 | Utility | ⚡ Zap | Special |
| CEMETERY | 94 | 9400 | Cemetery | 🏛️ Landmark | Special |

**Coverage:** 60+ property_use codes mapped

---

## 🔗 TABLE RELATIONSHIPS (Supabase)

### Core Tables with USE Data

```
florida_parcels (PRIMARY)
├── parcel_id (PK)
├── property_use ← MAIN USE FIELD
├── land_use_code
└── property_use_desc

property_sales_history
├── parcel_id (FK → florida_parcels.parcel_id)
├── dor_use_code (legacy, 3-digit codes)
└── sale_date

tax_certificates
├── parcel_id (FK → florida_parcels.parcel_id)
├── property_use_code
└── property_use_description

florida_entities (for Sunbiz matching)
├── entity_name
└── Related to owner_name in florida_parcels

sunbiz_corporate (for Sunbiz matching)
├── entity_name
└── Related to owner_name in florida_parcels
```

### Recommended Indexes

```sql
-- For fast USE filtering
CREATE INDEX idx_property_use ON florida_parcels(property_use);
CREATE INDEX idx_land_use_code ON florida_parcels(land_use_code);

-- For combined filtering
CREATE INDEX idx_county_use ON florida_parcels(county, property_use);

-- For autocomplete
CREATE INDEX idx_address_use ON florida_parcels(phy_addr1, property_use);
```

---

## 📍 WHERE USE/SUBUSE MUST BE DISPLAYED

### 1. ✅ AUTOCOMPLETE (FIXED)
**Location:** `apps/web/src/components/OptimizedSearchBar.tsx`
**Status:** ✅ Implemented
**Display:** Shows USE description below address

### 2. ⚠️ PROPERTY CARDS (NEEDS UPDATE)
**Location:** `apps/web/src/components/property/MiniPropertyCard.tsx`
**Status:** ⚠️ Needs USE display
**Required:** Show icon + USE label on each card

### 3. ⚠️ PROPERTY DETAIL PAGE (NEEDS UPDATE)
**Location:** `apps/web/src/pages/properties/[...slug].tsx`
**Status:** ⚠️ Needs prominent USE display
**Required:** Show USE/SUBUSE in property header

### 4. ⚠️ CORE PROPERTY TAB (NEEDS UPDATE)
**Location:** `apps/web/src/components/property/tabs/CorePropertyTab.tsx`
**Status:** ⚠️ Needs USE section
**Required:** Dedicated section for USE classification

### 5. ⚠️ SEARCH FILTERS (NEEDS UPDATE)
**Location:** Various filter components
**Status:** ⚠️ Needs USE-based filtering
**Required:** Filter by USE category (Residential, Commercial, etc.)

### 6. ⚠️ PROPERTY LIST VIEW (NEEDS UPDATE)
**Location:** `apps/web/src/components/property/VirtualizedPropertyList.tsx`
**Status:** ⚠️ Needs USE column
**Required:** Show USE in list view

### 7. ⚠️ OVERVIEW TAB (NEEDS UPDATE)
**Location:** `apps/web/src/components/property/tabs/OverviewTab.tsx`
**Status:** ⚠️ Needs USE summary
**Required:** Display USE in property overview

### 8. ⚠️ MAP VIEW (FUTURE)
**Status:** 🔮 Future enhancement
**Required:** Color-code map markers by USE

---

## 🎯 IMPLEMENTATION CHECKLIST

### Phase 1: Core Display (HIGH PRIORITY)
- [X] Autocomplete - Show USE descriptions
- [ ] MiniPropertyCard - Add USE badge/label
- [ ] Property Detail Header - Prominent USE display
- [ ] CorePropertyTab - USE classification section
- [ ] VirtualizedPropertyList - USE column

### Phase 2: Filtering & Search (HIGH PRIORITY)
- [ ] Advanced Filters - USE category filter
- [ ] Quick Filters - USE type buttons
- [ ] Search API - Support USE-based queries
- [ ] URL Parameters - USE filter support

### Phase 3: Analytics & Insights (MEDIUM PRIORITY)
- [ ] Property Ranking - Consider USE in scoring
- [ ] Market Analysis - Group by USE
- [ ] Investment Calculator - USE-specific metrics
- [ ] Comparable Properties - Filter by USE

### Phase 4: Visualization (LOW PRIORITY)
- [ ] Map View - Color by USE
- [ ] Charts - Distribution by USE
- [ ] Reports - USE breakdown
- [ ] Export - Include USE data

---

## 🔧 HOW TO ADD USE DISPLAY TO A COMPONENT

### Example: Add USE to MiniPropertyCard

```typescript
// 1. Import mapping functions
import { getDorCodeFromPropertyUse, getPropertyUseDescription } from '@/lib/propertyUseToDorCode';
import { getPropertyIcon, getPropertyIconColor } from '@/lib/dorUseCodes';

// 2. Convert property_use to DOR code
const dorCode = getDorCodeFromPropertyUse(data.property_use);
const useDescription = getPropertyUseDescription(data.property_use);

// 3. Get icon
const IconComponent = getPropertyIcon(dorCode);
const iconColor = getPropertyIconColor(dorCode);

// 4. Display in JSX
<div className="flex items-center gap-2">
  <IconComponent className={`w-4 h-4 ${iconColor}`} />
  <span className="text-xs font-medium text-blue-600">
    {useDescription}
  </span>
</div>
```

---

## 🚨 CRITICAL RULES

### Rule 1: ALWAYS Use the Mapping System
❌ **NEVER** use `property_use` directly for icons
✅ **ALWAYS** convert via `getDorCodeFromPropertyUse()`

```typescript
// ❌ WRONG
<Icon property_type={data.property_use} />  // "SFR" doesn't match any DOR code

// ✅ CORRECT
const dorCode = getDorCodeFromPropertyUse(data.property_use);
<Icon property_type={dorCode} />  // "0100" matches DOR system
```

### Rule 2: Display Human-Readable Labels
❌ **NEVER** show raw codes to users
✅ **ALWAYS** show descriptions

```typescript
// ❌ WRONG
<span>{data.property_use}</span>  // Shows "SFR"

// ✅ CORRECT
<span>{getPropertyUseDescription(data.property_use)}</span>  // Shows "Single Family"
```

### Rule 3: Maintain Consistency
**All components MUST use:**
- Same mapping file: `propertyUseToDorCode.ts`
- Same icon system: `dorUseCodes.ts`
- Same descriptions
- Same color scheme

### Rule 4: Handle Missing Data
```typescript
// Always provide fallback
const useDescription = getPropertyUseDescription(data.property_use) || 'Property';
const dorCode = getDorCodeFromPropertyUse(data.property_use) || '0100';
```

---

## 📚 REFERENCE DOCUMENTATION

### Florida DOR Use Codes
**Source:** https://floridarevenue.com/property/dataportal/
**File:** 2024 NAL/SDF/NAP User Guide
**Contains:** 100 DOR use codes (000-099)

### Local Documentation
- `BROWARD_NAL_DATA_DICTIONARY.md` - NAL file structure
- `PROPERTY_USE_COMPLETE_AUDIT_REPORT.md` - Full technical analysis
- `PROPERTY_USE_FIX_COMPLETE.md` - Implementation guide
- `apps/web/src/lib/dorUseCodes.ts` - Icon mapping system
- `apps/web/src/lib/propertyUseToDorCode.ts` - USE mapping system

---

## 🔍 DEBUGGING USE ISSUES

### Issue: Property shows wrong icon
**Solution:**
1. Check what `property_use` value is in database
2. Verify mapping exists in `PROPERTY_USE_TO_DOR_CODE`
3. Check if DOR code maps to icon in `dorUseCodes.ts`
4. Add missing mapping if needed

### Issue: USE description not showing
**Solution:**
1. Verify component imports `getPropertyUseDescription`
2. Check if `property_use` field is in query
3. Verify component is calling the function
4. Check if description is in JSX

### Issue: New property type not recognized
**Solution:**
1. Add to `PROPERTY_USE_TO_DOR_CODE` mapping
2. Add description to `getPropertyUseDescription`
3. Ensure DOR code exists in icon system
4. Test with sample data

---

## 💾 DATA QUALITY CHECKS

### Required Queries to Run Regularly

```sql
-- Check for NULL property_use
SELECT COUNT(*) FROM florida_parcels
WHERE property_use IS NULL;

-- Get distinct property_use values
SELECT DISTINCT property_use, COUNT(*) as count
FROM florida_parcels
GROUP BY property_use
ORDER BY count DESC;

-- Find unmapped codes
SELECT DISTINCT property_use
FROM florida_parcels
WHERE property_use NOT IN (
  'SFR', 'CONDO', 'MOBILE', 'MF_2-9', 'MF_10PLUS',
  'COM', 'STORE', 'OFFICE', 'REST', 'HOTEL',
  'IND', 'WAREHOUSE', 'AGR', 'GOV', 'VAC', 'VAC_RES'
  -- etc...
);
```

---

## 🎯 SUCCESS CRITERIA

**A component properly implements USE if:**
1. ✅ Shows correct icon based on property type
2. ✅ Displays human-readable USE description
3. ✅ Uses mapping functions (not raw codes)
4. ✅ Handles missing data gracefully
5. ✅ Maintains consistent styling
6. ✅ Performs well (<50ms mapping time)

---

## 📝 FUTURE ENHANCEMENTS

### Short Term
- [ ] Add SUBUSE display (finer classification)
- [ ] Add land_use_code display
- [ ] Create USE filter in Advanced Filters
- [ ] Add USE-based sorting

### Medium Term
- [ ] Import DOR_UC from source files
- [ ] Populate property_use_desc in database
- [ ] Create USE analytics dashboard
- [ ] Add USE-based investment scoring

### Long Term
- [ ] Machine learning USE classification
- [ ] Historical USE change tracking
- [ ] USE-based market predictions
- [ ] Automated USE verification

---

## 🚀 QUICK START FOR NEW DEVELOPERS

**When adding USE to a component:**

1. **Import the functions:**
```typescript
import { getDorCodeFromPropertyUse, getPropertyUseDescription } from '@/lib/propertyUseToDorCode';
```

2. **Convert the data:**
```typescript
const dorCode = getDorCodeFromPropertyUse(property.property_use);
const useDesc = getPropertyUseDescription(property.property_use);
```

3. **Display it:**
```typescript
<span>{useDesc}</span>  // e.g., "Single Family"
```

**That's it!** The system handles all the complex mapping.

---

**REMEMBER: Property USE/SUBUSE is CRITICAL to the entire ConcordBroker system.**
**Always ensure properties have proper USE classification.**
**Always use the mapping system - never display raw codes.**

---

**Last Updated:** October 24, 2025
**Maintained By:** Development Team
**Status:** ✅ ACTIVE - USE IN ALL SESSIONS
