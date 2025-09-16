import os
from dotenv import load_dotenv
from supabase import create_client
import json

# Load environment variables
load_dotenv()

def check_supabase():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("Missing Supabase credentials")
        return
    
    print(f"Connecting to Supabase...")
    print(f"URL: {url}")
    
    try:
        # Create Supabase client - correct way
        client = create_client(url, key)
        
        # List all tables
        print("\n=== CHECKING TABLES ===")
        
        # Try to query some known tables
        tables_to_check = [
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
        
        existing_tables = []
        
        for table in tables_to_check:
            try:
                result = client.table(table).select('*').limit(1).execute()
                count = len(result.data) if result.data else 0
                existing_tables.append(table)
                print(f"  [EXISTS] {table} - Sample record found: {count > 0}")
            except Exception as e:
                error_str = str(e)
                if "relation" in error_str.lower() or "does not exist" in error_str.lower():
                    print(f"  [MISSING] {table}")
                else:
                    print(f"  [ERROR] {table} - {error_str[:50]}")
        
        # Get record counts for existing tables
        if existing_tables:
            print("\n=== TABLE RECORD COUNTS ===")
            for table in existing_tables:
                try:
                    # Count records
                    result = client.table(table).select('id', count='exact').execute()
                    count = result.count if hasattr(result, 'count') else len(result.data)
                    print(f"  {table}: {count} records")
                except Exception as e:
                    print(f"  {table}: Error getting count")
        
        # Check monitoring agents status
        print("\n=== MONITORING AGENTS STATUS ===")
        try:
            agents = client.table('monitoring_agents').select('*').execute()
            if agents.data:
                for agent in agents.data:
                    status = "Enabled" if agent.get('enabled') else "Disabled"
                    print(f"  {agent.get('agent_name')}: {status}")
            else:
                print("  No monitoring agents found")
        except:
            print("  Monitoring agents table not accessible")
        
        # Check recent updates
        print("\n=== RECENT DATA UPDATES ===")
        try:
            updates = client.table('fl_data_updates').select('*').order('update_date', desc=True).limit(5).execute()
            if updates.data:
                for update in updates.data:
                    print(f"  {update.get('source_type')} - {update.get('update_date')} - {update.get('records_processed')} records")
            else:
                print("  No recent updates found")
        except:
            print("  Updates table not accessible")
            
        print("\n=== SUPABASE CONNECTION SUCCESSFUL ===")
        return True
        
    except Exception as e:
        print(f"\nError connecting to Supabase: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_supabase()