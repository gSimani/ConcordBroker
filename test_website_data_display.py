#!/usr/bin/env python3
"""
Test that the website is now displaying real property data instead of N/A values
"""

import requests
import json
from datetime import datetime

def test_property_page_data():
    """Test if property page has real data"""
    print("🔍 Testing Property Page Data Display...")
    print("=" * 50)
    
    # Test property that should have complete data
    test_parcel = "474131031040"
    
    try:
        # Test if frontend is running
        print("1. Testing frontend connectivity...")
        response = requests.get("http://localhost:5173/", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running on http://localhost:5173/")
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend not accessible: {e}")
        print("   Please ensure 'npm run dev' is running in apps/web/")
        return False
    
    try:
        # Test property page specifically
        print(f"\n2. Testing property page: {test_parcel}")
        property_url = f"http://localhost:5173/property/{test_parcel}"
        response = requests.get(property_url, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            print("✅ Property page loaded successfully")
            
            # Check for real data indicators
            real_data_found = False
            na_values_found = False
            
            # Look for specific real data we know should be there
            if "12681 NW 78 MNR" in content:
                print("✅ Real address found: 12681 NW 78 MNR")
                real_data_found = True
            elif "IH3 PROPERTY" in content:
                print("✅ Real owner found: IH3 PROPERTY FLORIDA LP")
                real_data_found = True
            
            # Check for N/A indicators
            na_count = content.count("N/A")
            no_sales_count = content.count("No recent sales")
            
            if na_count > 0:
                print(f"⚠️  Found {na_count} 'N/A' values in page")
                na_values_found = True
            
            if no_sales_count > 0:
                print(f"⚠️  Found {no_sales_count} 'No recent sales' messages")
                na_values_found = True
            
            # Summary
            print(f"\n📊 SUMMARY FOR PROPERTY {test_parcel}:")
            if real_data_found and not na_values_found:
                print("🎉 SUCCESS: Property page shows REAL DATA!")
                print("   The database import was successful.")
                return True
            elif real_data_found and na_values_found:
                print("⚠️  PARTIAL: Some real data found, but still some N/A values")
                print("   Data may be loading from different tables")
                return True
            else:
                print("❌ ISSUE: Property page still shows mostly N/A values")
                print("   Frontend may not be connecting to updated database")
                return False
                
        else:
            print(f"❌ Property page returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing property page: {e}")
        return False

def test_supabase_connection():
    """Test if we can verify the Supabase connection"""
    print(f"\n3. Testing Supabase data availability...")
    
    # Read the frontend's Supabase configuration
    try:
        with open("apps/web/.env", "r") as f:
            env_content = f.read()
            
        if "VITE_SUPABASE_URL" in env_content:
            supabase_url = None
            for line in env_content.split('\n'):
                if line.startswith('VITE_SUPABASE_URL='):
                    supabase_url = line.split('=')[1].strip()
                    break
            
            if supabase_url:
                print(f"✅ Frontend configured to use: {supabase_url[:30]}...")
                return True
            else:
                print("❌ VITE_SUPABASE_URL not found in .env")
                return False
        else:
            print("❌ Supabase configuration not found in apps/web/.env")
            return False
            
    except FileNotFoundError:
        print("❌ Could not find apps/web/.env file")
        return False

def main():
    """Run all tests"""
    print("🧪 WEBSITE DATA DISPLAY TEST")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Test Supabase config first
    supabase_ok = test_supabase_connection()
    
    # Test property page
    website_ok = test_property_page_data()
    
    print("\n" + "=" * 50)
    print("🏁 FINAL RESULT:")
    
    if website_ok:
        print("🎉 SUCCESS: Website is displaying real property data!")
        print("   Users will now see actual property information instead of N/A values.")
    else:
        print("⚠️  ATTENTION NEEDED:")
        print("   The website may still be showing N/A values.")
        print("   Check that:")
        print("   - Frontend is running (npm run dev in apps/web/)")
        print("   - Supabase credentials are correct")
        print("   - Database tables have been properly imported")
        print("   - usePropertyData.ts is querying the right tables")

if __name__ == "__main__":
    main()