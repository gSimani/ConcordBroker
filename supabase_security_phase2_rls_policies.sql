-- ================================================================
-- SUPABASE SECURITY REMEDIATION - PHASE 2: RLS AND POLICIES
-- ================================================================
-- PRIORITY: HIGH - Execute after Phase 1 completion
-- DESCRIPTION: Enable Row Level Security and create policies for all public tables
-- IMPACT: High - Implements proper data isolation and access control
-- EXECUTION TIME: 2-5 minutes
-- DOWNTIME: Minimal (may cause brief connection resets)
-- ================================================================

-- Start transaction for atomic execution
BEGIN;

-- =========================
-- PART A: USER-SPECIFIC DATA
-- =========================
-- Tables that should isolate data by user_id
-- Users can only access their own data, service_role has full access

-- Enable RLS on user-specific tables
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_queue ENABLE ROW LEVEL SECURITY;

-- Policies for user_preferences
CREATE POLICY "user_preferences_user_read" ON public.user_preferences
    FOR SELECT TO authenticated USING (auth.uid()::text = user_id);
CREATE POLICY "user_preferences_user_write" ON public.user_preferences
    FOR INSERT TO authenticated WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "user_preferences_user_update" ON public.user_preferences
    FOR UPDATE TO authenticated USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "user_preferences_user_delete" ON public.user_preferences
    FOR DELETE TO authenticated USING (auth.uid()::text = user_id);
CREATE POLICY "user_preferences_service_all" ON public.user_preferences
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Policies for watchlist
CREATE POLICY "watchlist_user_read" ON public.watchlist
    FOR SELECT TO authenticated USING (auth.uid()::text = user_id);
CREATE POLICY "watchlist_user_write" ON public.watchlist
    FOR INSERT TO authenticated WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "watchlist_user_update" ON public.watchlist
    FOR UPDATE TO authenticated USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "watchlist_user_delete" ON public.watchlist
    FOR DELETE TO authenticated USING (auth.uid()::text = user_id);
CREATE POLICY "watchlist_service_all" ON public.watchlist
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Policies for notification_history
CREATE POLICY "notification_history_user_read" ON public.notification_history
    FOR SELECT TO authenticated USING (auth.uid()::text = user_id);
CREATE POLICY "notification_history_user_write" ON public.notification_history
    FOR INSERT TO authenticated WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "notification_history_user_update" ON public.notification_history
    FOR UPDATE TO authenticated USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "notification_history_user_delete" ON public.notification_history
    FOR DELETE TO authenticated USING (auth.uid()::text = user_id);
CREATE POLICY "notification_history_service_all" ON public.notification_history
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Policies for user_watchlists
CREATE POLICY "user_watchlists_user_read" ON public.user_watchlists
    FOR SELECT TO authenticated USING (auth.uid()::text = user_id);
CREATE POLICY "user_watchlists_user_write" ON public.user_watchlists
    FOR INSERT TO authenticated WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "user_watchlists_user_update" ON public.user_watchlists
    FOR UPDATE TO authenticated USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "user_watchlists_user_delete" ON public.user_watchlists
    FOR DELETE TO authenticated USING (auth.uid()::text = user_id);
CREATE POLICY "user_watchlists_service_all" ON public.user_watchlists
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Policies for watchlist_items (linked to user through user_watchlists)
CREATE POLICY "watchlist_items_user_read" ON public.watchlist_items
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM public.user_watchlists uw WHERE uw.id = watchlist_id AND uw.user_id = auth.uid()::text)
    );
CREATE POLICY "watchlist_items_user_write" ON public.watchlist_items
    FOR INSERT TO authenticated WITH CHECK (
        EXISTS (SELECT 1 FROM public.user_watchlists uw WHERE uw.id = watchlist_id AND uw.user_id = auth.uid()::text)
    );
CREATE POLICY "watchlist_items_user_update" ON public.watchlist_items
    FOR UPDATE TO authenticated USING (
        EXISTS (SELECT 1 FROM public.user_watchlists uw WHERE uw.id = watchlist_id AND uw.user_id = auth.uid()::text)
    ) WITH CHECK (
        EXISTS (SELECT 1 FROM public.user_watchlists uw WHERE uw.id = watchlist_id AND uw.user_id = auth.uid()::text)
    );
