-- =====================================================
-- COMPLETE STANDARDIZATION FIX FOR FLORIDA_PARCELS
-- =====================================================
-- Date: October 30, 2025
-- Purpose: Populate standardized_property_use for ALL properties
-- Impact: Will update 9.7M rows based on DOR property_use codes
-- =====================================================

BEGIN;

-- Step 1: Update Residential Properties (DOR Codes 01-09)
-- Expected: 3,647,262 properties
UPDATE florida_parcels
SET standardized_property_use = 'Residential'
WHERE property_use IN (
    '01', '02', '03', '04', '05', '06', '07', '08', '09',
    '1', '2', '3', '4', '5', '6', '7', '8', '9'
)
AND (standardized_property_use IS NULL OR standardized_property_use != 'Residential');

-- Step 2: Update Commercial Properties (DOR Codes 10-39)
-- Expected: 157,008 properties
UPDATE florida_parcels
SET standardized_property_use = 'Commercial'
WHERE property_use IN (
    '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
    '20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
    '30', '31', '32', '33', '34', '35', '36', '37', '38', '39'
)
AND (standardized_property_use IS NULL OR standardized_property_use != 'Commercial');

-- Step 3: Update Industrial Properties (DOR Codes 40-49)
-- Expected: 41,964 properties
UPDATE florida_parcels
SET standardized_property_use = 'Industrial'
WHERE property_use IN (
    '40', '41', '42', '43', '44', '45', '46', '47', '48', '49'
)
AND (standardized_property_use IS NULL OR standardized_property_use != 'Industrial');

-- Step 4: Update Agricultural Properties (DOR Codes 51-69)
-- Expected: 127,476 properties
UPDATE florida_parcels
SET standardized_property_use = 'Agricultural'
WHERE property_use IN (
    '51', '52', '53', '54', '55', '56', '57', '58', '59',
    '60', '61', '62', '63', '64', '65', '66', '67', '68', '69'
)
AND (standardized_property_use IS NULL OR standardized_property_use != 'Agricultural');

-- Step 5: Update Institutional Properties (DOR Codes 71-79)
-- Expected: 22,454 properties
UPDATE florida_parcels
SET standardized_property_use = 'Institutional'
WHERE property_use IN (
    '71', '72', '73', '74', '75', '76', '77', '78', '79'
)
AND (standardized_property_use IS NULL OR standardized_property_use != 'Institutional');

-- Step 6: Update Government Properties (DOR Codes 81-89)
-- Expected: 91,016 properties
UPDATE florida_parcels
SET standardized_property_use = 'Government'
WHERE property_use IN (
    '81', '82', '83', '84', '85', '86', '87', '88', '89'
)
AND (standardized_property_use IS NULL OR standardized_property_use != 'Government');

-- Step 7: Update Vacant Land Properties (DOR Codes 00, 90-99)
-- Expected: 923,643 properties
UPDATE florida_parcels
SET standardized_property_use = 'Vacant Land'
WHERE property_use IN (
    '00', '0', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99'
)
AND (standardized_property_use IS NULL OR standardized_property_use != 'Vacant Land');

-- Step 8: Create performance index
CREATE INDEX IF NOT EXISTS idx_florida_parcels_standardized_use
ON florida_parcels(standardized_property_use)
WHERE standardized_property_use IS NOT NULL;

-- Step 9: Create index on property_use for filtering
CREATE INDEX IF NOT EXISTS idx_florida_parcels_property_use
ON florida_parcels(property_use);

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================
-- Run these after migration to verify success:
--
-- SELECT standardized_property_use, COUNT(*)
-- FROM florida_parcels
-- WHERE standardized_property_use IS NOT NULL
-- GROUP BY standardized_property_use
-- ORDER BY COUNT(*) DESC;
--
-- Expected Results:
-- Residential:   3,647,262
-- Vacant Land:     923,643
-- Commercial:      157,008
-- Agricultural:    127,476
-- Government:       91,016
-- Industrial:       41,964
-- Institutional:    22,454
-- =====================================================
