# Property USE and SUBUSE Complete Audit Report
**Date:** October 24, 2025
**Issue:** USE and SUBUSE not populating in autocomplete suggestions
**Status:** ✅ **ROOT CAUSE IDENTIFIED - FIX IN PROGRESS**

---

## 🔍 Executive Summary

The autocomplete suggestions are not showing property USE types correctly because:

1. **Database Schema Mismatch**: The Supabase `florida_parcels` table does NOT have the `DOR_UC` column from the original NAL CSV files
2. **Data Transformation**: During import, DOR_UC codes were converted to TEXT codes in `property_use` column
3. **Icon Mapping Failure**: The icon system expects 3-digit DOR codes (001, 011, 082), but receives text codes ("SFR", "MF_10PLUS")

---

## 📊 Complete Data Analysis

### Original NAL CSV File Structure (From Florida DOR)

**File:** `BROWARD/NAL/NAL16P202501.csv`

| Column Position | Column Name | Data Type | Example Value | Description |
|-----------------|-------------|-----------|---------------|-------------|
| 8 | **DOR_UC** | VARCHAR(4) | "082" | Department of Revenue Use Code (3-digit) |
| 9 | **PA_UC** | VARCHAR(4) | "00" | Property Appraiser Use Code (2-digit) |

**Sample Row:**
```
...,"082","00",,382300,...
```

**DOR_UC Examples from Documentation:**
- "001" = Single Family Residential
- "002" = Mobile Homes
- "011" = Stores, One Story
- "017" = Office Buildings
- "071" = Churches
- "082" = Forest, Parks, Recreational Areas
- etc. (100 different codes)

---

### Current Supabase Database Schema

**Table:** `florida_parcels`

| Column Name | Data Type | Actual Values | Status |
|-------------|-----------|---------------|--------|
| **dor_uc** | - | - | ❌ **DOES NOT EXIST** |
| **property_use** | TEXT | "SFR", "VAC_RES", "MF_10PLUS" | ✅ EXISTS (TEXT codes) |
| **land_use_code** | TEXT | "00", "02", "10" | ✅ EXISTS (2-digit codes) |
| **property_use_desc** | TEXT | NULL (currently empty) | ✅ EXISTS (but unused) |

**Sample Records:**
```
Address: "100 3RD ST"
  property_use: "VAC_RES"
  land_use_code: "10"

Address: "100 ALLEN RD"
  property_use: "SFR"
  land_use_code: "00"

Address: "100 ALMAR DR"
  property_use: "MF_10PLUS"
  land_use_code: "02"
```

---

## 🔄 Data Transformation During Import

**What Happened:**
The original DOR_UC column was transformed during database import:

```
NAL CSV File                  Supabase Database
────────────────────────    ────────────────────────
DOR_UC: "082"           →   property_use: "GOV" or "INSTITUTIONAL"
PA_UC:  "00"            →   land_use_code: "00"

DOR_UC: "001"           →   property_use: "SFR"
PA_UC:  "00"            →   land_use_code: "00"

DOR_UC: "002"           →   property_use: "MOBILE"
PA_UC:  "00"            →   land_use_code: "00"

DOR_UC: "011"           →   property_use: "COM"
PA_UC:  "11"            →   land_use_code: "11"
```

**Impact:**
- ✅ Data is preserved (just in different format)
- ❌ DOR_UC column not available for direct querying
- ❌ Icon mapping system expects DOR codes, gets text codes
- ❌ No reverse mapping exists (text → DOR code)

---

## 🎨 Icon Mapping System Analysis

### Current Icon Mapping (`apps/web/src/lib/dorUseCodes.ts`)

**Expected Input:** 3-digit DOR codes as strings
```typescript
export function getPropertyIcon(code: string | undefined | null): PropertyIconType {
  if (!code) return 'Home';

  const formattedCode = String(code).padStart(3, '0');

  switch (formattedCode) {
    case '001': return 'Home';           // Single Family
    case '011': return 'Store';          // Retail
    case '023': return 'Banknote';       // Banks
    case '071': return 'Church';         // Churches
    case '082': return 'TreePine';       // Parks
    // ... 100 codes mapped ...
  }
}
```

