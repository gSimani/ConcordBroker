-- ============================================================
-- RUN THIS SQL IN SUPABASE SQL EDITOR
-- Go to: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql/new
-- Copy all of this SQL and execute it
-- ============================================================

-- 1. Add sale_year column
ALTER TABLE public.florida_parcels 
ADD COLUMN IF NOT EXISTS sale_year integer;

-- 2. Create index on sale_year
CREATE INDEX IF NOT EXISTS idx_florida_parcels_sale_year 
ON public.florida_parcels(sale_year);

-- 3. Create index on county for faster grouping
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county 
ON public.florida_parcels(county);

-- 4. Create monitoring view
CREATE OR REPLACE VIEW public.florida_parcels_ingest_status
WITH (security_invoker=on) AS
SELECT
  county,
  COUNT(*) as total_rows,
  MAX(import_date) as last_insert_at
FROM public.florida_parcels
GROUP BY county
ORDER BY total_rows DESC;

-- 5. Grant permissions
GRANT SELECT ON public.florida_parcels_ingest_status TO anon, authenticated;

-- 6. Test the view
SELECT * FROM public.florida_parcels_ingest_status;

-- 7. Check total records
SELECT COUNT(*) as total_records FROM public.florida_parcels;

-- 8. Check if sale_year column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'florida_parcels' 
AND column_name = 'sale_year';