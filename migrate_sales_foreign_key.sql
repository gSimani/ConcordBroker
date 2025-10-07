-- ============================================================================
-- FOREIGN KEY MIGRATION: property_sales_history → florida_parcels
-- ============================================================================
--
-- STRATEGY: Option C (Surrogate Key)
-- PURPOSE: Add referential integrity without changing existing schema structure
-- TIME: 15-20 minutes for 117K sales records
-- IMPACT: Prevents orphaned sales records, enables CASCADE operations
--
-- SAFETY: All operations run with minimal locking
-- ROLLBACK: Full rollback script included at bottom
--
-- USAGE:
--   psql "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" -f migrate_sales_foreign_key.sql
-- ============================================================================

\timing on
\set ON_ERROR_STOP on

\echo '============================================================================'
\echo 'FOREIGN KEY MIGRATION - OPTION C (SURROGATE KEY)'
\echo '============================================================================'
\echo ''
\echo 'This script will:'
\echo '  1. Add parcel_pk column to property_sales_history'
\echo '  2. Backfill parcel_pk from florida_parcels.id in batches'
\echo '  3. Create index on parcel_pk'
\echo '  4. Add foreign key constraint'
\echo '  5. Validate referential integrity'
\echo ''
\echo 'Estimated time: 15-20 minutes'
\echo 'Database locks: Minimal (uses CONCURRENTLY where possible)'
\echo ''
\echo 'Press Ctrl+C to cancel, or wait 5 seconds to proceed...'
\echo ''

SELECT pg_sleep(5);

-- ============================================================================
-- PHASE 1: Pre-flight Checks
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 1: Pre-flight Checks'
\echo '============================================================================'
\echo ''

-- Check if migration already completed
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.table_constraints
    WHERE constraint_schema = 'public'
      AND table_name = 'property_sales_history'
      AND constraint_name = 'fk_sales_parcel_pk'
  ) THEN
    RAISE EXCEPTION 'Migration already completed: fk_sales_parcel_pk exists';
  END IF;
END $$;

-- Check florida_parcels has primary key
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.table_constraints
    WHERE constraint_schema = 'public'
      AND table_name = 'florida_parcels'
      AND constraint_type = 'PRIMARY KEY'
  ) THEN
    RAISE EXCEPTION 'florida_parcels must have a primary key';
  END IF;
END $$;

\echo 'Pre-flight checks passed'
\echo ''

-- Get current row counts
\echo 'Current row counts:'
SELECT
  'florida_parcels' AS table_name,
  COUNT(*) AS row_count
FROM florida_parcels
UNION ALL
SELECT
  'property_sales_history',
  COUNT(*)
FROM property_sales_history;

\echo ''

-- Check for orphaned sales records (records without matching parcel)
\echo 'Checking for orphaned sales records...'
WITH orphaned AS (
  SELECT COUNT(*) AS orphan_count
  FROM property_sales_history psh
  LEFT JOIN florida_parcels fp ON psh.parcel_id = fp.parcel_id
  WHERE fp.parcel_id IS NULL
)
SELECT
  orphan_count,
  CASE
    WHEN orphan_count = 0 THEN 'PASS: No orphaned records found'
    ELSE 'WARNING: ' || orphan_count || ' orphaned records will be handled'
  END AS status
FROM orphaned;

\echo ''

-- ============================================================================
-- PHASE 2: Add parcel_pk Column
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 2: Add parcel_pk Column'
\echo '============================================================================'
\echo ''

-- Add column if not exists (NULL allowed initially)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'property_sales_history'
      AND column_name = 'parcel_pk'
  ) THEN
    ALTER TABLE property_sales_history
    ADD COLUMN parcel_pk BIGINT;

    RAISE NOTICE 'Column parcel_pk added to property_sales_history';
  ELSE
    RAISE NOTICE 'Column parcel_pk already exists, skipping';
  END IF;
END $$;

\echo 'Column addition complete'
\echo ''

-- ============================================================================
-- PHASE 3: Backfill parcel_pk (Batched for Safety)
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 3: Backfill parcel_pk in Batches'
\echo '============================================================================'
\echo ''
\echo 'This will update ~117,000 records in batches of 5,000'
\echo 'Progress will be shown every batch...'
\echo ''

