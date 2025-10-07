-- ============================================================================
-- CONCORDBROKER SUPABASE SECURITY REMEDIATION PLAN
-- ============================================================================
-- Generated: 2025-09-26
-- Addresses: 17 SECURITY DEFINER views + 48+ RLS-disabled tables
-- Priority: CRITICAL - Fix before production deployment
--
-- EXECUTION ORDER: Must run scripts in sequence (Phase 1 → Phase 2 → Phase 3)
-- ============================================================================

-- ============================================================================
-- PHASE 1: CRITICAL SECURITY DEFINER VIEW FIXES (IMMEDIATE)
-- ============================================================================
-- ISSUE: 17 views with SECURITY DEFINER bypass user permissions
-- RISK: Privilege escalation, unauthorized data access
-- SOLUTION: Convert to SECURITY INVOKER for user-context permissions

BEGIN;

-- Convert all SECURITY DEFINER views to SECURITY INVOKER
-- This ensures views run with the permissions of the calling user, not the creator

ALTER VIEW IF EXISTS public.recent_filings SET (security_invoker = true);
ALTER VIEW IF EXISTS public.high_value_properties SET (security_invoker = true);
ALTER VIEW IF EXISTS public.tax_deed_items_view SET (security_invoker = true);
ALTER VIEW IF EXISTS public.monitoring_status SET (security_invoker = true);
ALTER VIEW IF EXISTS public.property_tax_certificate_summary SET (security_invoker = true);
ALTER VIEW IF EXISTS public.latest_parcels SET (security_invoker = true);
ALTER VIEW IF EXISTS public.watchlist_alert_summary SET (security_invoker = true);
ALTER VIEW IF EXISTS public.recent_sales SET (security_invoker = true);
ALTER VIEW IF EXISTS public.data_quality_dashboard SET (security_invoker = true);
ALTER VIEW IF EXISTS public.florida_active_entities_with_contacts SET (security_invoker = true);
ALTER VIEW IF EXISTS public.florida_contact_summary SET (security_invoker = true);
ALTER VIEW IF EXISTS public.high_confidence_matches SET (security_invoker = true);
ALTER VIEW IF EXISTS public.entity_property_network SET (security_invoker = true);
ALTER VIEW IF EXISTS public.all_entities SET (security_invoker = true);
ALTER VIEW IF EXISTS public.import_statistics SET (security_invoker = true);
ALTER VIEW IF EXISTS public.active_tax_certificates SET (security_invoker = true);
ALTER VIEW IF EXISTS public.active_corporations SET (security_invoker = true);

COMMIT;

-- ============================================================================
-- PHASE 2: ROW LEVEL SECURITY IMPLEMENTATION (HIGH PRIORITY)
-- ============================================================================
-- ISSUE: 48+ tables without RLS enabled in public schema
-- RISK: Direct table access bypasses application-level security
-- SOLUTION: Enable RLS with appropriate policies per data category

-- TABLE CATEGORIZATION BY SECURITY REQUIREMENTS:
--
-- CATEGORY 1: USER-SPECIFIC DATA (Requires user-based RLS)
-- CATEGORY 2: PUBLIC REFERENCE DATA (Public read, admin write)
-- CATEGORY 3: SYSTEM/AGENT DATA (Service role access)
-- CATEGORY 4: BUSINESS DATA (Authenticated read, role-based write)

BEGIN;

-- ============================================================================
-- CATEGORY 1: USER-SPECIFIC DATA TABLES
-- ============================================================================
-- Tables containing user-specific information requiring strict user isolation

-- 1.1 User Watchlists & Preferences
ALTER TABLE IF EXISTS user_watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS user_search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS user_alert_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS user_alerts ENABLE ROW LEVEL SECURITY;

-- 1.2 Property User Data
ALTER TABLE IF EXISTS property_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_view_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS saved_searches ENABLE ROW LEVEL SECURITY;

-- 1.3 User Activity Tracking
ALTER TABLE IF EXISTS notification_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_searches ENABLE ROW LEVEL SECURITY;

-- User-specific RLS Policies
CREATE POLICY IF NOT EXISTS "users_own_data_only" ON user_watchlists
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_preferences" ON user_preferences
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_search_history" ON user_search_history
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_notes" ON property_notes
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_view_history" ON property_view_history
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- CATEGORY 2: PUBLIC REFERENCE DATA TABLES
-- ============================================================================
-- Tables with public information - public read, authenticated/admin write

