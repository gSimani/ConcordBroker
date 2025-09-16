#!/usr/bin/env python3
"""
Create Property Appraiser tables in Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Override environment variables with correct values
os.environ['SUPABASE_URL'] = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'

# Get credentials
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

logger.info(f"Using Supabase URL: {url}")

# Create client
supabase: Client = create_client(url, key)

# Read the SQL schema
with open('property_appraiser_schema.sql', 'r') as f:
    schema_sql = f.read()

logger.info("SQL Schema loaded. Please execute this in your Supabase SQL Editor:")
logger.info("="*70)
print("\n\nPLEASE COPY AND PASTE THE FOLLOWING SQL INTO SUPABASE SQL EDITOR:\n")
print("1. Go to: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql/new")
print("2. Paste the SQL from property_appraiser_schema.sql")
print("3. Click 'Run' to create all tables")
print("\n" + "="*70)

# Test if tables exist
tables_to_check = [
    'property_assessments',
    'property_owners', 
    'property_sales',
    'nav_summaries',
    'nav_details'
]

print("\nChecking for existing tables...")
for table in tables_to_check:
    try:
        result = supabase.table(table).select('count', count='exact').limit(1).execute()
        print(f"✓ {table} exists")
    except Exception as e:
        if "does not exist" in str(e):
            print(f"✗ {table} does not exist - needs to be created")
        else:
            print(f"? {table} - error checking: {e}")

print("\nOnce tables are created, run: python property_appraiser_supabase_loader.py")