-- Add sale_year column to support year-only sales data
ALTER TABLE public.florida_parcels
  ADD COLUMN IF NOT EXISTS sale_year integer;

-- Index for analytics/filters on year
CREATE INDEX IF NOT EXISTS idx_florida_parcels_sale_year ON public.florida_parcels(sale_year);

-- Create monitoring view for upload progress
CREATE OR REPLACE VIEW public.florida_parcels_ingest_status WITH (security_invoker=on) AS 
SELECT 
  county, 
  COUNT(*) AS total,
  MAX(import_date) AS last_insert_at,
  COUNT(*) FILTER (WHERE just_value IS NOT NULL) AS has_values,
  COUNT(*) FILTER (WHERE owner_name IS NOT NULL) AS has_owner
FROM public.florida_parcels 
GROUP BY county
ORDER BY total DESC;