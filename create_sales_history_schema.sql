-- Comprehensive Sales History Schema for ConcordBroker
-- This table stores detailed sales history data with all transaction details

DROP TABLE IF EXISTS public.property_sales_history CASCADE;

-- Property Sales History table
CREATE TABLE public.property_sales_history (
    id SERIAL PRIMARY KEY,
    
    -- Property Identification
    parcel_id VARCHAR(50) NOT NULL,
    property_address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2) DEFAULT 'FL',
    zip_code VARCHAR(10),
    
    -- Sale Transaction Details
    sale_date DATE NOT NULL,
    sale_price DECIMAL(12,2),
    sale_type VARCHAR(100), -- Warranty Deed, Quit Claim, Foreclosure, Tax Deed, etc.
    sale_qualification VARCHAR(50), -- Qualified, Non-Qualified, etc.
    
    -- Recording Information
    book VARCHAR(20),
    page VARCHAR(20),
    book_page VARCHAR(50), -- Combined book/page format
    cin VARCHAR(50), -- Clerk Instrument Number
    instrument_number VARCHAR(50),
    doc_number VARCHAR(50),
    recording_date DATE,
    
    -- Parties Information
    grantor_name VARCHAR(255), -- Seller
    grantee_name VARCHAR(255), -- Buyer
    
    -- Sale Classification
    is_arms_length BOOLEAN DEFAULT TRUE,
    is_distressed BOOLEAN DEFAULT FALSE,
    is_foreclosure BOOLEAN DEFAULT FALSE,
    is_tax_deed BOOLEAN DEFAULT FALSE,
    is_bank_sale BOOLEAN DEFAULT FALSE,
    is_cash_sale BOOLEAN DEFAULT FALSE,
    is_qualified_sale BOOLEAN DEFAULT TRUE,
    
    -- Financial Details
    mortgage_amount DECIMAL(12,2),
    down_payment DECIMAL(12,2),
    financing_type VARCHAR(50), -- Cash, Conventional, FHA, VA, etc.
    
    -- Transfer Tax and Fees
    doc_stamps DECIMAL(10,2),
    transfer_tax DECIMAL(10,2),
    recording_fee DECIMAL(10,2),
    
    -- Property Details at Time of Sale
    living_area_sqft INTEGER,
    lot_size_sqft INTEGER,
    year_built INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    
    -- Price Analysis
    price_per_sqft DECIMAL(10,2),
    market_value_at_sale DECIMAL(12,2),
    sale_to_market_ratio DECIMAL(5,2), -- Sale price / Market value ratio
    
    -- Links and References
    record_link TEXT,
    property_appraiser_link TEXT,
    
    -- Subdivision Information
    subdivision_name VARCHAR(255),
    subdivision_plat_book VARCHAR(20),
    subdivision_plat_page VARCHAR(20),
    
    -- Data Quality
    data_source VARCHAR(50) DEFAULT 'County Records',
    verified BOOLEAN DEFAULT FALSE,
    verification_date DATE,
    
    -- System fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_sales_history_parcel_id ON property_sales_history(parcel_id);
CREATE INDEX idx_sales_history_sale_date ON property_sales_history(sale_date DESC);
CREATE INDEX idx_sales_history_sale_price ON property_sales_history(sale_price);
CREATE INDEX idx_sales_history_sale_type ON property_sales_history(sale_type);
CREATE INDEX idx_sales_history_book_page ON property_sales_history(book_page);
CREATE INDEX idx_sales_history_cin ON property_sales_history(cin);

-- Insert sample sales history data for testing
INSERT INTO property_sales_history (
    parcel_id, property_address, city, zip_code,
    sale_date, sale_price, sale_type, sale_qualification,
    book, page, book_page, cin, instrument_number,
    grantor_name, grantee_name,
    is_arms_length, is_qualified_sale,
    living_area_sqft, lot_size_sqft, year_built,
    price_per_sqft,
    record_link,
    subdivision_name,
    data_source
) VALUES 
-- Recent sale - 2024
('064210010010', '1234 SAMPLE ST', 'FORT LAUDERDALE', '33301',
 '2024-08-15', 485000.00, 'Warranty Deed', 'Qualified',
 '12345', '678', '12345/678', '2024000123456', 'INS2024000123456',
 'SMITH JOHN & MARY', 'JOHNSON FAMILY TRUST',
 TRUE, TRUE,
 2450, 7500, 1987,
 198.00,
 'https://officialrecords.broward.org/oncorewebaccesspublic/detail.aspx?id=2024000123456',
 'SAMPLE ESTATES',
 'Broward County Records'),

