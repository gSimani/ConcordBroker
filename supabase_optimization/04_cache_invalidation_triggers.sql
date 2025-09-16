-- =====================================================
-- STEP 4B: DATABASE TRIGGERS FOR CACHE INVALIDATION
-- Ensures cache consistency with database changes
-- =====================================================

-- Chain of Thought:
-- 1. Create notification channel for cache invalidation
-- 2. Create trigger function for data changes
-- 3. Attach triggers to critical tables
-- 4. Set up listener in application code

BEGIN;

-- =====================================================
-- NOTIFICATION CHANNELS
-- =====================================================

-- Create channels for different cache types
-- These will be listened to by the Redis cache layer

-- Channel for property updates
-- NOTIFY cache_invalidation, 'property:BROWARD:123456789';

-- Channel for county statistics updates
-- NOTIFY cache_invalidation_stats, 'county:BROWARD';

-- Channel for search results
-- NOTIFY cache_invalidation_search, 'search:*';

-- =====================================================
-- TRIGGER FUNCTIONS
-- =====================================================

-- Function to notify cache invalidation on property changes
CREATE OR REPLACE FUNCTION notify_property_cache_invalidation()
RETURNS TRIGGER AS $$
DECLARE
    channel TEXT;
    payload TEXT;
BEGIN
    -- Determine the operation type
    IF TG_OP = 'DELETE' THEN
        -- For deletes, use OLD record
        payload := format('property:%s:%s', OLD.county, OLD.parcel_id);

        -- Also invalidate county stats
        PERFORM pg_notify('cache_invalidation_stats',
            format('county:%s', OLD.county));

    ELSIF TG_OP = 'UPDATE' THEN
        -- For updates, invalidate both old and new if county changed
        payload := format('property:%s:%s', NEW.county, NEW.parcel_id);

        -- Invalidate old county if changed
        IF OLD.county != NEW.county THEN
            PERFORM pg_notify('cache_invalidation',
                format('property:%s:%s', OLD.county, OLD.parcel_id));
            PERFORM pg_notify('cache_invalidation_stats',
                format('county:%s', OLD.county));
        END IF;

        -- Invalidate county stats for new county
        PERFORM pg_notify('cache_invalidation_stats',
            format('county:%s', NEW.county));

    ELSIF TG_OP = 'INSERT' THEN
        -- For inserts, use NEW record
        payload := format('property:%s:%s', NEW.county, NEW.parcel_id);

        -- Invalidate county stats
        PERFORM pg_notify('cache_invalidation_stats',
            format('county:%s', NEW.county));
    END IF;

    -- Send main property invalidation
    PERFORM pg_notify('cache_invalidation', payload);

    -- Invalidate search results (pattern-based)
    PERFORM pg_notify('cache_invalidation_search', 'search:*');

    -- Return appropriate record
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to notify on bulk operations
CREATE OR REPLACE FUNCTION notify_bulk_cache_invalidation()
RETURNS TRIGGER AS $$
BEGIN
    -- For statement-level triggers on bulk operations

    -- Invalidate all county stats
    PERFORM pg_notify('cache_invalidation_stats', 'county:*');

    -- Invalidate all search results
    PERFORM pg_notify('cache_invalidation_search', 'search:*');

    -- Log bulk invalidation
    RAISE NOTICE 'Bulk cache invalidation triggered for table %', TG_TABLE_NAME;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to handle materialized view refresh
CREATE OR REPLACE FUNCTION notify_materialized_view_refresh()
RETURNS TRIGGER AS $$
BEGIN
    -- When materialized views are refreshed, invalidate related caches

    IF TG_TABLE_NAME = 'mv_county_statistics' THEN
        PERFORM pg_notify('cache_invalidation_stats', 'county:*');

    ELSIF TG_TABLE_NAME = 'mv_monthly_sales_trends' THEN
        PERFORM pg_notify('cache_invalidation', 'trends:*');

    ELSIF TG_TABLE_NAME = 'mv_property_valuations' THEN
        PERFORM pg_notify('cache_invalidation', 'valuations:*');
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- CREATE TRIGGERS
-- =====================================================

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS trg_property_cache_invalidation ON florida_parcels;
DROP TRIGGER IF EXISTS trg_bulk_property_cache_invalidation ON florida_parcels;

-- Row-level trigger for individual property changes
CREATE TRIGGER trg_property_cache_invalidation
    AFTER INSERT OR UPDATE OR DELETE
    ON florida_parcels
    FOR EACH ROW
    EXECUTE FUNCTION notify_property_cache_invalidation();

-- Statement-level trigger for bulk operations
CREATE TRIGGER trg_bulk_property_cache_invalidation
    AFTER TRUNCATE
    ON florida_parcels
    FOR EACH STATEMENT
    EXECUTE FUNCTION notify_bulk_cache_invalidation();

-- =====================================================
-- CACHE WARMING PROCEDURES
-- =====================================================

