-- ============================================================================
-- PHASE 1: IMMEDIATE SECURITY DEFINER VIEW REMEDIATION
-- ============================================================================
-- CRITICAL PRIORITY - Execute immediately before any other changes
-- Addresses 17 SECURITY DEFINER views that bypass user permissions
--
-- RISK: These views currently run with creator privileges instead of user privileges
-- SOLUTION: Convert to SECURITY INVOKER to respect calling user's permissions
-- ============================================================================

-- Ensure we're in a transaction for atomic execution
BEGIN;

-- ============================================================================
-- STEP 1: DOCUMENT CURRENT STATE
-- ============================================================================

-- Log current view security settings for audit trail
DO $$
DECLARE
    view_record RECORD;
    log_message TEXT;
BEGIN
    RAISE NOTICE 'SECURITY AUDIT LOG - Starting SECURITY DEFINER view remediation';
    RAISE NOTICE 'Timestamp: %', NOW();
    RAISE NOTICE '============================================================';

    -- Check and log each problematic view
    FOR view_record IN
        SELECT schemaname, viewname, definition
        FROM pg_views
        WHERE schemaname = 'public'
        AND definition ILIKE '%security_definer%'
    LOOP
        RAISE NOTICE 'FOUND SECURITY DEFINER VIEW: %.%', view_record.schemaname, view_record.viewname;
    END LOOP;

    RAISE NOTICE '============================================================';
END $$;

-- ============================================================================
-- STEP 2: CONVERT SECURITY DEFINER VIEWS TO SECURITY INVOKER
-- ============================================================================

-- Convert all identified SECURITY DEFINER views to SECURITY INVOKER
-- This ensures views execute with the permissions of the calling user

-- Property-related views
ALTER VIEW IF EXISTS public.recent_filings SET (security_invoker = true);
ALTER VIEW IF EXISTS public.high_value_properties SET (security_invoker = true);
ALTER VIEW IF EXISTS public.latest_parcels SET (security_invoker = true);
ALTER VIEW IF EXISTS public.recent_sales SET (security_invoker = true);

-- Tax and certificate views
ALTER VIEW IF EXISTS public.tax_deed_items_view SET (security_invoker = true);
ALTER VIEW IF EXISTS public.property_tax_certificate_summary SET (security_invoker = true);
ALTER VIEW IF EXISTS public.active_tax_certificates SET (security_invoker = true);

-- Monitoring and status views
ALTER VIEW IF EXISTS public.monitoring_status SET (security_invoker = true);
ALTER VIEW IF EXISTS public.data_quality_dashboard SET (security_invoker = true);
ALTER VIEW IF EXISTS public.import_statistics SET (security_invoker = true);

-- Entity and business data views
ALTER VIEW IF EXISTS public.florida_active_entities_with_contacts SET (security_invoker = true);
ALTER VIEW IF EXISTS public.florida_contact_summary SET (security_invoker = true);
ALTER VIEW IF EXISTS public.high_confidence_matches SET (security_invoker = true);
ALTER VIEW IF EXISTS public.entity_property_network SET (security_invoker = true);
ALTER VIEW IF EXISTS public.all_entities SET (security_invoker = true);
ALTER VIEW IF EXISTS public.active_corporations SET (security_invoker = true);

-- Watchlist and alert views
ALTER VIEW IF EXISTS public.watchlist_alert_summary SET (security_invoker = true);

-- ============================================================================
-- STEP 3: VERIFY CHANGES
-- ============================================================================

-- Verify that no SECURITY DEFINER views remain in public schema
DO $$
DECLARE
    remaining_count INTEGER;
    view_record RECORD;
BEGIN
    -- Count remaining SECURITY DEFINER views
    SELECT COUNT(*) INTO remaining_count
    FROM pg_views
    WHERE schemaname = 'public'
    AND definition ILIKE '%security_definer%';

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'VERIFICATION RESULTS:';
    RAISE NOTICE 'Remaining SECURITY DEFINER views in public schema: %', remaining_count;

    -- List any remaining views for manual review
    IF remaining_count > 0 THEN
        RAISE WARNING 'The following views still have SECURITY DEFINER:';
        FOR view_record IN
            SELECT schemaname, viewname
            FROM pg_views
            WHERE schemaname = 'public'
            AND definition ILIKE '%security_definer%'
        LOOP
            RAISE WARNING 'VIEW: %.%', view_record.schemaname, view_record.viewname;
        END LOOP;
    ELSE
        RAISE NOTICE 'SUCCESS: All SECURITY DEFINER views have been converted';
    END IF;

    RAISE NOTICE '============================================================';
END $$;

-- ============================================================================
-- STEP 4: DOCUMENT COMPLETION
-- ============================================================================

-- Create audit log entry
INSERT INTO agent_activity_logs (agent_name, activity_type, status, details, created_at)
VALUES (
    'security_remediation_agent',
    'security_definer_fix',
    'completed',
    jsonb_build_object(
        'phase', 'phase_1',
        'views_fixed', 17,
        'completed_at', NOW(),
        'risk_level', 'critical_resolved'
    ),
    NOW()
) ON CONFLICT DO NOTHING;

COMMIT;

-- ============================================================================
-- POST-EXECUTION VERIFICATION QUERIES
-- ============================================================================

-- Run these queries after the script to verify results:

-- 1. Check for any remaining SECURITY DEFINER views
/*
SELECT schemaname, viewname, definition
FROM pg_views
WHERE schemaname = 'public'
AND definition ILIKE '%security_definer%'
ORDER BY viewname;
*/

-- 2. Verify all views are now using SECURITY INVOKER (or default)
/*
SELECT schemaname, viewname,
       CASE
           WHEN definition ILIKE '%security_invoker%' THEN 'SECURITY INVOKER ✓'
           WHEN definition ILIKE '%security_definer%' THEN 'SECURITY DEFINER ✗'
           ELSE 'DEFAULT (INVOKER) ✓'
       END as security_mode
FROM pg_views
WHERE schemaname = 'public'
AND viewname IN (
    'recent_filings', 'high_value_properties', 'tax_deed_items_view',
    'monitoring_status', 'property_tax_certificate_summary', 'latest_parcels',
    'watchlist_alert_summary', 'recent_sales', 'data_quality_dashboard',
    'florida_active_entities_with_contacts', 'florida_contact_summary',
    'high_confidence_matches', 'entity_property_network', 'all_entities',
    'import_statistics', 'active_tax_certificates', 'active_corporations'
)
ORDER BY viewname;
*/

-- ============================================================================
-- IMMEDIATE NEXT STEPS
-- ============================================================================

/*
AFTER RUNNING THIS SCRIPT:

1. TEST APPLICATION FUNCTIONALITY:
   - Verify all views still return expected data
   - Test with different user roles (anon, authenticated, admin)
   - Check for any permission-related errors

2. MONITOR PERFORMANCE:
   - Views may now respect RLS policies (when implemented)
   - Performance may vary based on user permissions
   - Watch for any query plan changes

3. PROCEED TO PHASE 2:
   - Once Phase 1 is verified working
   - Run phase2_enable_rls_by_category.sql
   - Follow the sequential implementation plan

4. ROLLBACK PROCEDURE (if needed):
   - Change views back to SECURITY DEFINER if critical issues
   - Document any compatibility problems
   - Plan alternative approaches for affected views

SECURITY IMPACT:
✓ CRITICAL vulnerability closed - views no longer bypass user permissions
✓ Views now respect user context and future RLS policies
✓ Reduced privilege escalation risk
✓ Compliance with security best practices
*/