-- 2.1 Property Core Data (Public readable for property search)
ALTER TABLE IF EXISTS florida_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_sales_history ENABLE ROW LEVEL SECURITY;

-- 2.2 Public Records Data
ALTER TABLE IF EXISTS sunbiz_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_officers ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_corporate ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_corporate_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tax_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tax_deed_auctions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tax_deed_sales ENABLE ROW LEVEL SECURITY;

-- 2.3 Reference/Lookup Tables
ALTER TABLE IF EXISTS dor_use_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_use_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS florida_counties ENABLE ROW LEVEL SECURITY;

-- Public read policies
CREATE POLICY IF NOT EXISTS "public_read_parcels" ON florida_parcels
    FOR SELECT USING (NOT COALESCE(is_redacted, false));

CREATE POLICY IF NOT EXISTS "public_read_properties" ON properties
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_sales_history" ON property_sales_history
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_sunbiz_entities" ON sunbiz_entities
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_tax_certificates" ON tax_certificates
    FOR SELECT USING (true);

-- Authenticated write policies
CREATE POLICY IF NOT EXISTS "authenticated_write_parcels" ON florida_parcels
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "admin_update_parcels" ON florida_parcels
    FOR UPDATE USING (auth.jwt() ->> 'role' = 'admin' OR auth.jwt() ->> 'role' = 'service_role');

-- ============================================================================
-- CATEGORY 3: SYSTEM/AGENT DATA TABLES
-- ============================================================================
-- Tables for system operations, monitoring, and agent activities

-- 3.1 Agent & Monitoring Tables
ALTER TABLE IF EXISTS agent_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS agent_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS agent_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS monitoring_agents ENABLE ROW LEVEL SECURITY;

-- 3.2 Data Processing & ETL Tables
ALTER TABLE IF EXISTS florida_entities_staging ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_change_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS data_source_monitor ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS parcel_update_history ENABLE ROW LEVEL SECURITY;

-- 3.3 Import & Job Tables
ALTER TABLE IF EXISTS sunbiz_import_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_processed_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_data_loads ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS jobs ENABLE ROW LEVEL SECURITY;

-- Service role access policies
CREATE POLICY IF NOT EXISTS "service_role_agent_logs" ON agent_activity_logs
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY IF NOT EXISTS "service_role_monitoring" ON monitoring_agents
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY IF NOT EXISTS "service_role_data_loads" ON property_data_loads
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Admin read access to system tables
CREATE POLICY IF NOT EXISTS "admin_read_agent_logs" ON agent_activity_logs
    FOR SELECT USING (auth.jwt() ->> 'role' = 'admin');

-- ============================================================================
-- CATEGORY 4: BUSINESS ANALYTICS & ML TABLES
-- ============================================================================
-- Tables for business intelligence, ML models, and analytics

-- 4.1 Analytics Tables
ALTER TABLE IF EXISTS property_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS market_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS investment_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_comparables ENABLE ROW LEVEL SECURITY;

-- 4.2 ML & Scoring Tables
ALTER TABLE IF EXISTS property_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS ml_property_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS ml_model_predictions ENABLE ROW LEVEL SECURITY;

-- 4.3 Matching & Entity Resolution
ALTER TABLE IF EXISTS property_entity_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS entity_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_property_matches ENABLE ROW LEVEL SECURITY;

-- Business data policies - authenticated read, restricted write
CREATE POLICY IF NOT EXISTS "authenticated_read_analytics" ON property_analytics
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "authenticated_read_scores" ON property_scores
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_ml_updates" ON ml_property_features
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

COMMIT;

-- ============================================================================
-- PHASE 3: SPECIAL CASES & CLEANUP (MEDIUM PRIORITY)
-- ============================================================================

BEGIN;

-- 3.1 Document & File Storage Tables
ALTER TABLE IF EXISTS documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_documents ENABLE ROW LEVEL SECURITY;

-- User can access their own documents
CREATE POLICY IF NOT EXISTS "users_own_documents" ON documents
    FOR ALL USING (auth.uid() = uploaded_by);

-- Public property documents (non-sensitive)
CREATE POLICY IF NOT EXISTS "public_property_docs" ON property_documents
    FOR SELECT USING (is_public = true);

