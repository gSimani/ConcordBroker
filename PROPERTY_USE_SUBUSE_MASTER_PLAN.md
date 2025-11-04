# Property USE/SUBUSE Master Implementation Plan

**Date**: 2025-11-01
**Status**: READY FOR EXECUTION
**Scope**: 9.1M Florida properties across 67 counties

---

## Executive Summary

This plan establishes a comprehensive property classification system with proper USE and SUBUSE categorization, fixing critical data quality issues and implementing the official Florida Department of Revenue (DOR) use code system.

## Current State Analysis

### Database Status

**florida_parcels Table** (9.1M records):
- `property_use`: INCONSISTENT (mix of numeric, padded, and text codes)
  - "4" = 897 properties (89.7%)
  - "1" = 79 properties (7.9%)
  - "001" = 10 properties (1.0%)
  - "Condo", "SFR", "004" = 6 properties (0.6%)
- `property_use_desc`: **100% NULL** (1,000/1,000 in sample)
- `standardized_property_use`: Only 3 categories
  - Multi-Family (89.8%)
  - Single Family Residential (9.0%)
  - Condominium (0.4%)

**dor_use_codes Table**:
- ✅ Table EXISTS
- ❌ NOT populated with official Florida DOR codes
- Current data shows "N/A" placeholders

### Critical Issues Identified

1. **Data Inconsistency**: Property codes mix numeric ("1", "4"), zero-padded ("001"), and text ("Condo", "SFR")
2. **Missing Descriptions**: 100% NULL in property_use_desc field
3. **Limited Classification**: Only 3 standardized categories (should have 100+)
4. **Icon System Broken**: Expects 3-digit DOR codes but receives inconsistent formats
5. **No SUBUSE System**: No granular property subcategorization exists

---

## Official Florida DOR Use Code System

Based on Rule 12D-8.008, Florida Administrative Code:

### Primary Categories (USE)

| Code Range | Category | Description |
|------------|----------|-------------|
| **00-09** | Residential | Single family, condos, mobile homes, multi-family |
| **10-19** | Commercial | Stores, offices, retail, services |
| **20-29** | Industrial | Manufacturing, warehouses, processing |
| **30-39** | Agricultural | Farms, groves, ranches, timberland |
| **40-49** | Institutional | Schools, churches, hospitals, government |
| **50-69** | Miscellaneous | Recreation, mining, subsurface rights |
| **70-89** | Special Use | Centrally assessed, commons, leasehold |
| **90-99** | Government | Federal, state, county, municipal |

### Detailed Codes (SUBUSE)

**Residential (00-09)**:
- 00 = Vacant Residential
- 01 = Single Family
- 02 = Mobile Homes
- 03 = Multi-Family (less than 10 units)
- 04 = Condominiums
- 05 = Cooperatives
- 06 = Retirement Homes
- 07 = Miscellaneous Residential
- 08 = Multi-Family (10+ units)
- 09 = Residential Common Elements

**Commercial (10-19)**:
- 10 = Vacant Commercial
- 11 = Stores (one story)
- 12 = Mixed Use (store/office)
- 13 = Department Stores
- 14 = Supermarkets
- 15 = Regional Shopping Centers
- 16 = Community Shopping Centers
- 17 = Office Buildings (one story)
- 18 = Office Buildings (multi-story)
- 19 = Professional Service Buildings

**Industrial (20-29)**:
- 20 = Vacant Industrial
- 21 = Light Manufacturing
- 22 = Heavy Manufacturing
- 23 = Lumber Yards/Sawmills
- 24 = Packing Plants
- 25 = Canneries
- 26 = Other Food Processing
- 27 = Mineral Processing
- 28 = Warehousing/Distribution
- 29 = Industrial Common Elements