CREATE POLICY "watchlist_items_user_delete" ON public.watchlist_items
    FOR DELETE TO authenticated USING (
        EXISTS (SELECT 1 FROM public.user_watchlists uw WHERE uw.id = watchlist_id AND uw.user_id = auth.uid()::text)
    );
CREATE POLICY "watchlist_items_service_all" ON public.watchlist_items
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Policies for watchlist_alerts (linked to user through watchlist_items -> user_watchlists)
CREATE POLICY "watchlist_alerts_user_read" ON public.watchlist_alerts
    FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.watchlist_items wi
            JOIN public.user_watchlists uw ON uw.id = wi.watchlist_id
            WHERE wi.id = watchlist_item_id AND uw.user_id = auth.uid()::text
        )
    );
CREATE POLICY "watchlist_alerts_user_write" ON public.watchlist_alerts
    FOR INSERT TO authenticated WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.watchlist_items wi
            JOIN public.user_watchlists uw ON uw.id = wi.watchlist_id
            WHERE wi.id = watchlist_item_id AND uw.user_id = auth.uid()::text
        )
    );
CREATE POLICY "watchlist_alerts_user_update" ON public.watchlist_alerts
    FOR UPDATE TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.watchlist_items wi
            JOIN public.user_watchlists uw ON uw.id = wi.watchlist_id
            WHERE wi.id = watchlist_item_id AND uw.user_id = auth.uid()::text
        )
    ) WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.watchlist_items wi
            JOIN public.user_watchlists uw ON uw.id = wi.watchlist_id
            WHERE wi.id = watchlist_item_id AND uw.user_id = auth.uid()::text
        )
    );
CREATE POLICY "watchlist_alerts_user_delete" ON public.watchlist_alerts
    FOR DELETE TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.watchlist_items wi
            JOIN public.user_watchlists uw ON uw.id = wi.watchlist_id
            WHERE wi.id = watchlist_item_id AND uw.user_id = auth.uid()::text
        )
    );
CREATE POLICY "watchlist_alerts_service_all" ON public.watchlist_alerts
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Policies for notification_queue
CREATE POLICY "notification_queue_user_read" ON public.notification_queue
    FOR SELECT TO authenticated USING (auth.uid()::text = user_id);
CREATE POLICY "notification_queue_user_write" ON public.notification_queue
    FOR INSERT TO authenticated WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "notification_queue_user_update" ON public.notification_queue
    FOR UPDATE TO authenticated USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "notification_queue_user_delete" ON public.notification_queue
    FOR DELETE TO authenticated USING (auth.uid()::text = user_id);
CREATE POLICY "notification_queue_service_all" ON public.notification_queue
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- =========================
-- PART B: SYSTEM/AGENT DATA
-- =========================
-- Tables that should only be accessible to service_role and admins

-- Enable RLS on system tables
ALTER TABLE public.agent_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.edge_functions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_agent_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_data_updates ENABLE ROW LEVEL SECURITY;

-- Job and processing tables
ALTER TABLE public.sdf_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tpp_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nav_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_download_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_processing_queue ENABLE ROW LEVEL SECURITY;

-- Import and monitoring tables
ALTER TABLE public.sunbiz_import_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_processed_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_sftp_downloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_audit_log ENABLE ROW LEVEL SECURITY;

-- Create service_role-only policies for all system tables
CREATE POLICY "agent_activity_logs_service_only" ON public.agent_activity_logs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "agent_config_service_only" ON public.agent_config FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "agent_notifications_service_only" ON public.agent_notifications FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "edge_functions_service_only" ON public.edge_functions FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "fl_agent_status_service_only" ON public.fl_agent_status FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "fl_data_updates_service_only" ON public.fl_data_updates FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "sdf_jobs_service_only" ON public.sdf_jobs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "tpp_jobs_service_only" ON public.tpp_jobs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "nav_jobs_service_only" ON public.nav_jobs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "sunbiz_download_jobs_service_only" ON public.sunbiz_download_jobs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "document_processing_queue_service_only" ON public.document_processing_queue FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "sunbiz_import_log_service_only" ON public.sunbiz_import_log FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "sunbiz_processed_files_service_only" ON public.sunbiz_processed_files FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "sunbiz_sftp_downloads_service_only" ON public.sunbiz_sftp_downloads FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "match_audit_log_service_only" ON public.match_audit_log FOR ALL TO service_role USING (true) WITH CHECK (true);

-- =========================
-- PART C: BUSINESS DATA - AUTHENTICATED READ
-- =========================
-- Tables that authenticated users can read but only service_role can modify