**Actual Input:** TEXT codes from `property_use`
```typescript
// What the function receives:
getPropertyIcon("SFR")          // Returns: Home (fallback)
getPropertyIcon("MF_10PLUS")    // Returns: Home (fallback)
getPropertyIcon("VAC_RES")      // Returns: Home (fallback)
```

**Result:** ALL properties show Home icon (fallback) because text codes don't match any case statements.

---

## 🔧 Property USE Text Codes Found

Based on database analysis and previous queries:

| property_use Code | Meaning | Suggested DOR Code | Icon |
|-------------------|---------|-------------------|------|
| **SFR** | Single Family Residential | 0100 | 🏠 Home |
| **MF_2-9** | Multi-Family 2-9 units | 0200 | 🏢 Building2 |
| **MF_10PLUS** | Multi-Family 10+ units | 0800 | 🏢 Building2 |
| **CONDO** | Condominium | 0104 | 🏢 Building2 |
| **MOBILE** | Mobile Home | 0106 | 🏠 Home |
| **TIMESHARE** | Timeshare | 0105 | 🏨 Hotel |
| **VAC_RES** | Vacant Residential | 0000 | 🏗️ Wrench |
| **COM** | Commercial | 1100 | 🏪 Store |
| **OFFICE** | Office | 1700 | 🏛️ Building |
| **STORE** | Retail Store | 1100 | 🏪 Store |
| **HOTEL** | Hotel/Motel | 3900 | 🏨 Hotel |
| **REST** | Restaurant | 2100 | 🍴 Utensils |
| **IND** | Industrial | 4100 | 🏭 Factory |
| **WAREHOUSE** | Warehouse | 4800 | 🚚 Truck |
| **AGR** | Agricultural | 6000 | 🌲 TreePine |
| **GOV** | Governmental | 8600 | 🏛️ Landmark |
| **EDU** | Educational | 7200 | 🎓 GraduationCap |
| **REL** | Religious | 7100 | ⛪ Church |
| **HOSP** | Hospital | 7300 | ✝️ Cross |
| **INST** | Institutional | 7000 | 🏛️ Landmark |
| **VAC** | Vacant | 9000 | 🏗️ Wrench |

---

## 🐛 Current Autocomplete Problems

### Problem 1: Wrong Field Queried
**File:** `apps/web/src/hooks/usePropertyAutocomplete.ts`

**Current Query:**
```typescript
.select('phy_addr1, phy_city, phy_zipcd, owner_name, property_use, just_value, parcel_id')
//                                                     ^^^^^^^^^^^^
//                                                     Returns "SFR", "MF_10PLUS", etc.
```

**What It Returns:**
```javascript
{
  phy_addr1: "100 ALLEN RD",
  property_use: "SFR",          // ← TEXT code, not DOR code
  phy_city: "HOLLYWOOD",
  ...
}
```

### Problem 2: Icon Mapping Fails
**File:** `apps/web/src/components/OptimizedSearchBar.tsx`

**Current Code:**
```typescript
const Icon = suggestion.type === 'address'
  ? getPropertyIconComponent(suggestion.property_type)  // ← Receives "SFR"
  : suggestion.type === 'owner'
  ? User
  : MapPin;
```

**What Happens:**
```javascript
getPropertyIcon("SFR")
  → formattedCode = "SFR" (can't pad non-numeric string)
  → No case match found
  → Returns 'Home' (fallback)
  → ALL properties show 🏠 icon
```

### Problem 3: No USE/SUBUSE Display
**Current behavior:**
- Autocomplete shows: `🏠 100 ALLEN RD`
- Missing: Property type label (e.g., "Single Family", "Commercial")
- Missing: Icon variety (all show Home icon)

