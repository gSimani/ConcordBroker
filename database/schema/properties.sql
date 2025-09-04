-- Main Properties Table (Core NAL Data)
CREATE TABLE IF NOT EXISTS properties (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(30) UNIQUE NOT NULL,
    
    -- Address (Primary Organization)
    phy_addr1 VARCHAR(255),
    phy_addr2 VARCHAR(255),
    phy_city VARCHAR(100),
    phy_zipcd VARCHAR(10),
    address_full TEXT GENERATED ALWAYS AS (
        COALESCE(phy_addr1, '') || ' ' || 
        COALESCE(phy_city, '') || ', FL ' || 
        COALESCE(phy_zipcd, '')
    ) STORED,
    
    -- Property Classification
    dor_uc VARCHAR(4),
    property_type VARCHAR(50), -- Residential, Commercial, Industrial, etc.
    property_subtype VARCHAR(50), -- Single Family, Retail, Warehouse, etc.
    
    -- Core Values
    jv DECIMAL(15,2), -- Just/Market Value
    av_sd DECIMAL(15,2), -- Assessed Value School
    tv_sd DECIMAL(15,2), -- Taxable Value School
    av_nsd DECIMAL(15,2), -- Assessed Value Non-School
    tv_nsd DECIMAL(15,2), -- Taxable Value Non-School
    lnd_val DECIMAL(15,2), -- Land Value
    
    -- Owner Information
    own_name VARCHAR(255),
    own_addr1 VARCHAR(255),
    own_addr2 VARCHAR(255),
    own_city VARCHAR(100),
    own_state VARCHAR(50),
    own_zipcd VARCHAR(10),
    
    -- Physical Characteristics
    lnd_sqfoot BIGINT,
    tot_lvg_area INTEGER,
    act_yr_blt INTEGER,
    eff_yr_blt INTEGER,
    no_buldng INTEGER,
    no_res_unts INTEGER,
    
    -- Geographic/Legal
    section_num INTEGER,
    township VARCHAR(10),
    range VARCHAR(10),
    census_block VARCHAR(20),
    nbrhd_cd VARCHAR(10),
    
    -- Metadata
    co_no INTEGER DEFAULT 16, -- Broward County
    asmnt_yr INTEGER,
    file_t CHAR(1) DEFAULT 'R',
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for search
    CONSTRAINT idx_address_search 
        CHECK (phy_addr1 IS NOT NULL OR parcel_id IS NOT NULL)
);

-- Indexes for fast searching
CREATE INDEX idx_properties_address ON properties(phy_addr1, phy_city);
CREATE INDEX idx_properties_city ON properties(phy_city);
CREATE INDEX idx_properties_zip ON properties(phy_zipcd);
CREATE INDEX idx_properties_owner ON properties(LOWER(own_name));
CREATE INDEX idx_properties_value ON properties(jv DESC);
CREATE INDEX idx_properties_type ON properties(property_type, property_subtype);
CREATE INDEX idx_properties_year ON properties(act_yr_blt);

-- Full-text search index
CREATE INDEX idx_properties_search ON properties USING GIN(
    to_tsvector('english', 
        COALESCE(phy_addr1, '') || ' ' ||
        COALESCE(phy_city, '') || ' ' ||
        COALESCE(own_name, '')
    )
);

-- Sales History Table
CREATE TABLE IF NOT EXISTS property_sales (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT REFERENCES properties(id) ON DELETE CASCADE,
    parcel_id VARCHAR(30),
    
    sale_date DATE,
    sale_price DECIMAL(15,2),
    sale_type VARCHAR(50),
    qual_cd VARCHAR(2), -- Q=Qualified, U=Unqualified
    vi_cd VARCHAR(2), -- Validity Indicator
    
    grantor VARCHAR(255), -- Seller
    grantee VARCHAR(255), -- Buyer
    
    or_book VARCHAR(10),
    or_page VARCHAR(10),
    clerk_no VARCHAR(20),
    
    multi_parcel_sale BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT idx_sale_property FOREIGN KEY (parcel_id) 
        REFERENCES properties(parcel_id)
);

