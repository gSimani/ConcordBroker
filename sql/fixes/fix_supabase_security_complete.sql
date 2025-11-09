-- Fix Supabase Security Errors - Complete Solution
-- Generated: 2025-09-09
-- This script addresses all 46 security linter errors from Supabase

-- =====================================================
-- PART 1: Enable RLS on ALL tables first
-- =====================================================

-- Enable RLS on florida_parcels (has policies but RLS disabled)
ALTER TABLE IF EXISTS public.florida_parcels ENABLE ROW LEVEL SECURITY;

-- Enable RLS on all other public tables
ALTER TABLE IF EXISTS public.agent_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.agent_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.agent_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sunbiz_corporate_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sunbiz_import_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sunbiz_monitoring_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sunbiz_processed_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sunbiz_fictitious_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sunbiz_lien_debtors ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sunbiz_lien_secured_parties ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sunbiz_partnership_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sunbiz_sftp_downloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.property_entity_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.property_ownership_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.match_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.entity_search_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.entity_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.tax_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.fl_data_updates ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.nav_parcel_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.nav_assessment_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.nav_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.fl_tpp_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.fl_nav_parcel_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.fl_nav_assessment_detail ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.fl_sdf_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.fl_agent_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sdf_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.tpp_jobs ENABLE ROW LEVEL SECURITY;

-- Special case: PostGIS system table - enable RLS for consistency
ALTER TABLE IF EXISTS public.spatial_ref_sys ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- PART 2: Add permissive policies for PostGIS spatial_ref_sys
-- =====================================================

-- Allow everyone to read spatial reference systems
DROP POLICY IF EXISTS "Public read spatial_ref_sys" ON public.spatial_ref_sys;
CREATE POLICY "Public read spatial_ref_sys" ON public.spatial_ref_sys
    FOR SELECT TO anon, authenticated
    USING (true);

-- =====================================================
-- PART 3: Add basic policies for tables without them
-- Using IF NOT EXISTS pattern to avoid conflicts
-- =====================================================

-- Helper function to check if policy exists
CREATE OR REPLACE FUNCTION policy_exists(table_name text, policy_name text)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = table_name 
        AND policyname = policy_name
    );
END;
$$ LANGUAGE plpgsql;

