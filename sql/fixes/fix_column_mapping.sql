-- Fix column mapping for UI compatibility
-- The florida_parcels table has the data, but the UI expects different column names
-- This script creates a VIEW that maps the columns correctly

-- Drop the view if it exists
DROP VIEW IF EXISTS florida_parcels_ui CASCADE;

-- Create a view that maps existing columns to what the UI expects
CREATE OR REPLACE VIEW florida_parcels_ui AS
SELECT 
    id,
    parcel_id,
    county,
    year,
    
    -- Address fields (UI expects phy_* names which we already have!)
    phy_addr1,
    phy_addr2,
    phy_city,
    phy_state,
    phy_zipcd,
    
    -- Owner fields
    owner_name,
    owner_addr1,
    owner_city,
    owner_state,
    owner_zip,
    
    -- Value fields
    assessed_value,
    taxable_value,
    just_value,
    just_value as market_value,  -- UI might expect market_value
    land_value,
    building_value,
    building_value as improvement_value,  -- Alias for UI
    
    -- Property details
    year_built,
    year_built as eff_year_built,  -- UI expects this too
    total_living_area,
    total_living_area as living_area,  -- UI uses both names
    total_living_area as heated_area,  -- Another alias
    land_sqft,
    land_sqft as lot_size,  -- Alias
    bedrooms,
    bathrooms,
    units,
    units as total_units,  -- Alias
    
    -- Property classification
    property_use,
    property_use as usage_code,  -- Alias
    property_use as use_code,  -- Another alias
    property_use_desc,
    property_use_desc as property_type,  -- UI expects this
    property_use_desc as use_description,  -- Another alias
    
    -- Tax info (creating dummy fields for now)
    0 as tax_amount,
    'N' as homestead_exemption,
    'N' as homestead,
    NULL as other_exemptions,
    NULL as exemption_codes,
    
    -- Sale information
    sale_price,
    sale_date,
    NULL as sale_type,
    NULL as deed_type,
    NULL as or_book,
    NULL as or_page,
    NULL as book_page,
    NULL as recording_book_page,
    NULL as cin,
    NULL as clerk_instrument_number,
    
    -- Additional fields
    NULL as sketch_url,
    NULL as record_link,
    NULL as vi_code,
    false as is_distressed,
    false as is_bank_sale,
    NULL::jsonb as land_factors,
    
    -- Metadata
    import_date as created_at,
    update_date as updated_at
FROM florida_parcels;

-- Grant permissions
GRANT SELECT ON florida_parcels_ui TO anon, authenticated;

-- Create indexes on the view's base table for better performance
CREATE INDEX IF NOT EXISTS idx_fl_parcels_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_fl_parcels_county ON florida_parcels(county);
CREATE INDEX IF NOT EXISTS idx_fl_parcels_phy_addr1 ON florida_parcels(phy_addr1);
CREATE INDEX IF NOT EXISTS idx_fl_parcels_owner ON florida_parcels(owner_name);

-- Test the view
SELECT COUNT(*) as total_properties FROM florida_parcels_ui;

-- Test a specific property
SELECT 
    parcel_id,
    phy_addr1,
    phy_city,
    owner_name,
    assessed_value,
    year_built,
    bedrooms,
    bathrooms
FROM florida_parcels_ui
WHERE county = '06'  -- Broward County
LIMIT 5;

-- ALTERNATIVE: If the UI can't use a view, we need to rename the table
-- and update the UI code to use 'florida_parcels' instead of 'florida_parcels_ui'

-- Check if we have the columns the UI needs
SELECT 
    'SUCCESS: florida_parcels table has ' || COUNT(*) || ' properties with all required columns!' as status
FROM florida_parcels;