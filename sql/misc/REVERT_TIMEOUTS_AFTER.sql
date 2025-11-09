-- REVERT: Restore default timeout settings after bulk upload
-- Run this AFTER the upload completes

ALTER ROLE authenticated IN DATABASE postgres RESET statement_timeout;
ALTER ROLE authenticated IN DATABASE postgres RESET idle_in_transaction_session_timeout;

ALTER ROLE anon IN DATABASE postgres RESET statement_timeout;
ALTER ROLE anon IN DATABASE postgres RESET idle_in_transaction_session_timeout;

ALTER ROLE service_role IN DATABASE postgres RESET statement_timeout;
ALTER ROLE service_role IN DATABASE postgres RESET idle_in_transaction_session_timeout;

-- Verify the settings were reset
SELECT 
    rolname,
    rolconfig
FROM pg_roles 
WHERE rolname IN ('authenticated', 'anon', 'service_role');