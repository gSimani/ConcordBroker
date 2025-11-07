-- APPLY: Temporarily disable REST API timeouts for bulk upload (role-scoped)
-- Run this BEFORE starting the upload
-- Affects PostgREST sessions for anon/authenticated and service_role

ALTER ROLE authenticated IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE authenticated IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';

ALTER ROLE anon IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE anon IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';

ALTER ROLE service_role IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE service_role IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';

-- Verify the settings were applied
SELECT 
    rolname,
    rolconfig
FROM pg_roles 
WHERE rolname IN ('authenticated', 'anon', 'service_role');