**Agricultural (30-39)**:
- 30 = Vacant Agricultural
- 31 = Cropland (improved pasture)
- 32 = Timberland (commercial forests)
- 33 = Orchards/Groves (citrus)
- 34 = Specialized Agriculture
- 35 = Poultry/Bees/Tropical Fish/Rabbits
- 36 = Dairies/Feed Lots
- 37 = Ornamentals (sod farms, nurseries)
- 38 = Vacant Acreage
- 39 = Agricultural Common Elements

**Institutional (40-49, 70-79)**:
- 71 = Churches/Synagogues
- 72 = Private Schools/Colleges
- 73 = Privately Owned Hospitals
- 74 = Homes for Aged
- 75 = Orphanages/Non-Profit Service
- 76 = Mortuaries/Cemeteries/Crematories
- 80 = Cultural (museums, zoos, libraries)
- 84 = Charities/Civic/Social
- 89 = Other

**Government (90-99)**:
- 91 = Utility
- 92 = Mining Lands/Petroleum
- 93 = Subsurface Rights
- 94 = Right of Way/Easements/Wastelands
- 95 = Rivers/Lakes/Submerged Lands
- 96 = Parks/Recreation
- 97 = Outdoor Recreation/Neighborhood Parks
- 98 = Centrally Assessed

---

## Implementation Plan

### Phase 1: Populate DOR Use Codes Table (1 hour)

**Objective**: Load official Florida DOR codes into `dor_use_codes` table

**Tasks**:
1. Download official DOR code list from Florida Department of Revenue
2. Create comprehensive DOR codes JSON file with all 100+ codes
3. Populate `dor_use_codes` table with:
   - `use_code`: 2-digit code (e.g., "01", "17", "33")
   - `use_description`: Official description
   - `category`: Primary category (Residential, Commercial, etc.)
   - `subcategory`: Detailed subcategory
   - Boolean flags: `is_residential`, `is_commercial`, `is_industrial`, etc.

**Deliverable**: Fully populated `dor_use_codes` reference table

---

### Phase 2: Standardize Existing Data (2-3 hours)

**Objective**: Convert inconsistent property_use codes to standard format

**Current Issues**:
- Mixed formats: "1", "4", "001", "Condo", "SFR"
- Need: Consistent 2-digit format "01", "04", etc.

**Approach**:

```sql
-- Create mapping for current inconsistent codes
UPDATE florida_parcels
SET property_use = CASE
    -- Numeric codes (pad to 2 digits)
    WHEN property_use = '1' THEN '01'
    WHEN property_use = '4' THEN '04'
    WHEN property_use = '8' THEN '08'

    -- Already padded codes (strip to 2 digits)
    WHEN property_use LIKE '00%' THEN SUBSTRING(property_use, 1, 2)

    -- Text codes (convert to official DOR codes)
    WHEN property_use IN ('SFR', 'Single Family') THEN '01'
    WHEN property_use IN ('Condo', 'CONDO') THEN '04'
    WHEN property_use = 'MF_2-9' THEN '03'
    WHEN property_use = 'MF_10PLUS' THEN '08'
    WHEN property_use IN ('COM', 'Commercial') THEN '17'
    WHEN property_use IN ('IND', 'Industrial') THEN '21'
    WHEN property_use IN ('AGR', 'Agricultural') THEN '31'
    WHEN property_use IN ('VAC_RES', 'Vacant Residential') THEN '00'
    WHEN property_use IN ('VAC', 'Vacant') THEN '00'

    -- Fallback: use intelligent assignment based on property characteristics
    ELSE '01' -- Default to Single Family
END
WHERE year = 2025;
```

**Validation**:
- Query distinct property_use values after update
- Verify all codes match official DOR format (2 digits)
- Confirm all codes exist in `dor_use_codes` table

**Deliverable**: All 9.1M properties have standardized 2-digit DOR codes

---

### Phase 3: Populate property_use_desc (30 minutes)

**Objective**: Fill 100% NULL property_use_desc field with official descriptions

**Approach**:

```sql
-- Update property_use_desc from dor_use_codes table
UPDATE florida_parcels fp
SET property_use_desc = duc.use_description
FROM dor_use_codes duc
WHERE fp.property_use = duc.use_code
  AND fp.year = 2025
  AND (fp.property_use_desc IS NULL OR fp.property_use_desc = '');
```

