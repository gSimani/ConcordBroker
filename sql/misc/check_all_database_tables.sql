-- Check all tables in your Supabase database
-- Run this in SQL Editor to see what tables exist

-- 1. List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 2. Count records in each relevant table
SELECT 
    'florida_parcels' as table_name, 
    COUNT(*) as record_count 
FROM florida_parcels
UNION ALL
SELECT 
    'fl_nav_assessment_detail' as table_name, 
    COUNT(*) as record_count 
FROM fl_nav_assessment_detail
UNION ALL
SELECT 
    'fl_sdf_sales' as table_name, 
    COUNT(*) as record_count 
FROM fl_sdf_sales
UNION ALL
SELECT 
    'fl_tpp_accounts' as table_name, 
    COUNT(*) as record_count 
FROM fl_tpp_accounts;

-- 3. Check if we have data from the 2025 files
SELECT DISTINCT county, year, COUNT(*) as property_count
FROM florida_parcels
GROUP BY county, year
ORDER BY county, year;