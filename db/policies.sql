-- ConcordBroker RLS Policies
-- PostgreSQL/Supabase Row Level Security Configuration
-- Version 0.1.0

-- Set schema
SET search_path TO concordbroker, public;

-- ================================
-- Enable RLS on all tables
-- ================================

ALTER TABLE parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE recorded_docs ENABLE ROW LEVEL SECURITY;
ALTER TABLE doc_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE officers ENABLE ROW LEVEL SECURITY;
ALTER TABLE parcel_entity_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;

-- ================================
-- Service Role Policies (Full Access)
-- ================================

-- Service role can do everything (API backend)
CREATE POLICY "Service role full access parcels" ON parcels
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access sales" ON sales
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access recorded_docs" ON recorded_docs
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access doc_parcels" ON doc_parcels
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access entities" ON entities
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access officers" ON officers
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access parcel_entity_links" ON parcel_entity_links
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access jobs" ON jobs
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access users" ON users
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access saved_searches" ON saved_searches
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access watchlist" ON watchlist
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access rag_documents" ON rag_documents
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access agent_tasks" ON agent_tasks
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ================================
-- Authenticated User Policies (Read-Only for Most Tables)
-- ================================

-- Authenticated users can read public property data
CREATE POLICY "Authenticated read parcels" ON parcels
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated read sales" ON sales
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated read recorded_docs" ON recorded_docs
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated read doc_parcels" ON doc_parcels
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated read entities" ON entities
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated read officers" ON officers
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated read parcel_entity_links" ON parcel_entity_links
    FOR SELECT
    TO authenticated
    USING (true);

-- Authenticated users can only see their own user data
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT
    TO authenticated
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id AND role = 'user'); -- Prevent role escalation

-- Authenticated users can manage their own saved searches
CREATE POLICY "Users can view own saved searches" ON saved_searches
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own saved searches" ON saved_searches
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own saved searches" ON saved_searches
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own saved searches" ON saved_searches
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- Authenticated users can manage their own watchlist
CREATE POLICY "Users can view own watchlist" ON watchlist
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can add to own watchlist" ON watchlist
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own watchlist" ON watchlist
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete from own watchlist" ON watchlist
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- RAG documents are read-only for authenticated users
CREATE POLICY "Authenticated read rag_documents" ON rag_documents
    FOR SELECT
    TO authenticated
    USING (true);

-- ================================
-- Anonymous User Policies (No Access)
-- ================================

-- Anonymous users cannot access any data
CREATE POLICY "Deny anon parcels" ON parcels
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon sales" ON sales
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon recorded_docs" ON recorded_docs
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon doc_parcels" ON doc_parcels
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon entities" ON entities
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon officers" ON officers
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon parcel_entity_links" ON parcel_entity_links
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon jobs" ON jobs
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon users" ON users
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon saved_searches" ON saved_searches
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon watchlist" ON watchlist
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon rag_documents" ON rag_documents
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Deny anon agent_tasks" ON agent_tasks
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

-- ================================
-- Admin Policies (for admin role users)
-- ================================

-- Create admin policies for full access when user.role = 'admin'
CREATE POLICY "Admin full access parcels" ON parcels
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'admin'
        )
    );

CREATE POLICY "Admin full access sales" ON sales
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'admin'
        )
    );

CREATE POLICY "Admin full access jobs" ON jobs
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'admin'
        )
    );

CREATE POLICY "Admin full access agent_tasks" ON agent_tasks
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'admin'
        )
    );

-- ================================
-- Special Policies for Jobs Table
-- ================================

-- Allow authenticated users to view job status (but not details)
CREATE POLICY "Authenticated view job status" ON jobs
    FOR SELECT
    TO authenticated
    USING (true)
    -- Only show basic info, not error messages or parameters
    WITH CHECK (true);

-- ================================
-- Functions for Policy Helpers
-- ================================

-- Function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM users 
        WHERE id = auth.uid() 
        AND role = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user owns a resource
CREATE OR REPLACE FUNCTION owns_resource(resource_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN auth.uid() = resource_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================
-- Grant Permissions
-- ================================

-- Grant SELECT on views to authenticated users
GRANT SELECT ON v_parcel_summary TO authenticated;
GRANT SELECT ON v_recent_activity TO authenticated;

-- Grant EXECUTE on functions to authenticated users
GRANT EXECUTE ON FUNCTION calculate_property_score(VARCHAR) TO authenticated;
GRANT EXECUTE ON FUNCTION match_entity_name(TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION is_admin() TO authenticated;
GRANT EXECUTE ON FUNCTION owns_resource(UUID) TO authenticated;

-- Grant all permissions to service_role
GRANT ALL ON ALL TABLES IN SCHEMA concordbroker TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA concordbroker TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA concordbroker TO service_role;

-- ================================
-- API Key Scopes (for additional security)
-- ================================

-- Create a function to validate API key scopes
CREATE OR REPLACE FUNCTION validate_api_scope(required_scope TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    token_scopes TEXT[];
BEGIN
    -- Get scopes from JWT claims
    token_scopes := string_to_array(
        current_setting('request.jwt.claims', true)::json->>'scope', 
        ' '
    );
    
    -- Check if required scope exists
    RETURN required_scope = ANY(token_scopes);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================
-- Audit Log Policies
-- ================================

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    row_id TEXT,
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS on audit log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Only service role and admins can read audit logs
CREATE POLICY "Service role read audit_log" ON audit_log
    FOR SELECT
    TO service_role
    USING (true);

CREATE POLICY "Admin read audit_log" ON audit_log
    FOR SELECT
    TO authenticated
    USING (is_admin());

-- Service role can insert audit logs
CREATE POLICY "Service role insert audit_log" ON audit_log
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- ================================
-- Comments
-- ================================

COMMENT ON POLICY "Service role full access parcels" ON parcels IS 
    'Allows API backend full access to parcel data';
    
COMMENT ON POLICY "Authenticated read parcels" ON parcels IS 
    'Allows authenticated users to view public property data';
    
COMMENT ON POLICY "Deny anon parcels" ON parcels IS 
    'Prevents anonymous users from accessing any parcel data';
    
COMMENT ON FUNCTION is_admin() IS 
    'Helper function to check if current user has admin role';
    
COMMENT ON FUNCTION owns_resource(UUID) IS 
    'Helper function to check if current user owns a resource';

-- ================================
-- Initialize Default Admin User (optional)
-- ================================

-- This should be run manually after setup with proper admin credentials
-- INSERT INTO users (id, email, name, role) 
-- VALUES (
--     'YOUR-ADMIN-UUID-HERE',
--     'admin@concordbroker.com',
--     'System Administrator',
--     'admin'
-- ) ON CONFLICT (id) DO NOTHING;