-- =====================================================
-- PHASE 1.2: PROPERTY SALES HISTORY INDEXES
-- Optimize sales history queries
--
-- Estimated time: 10-15 minutes
-- Impact: 10-50x faster sales queries
-- Risk: LOW
--
-- Run in Supabase SQL Editor
-- =====================================================

-- =====================================================
-- Index 1: Parcel + Date Composite (Most Common)
-- Used in: Property detail pages, sales history retrieval
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_parcel_date
  ON property_sales_history(parcel_id, sale_date DESC)
  WHERE sale_date IS NOT NULL;

COMMENT ON INDEX idx_sales_parcel_date IS
  'Composite index for sales by parcel with date ordering';

-- =====================================================
-- Index 2: Sale Date Range Queries
-- Used in: Date range filters, recent sales
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_date
  ON property_sales_history(sale_date DESC)
  WHERE sale_date IS NOT NULL;

COMMENT ON INDEX idx_sales_date IS
  'Date range queries and recent sales lookups';

-- =====================================================
-- Index 3: Sale Price Filtering
-- Used in: Price range filters, market analysis
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_price
  ON property_sales_history(sale_price)
  WHERE sale_price IS NOT NULL;

COMMENT ON INDEX idx_sales_price IS
  'Sale price range queries';

-- =====================================================
-- Index 4: Qualified Sale Filtering
-- Used in: Market analysis (qualified sales only)
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_qualified
  ON property_sales_history(qualified_sale, sale_date DESC)
  WHERE qualified_sale = true;

COMMENT ON INDEX idx_sales_qualified IS
  'Filter for qualified sales with date ordering';

-- =====================================================
-- Index 5: Sale Type
-- Used in: Filtering by sale type (foreclosure, etc)
-- =====================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_type
  ON property_sales_history(sale_type)
  WHERE sale_type IS NOT NULL;

COMMENT ON INDEX idx_sales_type IS
  'Filter by sale type';

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Show all sales history indexes
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
WHERE tablename = 'property_sales_history'
  AND indexname LIKE 'idx_sales_%'
ORDER BY indexname;

-- Check index usage
SELECT
  schemaname,
  tablename,
  indexrelname,
  idx_scan as index_scans,
  idx_tup_read as rows_read
FROM pg_stat_user_indexes
WHERE tablename = 'property_sales_history'
  AND indexrelname LIKE 'idx_sales_%'
ORDER BY idx_scan DESC;

-- Total index size
SELECT
  pg_size_pretty(SUM(pg_relation_size(indexrelid))) as total_index_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
WHERE tablename = 'property_sales_history'
  AND indexname LIKE 'idx_sales_%';

-- =====================================================
-- EXPECTED RESULTS
-- =====================================================
--
-- After running this script:
-- - 5 new indexes on property_sales_history
-- - Total index size: ~50-100 MB
-- - Sales history queries: 2000ms → 100ms (20x faster)
-- =====================================================
