-- IMPORTANT: Run this SQL directly in Supabase SQL Editor
-- Go to: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql/new

-- Step 1: Add sale_year column if it doesn't exist
ALTER TABLE public.florida_parcels
  ADD COLUMN IF NOT EXISTS sale_year integer;

-- Step 2: Create index on sale_year
CREATE INDEX IF NOT EXISTS idx_florida_parcels_sale_year
  ON public.florida_parcels(sale_year);

-- Step 3: Create monitoring view (simple version without timestamp assumptions)
DROP VIEW IF EXISTS public.florida_parcels_ingest_status CASCADE;

CREATE OR REPLACE VIEW public.florida_parcels_ingest_status 
WITH (security_invoker=on) AS
SELECT
  county,
  COUNT(*) AS total_rows,
  MAX(sale_year) AS latest_sale_year,
  COUNT(*) FILTER (WHERE just_value IS NOT NULL) AS has_values,
  COUNT(*) FILTER (WHERE owner_name IS NOT NULL) AS has_owner
FROM public.florida_parcels
GROUP BY county
ORDER BY total_rows DESC;

-- Step 4: Grant permissions
GRANT SELECT ON public.florida_parcels_ingest_status TO anon, authenticated;

-- Step 5: Create summary function
CREATE OR REPLACE FUNCTION get_upload_summary()
RETURNS TABLE (
    total_counties bigint,
    total_records bigint,
    counties_loaded text[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT county)::bigint as total_counties,
        COUNT(*)::bigint as total_records,
        ARRAY_AGG(DISTINCT county ORDER BY county) as counties_loaded
    FROM public.florida_parcels;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION get_upload_summary() TO anon, authenticated;

-- Step 6: Verify everything works
SELECT * FROM public.florida_parcels_ingest_status;
SELECT * FROM get_upload_summary();