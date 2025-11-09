-- Create tax_certificates table for storing Florida tax certificate data
CREATE TABLE IF NOT EXISTS tax_certificates (
    id SERIAL PRIMARY KEY,
    
    -- Property identification
    parcel_id VARCHAR(50) NOT NULL,
    real_estate_account VARCHAR(50),
    county VARCHAR(50) DEFAULT 'BROWARD',
    
    -- Certificate details
    certificate_number VARCHAR(50) NOT NULL,
    advertised_number VARCHAR(50),
    tax_year INTEGER NOT NULL,
    
    -- Financial information
    face_amount DECIMAL(12, 2) NOT NULL,
    redemption_amount DECIMAL(12, 2),
    interest_rate DECIMAL(5, 2) DEFAULT 18.00,
    winning_bid_percentage DECIMAL(5, 2),
    
    -- Buyer information
    buyer_name VARCHAR(255) NOT NULL,
    buyer_entity_type VARCHAR(100),
    buyer_address TEXT,
    
    -- Important dates
    issued_date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    redemption_date DATE,
    sale_date DATE,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'redeemed', 'expired', 'foreclosed')),
    is_delinquent BOOLEAN DEFAULT true,
    
    -- Metadata
    data_source VARCHAR(100) DEFAULT 'BROWARD_TAX_COLLECTOR',
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Create indexes for common queries
    CONSTRAINT unique_cert UNIQUE (certificate_number, tax_year)
);

-- Create indexes for better query performance
CREATE INDEX idx_tax_cert_parcel ON tax_certificates(parcel_id);
CREATE INDEX idx_tax_cert_buyer ON tax_certificates(buyer_name);
CREATE INDEX idx_tax_cert_status ON tax_certificates(status);
CREATE INDEX idx_tax_cert_year ON tax_certificates(tax_year);
CREATE INDEX idx_tax_cert_county ON tax_certificates(county);

-- Create a view for active certificates with calculated fields
CREATE OR REPLACE VIEW active_tax_certificates AS
SELECT 
    tc.*,
    -- Calculate days until expiration
    EXTRACT(DAY FROM (expiration_date - CURRENT_DATE)) as days_until_expiration,
    -- Calculate current redemption amount with interest
    CASE 
        WHEN status = 'active' THEN
            face_amount * POWER(1 + (interest_rate / 100), 
            EXTRACT(YEAR FROM AGE(CURRENT_DATE, issued_date)) + 
            EXTRACT(MONTH FROM AGE(CURRENT_DATE, issued_date)) / 12.0)
        ELSE redemption_amount
    END as current_redemption_amount,
    -- Flag for imminent expiration (within 90 days)
    CASE 
        WHEN EXTRACT(DAY FROM (expiration_date - CURRENT_DATE)) <= 90 
        AND status = 'active' THEN true 
        ELSE false 
    END as expiring_soon
FROM tax_certificates tc
WHERE status = 'active';

-- Insert sample tax certificate data for testing
INSERT INTO tax_certificates (
    parcel_id, real_estate_account, certificate_number, advertised_number,
    tax_year, face_amount, redemption_amount, interest_rate, winning_bid_percentage,
    buyer_name, issued_date, expiration_date, status
) VALUES 
(
    '064210010010', '064210010010', '2023-14589', 'AD-2023-14589',
    2023, 3245.67, 3828.49, 18.00, 18.00,
    'CAPITAL ONE, NATIONAL ASSOCIATION (USA)',
    '2023-06-01', '2025-06-01', 'active'
),
(
    '064210010010', '064210010010', '2022-08926', 'AD-2022-08926',
    2022, 2890.45, 3406.73, 18.00, 18.00,
    'TLGFY, LLC, A FLORIDA LIMITED LIABILITY CO.',
    '2022-06-01', '2024-06-01', 'active'
),
(
    '064210010010', '064210010010', '2021-05472', 'AD-2021-05472',
    2021, 2750.32, 3575.42, 18.00, 18.00,
    '5T WEALTH PARTNERS LP',
    '2021-06-01', '2023-06-01', 'redeemed'
),
(
    '064210020020', '064210020020', '2023-22145', 'AD-2023-22145',
    2023, 5420.89, 6396.65, 18.00, 18.00,
    'FLORIDA TAX CERTIFICATE FUND III',
    '2023-06-01', '2025-06-01', 'active'
),
(
    '064210030030', '064210030030', '2023-33567', 'AD-2023-33567',
    2023, 1875.43, 2212.51, 18.00, 18.00,
    'BRIDGE TAX CERTIFICATE COMPANY',
    '2023-06-01', '2025-06-01', 'active'
);

-- Function to calculate certificate statistics for a property
CREATE OR REPLACE FUNCTION get_property_tax_certificate_stats(p_parcel_id VARCHAR)
RETURNS TABLE(
    total_certificates INTEGER,
    active_certificates INTEGER,
    total_face_amount DECIMAL,
    total_redemption_amount DECIMAL,
    oldest_certificate_year INTEGER,
    newest_certificate_year INTEGER,
    primary_buyer VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_certificates,
        COUNT(*) FILTER (WHERE status = 'active')::INTEGER as active_certificates,
        SUM(face_amount) as total_face_amount,
        SUM(CASE 
            WHEN status = 'active' THEN
                face_amount * POWER(1 + (interest_rate / 100), 
                EXTRACT(YEAR FROM AGE(CURRENT_DATE, issued_date)) + 
                EXTRACT(MONTH FROM AGE(CURRENT_DATE, issued_date)) / 12.0)
            ELSE redemption_amount
        END) as total_redemption_amount,
        MIN(tax_year)::INTEGER as oldest_certificate_year,
        MAX(tax_year)::INTEGER as newest_certificate_year,
        (SELECT buyer_name 
         FROM tax_certificates 
         WHERE parcel_id = p_parcel_id 
         GROUP BY buyer_name 
         ORDER BY COUNT(*) DESC 
         LIMIT 1) as primary_buyer
    FROM tax_certificates
    WHERE parcel_id = p_parcel_id;
END;
$$ LANGUAGE plpgsql;

-- Grant appropriate permissions
GRANT SELECT ON tax_certificates TO authenticated;
GRANT SELECT ON active_tax_certificates TO authenticated;
GRANT EXECUTE ON FUNCTION get_property_tax_certificate_stats TO authenticated;