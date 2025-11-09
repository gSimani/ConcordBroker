-- ============================================================================
-- PROPERTY APPRAISER CLOUD SYNC SCHEMA
-- ============================================================================
-- Tables and functions for automated daily synchronization
-- ============================================================================

-- 1) SYNC LOG TABLE - Tracks processed files
CREATE TABLE IF NOT EXISTS public.property_sync_log (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  filename text NOT NULL,
  file_hash text,
  file_type text CHECK (file_type IN ('NAL', 'NAP', 'SDF', 'NAV')),
  county_code text,
  status text CHECK (status IN ('pending', 'processing', 'completed', 'error')),
  error_message text,
  records_processed integer DEFAULT 0,
  processed_at timestamp with time zone DEFAULT now(),
  metadata jsonb,
  created_at timestamp with time zone DEFAULT now(),
  
  -- Unique constraint to prevent duplicate processing
  CONSTRAINT unique_file_processing UNIQUE (filename, file_hash)
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_sync_log_filename ON public.property_sync_log(filename);
CREATE INDEX IF NOT EXISTS idx_sync_log_status ON public.property_sync_log(status);
CREATE INDEX IF NOT EXISTS idx_sync_log_processed_at ON public.property_sync_log(processed_at DESC);

-- 2) SYNC STATISTICS VIEW - Monitor sync performance
CREATE OR REPLACE VIEW public.property_sync_stats AS
SELECT 
  DATE(processed_at) as sync_date,
  file_type,
  COUNT(*) as files_processed,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
  SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed,
  SUM(records_processed) as total_records,
  AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) as avg_processing_time_seconds
FROM public.property_sync_log
GROUP BY DATE(processed_at), file_type
ORDER BY sync_date DESC, file_type;

-- 3) FUNCTION: Get last successful sync
CREATE OR REPLACE FUNCTION public.get_last_property_sync()
RETURNS TABLE (
  last_sync timestamp with time zone,
  files_processed integer,
  records_processed integer,
  next_sync_due timestamp with time zone
)
LANGUAGE sql
STABLE
AS $$
  SELECT 
    MAX(processed_at) as last_sync,
    COUNT(*)::integer as files_processed,
    SUM(records_processed)::integer as records_processed,
    (MAX(processed_at) + INTERVAL '1 day')::timestamp with time zone as next_sync_due
  FROM public.property_sync_log
  WHERE status = 'completed'
  AND processed_at > CURRENT_DATE - INTERVAL '2 days';
$$;

-- 4) FUNCTION: Check if file needs processing
CREATE OR REPLACE FUNCTION public.needs_property_file_processing(
  p_filename text,
  p_file_hash text DEFAULT NULL
)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
  SELECT NOT EXISTS (
    SELECT 1 
    FROM public.property_sync_log 
    WHERE filename = p_filename 
    AND (p_file_hash IS NULL OR file_hash = p_file_hash)
    AND status = 'completed'
  );
$$;

-- 5) MONITORING TABLE - Track sync health
CREATE TABLE IF NOT EXISTS public.property_sync_monitoring (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  check_time timestamp with time zone DEFAULT now(),
  sync_status text,
  files_behind integer DEFAULT 0,
  last_error text,
  alert_sent boolean DEFAULT false,
  metadata jsonb
);

-- 6) AUTOMATED CLEANUP - Remove old logs after 90 days
CREATE OR REPLACE FUNCTION public.cleanup_old_property_sync_logs()
RETURNS void
LANGUAGE sql
AS $$
  DELETE FROM public.property_sync_log 
  WHERE processed_at < CURRENT_DATE - INTERVAL '90 days';
  
  DELETE FROM public.property_sync_monitoring
  WHERE check_time < CURRENT_DATE - INTERVAL '30 days';
$$;

-- 7) RLS POLICIES
ALTER TABLE public.property_sync_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_sync_monitoring ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read sync logs
CREATE POLICY "Read sync logs" ON public.property_sync_log
  FOR SELECT TO authenticated
  USING (true);

CREATE POLICY "Read monitoring" ON public.property_sync_monitoring
  FOR SELECT TO authenticated
  USING (true);

-- 8) GRANTS for Edge Functions (service role bypasses RLS)
GRANT ALL ON public.property_sync_log TO service_role;
GRANT ALL ON public.property_sync_monitoring TO service_role;
GRANT EXECUTE ON FUNCTION public.needs_property_file_processing TO service_role;
GRANT EXECUTE ON FUNCTION public.get_last_property_sync TO service_role;
GRANT EXECUTE ON FUNCTION public.cleanup_old_property_sync_logs TO service_role;

-- 9) Create scheduled job (using pg_cron if available)
-- Note: This requires pg_cron extension to be enabled in Supabase
-- Uncomment if pg_cron is available:
/*
SELECT cron.schedule(
  'property-appraiser-daily-sync',
  '0 2 * * *', -- Run at 2 AM EST daily
  $$
    SELECT net.http_post(
      url := 'https://pmispwtdngkcmsrsjwbp.supabase.co/functions/v1/property-appraiser-sync',
      headers := jsonb_build_object(
        'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key'),
        'Content-Type', 'application/json'
      ),
      body := jsonb_build_object('trigger', 'scheduled')
    );
  $$
);

-- Cleanup job - runs weekly
SELECT cron.schedule(
  'property-sync-cleanup',
  '0 3 * * 0', -- Run at 3 AM EST on Sundays
  'SELECT public.cleanup_old_property_sync_logs();'
);
*/

-- 10) Initial test data (optional)
INSERT INTO public.property_sync_log (filename, file_type, county_code, status, metadata)
VALUES 
  ('NAL16P202501.csv', 'NAL', '16', 'completed', '{"test": true}'::jsonb),
  ('NAP16P202501.csv', 'NAP', '16', 'completed', '{"test": true}'::jsonb)
ON CONFLICT DO NOTHING;

-- Verification
SELECT 'Property Appraiser Sync Schema deployed successfully!' as status;