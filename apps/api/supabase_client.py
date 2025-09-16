"""
Fixed Supabase Client - Direct Connection to pmispwtdngkcmsrsjwbp
"""

import os
import sys

# Fix for the proxy issue - patch httpx before importing supabase
import httpx

# Store original init
_original_client_init = httpx.Client.__init__

def patched_client_init(self, *args, **kwargs):
    # Remove proxy argument if present
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)

# Apply patch
httpx.Client.__init__ = patched_client_init

# Now import supabase
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """
    Create and return a Supabase client instance for ConcordBroker project.
    ALWAYS uses the correct pmispwtdngkcmsrsjwbp project.
    """
    # FORCE the correct Supabase project - pmispwtdngkcmsrsjwbp
    # DO NOT use any other project ID
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"
    
    # Create client with correct credentials
    client = create_client(url, key)
    
    return client

def test_connection():
    """Test the Supabase connection"""
    try:
        client = get_supabase_client()
        
        # Test with a simple limited query instead of count
        result = client.table('florida_parcels').select('parcel_id').limit(1).execute()
        print("Connection successful!")
        print(f"   Connected to: pmispwtdngkcmsrsjwbp.supabase.co")
        print(f"   Test query returned: {len(result.data)} row(s)")
        
        return True
        
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()