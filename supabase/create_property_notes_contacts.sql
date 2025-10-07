-- Create property_notes table if it doesn't exist
CREATE TABLE IF NOT EXISTS property_notes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  parcel_id VARCHAR(50) NOT NULL,
  user_id UUID REFERENCES auth.users(id),
  note TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(parcel_id, user_id)
);

-- Create property_contacts table
CREATE TABLE IF NOT EXISTS property_contacts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  parcel_id VARCHAR(50) NOT NULL,
  user_id UUID REFERENCES auth.users(id),
  contact_type VARCHAR(20) NOT NULL CHECK (contact_type IN ('phone', 'email', 'social')),
  contact_value VARCHAR(255) NOT NULL,
  contact_label VARCHAR(100),
  social_platform VARCHAR(50),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_property_notes_parcel_id ON property_notes(parcel_id);
CREATE INDEX IF NOT EXISTS idx_property_notes_user_id ON property_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_property_contacts_parcel_id ON property_contacts(parcel_id);
CREATE INDEX IF NOT EXISTS idx_property_contacts_user_id ON property_contacts(user_id);

-- Enable Row Level Security
ALTER TABLE property_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_contacts ENABLE ROW LEVEL SECURITY;

-- Create policies for property_notes
CREATE POLICY "Users can view their own notes" ON property_notes
  FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own notes" ON property_notes
  FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can update their own notes" ON property_notes
  FOR UPDATE USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can delete their own notes" ON property_notes
  FOR DELETE USING (auth.uid() = user_id OR user_id IS NULL);

-- Create policies for property_contacts
CREATE POLICY "Users can view their own contacts" ON property_contacts
  FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own contacts" ON property_contacts
  FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can update their own contacts" ON property_contacts
  FOR UPDATE USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can delete their own contacts" ON property_contacts
  FOR DELETE USING (auth.uid() = user_id OR user_id IS NULL);

-- Create function to automatically update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_property_notes_updated_at BEFORE UPDATE ON property_notes
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_property_contacts_updated_at BEFORE UPDATE ON property_contacts
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();