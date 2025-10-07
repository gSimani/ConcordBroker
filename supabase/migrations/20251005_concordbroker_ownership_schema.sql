-- ============================================================================
-- ConcordBroker Multi-Corporation Ownership Schema
-- Purpose: Track property owners across multiple corporate entities
-- Date: 2025-10-05
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Fuzzy text matching
CREATE EXTENSION IF NOT EXISTS vector;   -- For RAG embeddings

-- ============================================================================
-- OWNER IDENTITY RESOLUTION
-- ============================================================================

-- Canonical owner identities (resolves name variants)
CREATE TABLE IF NOT EXISTS owner_identities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name text NOT NULL UNIQUE,
    variant_names text[] DEFAULT '{}',  -- ["J Smith", "SMITH JOHN", "Smith, J"]

    -- Identity metadata
    identity_type text DEFAULT 'person', -- 'person', 'company', 'trust', 'estate'
    confidence_score numeric(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Contact info (if available)
    primary_address jsonb,  -- {addr1, city, state, zip}
    phone text,
    email text,

    -- Stats (computed)
    total_properties int DEFAULT 0,
    total_value numeric(15,2) DEFAULT 0,

    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX owner_identities_canonical_idx ON owner_identities(canonical_name);
CREATE INDEX owner_identities_variant_idx ON owner_identities USING gin(variant_names);
CREATE INDEX owner_identities_type_idx ON owner_identities(identity_type);

-- ============================================================================
-- PROPERTY OWNERSHIP LINKING
-- ============================================================================

-- Link properties to owner identities
CREATE TABLE IF NOT EXISTS property_ownership (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Property reference
    parcel_id text NOT NULL,
    county_code int NOT NULL,

    -- Owner reference
    owner_identity_id uuid REFERENCES owner_identities(id) ON DELETE CASCADE,

    -- Ownership details
    ownership_type text, -- 'individual', 'corporation', 'llc', 'trust', 'partnership'
    entity_id text,  -- References florida_entities.entity_id if corporate
    entity_name text,  -- Denormalized for quick lookup

    -- Ownership share
    ownership_percentage numeric(5,2) DEFAULT 100.00,

    -- Timeline
    acquired_date date,
    disposed_date date,

    -- Metadata
    source text DEFAULT 'florida_parcels',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),

    -- Constraints
    CONSTRAINT property_ownership_unique UNIQUE (parcel_id, county_code, owner_identity_id)
);

CREATE INDEX property_ownership_parcel_idx ON property_ownership(parcel_id, county_code);
CREATE INDEX property_ownership_identity_idx ON property_ownership(owner_identity_id);
CREATE INDEX property_ownership_entity_idx ON property_ownership(entity_id) WHERE entity_id IS NOT NULL;
CREATE INDEX property_ownership_type_idx ON property_ownership(ownership_type);
CREATE INDEX property_ownership_active_idx ON property_ownership(owner_identity_id)
    WHERE disposed_date IS NULL;

-- ============================================================================
-- ENTITY PRINCIPALS (Sunbiz linking)
-- ============================================================================

-- Link corporate entities to owner identities
CREATE TABLE IF NOT EXISTS entity_principals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Entity reference
    entity_id text NOT NULL,  -- References florida_entities.entity_id
    entity_name text,  -- Denormalized

    -- Principal reference
    owner_identity_id uuid REFERENCES owner_identities(id) ON DELETE CASCADE,
    principal_name text NOT NULL,  -- As listed in Sunbiz

    -- Role details
    role text,  -- 'owner', 'officer', 'director', 'registered_agent', 'manager', 'member'
    title text,  -- 'CEO', 'President', 'Managing Member', etc.

    -- Ownership
    ownership_percentage numeric(5,2),

    -- Timeline
    start_date date,
    end_date date,

    -- Metadata
    source text DEFAULT 'sunbiz',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),

    CONSTRAINT entity_principals_unique UNIQUE (entity_id, owner_identity_id, role)
);

CREATE INDEX entity_principals_entity_idx ON entity_principals(entity_id);
CREATE INDEX entity_principals_identity_idx ON entity_principals(owner_identity_id);
CREATE INDEX entity_principals_role_idx ON entity_principals(role);
CREATE INDEX entity_principals_active_idx ON entity_principals(owner_identity_id)
    WHERE end_date IS NULL;

-- ============================================================================
-- MATERIALIZED VIEW: OWNER PORTFOLIO SUMMARY
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS owner_portfolio_summary AS
SELECT
    oi.id as owner_identity_id,
    oi.canonical_name,
    oi.identity_type,

    -- Property stats
    COUNT(DISTINCT po.parcel_id) as total_properties,
    COUNT(DISTINCT po.parcel_id) FILTER (WHERE po.disposed_date IS NULL) as active_properties,

    -- Entity stats
    COUNT(DISTINCT po.entity_id) as total_entities,
    COUNT(DISTINCT ep.entity_id) as total_sunbiz_entities,

    -- Value stats
    SUM(p.just_value) as total_portfolio_value,
    AVG(p.just_value) as avg_property_value,
    MAX(p.just_value) as max_property_value,
    MIN(p.just_value) as min_property_value,

    -- Geographic distribution
    array_agg(DISTINCT p.county) as counties,
    COUNT(DISTINCT p.county) as total_counties,

    -- Entity IDs for quick lookup
    json_agg(DISTINCT jsonb_build_object(
        'entity_id', po.entity_id,
        'entity_name', po.entity_name,
        'properties_count', COUNT(po.parcel_id) OVER (PARTITION BY po.entity_id)
    )) FILTER (WHERE po.entity_id IS NOT NULL) as entities,

    -- Latest activity
    MAX(po.acquired_date) as latest_acquisition,
    MAX(po.updated_at) as last_updated