**Validation**:
- Count NULL property_use_desc (should be 0)
- Sample descriptions match official DOR descriptions

**Deliverable**: All properties have human-readable use descriptions

---

### Phase 4: Enhance standardized_property_use (30 minutes)

**Objective**: Expand from 3 categories to full DOR category system

**Current Categories**: Multi-Family, Single Family Residential, Condominium
**Target Categories**: Residential, Commercial, Industrial, Agricultural, Institutional, Government, Special Use, Miscellaneous

**Approach**:

```sql
-- Update standardized_property_use based on property_use code
UPDATE florida_parcels
SET standardized_property_use = CASE
    -- Residential (00-09)
    WHEN property_use::integer BETWEEN 0 AND 9 THEN
        CASE
            WHEN property_use = '00' THEN 'Vacant Residential'
            WHEN property_use = '01' THEN 'Single Family Residential'
            WHEN property_use = '02' THEN 'Mobile Home'
            WHEN property_use = '03' THEN 'Multi-Family (2-9 units)'
            WHEN property_use = '04' THEN 'Condominium'
            WHEN property_use = '05' THEN 'Cooperative'
            WHEN property_use = '06' THEN 'Retirement Home'
            WHEN property_use = '08' THEN 'Multi-Family (10+ units)'
            WHEN property_use = '09' THEN 'Residential Common Area'
            ELSE 'Residential'
        END

    -- Commercial (10-19)
    WHEN property_use::integer BETWEEN 10 AND 19 THEN
        CASE
            WHEN property_use = '10' THEN 'Vacant Commercial'
            WHEN property_use IN ('11', '12', '13', '14') THEN 'Retail/Store'
            WHEN property_use IN ('15', '16') THEN 'Shopping Center'
            WHEN property_use IN ('17', '18', '19') THEN 'Office Building'
            ELSE 'Commercial'
        END

    -- Industrial (20-29)
    WHEN property_use::integer BETWEEN 20 AND 29 THEN
        CASE
            WHEN property_use = '20' THEN 'Vacant Industrial'
            WHEN property_use IN ('21', '22') THEN 'Manufacturing'
            WHEN property_use = '28' THEN 'Warehouse/Distribution'
            ELSE 'Industrial'
        END

    -- Agricultural (30-39)
    WHEN property_use::integer BETWEEN 30 AND 39 THEN
        CASE
            WHEN property_use = '30' THEN 'Vacant Agricultural'
            WHEN property_use = '31' THEN 'Cropland'
            WHEN property_use = '32' THEN 'Timberland'
            WHEN property_use = '33' THEN 'Orchard/Grove'
            ELSE 'Agricultural'
        END

    -- Institutional (40-49, 70-89)
    WHEN property_use::integer BETWEEN 40 AND 89 THEN
        CASE
            WHEN property_use = '71' THEN 'Religious'
            WHEN property_use = '72' THEN 'Educational'
            WHEN property_use = '73' THEN 'Hospital'
            WHEN property_use = '74' THEN 'Senior Care'
            WHEN property_use = '80' THEN 'Cultural'
            ELSE 'Institutional'
        END

    -- Government/Miscellaneous (90-99)
    WHEN property_use::integer BETWEEN 90 AND 99 THEN
        CASE
            WHEN property_use = '91' THEN 'Utility'
            WHEN property_use = '96' THEN 'Park/Recreation'
            WHEN property_use = '98' THEN 'Centrally Assessed'
            ELSE 'Government'
        END

    ELSE 'Unknown'
END
WHERE year = 2025;
```

**Deliverable**: Comprehensive standardized property use categories

---

### Phase 5: Create USE/SUBUSE Display System (2 hours)

**Objective**: Implement frontend components to display USE and SUBUSE information

**Components to Create**:

