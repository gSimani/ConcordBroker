"""
Check if property 474130030430 has been updated with 5 bed / 4 bath
"""

import os
from supabase import create_client, Client

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pmispwtdngkcmsrsjwbp.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Query the property
result = supabase.table('florida_parcels')\
    .select('parcel_id, bedrooms, bathrooms, units, property_use')\
    .eq('parcel_id', '474130030430')\
    .eq('county', 'BROWARD')\
    .execute()

if result.data:
    print("Property 474130030430:")
    for key, value in result.data[0].items():
        print(f"  {key}: {value}")
else:
    print("Property not found!")
