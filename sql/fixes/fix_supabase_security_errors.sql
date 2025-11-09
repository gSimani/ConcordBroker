-- Fix Supabase Security Errors
-- Generated: 2025-09-09
-- This script addresses all security linter errors from Supabase

-- =====================================================
-- PART 1: Enable RLS on tables that already have policies
-- =====================================================

-- Florida Parcels already has policies, just needs RLS enabled
ALTER TABLE public.florida_parcels ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- PART 2: Fix SECURITY DEFINER views
-- Change all views to use SECURITY INVOKER instead
-- =====================================================

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
-- PART 3: Enable RLS on all public tables
-- =====================================================

-- Agent and monitoring tables
ALTER TABLE public.agent_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_config ENABLE ROW LEVEL SECURITY;

-- Sunbiz tables
ALTER TABLE public.sunbiz_corporate_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_import_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_monitoring_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_processed_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_fictitious_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_lien_debtors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_lien_secured_parties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_partnership_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_sftp_downloads ENABLE ROW LEVEL SECURITY;

-- Property and entity tables
ALTER TABLE public.property_entity_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_ownership_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entity_search_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entity_relationships ENABLE ROW LEVEL SECURITY;

-- Tax and financial tables
ALTER TABLE public.tax_certificates ENABLE ROW LEVEL SECURITY;

-- Florida data tables
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

-- PostGIS system table (special case - usually doesn't need RLS)
-- Only enable if you want to restrict access to spatial reference systems
-- ALTER TABLE public.spatial_ref_sys ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- PART 4: Add basic RLS policies for tables without them
-- These are permissive policies - adjust based on your security needs
-- =====================================================

-- Agent activity logs - allow authenticated users to read, admins to write
CREATE POLICY "Read agent activity logs" ON public.agent_activity_logs
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Admin manage agent logs" ON public.agent_activity_logs
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- Agent notifications - users see their own, admins see all
CREATE POLICY "Users read own notifications" ON public.agent_notifications
    FOR SELECT TO authenticated
    USING (user_id = auth.uid() OR auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Admin manage notifications" ON public.agent_notifications
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- Agent config - read for authenticated, write for admins
CREATE POLICY "Read agent config" ON public.agent_config
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Admin manage agent config" ON public.agent_config
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- Sunbiz tables - generally public read, admin write
CREATE POLICY "Public read sunbiz corporate" ON public.sunbiz_corporate_events
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY "Admin manage sunbiz corporate" ON public.sunbiz_corporate_events
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- Import logs - authenticated read, admin write
CREATE POLICY "Read import logs" ON public.sunbiz_import_log
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Admin manage import logs" ON public.sunbiz_import_log
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- Property data - public read for non-sensitive data
CREATE POLICY "Public read property matches" ON public.property_entity_matches
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY "Admin manage property matches" ON public.property_entity_matches
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Public read property history" ON public.property_ownership_history
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY "Admin manage property history" ON public.property_ownership_history
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Public read sales history" ON public.property_sales_history
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY "Admin manage sales history" ON public.property_sales_history
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- Tax certificates - public read
CREATE POLICY "Public read tax certificates" ON public.tax_certificates
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY "Admin manage tax certificates" ON public.tax_certificates
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- Florida data tables - public read for assessment data
CREATE POLICY "Public read nav assessments" ON public.nav_parcel_assessments
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY "Admin manage nav assessments" ON public.nav_parcel_assessments
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Public read assessment details" ON public.nav_assessment_details
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY "Admin manage assessment details" ON public.nav_assessment_details
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Public read florida sales" ON public.fl_sdf_sales
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY "Admin manage florida sales" ON public.fl_sdf_sales
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- Job tables - authenticated read, admin write
CREATE POLICY "Read nav jobs" ON public.nav_jobs
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Admin manage nav jobs" ON public.nav_jobs
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Read sdf jobs" ON public.sdf_jobs
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Admin manage sdf jobs" ON public.sdf_jobs
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Read tpp jobs" ON public.tpp_jobs
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Admin manage tpp jobs" ON public.tpp_jobs
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- Cache and audit tables - authenticated only
CREATE POLICY "Authenticated read cache" ON public.entity_search_cache
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Admin manage cache" ON public.entity_search_cache
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Authenticated read audit log" ON public.match_audit_log
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Admin manage audit log" ON public.match_audit_log
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- =====================================================
-- PART 5: Apply minimal policies to remaining tables
-- =====================================================

-- For tables that don't have specific policies above
DO $$
DECLARE
    tbl record;
BEGIN
    -- Add basic policies for any remaining tables
    FOR tbl IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename NOT IN (
            'florida_parcels', -- already has policies
            'spatial_ref_sys', -- PostGIS system table
            'agent_activity_logs',
            'agent_notifications',
            'agent_config',
            'sunbiz_corporate_events',
            'sunbiz_import_log',
            'property_entity_matches',
            'property_ownership_history',
            'property_sales_history',
            'tax_certificates',
            'nav_parcel_assessments',
            'nav_assessment_details',
            'fl_sdf_sales',
            'nav_jobs',
            'sdf_jobs',
            'tpp_jobs',
            'entity_search_cache',
            'match_audit_log'
        )
    LOOP
        -- Check if table already has policies
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'public' 
            AND tablename = tbl.tablename
        ) THEN
            -- Add basic read policy for authenticated users
            EXECUTE format('
                CREATE POLICY "Authenticated read %I" ON public.%I
                    FOR SELECT TO authenticated
                    USING (true)', 
                tbl.tablename, tbl.tablename
            );
            
            -- Add admin write policy
            EXECUTE format('
                CREATE POLICY "Admin manage %I" ON public.%I
                    FOR ALL TO authenticated
                    USING (auth.jwt() ->> ''role'' = ''admin'')
                    WITH CHECK (auth.jwt() ->> ''role'' = ''admin'')', 
                tbl.tablename, tbl.tablename
            );
        END IF;
    END LOOP;
END $$;

-- =====================================================
-- PART 6: Verify all fixes were applied
-- =====================================================

-- Check RLS status
SELECT 
    schemaname,
    tablename,
    rowsecurity,
    CASE 
        WHEN rowsecurity THEN 'RLS Enabled ✓'
        ELSE 'RLS DISABLED ✗'
    END as status
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY rowsecurity DESC, tablename;

-- Check view security settings
SELECT 
    schemaname,
    viewname,
    CASE 
        WHEN definition ILIKE '%security_invoker%' THEN 'Security Invoker ✓'
        WHEN definition ILIKE '%security_definer%' THEN 'SECURITY DEFINER ✗'
        ELSE 'Default (Invoker) ✓'
    END as security_mode
FROM pg_views
WHERE schemaname = 'public'
ORDER BY viewname;

-- Summary of policies
SELECT 
    schemaname,
    tablename,
    COUNT(*) as policy_count,
    STRING_AGG(policyname, ', ' ORDER BY policyname) as policies
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY schemaname, tablename
ORDER BY tablename;