-- Fix RLS Policies for Data Loading
-- Execute this in Supabase SQL Editor: https://supabase.com/dashboard/project/YOUR_PROJECT/sql

-- ============================================================================
-- OPTION 1: Temporarily Disable RLS (Recommended for Bulk Load)
-- ============================================================================

-- Disable RLS on florida_parcels for bulk data loading
ALTER TABLE florida_parcels DISABLE ROW LEVEL SECURITY;

-- After loading data, re-enable with:
-- ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- OPTION 2: Create Permissive Policy for Service Role (More Secure)
-- ============================================================================

-- First, ensure RLS is enabled
-- ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;

-- Create policy allowing service role full access
-- CREATE POLICY "service_role_full_access"
-- ON florida_parcels
-- FOR ALL
-- TO service_role
-- USING (true)
-- WITH CHECK (true);

-- ============================================================================
-- OPTION 3: Create Policies for All Tables (Complete Solution)
-- ============================================================================

-- Apply to all Sunbiz tables
-- DO $$
-- BEGIN
--     -- florida_parcels
--     ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;
--     DROP POLICY IF EXISTS "service_role_full_access" ON florida_parcels;
--     CREATE POLICY "service_role_full_access" ON florida_parcels
--         FOR ALL TO service_role USING (true) WITH CHECK (true);
--
--     -- sunbiz_corporate
--     ALTER TABLE sunbiz_corporate ENABLE ROW LEVEL SECURITY;
--     DROP POLICY IF EXISTS "service_role_full_access" ON sunbiz_corporate;
--     CREATE POLICY "service_role_full_access" ON sunbiz_corporate
--         FOR ALL TO service_role USING (true) WITH CHECK (true);
--
--     -- florida_entities
--     ALTER TABLE florida_entities ENABLE ROW LEVEL SECURITY;
--     DROP POLICY IF EXISTS "service_role_full_access" ON florida_entities;
--     CREATE POLICY "service_role_full_access" ON florida_entities
--         FOR ALL TO service_role USING (true) WITH CHECK (true);
--
--     -- property_sales_history
--     ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;
--     DROP POLICY IF EXISTS "service_role_full_access" ON property_sales_history;
--     CREATE POLICY "service_role_full_access" ON property_sales_history
--         FOR ALL TO service_role USING (true) WITH CHECK (true);
--
--     -- sunbiz_officer_contacts
--     ALTER TABLE sunbiz_officer_contacts ENABLE ROW LEVEL SECURITY;
--     DROP POLICY IF EXISTS "service_role_full_access" ON sunbiz_officer_contacts;
--     CREATE POLICY "service_role_full_access" ON sunbiz_officer_contacts
--         FOR ALL TO service_role USING (true) WITH CHECK (true);
-- END $$;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check current RLS status
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN (
        'florida_parcels',
        'sunbiz_corporate',
        'florida_entities',
        'property_sales_history',
        'sunbiz_officer_contacts'
    )
ORDER BY tablename;

-- Check existing policies
SELECT
    schemaname,
    tablename,
    policyname,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
    AND tablename IN (
        'florida_parcels',
        'sunbiz_corporate',
        'florida_entities',
        'property_sales_history',
        'sunbiz_officer_contacts'
    )
ORDER BY tablename, policyname;

-- ============================================================================
-- After Data Loading: Create Proper RLS Policies
-- ============================================================================

-- Example: Allow authenticated users to read all data
-- CREATE POLICY "authenticated_read_all"
-- ON florida_parcels
-- FOR SELECT
-- TO authenticated
-- USING (true);

-- Example: Allow service role to do everything
-- CREATE POLICY "service_role_full_access"
-- ON florida_parcels
-- FOR ALL
-- TO service_role
-- USING (true)
-- WITH CHECK (true);

-- Example: Allow anon users to read specific counties
-- CREATE POLICY "anon_read_specific_counties"
-- ON florida_parcels
-- FOR SELECT
-- TO anon
-- USING (county IN ('BROWARD', 'MIAMI-DADE', 'PALM BEACH'));
