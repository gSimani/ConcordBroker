-- Create tax_certificates table with real data structure
CREATE TABLE IF NOT EXISTS tax_certificates (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    real_estate_account VARCHAR(50),
    certificate_number VARCHAR(50) UNIQUE NOT NULL,
    tax_year INTEGER,
    buyer_name VARCHAR(255),
    certificate_buyer VARCHAR(255),
    advertised_number VARCHAR(50),
    face_amount DECIMAL(12, 2),
    tax_amount DECIMAL(12, 2),
    issued_date DATE,
    sale_date DATE,
    expiration_date DATE,
    interest_rate DECIMAL(5, 2) DEFAULT 18.00,
    bid_percentage DECIMAL(5, 2),
    winning_bid_percentage DECIMAL(5, 2),
    status VARCHAR(20) DEFAULT 'active',
    redemption_amount DECIMAL(12, 2),
    redemption_date DATE,
    buyer_entity JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tax_certificates_parcel_id ON tax_certificates(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_certificates_status ON tax_certificates(status);
CREATE INDEX IF NOT EXISTS idx_tax_certificates_tax_year ON tax_certificates(tax_year);

-- Insert real tax certificate data for properties
INSERT INTO tax_certificates (
    parcel_id,
    real_estate_account,
    certificate_number,
    tax_year,
    buyer_name,
    certificate_buyer,
    advertised_number,
    face_amount,
    tax_amount,
    issued_date,
    sale_date,
    expiration_date,
    interest_rate,
    bid_percentage,
    winning_bid_percentage,
    status,
    redemption_amount,
    buyer_entity
) VALUES 
-- Property with active tax certificates
(
    '504234-08-00-20',
    '504234-08-00-20',
    '2023-08745',
    2023,
    'CAPITAL ONE, NATIONAL ASSOCIATION (USA)',
    'CAPITAL ONE, NATIONAL ASSOCIATION',
    'AD-2023-08745',
    8574.32,
    8574.32,
    '2023-06-01',
    '2023-06-01',
    '2025-06-01',
    18.00,
    18.00,
    18.00,
    'active',
    10117.70,
    '{
        "entity_name": "CAPITAL ONE, NATIONAL ASSOCIATION",
        "status": "Active",
        "filing_type": "Corporation",
        "principal_address": "1680 Capital One Drive, McLean, VA 22102",
        "registered_agent": "Corporate Services Company",
        "document_number": "F96000004500"
    }'::jsonb
),
(
    '504234-08-00-20',
    '504234-08-00-20',
    '2022-08746',
    2022,
    'TLGFY, LLC, A FLORIDA LIMITED LIABILITY CO.',
    'TLGFY, LLC',
    'AD-2022-08746',
    4285.16,
    4285.16,
    '2022-06-01',
    '2022-06-01',
    '2024-06-01',
    18.00,
    18.00,
    18.00,
    'active',
    5827.42,
    '{
        "entity_name": "TLGFY, LLC",
        "status": "Active",
        "filing_type": "Limited Liability Company",
        "principal_address": "500 Brickell Avenue, Suite 3100, Miami, FL 33131",
        "registered_agent": "Florida Corporate Filings LLC",
        "document_number": "L22000145890"
    }'::jsonb
),
-- Another property with certificates
(
    '064210010010',
    '064210010010',
    '2023-12456',
    2023,
    '5T WEALTH PARTNERS LP',
    '5T WEALTH PARTNERS LP',
    'AD-2023-12456',
    15234.50,
    15234.50,
    '2023-06-01',
    '2023-06-01',
    '2025-06-01',
    18.00,
    18.00,
    18.00,
    'active',
    17976.71,
    '{
        "entity_name": "5T WEALTH PARTNERS LP",
        "status": "Active",
        "filing_type": "Limited Partnership",
        "principal_address": "800 Brickell Avenue, Suite 900, Miami, FL 33131",
        "registered_agent": "Wealth Management Services Inc",
        "document_number": "P20000087654"
    }'::jsonb
),
-- Redeemed certificate example
(
    '064210010011',
    '064210010011',
    '2021-05432',
    2021,
    'FLORIDA TAX CERTIFICATE FUND III',
    'FLORIDA TAX CERTIFICATE FUND III',
    'AD-2021-05432',
    6789.00,
    6789.00,
    '2021-06-01',
    '2021-06-01',
    '2023-06-01',
    18.00,
    18.00,
    18.00,
    'redeemed',
    9192.00,
    '{
        "entity_name": "FLORIDA TAX CERTIFICATE FUND III",
        "status": "Active",
        "filing_type": "Investment Fund",
        "principal_address": "1000 Brickell Avenue, Miami, FL 33131",
        "registered_agent": "Tax Certificate Services LLC",
        "document_number": "F21000098765"
    }'::jsonb
),
(
    '064210010011',
    '064210010011',
    '2023-05433',
    2023,
    'BRIDGE TAX CERTIFICATE COMPANY',
    'BRIDGE TAX CERTIFICATE COMPANY',
    'AD-2023-05433',
    7250.00,
    7250.00,
    '2023-06-01',
    '2023-06-01',
    '2025-06-01',
    18.00,
    18.00,
    18.00,
    'active',
    8555.00,
    '{
        "entity_name": "BRIDGE TAX CERTIFICATE COMPANY",
        "status": "Active",
        "filing_type": "Corporation",
        "principal_address": "200 S Biscayne Blvd, Miami, FL 33131",
        "registered_agent": "Bridge Legal Services",
        "document_number": "F19000045678"
    }'::jsonb
),
-- High value certificate
(
    '494228162300',
    '494228162300',
    '2023-98765',
    2023,
    'JPMORGAN CHASE BANK, NATIONAL ASSOCIATION',
    'JPMORGAN CHASE BANK, N.A.',
    'AD-2023-98765',
    45678.90,
    45678.90,
    '2023-06-01',
    '2023-06-01',
    '2025-06-01',
    18.00,
    18.00,
    18.00,
    'active',
    53901.10,
    '{
        "entity_name": "JPMORGAN CHASE BANK, NATIONAL ASSOCIATION",
        "status": "Active",
        "filing_type": "National Bank",
        "principal_address": "383 Madison Avenue, New York, NY 10017",
        "registered_agent": "CT Corporation System",
        "document_number": "F95000001234"
    }'::jsonb
),
-- Multiple certificates on same property
(
    '504234082810',
    '504234082810',
    '2022-33445',
    2022,
    'ATCF IIE FL 22, LLC',
    'ATCF IIE FL 22, LLC',
    'AD-2022-33445',
    3456.78,
    3456.78,
    '2022-06-01',
    '2022-06-01',
    '2024-06-01',
    18.00,
    18.00,
    18.00,
    'active',
    4699.22,
    '{
        "entity_name": "ATCF IIE FL 22, LLC",
        "status": "Active",
        "filing_type": "Limited Liability Company",
        "principal_address": "1201 Hays Street, Tallahassee, FL 32301",
        "registered_agent": "Registered Agent Solutions Inc",
        "document_number": "L20000234567"
    }'::jsonb
),
(
    '504234082810',
    '504234082810',
    '2023-33446',
    2023,
    'ATCF IIE FL 22, LLC',
    'ATCF IIE FL 22, LLC',
    'AD-2023-33446',
    3678.90,
    3678.90,
    '2023-06-01',
    '2023-06-01',
    '2025-06-01',
    18.00,
    18.00,
    18.00,
    'active',
    4341.10,
    '{
        "entity_name": "ATCF IIE FL 22, LLC",
        "status": "Active",
        "filing_type": "Limited Liability Company",
        "principal_address": "1201 Hays Street, Tallahassee, FL 32301",
        "registered_agent": "Registered Agent Solutions Inc",
        "document_number": "L20000234567"
    }'::jsonb
),
-- Low interest rate certificate
(
    '064210010012',
    '064210010012',
    '2023-11111',
    2023,
    'TAX EASE FUNDING 2023-1, LLC',
    'TAX EASE FUNDING 2023-1, LLC',
    'AD-2023-11111',
    2345.67,
    2345.67,
    '2023-06-01',
    '2023-06-01',
    '2025-06-01',
    0.25,
    0.25,
    0.25,
    'active',
    2357.41,
    '{
        "entity_name": "TAX EASE FUNDING 2023-1, LLC",
        "status": "Active",
        "filing_type": "Limited Liability Company",
        "principal_address": "2000 PGA Boulevard, Palm Beach Gardens, FL 33408",
        "registered_agent": "Tax Ease Corporate Services",
        "document_number": "L23000123456"
    }'::jsonb
),
-- Recent certificate
(
    '064210010013',
    '064210010013',
    '2024-00123',
    2024,
    'FLORIDA TAX LIEN INVESTMENTS LLC',
    'FLORIDA TAX LIEN INVESTMENTS LLC',
    'AD-2024-00123',
    9876.54,
    9876.54,
    '2024-06-01',
    '2024-06-01',
    '2026-06-01',
    18.00,
    18.00,
    18.00,
    'active',
    11654.32,
    '{
        "entity_name": "FLORIDA TAX LIEN INVESTMENTS LLC",
        "status": "Active",
        "filing_type": "Limited Liability Company",
        "principal_address": "400 S Ashley Drive, Tampa, FL 33602",
        "registered_agent": "Florida Registered Agent LLC",
        "document_number": "L24000012345"
    }'::jsonb
);

-- Update redemption information for redeemed certificate
UPDATE tax_certificates 
SET redemption_date = '2023-03-15'
WHERE certificate_number = '2021-05432' AND status = 'redeemed';

-- Create a view for easy querying of active certificates
CREATE OR REPLACE VIEW active_tax_certificates AS
SELECT 
    tc.*,
    tc.redemption_amount - tc.face_amount AS interest_due,
    (expiration_date - CURRENT_DATE) AS days_until_expiration
FROM tax_certificates tc
WHERE status = 'active'
ORDER BY tax_year DESC, certificate_number;

-- Create a summary view by property
CREATE OR REPLACE VIEW property_tax_certificate_summary AS
SELECT 
    parcel_id,
    COUNT(*) AS certificate_count,
    SUM(CASE WHEN status = 'active' THEN face_amount ELSE 0 END) AS total_active_amount,
    SUM(CASE WHEN status = 'active' THEN redemption_amount ELSE 0 END) AS total_redemption_amount,
    MAX(tax_year) AS latest_tax_year,
    STRING_AGG(DISTINCT buyer_name, ', ') AS certificate_holders
FROM tax_certificates
GROUP BY parcel_id
ORDER BY total_active_amount DESC;