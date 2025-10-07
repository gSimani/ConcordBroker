# Use Database Mapping Analysis

## Executive Summary
Critical discrepancies found between UI property categorization logic and actual Supabase database schema. This document provides comprehensive mapping to align mini property cards and Usage filter buttons with database reality.

## Database Schema Analysis

### Primary Tables with Use Data

#### 1. `florida_parcels` (Main Property Data)
- **Columns**: `property_use`, `property_use_desc`, `land_use_code`
- **Data Type**: Integer codes (0, 1, 2, 4, 8, 9, 10, 11, 16, 17, 19, 21, 28, 30, 48, 53, 55, 56, 57, 62, 63, 69, 71, 80, 86, 87, 91, 98, 99)
- **Current Issue**: UI expects 4-digit padded DOR codes, but database has integer values
- **Volume**: Primary property records

#### 2. `property_sales_history` (Sales with DOR Codes)
- **Columns**: `dor_use_code`
- **Data Type**: 3-digit string codes ("000", "001", "009", "094")
- **Current Issue**: Not integrated with property filtering
- **Volume**: Historical sales data

#### 3. `tax_certificates` (Tax Deed Properties)
- **Columns**: `property_use_code`, `property_use_description`
- **Data Type**: Mixed format
- **Usage**: Tax deed specific filtering

## Current UI Logic vs Database Reality

### Current `propertyCategories.ts` Logic
```typescript
// Current logic expects 4-digit padded codes
const codeStr = code.padStart(4, '0');
if (codeStr >= '0100' && codeStr <= '0199') return 'Residential';
```

### Actual Database Values
- **florida_parcels.property_use**: 1, 2, 4, 8, 9, 10, 11, 16, 17, 19, 21, 28, 30, 48, 53, 55, 56, 57, 62, 63, 69, 71, 80, 86, 87, 91, 98, 99
- **property_sales_history.dor_use_code**: "000", "001", "009", "094"

## Proposed Mapping Solution

### 1. Database Value to Category Mapping
Based on actual data, create hybrid mapping:

```typescript
// Integer codes from florida_parcels.property_use
const PROPERTY_USE_TO_CATEGORY = {
  0: 'Vacant',
  1: 'Residential',
  2: 'Residential',
  4: 'Condo',
  8: 'Multi-Family',
  9: 'Residential',
  10: 'Commercial',
  11: 'Commercial',
  16: 'Commercial',
  17: 'Commercial',
  19: 'Commercial',
  21: 'Industrial',
  28: 'Industrial',
  30: 'Industrial',
  48: 'Industrial',
  53: 'Agricultural',
  55: 'Agricultural',
  56: 'Agricultural',
  57: 'Agricultural',
  62: 'Agricultural',
  63: 'Agricultural',
  69: 'Agricultural',
  71: 'Institutional',
  80: 'Governmental',
  86: 'Governmental',
  87: 'Governmental',
  91: 'Special',
  98: 'Special',
  99: 'Special'
};

// 3-digit DOR codes from property_sales_history.dor_use_code
const DOR_CODE_TO_CATEGORY = {
  "000": 'Vacant',
  "001": 'Residential',
  "009": 'Residential',
  "094": 'Special'
};
```

### 2. API Filter Integration
Current API filtering uses `property_use` field. Update to support both:

```python
# In production_property_api.py
if usage_code:
    # Support both integer and string DOR codes
    if usage_code.isdigit() and len(usage_code) <= 2:
        # Integer property_use code
        query = query.eq('property_use', int(usage_code))
    else:
        # 3-digit DOR code - join with sales history
        query = query.eq('property_use', usage_code)
```

### 3. Frontend Filter Button Mapping
Update `dorCodeService.ts` to map UI categories to actual database values:

```typescript
export const PROPERTY_TYPE_TO_DB_VALUES = {
  'Residential': [1, 2, 9],
  'Commercial': [10, 11, 16, 17, 19],
  'Industrial': [21, 28, 30, 48],
  'Agricultural': [53, 55, 56, 57, 62, 63, 69],
  'Vacant': [0],
  'Condo': [4],
  'Multi-Family': [8],
  'Institutional': [71],
  'Governmental': [80, 86, 87],
  'Special': [91, 98, 99]
};
```

## Implementation Plan

### Phase 1: Update Property Categories (PRIORITY)
1. Create hybrid `getPropertyCategoryFromUse()` function
2. Support both integer and DOR code inputs
3. Map actual database values to display categories

### Phase 2: Fix API Filtering
1. Update property search API to handle integer property_use codes
2. Add support for category-to-codes mapping
3. Test all filter combinations

### Phase 3: Update UI Components
1. Update MiniPropertyCard to use new mapping
2. Fix Usage filter buttons to send correct database values
3. Update Advanced Filters DOR code autocomplete

### Phase 4: Data Integration
1. Consider joining sales history DOR codes for enhanced categorization
2. Implement fallback logic for missing property_use_desc
3. Add data validation and error handling

## Testing Requirements
- [ ] Verify all property types display correct categories
- [ ] Test filter buttons with actual database values
- [ ] Validate API responses match frontend expectations
- [ ] Confirm edge cases (null values, unknown codes)

## Risk Mitigation
- Maintain backward compatibility during transition
- Add comprehensive logging for mapping mismatches
- Implement graceful fallbacks for unknown codes
- Monitor performance impact of new mapping logic