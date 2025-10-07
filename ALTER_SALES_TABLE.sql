-- Add county column to property_sales_history table
-- Run this in Supabase SQL Editor

ALTER TABLE property_sales_history
ADD COLUMN IF NOT EXISTS county TEXT;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_sales_county
ON property_sales_history(county);

-- Verify the column was added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'property_sales_history'
ORDER BY ordinal_position;
