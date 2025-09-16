#!/usr/bin/env python3
"""
Test Supabase Connection
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_connection():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    print("Testing Supabase Connection")
    print("=" * 40)
    print(f"URL: {url}")
    print(f"Key: {key[:20]}...{key[-10:]}" if key else "No key found")
    
    try:
        # Create client
        supabase: Client = create_client(url, key)
        print("\n[OK] Client created successfully")
        
        # Test query
        result = supabase.table('florida_parcels').select('parcel_id').limit(1).execute()
        print(f"[OK] Query successful: {len(result.data)} records")
        
        # Get count
        count_result = supabase.table('florida_parcels').select('*', count='exact').limit(0).execute()
        print(f"[OK] Total records: {count_result.count if hasattr(count_result, 'count') else 'Unknown'}")
        
        print("\n[SUCCESS] Supabase connection working!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