-- Enable RLS on business data tables
ALTER TABLE public.property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_ownership_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tax_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tax_deed_auctions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tax_deed_bidding_items ENABLE ROW LEVEL SECURITY;

-- Entity and relationship tables
ALTER TABLE public.property_entity_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entity_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entity_search_cache ENABLE ROW LEVEL SECURITY;

-- Document tables
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_property_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_access_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_search_sessions ENABLE ROW LEVEL SECURITY;

-- Florida-specific data tables
ALTER TABLE public.fl_nav_assessment_detail ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_nav_parcel_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_sdf_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fl_tpp_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nav_parcel_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nav_assessment_details ENABLE ROW LEVEL SECURITY;

-- Sunbiz entity tables
ALTER TABLE public.sunbiz_officers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_fictitious_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_lien_debtors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_lien_secured_parties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_officer_corporation_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_corporate_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_partnership_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_principal_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sunbiz_monitoring_agents ENABLE ROW LEVEL SECURITY;

-- ML and analytics tables
ALTER TABLE public.ml_property_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ml_model_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ml_property_scores_xgb ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ab_validation_results ENABLE ROW LEVEL SECURITY;

-- Staging and utility tables
ALTER TABLE public.florida_entities_staging ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_change_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.spatial_ref_sys ENABLE ROW LEVEL SECURITY;

