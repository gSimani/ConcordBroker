-- ================================================================
-- SUPABASE SECURITY REMEDIATION - EMERGENCY ROLLBACK PROCEDURES
-- ================================================================
-- USE ONLY IN CASE OF CRITICAL ISSUES
-- This file contains rollback procedures for each phase if problems occur
-- Execute sections as needed based on which phase caused issues
-- ================================================================

-- =========================
-- ROLLBACK PHASE 3: PERFORMANCE INDEXES
-- =========================
-- If Phase 3 caused performance issues, remove the indexes

-- WARNING: Only run this if indexes are causing problems
-- Most indexes improve performance, but in rare cases they may cause issues

/*
BEGIN;

-- User-specific table indexes
DROP INDEX IF EXISTS idx_user_preferences_user_id;
DROP INDEX IF EXISTS idx_watchlist_user_id;
DROP INDEX IF EXISTS idx_notification_history_user_id;
DROP INDEX IF EXISTS idx_user_watchlists_user_id;
DROP INDEX IF EXISTS idx_notification_queue_user_id;
DROP INDEX IF EXISTS idx_watchlist_items_watchlist_id;
DROP INDEX IF EXISTS idx_watchlist_alerts_watchlist_item_id;
DROP INDEX IF EXISTS idx_watchlist_items_user_lookup;
DROP INDEX IF EXISTS idx_user_watchlists_composite;

-- Document and entity relationship indexes
DROP INDEX IF EXISTS idx_document_property_links_property;
DROP INDEX IF EXISTS idx_document_property_links_document;
DROP INDEX IF EXISTS idx_property_entity_matches_property;
DROP INDEX IF EXISTS idx_property_entity_matches_entity;

-- Performance indexes for frequently queried columns
DROP INDEX IF EXISTS idx_property_sales_history_parcel_id;
DROP INDEX IF EXISTS idx_property_sales_history_sale_date;
DROP INDEX IF EXISTS idx_tax_certificates_parcel_id;
DROP INDEX IF EXISTS idx_tax_certificates_status;

-- Sunbiz entity performance indexes
DROP INDEX IF EXISTS idx_sunbiz_officers_entity_id;
DROP INDEX IF EXISTS idx_sunbiz_officers_name;
DROP INDEX IF EXISTS idx_sunbiz_corporate_events_entity_id;

-- ML and analytics indexes
DROP INDEX IF EXISTS idx_ml_property_scores_parcel_id;
DROP INDEX IF EXISTS idx_ml_property_scores_score;
DROP INDEX IF EXISTS idx_ml_property_scores_xgb_parcel_id;

-- Agent and monitoring indexes
DROP INDEX IF EXISTS idx_agent_activity_logs_agent_id;
DROP INDEX IF EXISTS idx_agent_activity_logs_timestamp;
DROP INDEX IF EXISTS idx_fl_agent_status_agent_id;
DROP INDEX IF EXISTS idx_fl_agent_status_status;

-- Job processing indexes
DROP INDEX IF EXISTS idx_sdf_jobs_status;
DROP INDEX IF EXISTS idx_sdf_jobs_created_at;
DROP INDEX IF EXISTS idx_nav_jobs_status;
DROP INDEX IF EXISTS idx_nav_jobs_created_at;
DROP INDEX IF EXISTS idx_tpp_jobs_status;
DROP INDEX IF EXISTS idx_sunbiz_download_jobs_status;

COMMIT;
*/

-- =========================
-- ROLLBACK PHASE 2: RLS AND POLICIES (CRITICAL)
-- =========================
-- If Phase 2 broke application access, disable RLS and remove policies
-- WARNING: This will remove all security protections!

