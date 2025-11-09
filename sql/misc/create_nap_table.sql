-- =====================================================
-- CREATE DEDICATED NAP (Name Address Property) TABLE
-- Optimized for Broward County 2025 Assessment Data
-- =====================================================

-- Drop table if exists (for clean re-creation)
DROP TABLE IF EXISTS broward_nap_2025;

-- Create NAP table with all fields from NAP CSV
CREATE TABLE broward_nap_2025 (
    -- Primary key and identification
    id BIGSERIAL PRIMARY KEY,
    
    -- Core NAP fields (directly from CSV)
    co_no TEXT,                     -- County Number (16)
    acct_id TEXT NOT NULL,          -- Account ID (Parcel ID) - primary identifier
    file_t TEXT,                    -- File Type (P = Property)
    asmnt_yr INTEGER,               -- Assessment Year (2025)
    tax_auth_cd TEXT,               -- Tax Authority Code
    naics_cd TEXT,                  -- NAICS Code
    
    -- Valuation fields (key for property analysis)
    jv_f_f_e DECIMAL(15,2),         -- Just Value
    jv_lese_imp DECIMAL(15,2),      -- Just Value Leasehold Improvement  
    jv_total DECIMAL(15,2),         -- Total Just Value
    av_total DECIMAL(15,2),         -- Total Assessed Value
    jv_pol_contrl DECIMAL(15,2),    -- Just Value Policy Control
    av_pol_contrl DECIMAL(15,2),    -- Assessed Value Policy Control
    exmpt_val DECIMAL(15,2),        -- Exempt Value
    tax_val DECIMAL(15,2),          -- Taxable Value
    pen_rate DECIMAL(8,4),          -- Penalty Rate
    
    -- Owner information
    own_nam TEXT,                   -- Owner Name
    own_addr TEXT,                  -- Owner Address
    own_city TEXT,                  -- Owner City
    own_state TEXT,                 -- Owner State
    own_zipcd TEXT,                 -- Owner Zip Code
    own_state_dom TEXT,             -- Owner State Domicile
    
    -- Fiduciary information
    fidu_name TEXT,                 -- Fiduciary Name
    fidu_addr TEXT,                 -- Fiduciary Address
    fidu_city TEXT,                 -- Fiduciary City
    fidu_state TEXT,                -- Fiduciary State
    fidu_zipcd TEXT,                -- Fiduciary Zip
    fidu_cd TEXT,                   -- Fiduciary Code
    
    -- Physical property location
    phy_addr TEXT,                  -- Physical Address
    phy_city TEXT,                  -- Physical City
    phy_zipcd TEXT,                 -- Physical Zip Code
    
    -- Additional identifiers and codes
    fil TEXT,                       -- File Indicator
    alt_key TEXT,                   -- Alternate Key
    exmpt TEXT,                     -- Exemption Code
    acct_id_cng TEXT,               -- Account ID Change
    seq_no INTEGER,                 -- Sequence Number
    ts_id TEXT,                     -- Timestamp ID
    
    -- Metadata for tracking
    county TEXT DEFAULT 'BROWARD',
    data_source TEXT DEFAULT 'NAP_2025',
    import_date TIMESTAMP DEFAULT NOW(),
    update_date TIMESTAMP DEFAULT NOW(),
    
    -- Data integrity hash (for change detection)
    data_hash TEXT
);

-- =====================================================
-- PRIMARY INDEXES FOR FAST WEBSITE QUERIES
-- =====================================================

-- 1. Primary parcel lookup (most common)
CREATE INDEX idx_nap_acct_id ON broward_nap_2025 (acct_id);

-- 2. Owner name search (GIN index for full-text search)
CREATE INDEX idx_nap_owner_name ON broward_nap_2025 USING gin (to_tsvector('english', own_nam));

-- 3. Physical address search
CREATE INDEX idx_nap_phy_addr ON broward_nap_2025 USING gin (to_tsvector('english', phy_addr));

-- 4. Physical city (for location filtering)
CREATE INDEX idx_nap_phy_city ON broward_nap_2025 (phy_city);

