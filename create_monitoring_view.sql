-- Create monitoring view for upload progress
-- This view shows county-level statistics for monitoring the data upload

-- Drop if exists to recreate with latest definition
DROP VIEW IF EXISTS public.florida_parcels_ingest_status CASCADE;

-- Create the monitoring view with security invoker
CREATE OR REPLACE VIEW public.florida_parcels_ingest_status WITH (security_invoker=on) AS 
SELECT 
  county,
  COUNT(*) AS total,
  MAX(import_date) AS last_insert_at,
  COUNT(*) FILTER (WHERE just_value IS NOT NULL) AS has_values,
  COUNT(*) FILTER (WHERE owner_name IS NOT NULL) AS has_owner,
  COUNT(*) FILTER (WHERE sale_price IS NOT NULL) AS has_sales,
  AVG(just_value) FILTER (WHERE just_value > 0) AS avg_value,
  MIN(import_date) AS first_insert_at
FROM public.florida_parcels 
GROUP BY county
ORDER BY total DESC;

-- Grant read access to the view
GRANT SELECT ON public.florida_parcels_ingest_status TO anon, authenticated;

-- Create index on import_date for faster monitoring queries
CREATE INDEX IF NOT EXISTS idx_florida_parcels_import_date 
ON public.florida_parcels(import_date DESC);

-- Create composite index for county + import_date
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_import 
ON public.florida_parcels(county, import_date DESC);

-- Fix for varchar(2) state column issues
-- Alter columns to allow longer state codes if needed
DO $$ 
BEGIN
    -- Check if columns need resizing
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'florida_parcels' 
        AND column_name = 'owner_state' 
        AND character_maximum_length = 2
    ) THEN
        -- Optionally expand to varchar(10) to handle edge cases
        -- ALTER TABLE public.florida_parcels 
        -- ALTER COLUMN owner_state TYPE varchar(10);
        
        -- ALTER TABLE public.florida_parcels 
        -- ALTER COLUMN phy_state TYPE varchar(10);
        
        -- For now, just note the issue
        RAISE NOTICE 'State columns are varchar(2) - data will be truncated';
    END IF;
END $$;

-- Create function to get upload statistics
CREATE OR REPLACE FUNCTION get_upload_stats()
RETURNS TABLE (
    total_counties bigint,
    total_records bigint,
    counties_with_data bigint,
    last_upload timestamp with time zone,
    avg_records_per_county numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT county)::bigint as total_counties,
        COUNT(*)::bigint as total_records,
        COUNT(DISTINCT county) FILTER (WHERE import_date IS NOT NULL)::bigint as counties_with_data,
        MAX(import_date) as last_upload,
        ROUND(AVG(county_totals.total)::numeric, 0) as avg_records_per_county
    FROM public.florida_parcels
    LEFT JOIN (
        SELECT county, COUNT(*) as total 
        FROM public.florida_parcels 
        GROUP BY county
    ) county_totals ON true;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION get_upload_stats() TO anon, authenticated;