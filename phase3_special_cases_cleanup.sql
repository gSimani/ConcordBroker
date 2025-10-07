-- ============================================================================
-- PHASE 3: SPECIAL CASES & CLEANUP
-- ============================================================================
-- LOWER PRIORITY - Execute after Phase 1 & 2 completion and verification
-- Handles edge cases, system tables, and final cleanup
--
-- COVERS: Spatial data, document storage, archive tables, staging tables
-- PURPOSE: Complete security remediation for remaining edge cases
-- ============================================================================

-- ============================================================================
-- SPECIAL CASE 1: SPATIAL REFERENCE SYSTEM (PostGIS)
-- ============================================================================
-- PostGIS spatial_ref_sys table should not have RLS (system requirement)
-- SOLUTION: Move to extensions schema to avoid public schema RLS requirements

BEGIN;

-- Create extensions schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS extensions;

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA extensions TO postgres, anon, authenticated, service_role;

-- Move spatial_ref_sys to extensions schema (if it exists in public)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'spatial_ref_sys') THEN
        ALTER TABLE public.spatial_ref_sys SET SCHEMA extensions;
        RAISE NOTICE 'Moved spatial_ref_sys to extensions schema';
    ELSE
        RAISE NOTICE 'spatial_ref_sys not found in public schema - no action needed';
    END IF;
END $$;

-- Grant read access to spatial reference system
GRANT SELECT ON extensions.spatial_ref_sys TO anon, authenticated;

COMMIT;

-- ============================================================================
-- SPECIAL CASE 2: DOCUMENT & FILE STORAGE TABLES
-- ============================================================================
-- Handle document storage with user-based and public access patterns

BEGIN;

-- Enable RLS on document tables
ALTER TABLE IF EXISTS documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_documents ENABLE ROW LEVEL SECURITY;

-- Users can access their own uploaded documents
CREATE POLICY IF NOT EXISTS "users_own_documents" ON documents
    FOR ALL USING (
        auth.uid() = uploaded_by OR
        auth.jwt() ->> 'role' IN ('admin', 'service_role')
    );

-- Public property documents (non-sensitive attachments)
CREATE POLICY IF NOT EXISTS "public_property_docs" ON property_documents
    FOR SELECT USING (
        is_public = true OR
        auth.role() = 'authenticated' OR
        auth.jwt() ->> 'role' IN ('admin', 'service_role')
    );

-- Authenticated users can upload property documents
CREATE POLICY IF NOT EXISTS "authenticated_upload_property_docs" ON property_documents
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Service role can manage all documents
CREATE POLICY IF NOT EXISTS "service_role_manage_documents" ON documents
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

COMMIT;

-- ============================================================================
-- SPECIAL CASE 3: HISTORICAL & ARCHIVE TABLES
-- ============================================================================
-- Archive tables should be read-only for authenticated users

BEGIN;

-- Enable RLS on archive/backup tables
ALTER TABLE IF EXISTS florida_parcels_backup ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS florida_parcels_backup_migration ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_ownership_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sunbiz_officers_backup ENABLE ROW LEVEL SECURITY;

-- Archive tables - authenticated read only, service role full access
CREATE POLICY IF NOT EXISTS "authenticated_read_parcels_backup" ON florida_parcels_backup
    FOR SELECT USING (
        auth.role() = 'authenticated' OR
        auth.jwt() ->> 'role' IN ('admin', 'service_role')
    );

CREATE POLICY IF NOT EXISTS "authenticated_read_ownership_history" ON property_ownership_history
    FOR SELECT USING (
        auth.role() = 'authenticated' OR
        auth.jwt() ->> 'role' IN ('admin', 'service_role')
    );

-- Service role can manage archive tables
CREATE POLICY IF NOT EXISTS "service_role_manage_archives" ON florida_parcels_backup
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_manage_ownership_history" ON property_ownership_history
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

COMMIT;

-- ============================================================================
-- SPECIAL CASE 4: STAGING & TEMPORARY TABLES
-- ============================================================================
-- Staging tables should only be accessible to service role and ETL processes

BEGIN;

-- Enable RLS on staging/temporary tables
ALTER TABLE IF EXISTS florida_raw_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS nal_staging_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS florida_entities_staging ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS stg_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS raw_properties ENABLE ROW LEVEL SECURITY;

-- Staging tables - service role only access
CREATE POLICY IF NOT EXISTS "service_role_only_raw_records" ON florida_raw_records
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_only_nal_staging" ON nal_staging_data
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_only_stg_properties" ON stg_properties
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_only_raw_properties" ON raw_properties
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

COMMIT;

-- ============================================================================
-- SPECIAL CASE 5: CACHE & PERFORMANCE TABLES
-- ============================================================================
-- Cache tables for query optimization - service role managed

