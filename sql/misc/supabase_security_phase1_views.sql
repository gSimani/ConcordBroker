-- ================================================================
-- SUPABASE SECURITY REMEDIATION - PHASE 1: SECURITY DEFINER VIEWS
-- ================================================================
-- PRIORITY: IMMEDIATE - Execute first to remove privilege escalation
-- DESCRIPTION: Fix 17 views with SECURITY DEFINER to use SECURITY INVOKER
-- IMPACT: Critical - Views currently bypass user permissions
-- EXECUTION TIME: <1 minute
-- DOWNTIME: None
-- ================================================================

-- Start transaction for atomic execution
BEGIN;

-- =========================
-- FIX SECURITY DEFINER VIEWS
-- =========================
-- Change all views from SECURITY DEFINER to SECURITY INVOKER
-- This ensures views respect the permissions of the querying user, not the view creator

-- View 1: recent_filings
ALTER VIEW public.recent_filings SET (security_invoker = true);

-- View 2: high_value_properties
ALTER VIEW public.high_value_properties SET (security_invoker = true);

-- View 3: tax_deed_items_view
ALTER VIEW public.tax_deed_items_view SET (security_invoker = true);

-- View 4: monitoring_status
ALTER VIEW public.monitoring_status SET (security_invoker = true);

-- View 5: property_tax_certificate_summary
ALTER VIEW public.property_tax_certificate_summary SET (security_invoker = true);

-- View 6: latest_parcels
ALTER VIEW public.latest_parcels SET (security_invoker = true);

-- View 7: watchlist_alert_summary
ALTER VIEW public.watchlist_alert_summary SET (security_invoker = true);

-- View 8: recent_sales
ALTER VIEW public.recent_sales SET (security_invoker = true);

-- View 9: data_quality_dashboard
ALTER VIEW public.data_quality_dashboard SET (security_invoker = true);

-- View 10: florida_active_entities_with_contacts
ALTER VIEW public.florida_active_entities_with_contacts SET (security_invoker = true);

-- View 11: florida_contact_summary
ALTER VIEW public.florida_contact_summary SET (security_invoker = true);

-- View 12: high_confidence_matches
ALTER VIEW public.high_confidence_matches SET (security_invoker = true);

-- View 13: entity_property_network
ALTER VIEW public.entity_property_network SET (security_invoker = true);

-- View 14: all_entities
ALTER VIEW public.all_entities SET (security_invoker = true);

-- View 15: import_statistics
ALTER VIEW public.import_statistics SET (security_invoker = true);

-- View 16: active_tax_certificates
ALTER VIEW public.active_tax_certificates SET (security_invoker = true);

-- View 17: active_corporations
ALTER VIEW public.active_corporations SET (security_invoker = true);

-- Commit the transaction
COMMIT;

-- =========================
-- VALIDATION QUERIES
-- =========================
-- Run these to verify the changes worked correctly

-- Check that all views now have security_invoker = true
SELECT
    schemaname,
    viewname,
    definition
FROM pg_views
WHERE schemaname = 'public'
AND viewname IN (
    'recent_filings',
    'high_value_properties',
    'tax_deed_items_view',
    'monitoring_status',
    'property_tax_certificate_summary',
    'latest_parcels',
    'watchlist_alert_summary',
    'recent_sales',
    'data_quality_dashboard',
    'florida_active_entities_with_contacts',
    'florida_contact_summary',
    'high_confidence_matches',
    'entity_property_network',
    'all_entities',
    'import_statistics',
    'active_tax_certificates',
    'active_corporations'
)
ORDER BY viewname;

-- Alternative validation - check view options
SELECT
    relname as view_name,
    reloptions as options
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE relkind = 'v'
AND n.nspname = 'public'
AND relname IN (
    'recent_filings',
    'high_value_properties',
    'tax_deed_items_view',
    'monitoring_status',
    'property_tax_certificate_summary',
    'latest_parcels',
    'watchlist_alert_summary',
    'recent_sales',
    'data_quality_dashboard',
    'florida_active_entities_with_contacts',
    'florida_contact_summary',
    'high_confidence_matches',
    'entity_property_network',
    'all_entities',
    'import_statistics',
    'active_tax_certificates',
    'active_corporations'
)
ORDER BY relname;

-- =========================
-- SUCCESS CONFIRMATION
-- =========================
-- If both validation queries return results without errors:
-- ✅ Phase 1 Complete - Security Definer privilege escalation fixed
-- ✅ Views now respect querying user's permissions
-- ✅ Ready to proceed to Phase 2 (RLS enablement)

-- =========================
-- ROLLBACK PROCEDURE (IF NEEDED)
-- =========================
-- If you need to rollback this phase, uncomment and run:
/*
BEGIN;
ALTER VIEW public.recent_filings SET (security_definer = true);
ALTER VIEW public.high_value_properties SET (security_definer = true);
ALTER VIEW public.tax_deed_items_view SET (security_definer = true);
ALTER VIEW public.monitoring_status SET (security_definer = true);
ALTER VIEW public.property_tax_certificate_summary SET (security_definer = true);
ALTER VIEW public.latest_parcels SET (security_definer = true);
ALTER VIEW public.watchlist_alert_summary SET (security_definer = true);
ALTER VIEW public.recent_sales SET (security_definer = true);
ALTER VIEW public.data_quality_dashboard SET (security_definer = true);
ALTER VIEW public.florida_active_entities_with_contacts SET (security_definer = true);
ALTER VIEW public.florida_contact_summary SET (security_definer = true);
ALTER VIEW public.high_confidence_matches SET (security_definer = true);
ALTER VIEW public.entity_property_network SET (security_definer = true);
ALTER VIEW public.all_entities SET (security_definer = true);
ALTER VIEW public.import_statistics SET (security_definer = true);
ALTER VIEW public.active_tax_certificates SET (security_definer = true);
ALTER VIEW public.active_corporations SET (security_definer = true);
COMMIT;
*/