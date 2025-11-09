-- Add missing columns to florida_parcels table

-- Add homestead exemption columns
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS homestead_exemption BOOLEAN DEFAULT false;

ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS homestead_exemption_value INTEGER;

-- Add effective year built
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS eff_year_built INTEGER;

-- Add bedrooms and bathrooms (with decimal support for bathrooms)
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS bedrooms INTEGER;

ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS bathrooms DECIMAL(3,1);

-- Add exemptions as JSONB to store all exemption codes
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS exemptions JSONB;

-- Add building count
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS buildings INTEGER;

-- Verify columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'florida_parcels' 
AND column_name IN ('homestead_exemption', 'homestead_exemption_value', 'bedrooms', 'bathrooms', 'eff_year_built', 'exemptions', 'buildings')
ORDER BY column_name;