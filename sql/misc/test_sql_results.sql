-- Test if the previous SQL script worked
-- Run this in Supabase SQL Editor to check

-- Check if data exists
SELECT COUNT(*) as total_count FROM florida_parcels;

-- Check if our specific properties exist  
SELECT parcel_id, phy_addr1, is_redacted FROM florida_parcels 
WHERE phy_addr1 LIKE '%3930%' OR phy_addr1 LIKE '%Ocean%';

-- Check RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'florida_parcels';