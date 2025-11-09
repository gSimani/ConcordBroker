-- Create comprehensive sales history tables with buyer tracking

-- 1. Main sales history table (all transactions)
CREATE TABLE IF NOT EXISTS property_sales_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    property_address VARCHAR(255),
    property_city VARCHAR(100),
    property_zip VARCHAR(20),
    
    -- Sale details
    sale_date DATE,
    sale_year INTEGER,
    sale_month INTEGER,
    sale_price BIGINT,
    
    -- Buyer information (who bought it)
    buyer_name VARCHAR(255),
    buyer_address VARCHAR(255),
    buyer_city VARCHAR(100),
    buyer_state VARCHAR(50),
    buyer_zip VARCHAR(20),
    
    -- Seller information (who sold it)
    seller_name VARCHAR(255),
    seller_address VARCHAR(255),
    seller_city VARCHAR(100),
    seller_state VARCHAR(50),
    seller_zip VARCHAR(20),
    
    -- Transaction details
    deed_type VARCHAR(100),
    qual_code VARCHAR(10),
    vi_code VARCHAR(10),
    or_book VARCHAR(20),
    or_page VARCHAR(20),
    clerk_no VARCHAR(50),
    multi_parcel_sale BOOLEAN DEFAULT false,
    
    -- Data source tracking
    data_source VARCHAR(50), -- 'SDF', 'NAL_SALE1', 'NAL_SALE2', etc.
    import_date TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_sales_parcel (parcel_id),
    INDEX idx_sales_address (property_address),
    INDEX idx_sales_date (sale_date DESC),
    INDEX idx_sales_buyer (buyer_name),
    INDEX idx_sales_seller (seller_name),
    INDEX idx_sales_price (sale_price)
);

-- 2. Property ownership history (who owned when)
CREATE TABLE IF NOT EXISTS property_ownership_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    owner_name VARCHAR(255),
    ownership_start_date DATE,
    ownership_end_date DATE,
    purchase_price BIGINT,
    sale_price BIGINT,
    days_owned INTEGER,
    profit_loss BIGINT,
    
    INDEX idx_ownership_parcel (parcel_id),
    INDEX idx_ownership_owner (owner_name),
    INDEX idx_ownership_dates (ownership_start_date, ownership_end_date)
);

-- 3. Buyer activity tracking (track buyers across multiple properties)
CREATE TABLE IF NOT EXISTS buyer_activity (
    id BIGSERIAL PRIMARY KEY,
    buyer_name VARCHAR(255),
    buyer_normalized VARCHAR(255), -- Normalized name for matching
    total_purchases INTEGER DEFAULT 0,
    total_spent BIGINT DEFAULT 0,
    first_purchase_date DATE,
    last_purchase_date DATE,
    properties_owned TEXT[], -- Array of parcel IDs
    
    INDEX idx_buyer_name (buyer_name),
    INDEX idx_buyer_normalized (buyer_normalized),
    INDEX idx_buyer_activity (total_purchases DESC)
);

-- 4. Address-to-parcel matching table
CREATE TABLE IF NOT EXISTS address_parcel_match (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    address_full VARCHAR(500),
    address_normalized VARCHAR(500),
    address_number VARCHAR(50),
    address_street VARCHAR(255),
    address_city VARCHAR(100),
    address_zip VARCHAR(20),
    confidence_score FLOAT DEFAULT 1.0,
    
    INDEX idx_address_parcel (parcel_id),
    INDEX idx_address_full (address_full),
    INDEX idx_address_normalized (address_normalized),
    UNIQUE(parcel_id, address_normalized)
);

-- 5. Create view for complete property history
CREATE OR REPLACE VIEW property_complete_history AS
SELECT 
    p.parcel_id,
    p.phy_addr1 as current_address,
    p.phy_city as current_city,
    p.owner_name as current_owner,
    p.just_value,
    p.taxable_value,
    COUNT(DISTINCT s.id) as total_sales,
    MIN(s.sale_date) as first_sale_date,
    MAX(s.sale_date) as last_sale_date,
    MAX(s.sale_price) as last_sale_price,
    ARRAY_AGG(DISTINCT s.buyer_name) FILTER (WHERE s.buyer_name IS NOT NULL) as all_buyers,
    ARRAY_AGG(DISTINCT s.seller_name) FILTER (WHERE s.seller_name IS NOT NULL) as all_sellers
FROM florida_parcels p
LEFT JOIN property_sales_history s ON p.parcel_id = s.parcel_id
GROUP BY p.parcel_id, p.phy_addr1, p.phy_city, p.owner_name, p.just_value, p.taxable_value;

-- 6. Create view for buyer portfolio
CREATE OR REPLACE VIEW buyer_portfolio AS
SELECT 
    b.buyer_name,
    b.total_purchases,
    b.total_spent,
    b.first_purchase_date,
    b.last_purchase_date,
    COUNT(DISTINCT p.parcel_id) as properties_currently_owned,
    SUM(p.just_value) as portfolio_value,
    SUM(p.taxable_value) as portfolio_taxable_value
FROM buyer_activity b
LEFT JOIN florida_parcels p ON p.owner_name ILIKE b.buyer_normalized
GROUP BY b.buyer_name, b.total_purchases, b.total_spent, b.first_purchase_date, b.last_purchase_date;

-- Grant permissions
GRANT ALL ON property_sales_history TO anon, authenticated;
GRANT ALL ON property_ownership_history TO anon, authenticated;
GRANT ALL ON buyer_activity TO anon, authenticated;
GRANT ALL ON address_parcel_match TO anon, authenticated;
GRANT SELECT ON property_complete_history TO anon, authenticated;
GRANT SELECT ON buyer_portfolio TO anon, authenticated;

-- Enable RLS
ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_ownership_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE buyer_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE address_parcel_match ENABLE ROW LEVEL SECURITY;

-- Create policies for read access
CREATE POLICY "Allow public read property_sales_history" ON property_sales_history FOR SELECT USING (true);
CREATE POLICY "Allow public read property_ownership_history" ON property_ownership_history FOR SELECT USING (true);
CREATE POLICY "Allow public read buyer_activity" ON buyer_activity FOR SELECT USING (true);
CREATE POLICY "Allow public read address_parcel_match" ON address_parcel_match FOR SELECT USING (true);

-- Allow inserts for data loading
CREATE POLICY "Allow insert property_sales_history" ON property_sales_history FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow insert property_ownership_history" ON property_ownership_history FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow insert buyer_activity" ON buyer_activity FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow insert address_parcel_match" ON address_parcel_match FOR INSERT WITH CHECK (true);