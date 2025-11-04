-- Migration: Fix nav_assessments table permissions
-- Date: 2025-01-27
-- Purpose: Enable public read access to nav_assessments table to resolve 401 errors

-- First, check if the table exists and create it if it doesn't
CREATE TABLE IF NOT EXISTS nav_assessments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id TEXT NOT NULL,
    county TEXT,
    year INTEGER,
    assessment_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_nav_assessments_parcel_id ON nav_assessments(parcel_id);
CREATE INDEX IF NOT EXISTS idx_nav_assessments_county_year ON nav_assessments(county, year);

-- Enable Row Level Security
ALTER TABLE nav_assessments ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Public read access to nav_assessments" ON nav_assessments;
DROP POLICY IF EXISTS "Service role full access to nav_assessments" ON nav_assessments;

-- Create RLS policy for public read access (anonymous users)
CREATE POLICY "Public read access to nav_assessments"
    ON nav_assessments
    FOR SELECT
    TO anon
    USING (true);

-- Create RLS policy for authenticated users
CREATE POLICY "Authenticated read access to nav_assessments"
    ON nav_assessments
    FOR SELECT
    TO authenticated
    USING (true);

-- Grant SELECT permission to anon role
GRANT SELECT ON nav_assessments TO anon;
GRANT SELECT ON nav_assessments TO authenticated;

-- Service role should have full access
GRANT ALL ON nav_assessments TO service_role;

-- Add helpful comment
COMMENT ON TABLE nav_assessments IS 'NAV (Non Ad Valorem) Assessment data from Florida Department of Revenue';