FROM owner_identities oi
LEFT JOIN property_ownership po ON oi.id = po.owner_identity_id AND po.disposed_date IS NULL
LEFT JOIN florida_parcels p ON po.parcel_id = p.parcel_id AND po.county_code = p.county_code
LEFT JOIN entity_principals ep ON oi.id = ep.owner_identity_id AND ep.end_date IS NULL

GROUP BY oi.id, oi.canonical_name, oi.identity_type;

CREATE UNIQUE INDEX owner_portfolio_summary_idx ON owner_portfolio_summary(owner_identity_id);
CREATE INDEX owner_portfolio_summary_name_idx ON owner_portfolio_summary(canonical_name);
CREATE INDEX owner_portfolio_summary_properties_idx ON owner_portfolio_summary(total_properties DESC);
CREATE INDEX owner_portfolio_summary_value_idx ON owner_portfolio_summary(total_portfolio_value DESC NULLS LAST);

-- ============================================================================
-- RAG SYSTEM FOR AGENT LION
-- ============================================================================

-- Documentation embeddings
CREATE TABLE IF NOT EXISTS concordbroker_docs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Document classification
    category text NOT NULL,  -- 'tax_law', 'investment', 'corporate', 'internal'
    document_name text NOT NULL,
    section_title text,

    -- Content
    content text NOT NULL,
    embedding vector(1536),

    -- Metadata
    metadata jsonb,  -- {page, formula_name, statute_section, source_url, etc}

    -- Timestamps
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX concordbroker_docs_embedding_idx ON concordbroker_docs
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX concordbroker_docs_category_idx ON concordbroker_docs(category);
CREATE INDEX concordbroker_docs_document_idx ON concordbroker_docs(document_name);
CREATE INDEX concordbroker_docs_metadata_idx ON concordbroker_docs USING gin(metadata);

-- Agent Lion conversation memory
CREATE TABLE IF NOT EXISTS agent_lion_conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Session tracking
    session_id uuid NOT NULL,
    user_id uuid,  -- If authenticated

    -- Message
    role text NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content text NOT NULL,

    -- Context
    context jsonb,  -- {property_id, county, owner_identity_id, entity_ids, analysis_type}
    embedding vector(1536),

    -- Metadata
    tokens_used int,
    model text DEFAULT 'gpt-4',

    created_at timestamptz DEFAULT now()
);

CREATE INDEX agent_lion_conv_session_idx ON agent_lion_conversations(session_id, created_at DESC);
CREATE INDEX agent_lion_conv_user_idx ON agent_lion_conversations(user_id, created_at DESC)
    WHERE user_id IS NOT NULL;
CREATE INDEX agent_lion_conv_embedding_idx ON agent_lion_conversations
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- Agent Lion analysis cache
CREATE TABLE IF NOT EXISTS agent_lion_analyses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Analysis classification
    analysis_type text NOT NULL,  -- 'valuation', 'investment_roi', 'ownership_graph', 'financial_proforma'
    subject_id text NOT NULL,  -- parcel_id or owner_identity_id

    -- Inputs and outputs
    inputs jsonb NOT NULL,
    outputs jsonb NOT NULL,

    -- Methodology
    formula_used text,
    assumptions jsonb,
    confidence_score numeric(3,2),

    -- Caching
    expires_at timestamptz DEFAULT (now() + interval '30 days'),

    created_at timestamptz DEFAULT now()
);

CREATE INDEX agent_lion_analyses_subject_idx ON agent_lion_analyses(subject_id, analysis_type);
CREATE INDEX agent_lion_analyses_type_idx ON agent_lion_analyses(analysis_type);
CREATE INDEX agent_lion_analyses_expires_idx ON agent_lion_analyses(expires_at)
    WHERE expires_at > now();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Search RAG documentation
