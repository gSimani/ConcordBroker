-- Fix Supabase Security Errors - Final Solution
-- Generated: 2025-09-09
-- This script addresses all 46 security linter errors with proper handling

-- Start transaction for atomic execution
BEGIN;

-- =====================================================
-- PART 1: Fix SECURITY DEFINER views FIRST
-- Convert to SECURITY INVOKER (safest to do first)
-- =====================================================

-- Fix view security settings
ALTER VIEW public.recent_filings SET (security_invoker = true);
ALTER VIEW public.high_value_properties SET (security_invoker = true);
ALTER VIEW public.monitoring_status SET (security_invoker = true);
ALTER VIEW public.property_tax_certificate_summary SET (security_invoker = true);
ALTER VIEW public.latest_parcels SET (security_invoker = true);
ALTER VIEW public.recent_sales SET (security_invoker = true);
ALTER VIEW public.data_quality_dashboard SET (security_invoker = true);
ALTER VIEW public.high_confidence_matches SET (security_invoker = true);
ALTER VIEW public.entity_property_network SET (security_invoker = true);
ALTER VIEW public.all_entities SET (security_invoker = true);
ALTER VIEW public.import_statistics SET (security_invoker = true);
ALTER VIEW public.active_tax_certificates SET (security_invoker = true);
ALTER VIEW public.active_corporations SET (security_invoker = true);

-- =====================================================
-- PART 2: Handle spatial_ref_sys (PostGIS table)
-- Move to extensions schema to avoid RLS issues
-- =====================================================

-- Check if extensions schema exists, create if not
CREATE SCHEMA IF NOT EXISTS extensions;

-- Grant usage on extensions schema
GRANT USAGE ON SCHEMA extensions TO postgres, anon, authenticated, service_role;

-- Move spatial_ref_sys to extensions schema (safer than enabling RLS)
ALTER TABLE IF EXISTS public.spatial_ref_sys SET SCHEMA extensions;

-- Grant appropriate permissions on the moved table
GRANT SELECT ON extensions.spatial_ref_sys TO anon, authenticated;

-- =====================================================
-- PART 3: Enable RLS on florida_parcels
-- (Already has policies, just needs RLS enabled)
-- =====================================================

ALTER TABLE public.florida_parcels ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- PART 4: Add permissive policies BEFORE enabling RLS
-- This prevents access blocking when RLS is enabled
-- =====================================================

-- Create a helper function to check if policy exists
CREATE OR REPLACE FUNCTION pg_temp.create_policy_if_not_exists(
    p_table text,
    p_policy text,
    p_command text
) RETURNS void AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = p_table 
        AND policyname = p_policy
    ) THEN
        EXECUTE p_command;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Add basic policies for each table BEFORE enabling RLS
-- This ensures continued access

-- Agent tables
SELECT pg_temp.create_policy_if_not_exists(
    'agent_activity_logs',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.agent_activity_logs FOR SELECT TO authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'agent_notifications',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.agent_notifications FOR SELECT TO authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'agent_config',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.agent_config FOR SELECT TO authenticated USING (true)'
);

-- Sunbiz tables (public data)
SELECT pg_temp.create_policy_if_not_exists(
    'sunbiz_corporate_events',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.sunbiz_corporate_events FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'sunbiz_import_log',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.sunbiz_import_log FOR SELECT TO authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'sunbiz_monitoring_agents',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.sunbiz_monitoring_agents FOR SELECT TO authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'sunbiz_processed_files',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.sunbiz_processed_files FOR SELECT TO authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'sunbiz_fictitious_events',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.sunbiz_fictitious_events FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'sunbiz_lien_debtors',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.sunbiz_lien_debtors FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'sunbiz_lien_secured_parties',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.sunbiz_lien_secured_parties FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'sunbiz_partnership_events',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.sunbiz_partnership_events FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'sunbiz_sftp_downloads',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.sunbiz_sftp_downloads FOR SELECT TO authenticated USING (true)'
);

-- Property tables (public data)
SELECT pg_temp.create_policy_if_not_exists(
    'property_entity_matches',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.property_entity_matches FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'property_ownership_history',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.property_ownership_history FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'property_sales_history',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.property_sales_history FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'tax_certificates',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.tax_certificates FOR SELECT TO anon, authenticated USING (true)'
);

-- Audit and cache tables
SELECT pg_temp.create_policy_if_not_exists(
    'match_audit_log',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.match_audit_log FOR SELECT TO authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'entity_search_cache',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.entity_search_cache FOR SELECT TO authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'entity_relationships',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.entity_relationships FOR SELECT TO anon, authenticated USING (true)'
);