1. **USE Badge Component** (`apps/web/src/components/property/USEBadge.tsx`):
   ```typescript
   interface USEBadgeProps {
     useCode: string
     showDescription?: boolean
     size?: 'sm' | 'md' | 'lg'
   }

   // Displays: [01] Single Family
   // With color coding by category
   ```

2. **SUBUSE Display** (`apps/web/src/components/property/SUBUSEDisplay.tsx`):
   ```typescript
   // Shows detailed subcategory with icon
   // Example:
   //   USE: Residential
   //   SUBUSE: Single Family (01)
   //   Icon: House
   ```

3. **PropertyUseCard** (`apps/web/src/components/property/PropertyUseCard.tsx`):
   ```typescript
   // Summary card showing:
   // - Primary USE category with icon
   // - SUBUSE code and description
   // - Property characteristics that determine classification
   ```

4. **Update MiniPropertyCard**:
   - Add USE/SUBUSE display
   - Show category badge with proper icon
   - Include tooltip with full description

**Frontend Mapping** (`apps/web/src/lib/dorUseCodes.ts`):

```typescript
/**
 * Official Florida DOR Use Codes
 * Based on Rule 12D-8.008, FAC
 */
export const DOR_USE_CODES = {
  // Residential
  '00': { category: 'Residential', description: 'Vacant Residential', icon: 'Building', color: 'blue' },
  '01': { category: 'Residential', description: 'Single Family', icon: 'Home', color: 'blue' },
  '02': { category: 'Residential', description: 'Mobile Home', icon: 'Home', color: 'blue' },
  '03': { category: 'Residential', description: 'Multi-Family (2-9)', icon: 'Building2', color: 'blue' },
  '04': { category: 'Residential', description: 'Condominium', icon: 'Building2', color: 'blue' },
  '08': { category: 'Residential', description: 'Multi-Family (10+)', icon: 'Building', color: 'blue' },

  // Commercial
  '10': { category: 'Commercial', description: 'Vacant Commercial', icon: 'Store', color: 'green' },
  '11': { category: 'Commercial', description: 'Store (1 story)', icon: 'Store', color: 'green' },
  '17': { category: 'Commercial', description: 'Office (1 story)', icon: 'Building', color: 'green' },
  '18': { category: 'Commercial', description: 'Office (multi-story)', icon: 'Building', color: 'green' },

  // Industrial
  '20': { category: 'Industrial', description: 'Vacant Industrial', icon: 'Factory', color: 'orange' },
  '21': { category: 'Industrial', description: 'Light Manufacturing', icon: 'Factory', color: 'orange' },
  '28': { category: 'Industrial', description: 'Warehouse', icon: 'Truck', color: 'orange' },

  // Agricultural
  '30': { category: 'Agricultural', description: 'Vacant Agricultural', icon: 'TreePine', color: 'brown' },
  '31': { category: 'Agricultural', description: 'Cropland', icon: 'TreePine', color: 'brown' },
  '33': { category: 'Agricultural', description: 'Orchard/Grove', icon: 'TreePine', color: 'brown' },

  // Institutional
  '71': { category: 'Institutional', description: 'Church', icon: 'Church', color: 'purple' },
  '72': { category: 'Institutional', description: 'School', icon: 'GraduationCap', color: 'purple' },
  '73': { category: 'Institutional', description: 'Hospital', icon: 'Cross', color: 'purple' },

  // Government
  '91': { category: 'Government', description: 'Utility', icon: 'Zap', color: 'gray' },
  '96': { category: 'Government', description: 'Park', icon: 'TreePine', color: 'gray' }
}

export function getUSECategory(useCode: string): string {
  return DOR_USE_CODES[useCode]?.category || 'Unknown'
}

export function getSUBUSEDescription(useCode: string): string {
  return DOR_USE_CODES[useCode]?.description || 'Unknown'
}

export function getPropertyIcon(useCode: string): PropertyIconType {
  const icon = DOR_USE_CODES[useCode]?.icon
  return icon || 'Home'
}
```

