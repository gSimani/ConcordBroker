-- Performance indexes for DOR code lookup tables
-- These optimize the backfill UPDATE operation on florida_parcels

-- Index on dor_code_mappings_std for fast legacy code lookups
CREATE INDEX IF NOT EXISTS idx_dor_mappings_legacy_code
ON dor_code_mappings_std(legacy_code);

CREATE INDEX IF NOT EXISTS idx_dor_mappings_county
ON dor_code_mappings_std(county);

CREATE INDEX IF NOT EXISTS idx_dor_mappings_legacy_county
ON dor_code_mappings_std(legacy_code, county);

-- Index on dor_use_codes_std for fast full_code lookups
CREATE INDEX IF NOT EXISTS idx_dor_codes_full_code
ON dor_use_codes_std(full_code);

-- Index on florida_parcels.property_use to speed up the UPDATE WHERE clause
CREATE INDEX IF NOT EXISTS idx_florida_parcels_property_use
ON florida_parcels(property_use) WHERE property_use IS NOT NULL;

-- Analyze tables to update statistics for query planner
ANALYZE dor_code_mappings_std;
ANALYZE dor_use_codes_std;
ANALYZE florida_parcels;
