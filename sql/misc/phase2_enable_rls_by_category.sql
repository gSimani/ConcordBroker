-- ============================================================================
-- PHASE 2: ROW LEVEL SECURITY IMPLEMENTATION BY CATEGORY
-- ============================================================================
-- HIGH PRIORITY - Execute after Phase 1 completion and verification
-- Addresses 48+ tables without RLS in systematic, category-based approach
--
-- STRATEGY: Enable RLS by data sensitivity category to minimize disruption
-- ORDER: User data → Public data → System data → Analytics data
-- ============================================================================

-- ============================================================================
-- CATEGORY 1: USER-SPECIFIC DATA (HIGHEST PRIORITY)
-- ============================================================================
-- Tables containing user-specific information requiring strict user isolation
-- RISK: User data leakage between accounts
-- SOLUTION: User-scoped RLS policies

BEGIN;

-- 1.1 Enable RLS on user-specific tables
ALTER TABLE IF EXISTS user_watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS user_search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS user_alert_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS user_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_view_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS saved_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS notification_history ENABLE ROW LEVEL SECURITY;

-- 1.2 Create user isolation policies
-- Users can only access their own data

CREATE POLICY IF NOT EXISTS "users_own_watchlists" ON user_watchlists
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_preferences" ON user_preferences
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_search_history" ON user_search_history
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_alert_preferences" ON user_alert_preferences
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_alerts" ON user_alerts
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_property_notes" ON property_notes
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_view_history" ON property_view_history
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_watchlist_items" ON property_watchlist
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_saved_searches" ON saved_searches
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_own_notifications" ON notification_history
    FOR ALL USING (auth.uid() = user_id);

COMMIT;

-- Verification checkpoint for Category 1
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM pg_tables t
    WHERE t.schemaname = 'public'
    AND t.tablename LIKE ANY(ARRAY['user_%', '%_history', 'property_notes', 'saved_searches', 'notification_history'])
    AND EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = t.schemaname
        AND c.relname = t.tablename
        AND c.relrowsecurity = true
    );

    RAISE NOTICE 'CATEGORY 1 COMPLETE: % user-specific tables now have RLS enabled', table_count;
END $$;

-- ============================================================================
-- CATEGORY 2: PUBLIC REFERENCE DATA (MEDIUM PRIORITY)
-- ============================================================================
-- Tables with public information - public read access, controlled write access
-- RISK: Unauthorized data modification
-- SOLUTION: Public read, authenticated/admin write policies

BEGIN;

-- 2.1 Enable RLS on public reference tables
ALTER TABLE IF EXISTS florida_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_officers ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_corporate ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_corporate_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tax_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tax_deed_auctions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tax_deed_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tax_liens ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS building_permits ENABLE ROW LEVEL SECURITY;

-- 2.2 Reference/lookup tables
ALTER TABLE IF EXISTS dor_use_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_use_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS florida_counties ENABLE ROW LEVEL SECURITY;

-- 2.3 Create public read policies
-- Allow public read access to non-sensitive property data

CREATE POLICY IF NOT EXISTS "public_read_non_redacted_parcels" ON florida_parcels
    FOR SELECT USING (NOT COALESCE(is_redacted, false));

CREATE POLICY IF NOT EXISTS "public_read_properties" ON properties
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_sales_history" ON property_sales_history
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_sunbiz_entities" ON sunbiz_entities
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_sunbiz_officers" ON sunbiz_officers
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_tax_certificates" ON tax_certificates
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_tax_auctions" ON tax_deed_auctions
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_building_permits" ON building_permits
    FOR SELECT USING (true);

-- Reference data - public read access
CREATE POLICY IF NOT EXISTS "public_read_use_codes" ON dor_use_codes
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_property_use_codes" ON property_use_codes
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_counties" ON florida_counties
    FOR SELECT USING (true);

-- 2.4 Create authenticated write policies
-- Allow authenticated users to insert, admin/service role to update

CREATE POLICY IF NOT EXISTS "authenticated_insert_parcels" ON florida_parcels
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_update_parcels" ON florida_parcels
    FOR UPDATE USING (
        auth.jwt() ->> 'role' IN ('admin', 'service_role') OR
        auth.jwt() ->> 'email' = 'system@concordbroker.com'
    );

CREATE POLICY IF NOT EXISTS "service_role_update_properties" ON properties
    FOR UPDATE USING (auth.jwt() ->> 'role' IN ('admin', 'service_role'));

CREATE POLICY IF NOT EXISTS "service_role_insert_sales" ON property_sales_history
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' IN ('authenticated', 'service_role'));

COMMIT;

-- Verification checkpoint for Category 2
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM pg_tables t
    WHERE t.schemaname = 'public'
    AND t.tablename LIKE ANY(ARRAY['florida_%', 'properties', 'property_sales_%', 'sunbiz_%', 'tax_%', 'building_permits', 'dor_%'])
    AND EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = t.schemaname
        AND c.relname = t.tablename
        AND c.relrowsecurity = true
    );

    RAISE NOTICE 'CATEGORY 2 COMPLETE: % public reference tables now have RLS enabled', table_count;
END $$;

-- ============================================================================
-- CATEGORY 3: SYSTEM/AGENT DATA (MEDIUM PRIORITY)
-- ============================================================================
-- Tables for system operations, monitoring, and agent activities
-- RISK: Unauthorized system access, data corruption
-- SOLUTION: Service role and admin access only

BEGIN;

