-- Add auction_date and auction_description columns to tax_deed_bidding_items table
ALTER TABLE tax_deed_bidding_items 
ADD COLUMN IF NOT EXISTS auction_date DATE,
ADD COLUMN IF NOT EXISTS auction_description TEXT;

-- Update existing records with correct auction date
UPDATE tax_deed_bidding_items
SET auction_date = '2025-09-17',
    auction_description = '9/17/2025 Tax Deed Sale'
WHERE auction_date IS NULL;

-- Create index for better query performance on auction_date
CREATE INDEX IF NOT EXISTS idx_auction_date 
ON tax_deed_bidding_items(auction_date);