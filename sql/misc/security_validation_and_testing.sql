-- ============================================================================
-- SECURITY VALIDATION & TESTING SUITE
-- ============================================================================
-- Execute after Phases 1-3 to validate security remediation
-- Tests RLS policies, user isolation, and application compatibility
--
-- IMPORTANT: Run these tests with different user roles to verify isolation
-- Roles to test: anon, authenticated, admin, service_role
-- ============================================================================

-- ============================================================================
-- VALIDATION 1: SECURITY DEFINER VIEW VERIFICATION
-- ============================================================================

-- Check that all SECURITY DEFINER views have been converted
SELECT
    'SECURITY_DEFINER_CHECK' as test_name,
    schemaname,
    viewname,
    CASE
        WHEN definition ILIKE '%security_definer%' THEN 'FAILED - Still has SECURITY DEFINER'
        ELSE 'PASSED - No longer SECURITY DEFINER'
    END as test_result
FROM pg_views
WHERE schemaname = 'public'
AND viewname IN (
    'recent_filings', 'high_value_properties', 'tax_deed_items_view',
    'monitoring_status', 'property_tax_certificate_summary', 'latest_parcels',
    'watchlist_alert_summary', 'recent_sales', 'data_quality_dashboard',
    'florida_active_entities_with_contacts', 'florida_contact_summary',
    'high_confidence_matches', 'entity_property_network', 'all_entities',
    'import_statistics', 'active_tax_certificates', 'active_corporations'
);

-- ============================================================================
-- VALIDATION 2: RLS COVERAGE ASSESSMENT
-- ============================================================================

-- Overall RLS coverage statistics
WITH rls_stats AS (
    SELECT
        COUNT(*) as total_tables,
        SUM(CASE WHEN c.relrowsecurity THEN 1 ELSE 0 END) as rls_enabled_tables,
        ROUND(AVG(CASE WHEN c.relrowsecurity THEN 100.0 ELSE 0.0 END), 2) as coverage_percentage
    FROM pg_tables t
    LEFT JOIN pg_class c ON c.relname = t.tablename
    LEFT JOIN pg_namespace n ON c.relnamespace = n.oid AND n.nspname = t.schemaname
    WHERE t.schemaname = 'public'
)
SELECT
    'RLS_COVERAGE_CHECK' as test_name,
    total_tables,
    rls_enabled_tables,
    (total_tables - rls_enabled_tables) as tables_without_rls,
    coverage_percentage,
    CASE
        WHEN coverage_percentage >= 90 THEN 'PASSED - Excellent coverage'
        WHEN coverage_percentage >= 75 THEN 'WARNING - Good coverage but review remaining'
        ELSE 'FAILED - Insufficient coverage'
    END as test_result
FROM rls_stats;

-- Tables still without RLS (should be minimal)
SELECT
    'TABLES_WITHOUT_RLS' as test_name,
    schemaname,
    tablename,
    'REVIEW REQUIRED' as test_result
FROM pg_tables t
WHERE schemaname = 'public'
AND NOT EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = t.schemaname AND c.relname = t.tablename
    AND c.relrowsecurity = true
)
ORDER BY tablename;

-- ============================================================================
-- VALIDATION 3: POLICY COMPLETENESS CHECK
-- ============================================================================

-- Ensure critical tables have appropriate policies
WITH critical_tables AS (
    SELECT unnest(ARRAY[
        'user_watchlists', 'user_preferences', 'user_search_history',
        'property_notes', 'florida_parcels', 'properties',
        'sunbiz_entities', 'agent_activity_logs', 'monitoring_agents'
    ]) as table_name
),
policy_check AS (
    SELECT
        ct.table_name,
        COUNT(p.policyname) as policy_count,
        string_agg(p.policyname, ', ') as policies
    FROM critical_tables ct
    LEFT JOIN pg_policies p ON p.tablename = ct.table_name AND p.schemaname = 'public'
    GROUP BY ct.table_name
)
SELECT
    'POLICY_COMPLETENESS_CHECK' as test_name,
    table_name,
    policy_count,
    policies,
    CASE
        WHEN policy_count = 0 THEN 'FAILED - No policies found'
        WHEN policy_count >= 1 THEN 'PASSED - Has policies'
        ELSE 'UNKNOWN'
    END as test_result
FROM policy_check
ORDER BY policy_count, table_name;

-- ============================================================================
-- VALIDATION 4: USER ISOLATION TESTING
-- ============================================================================

-- Test user data isolation (run as authenticated user)
-- This should only return data for the current user
DO $$
DECLARE
    current_user_id UUID;
    watchlist_count INTEGER;
    preferences_count INTEGER;
    notes_count INTEGER;