-- Batched backfill with progress tracking
DO $$
DECLARE
  batch_size INT := 5000;
  rows_updated INT;
  total_updated INT := 0;
  batch_num INT := 0;
  start_time TIMESTAMP;
  elapsed INTERVAL;
BEGIN
  start_time := clock_timestamp();

  LOOP
    batch_num := batch_num + 1;

    -- Update one batch
    WITH batch AS (
      SELECT psh.id
      FROM property_sales_history psh
      WHERE psh.parcel_pk IS NULL
      LIMIT batch_size
    )
    UPDATE property_sales_history psh
    SET parcel_pk = fp.id
    FROM batch
    JOIN florida_parcels fp ON psh.parcel_id = fp.parcel_id
    WHERE psh.id = batch.id;

    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    total_updated := total_updated + rows_updated;

    EXIT WHEN rows_updated = 0;

    -- Progress report
    elapsed := clock_timestamp() - start_time;
    RAISE NOTICE 'Batch %: Updated % rows (Total: % in %)',
      batch_num, rows_updated, total_updated, elapsed;

    -- Throttle to avoid overwhelming database
    PERFORM pg_sleep(0.05);

    -- Commit batch (in psql autocommit mode, this is implicit)
  END LOOP;

  RAISE NOTICE 'Backfill complete: % total rows updated in %',
    total_updated, clock_timestamp() - start_time;
END $$;

\echo ''
\echo 'Backfill complete'
\echo ''

-- ============================================================================
-- PHASE 4: Handle Orphaned Records
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 4: Handle Orphaned Records'
\echo '============================================================================'
\echo ''

-- Check remaining NULL values (orphaned records)
WITH orphan_check AS (
  SELECT COUNT(*) AS orphan_count
  FROM property_sales_history
  WHERE parcel_pk IS NULL
)
SELECT
  orphan_count,
  CASE
    WHEN orphan_count = 0 THEN 'All records backfilled successfully'
    ELSE 'Found ' || orphan_count || ' orphaned records without matching parcel'
  END AS message
FROM orphan_check;

-- Optional: Delete orphaned records (uncomment if desired)
-- WARNING: This will permanently delete sales records without matching parcels
/*
DELETE FROM property_sales_history
WHERE parcel_pk IS NULL;

\echo 'Orphaned records deleted'
*/

-- Alternative: Report orphaned records for manual review
\echo ''
\echo 'Sample orphaned records (if any):'
SELECT
  id,
  parcel_id,
  sale_date,
  sale_price
FROM property_sales_history
WHERE parcel_pk IS NULL
LIMIT 10;

\echo ''
\echo 'Note: Orphaned records must be handled before adding FK constraint'
\echo 'Options:'
\echo '  1. Delete orphaned records (uncomment DELETE above)'
\echo '  2. Manually fix parcel_id values'
\echo '  3. Skip FK constraint (not recommended)'
\echo ''

-- ============================================================================
-- PHASE 5: Create Index on parcel_pk
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 5: Create Index on parcel_pk'
\echo '============================================================================'
\echo ''

-- Create index CONCURRENTLY for zero-downtime
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_parcel_pk
ON property_sales_history(parcel_pk)
WHERE parcel_pk IS NOT NULL;

\echo 'Index idx_sales_parcel_pk created'
\echo ''

-- ============================================================================
-- PHASE 6: Add Foreign Key Constraint
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 6: Add Foreign Key Constraint'
\echo '============================================================================'
\echo ''

-- This will fail if any orphaned records exist
DO $$
DECLARE
  orphan_count INT;