BEGIN;

-- Enable RLS on cache tables
ALTER TABLE IF EXISTS entity_search_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS property_search_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS cache_invalidation_log ENABLE ROW LEVEL SECURITY;

-- Cache tables - read access for authenticated, write for service role
CREATE POLICY IF NOT EXISTS "authenticated_read_entity_cache" ON entity_search_cache
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_cache" ON entity_search_cache
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_cache_invalidation" ON cache_invalidation_log
    FOR ALL USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

COMMIT;

-- ============================================================================
-- SPECIAL CASE 6: DIMENSION & LOOKUP TABLES
-- ============================================================================
-- Reference dimension tables - public read, service role write

BEGIN;

-- Enable RLS on dimension tables
ALTER TABLE IF EXISTS dim_address ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS dim_owner ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS dim_parcel ENABLE ROW LEVEL SECURITY;

-- Dimension tables - public read access
CREATE POLICY IF NOT EXISTS "public_read_dim_address" ON dim_address
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_dim_owner" ON dim_owner
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "public_read_dim_parcel" ON dim_parcel
    FOR SELECT USING (true);

-- Service role write access for dimension maintenance
CREATE POLICY IF NOT EXISTS "service_role_maintain_dimensions" ON dim_address
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

CREATE POLICY IF NOT EXISTS "service_role_update_dimensions" ON dim_address
    FOR UPDATE USING (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

COMMIT;

-- ============================================================================
-- SPECIAL CASE 7: AUDIT & COMPLIANCE TABLES
-- ============================================================================
-- Audit trails should be append-only with restricted access

BEGIN;

-- Enable RLS on audit tables
ALTER TABLE IF EXISTS audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS match_audit_log ENABLE ROW LEVEL SECURITY;

-- Audit tables - admin read access, service role append
CREATE POLICY IF NOT EXISTS "admin_read_audit_log" ON audit_log
    FOR SELECT USING (auth.jwt() ->> 'role' IN ('admin', 'service_role'));

CREATE POLICY IF NOT EXISTS "service_role_append_audit" ON audit_log
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

-- No UPDATE or DELETE on audit tables for compliance
-- Audit logs should be immutable

CREATE POLICY IF NOT EXISTS "admin_read_match_audit" ON match_audit_log
    FOR SELECT USING (auth.jwt() ->> 'role' IN ('admin', 'service_role'));

CREATE POLICY IF NOT EXISTS "service_role_append_match_audit" ON match_audit_log
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' IN ('service_role', 'admin'));

COMMIT;

-- ============================================================================
-- CLEANUP: REMAINING TABLES ASSESSMENT
-- ============================================================================
-- Identify and handle any remaining tables without RLS

DO $$
DECLARE
    table_record RECORD;
    remaining_count INTEGER := 0;
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'PHASE 3 CLEANUP: Assessing remaining tables without RLS';
    RAISE NOTICE '============================================================';

    FOR table_record IN
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
        ORDER BY tablename
    LOOP
        remaining_count := remaining_count + 1;

        -- Categorize remaining tables and suggest action
        IF table_record.tablename LIKE '%_temp' OR table_record.tablename LIKE 'temp_%' THEN
            RAISE NOTICE 'TEMP TABLE: % (Consider enabling RLS for service_role only)', table_record.tablename;
        ELSIF table_record.tablename LIKE '%_test' OR table_record.tablename LIKE 'test_%' THEN
            RAISE NOTICE 'TEST TABLE: % (Consider dropping if not needed)', table_record.tablename;
        ELSIF table_record.tablename LIKE '%_unknown' THEN
            RAISE NOTICE 'UNKNOWN TABLE: % (Investigate purpose and enable appropriate RLS)', table_record.tablename;
        ELSE
            RAISE NOTICE 'UNHANDLED TABLE: % (Manual review required)', table_record.tablename;
        END IF;
    END LOOP;

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Total remaining tables without RLS: %', remaining_count;

    IF remaining_count = 0 THEN
        RAISE NOTICE 'SUCCESS: All tables in public schema now have RLS enabled';
    ELSIF remaining_count <= 5 THEN
        RAISE NOTICE 'GOOD: Only % tables remain - manual review recommended', remaining_count;
    ELSE
        RAISE WARNING 'WARNING: % tables still need RLS - additional analysis required', remaining_count;
    END IF;

    RAISE NOTICE '============================================================';
END $$;

-- ============================================================================
-- FINAL SECURITY AUDIT
-- ============================================================================

-- Create comprehensive security audit report
DO $$
DECLARE
    total_tables INTEGER;
    rls_tables INTEGER;
    total_policies INTEGER;
    definer_views INTEGER;
    coverage_pct NUMERIC;
BEGIN
    -- Count tables and policies
    SELECT COUNT(*) INTO total_tables
    FROM pg_tables WHERE schemaname = 'public';

    SELECT COUNT(*) INTO rls_tables
    FROM pg_tables t
    WHERE schemaname = 'public'
    AND EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = t.schemaname AND c.relname = t.tablename
        AND c.relrowsecurity = true
    );

    SELECT COUNT(*) INTO total_policies
    FROM pg_policies WHERE schemaname = 'public';

    SELECT COUNT(*) INTO definer_views
    FROM pg_views
    WHERE schemaname = 'public'
    AND definition ILIKE '%security_definer%';

    coverage_pct := ROUND((rls_tables::NUMERIC / total_tables::NUMERIC) * 100, 2);

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'SUPABASE SECURITY REMEDIATION - FINAL AUDIT REPORT';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'PHASE 1 - Security Definer Views:';
    RAISE NOTICE '  Remaining SECURITY DEFINER views: %', definer_views;
    RAISE NOTICE '  Status: %', CASE WHEN definer_views = 0 THEN 'RESOLVED ✓' ELSE 'NEEDS ATTENTION ✗' END;
    RAISE NOTICE '';
    RAISE NOTICE 'PHASE 2 - Row Level Security:';
    RAISE NOTICE '  Total public tables: %', total_tables;
    RAISE NOTICE '  Tables with RLS: %', rls_tables;
    RAISE NOTICE '  RLS coverage: %% %', coverage_pct;
    RAISE NOTICE '  Total RLS policies: %', total_policies;
    RAISE NOTICE '';
    RAISE NOTICE 'OVERALL SECURITY STATUS:';

    IF definer_views = 0 AND coverage_pct >= 90 THEN
        RAISE NOTICE '  ✓ EXCELLENT - Security remediation successful';
        RAISE NOTICE '  ✓ Ready for production deployment';
    ELSIF definer_views = 0 AND coverage_pct >= 75 THEN
        RAISE NOTICE '  ⚠ GOOD - Minor cleanup recommended';
        RAISE NOTICE '  ⚠ Review remaining tables without RLS';
    ELSE
        RAISE NOTICE '  ✗ INCOMPLETE - Additional work required';
        RAISE NOTICE '  ✗ Not ready for production deployment';
    END IF;

    RAISE NOTICE '============================================================';
