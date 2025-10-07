# -*- coding: utf-8 -*-
import os
from supabase import create_client
from datetime import datetime

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

client = create_client(SUPABASE_URL, SUPABASE_KEY)

tables = ['florida_parcels', 'property_sales_history', 'florida_entities', 'sunbiz_corporate', 'tax_certificates']

print("=" * 80)
print("COMPREHENSIVE SUPABASE DATABASE AUDIT REPORT")
print("=" * 80)
print(f"Database: {SUPABASE_URL}")
print(f"Timestamp: {datetime.now()}")
print()

for table in tables:
    print(f"\n[TABLE: {table}]")
    try:
        response = client.table(table).select("*", count="exact").limit(0).execute()
        count = response.count
        print(f"  Row Count: {count:,}")
        
        sample = client.table(table).select("*").limit(5).execute()
        if sample.data and len(sample.data) > 0:
            print(f"  Columns: {len(sample.data[0].keys())}")
            print(f"  Sample columns: {list(sample.data[0].keys())[:10]}")
    except Exception as e:
        print(f"  ERROR: {str(e)}")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
