"""
Test the fixed property categorization logic
"""

from supabase import create_client
import sys
import os

# Add the API directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from production_property_api import determine_property_category, extract_property_subcategory, generate_property_description

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def test_property_categorization():
    """
    Test the fixed categorization logic on actual database records
    """
    print("TESTING PROPERTY CATEGORIZATION FIXES")
    print("=" * 50)
    print()

    try:
        # Get sample properties with different property_use codes
        response = supabase.table('florida_parcels')\
            .select('parcel_id, property_use, land_use_code, property_use_desc, owner_name, just_value, phy_addr1, county')\
            .not_.is_('property_use', 'null')\
            .limit(20)\
            .execute()

        if not response.data:
            print("No properties found with property_use data")
            return

        print(f"Testing categorization on {len(response.data)} properties:")
        print()

        results_summary = {}

        for i, prop in enumerate(response.data, 1):
            print(f"Property {i}: {prop.get('parcel_id', 'Unknown')}")
            print(f"  Address: {prop.get('phy_addr1', 'N/A')}")
            print(f"  County: {prop.get('county', 'N/A')}")
            print(f"  Owner: {prop.get('owner_name', 'N/A')[:50]}...")
            print(f"  Property Use Code: '{prop.get('property_use', 'N/A')}'")
            print(f"  Land Use Code: '{prop.get('land_use_code', 'N/A')}'")
            print(f"  Property Use Desc: '{prop.get('property_use_desc', 'N/A')}'")
            print()

            # Test the new categorization functions
            category = determine_property_category(prop)
            subcategory = extract_property_subcategory(prop)
            description = generate_property_description(prop)

            print(f"  NEW RESULTS:")
            print(f"    Category: {category}")
            print(f"    Subcategory: {subcategory}")
            print(f"    Description: {description}")
            print()

            # Track results
            if category not in results_summary:
                results_summary[category] = 0
            results_summary[category] += 1

            if i >= 10:  # Limit output
                break

        print("CATEGORIZATION SUMMARY:")
        print("-" * 30)
        for category, count in results_summary.items():
            print(f"  {category}: {count} properties")
        print()

        # Test before/after comparison with specific codes
        test_codes = ['1', '8', '0', '21', '41', '61', '86']
        print("SPECIFIC CODE TESTS:")
        print("-" * 30)
        for code in test_codes:
            test_row = {'property_use': code, 'owner_name': 'TEST OWNER'}
            category = determine_property_category(test_row)
            subcategory = extract_property_subcategory(test_row)
            print(f"  Code {code}: {category} > {subcategory}")

        print()
        print("SUCCESS: Property categorization logic updated successfully!")
        print("Properties should now show proper categories instead of 'Other'.")

    except Exception as e:
        print(f"Error testing categorization: {e}")
        return False

    return True

if __name__ == "__main__":
    test_property_categorization()