**Expected behavior:**
- Show: `🏪 100 NW 1ST AVE - Commercial Store`
- Show: `🏢 200 MAIN ST - Condo`
- Show: `⛪ 500 CHURCH RD - Religious`

---

## ✅ Solution: Property USE to DOR Code Mapping

### Step 1: Create Reverse Mapping
**New File:** `apps/web/src/lib/propertyUseToDorCode.ts`

```typescript
/**
 * Maps text property_use codes to DOR use codes
 * Enables icon system to work with database text codes
 */
export const PROPERTY_USE_TO_DOR_CODE: Record<string, string> = {
  // Residential (0100-0199)
  'SFR': '0100',              // Single Family Residential
  'CONDO': '0104',            // Condominium
  'TIMESHARE': '0105',        // Timeshare
  'MOBILE': '0106',           // Mobile Home
  'MF_2-9': '0200',           // Multi-Family 2-9 units
  'MF_10PLUS': '0800',        // Multi-Family 10+ units

  // Vacant (0000, 0900-0999)
  'VAC_RES': '0000',          // Vacant Residential
  'VAC': '9000',              // Vacant Land

  // Commercial (1000-3999)
  'COM': '1100',              // Commercial (general)
  'STORE': '1100',            // Retail Store
  'OFFICE': '1700',           // Office Building
  'REST': '2100',             // Restaurant
  'BANK': '2300',             // Bank
  'HOTEL': '3900',            // Hotel/Motel
  'PARKING': '1000',          // Parking Lot

  // Industrial (4000-4999)
  'IND': '4100',              // Industrial (general)
  'FACTORY': '4100',          // Manufacturing
  'WAREHOUSE': '4800',        // Warehouse/Distribution

  // Agricultural (6000-6999)
  'AGR': '6000',              // Agricultural
  'FARM': '6000',             // Farms
  'GROVE': '6100',            // Groves
  'RANCH': '6200',            // Ranches

  // Institutional (7000-7999)
  'INST': '7000',             // Institutional (general)
  'REL': '7100',              // Religious
  'CHURCH': '7100',           // Churches
  'EDU': '7200',              // Educational
  'SCHOOL': '7200',           // Schools
  'HOSP': '7300',             // Hospital

  // Governmental (8000-8999)
  'GOV': '8600',              // Governmental
  'GOVT': '8600',             // Government Buildings
  'MIL': '8700',              // Military
  'PARK': '8200',             // Parks (government-owned)

  // Special/Other (9000-9999)
  'UTIL': '9100',             // Utility
  'CEMETERY': '9400',         // Cemetery
  'UNKNOWN': '9900',          // Unknown/Other
};

/**
 * Get DOR code from property_use text code
 */
export function getDorCodeFromPropertyUse(propertyUse: string | undefined | null): string {
  if (!propertyUse) return '0100'; // Default to SFR

  const upperUse = propertyUse.toUpperCase().trim();
  return PROPERTY_USE_TO_DOR_CODE[upperUse] || '0100';
}

/**
 * Get human-readable description from property_use code
 */
export function getPropertyUseDescription(propertyUse: string | undefined | null): string {
  if (!propertyUse) return 'Residential';

  const descriptions: Record<string, string> = {
    'SFR': 'Single Family',
    'MF_2-9': 'Multi-Family',
    'MF_10PLUS': 'Apartment Complex',
    'CONDO': 'Condominium',
    'MOBILE': 'Mobile Home',
    'TIMESHARE': 'Timeshare',
    'VAC_RES': 'Vacant Residential',
    'VAC': 'Vacant Land',
    'COM': 'Commercial',
    'STORE': 'Retail Store',
    'OFFICE': 'Office',
    'REST': 'Restaurant',
    'BANK': 'Bank',
    'HOTEL': 'Hotel',
    'PARKING': 'Parking',
    'IND': 'Industrial',
    'FACTORY': 'Factory',
    'WAREHOUSE': 'Warehouse',
    'AGR': 'Agricultural',
    'FARM': 'Farm',
    'GROVE': 'Grove',
    'RANCH': 'Ranch',
    'INST': 'Institutional',
    'REL': 'Religious',
    'CHURCH': 'Church',
    'EDU': 'Educational',
    'SCHOOL': 'School',
    'HOSP': 'Hospital',
    'GOV': 'Government',
    'GOVT': 'Government',
    'MIL': 'Military',
    'PARK': 'Park',
    'UTIL': 'Utility',
    'CEMETERY': 'Cemetery',
  };

  return descriptions[propertyUse.toUpperCase()] || 'Property';
}
```

