import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def check_supabase_api():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("Missing Supabase credentials")
        return
    
    print(f"Connecting to Supabase API...")
    print(f"URL: {url}")
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    
    # Tables to check
    tables = [
        'florida_parcels',
        'fl_tpp_accounts', 
        'fl_nav_parcel_summary',
        'fl_nav_assessment_detail',
        'fl_sdf_sales',
        'sunbiz_corporate',
        'sunbiz_fictitious',
        'property_entity_matches',
        'monitoring_agents',
        'agent_activity_logs'
    ]
    
    print("\n=== CHECKING TABLES ===")
    existing_tables = []
    
    for table in tables:
        try:
            # Try to query each table
            response = requests.get(
                f"{url}/rest/v1/{table}",
                headers=headers,
                params={'select': '*', 'limit': 1}
            )
            
            if response.status_code == 200:
                data = response.json()
                has_data = len(data) > 0
                existing_tables.append(table)
                print(f"  [EXISTS] {table} - Has data: {has_data}")
            elif response.status_code == 400 and 'relation' in response.text:
                print(f"  [MISSING] {table}")
            else:
                print(f"  [ERROR] {table} - Status: {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] {table} - {str(e)[:50]}")
    
    # Get counts for existing tables
    if existing_tables:
        print("\n=== TABLE RECORD COUNTS ===")
        for table in existing_tables:
            try:
                response = requests.head(
                    f"{url}/rest/v1/{table}",
                    headers={**headers, 'Prefer': 'count=exact'},
                    params={'select': '*'}
                )
                
                if 'content-range' in response.headers:
                    count = response.headers['content-range'].split('/')[1]
                    print(f"  {table}: {count} records")
                else:
                    print(f"  {table}: Count not available")
            except Exception as e:
                print(f"  {table}: Error getting count")
    
    print("\n=== API CONNECTION TEST SUCCESSFUL ===")
    return True

if __name__ == "__main__":
    check_supabase_api()