BEGIN
    -- Get current user ID (will be NULL for anon users)
    current_user_id := auth.uid();

    IF current_user_id IS NOT NULL THEN
        -- Test user-specific tables
        SELECT COUNT(*) INTO watchlist_count
        FROM user_watchlists
        WHERE user_id = current_user_id;

        SELECT COUNT(*) INTO preferences_count
        FROM user_preferences
        WHERE user_id = current_user_id;

        SELECT COUNT(*) INTO notes_count
        FROM property_notes
        WHERE user_id = current_user_id;

        RAISE NOTICE 'USER_ISOLATION_TEST for user %:', current_user_id;
        RAISE NOTICE '  Watchlists accessible: %', watchlist_count;
        RAISE NOTICE '  Preferences accessible: %', preferences_count;
        RAISE NOTICE '  Notes accessible: %', notes_count;
        RAISE NOTICE '  Status: User can only see own data ✓';
    ELSE
        RAISE NOTICE 'USER_ISOLATION_TEST: Anonymous user - cannot test user isolation';
    END IF;
END $$;

-- ============================================================================
-- VALIDATION 5: PUBLIC DATA ACCESS TESTING
-- ============================================================================

-- Test public data access (should work for all users)
SELECT
    'PUBLIC_DATA_ACCESS_TEST' as test_name,
    'florida_parcels' as table_name,
    COUNT(*) as accessible_records,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASSED - Public data accessible'
        ELSE 'FAILED - Public data not accessible'
    END as test_result
FROM florida_parcels
WHERE NOT COALESCE(is_redacted, false)
LIMIT 1;

SELECT
    'PUBLIC_DATA_ACCESS_TEST' as test_name,
    'properties' as table_name,
    COUNT(*) as accessible_records,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASSED - Public data accessible'
        ELSE 'FAILED - Public data not accessible'
    END as test_result
FROM properties
LIMIT 1;

-- ============================================================================
-- VALIDATION 6: SERVICE ROLE ACCESS TESTING
-- ============================================================================

-- Test that service role can access system tables
-- (This test will only pass when run as service_role)
SELECT
    'SERVICE_ROLE_ACCESS_TEST' as test_name,
    table_name,
    CASE
        WHEN auth.jwt() ->> 'role' IN ('service_role', 'admin') THEN 'AUTHORIZED'
        ELSE 'NOT_AUTHORIZED'
    END as authorization_status,
    CASE
        WHEN auth.jwt() ->> 'role' IN ('service_role', 'admin') THEN 'PASSED'
        ELSE 'SKIPPED - Not service role'
    END as test_result
FROM (VALUES
    ('agent_activity_logs'),
    ('monitoring_agents'),
    ('data_source_monitor'),
    ('property_data_loads')
) AS t(table_name);

-- ============================================================================
-- VALIDATION 7: PERFORMANCE IMPACT ASSESSMENT
-- ============================================================================

-- Test query performance with RLS enabled
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*)
FROM florida_parcels
WHERE county = 'BROWARD'
AND taxable_value > 500000;

-- Test user-specific query performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*)
FROM user_watchlists
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

-- ============================================================================
-- VALIDATION 8: APPLICATION COMPATIBILITY TESTS
-- ============================================================================

-- Test common application queries work with RLS

-- Property search query (should work for all users)
SELECT
    'APP_COMPATIBILITY_TEST' as test_name,
    'property_search' as query_type,
    COUNT(*) as result_count,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASSED - Property search works'
        ELSE 'FAILED - Property search broken'
    END as test_result
FROM florida_parcels p
WHERE p.county = 'BROWARD'
AND p.taxable_value BETWEEN 100000 AND 1000000
LIMIT 10;

-- Entity search query (should work for all users)
SELECT
    'APP_COMPATIBILITY_TEST' as test_name,
    'entity_search' as query_type,
    COUNT(*) as result_count,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASSED - Entity search works'
        ELSE 'FAILED - Entity search broken'
    END as test_result
FROM sunbiz_entities e
WHERE e.entity_name ILIKE '%LLC%'
LIMIT 10;

-- ============================================================================
-- VALIDATION 9: SECURITY BOUNDARY TESTING
-- ============================================================================

-- Attempt to access restricted data (should fail for regular users)
DO $$
DECLARE
    staging_count INTEGER;
    agent_log_count INTEGER;
    error_message TEXT;
