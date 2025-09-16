import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(".env.mcp")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"URL: {url}")
print(f"Key: {key[:20] if key else None}...")

if url and key:
    try:
        supabase = create_client(url, key)
        print("Client created successfully")
        
        # Test with a simple table query
        result = supabase.table("florida_parcels").select("*").limit(1).execute()
        print(f"Table query result: {len(result.data)} records")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Missing credentials")
