"""
Execute the SQL population script via Supabase
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL') or os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: Supabase credentials not found")
    exit(1)

print(f"Connecting to Supabase: {SUPABASE_URL}")

# Headers for API requests
headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def execute_sql_file():
    """Execute the SQL file via RPC"""
    print("\nExecuting SQL population script...")
    if os.getenv('SUPABASE_ENABLE_SQL', 'false').lower() != 'true':
        print("Direct SQL execution is disabled. Set SUPABASE_ENABLE_SQL=true to enable vetted RPC execution.")
        print("Recommended: run SQL via Supabase dashboard or psql with admin credentials.")
        return False
    
    # Read the SQL file
    try:
        with open('populate_database.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except FileNotFoundError:
        print("Error: populate_database.sql not found")
        return False
    
    # Split into individual statements (simple split by semicolon)
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
    
    print(f"Found {len(statements)} SQL statements to execute")
    
    success_count = 0
    error_count = 0
    
    # Execute each statement via RPC
    for i, statement in enumerate(statements):
        if not statement:
            continue
            
        print(f"Executing statement {i+1}/{len(statements)}...")
        
        # Use Supabase RPC to execute SQL
        url = f"{SUPABASE_URL}/rest/v1/rpc/execute_sql"
        payload = {"sql": statement}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code in [200, 201, 204]:
                success_count += 1
                if i < 10:  # Show first 10 for debugging
                    print(f"  ✓ Success")
            else:
                error_count += 1
                print(f"  ✗ Error {response.status_code}: {response.text}")
                if "execute_sql" in response.text:
                    print("  Note: RPC function 'execute_sql' may not exist")
                    return False
        except Exception as e:
            error_count += 1
            print(f"  ✗ Exception: {e}")
    
    print(f"\nSQL Execution Summary:")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {error_count}")
    
    return error_count == 0

def verify_data():
    """Verify data was inserted"""
    print("\nVerifying data insertion...")
    
    # Check properties
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=*"
    headers_count = headers.copy()
    headers_count['Prefer'] = 'count=exact'
    
    try:
        response = requests.get(url, headers=headers_count)
        if response.status_code == 200:
            count = response.headers.get('content-range', '').split('/')[-1]
            properties = response.json()
            print(f"Properties in database: {count}")
            
            if properties:
                print("Sample properties:")
                for prop in properties[:3]:
                    print(f"  - {prop.get('phy_addr1', 'N/A')}, {prop.get('phy_city', 'N/A')}")
            
            return int(count) if count.isdigit() else 0
        else:
            print(f"Failed to verify properties: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Error verifying data: {e}")
        return 0

def main():
    """Main function"""
    print("POPULATING CONCORDBROKER DATABASE VIA SQL SCRIPT")
    print("=" * 60)
    
    # Execute SQL script
    sql_success = execute_sql_file()
    
    if not sql_success:
        print("\nSQL execution failed. Trying direct data insertion...")
        # Fall back to direct REST API insertion (simplified)
        insert_sample_data()
    
    # Verify
    property_count = verify_data()
    
    print("\n" + "=" * 60)
    if property_count > 0:
        print("DATABASE POPULATED SUCCESSFULLY!")
        print(f"{property_count} properties available")
        print("\nYour website should now display properties at:")
        print("   http://localhost:5174/properties")
        print("\nTry searching for:")
        print("   - 3930 (should suggest '3930 Bayview Drive')")
        print("   - Ocean Boulevard")
        print("   - Fort Lauderdale")
    else:
        print("DATABASE POPULATION INCOMPLETE")
        print("Manual SQL execution in Supabase dashboard may be required")
    print("=" * 60)

def insert_sample_data():
    """Fallback: Insert minimal sample data directly"""
    print("\nFallback: Inserting sample data directly...")
    
    # Minimal property data
    properties = [
        {
            'parcel_id': '10-42-35-4500-1200',
            'county': 'BROWARD',
            'year': 2025,
            'phy_addr1': '3930 Bayview Drive',
            'phy_city': 'Fort Lauderdale',
            'phy_state': 'FL',
            'phy_zipcd': '33308',
            'owner_name': 'Bayview Estates LLC',
            'just_value': 695000,
            'assessed_value': 625500,
            'taxable_value': 556000
        }
    ]
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    
    try:
        response = requests.post(url, json=properties, headers=headers)
        if response.status_code in [200, 201]:
            print(f"Successfully inserted {len(properties)} properties")
            return True
        else:
            print(f"Failed to insert properties: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error inserting properties: {e}")
        return False

if __name__ == "__main__":
    main()
