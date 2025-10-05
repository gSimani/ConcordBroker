-- ============================================================================
-- CRITICAL FIX: upsert_nal_to_core Function
-- Issue: Column name mismatches between migration and actual schema
-- Date: 2025-10-05
-- ============================================================================

-- Drop existing broken function
DROP FUNCTION IF EXISTS upsert_nal_to_core(INT);

-- Create corrected function with proper column names
CREATE OR REPLACE FUNCTION upsert_nal_to_core(p_county_code INT)
RETURNS TABLE(inserted BIGINT, updated BIGINT) AS $$
DECLARE
  v_inserted BIGINT := 0;
  v_updated BIGINT := 0;
  v_county_name TEXT;
  v_year INT := EXTRACT(YEAR FROM CURRENT_DATE);
BEGIN
  -- Map county code to county name (all 67 Florida counties)
  SELECT CASE p_county_code
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
    WHEN 14 THEN 'DESOTO'
    WHEN 15 THEN 'DIXIE'
    WHEN 16 THEN 'DUVAL'
    WHEN 17 THEN 'ESCAMBIA'
    WHEN 18 THEN 'FLAGLER'
    WHEN 19 THEN 'FRANKLIN'
    WHEN 20 THEN 'GADSDEN'
    WHEN 21 THEN 'GILCHRIST'
    WHEN 22 THEN 'GLADES'
    WHEN 23 THEN 'GULF'
    WHEN 24 THEN 'HAMILTON'
    WHEN 25 THEN 'HARDEE'
    WHEN 26 THEN 'HENDRY'
    WHEN 27 THEN 'HERNANDO'
    WHEN 28 THEN 'HIGHLANDS'
    WHEN 29 THEN 'HILLSBOROUGH'
    WHEN 30 THEN 'HOLMES'
    WHEN 31 THEN 'INDIAN RIVER'
    WHEN 32 THEN 'JACKSON'
    WHEN 33 THEN 'JEFFERSON'
    WHEN 34 THEN 'LAFAYETTE'
    WHEN 35 THEN 'LAKE'
    WHEN 36 THEN 'LEE'
    WHEN 37 THEN 'LEON'
    WHEN 38 THEN 'LEVY'
    WHEN 39 THEN 'LIBERTY'
    WHEN 40 THEN 'MADISON'
    WHEN 41 THEN 'MANATEE'
    WHEN 42 THEN 'MARION'
    WHEN 43 THEN 'MARTIN'
    WHEN 44 THEN 'MONROE'
    WHEN 45 THEN 'NASSAU'
    WHEN 46 THEN 'OKALOOSA'
    WHEN 47 THEN 'OKEECHOBEE'
    WHEN 48 THEN 'ORANGE'
    WHEN 49 THEN 'OSCEOLA'
    WHEN 50 THEN 'PALM BEACH'
    WHEN 51 THEN 'PASCO'
    WHEN 52 THEN 'PINELLAS'
    WHEN 53 THEN 'POLK'
    WHEN 54 THEN 'PUTNAM'
    WHEN 55 THEN 'SANTA ROSA'
    WHEN 56 THEN 'SARASOTA'
    WHEN 57 THEN 'SEMINOLE'
    WHEN 58 THEN 'ST JOHNS'
    WHEN 59 THEN 'ST LUCIE'
    WHEN 60 THEN 'SUMTER'
    WHEN 61 THEN 'SUWANNEE'
    WHEN 62 THEN 'TAYLOR'
    WHEN 63 THEN 'UNION'
    WHEN 64 THEN 'VOLUSIA'
    WHEN 65 THEN 'WAKULLA'
    WHEN 66 THEN 'WALTON'
    WHEN 67 THEN 'WASHINGTON'
    ELSE 'UNKNOWN'
  END INTO v_county_name;

  -- Upsert from nal_staging to florida_parcels
  WITH upsert_result AS (
    INSERT INTO florida_parcels (
      parcel_id,
      county,
      year,
      owner_name,
      owner_addr1,
      owner_addr2,
      owner_city,
      owner_state,
      owner_zip,
      phy_addr1,
      phy_city,
      phy_zipcd,
      just_value,
      taxable_value,
      land_value,
      building_value,
      property_use,
      source_type,
      last_validated_at,
      data_quality_score
    )
    SELECT
      s.parcel_id,
      v_county_name,
      v_year,
      s.owner_name,
      COALESCE(s.owner_addr1, ''),
      '',  -- owner_addr2 not in NAL files
      COALESCE(s.owner_city, ''),
      COALESCE(s.owner_state, ''),
      COALESCE(s.owner_zip, ''),
      COALESCE(s.situs_addr, ''),
      COALESCE(s.situs_city, ''),
      COALESCE(s.situs_zip, ''),
      COALESCE(s.just_value, 0),
      COALESCE(s.taxable_value, 0),
      COALESCE(s.land_value, 0),
      COALESCE(s.building_value, 0),
      COALESCE(s.property_use_code, ''),
      'DOR',
      NOW(),
      100  -- Default quality score, will be updated by AI validation
    FROM nal_staging s
    WHERE s.county_code = p_county_code
      AND s.parcel_id IS NOT NULL
      AND s.parcel_id != ''
      AND LENGTH(TRIM(s.parcel_id)) > 0
    ON CONFLICT (parcel_id, county, year) DO UPDATE SET
      owner_name = EXCLUDED.owner_name,
      owner_addr1 = EXCLUDED.owner_addr1,
      owner_city = EXCLUDED.owner_city,
      owner_state = EXCLUDED.owner_state,
      owner_zip = EXCLUDED.owner_zip,
      phy_addr1 = EXCLUDED.phy_addr1,
      phy_city = EXCLUDED.phy_city,
      phy_zipcd = EXCLUDED.phy_zipcd,
      just_value = EXCLUDED.just_value,
      taxable_value = EXCLUDED.taxable_value,
      land_value = EXCLUDED.land_value,
      building_value = EXCLUDED.building_value,
      property_use = EXCLUDED.property_use,
      last_validated_at = NOW(),
      update_date = NOW()
    RETURNING (xmax = 0) AS was_inserted
  )
  SELECT
    COUNT(*) FILTER (WHERE was_inserted) INTO v_inserted,
    COUNT(*) FILTER (WHERE NOT was_inserted) INTO v_updated
  FROM upsert_result;

  RETURN QUERY SELECT v_inserted, v_updated;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION upsert_nal_to_core(INT) TO service_role;
GRANT EXECUTE ON FUNCTION upsert_nal_to_core(INT) TO authenticated;

-- Test function (should return 0 inserted, 0 updated since staging is empty)
SELECT * FROM upsert_nal_to_core(6);

-- Verify function
\df upsert_nal_to_core
