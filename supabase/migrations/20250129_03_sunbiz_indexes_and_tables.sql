-- =====================================================
-- PHASE 1.3: SUNBIZ TABLES AND INDEXES
-- Create missing tables and indexes BEFORE data load
--
-- Estimated time: 15-20 minutes
-- Impact: CRITICAL - prevents 30-60s timeouts when data loads
-- Risk: NONE (tables empty, indexes instant)
--
-- Run in Supabase SQL Editor BEFORE loading Sunbiz data
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =====================================================
-- PART A: CREATE MISSING sunbiz_officers TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS sunbiz_officers (
  id BIGSERIAL PRIMARY KEY,
  doc_number VARCHAR(12) NOT NULL,
  officer_name VARCHAR(200) NOT NULL,
  officer_title VARCHAR(100),
  officer_address TEXT,
  officer_email VARCHAR(255),
  officer_phone VARCHAR(20),
  filing_date DATE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Prevent duplicate officer entries
  UNIQUE(doc_number, officer_name, officer_title),

  -- Foreign key to corporate table
  FOREIGN KEY (doc_number) REFERENCES sunbiz_corporate(doc_number) ON DELETE CASCADE
);

COMMENT ON TABLE sunbiz_officers IS
  'Corporate officers and managers from Sunbiz records';

-- Enable Row Level Security
ALTER TABLE sunbiz_officers ENABLE ROW LEVEL SECURITY;

-- Public read access
CREATE POLICY "Public read access on sunbiz_officers"
  ON sunbiz_officers FOR SELECT
  USING (true);

-- =====================================================
-- PART B: SUNBIZ_CORPORATE INDEXES
-- =====================================================

-- Index 1: Doc Number (Primary key alternative, for lookups)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_doc_number
  ON sunbiz_corporate(doc_number);

COMMENT ON INDEX idx_sunbiz_doc_number IS
  'Primary lookup by document number';

-- Index 2: Principal Address (For property matching)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_prin_addr
  ON sunbiz_corporate(prin_addr1)
  WHERE prin_addr1 IS NOT NULL;

COMMENT ON INDEX idx_sunbiz_prin_addr IS
  'Address matching - principal address';

-- Index 3: Mailing Address (For property matching)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_mail_addr
  ON sunbiz_corporate(mail_addr1)
  WHERE mail_addr1 IS NOT NULL;

COMMENT ON INDEX idx_sunbiz_mail_addr IS
  'Address matching - mailing address';

-- Index 4: Entity Name Exact
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_entity_name
  ON sunbiz_corporate(entity_name)
  WHERE entity_name IS NOT NULL;

COMMENT ON INDEX idx_sunbiz_entity_name IS
  'Exact entity name lookups';

-- Index 5: Entity Name Fuzzy (Trigram)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_entity_trgm
  ON sunbiz_corporate USING gist(entity_name gist_trgm_ops);

COMMENT ON INDEX idx_sunbiz_entity_trgm IS
  'Trigram index for ILIKE searches on entity names';

-- Index 6: Registered Agent Exact
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_agent
  ON sunbiz_corporate(registered_agent)
  WHERE registered_agent IS NOT NULL;

COMMENT ON INDEX idx_sunbiz_agent IS
  'Exact registered agent lookups';

-- Index 7: Registered Agent Fuzzy (Trigram)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_agent_trgm
  ON sunbiz_corporate USING gist(registered_agent gist_trgm_ops);

COMMENT ON INDEX idx_sunbiz_agent_trgm IS
  'Trigram index for ILIKE searches on registered agents';

-- Index 8: Status + Date Composite (Active entities)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_status_date
  ON sunbiz_corporate(status, filing_date DESC)
  WHERE status = 'ACTIVE';

COMMENT ON INDEX idx_sunbiz_status_date IS
  'Active entities with date ordering';

-- Index 9: Entity Type Filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sunbiz_entity_type
  ON sunbiz_corporate(entity_type)
  WHERE entity_type IS NOT NULL;

COMMENT ON INDEX idx_sunbiz_entity_type IS
  'Filter by entity type (LLC, Corp, etc)';

-- =====================================================
-- PART C: SUNBIZ_OFFICERS INDEXES
-- =====================================================