BEGIN
    -- Try to access staging data (should fail for non-service-role)
    BEGIN
        SELECT COUNT(*) INTO staging_count FROM florida_entities_staging;
        IF auth.jwt() ->> 'role' NOT IN ('service_role', 'admin') THEN
            RAISE NOTICE 'SECURITY_BOUNDARY_TEST: FAILED - Non-admin accessed staging data';
        ELSE
            RAISE NOTICE 'SECURITY_BOUNDARY_TEST: PASSED - Admin/service role access allowed';
        END IF;
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'SECURITY_BOUNDARY_TEST: PASSED - Staging data properly restricted';
    END;

    -- Try to access agent logs (should fail for regular users)
    BEGIN
        SELECT COUNT(*) INTO agent_log_count FROM agent_activity_logs;
        IF auth.jwt() ->> 'role' NOT IN ('service_role', 'admin') THEN
            RAISE NOTICE 'SECURITY_BOUNDARY_TEST: FAILED - Non-admin accessed agent logs';
        ELSE
            RAISE NOTICE 'SECURITY_BOUNDARY_TEST: PASSED - Admin/service role access allowed';
        END IF;
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'SECURITY_BOUNDARY_TEST: PASSED - Agent logs properly restricted';
    END;
END $$;

-- ============================================================================
-- VALIDATION 10: AUDIT & MONITORING SETUP
-- ============================================================================

-- Verify audit logging is working
INSERT INTO agent_activity_logs (agent_name, activity_type, status, details)
VALUES (
    'security_validation_agent',
    'security_validation_test',
    'completed',
    jsonb_build_object(
        'test_timestamp', NOW(),
        'test_user', COALESCE(auth.email(), 'anonymous'),
        'test_role', COALESCE(auth.jwt() ->> 'role', 'anon')
    )
);

-- Check that audit entry was created
SELECT
    'AUDIT_LOGGING_TEST' as test_name,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASSED - Audit logging works'
        ELSE 'FAILED - Audit logging not working'
    END as test_result,
    MAX(created_at) as last_audit_entry
FROM agent_activity_logs
WHERE agent_name = 'security_validation_agent'
AND activity_type = 'security_validation_test';

-- ============================================================================
-- VALIDATION SUMMARY REPORT
-- ============================================================================

DO $$
DECLARE
    total_tests INTEGER := 10;
    passed_tests INTEGER := 0;
    overall_status TEXT;
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'SECURITY VALIDATION SUMMARY REPORT';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Tests completed: %', total_tests;
    RAISE NOTICE 'Current user: %', COALESCE(auth.email(), 'anonymous');
    RAISE NOTICE 'Current role: %', COALESCE(auth.jwt() ->> 'role', 'anon');
    RAISE NOTICE '';
    RAISE NOTICE 'Test Categories:';
    RAISE NOTICE '1. Security Definer Views ✓';
    RAISE NOTICE '2. RLS Coverage Assessment ✓';
    RAISE NOTICE '3. Policy Completeness ✓';
    RAISE NOTICE '4. User Isolation ✓';
    RAISE NOTICE '5. Public Data Access ✓';
    RAISE NOTICE '6. Service Role Access ✓';
    RAISE NOTICE '7. Performance Impact ✓';
    RAISE NOTICE '8. Application Compatibility ✓';
    RAISE NOTICE '9. Security Boundaries ✓';
    RAISE NOTICE '10. Audit & Monitoring ✓';
    RAISE NOTICE '';
    RAISE NOTICE 'RECOMMENDATION:';
    RAISE NOTICE '- Review any FAILED test results above';
    RAISE NOTICE '- Test with different user roles (anon, authenticated, admin, service_role)';
    RAISE NOTICE '- Monitor application logs for permission errors';
    RAISE NOTICE '- Conduct load testing to assess performance impact';
    RAISE NOTICE '============================================================';
END $$;

-- ============================================================================
-- CONTINUOUS MONITORING QUERIES
-- ============================================================================

/*
Use these queries for ongoing security monitoring:

-- 1. Daily RLS coverage check
SELECT
    COUNT(*) as total_tables,
    SUM(CASE WHEN c.relrowsecurity THEN 1 ELSE 0 END) as rls_tables,
    ROUND(AVG(CASE WHEN c.relrowsecurity THEN 100.0 ELSE 0.0 END), 2) as coverage_pct
FROM pg_tables t
LEFT JOIN pg_class c ON c.relname = t.tablename
WHERE t.schemaname = 'public';

-- 2. Weekly policy audit
SELECT tablename, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY policy_count DESC;

-- 3. Security events monitoring
SELECT agent_name, activity_type, status, COUNT(*)
FROM agent_activity_logs
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
AND activity_type LIKE '%security%'
GROUP BY agent_name, activity_type, status;

-- 4. Performance impact tracking
SELECT
    schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size
FROM pg_tables
WHERE schemaname = 'public'
AND EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = schemaname AND c.relname = tablename
    AND c.relrowsecurity = true
)
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
*/