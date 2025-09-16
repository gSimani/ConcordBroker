-- Fix RLS issue for data loading
DROP POLICY IF EXISTS "Allow all" ON florida_parcels;
ALTER TABLE florida_parcels DISABLE ROW LEVEL SECURITY;

-- Verify current count
SELECT COUNT(*) as current_property_count FROM florida_parcels;