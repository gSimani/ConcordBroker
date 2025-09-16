"""
Test existing Sunbiz tables and show their structure
"""

import os
from supabase import create_client

# Initialize Supabase
supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

supabase = create_client(supabase_url, supabase_key)

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Testing Sunbiz tables...\n")

# Test each table
tables = ['sunbiz_corporate', 'sunbiz_fictitious', 'sunbiz_liens', 'sunbiz_partnerships']

for table in tables:
    try:
        # Get one row to see structure
        result = supabase.table(table).select('*').limit(1).execute()
        
        if result.data and len(result.data) > 0:
            print(f"✅ Table '{table}' exists with columns:")
            for key in result.data[0].keys():
                print(f"   - {key}")
        else:
            print(f"✅ Table '{table}' exists but is empty")
            # Try to get column info another way
            result2 = supabase.table(table).select('*').limit(0).execute()
            print(f"   (Ready for data insertion)")
        
        print()
        
    except Exception as e:
        print(f"❌ Table '{table}' error: {e}\n")

print("\nRecommendation: Use the existing table structure for data loading")