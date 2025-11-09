-- Fix RLS and prepare for data loading
-- Run this in Supabase SQL Editor

-- 1. First, check current count
SELECT COUNT(*) as current_count FROM florida_parcels;

-- 2. Drop the existing "Allow all" policy that's causing the error
DROP POLICY IF EXISTS "Allow all" ON florida_parcels;

-- 3. Disable RLS temporarily for data loading
ALTER TABLE florida_parcels DISABLE ROW LEVEL SECURITY;

-- 4. Create a better public access policy for later
-- (But don't enable it yet)
CREATE POLICY "Enable read access for all users" 
ON florida_parcels 
FOR SELECT 
USING (true);

CREATE POLICY "Enable insert for all users" 
ON florida_parcels 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Enable update for all users" 
ON florida_parcels 
FOR UPDATE 
USING (true);

-- 5. Verify RLS is disabled
SELECT 
    schemaname,
    tablename,
    rowsecurity
FROM 
    pg_tables
WHERE 
    tablename = 'florida_parcels';

-- 6. Count again to confirm
SELECT COUNT(*) as count_after_fix FROM florida_parcels;

-- Now you can:
-- 1. Go to Table Editor
-- 2. Click on florida_parcels
-- 3. Click "Import data from CSV"
-- 4. Upload NAL16P202501.csv
-- 5. Map the columns as instructed

-- After import is complete, you can re-enable RLS if needed:
-- ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;