-- Previous sale - 2021
('064210010010', '1234 SAMPLE ST', 'FORT LAUDERDALE', '33301',
 '2021-03-22', 380000.00, 'Warranty Deed', 'Qualified',
 '11890', '456', '11890/456', '2021000098765', 'INS2021000098765',
 'BROWN ROBERT', 'SMITH JOHN & MARY',
 TRUE, TRUE,
 2450, 7500, 1987,
 155.00,
 'https://officialrecords.broward.org/oncorewebaccesspublic/detail.aspx?id=2021000098765',
 'SAMPLE ESTATES',
 'Broward County Records'),

-- Older sale - 2018
('064210010010', '1234 SAMPLE ST', 'FORT LAUDERDALE', '33301',
 '2018-11-10', 320000.00, 'Warranty Deed', 'Qualified',
 '11234', '789', '11234/789', '2018000054321', 'INS2018000054321',
 'DAVIS MICHAEL', 'BROWN ROBERT',
 TRUE, TRUE,
 2450, 7500, 1987,
 131.00,
 'https://officialrecords.broward.org/oncorewebaccesspublic/detail.aspx?id=2018000054321',
 'SAMPLE ESTATES',
 'Broward County Records'),

-- Foreclosure sale - 2015
('064210010010', '1234 SAMPLE ST', 'FORT LAUDERDALE', '33301',
 '2015-06-05', 245000.00, 'Special Warranty Deed', 'Qualified',
 '10567', '234', '10567/234', '2015000034567', 'INS2015000034567',
 'BANK OF AMERICA NA', 'DAVIS MICHAEL',
 FALSE, TRUE,
 2450, 7500, 1987,
 100.00,
 'https://officialrecords.broward.org/oncorewebaccesspublic/detail.aspx?id=2015000034567',
 'SAMPLE ESTATES',
 'Broward County Records'),

-- Original sale - 2005
('064210010010', '1234 SAMPLE ST', 'FORT LAUDERDALE', '33301',
 '2005-09-15', 295000.00, 'Warranty Deed', 'Qualified',
 '9876', '543', '9876/543', '2005000012345', 'INS2005000012345',
 'ORIGINAL BUILDER LLC', 'FIRST OWNER',
 TRUE, TRUE,
 2450, 7500, 1987,
 120.00,
 'https://officialrecords.broward.org/oncorewebaccesspublic/detail.aspx?id=2005000012345',
 'SAMPLE ESTATES',
 'Broward County Records');

-- Create a view for easy querying with calculated fields
CREATE OR REPLACE VIEW sales_history_analysis AS
SELECT 
    *,
    -- Calculate days on market between sales
    LAG(sale_date) OVER (PARTITION BY parcel_id ORDER BY sale_date) as previous_sale_date,
    sale_date - LAG(sale_date) OVER (PARTITION BY parcel_id ORDER BY sale_date) as days_between_sales,
    
    -- Calculate price appreciation
    LAG(sale_price) OVER (PARTITION BY parcel_id ORDER BY sale_date) as previous_sale_price,
    CASE 
        WHEN LAG(sale_price) OVER (PARTITION BY parcel_id ORDER BY sale_date) > 0 THEN
            ROUND(((sale_price - LAG(sale_price) OVER (PARTITION BY parcel_id ORDER BY sale_date)) / 
                   LAG(sale_price) OVER (PARTITION BY parcel_id ORDER BY sale_date) * 100), 2)
        ELSE NULL
    END as price_change_percentage,
    
    -- Calculate annual appreciation rate
    CASE 
        WHEN LAG(sale_price) OVER (PARTITION BY parcel_id ORDER BY sale_date) > 0 
         AND sale_date - LAG(sale_date) OVER (PARTITION BY parcel_id ORDER BY sale_date) > 0 THEN
            ROUND(((sale_price / LAG(sale_price) OVER (PARTITION BY parcel_id ORDER BY sale_date))^
                   (365.0 / (sale_date - LAG(sale_date) OVER (PARTITION BY parcel_id ORDER BY sale_date))) - 1) * 100, 2)
        ELSE NULL
    END as annual_appreciation_rate

FROM property_sales_history;

-- Grant permissions
GRANT ALL ON property_sales_history TO anon, authenticated;
GRANT ALL ON sales_history_analysis TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;