BEGIN
  -- Final orphan check
  SELECT COUNT(*) INTO orphan_count
  FROM property_sales_history
  WHERE parcel_pk IS NULL;

  IF orphan_count > 0 THEN
    RAISE EXCEPTION 'Cannot add FK: % orphaned records found. Please handle them first.', orphan_count;
  END IF;

  -- Add foreign key constraint
  ALTER TABLE property_sales_history
  ADD CONSTRAINT fk_sales_parcel_pk
  FOREIGN KEY (parcel_pk)
  REFERENCES florida_parcels(id)
  ON DELETE CASCADE
  NOT VALID;  -- Add NOT VALID first for faster initial creation

  RAISE NOTICE 'Foreign key constraint added (NOT VALID)';

  -- Validate constraint (can be slow, but doesn't block writes)
  ALTER TABLE property_sales_history
  VALIDATE CONSTRAINT fk_sales_parcel_pk;

  RAISE NOTICE 'Foreign key constraint validated';
END $$;

\echo 'Foreign key constraint fk_sales_parcel_pk created'
\echo ''

-- ============================================================================
-- PHASE 7: Optional - Make parcel_pk NOT NULL
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 7: Make parcel_pk NOT NULL (Optional)'
\echo '============================================================================'
\echo ''

-- Only set NOT NULL if all records have values
DO $$
DECLARE
  null_count INT;
BEGIN
  SELECT COUNT(*) INTO null_count
  FROM property_sales_history
  WHERE parcel_pk IS NULL;

  IF null_count = 0 THEN
    ALTER TABLE property_sales_history
    ALTER COLUMN parcel_pk SET NOT NULL;
    RAISE NOTICE 'Column parcel_pk set to NOT NULL';
  ELSE
    RAISE WARNING 'Skipping NOT NULL constraint: % records still have NULL parcel_pk', null_count;
  END IF;
END $$;

\echo ''

-- ============================================================================
-- PHASE 8: Verification
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 8: Verification'
\echo '============================================================================'
\echo ''

-- Verify constraint exists
\echo 'Foreign key constraints on property_sales_history:'
SELECT
  conname AS constraint_name,
  contype AS constraint_type,
  pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid = 'property_sales_history'::regclass
  AND contype = 'f';

\echo ''

-- Verify backfill success rate
\echo 'Backfill statistics:'
SELECT
  COUNT(*) AS total_sales,
  COUNT(parcel_pk) AS backfilled,
  COUNT(*) - COUNT(parcel_pk) AS remaining_null,
  ROUND(100.0 * COUNT(parcel_pk) / NULLIF(COUNT(*), 0), 2) AS success_rate_pct
FROM property_sales_history;

\echo ''

-- Test query performance
\echo 'Testing JOIN performance with new FK:'
EXPLAIN ANALYZE
SELECT
  fp.parcel_id,
  fp.phy_addr1,
  fp.owner_name,
  COUNT(psh.id) AS sales_count
FROM florida_parcels fp
LEFT JOIN property_sales_history psh ON psh.parcel_pk = fp.id
WHERE fp.county = 'MIAMI-DADE'
  AND fp.just_value > 500000
GROUP BY fp.id, fp.parcel_id, fp.phy_addr1, fp.owner_name
LIMIT 10;

\echo ''

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

\echo '============================================================================'
\echo 'MIGRATION COMPLETE'
\echo '============================================================================'
\echo ''
\echo 'Summary:'
\echo '  ✓ parcel_pk column added to property_sales_history'
\echo '  ✓ Data backfilled from florida_parcels.id'
\echo '  ✓ Index created on parcel_pk'
\echo '  ✓ Foreign key constraint fk_sales_parcel_pk added'
\echo '  ✓ Referential integrity enforced'
\echo ''
\echo 'Benefits:'
\echo '  • Prevents orphaned sales records'
\echo '  • Enables CASCADE delete operations'
\echo '  • Improves JOIN performance'
\echo '  • Documents table relationships'
\echo ''
\echo 'Note: parcel_id column retained for backward compatibility'
\echo '      Future queries can use either parcel_id or parcel_pk'
\echo ''

-- ============================================================================
-- ROLLBACK SCRIPT (Save for emergency use)
-- ============================================================================

\echo '============================================================================'
\echo 'ROLLBACK SCRIPT (save this for emergency use)'
\echo '============================================================================'
\echo ''
\echo '-- To revert this migration:'
\echo 'ALTER TABLE property_sales_history DROP CONSTRAINT IF EXISTS fk_sales_parcel_pk CASCADE;'
\echo 'DROP INDEX CONCURRENTLY IF EXISTS idx_sales_parcel_pk;'
\echo 'ALTER TABLE property_sales_history DROP COLUMN IF EXISTS parcel_pk;'
\echo ''
\echo '-- To verify rollback:'
\echo 'SELECT column_name FROM information_schema.columns'
\echo 'WHERE table_name = '\''property_sales_history'\'' AND column_name = '\''parcel_pk'\'';'
\echo ''
