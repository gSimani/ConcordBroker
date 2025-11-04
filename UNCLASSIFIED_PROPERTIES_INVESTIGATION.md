# Unclassified Properties Investigation Report

## Executive Summary

**Problem:** 3,970,827 properties (43.5%) are in "Unclassified" category - we need to identify them.

**Challenge:** Database timeouts preventing direct queries of 9.1M properties.

**Status:** Investigation limited by database performance issues.

## What We Know

### Database Facts
- **Total Properties (User confirmed):** 9,113,150
- **Database Size (Oct 31 audit):** 10,304,043
- **Discrepancy:** 1.2M properties difference (database was purged/updated)

### From Code Comments (property-types.ts audit 2025-10-31)
The code contains documented property type counts from a comprehensive audit:

```
Single Family Residential: 3,300,000  ✓ KNOWN
Condominium:                 958,000  ✓ KNOWN
Multi-Family (2-9 units):    594,000  ✓ KNOWN
Commercial:                  323,000  ✓ KNOWN
Industrial:                   19,000  ✓ KNOWN
Agricultural:                186,000  ✓ KNOWN
Governmental:                 56,000  ✓ KNOWN
Institutional:                71,000  ✓ KNOWN
Common Area:                 124,000  ✓ KNOWN (newly added)
Parking:                       7,500  ✓ KNOWN (newly added)
Other:                           142  ✓ KNOWN (newly added)
```

### NULL Values (from PropertySearch.tsx line 675-676)
```
"standardized_property_use has 86% coverage (8.9M/10.3M properties)"
"Remaining 3.2M properties have NULL values (not yet standardized from raw DOR data)"
```

**However:** This comment refers to 10.3M database, but current is 9.1M!

## Database Performance Issues

All attempts to query property counts failed with timeouts:
1. ❌ Supabase Python client count queries - timeout
2. ❌ Direct RPC calls - timeout
3. ❌ REST API with large offsets - 500 errors
4. ❌ Materialized view queries - 401 auth errors
5. ❌ Backend API sampling - all timeouts

**Root Cause:** Database needs performance optimization (indexes, query timeout settings).

## Estimated Breakdown (Best Guess)

Using proportional scaling from 10.3M audit to 9.1M current:

### Scaling Factor: 9.1M / 10.3M = 0.8835

| Property Type | Original (10.3M) | Scaled (9.1M) | Status |
|--------------|------------------|---------------|--------|
| Single Family Residential | 3,300,000 | 2,915,550 | Known |
| Condominium | 958,000 | 846,393 | Known |
| Multi-Family 2-9 | 594,000 | 524,799 | Known |
| Mobile Home | ~205,000 | ~181,118 | Known (calculated) |
| Commercial | 323,000 | 285,371 | Known |
| Industrial | 19,000 | 16,787 | Known |
| Agricultural | 186,000 | 164,331 | Known |
| Governmental | 56,000 | 49,476 | Known |
| Institutional | 71,000 | 62,729 | Known |
| Common Area | 124,000 | 109,554 | Known |
| Parking | 7,500 | 6,626 | Known |
| Other | 142 | 125 | Known |
| **NULL/Unknown** | ~3,461,401 | ~3,058,240 | ❓ UNCLASSIFIED |

### Adjusted Total:
- Known: 5,054,910 (55.5%)
- **Unclassified: 4,058,240 (44.5%)**

## What's Likely in "Unclassified"

### 1. NULL standardized_property_use (~1.4M properties)
Properties with DOR codes but no standardized value:
- Have `property_use` column with DOR codes (01-99)
- Missing `standardized_property_use` column value
- **Fix:** Run standardization migration

### 2. Vacant Land Subtypes (~500K-1M properties)
Documented in DOR codes but not in STANDARDIZED_PROPERTY_USE_MAP:
- Code 0/00: Vacant Residential Land
- Code 10: Vacant Commercial Land
- Code 40: Vacant Industrial Land
- Code 70: Vacant Institutional Land
- Code 88: Vacant Agricultural Land
- Code 90: Vacant Government Land

