-- ConcordBroker Phase 1: User-Specific Tables for 100% Supabase Integration
-- Execute this in Supabase SQL Editor

-- ============================================================================
-- USER WATCHLISTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_watchlists (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  parcel_id TEXT NOT NULL,
  county TEXT,
  property_address TEXT,
  owner_name TEXT,
  market_value NUMERIC,
  notes TEXT,
  is_favorite BOOLEAN DEFAULT FALSE,
  alert_preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, parcel_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_watchlists_user_id ON user_watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_user_watchlists_parcel_id ON user_watchlists(parcel_id);
CREATE INDEX IF NOT EXISTS idx_user_watchlists_created_at ON user_watchlists(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_watchlists_county ON user_watchlists(county);

-- Enable RLS and create policies
ALTER TABLE user_watchlists ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_watchlists
DROP POLICY IF EXISTS "Users can view own watchlists" ON user_watchlists;
CREATE POLICY "Users can view own watchlists" ON user_watchlists
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own watchlists" ON user_watchlists;
CREATE POLICY "Users can insert own watchlists" ON user_watchlists
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own watchlists" ON user_watchlists;
CREATE POLICY "Users can update own watchlists" ON user_watchlists
  FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own watchlists" ON user_watchlists;
CREATE POLICY "Users can delete own watchlists" ON user_watchlists
  FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- PROPERTY NOTES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS property_notes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  parcel_id TEXT NOT NULL,
  county TEXT,
  title TEXT,
  notes TEXT NOT NULL,
  tags TEXT[] DEFAULT '{}',
  is_private BOOLEAN DEFAULT TRUE,
  note_type TEXT DEFAULT 'general' CHECK (note_type IN ('general', 'investment', 'contact', 'reminder', 'analysis')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_property_notes_user_id ON property_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_property_notes_parcel_id ON property_notes(parcel_id);
CREATE INDEX IF NOT EXISTS idx_property_notes_type ON property_notes(note_type);
CREATE INDEX IF NOT EXISTS idx_property_notes_tags ON property_notes USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_property_notes_created_at ON property_notes(created_at DESC);

-- Enable RLS and create policies
ALTER TABLE property_notes ENABLE ROW LEVEL SECURITY;

-- RLS Policies for property_notes
DROP POLICY IF EXISTS "Users can manage own notes" ON property_notes;
CREATE POLICY "Users can manage own notes" ON property_notes
  FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- USER PREFERENCES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_preferences (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  search_preferences JSONB DEFAULT '{}',
  notification_preferences JSONB DEFAULT '{}',
  display_preferences JSONB DEFAULT '{}',
  favorite_counties TEXT[] DEFAULT '{}',
  default_filters JSONB DEFAULT '{}',
  subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Enable RLS and create policies
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_preferences
DROP POLICY IF EXISTS "Users can manage own preferences" ON user_preferences;
CREATE POLICY "Users can manage own preferences" ON user_preferences
  FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- USER SEARCH HISTORY TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_search_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  search_query TEXT NOT NULL,
  search_filters JSONB DEFAULT '{}',
  results_count INTEGER DEFAULT 0,
  search_type TEXT DEFAULT 'property' CHECK (search_type IN ('property', 'owner', 'address', 'advanced')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_search_history_user_id ON user_search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_search_history_created_at ON user_search_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_search_history_type ON user_search_history(search_type);

-- Enable RLS and create policies
ALTER TABLE user_search_history ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_search_history
DROP POLICY IF EXISTS "Users can manage own search history" ON user_search_history;
CREATE POLICY "Users can manage own search history" ON user_search_history
  FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- PROPERTY VIEW HISTORY TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS property_view_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  parcel_id TEXT NOT NULL,
  county TEXT,
  view_count INTEGER DEFAULT 1,
  first_viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  view_source TEXT DEFAULT 'search',
  UNIQUE(user_id, parcel_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_property_view_history_user_id ON property_view_history(user_id);
CREATE INDEX IF NOT EXISTS idx_property_view_history_last_viewed ON property_view_history(last_viewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_property_view_history_parcel_id ON property_view_history(parcel_id);

-- Enable RLS and create policies
ALTER TABLE property_view_history ENABLE ROW LEVEL SECURITY;

-- RLS Policies for property_view_history
DROP POLICY IF EXISTS "Users can manage own view history" ON property_view_history;
CREATE POLICY "Users can manage own view history" ON property_view_history
  FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT FIELDS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for tables that need updated_at
DROP TRIGGER IF EXISTS update_user_watchlists_updated_at ON user_watchlists;
CREATE TRIGGER update_user_watchlists_updated_at
  BEFORE UPDATE ON user_watchlists
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_property_notes_updated_at ON property_notes;
CREATE TRIGGER update_property_notes_updated_at
  BEFORE UPDATE ON property_notes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER update_user_preferences_updated_at
  BEFORE UPDATE ON user_preferences
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- GRANT PERMISSIONS (if needed for service role)
-- ============================================================================
-- These are typically handled by Supabase automatically, but included for completeness
-- GRANT ALL ON user_watchlists TO authenticated;
-- GRANT ALL ON property_notes TO authenticated;
-- GRANT ALL ON user_preferences TO authenticated;
-- GRANT ALL ON user_search_history TO authenticated;
-- GRANT ALL ON property_view_history TO authenticated;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify tables were created successfully
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'user_%' OR tablename = 'property_notes';
-- SELECT schemaname, tablename, policyname, cmd, qual FROM pg_policies WHERE tablename IN ('user_watchlists', 'property_notes', 'user_preferences', 'user_search_history', 'property_view_history');