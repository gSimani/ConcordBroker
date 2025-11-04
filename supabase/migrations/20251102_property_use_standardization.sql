-- Property Use Standardization - Task 6: Text Label Mapping
-- Maps text labels (SFR, CONDO, etc.) to standard DOR codes via crosswalk
-- Expected impact: ~2.2M records across 8 counties
-- Target coverage: 79-80% of all 2025 records

-- Task 6: Map text labels to standard codes
UPDATE public.florida_parcels fp
SET property_use_std = xw.code
FROM public.property_use_crosswalk xw
WHERE fp.year = 2025
  AND fp.property_use_std IS NULL
  AND normalize_use_label(fp.property_use) = xw.normalized_label;

-- Verification Query 1: Overall Coverage Statistics
SELECT
  'OVERALL COVERAGE' AS checkpoint,
  COUNT(*) AS total_records,
  COUNT(*) FILTER (WHERE property_use_std IS NOT NULL) AS standardized,
  COUNT(*) FILTER (WHERE property_use_std IS NULL AND property_use IS NOT NULL) AS unmapped,
  ROUND(100.0 * COUNT(*) FILTER (WHERE property_use_std IS NOT NULL) / COUNT(*), 2) AS pct_standardized
FROM public.florida_parcels
WHERE year = 2025;

-- Verification Query 2: Top 10 Mapped Text Labels
SELECT
  fp.property_use AS original_label,
  fp.property_use_std AS mapped_code,
  d.label AS code_description,
  COUNT(*) AS record_count
FROM public.florida_parcels fp
JOIN public.dor_use_codes d ON d.code = fp.property_use_std
WHERE fp.year = 2025
  AND fp.property_use !~ '^[0-9]{3}'
GROUP BY fp.property_use, fp.property_use_std, d.label
ORDER BY record_count DESC
LIMIT 10;

-- Verification Query 3: Unmapped Labels Report (Task 7)
SELECT
  'UNMAPPED LABELS' AS checkpoint,
  fp.property_use AS unmapped_label,
  fp.county,
  COUNT(*) AS record_count
FROM public.florida_parcels fp
WHERE fp.year = 2025
  AND fp.property_use_std IS NULL
  AND fp.property_use IS NOT NULL
  AND fp.property_use !~ '^[0-9]{3}'
GROUP BY fp.property_use, fp.county
ORDER BY record_count DESC
LIMIT 20;

-- Verification Query 4: Coverage by County
SELECT
  county,
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE property_use_std IS NOT NULL) AS standardized,
  ROUND(100.0 * COUNT(*) FILTER (WHERE property_use_std IS NOT NULL) / COUNT(*), 2) AS pct_standardized
FROM public.florida_parcels
WHERE year = 2025
GROUP BY county
ORDER BY total DESC
LIMIT 10;
