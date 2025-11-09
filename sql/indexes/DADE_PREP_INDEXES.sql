-- ============================================================================
-- DADE PREP: CREATE SUPPORTING INDEXES (RUN BEFORE STEP 1)
-- ============================================================================
-- These indexes speed up the temp table population and batch processing.
-- Run this once before executing FINAL_OPTIMIZED_DADE.sql
-- ============================================================================

-- Index 1: Speed up year/county filtering (used in STEP 1 INSERT)
CREATE INDEX IF NOT EXISTS idx_parcels_year_county
ON public.florida_parcels(year, county);

-- Index 2: Speed up land_use_code filtering (optional, helps if repeating often)
-- This partial index only stores rows that need updating
CREATE INDEX IF NOT EXISTS idx_parcels_luc_null
ON public.florida_parcels(id)
WHERE land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99';

-- Note: id is already the PRIMARY KEY, so it's automatically indexed

-- ============================================================================
-- Verify indexes were created
-- ============================================================================
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'florida_parcels'
    AND indexname IN ('idx_parcels_year_county', 'idx_parcels_luc_null', 'florida_parcels_pkey')
ORDER BY indexname;

-- ============================================================================
-- TIMELINE NOTES:
-- - Index 1 creation: ~30-60 seconds (9.14M rows)
-- - Index 2 creation: ~45-90 seconds (partial index on 5.95M rows)
-- - These indexes will significantly speed up STEP 1 temp table population
-- - Run this ONCE, then proceed to FINAL_OPTIMIZED_DADE.sql
-- ============================================================================