#!/usr/bin/env python3
"""
Test Supabase order syntax to verify what works
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Testing Supabase order syntax:")

# Test 1: Basic order (should work)
try:
    result = supabase.table('florida_parcels').select('parcel_id, phy_addr1').order('phy_addr1').limit(2).execute()
    print("OK: Basic order() works - Records:", len(result.data))
    if result.data:
        print("  First record:", result.data[0])
except Exception as e:
    print("ERROR: Basic order() failed:", str(e))

# Test 2: Order with desc=True (should work)
try:
    result = supabase.table('florida_parcels').select('parcel_id, phy_addr1').order('phy_addr1', desc=True).limit(2).execute()
    print("OK: order(field, desc=True) works - Records:", len(result.data))
except Exception as e:
    print("ERROR: order(field, desc=True) failed:", str(e))

# Test 3: Order with ascending=True (should fail)
try:
    result = supabase.table('florida_parcels').select('parcel_id, phy_addr1').order('phy_addr1', ascending=True).limit(2).execute()
    print("UNEXPECTED: order(field, ascending=True) works")
except Exception as e:
    print("EXPECTED: order(field, ascending=True) failed:", str(e))

print("\nTesting API endpoint simulation:")
# Test the exact same query as the API uses
try:
    query = supabase.table('florida_parcels').select('*', count='exact')
    sortBy = 'phy_addr1'
    sortOrder = 'asc'

    if sortBy and sortOrder:
        if sortOrder.lower() == 'asc':
            query = query.order(sortBy)
        else:
            query = query.order(sortBy, desc=True)

    query = query.range(0, 1)
    response = query.execute()
    print("API SIMULATION: Works! Records:", len(response.data))

except Exception as e:
    print("API SIMULATION FAILED:", str(e))