-- 5. Physical zip (for area analysis)
CREATE INDEX idx_nap_phy_zipcd ON broward_nap_2025 (phy_zipcd);

-- =====================================================
-- VALUATION INDEXES FOR MARKET ANALYSIS
-- =====================================================

-- 6. Just value (market value queries)
CREATE INDEX idx_nap_jv_total ON broward_nap_2025 (jv_total DESC NULLS LAST);

-- 7. Assessed value 
CREATE INDEX idx_nap_av_total ON broward_nap_2025 (av_total DESC NULLS LAST);

-- 8. Taxable value (most important for tax analysis)
CREATE INDEX idx_nap_tax_val ON broward_nap_2025 (tax_val DESC NULLS LAST);

-- =====================================================
-- COMPOSITE INDEXES FOR COMMON QUERY PATTERNS
-- =====================================================

-- 9. City + Value range (neighborhood analysis)
CREATE INDEX idx_nap_city_value ON broward_nap_2025 (phy_city, jv_total DESC NULLS LAST);

-- 10. Owner + City (portfolio analysis)
CREATE INDEX idx_nap_owner_city ON broward_nap_2025 (own_nam, phy_city);

-- 11. Zip + Value (area value analysis)
CREATE INDEX idx_nap_zip_value ON broward_nap_2025 (phy_zipcd, tax_val DESC NULLS LAST);

-- 12. Tax Authority + Year (jurisdiction analysis)
CREATE INDEX idx_nap_tax_auth_year ON broward_nap_2025 (tax_auth_cd, asmnt_yr);

-- =====================================================
-- DATA QUALITY CONSTRAINTS
-- =====================================================

-- Ensure account ID is not empty
ALTER TABLE broward_nap_2025 ADD CONSTRAINT check_acct_id_not_empty 
    CHECK (acct_id IS NOT NULL AND LENGTH(TRIM(acct_id)) > 0);

-- Ensure assessment year is reasonable
ALTER TABLE broward_nap_2025 ADD CONSTRAINT check_asmnt_yr_valid 
    CHECK (asmnt_yr IS NULL OR (asmnt_yr >= 2020 AND asmnt_yr <= 2030));

-- Ensure valuation fields are non-negative
ALTER TABLE broward_nap_2025 ADD CONSTRAINT check_values_non_negative 
    CHECK (jv_total IS NULL OR jv_total >= 0);

-- =====================================================
-- PERFORMANCE OPTIMIZATION SETTINGS
-- =====================================================

-- Update table statistics for query optimizer
ANALYZE broward_nap_2025;

-- Enable parallel queries for large operations
ALTER TABLE broward_nap_2025 SET (parallel_workers = 4);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) SETUP
-- =====================================================

-- Enable RLS (can be disabled if not needed)
ALTER TABLE broward_nap_2025 ENABLE ROW LEVEL SECURITY;

-- Create policy for public read access (adjust as needed)
CREATE POLICY "Allow public read access" ON broward_nap_2025
    FOR SELECT USING (true);

-- Create policy for service role full access
CREATE POLICY "Allow service role full access" ON broward_nap_2025
    FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE broward_nap_2025 IS 'Broward County NAP (Name Address Property) data for 2025 assessments - contains official property valuation and ownership information';

COMMENT ON COLUMN broward_nap_2025.acct_id IS 'Primary parcel identifier from Broward County assessor';
COMMENT ON COLUMN broward_nap_2025.jv_total IS 'Total Just Value - market value assessment';
COMMENT ON COLUMN broward_nap_2025.av_total IS 'Total Assessed Value - value for tax purposes';
COMMENT ON COLUMN broward_nap_2025.tax_val IS 'Taxable Value - actual value subject to taxation';
COMMENT ON COLUMN broward_nap_2025.own_nam IS 'Legal owner name from county records';
COMMENT ON COLUMN broward_nap_2025.phy_addr IS 'Physical property address';

-- =====================================================
-- VERIFICATION QUERY
-- =====================================================

-- Query to verify table creation
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'broward_nap_2025'
ORDER BY ordinal_position;