-- Procedure to warm cache with most accessed properties
CREATE OR REPLACE PROCEDURE warm_property_cache(
    p_county TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 1000
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_record RECORD;
    v_count INTEGER := 0;
BEGIN
    -- Get most valuable properties to pre-cache
    FOR v_record IN
        SELECT parcel_id, county
        FROM florida_parcels
        WHERE (p_county IS NULL OR county = p_county)
            AND just_value > 0
        ORDER BY just_value DESC
        LIMIT p_limit
    LOOP
        -- Notify cache warming system
        PERFORM pg_notify('cache_warm',
            format('property:%s:%s', v_record.county, v_record.parcel_id));

        v_count := v_count + 1;

        -- Batch notifications
        IF v_count % 100 = 0 THEN
            PERFORM pg_sleep(0.1); -- Small delay to prevent overwhelming
        END IF;
    END LOOP;

    RAISE NOTICE 'Warmed cache with % properties', v_count;
END;
$$;

-- Procedure to warm cache with county statistics
CREATE OR REPLACE PROCEDURE warm_county_stats_cache()
LANGUAGE plpgsql
AS $$
DECLARE
    v_county TEXT;
BEGIN
    -- Warm cache for all counties
    FOR v_county IN
        SELECT DISTINCT county
        FROM florida_parcels
        WHERE county IS NOT NULL
        ORDER BY county
    LOOP
        -- Notify cache warming system
        PERFORM pg_notify('cache_warm_stats', format('county:%s', v_county));
    END LOOP;

    RAISE NOTICE 'Warmed cache for all county statistics';
END;
$$;

-- =====================================================
-- CACHE INVALIDATION PATTERNS
-- =====================================================

-- Function to invalidate cache by pattern
CREATE OR REPLACE FUNCTION invalidate_cache_pattern(
    p_pattern TEXT
)
RETURNS void AS $$
BEGIN
    -- Send pattern-based invalidation
    PERFORM pg_notify('cache_invalidation_pattern', p_pattern);

    RAISE NOTICE 'Cache invalidation sent for pattern: %', p_pattern;
END;
$$ LANGUAGE plpgsql;

-- Function to invalidate all caches
CREATE OR REPLACE FUNCTION invalidate_all_caches()
RETURNS void AS $$
BEGIN
    -- Nuclear option - invalidate everything
    PERFORM pg_notify('cache_invalidation_all', 'FLUSH_ALL');

    RAISE WARNING 'All caches have been invalidated!';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- MONITORING FUNCTIONS
-- =====================================================

-- Function to track cache invalidation frequency
CREATE TABLE IF NOT EXISTS cache_invalidation_log (
    id SERIAL PRIMARY KEY,
    invalidation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    channel TEXT,
    payload TEXT,
    table_name TEXT,
    operation TEXT
);

-- Enhanced trigger function with logging
CREATE OR REPLACE FUNCTION notify_and_log_cache_invalidation()
RETURNS TRIGGER AS $$
DECLARE
    payload TEXT;
BEGIN
    -- Generate payload based on operation
    IF TG_OP = 'DELETE' THEN
        payload := format('property:%s:%s', OLD.county, OLD.parcel_id);
    ELSE
        payload := format('property:%s:%s', NEW.county, NEW.parcel_id);
    END IF;

    -- Log invalidation
    INSERT INTO cache_invalidation_log (channel, payload, table_name, operation)
    VALUES ('cache_invalidation', payload, TG_TABLE_NAME, TG_OP);

    -- Send notification
    PERFORM pg_notify('cache_invalidation', payload);

    -- Clean old logs (keep last 7 days)
    DELETE FROM cache_invalidation_log
    WHERE invalidation_time < CURRENT_TIMESTAMP - INTERVAL '7 days';

    -- Return appropriate record
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- View to analyze cache invalidation patterns
CREATE OR REPLACE VIEW v_cache_invalidation_analysis AS
SELECT
    DATE_TRUNC('hour', invalidation_time) as hour,
    channel,
    operation,
    COUNT(*) as invalidation_count,
    COUNT(DISTINCT payload) as unique_keys_invalidated
FROM cache_invalidation_log
WHERE invalidation_time >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', invalidation_time), channel, operation
ORDER BY hour DESC;

COMMIT;

-- =====================================================
-- USAGE EXAMPLES
-- =====================================================

-- Warm property cache for Broward County
-- CALL warm_property_cache('BROWARD', 500);

-- Warm all county statistics
-- CALL warm_county_stats_cache();

-- Invalidate specific pattern
-- SELECT invalidate_cache_pattern('search:county=MIAMI-DADE*');

-- View invalidation patterns
-- SELECT * FROM v_cache_invalidation_analysis;

-- =====================================================
-- EXPECTED IMPROVEMENTS
-- =====================================================

-- Query: Repeated property lookup
-- Before: 50ms (database query each time)
-- After: 0.05ms (Redis cache) - 1000x improvement

-- Query: County statistics (materialized view)
-- Before: 100ms (materialized view query)
-- After: 0.1ms (Redis cache) - 1000x improvement

-- Query: Complex search results
-- Before: 500ms (database query with joins)
-- After: 0.5ms (Redis cache) - 1000x improvement