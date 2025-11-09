-- Database Constraints for Tax Deed Bidding Items
-- These constraints will prevent future data quality issues
-- Run these in Supabase SQL Editor

-- 1. Ensure tax deed numbers follow proper format
ALTER TABLE tax_deed_bidding_items
ADD CONSTRAINT check_td_number_format
CHECK (
  tax_deed_number IS NOT NULL AND
  tax_deed_number LIKE 'TD-%' AND
  tax_deed_number NOT LIKE '%AUTO%'
);

-- 2. Prevent UNKNOWN or placeholder parcel IDs
ALTER TABLE tax_deed_bidding_items  
ADD CONSTRAINT check_parcel_not_placeholder
CHECK (
  parcel_id IS NOT NULL AND
  parcel_id NOT LIKE 'UNKNOWN%' AND
  parcel_id NOT LIKE 'PARCEL-%'
);

-- 3. Require real addresses (not placeholders)
ALTER TABLE tax_deed_bidding_items
ADD CONSTRAINT check_address_not_placeholder  
CHECK (
  legal_situs_address IS NOT NULL AND
  legal_situs_address != 'Address not available' AND
  legal_situs_address != 'Address pending' AND
  length(legal_situs_address) > 10
);

-- 4. Active/Upcoming properties must have opening bid
ALTER TABLE tax_deed_bidding_items
ADD CONSTRAINT check_active_has_opening_bid
CHECK (
  (item_status NOT IN ('Active', 'Upcoming')) OR
  (opening_bid IS NOT NULL AND opening_bid > 0)
);

-- 5. Valid status values only
ALTER TABLE tax_deed_bidding_items
ADD CONSTRAINT check_valid_status
CHECK (
  item_status IN ('Active', 'Upcoming', 'Sold', 'Cancelled', 'Canceled', 'Canceled Removed', 'Past')
);

-- 6. Ensure unique tax deed numbers
ALTER TABLE tax_deed_bidding_items
ADD CONSTRAINT unique_tax_deed_number
UNIQUE (tax_deed_number);

-- Optional: Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_tax_deed_status 
ON tax_deed_bidding_items(item_status);

CREATE INDEX IF NOT EXISTS idx_tax_deed_parcel
ON tax_deed_bidding_items(parcel_id);

CREATE INDEX IF NOT EXISTS idx_tax_deed_opening_bid
ON tax_deed_bidding_items(opening_bid);

-- View to see only clean, active properties
CREATE OR REPLACE VIEW active_tax_deeds AS
SELECT 
  tax_deed_number,
  parcel_id,
  legal_situs_address,
  opening_bid,
  item_status,
  applicant_name,
  close_time,
  homestead_exemption,
  assessed_value
FROM tax_deed_bidding_items
WHERE item_status IN ('Active', 'Upcoming')
  AND opening_bid > 0
  AND legal_situs_address NOT LIKE '%Thursday%'
ORDER BY opening_bid DESC;