CREATE OR REPLACE FUNCTION search_concordbroker_docs(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    category_filter text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    category text,
    document_name text,
    section_title text,
    content text,
    metadata jsonb,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.category,
        d.document_name,
        d.section_title,
        d.content,
        d.metadata,
        1 - (d.embedding <=> query_embedding) as similarity
    FROM concordbroker_docs d
    WHERE (category_filter IS NULL OR d.category = category_filter)
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Get owner complete portfolio
CREATE OR REPLACE FUNCTION get_owner_portfolio(p_owner_identity_id uuid)
RETURNS jsonb AS $$
DECLARE
    result jsonb;
BEGIN
    SELECT jsonb_build_object(
        'owner', (
            SELECT jsonb_build_object(
                'id', id,
                'name', canonical_name,
                'type', identity_type,
                'variant_names', variant_names
            )
            FROM owner_identities
            WHERE id = p_owner_identity_id
        ),
        'summary', (
            SELECT row_to_json(ops.*)
            FROM owner_portfolio_summary ops
            WHERE ops.owner_identity_id = p_owner_identity_id
        ),
        'properties', (
            SELECT json_agg(
                jsonb_build_object(
                    'parcel_id', po.parcel_id,
                    'county', p.county,
                    'address', p.phy_addr1,
                    'city', p.phy_city,
                    'value', p.just_value,
                    'entity_name', po.entity_name,
                    'entity_id', po.entity_id,
                    'acquired_date', po.acquired_date
                )
                ORDER BY p.just_value DESC
            )
            FROM property_ownership po
            LEFT JOIN florida_parcels p ON po.parcel_id = p.parcel_id AND po.county_code = p.county_code
            WHERE po.owner_identity_id = p_owner_identity_id
            AND po.disposed_date IS NULL
        ),
        'entities', (
            SELECT json_agg(
                jsonb_build_object(
                    'entity_id', ep.entity_id,
                    'entity_name', ep.entity_name,
                    'role', ep.role,
                    'title', ep.title,
                    'ownership_percentage', ep.ownership_percentage
                )
            )
            FROM entity_principals ep
            WHERE ep.owner_identity_id = p_owner_identity_id
            AND ep.end_date IS NULL
        )
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Find owner by property
CREATE OR REPLACE FUNCTION find_owner_by_property(p_parcel_id text, p_county_code int)
RETURNS uuid AS $$
    SELECT owner_identity_id
    FROM property_ownership
    WHERE parcel_id = p_parcel_id
    AND county_code = p_county_code
    AND disposed_date IS NULL
    LIMIT 1;
$$ LANGUAGE sql STABLE;

-- Function: Refresh owner stats
CREATE OR REPLACE FUNCTION refresh_owner_stats()
RETURNS void AS $$
BEGIN
    -- Update total_properties and total_value in owner_identities
    UPDATE owner_identities oi SET
        total_properties = (
            SELECT COUNT(*)
            FROM property_ownership po
            WHERE po.owner_identity_id = oi.id
            AND po.disposed_date IS NULL
        ),
        total_value = (
            SELECT COALESCE(SUM(p.just_value), 0)
            FROM property_ownership po
            LEFT JOIN florida_parcels p ON po.parcel_id = p.parcel_id AND po.county_code = p.county_code
            WHERE po.owner_identity_id = oi.id
            AND po.disposed_date IS NULL
        ),
        updated_at = now();

    -- Refresh materialized view
    REFRESH MATERIALIZED VIEW CONCURRENTLY owner_portfolio_summary;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE owner_identities ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_ownership ENABLE ROW LEVEL SECURITY;
ALTER TABLE entity_principals ENABLE ROW LEVEL SECURITY;
ALTER TABLE concordbroker_docs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_lion_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_lion_analyses ENABLE ROW LEVEL SECURITY;

-- Public read access for authenticated users
CREATE POLICY "Public read access" ON owner_identities FOR SELECT USING (true);
CREATE POLICY "Public read access" ON property_ownership FOR SELECT USING (true);
CREATE POLICY "Public read access" ON entity_principals FOR SELECT USING (true);
CREATE POLICY "Public read access" ON concordbroker_docs FOR SELECT USING (true);
CREATE POLICY "Public read access" ON agent_lion_analyses FOR SELECT USING (true);

-- User-specific conversation access
CREATE POLICY "Users can read own conversations" ON agent_lion_conversations
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

-- Service role can do everything
CREATE POLICY "Service role full access" ON owner_identities FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON property_ownership FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON entity_principals FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON concordbroker_docs FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON agent_lion_conversations FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON agent_lion_analyses FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT USAGE ON SCHEMA public TO authenticated, anon;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated, anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated, anon, service_role;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ ConcordBroker ownership schema deployed successfully!';
    RAISE NOTICE 'Created tables:';
    RAISE NOTICE '  - owner_identities (canonical owner names)';
    RAISE NOTICE '  - property_ownership (property → owner → entity linking)';
    RAISE NOTICE '  - entity_principals (Sunbiz entity officers/owners)';
    RAISE NOTICE '  - concordbroker_docs (RAG embeddings)';
    RAISE NOTICE '  - agent_lion_conversations (chat memory)';
    RAISE NOTICE '  - agent_lion_analyses (cached analyses)';
    RAISE NOTICE 'Created views:';
    RAISE NOTICE '  - owner_portfolio_summary (aggregated portfolios)';
    RAISE NOTICE 'Created functions:';
    RAISE NOTICE '  - search_concordbroker_docs()';
    RAISE NOTICE '  - get_owner_portfolio()';
    RAISE NOTICE '  - find_owner_by_property()';
    RAISE NOTICE '  - refresh_owner_stats()';
    RAISE NOTICE '';
    RAISE NOTICE 'Next: Run owner identity resolution to populate data';
END $$;