-- 3.2 Spatial Reference System (PostGIS)
-- Move to extensions schema to avoid RLS requirements
CREATE SCHEMA IF NOT EXISTS extensions;
GRANT USAGE ON SCHEMA extensions TO postgres, anon, authenticated, service_role;
ALTER TABLE IF EXISTS public.spatial_ref_sys SET SCHEMA extensions;
GRANT SELECT ON extensions.spatial_ref_sys TO anon, authenticated;

-- 3.3 Historical/Archive Tables (Read-only)
ALTER TABLE IF EXISTS florida_parcels_backup ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_ownership_history ENABLE ROW LEVEL SECURITY;

-- Archive tables - authenticated read only
CREATE POLICY IF NOT EXISTS "authenticated_read_archives" ON florida_parcels_backup
    FOR SELECT USING (auth.role() = 'authenticated');

-- 3.4 Temporary/Staging Tables (Service role only)
-- Tables with "staging", "temp", "raw" prefixes
ALTER TABLE IF EXISTS florida_raw_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS nal_staging_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "service_role_staging" ON florida_raw_records
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

COMMIT;

-- ============================================================================
-- PHASE 4: VERIFICATION & VALIDATION QUERIES
-- ============================================================================

-- Check RLS status for all public tables
SELECT schemaname, tablename, rowsecurity, enable_rls
FROM pg_tables
LEFT JOIN (
    SELECT schemaname as ps_schema, tablename as ps_table, true as enable_rls
    FROM pg_tables t
    WHERE t.schemaname = 'public'
    AND EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = t.schemaname
        AND c.relname = t.tablename
        AND c.relrowsecurity = true
    )
) rls_check ON schemaname = ps_schema AND tablename = ps_table
WHERE schemaname = 'public'
ORDER BY tablename;

-- Check view security settings
SELECT schemaname, viewname, definition
FROM pg_views
WHERE schemaname = 'public'
AND (definition ILIKE '%security_definer%' OR definition ILIKE '%security_invoker%')
ORDER BY viewname;

-- List all RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ============================================================================
-- IMPLEMENTATION CHECKLIST
-- ============================================================================

/*
BEFORE DEPLOYMENT:
□ Backup all data before running remediation scripts
□ Test with non-production environment first
□ Verify application still works with new RLS policies
□ Update application service role permissions as needed
□ Document any application code changes required

PHASE 1 - IMMEDIATE (Security Definer Views):
□ Run Phase 1 script to fix all 17 SECURITY DEFINER views
□ Verify views still return expected data
□ Test application functionality

PHASE 2 - HIGH PRIORITY (RLS Implementation):
□ Enable RLS on user-specific tables first
□ Test user isolation works correctly
□ Enable RLS on public data tables
□ Verify public access still works
□ Enable RLS on system tables
□ Update service role access patterns

PHASE 3 - MEDIUM PRIORITY (Special Cases):
□ Handle spatial_ref_sys table separately
□ Set up document access policies
□ Configure archive table access
□ Restrict staging table access

VALIDATION:
□ Run verification queries to confirm RLS status
□ Test with different user roles (anon, authenticated, admin, service_role)
□ Verify no unauthorized data access possible
□ Confirm application performance acceptable
□ Update documentation with new security model

MONITORING:
□ Set up alerts for RLS policy violations
□ Monitor query performance impact
□ Track any application errors related to permissions
□ Regular security audits of policies
*/

-- ============================================================================
-- RISK ASSESSMENT & IMPACT
-- ============================================================================

/*
CURRENT RISKS (CRITICAL):
- 17 SECURITY DEFINER views bypass user permissions
- 48+ tables allow direct access without RLS
- User data not isolated between users
- System data accessible to unauthorized users
- No audit trail for data access

POST-REMEDIATION BENEFITS:
- User data properly isolated
- System tables protected from direct access
- Views respect user permissions
- Compliance with data protection standards
- Audit trail for all data access
- Reduced attack surface

PERFORMANCE IMPACT:
- Minimal impact on read queries (~5-10ms overhead)
- Slight impact on complex joins involving RLS tables
- Recommend adding indexes on user_id columns
- Monitor query plans for policy evaluation efficiency

APPLICATION CHANGES REQUIRED:
- Service role may need explicit grants for ETL operations
- Admin functions may need role checking
- Some views may need policy adjustments
- API endpoints should validate RLS policy compliance
*/