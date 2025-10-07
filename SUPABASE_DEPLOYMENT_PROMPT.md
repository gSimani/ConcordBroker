# SUPABASE DEPLOYMENT PROMPT - FLORIDA DATA AUTOMATION
**Copy everything between the START and END markers below and paste into Supabase SQL Editor**

---

## 📋 PROMPT START (Copy from here)

```
I need you to execute the following SQL migration to set up the Florida Property Data Automation system in our Supabase database.

CONTEXT:
- We are building a fully automated daily ingestion system for all 67 Florida counties
- This system will ingest NAL (Name/Address/Legal), SDF (Sales Data), and NAP (Property Characteristics) files
- We need staging tables, audit tables, file registry for delta detection, and SQL functions
- Our existing tables are `florida_parcels` and `property_sales_history` - we will enhance them, not replace them

REQUIREMENTS:
1. Create all staging tables (nal_staging, sdf_staging, nap_staging)
2. Create audit/monitoring tables (ingestion_runs, file_registry, validation_errors)
3. Add new columns to existing florida_parcels table (data_quality_score, last_validated_at, source_type, ingestion_run_id)
4. Add new columns to existing property_sales_history table (same as above)
5. Create SQL functions for upsert operations (upsert_nal_to_core, get_county_coverage, cleanup_staging_tables)
6. Create views for monitoring (data_quality_dashboard, recent_ingestion_activity)
7. Set up Row Level Security policies for service_role access
8. Create all necessary indexes for performance

CRITICAL NOTES:
- DO NOT drop or truncate existing tables
- Use "ALTER TABLE ... ADD COLUMN IF NOT EXISTS" for existing tables
- Use "CREATE TABLE IF NOT EXISTS" for new tables
- Use "CREATE INDEX IF NOT EXISTS" for all indexes
- Use "CREATE OR REPLACE" for functions and views
- The florida_parcels table has a composite unique constraint on (parcel_id, county, year)
- Preserve all existing data

PLEASE EXECUTE THE FOLLOWING SQL:

-- ============================================================================
-- Florida Property Data Automation - Complete Database Schema
-- Version: 1.0
-- Date: 2025-01-05
-- ============================================================================

-- ============================================================================
-- 1. STAGING TABLES (Raw ingestion before validation)
-- ============================================================================

-- NAL Staging (Name/Address/Legal)
CREATE TABLE IF NOT EXISTS nal_staging (
  id BIGSERIAL PRIMARY KEY,
  county_code INT NOT NULL,
  parcel_id TEXT,
  rs_id TEXT,
  owner_name TEXT,
  owner_addr1 TEXT,
  owner_addr2 TEXT,
  owner_city TEXT,
  owner_state TEXT,
  owner_zip TEXT,
  situs_addr TEXT,
  situs_city TEXT,
  situs_zip TEXT,
  property_use_code TEXT,
  just_value NUMERIC(15,2),
  assessed_value NUMERIC(15,2),
  taxable_value NUMERIC(15,2),
  land_value NUMERIC(15,2),
  building_value NUMERIC(15,2),
  source_file TEXT,
  loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nal_staging_county_parcel ON nal_staging(county_code, parcel_id);
CREATE INDEX IF NOT EXISTS idx_nal_staging_loaded ON nal_staging(loaded_at DESC);

-- SDF Staging (Sales Data File)
CREATE TABLE IF NOT EXISTS sdf_staging (
  id BIGSERIAL PRIMARY KEY,
  county_code INT NOT NULL,
  parcel_id TEXT,
  sale_date DATE,
  sale_price NUMERIC(15,2),
  sale_type TEXT,
  qualified_sale BOOLEAN,
  or_book TEXT,
  or_page TEXT,
  clerk_instrument_number TEXT,
  verification_code TEXT,
  source_file TEXT,
  loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sdf_staging_county_parcel ON sdf_staging(county_code, parcel_id);
CREATE INDEX IF NOT EXISTS idx_sdf_staging_date ON sdf_staging(sale_date DESC);

-- NAP Staging (Property Characteristics)
CREATE TABLE IF NOT EXISTS nap_staging (
  id BIGSERIAL PRIMARY KEY,
  county_code INT NOT NULL,
  parcel_id TEXT,
  bedrooms INT,
  bathrooms INT,
  units INT,
  stories INT,
  year_built INT,
  total_living_area NUMERIC(12,2),
  lot_size_sqft NUMERIC(12,2),
  dor_use_code TEXT,
  land_use_code TEXT,
  source_file TEXT,
  loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nap_staging_county_parcel ON nap_staging(county_code, parcel_id);

-- ============================================================================
-- 2. AUDIT & MONITORING TABLES
-- ============================================================================

-- Ingestion Run Tracking
CREATE TABLE IF NOT EXISTS ingestion_runs (
  id BIGSERIAL PRIMARY KEY,
  run_timestamp TIMESTAMPTZ DEFAULT NOW(),
  source_type TEXT NOT NULL,
  county_code INT,
  file_name TEXT,
  file_size BIGINT,
  file_hash TEXT,
  rows_inserted INT DEFAULT 0,
  rows_updated INT DEFAULT 0,
  rows_failed INT DEFAULT 0,
  duration_seconds NUMERIC(10,2),
  ai_quality_score INT,
  status TEXT DEFAULT 'RUNNING',
  error_message TEXT,
  completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_timestamp ON ingestion_runs(run_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status ON ingestion_runs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_county ON ingestion_runs(county_code);

-- File Registry (Delta Detection via SHA256)
CREATE TABLE IF NOT EXISTS file_registry (
  id BIGSERIAL PRIMARY KEY,
  source_url TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_hash TEXT NOT NULL,
  file_size BIGINT,
  file_type TEXT,
  county_code INT,
  year INT,
  last_modified TIMESTAMPTZ,
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_checked TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(source_url, file_hash)
);

CREATE INDEX IF NOT EXISTS idx_file_registry_url ON file_registry(source_url);
CREATE INDEX IF NOT EXISTS idx_file_registry_hash ON file_registry(file_hash);
CREATE INDEX IF NOT EXISTS idx_file_registry_county ON file_registry(county_code, file_type);

-- Validation Errors
CREATE TABLE IF NOT EXISTS validation_errors (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT REFERENCES ingestion_runs(id) ON DELETE CASCADE,
  county_code INT,
  parcel_id TEXT,
  error_type TEXT NOT NULL,
  error_message TEXT,
  raw_data JSONB,
  severity TEXT DEFAULT 'WARNING',
  detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_validation_errors_run ON validation_errors(run_id);
CREATE INDEX IF NOT EXISTS idx_validation_errors_type ON validation_errors(error_type);
CREATE INDEX IF NOT EXISTS idx_validation_errors_severity ON validation_errors(severity);

-- ============================================================================
-- 3. ENHANCE EXISTING CORE TABLES
-- ============================================================================

-- Add new columns to florida_parcels
DO $$
BEGIN
  -- Add data_quality_score column
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'florida_parcels' AND column_name = 'data_quality_score'
  ) THEN
    ALTER TABLE florida_parcels ADD COLUMN data_quality_score INT DEFAULT 100;
  END IF;

  -- Add last_validated_at column
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'florida_parcels' AND column_name = 'last_validated_at'
  ) THEN
    ALTER TABLE florida_parcels ADD COLUMN last_validated_at TIMESTAMPTZ;
  END IF;

  -- Add source_type column
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'florida_parcels' AND column_name = 'source_type'
  ) THEN
    ALTER TABLE florida_parcels ADD COLUMN source_type TEXT DEFAULT 'DOR';
  END IF;

  -- Add ingestion_run_id column
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'florida_parcels' AND column_name = 'ingestion_run_id'
  ) THEN
    ALTER TABLE florida_parcels ADD COLUMN ingestion_run_id BIGINT REFERENCES ingestion_runs(id);
  END IF;
END $$;

-- Add composite index for core lookups
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_parcel ON florida_parcels(county, parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_quality ON florida_parcels(data_quality_score) WHERE data_quality_score < 80;

-- Add new columns to property_sales_history
DO $$
BEGIN
  -- Add data_quality_score column
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'property_sales_history' AND column_name = 'data_quality_score'
  ) THEN
    ALTER TABLE property_sales_history ADD COLUMN data_quality_score INT DEFAULT 100;
  END IF;

  -- Add source_type column
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'property_sales_history' AND column_name = 'source_type'
  ) THEN
    ALTER TABLE property_sales_history ADD COLUMN source_type TEXT DEFAULT 'DOR';
  END IF;

  -- Add ingestion_run_id column
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'property_sales_history' AND column_name = 'ingestion_run_id'
  ) THEN
    ALTER TABLE property_sales_history ADD COLUMN ingestion_run_id BIGINT REFERENCES ingestion_runs(id);
  END IF;
END $$;

-- ============================================================================
-- 4. FUNCTIONS - Upsert from Staging to Core
-- ============================================================================

-- Function: Upsert NAL staging data into florida_parcels
CREATE OR REPLACE FUNCTION upsert_nal_to_core(p_county_code INT)
RETURNS TABLE(inserted BIGINT, updated BIGINT) AS $$
DECLARE
  v_inserted BIGINT := 0;
  v_updated BIGINT := 0;
  v_county_name TEXT;
BEGIN
  -- Get county name from code
  v_county_name := CASE p_county_code
    WHEN 1 THEN 'ALACHUA'
    WHEN 2 THEN 'BAKER'
    WHEN 3 THEN 'BAY'
    WHEN 4 THEN 'BRADFORD'
    WHEN 5 THEN 'BREVARD'
    WHEN 6 THEN 'BROWARD'
    WHEN 7 THEN 'CALHOUN'
    WHEN 8 THEN 'CHARLOTTE'
    WHEN 9 THEN 'CITRUS'
    WHEN 10 THEN 'CLAY'
    WHEN 11 THEN 'COLLIER'
    WHEN 12 THEN 'COLUMBIA'
    WHEN 13 THEN 'MIAMI-DADE'
    WHEN 16 THEN 'DUVAL'
    WHEN 29 THEN 'HILLSBOROUGH'
    WHEN 48 THEN 'ORANGE'
    WHEN 50 THEN 'PALM BEACH'
    WHEN 52 THEN 'PINELLAS'
    ELSE 'UNKNOWN'
  END;

  -- Upsert from staging to core
  WITH upsert_result AS (
    INSERT INTO florida_parcels (
      county, parcel_id, year, owner_name, phy_addr1, phy_city, phy_zipcd,
      own_name, owner_addr1, owner_city, owner_state, owner_zip,
      just_value, tv_sd, lnd_val, bldg_val,
      property_use, source_type, last_updated_at
    )
    SELECT
      v_county_name,
      s.parcel_id,
      EXTRACT(YEAR FROM NOW())::INT,
      s.owner_name,
      s.situs_addr,
      s.situs_city,
      s.situs_zip,
      s.owner_name,
      s.owner_addr1,
      s.owner_city,
      s.owner_state,
      s.owner_zip,
      s.just_value,
      s.taxable_value,
      s.land_value,
      s.building_value,
      s.property_use_code,
      'DOR',
      NOW()
    FROM nal_staging s
    WHERE s.county_code = p_county_code
      AND s.parcel_id IS NOT NULL
      AND s.parcel_id != ''
    ON CONFLICT (parcel_id, county, year) DO UPDATE SET
      owner_name = EXCLUDED.owner_name,
      phy_addr1 = EXCLUDED.phy_addr1,
      phy_city = EXCLUDED.phy_city,
      phy_zipcd = EXCLUDED.phy_zipcd,
      own_name = EXCLUDED.own_name,
      owner_addr1 = EXCLUDED.owner_addr1,
      owner_city = EXCLUDED.owner_city,
      owner_state = EXCLUDED.owner_state,
      owner_zip = EXCLUDED.owner_zip,
      just_value = EXCLUDED.just_value,
      tv_sd = EXCLUDED.tv_sd,
      lnd_val = EXCLUDED.lnd_val,
      bldg_val = EXCLUDED.bldg_val,
      property_use = EXCLUDED.property_use,
      last_updated_at = NOW()
    RETURNING (xmax = 0) AS was_inserted
  )
  SELECT
    COUNT(*) FILTER (WHERE was_inserted) INTO v_inserted,
    COUNT(*) FILTER (WHERE NOT was_inserted) INTO v_updated
  FROM upsert_result;

  RETURN QUERY SELECT v_inserted, v_updated;
END;
$$ LANGUAGE plpgsql;

-- Function: Get county coverage statistics
CREATE OR REPLACE FUNCTION get_county_coverage()
RETURNS TABLE(
  county_code INT,
  county_name TEXT,
  total_parcels BIGINT,
  with_sales BIGINT,
  with_characteristics BIGINT,
  avg_quality_score NUMERIC,
  last_updated TIMESTAMPTZ,
  coverage_percent NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  WITH county_stats AS (
    SELECT
      CASE p.county
        WHEN 'ALACHUA' THEN 1
        WHEN 'BROWARD' THEN 6
        WHEN 'MIAMI-DADE' THEN 13
        WHEN 'DUVAL' THEN 16
        WHEN 'HILLSBOROUGH' THEN 29
        WHEN 'ORANGE' THEN 48
        WHEN 'PALM BEACH' THEN 50
        WHEN 'PINELLAS' THEN 52
        ELSE 0
      END AS code,
      p.county AS name,
      COUNT(p.id) AS total,
      COUNT(s.id) AS sales,
      COUNT(CASE WHEN p.bedrooms IS NOT NULL THEN 1 END) AS characteristics,
      ROUND(AVG(p.data_quality_score), 0) AS avg_score,
      MAX(p.last_updated_at) AS updated
    FROM florida_parcels p
    LEFT JOIN property_sales_history s ON s.county = p.county AND s.parcel_id = p.parcel_id
    GROUP BY p.county
  )
  SELECT
    cs.code::INT,
    cs.name::TEXT,
    cs.total::BIGINT,
    cs.sales::BIGINT,
    cs.characteristics::BIGINT,
    cs.avg_score::NUMERIC,
    cs.updated::TIMESTAMPTZ,
    ROUND(
      (cs.characteristics::NUMERIC / NULLIF(cs.total, 0)::NUMERIC) * 100,
      2
    )::NUMERIC AS coverage_percent
  FROM county_stats cs
  WHERE cs.code > 0
  ORDER BY cs.code;
END;
$$ LANGUAGE plpgsql;

-- Function: Clean old staging data
CREATE OR REPLACE FUNCTION cleanup_staging_tables(days_to_keep INT DEFAULT 7)
RETURNS TABLE(nal_deleted BIGINT, sdf_deleted BIGINT, nap_deleted BIGINT) AS $$
DECLARE
  v_nal_deleted BIGINT;
  v_sdf_deleted BIGINT;
  v_nap_deleted BIGINT;
BEGIN
  DELETE FROM nal_staging WHERE loaded_at < NOW() - (days_to_keep || ' days')::INTERVAL;
  GET DIAGNOSTICS v_nal_deleted = ROW_COUNT;

  DELETE FROM sdf_staging WHERE loaded_at < NOW() - (days_to_keep || ' days')::INTERVAL;
  GET DIAGNOSTICS v_sdf_deleted = ROW_COUNT;

  DELETE FROM nap_staging WHERE loaded_at < NOW() - (days_to_keep || ' days')::INTERVAL;
  GET DIAGNOSTICS v_nap_deleted = ROW_COUNT;

  RETURN QUERY SELECT v_nal_deleted, v_sdf_deleted, v_nap_deleted;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. VIEWS - Quick Data Quality Insights
-- ============================================================================

-- View: Data quality dashboard
CREATE OR REPLACE VIEW data_quality_dashboard AS
SELECT
  county,
  COUNT(*) AS total_parcels,
  COUNT(CASE WHEN bedrooms IS NOT NULL THEN 1 END) AS with_bedrooms,
  COUNT(CASE WHEN year_built IS NOT NULL THEN 1 END) AS with_year_built,
  COUNT(CASE WHEN data_quality_score >= 80 THEN 1 END) AS high_quality,
  COUNT(CASE WHEN data_quality_score < 50 THEN 1 END) AS low_quality,
  ROUND(AVG(data_quality_score), 2) AS avg_quality_score,
  MAX(last_updated_at) AS last_updated
FROM florida_parcels
GROUP BY county
ORDER BY county;

-- View: Recent ingestion activity
CREATE OR REPLACE VIEW recent_ingestion_activity AS
SELECT
  ir.id,
  ir.run_timestamp,
  ir.source_type,
  ir.county_code,
  CASE ir.county_code
    WHEN 6 THEN 'BROWARD'
    WHEN 13 THEN 'MIAMI-DADE'
    WHEN 16 THEN 'DUVAL'
    WHEN 29 THEN 'HILLSBOROUGH'
    WHEN 48 THEN 'ORANGE'
    WHEN 50 THEN 'PALM BEACH'
    WHEN 52 THEN 'PINELLAS'
    ELSE 'UNKNOWN'
  END AS county_name,
  ir.file_name,
  ir.rows_inserted,
  ir.rows_updated,
  ir.rows_failed,
  ir.duration_seconds,
  ir.ai_quality_score,
  ir.status,
  COUNT(ve.id) AS validation_errors
FROM ingestion_runs ir
LEFT JOIN validation_errors ve ON ve.run_id = ir.id
GROUP BY ir.id
ORDER BY ir.run_timestamp DESC
LIMIT 50;

-- ============================================================================
-- 6. ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on audit tables
ALTER TABLE ingestion_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_errors ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Service role can access ingestion_runs" ON ingestion_runs;
DROP POLICY IF EXISTS "Service role can access file_registry" ON file_registry;
DROP POLICY IF EXISTS "Service role can access validation_errors" ON validation_errors;
DROP POLICY IF EXISTS "Authenticated users can read ingestion_runs" ON ingestion_runs;

-- Create policies
CREATE POLICY "Service role can access ingestion_runs"
  ON ingestion_runs FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access file_registry"
  ON file_registry FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access validation_errors"
  ON validation_errors FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Authenticated users can read ingestion_runs"
  ON ingestion_runs FOR SELECT
  USING (auth.role() = 'authenticated');

-- ============================================================================
-- 7. FINAL OPTIMIZATION
-- ============================================================================

ANALYZE nal_staging;
ANALYZE sdf_staging;
ANALYZE nap_staging;
ANALYZE ingestion_runs;
ANALYZE file_registry;
ANALYZE validation_errors;
ANALYZE florida_parcels;
ANALYZE property_sales_history;

-- ============================================================================
-- MIGRATION COMPLETE - Report Results
-- ============================================================================

SELECT
  'Migration completed successfully!' AS status,
  (SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('nal_staging', 'sdf_staging', 'nap_staging', 'ingestion_runs', 'file_registry', 'validation_errors')) AS tables_created,
  (SELECT COUNT(*) FROM information_schema.routines WHERE routine_name IN ('upsert_nal_to_core', 'get_county_coverage', 'cleanup_staging_tables')) AS functions_created,
  (SELECT COUNT(*) FROM information_schema.views WHERE table_name IN ('data_quality_dashboard', 'recent_ingestion_activity')) AS views_created;
```

