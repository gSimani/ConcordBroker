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
  source_type TEXT NOT NULL, -- 'DOR', 'COUNTY_PA', 'FGIO', 'ORCHESTRATOR'
  county_code INT,
  file_name TEXT,
  file_size BIGINT,
  file_hash TEXT,
  rows_inserted INT DEFAULT 0,
  rows_updated INT DEFAULT 0,
  rows_failed INT DEFAULT 0,
  duration_seconds NUMERIC(10,2),
  ai_quality_score INT,
  status TEXT DEFAULT 'RUNNING', -- 'RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED'
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
  file_hash TEXT NOT NULL, -- SHA256
  file_size BIGINT,
  file_type TEXT, -- 'NAL', 'SDF', 'NAP', 'FGIO'
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
  severity TEXT DEFAULT 'WARNING', -- 'WARNING', 'ERROR', 'CRITICAL'
  detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_validation_errors_run ON validation_errors(run_id);
CREATE INDEX IF NOT EXISTS idx_validation_errors_type ON validation_errors(error_type);
CREATE INDEX IF NOT EXISTS idx_validation_errors_severity ON validation_errors(severity);

-- ============================================================================
-- 3. CORE PRODUCTION TABLES (Validated, Deduplicated)
-- ============================================================================

-- Note: florida_parcels already exists, so we'll add missing columns and indexes

-- Add missing columns to florida_parcels if they don't exist
ALTER TABLE florida_parcels
  ADD COLUMN IF NOT EXISTS data_quality_score INT DEFAULT 100,
  ADD COLUMN IF NOT EXISTS last_validated_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'DOR', -- 'DOR', 'COUNTY_PA', 'MANUAL'
  ADD COLUMN IF NOT EXISTS ingestion_run_id BIGINT REFERENCES ingestion_runs(id);

-- Add composite index for core lookups
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_parcel ON florida_parcels(county, parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_quality ON florida_parcels(data_quality_score) WHERE data_quality_score < 80;

-- property_sales_history already exists, add missing columns
ALTER TABLE property_sales_history
  ADD COLUMN IF NOT EXISTS data_quality_score INT DEFAULT 100,
  ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'DOR',
  ADD COLUMN IF NOT EXISTS ingestion_run_id BIGINT REFERENCES ingestion_runs(id);

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
  -- Get county name
  SELECT CASE p_county_code
    WHEN 1 THEN 'ALACHUA'
    WHEN 6 THEN 'BROWARD'
    WHEN 13 THEN 'MIAMI-DADE'
    WHEN 16 THEN 'DUVAL'
    -- ... all 67 counties
    ELSE 'UNKNOWN'
  END INTO v_county_name;

  -- Upsert from staging to core
  WITH upsert_result AS (
    INSERT INTO florida_parcels (
      county, parcel_id, owner_name, phy_addr1, phy_city, phy_zipcd,
      own_name, owner_addr1, owner_city, owner_state, owner_zip,
      just_value, tv_sd, lnd_val, bldg_val,
      property_use, source_type, last_updated_at
    )
    SELECT
      v_county_name,
      s.parcel_id,
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
  WITH county_codes AS (
    SELECT
      1 AS code, 'ALACHUA' AS name UNION ALL
    SELECT 6, 'BROWARD' UNION ALL
    SELECT 13, 'MIAMI-DADE' UNION ALL
    SELECT 16, 'DUVAL'
    -- ... all 67 counties
  )
  SELECT
    cc.code AS county_code,
    cc.name AS county_name,
    COUNT(p.id)::BIGINT AS total_parcels,
    COUNT(s.id)::BIGINT AS with_sales,
    COUNT(CASE WHEN p.bedrooms IS NOT NULL THEN 1 END)::BIGINT AS with_characteristics,
    ROUND(AVG(p.data_quality_score), 0)::NUMERIC AS avg_quality_score,
    MAX(p.last_updated_at) AS last_updated,
    ROUND(
      (COUNT(CASE WHEN p.bedrooms IS NOT NULL AND s.id IS NOT NULL THEN 1 END)::NUMERIC / NULLIF(COUNT(p.id), 0)::NUMERIC) * 100,
      2
    ) AS coverage_percent
  FROM county_codes cc
  LEFT JOIN florida_parcels p ON p.county = cc.name
  LEFT JOIN property_sales_history s ON s.county = cc.name AND s.parcel_id = p.parcel_id
  GROUP BY cc.code, cc.name
  ORDER BY cc.code;
END;
$$ LANGUAGE plpgsql;

-- Function: Clean old staging data (run after successful ingestion)
CREATE OR REPLACE FUNCTION cleanup_staging_tables(days_to_keep INT DEFAULT 7)
RETURNS TABLE(nal_deleted BIGINT, sdf_deleted BIGINT, nap_deleted BIGINT) AS $$
DECLARE
  v_nal_deleted BIGINT;
  v_sdf_deleted BIGINT;
  v_nap_deleted BIGINT;
BEGIN
  -- Delete old NAL staging records
  DELETE FROM nal_staging
  WHERE loaded_at < NOW() - (days_to_keep || ' days')::INTERVAL;
  GET DIAGNOSTICS v_nal_deleted = ROW_COUNT;

  -- Delete old SDF staging records
  DELETE FROM sdf_staging
  WHERE loaded_at < NOW() - (days_to_keep || ' days')::INTERVAL;
  GET DIAGNOSTICS v_sdf_deleted = ROW_COUNT;

  -- Delete old NAP staging records
  DELETE FROM nap_staging
  WHERE loaded_at < NOW() - (days_to_keep || ' days')::INTERVAL;
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
-- 6. STORAGE BUCKETS (Supabase Storage)
-- ============================================================================

-- Create storage bucket for raw files (if not exists)
-- Run this via Supabase Dashboard or API:
-- INSERT INTO storage.buckets (id, name, public) VALUES ('florida-property-data', 'florida-property-data', false);

-- ============================================================================
-- 7. ROW LEVEL SECURITY (Optional - for multi-tenant access)
-- ============================================================================

-- Enable RLS on audit tables (allow service_role full access)
ALTER TABLE ingestion_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_errors ENABLE ROW LEVEL SECURITY;

-- Policy: Allow service_role full access
CREATE POLICY IF NOT EXISTS "Service role can access ingestion_runs"
  ON ingestion_runs FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS "Service role can access file_registry"
  ON file_registry FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS "Service role can access validation_errors"
  ON validation_errors FOR ALL
  USING (auth.role() = 'service_role');

-- Policy: Allow authenticated users read access to monitoring views
CREATE POLICY IF NOT EXISTS "Authenticated users can read ingestion_runs"
  ON ingestion_runs FOR SELECT
  USING (auth.role() = 'authenticated');

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Run final optimization
ANALYZE nal_staging;
ANALYZE sdf_staging;
ANALYZE nap_staging;
ANALYZE ingestion_runs;
ANALYZE file_registry;
ANALYZE validation_errors;
ANALYZE florida_parcels;
ANALYZE property_sales_history;
