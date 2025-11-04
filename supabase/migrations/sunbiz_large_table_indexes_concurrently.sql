-- Sunbiz Large Table Indexes (CONCURRENTLY)
-- Run via: psql -f sunbiz_large_table_indexes_concurrently.sql
-- Requires: Direct database connection (not SQL editor)
-- Purpose: Create performance indexes on 2M+ row tables without blocking
--
-- IMPORTANT: Do NOT run this inside a transaction (no BEGIN/COMMIT)
-- Each CREATE INDEX CONCURRENTLY must run in autocommit mode
--
-- Run via psql:
--   psql "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" -f sunbiz_large_table_indexes_concurrently.sql

-- sunbiz_corporate (2M+ rows) - Core entity table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_doc_number
  ON public.sunbiz_corporate(doc_number);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_entity_name
  ON public.sunbiz_corporate(entity_name);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_filing_date
  ON public.sunbiz_corporate(filing_date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_updated_at
  ON public.sunbiz_corporate(updated_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_source_file
  ON public.sunbiz_corporate(source_file);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_status
  ON public.sunbiz_corporate(status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corporate_subtype
  ON public.sunbiz_corporate(subtype);

-- sunbiz_corporate_events (recommended for lookups and deduplication)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corp_events_doc_number
  ON public.sunbiz_corporate_events(doc_number);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corp_events_event_date
  ON public.sunbiz_corporate_events(event_date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_corp_events_event_type
  ON public.sunbiz_corporate_events(event_type);

-- Verify indexes created:
-- SELECT schemaname, tablename, indexname
-- FROM pg_indexes
-- WHERE tablename IN ('sunbiz_corporate', 'sunbiz_corporate_events')
-- ORDER BY tablename, indexname;

-- Check index status (useful if CONCURRENTLY was interrupted):
-- SELECT schemaname, tablename, indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename IN ('sunbiz_corporate', 'sunbiz_corporate_events')
--   AND indexname LIKE 'idx_sunbiz_%'
-- ORDER BY tablename, indexname;

-- Expected output after running:
-- ✓ 7 indexes on sunbiz_corporate
-- ✓ 3 indexes on sunbiz_corporate_events
-- ✓ All created without locking tables
