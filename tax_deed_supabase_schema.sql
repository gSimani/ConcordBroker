-- Tax Deed Sales Database Schema for Supabase
-- =============================================

-- Drop existing tables if needed (be careful in production!)
-- DROP TABLE IF EXISTS tax_deed_contacts CASCADE;
-- DROP TABLE IF EXISTS tax_deed_properties CASCADE;
-- DROP TABLE IF EXISTS tax_deed_auctions CASCADE;

-- Main auctions table
CREATE TABLE IF NOT EXISTS tax_deed_auctions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    auction_id TEXT UNIQUE NOT NULL,
    description TEXT,
    auction_date TIMESTAMP WITH TIME ZONE,
    total_items INTEGER DEFAULT 0,
    available_items INTEGER DEFAULT 0,
    advertised_items INTEGER DEFAULT 0,
    canceled_items INTEGER DEFAULT 0,
    status TEXT CHECK (status IN ('Upcoming', 'Active', 'Closed', 'Canceled')),
    auction_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Properties table with all details
CREATE TABLE IF NOT EXISTS tax_deed_properties (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    composite_key TEXT UNIQUE NOT NULL, -- auction_id_item_id
    auction_id TEXT REFERENCES tax_deed_auctions(auction_id) ON DELETE CASCADE,
    item_id TEXT NOT NULL,
    tax_deed_number TEXT,
    parcel_number TEXT,
    parcel_url TEXT,
    tax_certificate_number TEXT,
    legal_description TEXT,
    situs_address TEXT,
    city TEXT,
    state TEXT DEFAULT 'FL',
    zip_code TEXT,
    homestead BOOLEAN DEFAULT FALSE,
    assessed_value NUMERIC(12, 2),
    soh_value NUMERIC(12, 2),
    applicant TEXT,
    applicant_companies TEXT[],
    gis_map_url TEXT,
    opening_bid NUMERIC(12, 2),
    best_bid NUMERIC(12, 2),
    close_time TIMESTAMP WITH TIME ZONE,
    status TEXT CHECK (status IN ('Upcoming', 'Active', 'Sold', 'Canceled', 'Removed')),
    
    -- Sunbiz matching fields
    sunbiz_matched BOOLEAN DEFAULT FALSE,
    sunbiz_entity_names TEXT[],
    sunbiz_entity_ids TEXT[],
    sunbiz_data JSONB DEFAULT '{}',
    
    -- Additional tracking
    property_type TEXT,
    land_use_code TEXT,
    year_built INTEGER,
    living_area_sqft INTEGER,
    lot_size_sqft INTEGER,
    
    extracted_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Contact information and notes table
CREATE TABLE IF NOT EXISTS tax_deed_contacts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    property_id UUID REFERENCES tax_deed_properties(id) ON DELETE CASCADE,
    composite_key TEXT REFERENCES tax_deed_properties(composite_key),
    
    -- Owner contact information
    owner_name TEXT,
    owner_phone TEXT,
    owner_email TEXT,
    owner_mailing_address TEXT,
    
    -- Contact attempts and notes
    contact_status TEXT CHECK (contact_status IN ('Not Contacted', 'Attempted', 'Connected', 'Not Interested', 'Interested', 'In Negotiation', 'Deal Closed')),
    last_contact_date DATE,
    next_followup_date DATE,
    notes TEXT,
    
    -- Additional contacts
    alternative_phones TEXT[],
    alternative_emails TEXT[],
    
    -- User tracking
    assigned_to TEXT,
    created_by TEXT,
    updated_by TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Property history table for tracking changes
CREATE TABLE IF NOT EXISTS tax_deed_property_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    property_id UUID REFERENCES tax_deed_properties(id) ON DELETE CASCADE,
    composite_key TEXT,
    auction_id TEXT,
    item_id TEXT,
    snapshot_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Snapshot of key fields
    tax_deed_number TEXT,
    parcel_number TEXT,
    status TEXT,
    opening_bid NUMERIC(12, 2),
    best_bid NUMERIC(12, 2),
    change_type TEXT, -- 'status_change', 'bid_update', 'info_update'
    change_details JSONB,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts and notifications table
CREATE TABLE IF NOT EXISTS tax_deed_alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    alert_type TEXT NOT NULL,
    priority TEXT CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),
    title TEXT NOT NULL,
    details TEXT,
    property_id UUID REFERENCES tax_deed_properties(id) ON DELETE CASCADE,
    auction_id TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_auctions_status ON tax_deed_auctions(status);
