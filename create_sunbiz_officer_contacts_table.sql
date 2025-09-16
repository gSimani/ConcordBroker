-- Create enhanced table for Sunbiz officer contacts with email/phone
CREATE TABLE IF NOT EXISTS sunbiz_officer_contacts (
    id BIGSERIAL PRIMARY KEY,
    entity_name TEXT,
    officer_name TEXT,
    officer_email TEXT,
    officer_phone TEXT,
    additional_emails TEXT,
    additional_phones TEXT,
    source_file TEXT NOT NULL,
    source_line INTEGER,
    context TEXT,
    extracted_date TIMESTAMPTZ,
    import_date TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes for fast searching
    CONSTRAINT unique_officer_contact UNIQUE (entity_name, officer_name, officer_email)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sunbiz_officer_contacts_entity ON sunbiz_officer_contacts(entity_name);
CREATE INDEX IF NOT EXISTS idx_sunbiz_officer_contacts_officer ON sunbiz_officer_contacts(officer_name);
CREATE INDEX IF NOT EXISTS idx_sunbiz_officer_contacts_email ON sunbiz_officer_contacts(officer_email);
CREATE INDEX IF NOT EXISTS idx_sunbiz_officer_contacts_phone ON sunbiz_officer_contacts(officer_phone);
CREATE INDEX IF NOT EXISTS idx_sunbiz_officer_contacts_source ON sunbiz_officer_contacts(source_file);

-- Enable Row Level Security
ALTER TABLE sunbiz_officer_contacts ENABLE ROW LEVEL SECURITY;

-- Create policy to allow read access
CREATE POLICY "Allow read access to sunbiz_officer_contacts" ON sunbiz_officer_contacts
    FOR SELECT USING (true);

-- Create policy to allow insert
CREATE POLICY "Allow insert to sunbiz_officer_contacts" ON sunbiz_officer_contacts
    FOR INSERT WITH CHECK (true);

-- Add comments
COMMENT ON TABLE sunbiz_officer_contacts IS 'Enhanced Sunbiz officer contact information with emails and phone numbers';
COMMENT ON COLUMN sunbiz_officer_contacts.entity_name IS 'Business entity name';
COMMENT ON COLUMN sunbiz_officer_contacts.officer_name IS 'Officer/director name';
COMMENT ON COLUMN sunbiz_officer_contacts.officer_email IS 'Primary email address';
COMMENT ON COLUMN sunbiz_officer_contacts.officer_phone IS 'Primary phone number';
COMMENT ON COLUMN sunbiz_officer_contacts.additional_emails IS 'Additional email addresses (comma-separated)';
COMMENT ON COLUMN sunbiz_officer_contacts.additional_phones IS 'Additional phone numbers (comma-separated)';
COMMENT ON COLUMN sunbiz_officer_contacts.source_file IS 'Source file from FTP download';
COMMENT ON COLUMN sunbiz_officer_contacts.context IS 'Context text around the contact information';