AFTER EXECUTION:
1. Confirm all tables were created (should show 6 tables)
2. Confirm all functions were created (should show 3 functions)
3. Confirm all views were created (should show 2 views)
4. Run this test query to verify everything works:

```sql
-- Test query to verify setup
SELECT * FROM data_quality_dashboard LIMIT 5;
SELECT * FROM get_county_coverage();
SELECT COUNT(*) FROM ingestion_runs;
SELECT COUNT(*) FROM file_registry;
```

If you see any errors, please share them so I can help troubleshoot.
```

## 📋 PROMPT END (Stop copying here)

---

## ✅ VERIFICATION STEPS

After Supabase executes the migration, you should see:

### Expected Output:
```
status: "Migration completed successfully!"
tables_created: 6
functions_created: 3
views_created: 2
```

### Tables Created:
1. ✅ `nal_staging`
2. ✅ `sdf_staging`
3. ✅ `nap_staging`
4. ✅ `ingestion_runs`
5. ✅ `file_registry`
6. ✅ `validation_errors`

### Functions Created:
1. ✅ `upsert_nal_to_core(county_code)`
2. ✅ `get_county_coverage()`
3. ✅ `cleanup_staging_tables(days_to_keep)`

### Views Created:
1. ✅ `data_quality_dashboard`
2. ✅ `recent_ingestion_activity`

### Existing Tables Enhanced:
1. ✅ `florida_parcels` (+ 4 new columns)
2. ✅ `property_sales_history` (+ 3 new columns)

---

## 🔧 POST-MIGRATION TESTING

Run these queries in Supabase SQL Editor to verify:

```sql
-- 1. Check staging tables exist
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('nal_staging', 'sdf_staging', 'nap_staging');

