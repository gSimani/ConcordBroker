
-- SDF (Sales Data File) Table
CREATE TABLE IF NOT EXISTS sdf_sales (
    id BIGSERIAL PRIMARY KEY,
    parcel_id TEXT NOT NULL,
    county TEXT NOT NULL,
    year INTEGER NOT NULL,

    -- Sale information
    sale_date DATE,
    sale_price BIGINT,
    sale_year INTEGER,
    sale_month INTEGER,

    -- Sale details
    sale_type TEXT,
    sale_qualification TEXT,
    deed_type TEXT,
    verified_sale BOOLEAN,

    -- Parties
    grantor_name TEXT,
    grantee_name TEXT,

    -- Recording info
    book_page TEXT,
    instrument_number TEXT,
    or_book TEXT,
    or_page TEXT,
    clerk_number TEXT,

    -- Multi-parcel sale
    multi_parcel_sale BOOLEAN,
    parcel_count INTEGER,

    -- Vacancy
    vacant_at_sale BOOLEAN,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(parcel_id, county, year, sale_date)
);

CREATE INDEX idx_sdf_parcel_county_year ON sdf_sales(parcel_id, county, year);
CREATE INDEX idx_sdf_county_year ON sdf_sales(county, year);
CREATE INDEX idx_sdf_sale_date ON sdf_sales(sale_date);
CREATE INDEX idx_sdf_sale_price ON sdf_sales(sale_price);
