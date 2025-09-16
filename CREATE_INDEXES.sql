-- Create indexes for florida_parcels performance
-- Run this in Supabase SQL Editor before bulk upload

-- Ensure upserts work: make the natural key unique for PostgREST
CREATE UNIQUE INDEX IF NOT EXISTS uq_florida_parcels_key
  ON public.florida_parcels (parcel_id, county, year);

-- Helpful filters during load/queries
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_year
  ON public.florida_parcels (county, year);
  
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name
  ON public.florida_parcels (owner_name);

-- Verify indexes were created
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'florida_parcels'
ORDER BY indexname;