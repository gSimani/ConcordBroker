"""
Test using Supabase client with service role key for bulk operations
This bypasses the direct PostgreSQL connection issues
"""

from supabase import create_client, Client
import os
import time

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"

# Get service role key from .env file
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

if not SERVICE_ROLE_KEY:
    print("=" * 70)
    print("SERVICE ROLE KEY NEEDED")
    print("=" * 70)
    print("\nTo bypass the PostgreSQL connection issues, we can use the")
    print("Supabase service role key for bulk operations.")
    print("\nPlease get the service role key from:")
    print("Dashboard -> Settings -> API -> service_role (secret)")
    print("\nThen set it as an environment variable:")
    print("set SUPABASE_SERVICE_ROLE_KEY=your_key_here")
    print("=" * 70)
else:
    print("=" * 70)
    print("TESTING SUPABASE CLIENT CONNECTION")
    print("=" * 70)
    
    try:
        # Create client with service role key (bypasses RLS)
        supabase: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
        
        print("\nTesting connection...")
        
        # Test query with count
        result = supabase.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
        
        if hasattr(result, 'count'):
            total = result.count
            print(f"SUCCESS! Connected to Supabase")
            print(f"Total records in florida_parcels: {total:,}")
            
            # Check a few counties
            print("\nChecking county distribution...")
            counties = ['BROWARD', 'DADE', 'PALM BEACH', 'HILLSBOROUGH', 'ORANGE']
            
            for county in counties:
                result = supabase.table('florida_parcels')\
                    .select('parcel_id', count='exact')\
                    .eq('county', county)\
                    .limit(1)\
                    .execute()
                
                if hasattr(result, 'count'):
                    print(f"  {county}: {result.count:,} records")
            
            print("\n" + "=" * 70)
            print("CONNECTION SUCCESSFUL!")
            print("We can use this method for bulk uploads")
            print("=" * 70)
            
            # Test if we can disable RLS for faster operations
            print("\nNote: For bulk operations, we should:")
            print("1. Use batch uploads with the service role key")
            print("2. Process in chunks of 1000-5000 records")
            print("3. Implement retry logic for timeouts")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nPlease verify the service role key is correct")