import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
# Use the service role key for admin operations
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not key:
    print("Service role key not found, trying anon key...")
    key = os.getenv('VITE_SUPABASE_ANON_KEY')

print(f"Using Supabase URL: {url}")
print(f"Using key starting with: {key[:20]}..." if key else "No key found")

supabase = create_client(url, key)

# Create the tax_certificates table using SQL via RPC
create_table_sql = """
CREATE TABLE IF NOT EXISTS tax_certificates (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    real_estate_account VARCHAR(50),
    certificate_number VARCHAR(50),
    tax_year INTEGER,
    buyer_name VARCHAR(255),
    certificate_buyer VARCHAR(255),
    advertised_number VARCHAR(50),
    face_amount DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    issued_date DATE,
    sale_date DATE,
    expiration_date DATE,
    interest_rate DECIMAL(5,2),
    bid_percentage DECIMAL(5,2),
    winning_bid_percentage DECIMAL(5,2),
    status VARCHAR(20),
    redemption_amount DECIMAL(15,2),
    redemption_date DATE,
    buyer_entity JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_tax_certificates_parcel_id ON tax_certificates(parcel_id);
CREATE INDEX IF NOT EXISTS idx_tax_certificates_tax_year ON tax_certificates(tax_year);
"""

print("Creating tax_certificates table...")

# Try to execute the SQL directly
try:
    # Use the service role key to bypass RLS
    from supabase import create_client
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    if service_key:
        admin_supabase = create_client(url, service_key)
        # Note: Supabase Python client doesn't have direct SQL execution
        # We'll create the table via insert operations
        print("Table creation SQL prepared. Please execute in Supabase SQL Editor:")
        print(create_table_sql)
        
except Exception as e:
    print(f"Error: {e}")
    print("\nPlease run the following SQL in your Supabase SQL Editor:")
    print(create_table_sql)

# Now insert sample data
sample_certificates = [
    {
        "parcel_id": "064210010010",
        "real_estate_account": "064210010010",
        "certificate_number": "2023-12456",
        "tax_year": 2023,
        "buyer_name": "5T WEALTH PARTNERS LP",
        "certificate_buyer": "5T WEALTH PARTNERS LP",
        "advertised_number": "AD-2023-12456",
        "face_amount": 15234.50,
        "tax_amount": 15234.50,
        "issued_date": "2023-06-01",
        "sale_date": "2023-06-01",
        "expiration_date": "2025-06-01",
        "interest_rate": 18.0,
        "bid_percentage": 18.0,
        "winning_bid_percentage": 18.0,
        "status": "active",
        "redemption_amount": 17976.71,
        "buyer_entity": {
            "status": "Active",
            "entity_name": "5T WEALTH PARTNERS LP",
            "filing_type": "Limited Partnership",
            "document_number": "P20000087654",
            "registered_agent": "Wealth Management Services Inc",
            "principal_address": "800 Brickell Avenue, Suite 900, Miami, FL 33131"
        }
    },
    {
        "parcel_id": "474135040890",  # The property user is viewing
        "real_estate_account": "474135040890",
        "certificate_number": "2023-98765",
        "tax_year": 2023,
        "buyer_name": "CAPITAL ONE, NATIONAL ASSOCIATION",
        "certificate_buyer": "CAPITAL ONE, NATIONAL ASSOCIATION",
        "advertised_number": "AD-2023-98765",
        "face_amount": 12500.00,
        "tax_amount": 12500.00,
        "issued_date": "2023-06-01",
        "sale_date": "2023-06-01",
        "expiration_date": "2025-06-01",
        "interest_rate": 18.0,
        "bid_percentage": 18.0,
        "winning_bid_percentage": 18.0,
        "status": "active",
        "redemption_amount": 14750.00,
        "buyer_entity": {
            "status": "Active",
            "entity_name": "CAPITAL ONE, NATIONAL ASSOCIATION",
            "filing_type": "Corporation",
            "document_number": "F96000004500",
            "registered_agent": "Corporate Services Company",
            "principal_address": "1680 Capital One Drive, McLean, VA 22102"
        }
    },
    {
        "parcel_id": "474135040890",  # Another certificate for same property
        "real_estate_account": "474135040890",
        "certificate_number": "2022-87654",
        "tax_year": 2022,
        "buyer_name": "TLGFY, LLC",
        "certificate_buyer": "TLGFY, LLC",
        "advertised_number": "AD-2022-87654",
        "face_amount": 11800.00,
        "tax_amount": 11800.00,
        "issued_date": "2022-06-01",
        "sale_date": "2022-06-01",
        "expiration_date": "2024-06-01",
        "interest_rate": 18.0,
        "bid_percentage": 18.0,
        "winning_bid_percentage": 18.0,
        "status": "active",
        "redemption_amount": 16048.00,
        "buyer_entity": {
            "status": "Active",
            "entity_name": "TLGFY, LLC",
            "filing_type": "Limited Liability Company",
            "document_number": "L22000145890",
            "registered_agent": "Florida Corporate Filings LLC",
            "principal_address": "500 Brickell Avenue, Suite 3100, Miami, FL 33131"
        }
    }
]

print("\nAttempting to insert sample tax certificates...")

try:
    # Try to insert sample data
    response = supabase.table('tax_certificates').insert(sample_certificates).execute()
    print(f"Successfully inserted {len(sample_certificates)} tax certificates!")
    print(f"Certificates added for parcels: 064210010010, 474135040890")
except Exception as e:
    if 'does not exist' in str(e):
        print("\nTable doesn't exist yet. Please create it first using this SQL in Supabase:")
        print(create_table_sql)
        print("\nThen run this script again to insert the data.")
    else:
        print(f"Error inserting data: {e}")