CREATE INDEX idx_sales_property ON property_sales(property_id);
CREATE INDEX idx_sales_date ON property_sales(sale_date DESC);
CREATE INDEX idx_sales_price ON property_sales(sale_price DESC);

-- Property Details (Type-Specific)
CREATE TABLE IF NOT EXISTS property_details (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT REFERENCES properties(id) ON DELETE CASCADE,
    
    -- Residential Details
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    garage_spaces INTEGER,
    pool VARCHAR(20), -- none, private, community
    stories INTEGER,
    
    -- Commercial Details
    rentable_area INTEGER,
    tenant_count INTEGER,
    occupancy_rate DECIMAL(5,2),
    avg_lease_rate DECIMAL(10,2),
    parking_spaces INTEGER,
    parking_ratio VARCHAR(20),
    
    -- Industrial Details
    warehouse_space INTEGER,
    office_space INTEGER,
    clear_height INTEGER,
    loading_docks INTEGER,
    power_capacity INTEGER,
    rail_access BOOLEAN,
    
    -- Agricultural Details
    tillable_acres DECIMAL(10,2),
    pasture_acres DECIMAL(10,2),
    crop_type VARCHAR(100),
    irrigation VARCHAR(50),
    
    -- Vacant Land Details
    zoning VARCHAR(50),
    future_land_use VARCHAR(50),
    max_density VARCHAR(50),
    utilities_available BOOLEAN,
    
    -- Custom JSON for additional fields
    custom_fields JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_details_property ON property_details(property_id);

-- Property Notes & Timeline
CREATE TABLE IF NOT EXISTS property_notes (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT REFERENCES properties(id) ON DELETE CASCADE,
    
    note_text TEXT NOT NULL,
    priority VARCHAR(10) DEFAULT 'low', -- low, medium, high
    status VARCHAR(20) DEFAULT 'open', -- open, completed, archived
    
    author_id VARCHAR(100),
    author_name VARCHAR(100),
    
    due_date DATE,
    completed_at TIMESTAMP,
    
    attachments JSONB, -- Array of attachment URLs/IDs
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notes_property ON property_notes(property_id);
CREATE INDEX idx_notes_priority ON property_notes(priority);
CREATE INDEX idx_notes_status ON property_notes(status);
CREATE INDEX idx_notes_created ON property_notes(created_at DESC);

-- Property Contacts (Owner phone/email we find)
CREATE TABLE IF NOT EXISTS property_contacts (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT REFERENCES properties(id) ON DELETE CASCADE,
    
    contact_type VARCHAR(20), -- owner, tenant, agent, other
    name VARCHAR(255),
    phone VARCHAR(20),
    phone2 VARCHAR(20),
    email VARCHAR(255),
    
    is_primary BOOLEAN DEFAULT FALSE,
    verified BOOLEAN DEFAULT FALSE,
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_contacts_property ON property_contacts(property_id);
CREATE INDEX idx_contacts_email ON property_contacts(email);
CREATE INDEX idx_contacts_phone ON property_contacts(phone);

-- Property Watchlist
CREATE TABLE IF NOT EXISTS property_watchlist (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT REFERENCES properties(id) ON DELETE CASCADE,
    user_id VARCHAR(100),
    
    reason TEXT,
    priority VARCHAR(10) DEFAULT 'medium',
    
    alert_on_sale BOOLEAN DEFAULT TRUE,
    alert_on_value_change BOOLEAN DEFAULT TRUE,
    alert_threshold_percent DECIMAL(5,2), -- Alert if value changes by X%
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_watchlist_property ON property_watchlist(property_id);
CREATE INDEX idx_watchlist_user ON property_watchlist(user_id);

-- Property Exemptions
CREATE TABLE IF NOT EXISTS property_exemptions (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT REFERENCES properties(id) ON DELETE CASCADE,
    
    exemption_type VARCHAR(50),
    exemption_code VARCHAR(10),
    exemption_amount DECIMAL(15,2),
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_exemptions_property ON property_exemptions(property_id);

-- Views for easier querying
CREATE OR REPLACE VIEW property_summary AS
SELECT 
    p.id,
    p.parcel_id,
    p.phy_addr1,
    p.phy_city,
    p.phy_zipcd,
    p.address_full,
    p.own_name,
    p.property_type,
    p.property_subtype,
    p.jv as market_value,
    p.tv_sd as taxable_value,
    p.lnd_val as land_value,
    p.tot_lvg_area as building_sqft,
    p.lnd_sqfoot as land_sqft,
    p.act_yr_blt as year_built,
    ps.sale_date as last_sale_date,
    ps.sale_price as last_sale_price,
    COUNT(DISTINCT pn.id) as note_count,
    EXISTS(SELECT 1 FROM property_watchlist pw WHERE pw.property_id = p.id) as is_watched
FROM properties p
LEFT JOIN LATERAL (
    SELECT sale_date, sale_price 
    FROM property_sales 
    WHERE property_id = p.id 
    ORDER BY sale_date DESC 
    LIMIT 1
) ps ON true
LEFT JOIN property_notes pn ON pn.property_id = p.id AND pn.status = 'open'
GROUP BY p.id, ps.sale_date, ps.sale_price;

-- Function to categorize property type from use code
CREATE OR REPLACE FUNCTION get_property_type(use_code VARCHAR) 
RETURNS TABLE(property_type VARCHAR, property_subtype VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN use_code LIKE '00%' THEN 'Residential'
            WHEN use_code LIKE '01%' THEN 'Residential'
            WHEN use_code LIKE '02%' THEN 'Residential'
            WHEN use_code LIKE '03%' THEN 'Residential'
            WHEN use_code LIKE '04%' THEN 'Residential'
            WHEN use_code LIKE '1%' THEN 'Commercial'
            WHEN use_code LIKE '2%' THEN 'Industrial'
            WHEN use_code LIKE '3%' THEN 'Agricultural'
            WHEN use_code LIKE '4%' THEN 'Institutional'
            WHEN use_code LIKE '5%' THEN 'Government'
            ELSE 'Other'
        END as property_type,
        CASE 
            WHEN use_code = '000' THEN 'Vacant Residential'
            WHEN use_code = '001' THEN 'Single Family'
            WHEN use_code = '002' THEN 'Mobile Home'
            WHEN use_code = '003' THEN 'Multi-Family'
            WHEN use_code = '004' THEN 'Condominium'
            WHEN use_code = '100' THEN 'Vacant Commercial'
            WHEN use_code = '101' THEN 'Retail'
            WHEN use_code = '102' THEN 'Office'
            WHEN use_code = '104' THEN 'Restaurant'
            WHEN use_code = '105' THEN 'Hotel'
            WHEN use_code = '200' THEN 'Vacant Industrial'
            WHEN use_code = '201' THEN 'Manufacturing'
            WHEN use_code = '202' THEN 'Warehouse'
            ELSE 'Other'
        END as property_subtype;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update property types on insert/update
CREATE OR REPLACE FUNCTION update_property_type() RETURNS TRIGGER AS $$
BEGIN
    SELECT property_type, property_subtype 
    INTO NEW.property_type, NEW.property_subtype
    FROM get_property_type(NEW.dor_uc);
    
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_property_type
    BEFORE INSERT OR UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION update_property_type();

-- Row Level Security Policies
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_contacts ENABLE ROW LEVEL SECURITY;

-- Public read access for properties
CREATE POLICY "Public properties read" ON properties FOR SELECT USING (true);
CREATE POLICY "Public sales read" ON property_sales FOR SELECT USING (true);
CREATE POLICY "Public details read" ON property_details FOR SELECT USING (true);

-- Authenticated users can manage notes and contacts
CREATE POLICY "Auth notes manage" ON property_notes 
    FOR ALL USING (auth.uid() IS NOT NULL);
CREATE POLICY "Auth contacts manage" ON property_contacts 
    FOR ALL USING (auth.uid() IS NOT NULL);