-- Add enhanced fields to tax_deed_bidding_items table
-- Migration: 2025-11-04 - Tax Deed Enhanced Fields

-- Add new columns if they don't exist
ALTER TABLE tax_deed_bidding_items
ADD COLUMN IF NOT EXISTS legal_description TEXT,
ADD COLUMN IF NOT EXISTS gis_map_url TEXT,
ADD COLUMN IF NOT EXISTS bid_details_url TEXT,
ADD COLUMN IF NOT EXISTS company_detected BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS company_type TEXT;

-- Add comments for documentation
COMMENT ON COLUMN tax_deed_bidding_items.legal_description IS 'Legal property description (e.g., "FIRST ADD TO TUSKEGEE PARK 9-65 B LOT 11 BLK 8")';
COMMENT ON COLUMN tax_deed_bidding_items.gis_map_url IS 'Full URL to county GIS map for this parcel';
COMMENT ON COLUMN tax_deed_bidding_items.bid_details_url IS 'Full URL to auction bid details page';
COMMENT ON COLUMN tax_deed_bidding_items.company_detected IS 'Whether applicant name contains LLC, INC, CORP, etc.';
COMMENT ON COLUMN tax_deed_bidding_items.company_type IS 'Type of company detected (LLC, INC, CORP, etc.)';

-- Create index for company lookups (for SUNBIZ matching)
CREATE INDEX IF NOT EXISTS idx_tax_deed_company_detected
ON tax_deed_bidding_items(company_detected)
WHERE company_detected = TRUE;

-- Create index for applicant name searches (for SUNBIZ linking)
CREATE INDEX IF NOT EXISTS idx_tax_deed_applicant_name
ON tax_deed_bidding_items(applicant_name)
WHERE applicant_name IS NOT NULL;

-- Create GIN index for full-text search on legal description
CREATE INDEX IF NOT EXISTS idx_tax_deed_legal_description_fts
ON tax_deed_bidding_items
USING GIN (to_tsvector('english', COALESCE(legal_description, '')));

-- Verification query to check all columns
DO $$
BEGIN
  RAISE NOTICE 'Tax Deed Enhanced Fields Migration Complete';
  RAISE NOTICE 'Columns added: legal_description, gis_map_url, bid_details_url, company_detected, company_type';
  RAISE NOTICE 'Indexes created: idx_tax_deed_company_detected, idx_tax_deed_applicant_name, idx_tax_deed_legal_description_fts';
END $$;