CREATE INDEX IF NOT EXISTS idx_auctions_date ON tax_deed_auctions(auction_date);

CREATE INDEX IF NOT EXISTS idx_properties_auction ON tax_deed_properties(auction_id);
CREATE INDEX IF NOT EXISTS idx_properties_parcel ON tax_deed_properties(parcel_number);
CREATE INDEX IF NOT EXISTS idx_properties_address ON tax_deed_properties(situs_address);
CREATE INDEX IF NOT EXISTS idx_properties_status ON tax_deed_properties(status);
CREATE INDEX IF NOT EXISTS idx_properties_homestead ON tax_deed_properties(homestead);
CREATE INDEX IF NOT EXISTS idx_properties_opening_bid ON tax_deed_properties(opening_bid);
CREATE INDEX IF NOT EXISTS idx_properties_sunbiz ON tax_deed_properties(sunbiz_matched);
CREATE INDEX IF NOT EXISTS idx_properties_composite ON tax_deed_properties(composite_key);

CREATE INDEX IF NOT EXISTS idx_contacts_property ON tax_deed_contacts(property_id);
CREATE INDEX IF NOT EXISTS idx_contacts_status ON tax_deed_contacts(contact_status);
CREATE INDEX IF NOT EXISTS idx_contacts_assigned ON tax_deed_contacts(assigned_to);

CREATE INDEX IF NOT EXISTS idx_history_property ON tax_deed_property_history(property_id);
CREATE INDEX IF NOT EXISTS idx_history_time ON tax_deed_property_history(snapshot_time);

CREATE INDEX IF NOT EXISTS idx_alerts_unread ON tax_deed_alerts(is_read) WHERE is_read = FALSE;

-- Create views for easier querying
CREATE OR REPLACE VIEW tax_deed_properties_with_contacts AS
SELECT 
    p.*,
    c.owner_name,
    c.owner_phone,
    c.owner_email,
    c.contact_status,
    c.notes,
    c.last_contact_date,
    c.next_followup_date,
    c.assigned_to
FROM tax_deed_properties p
LEFT JOIN tax_deed_contacts c ON p.id = c.property_id;

CREATE OR REPLACE VIEW tax_deed_upcoming_high_value AS
SELECT 
    p.*,
    a.description as auction_description,
    a.auction_date
FROM tax_deed_properties p
JOIN tax_deed_auctions a ON p.auction_id = a.auction_id
WHERE p.status = 'Upcoming' 
    AND p.opening_bid > 100000
ORDER BY a.auction_date, p.opening_bid DESC;

CREATE OR REPLACE VIEW tax_deed_homestead_properties AS
SELECT 
    p.*,
    a.description as auction_description,
    a.auction_date,
    c.contact_status,
    c.owner_phone,
    c.owner_email
FROM tax_deed_properties p
JOIN tax_deed_auctions a ON p.auction_id = a.auction_id
LEFT JOIN tax_deed_contacts c ON p.id = c.property_id
WHERE p.homestead = TRUE 
    AND p.status = 'Upcoming'
ORDER BY a.auction_date;

-- Functions for updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_tax_deed_auctions_updated_at 
    BEFORE UPDATE ON tax_deed_auctions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tax_deed_properties_updated_at 
    BEFORE UPDATE ON tax_deed_properties 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tax_deed_contacts_updated_at 
    BEFORE UPDATE ON tax_deed_contacts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
ALTER TABLE tax_deed_auctions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_deed_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_deed_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_deed_property_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_deed_alerts ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (adjust as needed)
CREATE POLICY "Allow public read for auctions" ON tax_deed_auctions
    FOR SELECT USING (true);

CREATE POLICY "Allow public read for properties" ON tax_deed_properties
    FOR SELECT USING (true);

-- Contacts should be more restricted
CREATE POLICY "Allow authenticated read for contacts" ON tax_deed_contacts
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated insert for contacts" ON tax_deed_contacts
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated update for contacts" ON tax_deed_contacts
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Sample data insertion (for testing)
/*
INSERT INTO tax_deed_auctions (auction_id, description, auction_date, total_items, status, auction_url)
VALUES 
    ('110', '9/17/2025 Tax Deed Sale', '2025-09-17', 46, 'Upcoming', 'https://broward.deedauction.net/auction/110'),
    ('111', '10/15/2025 Tax Deed Sale', '2025-10-15', 63, 'Upcoming', 'https://broward.deedauction.net/auction/111');
*/