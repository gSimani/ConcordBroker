-- APPLY: Temporarily disable REST API timeouts for bulk upload
-- These are role-scoped changes that only affect API sessions
-- Much safer than database-wide changes

-- Disable timeouts for authenticated role
ALTER ROLE authenticated IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE authenticated IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';

-- Disable timeouts for anon role  
ALTER ROLE anon IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE anon IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';

-- Also disable for service_role if using service key
ALTER ROLE service_role IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE service_role IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';

-- Verify the settings
SELECT 
    rolname,
    rolconfig
FROM pg_roles 
WHERE rolname IN ('authenticated', 'anon', 'service_role');

-- Note: Run this in Supabase SQL Editor with your database owner credentials