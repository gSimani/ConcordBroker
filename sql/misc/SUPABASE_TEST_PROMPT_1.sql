-- ============================================================
-- TEST PROMPT 1: Current DOR Use Code Coverage Analysis
-- Copy this into Supabase SQL Editor and execute
-- This will show the current state before any assignments
-- ============================================================

SELECT
    -- Overall statistics
    COUNT(*) as total_properties,
    COUNT(CASE WHEN dor_uc IS NOT NULL AND dor_uc != '' THEN 1 END) as properties_with_code,
    COUNT(CASE WHEN dor_uc IS NULL OR dor_uc = '' THEN 1 END) as properties_without_code,
    ROUND(COUNT(CASE WHEN dor_uc IS NOT NULL AND dor_uc != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_percentage,

    -- Sample of codes present
    COUNT(DISTINCT dor_uc) as unique_codes_found,

    -- Property use data
    COUNT(CASE WHEN property_use IS NOT NULL AND property_use != '' THEN 1 END) as properties_with_use_description,
    COUNT(CASE WHEN property_use_category IS NOT NULL AND property_use_category != '' THEN 1 END) as properties_with_category

FROM florida_parcels
WHERE year = 2025;