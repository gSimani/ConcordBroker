-- Create property_notes table
CREATE TABLE IF NOT EXISTS property_notes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    parcel_id TEXT NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    note_type TEXT CHECK (note_type IN ('general', 'investment', 'legal', 'inspection', 'research')) DEFAULT 'general',
    priority TEXT CHECK (priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
    is_private BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_property_notes_parcel_id ON property_notes(parcel_id);
CREATE INDEX IF NOT EXISTS idx_property_notes_user_id ON property_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_property_notes_created_at ON property_notes(created_at DESC);

-- Enable RLS (Row Level Security)
ALTER TABLE property_notes ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can view all public notes and their own private notes
CREATE POLICY "Users can view notes" ON property_notes
    FOR SELECT
    USING (
        is_private = false OR
        auth.uid() = user_id
    );

-- Users can insert their own notes
CREATE POLICY "Users can create notes" ON property_notes
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own notes
CREATE POLICY "Users can update own notes" ON property_notes
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own notes
CREATE POLICY "Users can delete own notes" ON property_notes
    FOR DELETE
    USING (auth.uid() = user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_property_notes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_property_notes_updated_at
    BEFORE UPDATE ON property_notes
    FOR EACH ROW
    EXECUTE FUNCTION update_property_notes_updated_at();