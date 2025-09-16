"""
Analyze the existing Florida parcels data to understand what we have
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import httpx
import json

# Fix proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

load_dotenv(override=True)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client = create_client(url, key)

print("ANALYZING EXISTING FLORIDA PARCELS DATA")
print("=" * 80)

# 1. Check florida_parcels structure
print("\n1. FLORIDA_PARCELS TABLE STRUCTURE:")
print("-" * 80)

try:
    # Get a sample record to see columns
    sample = client.table('florida_parcels').select('*').limit(1).execute()
    if sample.data:
        columns = list(sample.data[0].keys())
        print(f"Total columns: {len(columns)}")
        print("\nColumn names:")
        for i, col in enumerate(columns, 1):
            print(f"  {i:2}. {col}")
        
        # Check for UI-required columns
        print("\n2. CHECKING UI-REQUIRED COLUMNS:")
        print("-" * 80)
        
        required_columns = {
            'parcel_id': 'Primary identifier',
            'phy_addr1': 'Physical address line 1',
            'phy_city': 'City',
            'phy_zipcd': 'Zip code',
            'owner_name': 'Owner name',
            'assessed_value': 'Assessed value',
            'taxable_value': 'Taxable value',
            'just_value': 'Just/Market value',
            'year_built': 'Year built',
            'bedrooms': 'Number of bedrooms',
            'bathrooms': 'Number of bathrooms',
            'living_area': 'Living area sq ft',
            'property_type': 'Property type'
        }
        
        missing_columns = []
        found_columns = []
        
        for col, description in required_columns.items():
            if col in columns:
                found_columns.append(col)
                print(f"  ✓ {col}: {description}")
            else:
                missing_columns.append(col)
                print(f"  ✗ {col}: {description} [MISSING]")
        
        # Check sample data
        print("\n3. SAMPLE DATA:")
        print("-" * 80)
        sample_data = sample.data[0]
        for key in ['parcel_id', 'county', 'owner_name', 'property_address']:
            if key in sample_data:
                value = sample_data[key]
                print(f"  {key}: {value}")
        
        # Get data distribution
        print("\n4. DATA DISTRIBUTION:")
        print("-" * 80)
        
        # Count by county
        county_counts = client.table('florida_parcels').select('county', count='exact').execute()
        print(f"  Total records: {county_counts.count if hasattr(county_counts, 'count') else 'Unknown'}")
        
        # Try to get a specific Broward property
        print("\n5. TESTING BROWARD PROPERTY SEARCH:")
        print("-" * 80)
        
        # Search for properties in Broward
        broward_test = client.table('florida_parcels').select('*').eq('county', '06').limit(5).execute()
        if broward_test.data:
            print(f"  Found {len(broward_test.data)} Broward properties")
            for prop in broward_test.data[:2]:
                print(f"\n  Property: {prop.get('parcel_id', 'N/A')}")
                print(f"    Address: {prop.get('property_address', 'N/A')}")
                print(f"    Owner: {prop.get('owner_name', 'N/A')}")
        else:
            # Try different county code
            broward_test2 = client.table('florida_parcels').select('*').eq('county', 'BROWARD').limit(5).execute()
            if broward_test2.data:
                print(f"  Found {len(broward_test2.data)} Broward properties (using 'BROWARD')")
            else:
                print("  No Broward properties found")
        
        # Check what the UI expects vs what we have
        print("\n6. UI COMPATIBILITY ANALYSIS:")
        print("-" * 80)
        
        ui_mapping = {
            'UI expects': 'Database has',
            'phy_addr1': 'property_address' if 'property_address' in columns else 'MISSING',
            'phy_city': 'city' if 'city' in columns else 'MISSING',
            'phy_zipcd': 'zip' if 'zip' in columns else 'MISSING',
            'owner_name': 'owner_name' if 'owner_name' in columns else 'MISSING',
            'assessed_value': 'av_nsd' if 'av_nsd' in columns else 'MISSING',
            'taxable_value': 'tv_nsd' if 'tv_nsd' in columns else 'MISSING',
            'just_value': 'jv' if 'jv' in columns else 'MISSING'
        }
        
        print("\nColumn Mapping Needed:")
        for ui_col, db_col in ui_mapping.items():
            if ui_col != 'UI expects':
                status = "✓" if db_col != 'MISSING' else "✗"
                print(f"  {status} UI: {ui_col:15} -> DB: {db_col}")
        
        # Save analysis
        analysis = {
            'total_columns': len(columns),
            'columns': columns,
            'missing_ui_columns': missing_columns,
            'found_ui_columns': found_columns,
            'sample_record': sample.data[0],
            'ui_mapping_needed': ui_mapping
        }
        
        with open('florida_parcels_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\n7. RECOMMENDATIONS:")
        print("-" * 80)
        
        if missing_columns:
            print("The database HAS data but needs column mapping!")
            print("\nOptions:")
            print("1. Create a VIEW that maps existing columns to UI names")
            print("2. Add missing columns to the table")
            print("3. Update the UI code to use existing column names")
            print("\nI'll create a migration script to fix this...")
        else:
            print("Database structure matches UI requirements!")
            print("The app should work with the existing data.")
            
except Exception as e:
    print(f"Error analyzing florida_parcels: {str(e)}")

# Check other tables
print("\n" + "=" * 80)
print("OTHER TABLES STATUS:")
print("-" * 80)

other_tables = ['properties', 'property_sales_history', 'nav_assessments', 'sunbiz_corporate']
for table in other_tables:
    try:
        result = client.table(table).select('*', count='exact', head=True).execute()
        count = result.count if hasattr(result, 'count') else 0
        print(f"  {table}: {count} rows")
        
        if count > 0:
            sample = client.table(table).select('*').limit(1).execute()
            if sample.data:
                cols = list(sample.data[0].keys())
                print(f"    Columns: {', '.join(cols[:5])}...")
    except:
        print(f"  {table}: ERROR or doesn't exist")