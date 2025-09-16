"""
Add Sunbiz Entity Data to Database
This script adds IH3 PROPERTY GP or other Sunbiz entities to the database
"""

import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(url, key)

# IH3 PROPERTY GP data based on the URL you provided
ih3_entity = {
    "entity_name": "IH3 PROPERTY GP",
    "document_number": "M13000005449",
    "entity_type": "Florida Limited Partnership",
    "status": "Active",
    "state": "FL",
    "fei_ein_number": "",  # Add if visible on the page
    "date_filed": "",  # Add the date from the page
    "effective_date": "",  # Add if available
    "principal_address": "",  # Add from the page
    "mailing_address": "",  # Add from the page
    "registered_agent_name": "",  # Add from the page
    "registered_agent_address": "",  # Add from the page
    "aggregate_id": "forl-m13000005449-f986457f-0071-4542-9fb8-3e814cabb62d"
}

# First, create the sunbiz_entities table if it doesn't exist
create_table_sql = """
CREATE TABLE IF NOT EXISTS sunbiz_entities (
    id SERIAL PRIMARY KEY,
    entity_name VARCHAR(255),
    document_number VARCHAR(50) UNIQUE,
    entity_type VARCHAR(100),
    status VARCHAR(50),
    state VARCHAR(2),
    fei_ein_number VARCHAR(20),
    date_filed DATE,
    effective_date DATE,
    principal_address TEXT,
    mailing_address TEXT,
    registered_agent_name VARCHAR(255),
    registered_agent_address TEXT,
    aggregate_id VARCHAR(255),
    officers JSONB,
    annual_reports JSONB,
    filing_history JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sunbiz_entities_name ON sunbiz_entities(entity_name);
CREATE INDEX IF NOT EXISTS idx_sunbiz_entities_doc_num ON sunbiz_entities(document_number);
"""

print("=" * 80)
print("SUNBIZ ENTITY DATA INTEGRATION")
print("=" * 80)
print("\nPlease fill in the entity details from the Sunbiz page:")
print(f"URL: https://search.sunbiz.org/.../M13000005449...")
print("\nCurrent entity skeleton:")
print(f"Entity Name: {ih3_entity['entity_name']}")
print(f"Document Number: {ih3_entity['document_number']}")
print(f"Type: {ih3_entity['entity_type']}")
print(f"Status: {ih3_entity['status']}")

print("\n" + "=" * 80)
print("SQL TO CREATE TABLE (run in Supabase if needed):")
print("=" * 80)
print(create_table_sql)

print("\n" + "=" * 80)
print("TO ADD THIS ENTITY:")
print("=" * 80)
print("""
1. Open the Sunbiz URL in your browser
2. Copy the following information:
   - Principal Address
   - Mailing Address  
   - Registered Agent Name
   - Registered Agent Address
   - Date Filed
   - FEI/EIN Number
   - Officers/Directors (names, titles, addresses)

3. Update this script with the actual values
4. Run: python add_sunbiz_entity.py
""")

# Sample code to insert once you have the data
"""
# Example with filled data:
ih3_entity_complete = {
    "entity_name": "IH3 PROPERTY GP",
    "document_number": "M13000005449",
    "entity_type": "Florida Limited Partnership",
    "status": "Active",
    "state": "FL",
    "fei_ein_number": "XX-XXXXXXX",
    "date_filed": "2013-05-15",
    "effective_date": "2013-05-15",
    "principal_address": "123 Main St, Miami, FL 33131",
    "mailing_address": "PO Box 123, Miami, FL 33131",
    "registered_agent_name": "Corporate Agent Services",
    "registered_agent_address": "456 Agent Ave, Miami, FL 33131",
    "officers": [
        {
            "name": "John Doe",
            "title": "General Partner",
            "address": "789 Partner Ln, Miami, FL 33131"
        }
    ]
}

try:
    response = supabase.table('sunbiz_entities').insert(ih3_entity_complete).execute()
    print(f"Successfully added entity: {ih3_entity_complete['entity_name']}")
except Exception as e:
    print(f"Error: {e}")
"""

# Also update tax certificates to link to this entity
update_certificates_sql = """
-- Once you have the Sunbiz entity data, update tax certificates:
UPDATE tax_certificates 
SET buyer_entity = jsonb_build_object(
    'entity_name', 'IH3 PROPERTY GP',
    'document_number', 'M13000005449',
    'entity_type', 'Florida Limited Partnership',
    'status', 'Active',
    'principal_address', '(add from Sunbiz page)',
    'registered_agent', '(add from Sunbiz page)'
)
WHERE buyer_name LIKE '%IH3%' OR buyer_name LIKE '%IH3 PROPERTY%';
"""

print("\n" + "=" * 80)
print("SQL TO LINK TO TAX CERTIFICATES:")
print("=" * 80)
print(update_certificates_sql)