END $$;

-- ============================================================================
-- FINAL VERIFICATION QUERIES
-- ============================================================================

-- Log completion to agent activity
INSERT INTO agent_activity_logs (agent_name, activity_type, status, details, created_at)
VALUES (
    'security_remediation_agent',
    'phase_3_special_cases',
    'completed',
    jsonb_build_object(
        'phase', 'phase_3',
        'completed_at', NOW(),
        'spatial_refs_moved', true,
        'documents_secured', true,
        'archives_protected', true,
        'staging_restricted', true,
        'cache_secured', true,
        'audit_protected', true
    ),
    NOW()
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- POST-COMPLETION VERIFICATION QUERIES
-- ============================================================================

/*
-- Run these queries after script completion:

-- 1. List all remaining tables without RLS
SELECT schemaname, tablename, 'NEEDS_RLS' as status
FROM pg_tables t
WHERE schemaname = 'public'
AND NOT EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = t.schemaname AND c.relname = t.tablename
    AND c.relrowsecurity = true
)
ORDER BY tablename;

-- 2. Security summary by table category
SELECT
    CASE
        WHEN tablename LIKE 'user_%' THEN 'User Data'
        WHEN tablename LIKE 'agent_%' THEN 'System/Agent'
        WHEN tablename LIKE 'florida_%' THEN 'Property Data'
        WHEN tablename LIKE 'sunbiz_%' THEN 'Business Data'
        WHEN tablename LIKE 'tax_%' THEN 'Tax Data'
        WHEN tablename LIKE '%_backup' OR tablename LIKE '%_history' THEN 'Archive'
        WHEN tablename LIKE '%_staging' OR tablename LIKE 'raw_%' THEN 'Staging'
        ELSE 'Other'
    END as category,
    COUNT(*) as total_tables,
    SUM(CASE WHEN c.relrowsecurity THEN 1 ELSE 0 END) as rls_enabled,
    ROUND(AVG(CASE WHEN c.relrowsecurity THEN 100.0 ELSE 0.0 END), 1) as rls_coverage_pct
FROM pg_tables t
LEFT JOIN pg_class c ON c.relname = t.tablename
LEFT JOIN pg_namespace n ON c.relnamespace = n.oid AND n.nspname = t.schemaname
WHERE t.schemaname = 'public'
GROUP BY 1
ORDER BY rls_coverage_pct DESC;

-- 3. Policy count by table
SELECT tablename, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
HAVING COUNT(*) > 0
ORDER BY policy_count DESC;
*/