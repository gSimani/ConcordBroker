-- ============================================
-- SUPABASE TIMEOUT MANAGEMENT SCRIPT
-- ============================================
-- Purpose: Safely disable/restore timeouts for bulk database operations
-- Use Case: Large property uploads, DOR code assignments, bulk updates
-- Safety: Includes monitoring queries and restore procedures
-- ============================================

-- ============================================
-- SECTION 1: DISABLE TIMEOUTS (Before Bulk Upload)
-- ============================================
-- WARNING: Only run this before starting bulk operations
-- Make sure to run SECTION 2 after operations complete!

-- Option A: Role-level timeout disabling (affects ALL sessions for role)
-- Recommended for: Long-running operations spanning multiple connections
ALTER ROLE authenticated IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE authenticated IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';

ALTER ROLE anon IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE anon IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';

ALTER ROLE service_role IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE service_role IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';

-- Option B: Session-level timeout disabling (SAFER - only affects current session)
-- Recommended for: Single-session bulk operations
-- Uncomment these instead of Option A if you want session-only scope:
-- SET statement_timeout = '0';
-- SET idle_in_transaction_session_timeout = '0';

-- ============================================
-- VERIFICATION: Check that timeouts are disabled
-- ============================================
SELECT
    rolname,
    rolconfig
FROM pg_roles
WHERE rolname IN ('authenticated', 'anon', 'service_role');

-- Expected output should show:
-- rolconfig: {statement_timeout=0,idle_in_transaction_session_timeout=0}

-- For session-level verification:
-- SHOW statement_timeout;
-- SHOW idle_in_transaction_session_timeout;

-- ============================================
-- SECTION 2: RESTORE TIMEOUTS (After Bulk Upload)
-- ============================================
-- IMPORTANT: Run this immediately after bulk operations complete!
-- This restores normal timeouts to prevent runaway queries

-- Restore role-level timeouts to safe defaults
ALTER ROLE authenticated IN DATABASE postgres RESET statement_timeout;
ALTER ROLE authenticated IN DATABASE postgres RESET idle_in_transaction_session_timeout;

ALTER ROLE anon IN DATABASE postgres RESET statement_timeout;
ALTER ROLE anon IN DATABASE postgres RESET idle_in_transaction_session_timeout;

ALTER ROLE service_role IN DATABASE postgres RESET statement_timeout;
ALTER ROLE service_role IN DATABASE postgres RESET idle_in_transaction_session_timeout;

-- Or set to specific safe values (e.g., 5 minutes)
-- ALTER ROLE authenticated IN DATABASE postgres SET statement_timeout = '300s';
-- ALTER ROLE authenticated IN DATABASE postgres SET idle_in_transaction_session_timeout = '300s';

-- For session-level restore:
-- RESET statement_timeout;
-- RESET idle_in_transaction_session_timeout;

-- ============================================
-- VERIFICATION: Confirm timeouts are restored
-- ============================================
SELECT
    rolname,
    rolconfig
FROM pg_roles
WHERE rolname IN ('authenticated', 'anon', 'service_role');

-- Expected output should show NULL or default values

-- ============================================
-- SECTION 3: MONITORING QUERIES
-- ============================================
-- Use these to monitor long-running operations during bulk uploads

-- 1. Check active queries and their durations
SELECT
    pid,
    usename,
    application_name,
    state,
    now() - query_start AS duration,
    query
FROM pg_stat_activity
WHERE state != 'idle'
    AND query NOT LIKE '%pg_stat_activity%'
ORDER BY duration DESC;

-- 2. Check for blocking queries
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
    JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
    JOIN pg_catalog.pg_locks blocking_locks
        ON blocking_locks.locktype = blocked_locks.locktype
        AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
        AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
        AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
        AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
        AND blocking_locks.pid != blocked_locks.pid
    JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- 3. Check table sizes (before/after operations)
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('florida_parcels', 'property_sales_history', 'tax_certificates')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 4. Check index health after bulk operations
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND tablename = 'florida_parcels'
ORDER BY idx_scan DESC;

-- ============================================
-- SECTION 4: TABLE MAINTENANCE (After Large Uploads)
-- ============================================
-- Run these after bulk operations to maintain performance

-- Update table statistics for query planner
ANALYZE florida_parcels;
ANALYZE property_sales_history;
ANALYZE tax_certificates;

-- Reclaim storage and update statistics (takes longer)
-- VACUUM ANALYZE florida_parcels;

-- For extremely large operations, consider VACUUM FULL (locks table!)
-- VACUUM FULL ANALYZE florida_parcels;

-- ============================================
-- USAGE WORKFLOW
-- ============================================
--
-- STEP 1: Before bulk upload
--    - Run SECTION 1 (disable timeouts)
--    - Run verification query
--
-- STEP 2: During bulk upload
--    - Monitor with SECTION 3 queries
--    - Watch for errors or blocking
--
-- STEP 3: After bulk upload completes
--    - Run SECTION 2 (restore timeouts)
--    - Run verification query
--    - Run SECTION 4 (table maintenance)
--
-- STEP 4: Emergency rollback
--    - If something goes wrong, immediately run SECTION 2
--    - Check pg_stat_activity for hanging queries
--    - Kill problematic queries: SELECT pg_terminate_backend(pid);
--
-- ============================================
-- SAFETY NOTES
-- ============================================
--
-- 1. Session-level is SAFER than role-level
--    - Use SET instead of ALTER ROLE when possible
--    - Session-level automatically restores on disconnect
--
-- 2. Always restore timeouts after operations
--    - Disabled timeouts can allow runaway queries
--    - Set calendar reminders or use automation
--
-- 3. Monitor during large operations
--    - Use SECTION 3 queries every 5-10 minutes
--    - Watch for blocking and memory usage
--
-- 4. Plan for rollback
--    - Take backups before major operations
--    - Have a plan to kill queries if needed
--    - Test on small datasets first
--
-- ============================================
-- TROUBLESHOOTING
-- ============================================
--
-- Problem: "statement timeout" error during upload
-- Solution: Verify timeouts are disabled (run verification query)
--
-- Problem: Operation hangs indefinitely
-- Solution: Check for blocking queries (SECTION 3, query #2)
--
-- Problem: Can't restore timeouts (permission denied)
-- Solution: Must be superuser or role owner to ALTER ROLE
--
-- Problem: Forgot to restore timeouts
-- Solution: Run SECTION 2 immediately, then check pg_stat_activity
--
-- ============================================

-- End of script
