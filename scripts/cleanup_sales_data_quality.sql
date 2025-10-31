-- ============================================================================
-- SALES HISTORY DATA QUALITY CLEANUP SCRIPT
-- ============================================================================
-- Purpose: Fix data quality issues in property_sales_history table
-- Issue: 1,788 records have prices over $1 billion (cents stored as dollars)
-- Date: 2025-10-30
-- Author: Claude Code
-- Severity: HIGH - Bad data visible to users
-- ============================================================================

-- STEP 1: Add data quality tracking column (if not exists)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'property_sales_history'
        AND column_name = 'data_quality_flag'
    ) THEN
        ALTER TABLE property_sales_history
        ADD COLUMN data_quality_flag TEXT;

        RAISE NOTICE 'Added data_quality_flag column to property_sales_history';
    ELSE
        RAISE NOTICE 'Column data_quality_flag already exists';
    END IF;
END $$;

-- STEP 2: Analyze current data quality issues
-- ============================================================================

-- Count records by price range
SELECT
    'Records with $0 sales' as category,
    COUNT(*) as record_count
FROM property_sales_history
WHERE sale_price = 0

UNION ALL

SELECT
    'Records $1-$999 (likely non-market)' as category,
    COUNT(*) as record_count
FROM property_sales_history
WHERE sale_price > 0 AND sale_price < 1000

UNION ALL

SELECT
    'Records $1k-$100k (normal residential)' as category,
    COUNT(*) as record_count
FROM property_sales_history
WHERE sale_price >= 1000 AND sale_price < 100000

UNION ALL

SELECT
    'Records $100k-$1M (high-end residential)' as category,
    COUNT(*) as record_count
FROM property_sales_history
WHERE sale_price >= 100000 AND sale_price < 1000000

UNION ALL

SELECT
    'Records $1M-$100M (luxury/commercial)' as category,
    COUNT(*) as record_count
FROM property_sales_history
WHERE sale_price >= 1000000 AND sale_price < 100000000

UNION ALL

SELECT
    'Records $100M-$1B (extremely rare, verify)' as category,
    COUNT(*) as record_count
FROM property_sales_history
WHERE sale_price >= 100000000 AND sale_price < 1000000000

UNION ALL

SELECT
    'Records over $1B (DATA ERRORS)' as category,
    COUNT(*) as record_count
FROM property_sales_history
WHERE sale_price >= 1000000000

ORDER BY
    CASE category
        WHEN 'Records with $0 sales' THEN 1
        WHEN 'Records $1-$999 (likely non-market)' THEN 2
        WHEN 'Records $1k-$100k (normal residential)' THEN 3
        WHEN 'Records $100k-$1M (high-end residential)' THEN 4
        WHEN 'Records $1M-$100M (luxury/commercial)' THEN 5
        WHEN 'Records $100M-$1B (extremely rare, verify)' THEN 6
        WHEN 'Records over $1B (DATA ERRORS)' THEN 7
    END;

-- STEP 3: Flag records with obvious data quality issues
-- ============================================================================

-- Flag sales over $1 billion (obvious errors - cents stored as dollars)
UPDATE property_sales_history
SET data_quality_flag = 'PRICE_OVER_1B_CENTS_AS_DOLLARS'
WHERE sale_price >= 1000000000
  AND (data_quality_flag IS NULL OR data_quality_flag = '');

-- Report results
SELECT
    data_quality_flag,
    COUNT(*) as count,
    MIN(sale_price) as min_price,
    MAX(sale_price) as max_price,
    ROUND(AVG(sale_price)) as avg_price
FROM property_sales_history
WHERE data_quality_flag IS NOT NULL
GROUP BY data_quality_flag;

-- STEP 4: Show sample of flagged records for manual review
-- ============================================================================

SELECT
    parcel_id,
    county,
    sale_date,
    sale_price as stored_price,
    ROUND(sale_price / 100) as likely_actual_price_option_1,
    ROUND(sale_price / 10000) as likely_actual_price_option_2,
    or_book,
    or_page,
    clerk_no,
    data_quality_flag
