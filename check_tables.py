import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.mcp')

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
anon_key = os.environ.get("SUPABASE_ANON_KEY")
service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Try service key first, then anon key
key = service_key if service_key else anon_key

if not url or not key:
    print("ERROR: Missing Supabase credentials in .env.mcp")
    exit(1)

print(f"Connecting to Supabase...")
print(f"URL: {url}")

supabase: Client = create_client(url, key)

# Try to query system tables to get a list of all tables
try:
    # Method 1: Try direct SQL query
    print("\nAttempting to list all tables...")

    # First, let's try to access the User table which we know exists
    print("\n1. Testing with User table:")
    result = supabase.table('User').select("*").limit(1).execute()
    if result.data:
        print(f"   - User table exists with {len(result.data)} sample record(s)")

    # Try different table names
    tables_to_test = [
        # Original expected names
        'florida_parcels',
        'properties',
        'property_sales',
        'sales_history',

        # Possible alternative names
        'Properties',
        'Property',
        'Parcels',
        'Sales',
        'PropertySales',
        'SalesHistory',
        'TaxDeeds',
        'tax_deeds',

        # Florida specific
        'florida_properties',
        'fl_parcels',
        'fl_properties',
        'broward_properties',
        'miami_dade_properties',

        # Generic names
        'listings',
        'real_estate',
        'realestate',
        'parcels_data',
        'property_data',

        # User related
        'user_properties',
        'UserProperties',
        'user_listings',

        # Other possible tables
        'contacts',
        'notes',
        'alerts',
        'watchlist',
        'favorites'
    ]

    print("\n2. Checking for property-related tables:")
    found_tables = []

    for table_name in tables_to_test:
        try:
            result = supabase.table(table_name).select("*", count='exact').limit(0).execute()
            count = result.count if hasattr(result, 'count') else 0
            if count >= 0:  # Table exists if no error
                found_tables.append((table_name, count))
                print(f"   FOUND: {table_name} - {count:,} records")
        except Exception as e:
            # Table doesn't exist or error accessing it
            pass

    # Summary
    print("\n" + "="*60)
    print("SUMMARY OF FOUND TABLES")
    print("="*60)

    if found_tables:
        total_records = 0
        print("\nProperty-Related Tables Found:")
        for table_name, count in sorted(found_tables, key=lambda x: x[1], reverse=True):
            print(f"  - {table_name}: {count:,} records")
            total_records += count

        print(f"\nTotal Records Across All Tables: {total_records:,}")

        # Get sample from largest table
        if found_tables:
            largest_table = sorted(found_tables, key=lambda x: x[1], reverse=True)[0]
            if largest_table[1] > 0:
                print(f"\nSample from largest table ({largest_table[0]}):")
                sample = supabase.table(largest_table[0]).select("*").limit(1).execute()
                if sample.data:
                    print(f"Columns: {', '.join(sample.data[0].keys())}")
    else:
        print("\nNo property-related tables found in the database.")
        print("The database may be empty or tables may have different names.")

    # Save results
    results = {
        "tables_found": [{"name": name, "count": count} for name, count in found_tables],
        "total_tables": len(found_tables),
        "total_records": sum(count for _, count in found_tables)
    }

    with open('table_discovery_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to: table_discovery_results.json")

except Exception as e:
    print(f"\nError during table discovery: {str(e)}")
    import traceback
    traceback.print_exc()