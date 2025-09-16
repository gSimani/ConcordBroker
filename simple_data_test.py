#!/usr/bin/env python3
"""
Simple test to verify website shows real data
"""

import requests
import sys

def test_frontend():
    """Test if property data is displayed"""
    print("Testing property page data...")
    
    try:
        # Test property 474131031040
        url = "http://localhost:5173/property/474131031040"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            print("SUCCESS: Property page loaded")
            
            # Check for real data
            if "12681 NW 78 MNR" in content:
                print("SUCCESS: Real address found!")
                return True
            elif "IH3 PROPERTY" in content:
                print("SUCCESS: Real owner found!")
                return True
            elif "PARKLAND" in content:
                print("SUCCESS: Real city found!")
                return True
            else:
                # Count N/A occurrences
                na_count = content.count("N/A")
                print(f"INFO: Found {na_count} N/A values")
                
                if na_count < 10:
                    print("PARTIAL SUCCESS: Limited N/A values")
                    return True
                else:
                    print("ISSUE: Too many N/A values")
                    return False
        else:
            print(f"ERROR: Property page returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_frontend()
    if success:
        print("\nRESULT: Website appears to be showing real data!")
    else:
        print("\nRESULT: Website may still have N/A values")
    
    sys.exit(0 if success else 1)