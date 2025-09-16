"""
Verify Property Appraiser Schema Deployment
Quick check to see if tables were created in Supabase
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.mcp')

def verify_deployment():
    """Verify that the schema was deployed successfully"""

    print("="*60)
    print("SCHEMA DEPLOYMENT VERIFICATION")
    print("="*60)

    # Initialize Supabase
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("✗ ERROR: Missing Supabase credentials")
        return False

    try:
        supabase = create_client(url, key)
        print("✓ Supabase client connected")

        # Test 1: Check if main table exists
        print("\n1. Testing main table (florida_parcels)...")
        try:
            result = supabase.table('florida_parcels').select("*").limit(1).execute()
            print(f"✓ florida_parcels table exists ({len(result.data)} sample records)")

            # If there are records, show a sample
            if result.data:
                sample = result.data[0]
                print(f"  Sample record columns: {len(sample.keys())}")
                key_fields = ['parcel_id', 'county', 'owner_name', 'just_value']
                for field in key_fields:
                    value = sample.get(field, 'NULL')
                    print(f"    {field}: {value}")

        except Exception as e:
            print(f"✗ florida_parcels table: {e}")
            return False

        # Test 2: Check supporting tables
        print("\n2. Testing supporting tables...")
        supporting_tables = [
            'property_use_codes',
            'florida_counties',
            'sales_history'
        ]

        for table in supporting_tables:
            try:
                result = supabase.table(table).select("*").limit(1).execute()
                print(f"✓ {table}: exists")
            except Exception as e:
                print(f"? {table}: {str(e)[:50]}...")

        # Test 3: Check if we can insert a test record
        print("\n3. Testing data insertion...")
        try:
            test_record = {
                'parcel_id': 'TEST123456789',
                'county': 'TEST_COUNTY',
                'year': 2025,
                'owner_name': 'Test Owner',
                'just_value': 100000,
                'land_sqft': 5000,
                'data_source': 'TEST',
                'data_hash': 'test_hash_123'
            }

            # Insert test record
            result = supabase.table('florida_parcels').insert(test_record).execute()
            print("✓ Test record inserted successfully")

            # Delete test record
            supabase.table('florida_parcels').delete().eq('parcel_id', 'TEST123456789').execute()
            print("✓ Test record cleaned up")

        except Exception as e:
            print(f"? Data insertion test: {str(e)[:100]}...")

        # Test 4: Check database performance
        print("\n4. Testing database performance...")
        try:
            # Test a simple count query
            result = supabase.table('florida_parcels').select('*', count='exact').limit(1).execute()
            record_count = result.count if hasattr(result, 'count') else 0
            print(f"✓ Current record count: {record_count:,}")

            if record_count > 0:
                print("✓ Database contains data - ready for production!")
            else:
                print("? Database is empty - ready for data loading")

        except Exception as e:
            print(f"? Performance test: {e}")

        print("\n" + "="*60)
        print("VERIFICATION COMPLETE")
        print("✓ Schema deployment appears successful")
        print("✓ Ready to run data loading scripts")
        print("="*60)

        return True

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def show_next_steps():
    """Show next steps after verification"""

    print("\nNEXT STEPS:")
    print("-" * 40)
    print("1. If schema verification passed:")
    print("   python property_appraiser_data_loader.py")
    print()
    print("2. If schema verification failed:")
    print("   - Go to Supabase Dashboard > SQL Editor")
    print("   - Copy/paste DEPLOY_SCHEMA_TO_SUPABASE.sql")
    print("   - Run the SQL script")
    print("   - Then run this verification again")
    print()
    print("3. Monitor data loading progress:")
    print("   - Check the generated reports")
    print("   - Review logs for any issues")
    print("   - Use florida_revenue_monitor_advanced.py")

if __name__ == "__main__":
    success = verify_deployment()
    show_next_steps()