FROM property_sales_history
WHERE data_quality_flag = 'PRICE_OVER_1B_CENTS_AS_DOLLARS'
ORDER BY sale_price DESC
LIMIT 20;

-- STEP 5: OPTIONAL - Fix the data (CAUTION: Only run after manual review)
-- ============================================================================

-- OPTION A: Divide by 100 (if we're confident it's cents as dollars)
-- UNCOMMENT ONLY AFTER MANUAL REVIEW:
/*
UPDATE property_sales_history
SET
    sale_price = ROUND(sale_price / 100),
    data_quality_flag = 'CORRECTED_CENTS_TO_DOLLARS'
WHERE data_quality_flag = 'PRICE_OVER_1B_CENTS_AS_DOLLARS';
*/

-- OPTION B: Delete bad records (if data is unrecoverable)
-- UNCOMMENT ONLY AFTER MANUAL REVIEW:
/*
DELETE FROM property_sales_history
WHERE data_quality_flag = 'PRICE_OVER_1B_CENTS_AS_DOLLARS';
*/

-- STEP 6: Create view for clean data only
-- ============================================================================

CREATE OR REPLACE VIEW property_sales_history_clean AS
SELECT
    id,
    county_no,
    parcel_id,
    state_parcel_id,
    assessment_year,
    sale_date,
    sale_price,
    sale_year,
    sale_month,
    quality_code,
    or_book,
    or_page,
    clerk_no,
    county,
    data_quality_score,
    source_type,
    created_at,
    updated_at
FROM property_sales_history
WHERE
    -- Exclude flagged data quality issues
    (data_quality_flag IS NULL OR data_quality_flag NOT LIKE '%OVER_1B%')
    -- Exclude zero-price sales (non-market transfers)
    AND sale_price > 0
    -- Reasonable price range for Florida real estate
    AND sale_price >= 1000
    AND sale_price < 100000000;

-- Grant access to view
GRANT SELECT ON property_sales_history_clean TO authenticated;
GRANT SELECT ON property_sales_history_clean TO anon;

-- STEP 7: Verification queries
-- ============================================================================

-- Verify flagged records are excluded from clean view
SELECT
    'Total records in raw table' as metric,
    COUNT(*) as count
FROM property_sales_history

UNION ALL

SELECT
    'Records flagged with quality issues' as metric,
    COUNT(*) as count
FROM property_sales_history
WHERE data_quality_flag IS NOT NULL

UNION ALL

SELECT
    'Records in clean view' as metric,
    COUNT(*) as count
FROM property_sales_history_clean

UNION ALL

SELECT
    'Records excluded from clean view' as metric,
    COUNT(*) as count
FROM property_sales_history
WHERE id NOT IN (SELECT id FROM property_sales_history_clean);

-- STEP 8: Create index for performance
-- ============================================================================

-- Index on data_quality_flag for faster filtering
CREATE INDEX IF NOT EXISTS idx_sales_data_quality_flag
ON property_sales_history(data_quality_flag);

-- COMPLETION SUMMARY
-- ============================================================================
SELECT
    '=====================================' as summary,
    'DATA QUALITY CLEANUP COMPLETED' as status,
    '=====================================' as summary2;

SELECT
    'Flagged records with quality issues' as action,
    COUNT(*) as count
FROM property_sales_history
WHERE data_quality_flag = 'PRICE_OVER_1B_CENTS_AS_DOLLARS';

SELECT
    'Created property_sales_history_clean view' as action,
    'Use this view in application queries' as recommendation;

SELECT
    'Next steps:' as step,
    '1. Review flagged records manually' as action;

SELECT
    'Next steps:' as step,
    '2. Decide on correction strategy (divide by 100 or delete)' as action;

SELECT
    'Next steps:' as step,
    '3. Update application to use property_sales_history_clean view' as action;

SELECT
    'Next steps:' as step,
    '4. Fix SDF import process to prevent future issues' as action;