-- 3.1 Enable RLS on system tables
ALTER TABLE IF EXISTS agent_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS agent_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS agent_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS monitoring_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS data_source_monitor ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS parcel_update_history ENABLE ROW LEVEL SECURITY;

-- 3.2 ETL and processing tables
ALTER TABLE IF EXISTS florida_entities_staging ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_change_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_data_loads ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_import_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_processed_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS jobs ENABLE ROW LEVEL SECURITY;

-- 3.3 Create service role policies
-- Only service role and admin can access system tables

CREATE POLICY IF NOT EXISTS "service_role_agent_logs" ON agent_activity_logs
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_agent_config" ON agent_config
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_monitoring" ON monitoring_agents
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_data_source_monitor" ON data_source_monitor
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_update_history" ON parcel_update_history
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_staging" ON florida_entities_staging
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_change_log" ON property_change_log
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_data_loads" ON property_data_loads
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_import_log" ON sunbiz_import_log
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_jobs" ON jobs
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

-- 3.4 Read-only admin access to system status
CREATE POLICY IF NOT EXISTS "admin_read_agent_logs" ON agent_activity_logs
    FOR SELECT USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY IF NOT EXISTS "admin_read_monitoring" ON monitoring_agents
    FOR SELECT USING (auth.jwt() ->> 'role' = 'admin');

COMMIT;

-- Verification checkpoint for Category 3
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM pg_tables t
    WHERE t.schemaname = 'public'
    AND t.tablename LIKE ANY(ARRAY['agent_%', 'monitoring_%', 'data_source_%', '%_log', '%_staging', 'jobs'])
    AND EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = t.schemaname
        AND c.relname = t.tablename
        AND c.relrowsecurity = true
    );

    RAISE NOTICE 'CATEGORY 3 COMPLETE: % system/agent tables now have RLS enabled', table_count;
END $$;

-- ============================================================================
-- CATEGORY 4: ANALYTICS & ML DATA (LOWER PRIORITY)
-- ============================================================================
-- Tables for business intelligence, ML models, and analytics
-- RISK: Unauthorized access to business insights
-- SOLUTION: Authenticated read access, service role write access

BEGIN;

-- 4.1 Enable RLS on analytics tables
ALTER TABLE IF EXISTS property_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS market_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS investment_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_comparables ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_scores ENABLE ROW LEVEL SECURITY;

-- 4.2 ML and matching tables
ALTER TABLE IF EXISTS property_entity_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS entity_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_property_matches ENABLE ROW LEVEL SECURITY;

-- 4.3 Create analytics access policies
-- Authenticated users can read, service role can write

CREATE POLICY IF NOT EXISTS "authenticated_read_analytics" ON property_analytics
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "authenticated_read_market_analysis" ON market_analysis
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "authenticated_read_investment_analysis" ON investment_analysis
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "authenticated_read_scores" ON property_scores
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_analytics_write" ON property_analytics
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_matches_write" ON property_entity_matches
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_relationships_write" ON entity_relationships
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

COMMIT;

-- ============================================================================
-- FINAL VERIFICATION & REPORTING
-- ============================================================================

DO $$
DECLARE
    total_tables INTEGER;
    rls_enabled_tables INTEGER;
    remaining_tables INTEGER;
    coverage_percentage NUMERIC;
BEGIN
    -- Count total public tables
    SELECT COUNT(*) INTO total_tables
    FROM pg_tables
    WHERE schemaname = 'public';

    -- Count tables with RLS enabled
    SELECT COUNT(*) INTO rls_enabled_tables
    FROM pg_tables t
    WHERE t.schemaname = 'public'
    AND EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = t.schemaname
        AND c.relname = t.tablename
        AND c.relrowsecurity = true
    );

    remaining_tables := total_tables - rls_enabled_tables;
    coverage_percentage := ROUND((rls_enabled_tables::NUMERIC / total_tables::NUMERIC) * 100, 2);

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'PHASE 2 RLS IMPLEMENTATION COMPLETE';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Total public tables: %', total_tables;
    RAISE NOTICE 'Tables with RLS enabled: %', rls_enabled_tables;
    RAISE NOTICE 'Tables without RLS: %', remaining_tables;
    RAISE NOTICE 'RLS coverage: %% %', coverage_percentage;
    RAISE NOTICE '============================================================';

    IF coverage_percentage >= 85 THEN
        RAISE NOTICE 'SUCCESS: Excellent RLS coverage achieved';
    ELSIF coverage_percentage >= 70 THEN
        RAISE NOTICE 'GOOD: Satisfactory RLS coverage achieved';
    ELSE
        RAISE WARNING 'WARNING: Low RLS coverage - review remaining tables';
    END IF;
END $$;

-- ============================================================================
-- POST-EXECUTION VERIFICATION QUERIES
-- ============================================================================

-- Run these queries after script completion to verify results:

-- 1. Tables still without RLS
/*
SELECT schemaname, tablename
FROM pg_tables t
WHERE t.schemaname = 'public'
AND NOT EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = t.schemaname
    AND c.relname = t.tablename
    AND c.relrowsecurity = true
)
ORDER BY tablename;
*/

-- 2. RLS policy summary
/*
SELECT tablename, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY policy_count DESC, tablename;
*/

-- 3. Test user isolation (run as different users)
/*
-- Test as authenticated user
SELECT COUNT(*) FROM user_watchlists;
SELECT COUNT(*) FROM property_notes;

-- Should only see own data, not other users' data
*/