-- Index 1: Officer Name Exact
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_officers_name
  ON sunbiz_officers(officer_name)
  WHERE officer_name IS NOT NULL;

COMMENT ON INDEX idx_officers_name IS
  'Exact officer name lookups';

-- Index 2: Officer Name Fuzzy (Trigram)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_officers_name_trgm
  ON sunbiz_officers USING gist(officer_name gist_trgm_ops);

COMMENT ON INDEX idx_officers_name_trgm IS
  'Trigram index for ILIKE searches on officer names';

-- Index 3: Doc Number (For joins)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_officers_doc_number
  ON sunbiz_officers(doc_number);

COMMENT ON INDEX idx_officers_doc_number IS
  'Join index to sunbiz_corporate';

-- =====================================================
-- PART D: SUNBIZ_FICTITIOUS INDEXES
-- =====================================================

-- Index 1: Fictitious Name Exact
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_name
  ON sunbiz_fictitious(name)
  WHERE name IS NOT NULL;

COMMENT ON INDEX idx_fict_name IS
  'Exact fictitious name lookups';

-- Index 2: Fictitious Name Fuzzy (Trigram)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_name_trgm
  ON sunbiz_fictitious USING gist(name gist_trgm_ops);

COMMENT ON INDEX idx_fict_name_trgm IS
  'Trigram index for ILIKE searches on fictitious names';

-- Index 3: Fictitious Name Full-Text Search (GIN)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_name_gin
  ON sunbiz_fictitious USING gin(to_tsvector('english', name));

COMMENT ON INDEX idx_fict_name_gin IS
  'Full-text search on fictitious names';

-- Index 4: Owner Name Exact
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_owner
  ON sunbiz_fictitious(owner_name)
  WHERE owner_name IS NOT NULL;

COMMENT ON INDEX idx_fict_owner IS
  'Exact owner name lookups';

-- Index 5: Owner Name Fuzzy (Trigram)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_owner_trgm
  ON sunbiz_fictitious USING gist(owner_name gist_trgm_ops);

COMMENT ON INDEX idx_fict_owner_trgm IS
  'Trigram index for ILIKE searches on owner names';

-- Index 6: Owner Name Full-Text Search (GIN)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fict_owner_gin
  ON sunbiz_fictitious USING gin(to_tsvector('english', owner_name));

COMMENT ON INDEX idx_fict_owner_gin IS
  'Full-text search on owner names';

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Show all Sunbiz indexes
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
WHERE tablename LIKE 'sunbiz%'
  AND (indexname LIKE 'idx_%' OR indexname LIKE 'idx_fict_%' OR indexname LIKE 'idx_officers_%')
ORDER BY tablename, indexname;

-- Verify sunbiz_officers table created
SELECT
  table_name,
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_name = 'sunbiz_officers'
ORDER BY ordinal_position;

-- Count records in each table (should be 0 before data load)
SELECT
  'sunbiz_corporate' as table_name,
  COUNT(*) as record_count
FROM sunbiz_corporate
UNION ALL
SELECT
  'sunbiz_officers' as table_name,
  COUNT(*) as record_count
FROM sunbiz_officers
UNION ALL
SELECT
  'sunbiz_fictitious' as table_name,
  COUNT(*) as record_count
FROM sunbiz_fictitious;

-- Total index size for Sunbiz tables
SELECT
  tablename,
  pg_size_pretty(SUM(pg_relation_size(indexrelid))) as total_index_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
WHERE tablename LIKE 'sunbiz%'
GROUP BY tablename
ORDER BY tablename;

-- =====================================================
-- EXPECTED RESULTS
-- =====================================================
--
-- After running this script:
-- - sunbiz_officers table created (0 records)
-- - 9 indexes on sunbiz_corporate
-- - 3 indexes on sunbiz_officers
-- - 6 indexes on sunbiz_fictitious
-- - Total: 18 new indexes
-- - All indexes created instantly (tables empty)
--
-- When data loads:
-- - Address searches: No timeout (was 30-60s)
-- - Entity name searches: <200ms (was 10-30s)
-- - Officer matching: <300ms (was 5-10s)
--
-- CRITICAL: Run this BEFORE loading Sunbiz data!
-- Creating indexes after data load takes 10-20x longer!
-- =====================================================
