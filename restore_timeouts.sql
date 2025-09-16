-- REVERT: Restore default timeout settings after bulk upload
-- Run this after the upload is complete to restore normal behavior

-- Reset timeouts for authenticated role
ALTER ROLE authenticated IN DATABASE postgres RESET statement_timeout;
ALTER ROLE authenticated IN DATABASE postgres RESET idle_in_transaction_session_timeout;

-- Reset timeouts for anon role
ALTER ROLE anon IN DATABASE postgres RESET statement_timeout;
ALTER ROLE anon IN DATABASE postgres RESET idle_in_transaction_session_timeout;

-- Reset timeouts for service_role
ALTER ROLE service_role IN DATABASE postgres RESET statement_timeout;
ALTER ROLE service_role IN DATABASE postgres RESET idle_in_transaction_session_timeout;

-- Verify the settings are reset
SELECT 
    rolname,
    rolconfig
FROM pg_roles 
WHERE rolname IN ('authenticated', 'anon', 'service_role');

-- Note: Run this in Supabase SQL Editor after upload completes