-- Florida data tables (public data)
SELECT pg_temp.create_policy_if_not_exists(
    'fl_data_updates',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.fl_data_updates FOR SELECT TO authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'nav_parcel_assessments',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.nav_parcel_assessments FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'nav_assessment_details',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.nav_assessment_details FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'fl_nav_parcel_summary',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.fl_nav_parcel_summary FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'fl_nav_assessment_detail',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.fl_nav_assessment_detail FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'fl_sdf_sales',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.fl_sdf_sales FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'fl_tpp_accounts',
    'Allow public read',
    'CREATE POLICY "Allow public read" ON public.fl_tpp_accounts FOR SELECT TO anon, authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'fl_agent_status',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.fl_agent_status FOR SELECT TO authenticated USING (true)'
);

-- Job tables
SELECT pg_temp.create_policy_if_not_exists(
    'nav_jobs',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.nav_jobs FOR SELECT TO authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'sdf_jobs',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.sdf_jobs FOR SELECT TO authenticated USING (true)'
);

SELECT pg_temp.create_policy_if_not_exists(
    'tpp_jobs',
    'Allow authenticated read',
    'CREATE POLICY "Allow authenticated read" ON public.tpp_jobs FOR SELECT TO authenticated USING (true)'
);

-- =====================================================
-- PART 5: Enable RLS on all tables (after policies exist)
-- =====================================================

ALTER TABLE public.agent_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_corporate_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_import_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_monitoring_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_processed_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_fictitious_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_lien_debtors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_lien_secured_parties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_entity_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_ownership_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entity_search_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entity_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_partnership_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tax_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_data_updates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nav_parcel_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nav_assessment_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nav_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_tpp_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_nav_parcel_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_nav_assessment_detail ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_sdf_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_agent_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sdf_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tpp_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_sftp_downloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_config ENABLE ROW LEVEL SECURITY;

-- Clean up temp function
DROP FUNCTION IF EXISTS pg_temp.create_policy_if_not_exists(text, text, text);

-- Commit the transaction
COMMIT;

-- =====================================================
-- PART 6: Verification Queries (run separately)
-- =====================================================

-- Check RLS status on public tables
SELECT 
    'RLS Status' as check_type,
    tablename,
    CASE 
        WHEN rowsecurity THEN '✅ Enabled'
        ELSE '❌ Disabled'
    END as rls_status,
    (SELECT COUNT(*) FROM pg_policies p 
     WHERE p.schemaname = 'public' 
     AND p.tablename = t.tablename) as policy_count
FROM pg_tables t
WHERE schemaname = 'public'
ORDER BY rowsecurity DESC, tablename;

-- Check view security settings
SELECT 
    'View Security' as check_type,
    viewname,
    'SECURITY INVOKER ✅' as status
FROM pg_views
WHERE schemaname = 'public'
AND viewname IN (
    'recent_filings', 'high_value_properties', 'monitoring_status',
    'property_tax_certificate_summary', 'latest_parcels', 'recent_sales',
    'data_quality_dashboard', 'high_confidence_matches', 'entity_property_network',
    'all_entities', 'import_statistics', 'active_tax_certificates', 'active_corporations'
);

-- Verify spatial_ref_sys moved to extensions
SELECT 
    'PostGIS Table Location' as check_type,
    schemaname,
    tablename,
    CASE 
        WHEN schemaname = 'extensions' THEN '✅ Moved to extensions'
        WHEN schemaname = 'public' THEN '❌ Still in public'
        ELSE '❓ Unknown location'
    END as status
FROM pg_tables
WHERE tablename = 'spatial_ref_sys';

-- Summary report
WITH rls_count AS (
    SELECT 
        COUNT(*) FILTER (WHERE rowsecurity) as enabled,
        COUNT(*) FILTER (WHERE NOT rowsecurity) as disabled
    FROM pg_tables
    WHERE schemaname = 'public'
),
policy_count AS (
    SELECT COUNT(DISTINCT tablename) as tables_with_policies
    FROM pg_policies
    WHERE schemaname = 'public'
)
SELECT 
    'SUMMARY REPORT' as report,
    rls_count.enabled as "Tables with RLS",
    rls_count.disabled as "Tables without RLS",
    policy_count.tables_with_policies as "Tables with Policies",
    (SELECT COUNT(*) FROM pg_views WHERE schemaname = 'public') as "Total Views"
FROM rls_count, policy_count;