/*
BEGIN;

-- =========================
-- DISABLE RLS ON ALL TABLES
-- =========================

-- User-specific tables
ALTER TABLE public.user_preferences DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_watchlists DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist_alerts DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_queue DISABLE ROW LEVEL SECURITY;

-- System/Agent tables
ALTER TABLE public.agent_activity_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_config DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.edge_functions DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_agent_status DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_data_updates DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sdf_jobs DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.tpp_jobs DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.nav_jobs DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_download_jobs DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_processing_queue DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_import_log DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_processed_files DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_sftp_downloads DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_audit_log DISABLE ROW LEVEL SECURITY;

-- Business data tables
ALTER TABLE public.property_sales_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_ownership_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.tax_certificates DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.tax_deed_auctions DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.tax_deed_bidding_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_entity_matches DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.entity_relationships DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.entity_search_cache DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_categories DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_property_links DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_access_log DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_alerts DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_search_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_nav_assessment_detail DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_nav_parcel_summary DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_sdf_sales DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_tpp_accounts DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.nav_parcel_assessments DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.nav_assessment_details DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_officers DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_fictitious_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_lien_debtors DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_lien_secured_parties DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_officer_corporation_matches DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_corporate_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_partnership_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_principal_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_monitoring_agents DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.ml_property_scores DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.ml_model_metrics DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.ml_property_scores_xgb DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.ab_validation_results DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.florida_entities_staging DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_change_log DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.spatial_ref_sys DISABLE ROW LEVEL SECURITY;

-- =========================
-- DROP ALL POLICIES
-- =========================

-- Get all policies and drop them (run this query first to see all policies)
-- SELECT 'DROP POLICY "' || policyname || '" ON ' || schemaname || '.' || tablename || ';'
-- FROM pg_policies WHERE schemaname = 'public';

-- User-specific table policies
DROP POLICY IF EXISTS "user_preferences_user_read" ON public.user_preferences;
DROP POLICY IF EXISTS "user_preferences_user_write" ON public.user_preferences;
DROP POLICY IF EXISTS "user_preferences_user_update" ON public.user_preferences;
DROP POLICY IF EXISTS "user_preferences_user_delete" ON public.user_preferences;
DROP POLICY IF EXISTS "user_preferences_service_all" ON public.user_preferences;

DROP POLICY IF EXISTS "watchlist_user_read" ON public.watchlist;
DROP POLICY IF EXISTS "watchlist_user_write" ON public.watchlist;
DROP POLICY IF EXISTS "watchlist_user_update" ON public.watchlist;
DROP POLICY IF EXISTS "watchlist_user_delete" ON public.watchlist;
DROP POLICY IF EXISTS "watchlist_service_all" ON public.watchlist;

DROP POLICY IF EXISTS "notification_history_user_read" ON public.notification_history;
DROP POLICY IF EXISTS "notification_history_user_write" ON public.notification_history;
DROP POLICY IF EXISTS "notification_history_user_update" ON public.notification_history;
DROP POLICY IF EXISTS "notification_history_user_delete" ON public.notification_history;
DROP POLICY IF EXISTS "notification_history_service_all" ON public.notification_history;

DROP POLICY IF EXISTS "user_watchlists_user_read" ON public.user_watchlists;
DROP POLICY IF EXISTS "user_watchlists_user_write" ON public.user_watchlists;
DROP POLICY IF EXISTS "user_watchlists_user_update" ON public.user_watchlists;
DROP POLICY IF EXISTS "user_watchlists_user_delete" ON public.user_watchlists;
DROP POLICY IF EXISTS "user_watchlists_service_all" ON public.user_watchlists;

DROP POLICY IF EXISTS "watchlist_items_user_read" ON public.watchlist_items;
DROP POLICY IF EXISTS "watchlist_items_user_write" ON public.watchlist_items;
DROP POLICY IF EXISTS "watchlist_items_user_update" ON public.watchlist_items;
DROP POLICY IF EXISTS "watchlist_items_user_delete" ON public.watchlist_items;
DROP POLICY IF EXISTS "watchlist_items_service_all" ON public.watchlist_items;

DROP POLICY IF EXISTS "watchlist_alerts_user_read" ON public.watchlist_alerts;
DROP POLICY IF EXISTS "watchlist_alerts_user_write" ON public.watchlist_alerts;
DROP POLICY IF EXISTS "watchlist_alerts_user_update" ON public.watchlist_alerts;
DROP POLICY IF EXISTS "watchlist_alerts_user_delete" ON public.watchlist_alerts;
DROP POLICY IF EXISTS "watchlist_alerts_service_all" ON public.watchlist_alerts;

DROP POLICY IF EXISTS "notification_queue_user_read" ON public.notification_queue;
DROP POLICY IF EXISTS "notification_queue_user_write" ON public.notification_queue;
DROP POLICY IF EXISTS "notification_queue_user_update" ON public.notification_queue;
DROP POLICY IF EXISTS "notification_queue_user_delete" ON public.notification_queue;
DROP POLICY IF EXISTS "notification_queue_service_all" ON public.notification_queue;

-- System table policies
DROP POLICY IF EXISTS "agent_activity_logs_service_only" ON public.agent_activity_logs;
DROP POLICY IF EXISTS "agent_config_service_only" ON public.agent_config;
DROP POLICY IF EXISTS "agent_notifications_service_only" ON public.agent_notifications;
DROP POLICY IF EXISTS "edge_functions_service_only" ON public.edge_functions;
DROP POLICY IF EXISTS "fl_agent_status_service_only" ON public.fl_agent_status;
DROP POLICY IF EXISTS "fl_data_updates_service_only" ON public.fl_data_updates;
DROP POLICY IF EXISTS "sdf_jobs_service_only" ON public.sdf_jobs;
DROP POLICY IF EXISTS "tpp_jobs_service_only" ON public.tpp_jobs;
DROP POLICY IF EXISTS "nav_jobs_service_only" ON public.nav_jobs;
DROP POLICY IF EXISTS "sunbiz_download_jobs_service_only" ON public.sunbiz_download_jobs;
DROP POLICY IF EXISTS "document_processing_queue_service_only" ON public.document_processing_queue;
DROP POLICY IF EXISTS "sunbiz_import_log_service_only" ON public.sunbiz_import_log;
DROP POLICY IF EXISTS "sunbiz_processed_files_service_only" ON public.sunbiz_processed_files;
DROP POLICY IF EXISTS "sunbiz_sftp_downloads_service_only" ON public.sunbiz_sftp_downloads;
DROP POLICY IF EXISTS "match_audit_log_service_only" ON public.match_audit_log;

-- Business data policies (this is a sample - there are many more)
DROP POLICY IF EXISTS "property_sales_history_read" ON public.property_sales_history;
DROP POLICY IF EXISTS "property_sales_history_service" ON public.property_sales_history;
DROP POLICY IF EXISTS "tax_certificates_read" ON public.tax_certificates;
DROP POLICY IF EXISTS "tax_certificates_service" ON public.tax_certificates;
DROP POLICY IF EXISTS "documents_read" ON public.documents;
DROP POLICY IF EXISTS "documents_service" ON public.documents;

-- NOTE: Add more DROP POLICY statements as needed for all tables

COMMIT;
*/

