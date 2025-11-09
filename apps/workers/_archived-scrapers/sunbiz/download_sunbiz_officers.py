"""
Download Sunbiz Officers/Directors data with emails
Uses multiple methods to bypass FTP restrictions
"""

import os
import sys
import io
import requests
import subprocess
from pathlib import Path
import json
from datetime import datetime

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SunbizDataDownloader:
    """Download missing Sunbiz data with contact info"""
    
    def __init__(self):
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def method1_wget(self):
        """Method 1: Use wget if available"""
        print("\n" + "=" * 60)
        print("METHOD 1: WGET DOWNLOAD")
        print("=" * 60)
        
        # Check if wget is installed
        try:
            result = subprocess.run(['wget', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ wget is installed")
                
                # Download commands
                commands = [
                    ('off', 'wget -r -np -nH --cut-dirs=3 -P "{}" ftp://ftp.dos.state.fl.us/public/doc/off/'),
                    ('annual', 'wget -r -np -nH --cut-dirs=3 -P "{}" ftp://ftp.dos.state.fl.us/public/doc/annual/'),
                    ('llc', 'wget -r -np -nH --cut-dirs=3 -P "{}" ftp://ftp.dos.state.fl.us/public/doc/llc/'),
                    ('AG', 'wget -r -np -nH --cut-dirs=3 -P "{}" ftp://ftp.dos.state.fl.us/public/doc/AG/')
                ]
                
                print("\nRun these commands to download:")
                for data_type, cmd in commands:
                    target_dir = self.base_path / data_type
                    print(f"\n{data_type} data:")
                    print(cmd.format(target_dir))
                    
        except FileNotFoundError:
            print("❌ wget not installed")
            print("\nTo install wget on Windows:")
            print("1. Download from: https://eternallybored.org/misc/wget/")
            print("2. Extract wget.exe to C:\\Windows\\System32")
            print("3. Restart terminal and try again")
    
    def method2_curl(self):
        """Method 2: Use curl (usually available on Windows 10+)"""
        print("\n" + "=" * 60)
        print("METHOD 2: CURL DOWNLOAD")
        print("=" * 60)
        
        try:
            result = subprocess.run(['curl', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ curl is installed")
                
                # Create download script
                script_content = """
@echo off
echo Downloading Sunbiz Officers data...

REM Download Officers/Directors (most likely to have emails)
curl -o officers_list.txt ftp://ftp.dos.state.fl.us/public/doc/off/
curl -o annual_list.txt ftp://ftp.dos.state.fl.us/public/doc/annual/

echo.
echo Check *_list.txt files for available data files
echo Then download specific files with:
echo curl -o filename.txt ftp://ftp.dos.state.fl.us/public/doc/off/filename.txt
"""
                
                script_path = self.base_path / "download_sunbiz.bat"
                with open(script_path, 'w') as f:
                    f.write(script_content)
                
                print(f"\n✅ Created download script: {script_path}")
                print("Run it with: cd TEMP\\DATABASE\\doc && download_sunbiz.bat")
                
        except FileNotFoundError:
            print("❌ curl not installed")
    
    def method3_python_requests(self):
        """Method 3: Try HTTP mirrors"""
        print("\n" + "=" * 60)
        print("METHOD 3: HTTP MIRRORS")
        print("=" * 60)
        
        # Check known HTTP mirrors
        mirrors = [
            "http://ftp.dos.state.fl.us/public/doc/",
            "http://199.242.69.68/public/doc/",  # Direct IP
            "http://floridasunbiz.gov/data/",
        ]
        
        for mirror in mirrors:
            try:
                print(f"\nTrying: {mirror}")
                response = requests.get(mirror + "off/", timeout=5)
                if response.status_code == 200:
                    print(f"✅ SUCCESS! Found working mirror: {mirror}")
                    print("\nDownloading file list...")
                    
                    # Parse directory listing
                    if "Index of" in response.text or "<a href=" in response.text:
                        print("Directory listing available!")
                        # Save for analysis
                        list_file = self.base_path / "off_directory_listing.html"
                        with open(list_file, 'w') as f:
                            f.write(response.text)
                        print(f"Saved to: {list_file}")
                        break
                else:
                    print(f"❌ Status {response.status_code}")
            except Exception as e:
                print(f"❌ Failed: {e}")
    
    def method4_supabase_proxy(self):
        """Method 4: Use Supabase as proxy"""
        print("\n" + "=" * 60)
        print("METHOD 4: SUPABASE EDGE FUNCTION")
        print("=" * 60)
        
        print("Create Supabase Edge Function to fetch data:")
        print("-" * 40)
        
        # Create edge function file
        edge_func = """
// Save this as: supabase/functions/fetch-sunbiz/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const { data_type, filename } = await req.json()
  
  const ftpUrl = filename 
    ? `ftp://ftp.dos.state.fl.us/public/doc/${data_type}/${filename}`
    : `ftp://ftp.dos.state.fl.us/public/doc/${data_type}/`
  
  try {
    // Use alternative method - HTTP mirror
    const httpUrl = ftpUrl.replace('ftp://', 'http://')
    const response = await fetch(httpUrl)
    
    if (response.ok) {
      const data = await response.text()
      
      // Check for emails
      const emailCount = (data.match(/@/g) || []).length
      
      return new Response(JSON.stringify({
        success: true,
        data_type,
        filename,
        size: data.length,
        emailCount,
        sample: data.substring(0, 1000)
      }))
    }
    
    return new Response(JSON.stringify({
      error: 'Failed to fetch',
      status: response.status
    }))
    
  } catch (error) {
    return new Response(JSON.stringify({
      error: error.message
    }))
  }
})
"""
        
        func_path = self.base_path / "fetch-sunbiz-function.ts"
        with open(func_path, 'w') as f:
            f.write(edge_func)
        
        print(f"✅ Created edge function: {func_path}")
        print("\nDeploy with:")
        print("1. supabase functions new fetch-sunbiz")
        print("2. Copy the function code")
        print("3. supabase functions deploy fetch-sunbiz")
        print("\nThen call with:")
        print("curl -X POST https://pmispwtdngkcmsrsjwbp.supabase.co/functions/v1/fetch-sunbiz \\")
        print('  -H "Authorization: Bearer YOUR_ANON_KEY" \\')
        print('  -d \'{"data_type": "off"}\'')
    
    def method5_alternative_sources(self):
        """Method 5: Alternative data sources"""
        print("\n" + "=" * 60)
        print("METHOD 5: ALTERNATIVE SOURCES")
        print("=" * 60)
        
        print("\n1. OpenCorporates API (has some officer emails):")
        print("-" * 40)
        print("API: https://api.opencorporates.com/")
        print("Docs: https://api.opencorporates.com/documentation/API-Reference")
        print("\nExample:")
        
        # Try OpenCorporates
        try:
            url = "https://api.opencorporates.com/v0.4/companies/search"
            params = {
                "q": "LLC",
                "jurisdiction_code": "us_fl",
                "per_page": 5
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('results', {}).get('companies'):
                    print("✅ OpenCorporates API works!")
                    print(f"Found {data['results']['total_count']} Florida companies")
                    
                    # Check first company for officers
                    first_company = data['results']['companies'][0]['company']
                    company_num = first_company['company_number']
                    
                    # Get company details
                    detail_url = f"https://api.opencorporates.com/v0.4/companies/us_fl/{company_num}"
                    detail_response = requests.get(detail_url, timeout=10)
                    
                    if detail_response.status_code == 200:
                        details = detail_response.json()
                        if details.get('results', {}).get('company', {}).get('officers'):
                            print("✅ Officer data available!")
        except Exception as e:
            print(f"OpenCorporates error: {e}")
        
        print("\n2. Florida Department of State API:")
        print("-" * 40)
        print("Contact: sunbiz@dos.myflorida.com")
        print("Request bulk data access with contact information")
        
        print("\n3. Data.gov:")
        print("-" * 40)
        print("Search: https://catalog.data.gov/dataset?q=florida+business+email")
        
        print("\n4. GitHub Datasets:")
        print("-" * 40)
        print("Search: https://github.com/search?q=florida+sunbiz+officers")
        
    def run_all_methods(self):
        """Try all download methods"""
        print("=" * 60)
        print("SUNBIZ OFFICERS/EMAIL DATA DOWNLOADER")
        print("=" * 60)
        print(f"Target directory: {self.base_path}")
        
        self.method1_wget()
        self.method2_curl()
        self.method3_python_requests()
        self.method4_supabase_proxy()
        self.method5_alternative_sources()
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("\n📧 To get email data, you need the /off/ directory")
        print("This contains Officers/Directors information")
        print("\nBest options:")
        print("1. Install wget and use Method 1")
        print("2. Deploy Supabase Edge Function (Method 4)")
        print("3. Use OpenCorporates API for some data (Method 5)")
        print("4. Email sunbiz@dos.myflorida.com for bulk access")

if __name__ == "__main__":
    downloader = SunbizDataDownloader()
    downloader.run_all_methods()