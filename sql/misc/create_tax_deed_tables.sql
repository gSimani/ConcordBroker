-- Create Tax Deed Properties table with all necessary fields
CREATE TABLE IF NOT EXISTS tax_deed_properties (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Auction Information
    auction_date DATE NOT NULL,
    auction_id VARCHAR(50),
    auction_description VARCHAR(255),
    
    -- Property Identifiers
    tax_deed_number VARCHAR(50),
    parcel_number VARCHAR(50) NOT NULL,
    tax_certificate_number VARCHAR(50),
    
    -- Property Details
    situs_address TEXT,
    city VARCHAR(100),
    state VARCHAR(2) DEFAULT 'FL',
    zip_code VARCHAR(10),
    legal_description TEXT,
    
    -- Financial Information
    assessed_value DECIMAL(12, 2),
    opening_bid DECIMAL(12, 2) NOT NULL,
    winning_bid DECIMAL(12, 2),  -- For past auctions
    best_bid DECIMAL(12, 2),      -- Current highest bid
    
    -- Status Information
    status VARCHAR(50) DEFAULT 'Active',  -- Active, Sold, Cancelled, Pending
    is_homestead BOOLEAN DEFAULT FALSE,
    
    -- Parties Involved
    applicant_name VARCHAR(255),
    winner_name VARCHAR(255),  -- For sold properties
    
    -- URLs
    property_appraiser_url TEXT,
    gis_map_url TEXT,
    sunbiz_url TEXT,
    
    -- Metadata
    source VARCHAR(100) DEFAULT 'broward.realauction.com',
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Create unique constraint on parcel + auction_date
    UNIQUE(parcel_number, auction_date)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_tax_deed_properties_auction_date ON tax_deed_properties(auction_date);
CREATE INDEX IF NOT EXISTS idx_tax_deed_properties_parcel ON tax_deed_properties(parcel_number);
CREATE INDEX IF NOT EXISTS idx_tax_deed_properties_status ON tax_deed_properties(status);
CREATE INDEX IF NOT EXISTS idx_tax_deed_properties_opening_bid ON tax_deed_properties(opening_bid);
CREATE INDEX IF NOT EXISTS idx_tax_deed_properties_winning_bid ON tax_deed_properties(winning_bid);
CREATE INDEX IF NOT EXISTS idx_tax_deed_properties_homestead ON tax_deed_properties(is_homestead);

-- Create Tax Deed Contacts table for managing outreach
CREATE TABLE IF NOT EXISTS tax_deed_contacts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    property_id UUID REFERENCES tax_deed_properties(id) ON DELETE CASCADE,
    
    -- Contact Information
    owner_name VARCHAR(255),
    owner_phone VARCHAR(20),
    owner_email VARCHAR(255),
    
    -- Contact Management
    contact_status VARCHAR(50) DEFAULT 'Not Contacted',  -- Not Contacted, Attempted, Connected, Not Interested, Interested, In Negotiation, Deal Closed
    last_contact_date DATE,
    next_followup_date DATE,
    
    -- Notes
    notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(property_id)
);

-- Create index for contact queries
CREATE INDEX IF NOT EXISTS idx_tax_deed_contacts_property ON tax_deed_contacts(property_id);
CREATE INDEX IF NOT EXISTS idx_tax_deed_contacts_status ON tax_deed_contacts(contact_status);

-- Create view that combines properties with contact info
CREATE OR REPLACE VIEW tax_deed_properties_with_contacts AS
SELECT 
    p.*,
    c.owner_name,
    c.owner_phone,
    c.owner_email,
    c.contact_status,
    c.last_contact_date,
    c.next_followup_date,
    c.notes as contact_notes
FROM tax_deed_properties p
LEFT JOIN tax_deed_contacts c ON p.id = c.property_id;

-- Add RLS policies if needed
ALTER TABLE tax_deed_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_deed_contacts ENABLE ROW LEVEL SECURITY;

-- Create policies for anonymous access (adjust as needed)
CREATE POLICY "Allow anonymous read tax_deed_properties" ON tax_deed_properties
    FOR SELECT USING (true);

CREATE POLICY "Allow anonymous read tax_deed_contacts" ON tax_deed_contacts
    FOR SELECT USING (true);

-- Add comments for documentation
COMMENT ON TABLE tax_deed_properties IS 'Stores tax deed auction properties scraped from broward.realauction.com';
COMMENT ON TABLE tax_deed_contacts IS 'Stores contact management information for tax deed properties';
COMMENT ON VIEW tax_deed_properties_with_contacts IS 'Combined view of properties with their contact information';