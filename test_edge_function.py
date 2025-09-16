"""
Test Supabase Edge Function for Sunbiz data
Quick test to verify Edge Function is working
"""

import requests
import json

def test_edge_function():
    """Test the Edge Function deployment"""
    
    print("=" * 60)
    print("TESTING SUPABASE EDGE FUNCTION")
    print("=" * 60)
    
    # Configuration
    edge_url = "https://pmispwtdngkcmsrsjwbp.supabase.co/functions/v1/fetch-sunbiz"
    anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU0OTEyNjQsImV4cCI6MjA0MTA2NzI2NH0.2uYtqSu7tb-umJmDx5kGFOHHLzMO0LlNvFxB8L_C-tE"
    
    headers = {
        'Authorization': f'Bearer {anon_key}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: List officer files
    print("\n1. Testing LIST action for officer files...")
    print("-" * 40)
    
    payload = {
        'action': 'list',
        'data_type': 'off'
    }
    
    try:
        response = requests.post(edge_url, headers=headers, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ SUCCESS! Found {data.get('file_count', 0)} files")
                
                # Show first 5 files
                files = data.get('files', [])[:5]
                if files:
                    print("\nSample files:")
                    for f in files:
                        print(f"  - {f.get('filename')} ({f.get('type')})")
                        
                    # Test 2: Download first file
                    first_file = files[0]['filename']
                    print(f"\n2. Testing DOWNLOAD action for {first_file}...")
                    print("-" * 40)
                    
                    download_payload = {
                        'action': 'download',
                        'data_type': 'off',
                        'filename': first_file
                    }
                    
                    dl_response = requests.post(edge_url, headers=headers, json=download_payload, timeout=60)
                    print(f"Status: {dl_response.status_code}")
                    
                    if dl_response.status_code == 200:
                        dl_data = dl_response.json()
                        if dl_data.get('success'):
                            print(f"✅ File downloaded successfully!")
                            print(f"  Size: {dl_data.get('size', 0):,} bytes")
                            print(f"  📧 Emails found: {dl_data.get('emailCount', 0)}")
                            print(f"  📞 Phones found: {dl_data.get('phoneCount', 0)}")
                            print(f"  Storage path: {dl_data.get('storagePath')}")
                        else:
                            print(f"❌ Download failed: {dl_data}")
                    else:
                        print(f"❌ Download request failed: {dl_response.text}")
                        
            else:
                print(f"❌ List failed: {data}")
        else:
            print(f"❌ Request failed: {response.text}")
            
            # Check if function exists
            if response.status_code == 404:
                print("\n⚠️ Edge Function not found!")
                print("Deploy it with: ./deploy_sunbiz_edge_function.ps1")
            elif response.status_code == 401:
                print("\n⚠️ Authentication failed!")
                print("Check your anon key in the script")
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out - Edge Function may not be deployed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\nIf the Edge Function is working:")
    print("✅ Run: python sunbiz_edge_pipeline_loader.py")
    print("   This will download all officer data with emails")
    print("\nIf the Edge Function is NOT working:")
    print("1. Deploy it: powershell ./deploy_sunbiz_edge_function.ps1")
    print("2. Or use alternative: python download_sunbiz_officers.py")

if __name__ == "__main__":
    test_edge_function()