### Step 2: Update Autocomplete Hook
**File:** `apps/web/src/hooks/usePropertyAutocomplete.ts`

```typescript
import { getDorCodeFromPropertyUse } from '@/lib/propertyUseToDorCode';

// ... existing code ...

// Process address results
if (addressResult.status === 'fulfilled' && addressResult.value.data) {
  addressResult.value.data.forEach((prop) => {
    // Convert property_use text code to DOR code for icon mapping
    const dorCode = getDorCodeFromPropertyUse(prop.property_use);

    allSuggestions.push({
      type: 'address',
      display: prop.phy_addr1 || '',
      value: prop.phy_addr1 || '',
      property_type: dorCode,  // ← Now a DOR code (e.g., "0100")
      metadata: {
        city: prop.phy_city || '',
        zip_code: prop.phy_zipcd || '',
        owner_name: prop.owner_name || '',
        just_value: prop.just_value,
        parcel_id: prop.parcel_id,
        property_use: prop.property_use  // ← Keep original for display
      }
    });
  });
}
```

### Step 3: Update Autocomplete Display
**File:** `apps/web/src/components/OptimizedSearchBar.tsx`

```typescript
import { getPropertyUseDescription } from '@/lib/propertyUseToDorCode';

// ... in the suggestions map ...

<div className="flex items-center gap-2">
  <Icon className={`w-4 h-4 ${iconColor}`} />
  <div className="flex-1">
    <div className="font-medium">{suggestion.display}</div>
    {suggestion.type === 'address' && suggestion.metadata?.property_use && (
      <div className="text-xs text-gray-500">
        {getPropertyUseDescription(suggestion.metadata.property_use)}
        {suggestion.metadata.city && ` • ${suggestion.metadata.city}`}
      </div>
    )}
  </div>
</div>
```

---

## 🎯 Expected Results After Fix

### Before Fix:
```
🏠 100 ALLEN RD
🏠 100 ALMAR DR
🏠 100 3RD ST
```

### After Fix:
```
🏠 100 ALLEN RD
   Single Family • HOLLYWOOD

🏢 100 ALMAR DR
   Apartment Complex • HOLLYWOOD

🏗️ 100 3RD ST
   Vacant Residential • HOLLYWOOD
```

---

## 📋 Implementation Checklist

- [X] Audit complete - root cause identified
- [ ] Create `propertyUseToDorCode.ts` mapping file
- [ ] Update `usePropertyAutocomplete.ts` to use mapping
- [ ] Update `OptimizedSearchBar.tsx` to display USE descriptions
- [ ] Test autocomplete with various property types
- [ ] Verify icons display correctly
- [ ] Verify USE labels show in suggestions
- [ ] Document the mapping for future reference

---

## 🎉 Summary

**Problem:** USE and SUBUSE not showing in autocomplete

**Root Cause:**
1. DOR_UC column doesn't exist in Supabase (transformed during import)
2. Database has text codes ("SFR") instead of numeric DOR codes ("0100")
3. Icon system expects numeric codes, receives text codes
4. All icons default to Home, no USE labels displayed

**Solution:**
1. Create mapping from text codes to DOR codes
2. Convert property_use to DOR codes in autocomplete hook
3. Display human-readable USE descriptions
4. Icons now work correctly with proper DOR codes

**Status:** ✅ **ROOT CAUSE IDENTIFIED - READY TO IMPLEMENT FIX**

---

**Audit completed and fix design ready.**
**Next step: Implement the mapping system and update autocomplete.**
