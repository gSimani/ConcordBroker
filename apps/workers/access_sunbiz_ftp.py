"""
Multiple methods to access Sunbiz FTP data
Including using Supabase Edge Functions as a proxy
"""

import os
import sys
import io
import requests
import json
from pathlib import Path

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_access_methods():
    """Check different methods to access Sunbiz FTP"""
    
    print("=" * 60)
    print("SUNBIZ FTP ACCESS METHODS")
    print("=" * 60)
    
    # Method 1: Try HTTPS mirror
    print("\n1. CHECKING HTTPS MIRRORS:")
    print("-" * 40)
    
    https_mirrors = [
        "https://dos.myflorida.com/sunbiz/search/",
        "https://search.sunbiz.org/",
        "http://search.sunbiz.org/Inquiry/CorporationSearch/ByName",
        "https://dos.fl.gov/sunbiz/",
    ]
    
    for url in https_mirrors:
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code < 400:
                print(f"  ✅ {url} - Accessible")
            else:
                print(f"  ❌ {url} - Status {response.status_code}")
        except Exception as e:
            print(f"  ❌ {url} - Failed")
    
    # Method 2: Check alternative data sources
    print("\n2. ALTERNATIVE DATA SOURCES:")
    print("-" * 40)
    
    alternatives = {
        "OpenCorporates API": "https://api.opencorporates.com/v0.4/companies/search?jurisdiction_code=us_fl",
        "Florida OpenData": "https://data.florida.gov/",
        "Data.gov": "https://catalog.data.gov/dataset?q=florida+business",
        "GitHub Datasets": "https://github.com/search?q=florida+sunbiz+dataset",
        "Kaggle": "https://www.kaggle.com/search?q=florida+business"
    }
    
    for name, url in alternatives.items():
        print(f"  • {name}")
        print(f"    {url}")
    
    # Method 3: Supabase Edge Function approach
    print("\n3. SUPABASE EDGE FUNCTION PROXY:")
    print("-" * 40)
    print("  We can create a Supabase Edge Function to:")
    print("  1. Fetch data from FTP (server-side, no CORS)")
    print("  2. Store in Supabase Storage")
    print("  3. Process and load into database")
    
    print("\n  Edge Function Code:")
    print("  " + "-" * 35)
    
    edge_function_code = '''
// supabase/functions/fetch-sunbiz/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const { data_type } = await req.json()
  
  // Fetch from FTP using Deno
  const ftpUrl = `ftp://ftp.dos.state.fl.us/public/doc/${data_type}/`
  
  try {
    // Download files
    const response = await fetch(ftpUrl)
    const data = await response.arrayBuffer()
    
    // Store in Supabase Storage
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )
    
    const { data: upload, error } = await supabase.storage
      .from('sunbiz-data')
      .upload(`${data_type}/data.txt`, data)
    
    return new Response(JSON.stringify({ success: true, upload }))
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }))
  }
})
'''
    
    print(edge_function_code)
    
    # Method 4: Using curl/wget through subprocess
    print("\n4. COMMAND LINE TOOLS:")
    print("-" * 40)
    print("  Install wget for Windows:")
    print("  1. Download: https://eternallybored.org/misc/wget/")
    print("  2. Add to PATH")
    print("  3. Run: wget --no-passive-ftp ftp://ftp.dos.state.fl.us/public/doc/off/")
    
    # Method 5: Python FTP with proxy
    print("\n5. PYTHON FTP WITH DIFFERENT SETTINGS:")
    print("-" * 40)
    
    print("  Try these FTP connection settings:")
    print("""
import ftplib
import ssl

# Try with different settings
ftp = ftplib.FTP_TLS()  # Use TLS
ftp.connect('ftp.dos.state.fl.us', 21)
ftp.login()  # Anonymous
ftp.prot_p()  # Enable protection
ftp.cwd('/public/doc')
ftp.retrlines('LIST')
    """)
    
    # Method 6: Direct database query
    print("\n6. QUERY SUPABASE FOR EXISTING DATA:")
    print("-" * 40)
    print("  Check if any users have already loaded this data:")
    
    from supabase import create_client
    
    supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Check if we have officer data
    try:
        # Check for any table that might have officer data
        tables_to_check = ['sunbiz_officers', 'sunbiz_directors', 'officers', 'directors']
        
        for table in tables_to_check:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                if result.data:
                    print(f"  ✅ Found table: {table}")
            except:
                pass
    except Exception as e:
        print(f"  No officer tables found in database")
    
    print("\n" + "=" * 60)
    print("RECOMMENDED APPROACH")
    print("=" * 60)
    
    print("\nOPTION A: Use Supabase Edge Function")
    print("-" * 40)
    print("1. Deploy edge function to fetch FTP data")
    print("2. Edge function runs server-side (no firewall issues)")
    print("3. Stores data in Supabase Storage")
    print("4. Process and load into database")
    print("\nDeploy command:")
    print("supabase functions deploy fetch-sunbiz")
    
    print("\nOPTION B: Use Cloud Server")
    print("-" * 40)
    print("1. Spin up a small EC2/Droplet/Cloud instance")
    print("2. Run wget from cloud server")
    print("3. Upload to Supabase Storage")
    print("4. Process with our existing loaders")
    
    print("\nOPTION C: Request from Florida")
    print("-" * 40)
    print("1. Contact: sunbiz@dos.myflorida.com")
    print("2. Request bulk data export with emails")
    print("3. Many researchers get special access")
    
    return True

if __name__ == "__main__":
    check_access_methods()