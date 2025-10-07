import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

const createNotesTable = async () => {
  try {
    console.log('Creating property_notes table...');

    const { data, error } = await supabase.rpc('exec_sql', {
      sql: `
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

        -- Create function to update updated_at timestamp
        CREATE OR REPLACE FUNCTION update_property_notes_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        -- Create trigger to automatically update updated_at
        DROP TRIGGER IF EXISTS update_property_notes_updated_at ON property_notes;
        CREATE TRIGGER update_property_notes_updated_at
            BEFORE UPDATE ON property_notes
            FOR EACH ROW
            EXECUTE FUNCTION update_property_notes_updated_at();
      `
    });

    if (error) {
      console.error('Error creating table:', error);
    } else {
      console.log('Table created successfully!');
    }

    // Create RLS policies separately
    console.log('Creating RLS policies...');

    const policies = [
      {
        name: 'Users can view notes',
        sql: `
          DROP POLICY IF EXISTS "Users can view notes" ON property_notes;
          CREATE POLICY "Users can view notes" ON property_notes
              FOR SELECT
              USING (
                  is_private = false OR
                  auth.uid() = user_id
              );
        `
      },
      {
        name: 'Users can create notes',
        sql: `
          DROP POLICY IF EXISTS "Users can create notes" ON property_notes;
          CREATE POLICY "Users can create notes" ON property_notes
              FOR INSERT
              WITH CHECK (auth.uid() = user_id);
        `
      },
      {
        name: 'Users can update own notes',
        sql: `
          DROP POLICY IF EXISTS "Users can update own notes" ON property_notes;
          CREATE POLICY "Users can update own notes" ON property_notes
              FOR UPDATE
              USING (auth.uid() = user_id)
              WITH CHECK (auth.uid() = user_id);
        `
      },
      {
        name: 'Users can delete own notes',
        sql: `
          DROP POLICY IF EXISTS "Users can delete own notes" ON property_notes;
          CREATE POLICY "Users can delete own notes" ON property_notes
              FOR DELETE
              USING (auth.uid() = user_id);
        `
      }
    ];

    for (const policy of policies) {
      const { error: policyError } = await supabase.rpc('exec_sql', {
        sql: policy.sql
      });

      if (policyError) {
        console.error(`Error creating policy "${policy.name}":`, policyError);
      } else {
        console.log(`Policy "${policy.name}" created successfully!`);
      }
    }

  } catch (error) {
    console.error('Unexpected error:', error);
  }
};

createNotesTable();