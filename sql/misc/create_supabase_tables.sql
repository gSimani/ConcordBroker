-- DOR Properties Table
CREATE TABLE IF NOT EXISTS dor_properties (
    id BIGSERIAL PRIMARY KEY,
    folio VARCHAR(30) UNIQUE NOT NULL,
    county VARCHAR(50),
    year INTEGER,
    
    -- Owner Information
    owner_name TEXT,
    
    -- Mailing Address
    mail_address_1 TEXT,
    mail_address_2 TEXT,
    mail_city VARCHAR(100),
    mail_state VARCHAR(2),
    mail_zip VARCHAR(10),
    
    -- Property Address
    situs_address_1 TEXT,
    situs_address_2 TEXT,
    situs_city VARCHAR(100),
    situs_zip VARCHAR(10),
    
    -- Property Details
    use_code VARCHAR(10),
    subdivision TEXT,
    
    -- Physical Characteristics
    living_area_sf NUMERIC,
    year_built INTEGER,
    bedrooms INTEGER,
    bathrooms NUMERIC(4,2),
    pool BOOLEAN DEFAULT FALSE,
    
    -- Values
    land_value NUMERIC(15,2),
    building_value NUMERIC(15,2),
    just_value NUMERIC(15,2),
    taxable_value NUMERIC(15,2),
    
    -- Metadata
    source_file VARCHAR(255),
    load_timestamp TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- DOR Sales Table
CREATE TABLE IF NOT EXISTS dor_sales (
    id BIGSERIAL PRIMARY KEY,
    folio VARCHAR(30),
    county VARCHAR(50),
    
    -- Sale Information
    sale_date DATE,
    sale_price NUMERIC(15,2),
    sale_type VARCHAR(50),
    
    -- Parties
    grantor TEXT,
    grantee TEXT,
    
    -- Recording Info
    deed_type VARCHAR(50),
    instrument_number VARCHAR(50),
    
    -- Metadata
    source_file VARCHAR(255),
    load_timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_dor_properties_folio ON dor_properties(folio);
CREATE INDEX IF NOT EXISTS idx_dor_properties_owner ON dor_properties(LOWER(owner_name));
CREATE INDEX IF NOT EXISTS idx_dor_properties_city ON dor_properties(situs_city);
CREATE INDEX IF NOT EXISTS idx_dor_properties_value ON dor_properties(just_value DESC);

CREATE INDEX IF NOT EXISTS idx_dor_sales_folio ON dor_sales(folio);
CREATE INDEX IF NOT EXISTS idx_dor_sales_date ON dor_sales(sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_dor_sales_price ON dor_sales(sale_price DESC);

-- Grant permissions for Row Level Security
ALTER TABLE dor_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE dor_sales ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access
CREATE POLICY "Public read access" ON dor_properties FOR SELECT USING (true);
CREATE POLICY "Public read access" ON dor_sales FOR SELECT USING (true);