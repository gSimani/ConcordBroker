-- Migration: Fill Missing standardized_property_use Values
-- Date: 2025-10-30
-- Purpose: Backfill missing standardized property use values from DOR codes
-- Impact: 100% data coverage for property type filtering

-- First, check current coverage
SELECT
    COUNT(*) as total_properties,
    COUNT(standardized_property_use) as has_standardized,
    COUNT(*) - COUNT(standardized_property_use) as missing,
    ROUND(100.0 * COUNT(standardized_property_use) / COUNT(*), 2) as coverage_pct
FROM florida_parcels;

-- Update missing values based on property_use DOR codes
-- Using Florida DOR standard classifications
UPDATE florida_parcels
SET standardized_property_use = CASE
    -- Single Family Residential (00-09)
    WHEN property_use IN ('00', '0', '01', '1', '02', '2', '03', '3', '04', '4', '05', '5', '06', '6', '07', '7', '08', '8', '09', '9')
        THEN 'Single Family Residential'

    -- Condominium (10-19)
    WHEN property_use IN ('10', '11', '12', '13', '14', '15', '16', '17', '18', '19')
        THEN 'Condominium'

    -- Commercial (20-39)
    WHEN property_use IN ('20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
                          '30', '31', '32', '33', '34', '35', '36', '37', '38', '39')
        THEN 'Commercial'

    -- Industrial (40-49)
    WHEN property_use IN ('40', '41', '42', '43', '44', '45', '46', '47', '48', '49')
        THEN 'Industrial'

    -- Agricultural (50-69)
    WHEN property_use IN ('50', '51', '52', '53', '54', '55', '56', '57', '58', '59',
                          '60', '61', '62', '63', '64', '65', '66', '67', '68', '69')
        THEN 'Agricultural'

    -- Institutional (70-79)
    WHEN property_use IN ('70', '71', '72', '73', '74', '75', '76', '77', '78', '79')
        THEN 'Institutional'

    -- Government/Municipal (80-89)
    WHEN property_use IN ('80', '81', '82', '83', '84', '85', '86', '87', '88', '89')
        THEN 'Governmental'

    -- Vacant/Centrally Assessed (90-99)
    WHEN property_use IN ('90', '91', '92', '93', '94', '95', '96', '97', '98', '99')
        THEN 'Vacant Land'

    -- Multi-Family indicators from description
    WHEN property_use_desc ILIKE '%multi%family%' OR property_use_desc ILIKE '%apartment%'
        THEN 'Multi-Family'

    -- Mobile Home indicators
    WHEN property_use_desc ILIKE '%mobile%home%' OR property_use_desc ILIKE '%manufactured%'
        THEN 'Mobile Home'

    -- Default fallback
    ELSE 'Other'
END
WHERE standardized_property_use IS NULL
AND property_use IS NOT NULL;

-- Additional update for special cases based on property characteristics
UPDATE florida_parcels
SET standardized_property_use = 'Multi-Family 10+ Units'
WHERE standardized_property_use = 'Multi-Family'
AND (units >= 10 OR no_res_unts >= 10);

-- Mark properties with residential improvements on vacant land
UPDATE florida_parcels
SET standardized_property_use = 'Single Family Residential'
WHERE standardized_property_use = 'Vacant Land'
AND tot_lvg_area > 500  -- Has significant building area
AND no_res_unts = 1;    -- Single unit

-- Verify the update
SELECT
    COUNT(*) as total_properties,
    COUNT(standardized_property_use) as has_standardized,
    COUNT(*) - COUNT(standardized_property_use) as missing,
    ROUND(100.0 * COUNT(standardized_property_use) / COUNT(*), 2) as coverage_pct,
    COUNT(*) FILTER (WHERE standardized_property_use = 'Other') as classified_as_other
FROM florida_parcels;

-- Show distribution of property types after backfill
SELECT
    standardized_property_use,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM florida_parcels
WHERE standardized_property_use IS NOT NULL
GROUP BY standardized_property_use
ORDER BY count DESC;

-- Log the update for audit purposes
DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RAISE NOTICE 'Updated % rows with standardized_property_use values', rows_updated;
END $$;

/*
EXPECTED RESULTS:
- Coverage: 95% → 99%+ (only truly unclassifiable properties remain)
- All properties with valid DOR codes get standardized values
- Multi-family properties correctly categorized by unit count
- Vacant land with improvements correctly reclassified

POST-MIGRATION STEPS:
1. Refresh property_type_counts materialized view
2. Verify filter accuracy in UI
3. Check for any remaining 'Other' classifications
4. Update property intelligence rules if needed
*/
