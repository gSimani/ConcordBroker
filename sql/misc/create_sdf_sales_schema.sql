-- SDF Sales Data Schema for Broward County
-- This schema is optimized for fast queries and prevents duplicates

DROP TABLE IF EXISTS property_sales_history CASCADE;

CREATE TABLE property_sales_history (
    id BIGSERIAL PRIMARY KEY,
    
    -- Core identifiers
    county_no VARCHAR(10) NOT NULL,
    parcel_id VARCHAR(50) NOT NULL,
    state_parcel_id VARCHAR(50),
    
    -- Assessment data
    assessment_year INTEGER,
    atv_start INTEGER,
    group_no VARCHAR(10),
    dor_use_code VARCHAR(10),
    neighborhood_code VARCHAR(20),
    market_area VARCHAR(10),
    census_block VARCHAR(20),
    
    -- Sale identification
    sale_id_code VARCHAR(50),
    sale_change_code VARCHAR(10),
    verification_code VARCHAR(10),
    
    -- Official records
    or_book VARCHAR(20),
    or_page VARCHAR(20),
    clerk_no VARCHAR(50),
    
    -- Sale details
    quality_code VARCHAR(10),
    sale_year INTEGER NOT NULL,
    sale_month INTEGER NOT NULL,
    sale_price BIGINT,
    multi_parcel_sale VARCHAR(10),
    
    -- Additional identifiers
    rs_id VARCHAR(50),
    mp_id VARCHAR(50),
    
    -- Computed fields for better querying
    sale_date DATE GENERATED ALWAYS AS (
        CASE 
            WHEN sale_year IS NOT NULL AND sale_month IS NOT NULL 
            THEN make_date(sale_year, sale_month, 1)
            ELSE NULL
        END
    ) STORED,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for fast queries
CREATE INDEX idx_property_sales_parcel_id ON property_sales_history(parcel_id);
CREATE INDEX idx_property_sales_state_parcel_id ON property_sales_history(state_parcel_id);
CREATE INDEX idx_property_sales_date ON property_sales_history(sale_date DESC);
CREATE INDEX idx_property_sales_year_month ON property_sales_history(sale_year DESC, sale_month DESC);
CREATE INDEX idx_property_sales_price ON property_sales_history(sale_price DESC);
CREATE INDEX idx_property_sales_quality ON property_sales_history(quality_code);

-- Composite index for common queries
CREATE INDEX idx_property_sales_parcel_date ON property_sales_history(parcel_id, sale_date DESC);
CREATE INDEX idx_property_sales_parcel_price ON property_sales_history(parcel_id, sale_price DESC);

-- Unique constraint to prevent duplicate sales records
CREATE UNIQUE INDEX idx_property_sales_unique ON property_sales_history(
    parcel_id, sale_year, sale_month, sale_price, or_book, or_page
) WHERE or_book IS NOT NULL AND or_page IS NOT NULL;

-- Alternative unique constraint for records without official records
CREATE UNIQUE INDEX idx_property_sales_unique_no_or ON property_sales_history(
    parcel_id, sale_year, sale_month, sale_price, clerk_no
) WHERE (or_book IS NULL OR or_page IS NULL) AND clerk_no IS NOT NULL;

-- Add comments for documentation
COMMENT ON TABLE property_sales_history IS 'Sales history data from Florida SDF files';
COMMENT ON COLUMN property_sales_history.parcel_id IS 'Property parcel identifier from tax assessor';
COMMENT ON COLUMN property_sales_history.sale_price IS 'Sale price in cents to avoid decimal issues';
COMMENT ON COLUMN property_sales_history.sale_date IS 'Computed sale date from year and month';
COMMENT ON COLUMN property_sales_history.quality_code IS 'Sale quality code indicating validity';

-- Row Level Security (disable for bulk import, can enable later)
-- ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;