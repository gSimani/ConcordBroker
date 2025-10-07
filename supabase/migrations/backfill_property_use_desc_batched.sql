-- Backfill property_use_desc in batches by county to avoid timeout
-- This approach processes one county at a time to stay under timeout limits

-- Batch 1: ALACHUA
UPDATE florida_parcels fp
SET property_use_desc = COALESCE(
  (SELECT duc.description
   FROM dor_code_mappings_std dcm
   JOIN dor_use_codes_std duc ON dcm.standard_full_code = duc.full_code
   WHERE dcm.legacy_code = fp.property_use::text
   AND (dcm.county IS NULL OR dcm.county = fp.county)
   LIMIT 1),
  CASE
    WHEN fp.property_use::int BETWEEN 0 AND 9 THEN 'Residential Property'
    WHEN fp.property_use::int BETWEEN 10 AND 39 THEN 'Commercial Property'
    WHEN fp.property_use::int BETWEEN 40 AND 49 THEN 'Industrial Property'
    WHEN fp.property_use::int BETWEEN 50 AND 69 THEN 'Agricultural Property'
    WHEN fp.property_use::int BETWEEN 70 AND 79 THEN 'Institutional Property'
    WHEN fp.property_use::int BETWEEN 80 AND 89 THEN 'Government Property'
    WHEN fp.property_use::int BETWEEN 90 AND 99 THEN 'Vacant Land'
    ELSE 'Unknown Property Type'
  END
)
WHERE fp.county = 'ALACHUA'
AND fp.property_use IS NOT NULL
AND (fp.property_use_desc IS NULL OR fp.property_use_desc = '');

-- Batch 2: BAKER
UPDATE florida_parcels fp
SET property_use_desc = COALESCE(
  (SELECT duc.description
   FROM dor_code_mappings_std dcm
   JOIN dor_use_codes_std duc ON dcm.standard_full_code = duc.full_code
   WHERE dcm.legacy_code = fp.property_use::text
   AND (dcm.county IS NULL OR dcm.county = fp.county)
   LIMIT 1),
  CASE
    WHEN fp.property_use::int BETWEEN 0 AND 9 THEN 'Residential Property'
    WHEN fp.property_use::int BETWEEN 10 AND 39 THEN 'Commercial Property'
    WHEN fp.property_use::int BETWEEN 40 AND 49 THEN 'Industrial Property'
    WHEN fp.property_use::int BETWEEN 50 AND 69 THEN 'Agricultural Property'
    WHEN fp.property_use::int BETWEEN 70 AND 79 THEN 'Institutional Property'
    WHEN fp.property_use::int BETWEEN 80 AND 89 THEN 'Government Property'
    WHEN fp.property_use::int BETWEEN 90 AND 99 THEN 'Vacant Land'
    ELSE 'Unknown Property Type'
  END
)
WHERE fp.county = 'BAKER'
AND fp.property_use IS NOT NULL
AND (fp.property_use_desc IS NULL OR fp.property_use_desc = '');

-- Continue for remaining counties...
-- Note: This file shows the pattern. Execute one county at a time to avoid timeout.
