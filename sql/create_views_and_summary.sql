-- Create a current-views layer and a materialized sales summary
-- Run in Supabase SQL Editor

-- 1) Latest parcel snapshot per (parcel_id, county)
CREATE OR REPLACE VIEW public.florida_parcels_latest AS
SELECT fp.*
FROM public.florida_parcels fp
JOIN (
  SELECT parcel_id, county, MAX(year) AS max_year
  FROM public.florida_parcels
  GROUP BY parcel_id, county
) m
  ON m.parcel_id = fp.parcel_id
 AND m.county    = fp.county
 AND m.max_year  = fp.year;

-- Helpful index for consumers of the view (on base table)
CREATE INDEX IF NOT EXISTS idx_fp_latest_year ON public.florida_parcels(parcel_id, county, year);

-- 2) Materialized view summarizing sales per parcel
--    Provides total_sales, last_sale_date, last_sale_price for each (parcel_id, county)
DROP MATERIALIZED VIEW IF EXISTS public.parcel_sales_summary;
CREATE MATERIALIZED VIEW public.parcel_sales_summary AS
WITH ranked AS (
  SELECT
    psh.parcel_id,
    psh.county,
    psh.sale_date,
    psh.sale_price,
    ROW_NUMBER() OVER (
      PARTITION BY psh.parcel_id, psh.county
      ORDER BY psh.sale_date DESC, psh.sale_price DESC NULLS LAST
    ) AS rn,
    COUNT(*) OVER (
      PARTITION BY psh.parcel_id, psh.county
    ) AS total_sales
  FROM public.property_sales_history psh
)
SELECT
  parcel_id,
  county,
  total_sales,
  sale_date  AS last_sale_date,
  sale_price AS last_sale_price
FROM ranked
WHERE rn = 1;

-- Unique index to allow CONCURRENT REFRESH and fast lookups
CREATE UNIQUE INDEX IF NOT EXISTS uk_parcel_sales_summary
  ON public.parcel_sales_summary(parcel_id, county);

CREATE INDEX IF NOT EXISTS idx_parcel_sales_summary_last_date
  ON public.parcel_sales_summary(last_sale_date DESC);

-- 3) Helper function to refresh concurrently
CREATE OR REPLACE FUNCTION public.refresh_parcel_sales_summary()
RETURNS void
LANGUAGE sql
AS $$
  REFRESH MATERIALIZED VIEW CONCURRENTLY public.parcel_sales_summary;
$$;