-- Create authenticated read + service_role write policies
-- Property and tax data
CREATE POLICY "property_sales_history_read" ON public.property_sales_history FOR SELECT TO authenticated USING (true);
CREATE POLICY "property_sales_history_service" ON public.property_sales_history FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "property_ownership_history_read" ON public.property_ownership_history FOR SELECT TO authenticated USING (true);
CREATE POLICY "property_ownership_history_service" ON public.property_ownership_history FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "tax_certificates_read" ON public.tax_certificates FOR SELECT TO authenticated USING (true);
CREATE POLICY "tax_certificates_service" ON public.tax_certificates FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "tax_deed_auctions_read" ON public.tax_deed_auctions FOR SELECT TO authenticated USING (true);
CREATE POLICY "tax_deed_auctions_service" ON public.tax_deed_auctions FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "tax_deed_bidding_items_read" ON public.tax_deed_bidding_items FOR SELECT TO authenticated USING (true);
CREATE POLICY "tax_deed_bidding_items_service" ON public.tax_deed_bidding_items FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Entity data
CREATE POLICY "property_entity_matches_read" ON public.property_entity_matches FOR SELECT TO authenticated USING (true);
CREATE POLICY "property_entity_matches_service" ON public.property_entity_matches FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "entity_relationships_read" ON public.entity_relationships FOR SELECT TO authenticated USING (true);
CREATE POLICY "entity_relationships_service" ON public.entity_relationships FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "entity_search_cache_read" ON public.entity_search_cache FOR SELECT TO authenticated USING (true);
CREATE POLICY "entity_search_cache_service" ON public.entity_search_cache FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Document data (Note: documents may need user-specific policies - review based on your use case)
CREATE POLICY "documents_read" ON public.documents FOR SELECT TO authenticated USING (true);
CREATE POLICY "documents_service" ON public.documents FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "document_categories_read" ON public.document_categories FOR SELECT TO authenticated USING (true);
CREATE POLICY "document_categories_service" ON public.document_categories FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "document_property_links_read" ON public.document_property_links FOR SELECT TO authenticated USING (true);
CREATE POLICY "document_property_links_service" ON public.document_property_links FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "document_access_log_service" ON public.document_access_log FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "document_alerts_service" ON public.document_alerts FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "document_search_sessions_service" ON public.document_search_sessions FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Florida data
CREATE POLICY "fl_nav_assessment_detail_read" ON public.fl_nav_assessment_detail FOR SELECT TO authenticated USING (true);
CREATE POLICY "fl_nav_assessment_detail_service" ON public.fl_nav_assessment_detail FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "fl_nav_parcel_summary_read" ON public.fl_nav_parcel_summary FOR SELECT TO authenticated USING (true);
CREATE POLICY "fl_nav_parcel_summary_service" ON public.fl_nav_parcel_summary FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "fl_sdf_sales_read" ON public.fl_sdf_sales FOR SELECT TO authenticated USING (true);
CREATE POLICY "fl_sdf_sales_service" ON public.fl_sdf_sales FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "fl_tpp_accounts_read" ON public.fl_tpp_accounts FOR SELECT TO authenticated USING (true);
CREATE POLICY "fl_tpp_accounts_service" ON public.fl_tpp_accounts FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "nav_parcel_assessments_read" ON public.nav_parcel_assessments FOR SELECT TO authenticated USING (true);
CREATE POLICY "nav_parcel_assessments_service" ON public.nav_parcel_assessments FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "nav_assessment_details_read" ON public.nav_assessment_details FOR SELECT TO authenticated USING (true);
CREATE POLICY "nav_assessment_details_service" ON public.nav_assessment_details FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Sunbiz entity data
CREATE POLICY "sunbiz_officers_read" ON public.sunbiz_officers FOR SELECT TO authenticated USING (true);
CREATE POLICY "sunbiz_officers_service" ON public.sunbiz_officers FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "sunbiz_fictitious_events_read" ON public.sunbiz_fictitious_events FOR SELECT TO authenticated USING (true);
CREATE POLICY "sunbiz_fictitious_events_service" ON public.sunbiz_fictitious_events FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "sunbiz_lien_debtors_read" ON public.sunbiz_lien_debtors FOR SELECT TO authenticated USING (true);
CREATE POLICY "sunbiz_lien_debtors_service" ON public.sunbiz_lien_debtors FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "sunbiz_lien_secured_parties_read" ON public.sunbiz_lien_secured_parties FOR SELECT TO authenticated USING (true);
CREATE POLICY "sunbiz_lien_secured_parties_service" ON public.sunbiz_lien_secured_parties FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "sunbiz_officer_corporation_matches_read" ON public.sunbiz_officer_corporation_matches FOR SELECT TO authenticated USING (true);
CREATE POLICY "sunbiz_officer_corporation_matches_service" ON public.sunbiz_officer_corporation_matches FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "sunbiz_corporate_events_read" ON public.sunbiz_corporate_events FOR SELECT TO authenticated USING (true);
CREATE POLICY "sunbiz_corporate_events_service" ON public.sunbiz_corporate_events FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "sunbiz_partnership_events_read" ON public.sunbiz_partnership_events FOR SELECT TO authenticated USING (true);
CREATE POLICY "sunbiz_partnership_events_service" ON public.sunbiz_partnership_events FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "sunbiz_principal_data_read" ON public.sunbiz_principal_data FOR SELECT TO authenticated USING (true);
CREATE POLICY "sunbiz_principal_data_service" ON public.sunbiz_principal_data FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "sunbiz_monitoring_agents_service" ON public.sunbiz_monitoring_agents FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ML and analytics
CREATE POLICY "ml_property_scores_read" ON public.ml_property_scores FOR SELECT TO authenticated USING (true);
CREATE POLICY "ml_property_scores_service" ON public.ml_property_scores FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "ml_model_metrics_service" ON public.ml_model_metrics FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "ml_property_scores_xgb_read" ON public.ml_property_scores_xgb FOR SELECT TO authenticated USING (true);
CREATE POLICY "ml_property_scores_xgb_service" ON public.ml_property_scores_xgb FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "ab_validation_results_service" ON public.ab_validation_results FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Staging and utility
CREATE POLICY "florida_entities_staging_service" ON public.florida_entities_staging FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "property_change_log_service" ON public.property_change_log FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "spatial_ref_sys_read" ON public.spatial_ref_sys FOR SELECT TO authenticated USING (true);
CREATE POLICY "spatial_ref_sys_service" ON public.spatial_ref_sys FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Commit the transaction
COMMIT;

-- =========================
-- VALIDATION QUERIES
-- =========================
-- Run these to verify RLS is enabled correctly

-- Check that RLS is enabled on all tables
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'user_preferences', 'watchlist', 'notification_history', 'user_watchlists',
    'watchlist_items', 'watchlist_alerts', 'notification_queue',
    'agent_activity_logs', 'agent_config', 'agent_notifications', 'edge_functions',
    'property_sales_history', 'tax_certificates', 'documents'
)
ORDER BY tablename;

-- Check policies exist
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Count policies per table
SELECT
    tablename,
    COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- =========================
-- SUCCESS CONFIRMATION
-- =========================
-- If validation queries show RLS enabled and policies created:
-- ✅ Phase 2 Complete - Row Level Security implemented
-- ✅ User data isolation active
-- ✅ System tables protected
-- ✅ Ready to proceed to Phase 3 (performance optimization)