-- =========================
-- ROLLBACK PHASE 1: SECURITY DEFINER VIEWS (LEAST RISKY)
-- =========================
-- If Phase 1 broke view access, restore SECURITY DEFINER

/*
BEGIN;

-- Restore SECURITY DEFINER on all views
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

-- =========================
-- COMPLETE EMERGENCY ROLLBACK
-- =========================
-- If everything is broken, run this to restore to original state
-- WARNING: This removes ALL security improvements!

/*
-- EMERGENCY ROLLBACK - REMOVES ALL SECURITY!
BEGIN;

-- 1. Restore SECURITY DEFINER on views
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

-- 2. Drop all policies (get complete list first)
DO $$
DECLARE
    pol RECORD;
BEGIN
    FOR pol IN
        SELECT schemaname, tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I',
                      pol.policyname, pol.schemaname, pol.tablename);
    END LOOP;
END $$;

-- 3. Disable RLS on all tables
DO $$
DECLARE
    tbl RECORD;
BEGIN
    FOR tbl IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public' AND rowsecurity = true
    LOOP
        EXECUTE format('ALTER TABLE public.%I DISABLE ROW LEVEL SECURITY', tbl.tablename);
    END LOOP;
END $$;

-- 4. Drop all security-related indexes
DO $$
DECLARE
    idx RECORD;
BEGIN
    FOR idx IN
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
    LOOP
        EXECUTE format('DROP INDEX IF EXISTS %I', idx.indexname);
    END LOOP;
END $$;

COMMIT;

-- Verify rollback completed
SELECT 'EMERGENCY ROLLBACK COMPLETE' as status,
       'ALL SECURITY MEASURES REMOVED' as warning,
       'DATABASE RESTORED TO ORIGINAL STATE' as result;
*/

-- =========================
-- ROLLBACK VERIFICATION
-- =========================
-- After any rollback, run these queries to verify the state

-- Check view security status
SELECT
    schemaname,
    viewname,
    CASE
        WHEN definition ILIKE '%security_definer%' THEN 'SECURITY DEFINER (ORIGINAL)'
        WHEN definition ILIKE '%security_invoker%' THEN 'SECURITY INVOKER (SECURE)'
        ELSE 'UNKNOWN'
    END as security_mode
FROM pg_views
WHERE schemaname = 'public'
AND viewname IN (
    'recent_filings', 'high_value_properties', 'tax_deed_items_view'
)
ORDER BY viewname;

-- Check RLS status
SELECT
    tablename,
    CASE
        WHEN rowsecurity = true THEN 'RLS ENABLED'
        ELSE 'RLS DISABLED (ORIGINAL)'
    END as rls_status
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('user_preferences', 'watchlist', 'agent_activity_logs')
ORDER BY tablename;

-- Check policy count
SELECT
    'Total Policies' as metric,
    COUNT(*) as count,
    CASE
        WHEN COUNT(*) = 0 THEN 'NO POLICIES (ORIGINAL STATE)'
        ELSE 'POLICIES EXIST'
    END as status
FROM pg_policies
WHERE schemaname = 'public';

-- Check index count
SELECT
    'Security Indexes' as metric,
    COUNT(*) as count,
    CASE
        WHEN COUNT(*) = 0 THEN 'NO SECURITY INDEXES'
        ELSE 'SECURITY INDEXES EXIST'
    END as status
FROM pg_indexes
WHERE schemaname = 'public'
AND indexname LIKE 'idx_%';

-- =========================
-- POST-ROLLBACK ACTIONS
-- =========================
-- After any rollback:
-- 1. Test application functionality
-- 2. Review logs for errors
-- 3. Determine root cause of issues
-- 4. Plan corrective measures
-- 5. Consider partial re-implementation with fixes