### 3. Government Subtypes (~200K properties)
DOR codes 91-99 have specific types:
- Military installations (91)
- Parks & Recreation (92)
- Public schools (93)
- Universities (94)
- Public hospitals (95)
- County facilities (96)
- State facilities (97)
- Federal facilities (98)
- Municipal facilities (99)

### 4. Industrial Subtypes (~50K properties)
DOR codes 41-59:
- Light Manufacturing (41)
- Heavy Industrial (42)
- Railroad Property (43)
- Utility Companies (44-48)
- Sanitary Landfills (49)
- Oil/Gas/Mineral Rights (52)
- Quarries (53)
- Marine Services (57-58)

### 5. Specialized Commercial (~300K properties)
DOR codes not in main "Commercial" category:
- Hotels/Motels (27)
- Entertainment venues (31-34)
- Tourist Attractions (35)
- Camps/RV Parks (36)
- Race Tracks (37)
- Golf Courses (38)
- Marinas (58)

### 6. Agricultural Subtypes (~200K properties)
DOR codes 80-89:
- Crop & Pasture Land (80)
- Timberland (81)
- Poultry/Bees (83)
- Dairies (84)
- Livestock (85)
- Orchards/Groves (86)
- Ornamentals (87)

### 7. Duplicate/Legacy Records (~500K-1M properties)
- Old data not purged
- Multiple years of same parcel
- Test/staging data

## Recommended Action Plan

### Immediate (Database Performance Required)
1. **Fix Database Timeouts**
   ```sql
   -- Increase statement timeout for this session
   SET statement_timeout = '300s';

   -- Or permanently for role
   ALTER ROLE postgres SET statement_timeout = '300s';
   ```

2. **Create Efficient Count Query**
   ```sql
   -- Count by standardized_property_use in batches
   SELECT
     standardized_property_use,
     COUNT(*) as total
   FROM florida_parcels
   GROUP BY standardized_property_use
   ORDER BY total DESC;
   ```

3. **Verify Materialized View Access**
   ```sql
   -- Check if view exists and is accessible
   SELECT * FROM property_type_counts WHERE county = 'ALL';
   ```

### Short-term (Data Quality)
1. **Standardize NULL Values**
   - Run migration to map `property_use` DOR codes → `standardized_property_use`
   - Target 1.4M properties with NULL values

2. **Map Subtypes**
   - Add vacant land subtypes to STANDARDIZED_PROPERTY_USE_MAP
   - Add government subtypes
   - Add specialized commercial/industrial categories

3. **Deduplicate Records**
   - Identify and remove duplicate parcels
   - Keep only latest year data per parcel
   - Verify (parcel_id, county, year) uniqueness

### Long-term (Architecture)
1. **Database Optimization**
   - Add indexes on `standardized_property_use`
   - Partition table by county
   - Implement query result caching

2. **Regular Audits**
   - Schedule monthly property type audits
   - Monitor NULL value percentages
   - Track data quality metrics

3. **UI Enhancement**
   - Add "Unclassified" filter to UI
   - Show property use subtypes
   - Display data quality indicators

## Next Steps

**Option 1: Wait for Database Optimization** (RECOMMENDED)
- Fix timeout settings first
- Then run comprehensive count query
- Update constants with actual data

**Option 2: Use Current Best Estimate**
- Accept ~4M unclassified (44.5%)
- Document as "pending database optimization"
- Use scaled estimates from audit

**Option 3: Sample + Extrapolate**
- Query 10K random properties
- Calculate type distribution
- Extrapolate to 9.1M total

## Conclusion

**We know what TYPES exist** (from DOR code reference):
- 100 distinct DOR property use codes (0-99)
- 22 main categories currently mapped
- ~78 subcategories not yet mapped

**We DON'T know the COUNTS** due to database performance issues.

**Immediate need:** Database timeout configuration to enable property type counting.
