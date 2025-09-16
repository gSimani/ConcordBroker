-- Add winning_bid and winner_name columns to tax_deed_properties table
-- These columns will store the final bid amount and winner for past auctions

ALTER TABLE tax_deed_properties 
ADD COLUMN IF NOT EXISTS winning_bid DECIMAL(12, 2),
ADD COLUMN IF NOT EXISTS winner_name VARCHAR(255);

-- Add index for faster queries on bid amounts
CREATE INDEX IF NOT EXISTS idx_tax_deed_properties_opening_bid ON tax_deed_properties(opening_bid);
CREATE INDEX IF NOT EXISTS idx_tax_deed_properties_winning_bid ON tax_deed_properties(winning_bid);
CREATE INDEX IF NOT EXISTS idx_tax_deed_properties_auction_status ON tax_deed_properties(auction_status);

-- Update column comments for documentation
COMMENT ON COLUMN tax_deed_properties.winning_bid IS 'Final winning bid amount for past auctions (in USD)';
COMMENT ON COLUMN tax_deed_properties.winner_name IS 'Name of the winning bidder for past auctions';