**Deliverable**: Full frontend USE/SUBUSE display system

---

### Phase 6: Intelligence-Based Assignment (Optional - 3 hours)

**Objective**: For properties with missing or unclear codes, use AI to assign appropriate classifications

**Approach**: Use existing SQLAlchemy agent with enhanced logic:

```python
# For properties still without proper codes
def intelligent_use_code_assignment(property):
    """
    Assign DOR use code based on property characteristics
    """
    # Residential indicators
    if property.building_value > 50000 and property.building_value > property.land_value:
        if property.just_value < 500000:
            return '01'  # Single Family
        elif property.building_value > property.land_value * 2:
            return '08'  # Multi-Family 10+
        else:
            return '01'  # Single Family

    # Commercial indicators
    elif property.just_value > 500000 and property.building_value > 200000:
        return '17'  # Office

    # Industrial indicators
    elif property.building_value > 1000000 and property.land_value < 500000:
        return '21'  # Manufacturing

    # Agricultural indicators
    elif property.land_value > property.building_value * 5:
        return '31'  # Cropland

    # Vacant indicators
    elif property.land_value > 0 and (not property.building_value or property.building_value == 0):
        return '00'  # Vacant Residential

    # Default
    return '01'  # Single Family
```

**Deliverable**: 100% coverage with intelligent fallback assignment

---

## Validation & Testing

### Database Validation Queries

```sql
-- 1. Check property_use standardization
SELECT
    property_use,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM florida_parcels
WHERE year = 2025
GROUP BY property_use
ORDER BY count DESC
LIMIT 50;

-- 2. Check property_use_desc population
SELECT
    COUNT(*) as total_properties,
    COUNT(property_use_desc) as with_description,
    COUNT(*) - COUNT(property_use_desc) as null_descriptions,
    ROUND(COUNT(property_use_desc) * 100.0 / COUNT(*), 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025;

-- 3. Check standardized_property_use distribution
SELECT
    standardized_property_use,
    COUNT(*) as count,
    ROUND(AVG(just_value), 2) as avg_value
FROM florida_parcels
WHERE year = 2025
GROUP BY standardized_property_use
ORDER BY count DESC;

-- 4. Verify all codes exist in reference table
SELECT
    fp.property_use,
    COUNT(*) as properties_count,
    duc.use_description
FROM florida_parcels fp
LEFT JOIN dor_use_codes duc ON fp.property_use = duc.use_code
WHERE fp.year = 2025
GROUP BY fp.property_use, duc.use_description
ORDER BY properties_count DESC;
```

### Frontend Testing Checklist

- [ ] MiniPropertyCard displays USE category with correct icon
- [ ] MiniPropertyCard displays SUBUSE description
- [ ] Property detail page shows full USE/SUBUSE information
- [ ] Icon mapping works for all 100+ DOR codes
- [ ] Color coding matches category (blue=residential, green=commercial, etc.)
- [ ] Tooltips show full official DOR descriptions
- [ ] Filters work with new USE/SUBUSE system
- [ ] Search autocomplete shows USE category in suggestions

---

## Timeline & Resources

### Estimated Timeline

| Phase | Description | Time | Dependencies |
|-------|-------------|------|--------------|
| **Phase 1** | Populate DOR codes table | 1 hour | Florida DOR data |
| **Phase 2** | Standardize property_use | 2-3 hours | Phase 1 complete |
| **Phase 3** | Populate property_use_desc | 30 min | Phase 1, 2 complete |
| **Phase 4** | Enhance standardized_property_use | 30 min | Phase 2 complete |
| **Phase 5** | Frontend display system | 2 hours | Phase 2, 3, 4 complete |
| **Phase 6** | Intelligent assignment (optional) | 3 hours | All phases complete |
| **Testing** | Validation & verification | 1 hour | All phases complete |

**Total Time**: 7-10 hours

### Resources Required

**Technical**:
- ✅ Supabase database access (SERVICE_ROLE_KEY)
- ✅ Python environment with supabase-py
- ✅ Frontend development environment
- ✅ Official Florida DOR use code documentation