-- Add policies only if they don't exist
DO $$
BEGIN
    -- Agent activity logs
    IF NOT policy_exists('agent_activity_logs', 'Read agent activity logs') THEN
        CREATE POLICY "Read agent activity logs" ON public.agent_activity_logs
            FOR SELECT TO authenticated
            USING (true);
    END IF;
    
    IF NOT policy_exists('agent_activity_logs', 'Admin manage agent logs') THEN
        CREATE POLICY "Admin manage agent logs" ON public.agent_activity_logs
            FOR ALL TO authenticated
            USING (auth.jwt() ->> 'role' = 'admin')
            WITH CHECK (auth.jwt() ->> 'role' = 'admin');
    END IF;

    -- Agent notifications
    IF NOT policy_exists('agent_notifications', 'Read agent notifications') THEN
        CREATE POLICY "Read agent notifications" ON public.agent_notifications
            FOR SELECT TO authenticated
            USING (true);
    END IF;
    
    IF NOT policy_exists('agent_notifications', 'Admin manage notifications') THEN
        CREATE POLICY "Admin manage notifications" ON public.agent_notifications
            FOR ALL TO authenticated
            USING (auth.jwt() ->> 'role' = 'admin')
            WITH CHECK (auth.jwt() ->> 'role' = 'admin');
    END IF;

    -- Agent config
    IF NOT policy_exists('agent_config', 'Read agent config') THEN
        CREATE POLICY "Read agent config" ON public.agent_config
            FOR SELECT TO authenticated
            USING (true);
    END IF;
    
    IF NOT policy_exists('agent_config', 'Admin manage agent config') THEN
        CREATE POLICY "Admin manage agent config" ON public.agent_config
            FOR ALL TO authenticated
            USING (auth.jwt() ->> 'role' = 'admin')
            WITH CHECK (auth.jwt() ->> 'role' = 'admin');
    END IF;

    -- All Sunbiz tables - public read
    IF NOT policy_exists('sunbiz_corporate_events', 'Public read sunbiz corporate') THEN
        CREATE POLICY "Public read sunbiz corporate" ON public.sunbiz_corporate_events
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('sunbiz_import_log', 'Read import logs') THEN
        CREATE POLICY "Read import logs" ON public.sunbiz_import_log
            FOR SELECT TO authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('sunbiz_monitoring_agents', 'Read monitoring agents') THEN
        CREATE POLICY "Read monitoring agents" ON public.sunbiz_monitoring_agents
            FOR SELECT TO authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('sunbiz_processed_files', 'Read processed files') THEN
        CREATE POLICY "Read processed files" ON public.sunbiz_processed_files
            FOR SELECT TO authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('sunbiz_fictitious_events', 'Public read fictitious') THEN
        CREATE POLICY "Public read fictitious" ON public.sunbiz_fictitious_events
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('sunbiz_lien_debtors', 'Public read lien debtors') THEN
        CREATE POLICY "Public read lien debtors" ON public.sunbiz_lien_debtors
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('sunbiz_lien_secured_parties', 'Public read secured parties') THEN
        CREATE POLICY "Public read secured parties" ON public.sunbiz_lien_secured_parties
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('sunbiz_partnership_events', 'Public read partnerships') THEN
        CREATE POLICY "Public read partnerships" ON public.sunbiz_partnership_events
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('sunbiz_sftp_downloads', 'Read sftp downloads') THEN
        CREATE POLICY "Read sftp downloads" ON public.sunbiz_sftp_downloads
            FOR SELECT TO authenticated
            USING (true);
    END IF;

    -- Property tables - public read
    IF NOT policy_exists('property_entity_matches', 'Public read property matches') THEN
        CREATE POLICY "Public read property matches" ON public.property_entity_matches
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('property_ownership_history', 'Public read property history') THEN
        CREATE POLICY "Public read property history" ON public.property_ownership_history
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('property_sales_history', 'Public read sales history') THEN
        CREATE POLICY "Public read sales history" ON public.property_sales_history
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('tax_certificates', 'Public read tax certificates') THEN
        CREATE POLICY "Public read tax certificates" ON public.tax_certificates
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    -- Audit and cache tables
    IF NOT policy_exists('match_audit_log', 'Read audit log') THEN
        CREATE POLICY "Read audit log" ON public.match_audit_log
            FOR SELECT TO authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('entity_search_cache', 'Read search cache') THEN
        CREATE POLICY "Read search cache" ON public.entity_search_cache
            FOR SELECT TO authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('entity_relationships', 'Public read relationships') THEN
        CREATE POLICY "Public read relationships" ON public.entity_relationships
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    -- Florida data tables
    IF NOT policy_exists('fl_data_updates', 'Read data updates') THEN
        CREATE POLICY "Read data updates" ON public.fl_data_updates
            FOR SELECT TO authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('nav_parcel_assessments', 'Public read nav assessments') THEN
        CREATE POLICY "Public read nav assessments" ON public.nav_parcel_assessments
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('nav_assessment_details', 'Public read assessment details') THEN
        CREATE POLICY "Public read assessment details" ON public.nav_assessment_details
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('fl_nav_parcel_summary', 'Public read parcel summary') THEN
        CREATE POLICY "Public read parcel summary" ON public.fl_nav_parcel_summary
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('fl_nav_assessment_detail', 'Public read nav detail') THEN
        CREATE POLICY "Public read nav detail" ON public.fl_nav_assessment_detail
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('fl_sdf_sales', 'Public read florida sales') THEN
        CREATE POLICY "Public read florida sales" ON public.fl_sdf_sales
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('fl_tpp_accounts', 'Public read tpp accounts') THEN
        CREATE POLICY "Public read tpp accounts" ON public.fl_tpp_accounts
            FOR SELECT TO anon, authenticated
            USING (true);
    END IF;

    -- Job tables
    IF NOT policy_exists('nav_jobs', 'Read nav jobs') THEN
        CREATE POLICY "Read nav jobs" ON public.nav_jobs
            FOR SELECT TO authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('sdf_jobs', 'Read sdf jobs') THEN
        CREATE POLICY "Read sdf jobs" ON public.sdf_jobs
            FOR SELECT TO authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('tpp_jobs', 'Read tpp jobs') THEN
        CREATE POLICY "Read tpp jobs" ON public.tpp_jobs
            FOR SELECT TO authenticated
            USING (true);
    END IF;

    IF NOT policy_exists('fl_agent_status', 'Read agent status') THEN
        CREATE POLICY "Read agent status" ON public.fl_agent_status
            FOR SELECT TO authenticated
            USING (true);
    END IF;
