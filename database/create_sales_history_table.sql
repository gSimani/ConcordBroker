-- Create comprehensive property sales history table for Florida properties
-- This table will store complete historical sales data from SDF files

CREATE TABLE IF NOT EXISTS property_sales_history (
    id BIGSERIAL PRIMARY KEY,

    -- Property Identification
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,

    -- Sale Transaction Details
    sale_date DATE,
    sale_year INTEGER,
    sale_month INTEGER,
    sale_day INTEGER,
    sale_price NUMERIC(12, 2),

    -- Transaction Parties
    grantor VARCHAR(255),
    grantee VARCHAR(255),

    -- Document Information
    instrument_type VARCHAR(50),
    instrument_number VARCHAR(50),
    or_book VARCHAR(20),
    or_page VARCHAR(20),
    clerk_no VARCHAR(50),

    -- Sale Qualification
    sale_qualification VARCHAR(50),
    quality_code VARCHAR(10),
    vi_code VARCHAR(10),
    reason VARCHAR(255),

    -- Property Status at Sale
    vacant_improved VARCHAR(20),
    property_use VARCHAR(50),

    -- Additional Flags
    qualified_sale BOOLEAN DEFAULT FALSE,
    arms_length BOOLEAN DEFAULT FALSE,
    multi_parcel BOOLEAN DEFAULT FALSE,
    foreclosure BOOLEAN DEFAULT FALSE,
    rea_sale BOOLEAN DEFAULT FALSE,
    short_sale BOOLEAN DEFAULT FALSE,
    distressed_sale BOOLEAN DEFAULT FALSE,

    -- Metadata
    data_source VARCHAR(50) DEFAULT 'SDF',
    import_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for performance
    CONSTRAINT unique_sale UNIQUE (parcel_id, sale_date, sale_price, or_book, or_page)
);

-- Create indexes for performance
CREATE INDEX idx_sales_parcel_id ON property_sales_history(parcel_id);
CREATE INDEX idx_sales_county ON property_sales_history(county);
CREATE INDEX idx_sales_date ON property_sales_history(sale_date DESC);
CREATE INDEX idx_sales_price ON property_sales_history(sale_price);
CREATE INDEX idx_sales_year ON property_sales_history(sale_year DESC);
CREATE INDEX idx_sales_qualified ON property_sales_history(qualified_sale);
CREATE INDEX idx_sales_parcel_date ON property_sales_history(parcel_id, sale_date DESC);

-- Add comments
COMMENT ON TABLE property_sales_history IS 'Complete historical sales data for Florida properties from SDF files';
COMMENT ON COLUMN property_sales_history.parcel_id IS 'Property parcel identification number';
COMMENT ON COLUMN property_sales_history.sale_price IS 'Sale price in dollars';
COMMENT ON COLUMN property_sales_history.qualified_sale IS 'Whether this is a qualified arms-length sale';
COMMENT ON COLUMN property_sales_history.quality_code IS 'Florida DOR quality code (01-19)';