-- Create tax deed properties table with contact management
CREATE TABLE IF NOT EXISTS tax_deed_properties_with_contacts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    composite_key TEXT UNIQUE NOT NULL,
    auction_id TEXT,
    tax_deed_number TEXT NOT NULL,
    parcel_number TEXT NOT NULL,
    parcel_url TEXT,
    tax_certificate_number TEXT,
    legal_description TEXT,
    situs_address TEXT NOT NULL,
    city TEXT,
    state TEXT DEFAULT 'FL',
    zip_code TEXT,
    homestead BOOLEAN DEFAULT false,
    assessed_value NUMERIC,
    opening_bid NUMERIC NOT NULL,
    best_bid NUMERIC,
    close_time TEXT,
    status TEXT NOT NULL,
    applicant TEXT,
    applicant_companies TEXT[],
    gis_map_url TEXT,
    sunbiz_matched BOOLEAN DEFAULT false,
    sunbiz_entity_names TEXT[],
    sunbiz_entity_ids TEXT[],
    sunbiz_data JSONB,
    auction_date DATE,
    auction_description TEXT,
    -- Contact management fields
    owner_name TEXT,
    owner_phone TEXT,
    owner_email TEXT,
    contact_status TEXT DEFAULT 'Not Contacted',
    notes TEXT,
    last_contact_date DATE,
    next_followup_date DATE,
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tax_deed_parcel ON tax_deed_properties_with_contacts(parcel_number);
CREATE INDEX IF NOT EXISTS idx_tax_deed_status ON tax_deed_properties_with_contacts(status);
CREATE INDEX IF NOT EXISTS idx_tax_deed_auction_date ON tax_deed_properties_with_contacts(auction_date);
CREATE INDEX IF NOT EXISTS idx_tax_deed_opening_bid ON tax_deed_properties_with_contacts(opening_bid);
CREATE INDEX IF NOT EXISTS idx_tax_deed_composite ON tax_deed_properties_with_contacts(composite_key);

-- Enable Row Level Security
ALTER TABLE tax_deed_properties_with_contacts ENABLE ROW LEVEL SECURITY;

-- Create policy for anonymous access (read-only)
CREATE POLICY "Allow anonymous read access" ON tax_deed_properties_with_contacts
    FOR SELECT USING (true);

-- Create policy for authenticated users (full access)
CREATE POLICY "Allow authenticated users full access" ON tax_deed_properties_with_contacts
    FOR ALL USING (true);