**Data**:
- Florida DOR Property Use Codes (download from floridarevenue.com)
- County-specific code mappings (if needed)

**Tools Already Available**:
- ✅ SQLAlchemy agent (`mcp-server/ai-agents/dor_use_code_assignment_agent.py`)
- ✅ FastAPI service (`mcp-server/fastapi-endpoints/dor_use_code_api.py`)
- ✅ PySpark processor (`mcp-server/pyspark-processors/dor_use_code_spark_processor.py`)
- ✅ Jupyter notebook (`mcp-server/notebooks/dor_use_code_analysis.ipynb`)

---

## Success Metrics

| Metric | Current State | Target State |
|--------|--------------|--------------|
| property_use standardization | Mixed formats | 100% 2-digit DOR codes |
| property_use_desc population | 0% (100% NULL) | 100% populated |
| standardized_property_use categories | 3 categories | 50+ categories |
| DOR code coverage | Unknown | 100% of 9.1M properties |
| Icon mapping accuracy | ~5% (fallback only) | 100% correct icons |
| Frontend USE/SUBUSE display | Not implemented | Full display system |

---

## Risk Mitigation

### Data Quality Risks

**Risk**: Some properties may not fit standard DOR classifications
**Mitigation**: Implement intelligent fallback assignment based on property characteristics

**Risk**: County-specific code variations
**Mitigation**: Use official Florida DOR codes as authoritative source, map county variations

**Risk**: Historical data inconsistencies
**Mitigation**: Focus on year=2025 data first, extend to historical years after validation

### Technical Risks

**Risk**: Database timeout on bulk updates (9.1M records)
**Mitigation**:
- Break into county-level batches
- Use Supabase dashboard for large SQL operations
- Implement connection pooling via FastAPI service

**Risk**: Frontend performance with 100+ code mappings
**Mitigation**:
- Implement code lookup caching
- Pre-load DOR codes at app initialization
- Use memoization for icon/color lookups

---

## Next Steps

### Immediate Actions

1. **Download Official DOR Codes**: Fetch from floridarevenue.com
2. **Create DOR Codes JSON**: Structure all 100+ codes for import
3. **Populate dor_use_codes Table**: Load official reference data
4. **Execute Phase 2 SQL**: Standardize existing property_use codes
5. **Validate Results**: Run validation queries
6. **Implement Frontend**: Create USE/SUBUSE display components
7. **Test End-to-End**: Verify full system functionality

---

## Documentation & Support

**Reference Links**:
- Florida DOR Property Codes: https://floridarevenue.com/property/Documents/2023FINALCompSubmStd.pdf
- Rule 12D-8.008, FAC: https://www.flrules.org/gateway/ruleno.asp?id=12D-8.008
- DOR Data Portal: https://floridarevenue.com/property/dataportal/Pages/default.aspx

**Internal Documentation**:
- `DOR_USE_CODE_ASSIGNMENT_COMPLETE_SYSTEM.md`: Existing agent system
- `PROPERTY_USE_COMPLETE_AUDIT_REPORT.md`: Historical analysis
- `DOR_UC_TO_PROPERTY_USE_FINAL_VERIFICATION_REPORT.md`: Previous mapping work

---

## Conclusion

This comprehensive plan addresses all identified issues with the current property USE/SUBUSE system:

✅ Standardizes inconsistent property_use codes
✅ Populates missing property_use_desc fields
✅ Expands limited standardized_property_use categories
✅ Implements official Florida DOR use code system
✅ Creates frontend USE/SUBUSE display components
✅ Provides intelligent fallback assignment for edge cases
✅ Establishes 100% data quality and coverage

**Status**: READY FOR EXECUTION
**Estimated Completion**: 7-10 hours
**Impact**: 9.1M properties with proper classification

---

**Project Lead**: Claude AI Agent
**Date Prepared**: 2025-11-01
**Version**: 1.0