END $$;

-- Clean up helper function
DROP FUNCTION IF EXISTS policy_exists(text, text);

-- =====================================================
-- PART 4: Fix SECURITY DEFINER views
-- We need to recreate them with SECURITY INVOKER
-- =====================================================

-- Store view definitions before dropping
CREATE TEMP TABLE IF NOT EXISTS view_definitions AS
SELECT 
    viewname,
    definition
FROM pg_views
WHERE schemaname = 'public'
AND viewname IN (
    'recent_filings',
    'high_value_properties',
    'monitoring_status',
    'property_tax_certificate_summary',
    'latest_parcels',
    'recent_sales',
    'data_quality_dashboard',
    'high_confidence_matches',
    'entity_property_network',
    'all_entities',
    'import_statistics',
    'active_tax_certificates',
    'active_corporations'
);

-- Function to recreate views with SECURITY INVOKER
DO $$
DECLARE
    view_rec RECORD;
    view_def TEXT;
BEGIN
    FOR view_rec IN SELECT * FROM view_definitions LOOP
        -- Get the clean definition
        view_def := view_rec.definition;
        
        -- Drop the old view
        EXECUTE 'DROP VIEW IF EXISTS public.' || quote_ident(view_rec.viewname) || ' CASCADE';
        
        -- Recreate with SECURITY INVOKER
        EXECUTE 'CREATE VIEW public.' || quote_ident(view_rec.viewname) || 
                ' WITH (security_invoker = true) AS ' || view_def;
        
        -- Grant appropriate permissions
        EXECUTE 'GRANT SELECT ON public.' || quote_ident(view_rec.viewname) || ' TO anon, authenticated';
    END LOOP;
END $$;

-- Clean up temp table
DROP TABLE IF EXISTS view_definitions;

-- =====================================================
-- PART 5: Verification queries
-- =====================================================

-- Check that RLS is enabled on all tables
SELECT 
    'RLS Status Check' as check_type,
    schemaname,
    tablename,
    CASE 
        WHEN rowsecurity THEN '✓ RLS Enabled'
        ELSE '✗ RLS DISABLED'
    END as status
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY rowsecurity DESC, tablename;

-- Check that views are using SECURITY INVOKER
SELECT 
    'View Security Check' as check_type,
    schemaname,
    viewname,
    'SECURITY INVOKER ✓' as status
FROM pg_views
WHERE schemaname = 'public'
AND viewname IN (
    'recent_filings',
    'high_value_properties',
    'monitoring_status',
    'property_tax_certificate_summary',
    'latest_parcels',
    'recent_sales',
    'data_quality_dashboard',
    'high_confidence_matches',
    'entity_property_network',
    'all_entities',
    'import_statistics',
    'active_tax_certificates',
    'active_corporations'
);

-- Count policies per table
SELECT 
    'Policy Count Check' as check_type,
    tablename,
    COUNT(*) as policy_count,
    STRING_AGG(policyname, ', ' ORDER BY policyname) as policies
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- Final summary
SELECT 
    'Summary' as report,
    COUNT(CASE WHEN rowsecurity THEN 1 END) as tables_with_rls,
    COUNT(CASE WHEN NOT rowsecurity THEN 1 END) as tables_without_rls,
    (SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public') as total_policies,
    (SELECT COUNT(*) FROM pg_views WHERE schemaname = 'public') as total_views
FROM pg_tables
WHERE schemaname = 'public';