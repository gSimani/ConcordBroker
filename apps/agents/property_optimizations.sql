-- PERFORMANCE INDEXES
-- These indexes will significantly improve query performance

CREATE INDEX IF NOT EXISTS idx_properties_parcel_id
ON properties (parcel_id);

CREATE INDEX IF NOT EXISTS idx_properties_owner_name
ON properties (owner_name);

CREATE INDEX IF NOT EXISTS idx_properties_address
ON properties (address);

CREATE INDEX IF NOT EXISTS idx_properties_city
ON properties (city);

CREATE INDEX IF NOT EXISTS idx_properties_zip_code
ON properties (zip_code);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id
ON florida_parcels (parcel_id);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name
ON florida_parcels (owner_name);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_city
ON florida_parcels (phy_city);

CREATE INDEX IF NOT EXISTS idx_property_sales_history_parcel_id
ON property_sales_history (parcel_id);

CREATE INDEX IF NOT EXISTS idx_property_sales_history_sale_date
ON property_sales_history (sale_date);

CREATE INDEX IF NOT EXISTS idx_property_sales_history_sale_price
ON property_sales_history (sale_price);

CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_entity_name
ON sunbiz_corporate (entity_name);

CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_principal_address
ON sunbiz_corporate (principal_address);

CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_status
ON sunbiz_corporate (status);

-- COMPOSITE INDEXES FOR COMMON QUERIES
CREATE INDEX IF NOT EXISTS idx_properties_search
ON properties (city, property_type, assessed_value);

CREATE INDEX IF NOT EXISTS idx_sales_history_lookup
ON property_sales_history (parcel_id, sale_date DESC);

-- MATERIALIZED VIEW FOR LATEST SALES
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_property_sales AS
SELECT DISTINCT ON (parcel_id)
  parcel_id,
  sale_date,
  sale_price,
  qual_code,
  or_book,
  or_page
FROM property_sales_history
ORDER BY parcel_id, sale_date DESC;

CREATE UNIQUE INDEX ON latest_property_sales (parcel_id);

-- FUNCTION FOR EFFICIENT PROPERTY SEARCH
CREATE OR REPLACE FUNCTION search_properties(
  search_text TEXT DEFAULT NULL,
  search_city TEXT DEFAULT NULL,
  min_price NUMERIC DEFAULT NULL,
  max_price NUMERIC DEFAULT NULL,
  property_types TEXT[] DEFAULT NULL,
  result_limit INT DEFAULT 20,
  result_offset INT DEFAULT 0
) RETURNS TABLE (
  parcel_id TEXT,
  owner_name TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip_code TEXT,
  property_type TEXT,
  assessed_value NUMERIC,
  last_sale_date DATE,
  last_sale_price NUMERIC,
  total_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  WITH filtered_properties AS (
    SELECT p.*,
           COUNT(*) OVER() as total_count
    FROM properties p
    WHERE
      (search_text IS NULL OR (
        p.owner_name ILIKE '%' || search_text || '%' OR
        p.address ILIKE '%' || search_text || '%' OR
        p.parcel_id = search_text
      )) AND
      (search_city IS NULL OR p.city = search_city) AND
      (min_price IS NULL OR p.assessed_value >= min_price) AND
      (max_price IS NULL OR p.assessed_value <= max_price) AND
      (property_types IS NULL OR p.property_type = ANY(property_types))
    ORDER BY p.assessed_value DESC NULLS LAST
    LIMIT result_limit
    OFFSET result_offset
  )
  SELECT
    fp.parcel_id,
    fp.owner_name,
    fp.address,
    fp.city,
    fp.state,
    fp.zip_code,
    fp.property_type,
    fp.assessed_value,
    fp.last_sale_date,
    fp.last_sale_price,
    fp.total_count
  FROM filtered_properties fp;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER FOR AUTO-SYNC BETWEEN TABLES
CREATE OR REPLACE FUNCTION sync_property_data()
RETURNS TRIGGER AS $$
BEGIN
  -- Sync from florida_parcels to properties
  IF TG_TABLE_NAME = 'florida_parcels' THEN
    INSERT INTO properties (
      parcel_id, owner_name, address, city, state, zip_code
    )
    VALUES (
      NEW.parcel_id, NEW.owner_name, NEW.phy_addr1,
      NEW.phy_city, NEW.phy_state, NEW.phy_zipcd
    )
    ON CONFLICT (parcel_id) DO UPDATE SET
      owner_name = EXCLUDED.owner_name,
      address = EXCLUDED.address,
      city = EXCLUDED.city,
      state = EXCLUDED.state,
      zip_code = EXCLUDED.zip_code,
      updated_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sync_florida_parcels_to_properties
AFTER INSERT OR UPDATE ON florida_parcels
FOR EACH ROW
EXECUTE FUNCTION sync_property_data();