-- 2. Check audit tables exist
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('ingestion_runs', 'file_registry', 'validation_errors');

-- 3. Test coverage function
SELECT * FROM get_county_coverage();

-- 4. Check new columns in florida_parcels
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'florida_parcels'
  AND column_name IN ('data_quality_score', 'last_validated_at', 'source_type', 'ingestion_run_id');

-- 5. View data quality dashboard
SELECT * FROM data_quality_dashboard LIMIT 10;
```

---

## 🚨 TROUBLESHOOTING

If you see any errors:

### Error: "relation already exists"
- This is OK! The migration uses `CREATE TABLE IF NOT EXISTS`
- Continue with the rest of the migration

### Error: "column already exists"
- This is OK! The migration uses `IF NOT EXISTS` checks
- Continue with the rest of the migration

### Error: "permission denied"
- Make sure you're using the Supabase SQL Editor with service_role permissions
- Or use the "service_role" key in your API calls

### Error: "function does not exist"
- The functions should be created by the migration
- Check if you have permissions to create functions
- Try running the function creation statements separately

---

## 📝 NEXT STEPS AFTER MIGRATION

1. ✅ Verify all tables/functions/views created
2. ✅ Test the coverage function returns data
3. ✅ Check the dashboard view shows your counties
4. ✅ Create the Supabase Storage bucket:
   - Go to Supabase Dashboard → Storage
   - Create bucket: `florida-property-data`
   - Set to Private
5. ✅ Deploy the Python orchestrator to Railway
6. ✅ Test manual ingestion trigger

---

**Document Version**: 1.0
**Last Updated**: 2025-01-05
**Status**: ✅ READY TO EXECUTE
