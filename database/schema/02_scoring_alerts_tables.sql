-- ConcordBroker Phase 2: Property Scoring & Alerts System
-- Execute this in Supabase SQL Editor AFTER Phase 1 tables are created

-- ============================================================================
-- PROPERTY SCORES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS property_scores (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  parcel_id TEXT NOT NULL UNIQUE,
  county TEXT NOT NULL,
  investment_score NUMERIC(5,2) CHECK (investment_score >= 0 AND investment_score <= 100),
  market_score NUMERIC(5,2) CHECK (market_score >= 0 AND market_score <= 100),
  rental_yield_score NUMERIC(5,2) CHECK (rental_yield_score >= 0 AND rental_yield_score <= 100),
  flip_potential_score NUMERIC(5,2) CHECK (flip_potential_score >= 0 AND flip_potential_score <= 100),
  location_score NUMERIC(5,2) CHECK (location_score >= 0 AND location_score <= 100),
  condition_score NUMERIC(5,2) CHECK (condition_score >= 0 AND condition_score <= 100),
  liquidity_score NUMERIC(5,2) CHECK (liquidity_score >= 0 AND liquidity_score <= 100),
  score_factors JSONB DEFAULT '{}',
  last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_property_scores_parcel_id ON property_scores(parcel_id);
CREATE INDEX IF NOT EXISTS idx_property_scores_investment_score ON property_scores(investment_score DESC);
CREATE INDEX IF NOT EXISTS idx_property_scores_county ON property_scores(county);
CREATE INDEX IF NOT EXISTS idx_property_scores_market_score ON property_scores(market_score DESC);
CREATE INDEX IF NOT EXISTS idx_property_scores_last_calculated ON property_scores(last_calculated DESC);

-- ============================================================================
-- PROPERTY ALERTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS property_alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  parcel_id TEXT NOT NULL,
  county TEXT,
  alert_type TEXT NOT NULL CHECK (alert_type IN ('price_change', 'new_sale', 'foreclosure', 'tax_deed', 'permit', 'owner_change', 'market_event', 'score_change')),
  alert_title TEXT NOT NULL,
  alert_message TEXT NOT NULL,
  alert_data JSONB DEFAULT '{}',
  is_read BOOLEAN DEFAULT FALSE,
  is_dismissed BOOLEAN DEFAULT FALSE,
  priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_property_alerts_user_id ON property_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_property_alerts_parcel_id ON property_alerts(parcel_id);
CREATE INDEX IF NOT EXISTS idx_property_alerts_type ON property_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_property_alerts_unread ON property_alerts(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_property_alerts_priority ON property_alerts(priority);
CREATE INDEX IF NOT EXISTS idx_property_alerts_created_at ON property_alerts(created_at DESC);

-- Enable RLS and create policies
ALTER TABLE property_alerts ENABLE ROW LEVEL SECURITY;

-- RLS Policies for property_alerts
DROP POLICY IF EXISTS "Users can manage own alerts" ON property_alerts;
CREATE POLICY "Users can manage own alerts" ON property_alerts
  FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- MARKET COMPARABLES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS market_comparables (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  parcel_id TEXT NOT NULL,
  county TEXT NOT NULL,
  comparable_parcel_id TEXT NOT NULL,
  similarity_score NUMERIC(5,2) CHECK (similarity_score >= 0 AND similarity_score <= 100),
  distance_miles NUMERIC(8,2),
  price_difference_pct NUMERIC(8,2),
  comparison_factors JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(parcel_id, comparable_parcel_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_market_comparables_parcel_id ON market_comparables(parcel_id);
CREATE INDEX IF NOT EXISTS idx_market_comparables_similarity ON market_comparables(similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_market_comparables_distance ON market_comparables(distance_miles);
CREATE INDEX IF NOT EXISTS idx_market_comparables_county ON market_comparables(county);

-- ============================================================================
-- USER ALERT PREFERENCES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_alert_preferences (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  price_change_threshold NUMERIC(5,2) DEFAULT 10.0,
  enable_price_alerts BOOLEAN DEFAULT TRUE,
  enable_sale_alerts BOOLEAN DEFAULT TRUE,
  enable_foreclosure_alerts BOOLEAN DEFAULT TRUE,
  enable_tax_deed_alerts BOOLEAN DEFAULT TRUE,
  enable_permit_alerts BOOLEAN DEFAULT FALSE,
  enable_owner_change_alerts BOOLEAN DEFAULT TRUE,
  enable_market_alerts BOOLEAN DEFAULT TRUE,
  enable_score_alerts BOOLEAN DEFAULT TRUE,
  alert_frequency TEXT DEFAULT 'daily' CHECK (alert_frequency IN ('immediate', 'daily', 'weekly')),
  email_alerts BOOLEAN DEFAULT TRUE,
  push_notifications BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_user_alert_preferences_user_id ON user_alert_preferences(user_id);

-- Enable RLS and create policies
ALTER TABLE user_alert_preferences ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_alert_preferences
DROP POLICY IF EXISTS "Users can manage own alert preferences" ON user_alert_preferences;
CREATE POLICY "Users can manage own alert preferences" ON user_alert_preferences
  FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- PROPERTY ANALYTICS TABLE (for trending data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS property_analytics (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  parcel_id TEXT NOT NULL,
  county TEXT NOT NULL,
  metric_type TEXT NOT NULL CHECK (metric_type IN ('views', 'watchlist_adds', 'note_creates', 'searches')),
  metric_value INTEGER DEFAULT 1,
  date_recorded DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(parcel_id, metric_type, date_recorded)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_property_analytics_parcel_id ON property_analytics(parcel_id);
CREATE INDEX IF NOT EXISTS idx_property_analytics_metric_type ON property_analytics(metric_type);
CREATE INDEX IF NOT EXISTS idx_property_analytics_date ON property_analytics(date_recorded DESC);
CREATE INDEX IF NOT EXISTS idx_property_analytics_county ON property_analytics(county);

-- ============================================================================
-- PROPERTY SCORE CALCULATION FUNCTIONS
-- ============================================================================

-- Function to calculate investment score based on property data
CREATE OR REPLACE FUNCTION calculate_investment_score(p_parcel_id TEXT)
RETURNS JSONB AS $$
DECLARE
    property_data RECORD;
    investment_score NUMERIC := 50.0;
    market_score NUMERIC := 50.0;
    rental_score NUMERIC := 50.0;
    flip_score NUMERIC := 50.0;
    location_score NUMERIC := 50.0;
    condition_score NUMERIC := 50.0;
    liquidity_score NUMERIC := 50.0;
    score_factors JSONB := '{}';
BEGIN
    -- Get property data from florida_parcels
    SELECT
        just_value,
        land_value,
        building_value,
        year_built,
        total_living_area,
        phy_city,
        county,
        sale_price,
        sale_date,
        property_use
    INTO property_data
    FROM florida_parcels
    WHERE parcel_id = p_parcel_id
    LIMIT 1;

    IF property_data IS NULL THEN
        RETURN jsonb_build_object(
            'error', 'Property not found',
            'parcel_id', p_parcel_id
        );
    END IF;

    -- Calculate market score based on value metrics
    IF property_data.just_value IS NOT NULL AND property_data.just_value > 0 THEN
        -- Properties under $300K get higher investment scores
        IF property_data.just_value < 300000 THEN
            market_score := market_score + 15;
        ELSIF property_data.just_value < 500000 THEN
            market_score := market_score + 10;
        ELSIF property_data.just_value > 1000000 THEN
            market_score := market_score - 10;
        END IF;

        -- Value to land ratio
        IF property_data.land_value IS NOT NULL AND property_data.land_value > 0 THEN
            IF (property_data.just_value / property_data.land_value) < 3 THEN
                market_score := market_score + 10; -- Land-heavy properties
            END IF;
        END IF;

        score_factors := jsonb_set(score_factors, '{market_factors}',
            jsonb_build_object('just_value', property_data.just_value));
    END IF;

    -- Calculate rental yield score
    IF property_data.total_living_area IS NOT NULL AND property_data.total_living_area > 0 THEN
        -- Properties with good price per sqft
        IF property_data.just_value / property_data.total_living_area < 200 THEN
            rental_score := rental_score + 20;
        ELSIF property_data.just_value / property_data.total_living_area < 300 THEN
            rental_score := rental_score + 10;
        END IF;

        score_factors := jsonb_set(score_factors, '{rental_factors}',
            jsonb_build_object('price_per_sqft', property_data.just_value / property_data.total_living_area));
    END IF;

    -- Calculate flip potential score
    IF property_data.year_built IS NOT NULL THEN
        -- Newer properties have better flip potential
        IF property_data.year_built > 2000 THEN
            flip_score := flip_score + 15;
        ELSIF property_data.year_built > 1980 THEN
            flip_score := flip_score + 10;
        ELSIF property_data.year_built < 1970 THEN
            flip_score := flip_score - 15; -- May need significant work
        END IF;

        score_factors := jsonb_set(score_factors, '{flip_factors}',
            jsonb_build_object('year_built', property_data.year_built));
    END IF;

    -- Calculate location score based on city/county
    location_score := location_score + 5; -- Default bonus for Florida

    -- Calculate condition score (estimated from age and value)
    IF property_data.building_value IS NOT NULL AND property_data.land_value IS NOT NULL THEN
        IF property_data.building_value > property_data.land_value * 2 THEN
            condition_score := condition_score + 10; -- Well-improved property
        END IF;
    END IF;

    -- Calculate liquidity score
    IF property_data.sale_date IS NOT NULL AND property_data.sale_date::date > CURRENT_DATE - INTERVAL '5 years' THEN
        liquidity_score := liquidity_score + 15; -- Recent sales activity
    END IF;

    -- Calculate overall investment score (weighted average)
    investment_score := (
        market_score * 0.25 +
        rental_score * 0.20 +
        flip_score * 0.15 +
        location_score * 0.15 +
        condition_score * 0.15 +
        liquidity_score * 0.10
    );

    -- Ensure scores are within bounds
    investment_score := GREATEST(0, LEAST(100, investment_score));
    market_score := GREATEST(0, LEAST(100, market_score));
    rental_score := GREATEST(0, LEAST(100, rental_score));
    flip_score := GREATEST(0, LEAST(100, flip_score));
    location_score := GREATEST(0, LEAST(100, location_score));
    condition_score := GREATEST(0, LEAST(100, condition_score));
    liquidity_score := GREATEST(0, LEAST(100, liquidity_score));

    RETURN jsonb_build_object(
        'parcel_id', p_parcel_id,
        'investment_score', investment_score,
        'market_score', market_score,
        'rental_yield_score', rental_score,
        'flip_potential_score', flip_score,
        'location_score', location_score,
        'condition_score', condition_score,
        'liquidity_score', liquidity_score,
        'score_factors', score_factors,
        'calculated_at', NOW()
    );
END;
$$ LANGUAGE plpgsql;

-- Function to find comparable properties
CREATE OR REPLACE FUNCTION find_comparable_properties(
    p_parcel_id TEXT,
    p_radius_miles NUMERIC DEFAULT 5,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    comparable_parcel_id TEXT,
    similarity_score NUMERIC,
    distance_miles NUMERIC,
    price_difference_pct NUMERIC,
    comparison_factors JSONB
) AS $$
DECLARE
    base_property RECORD;
BEGIN
    -- Get base property data
    SELECT just_value, total_living_area, year_built, phy_city, county, property_use
    INTO base_property
    FROM florida_parcels
    WHERE parcel_id = p_parcel_id
    LIMIT 1;

    IF base_property IS NULL THEN
        RETURN;
    END IF;

    -- Find similar properties in the same county/city
    RETURN QUERY
    SELECT
        fp.parcel_id::TEXT as comparable_parcel_id,
        (
            CASE WHEN base_property.just_value > 0 AND fp.just_value > 0 THEN
                100 - ABS(base_property.just_value - fp.just_value) / GREATEST(base_property.just_value, fp.just_value) * 100
            ELSE 50 END +
            CASE WHEN base_property.total_living_area > 0 AND fp.total_living_area > 0 THEN
                100 - ABS(base_property.total_living_area - fp.total_living_area) / GREATEST(base_property.total_living_area, fp.total_living_area) * 100
            ELSE 50 END +
            CASE WHEN base_property.year_built IS NOT NULL AND fp.year_built IS NOT NULL THEN
                100 - ABS(base_property.year_built - fp.year_built) / 50.0 * 100
            ELSE 50 END
        ) / 3.0 AS similarity_score,
        0.5::NUMERIC AS distance_miles, -- Simplified distance
        CASE WHEN base_property.just_value > 0 AND fp.just_value > 0 THEN
            (fp.just_value - base_property.just_value) / base_property.just_value * 100
        ELSE 0 END AS price_difference_pct,
        jsonb_build_object(
            'value_match', CASE WHEN base_property.just_value > 0 AND fp.just_value > 0 THEN
                100 - ABS(base_property.just_value - fp.just_value) / GREATEST(base_property.just_value, fp.just_value) * 100
            ELSE NULL END,
            'size_match', CASE WHEN base_property.total_living_area > 0 AND fp.total_living_area > 0 THEN
                100 - ABS(base_property.total_living_area - fp.total_living_area) / GREATEST(base_property.total_living_area, fp.total_living_area) * 100
            ELSE NULL END,
            'age_match', CASE WHEN base_property.year_built IS NOT NULL AND fp.year_built IS NOT NULL THEN
                100 - ABS(base_property.year_built - fp.year_built) / 50.0 * 100
            ELSE NULL END
        ) AS comparison_factors
    FROM florida_parcels fp
    WHERE fp.parcel_id != p_parcel_id
        AND fp.county = base_property.county
        AND fp.phy_city = base_property.phy_city
        AND fp.property_use = base_property.property_use
        AND fp.just_value > 0
        AND fp.is_redacted = FALSE
    ORDER BY similarity_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT FIELDS
-- ============================================================================

DROP TRIGGER IF EXISTS update_user_alert_preferences_updated_at ON user_alert_preferences;
CREATE TRIGGER update_user_alert_preferences_updated_at
  BEFORE UPDATE ON user_alert_preferences
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA INSERTION (for testing)
-- ============================================================================

-- Insert sample alert preferences for testing
-- INSERT INTO user_alert_preferences (user_id)
-- SELECT id FROM auth.users LIMIT 1
-- ON CONFLICT (user_id) DO NOTHING;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify tables were created successfully
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('property_scores', 'property_alerts', 'market_comparables', 'user_alert_preferences', 'property_analytics');
-- SELECT routine_name, routine_type FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name IN ('calculate_investment_score', 'find_comparable_properties');