"""
Check the status of pipeline agents and recent data loads
"""

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
from tabulate import tabulate

# Load environment variables
load_dotenv()

def check_pipeline_status():
    # Get database URL and clean it
    db_url = os.getenv('DATABASE_URL')
    if '&supa=' in db_url:
        db_url = db_url.split('&supa=')[0]
    elif '?supa=' in db_url:
        db_url = db_url.split('?supa=')[0]
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("="*70)
        print("CONCORDBROKER PIPELINE STATUS")
        print("="*70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check agent status
        print("\n[AGENT STATUS]")
        cursor.execute("""
            SELECT 
                agent_name,
                agent_type,
                is_enabled,
                is_running,
                current_status,
                last_run_start,
                last_run_status,
                next_scheduled_run
            FROM fl_agent_status
            ORDER BY agent_name
        """)
        
        agents = cursor.fetchall()
        agent_data = []
        for agent in agents:
            enabled = "Yes" if agent[2] else "No"
            running = "Running" if agent[3] else "Idle"
            last_run = agent[5].strftime('%m/%d %H:%M') if agent[5] else "Never"
            next_run = agent[7].strftime('%m/%d %H:%M') if agent[7] else "Not scheduled"
            status = agent[6] or "pending"
            
            agent_data.append([
                agent[0],
                agent[1],
                enabled,
                running,
                status,
                last_run,
                next_run
            ])
        
        print(tabulate(agent_data, 
                      headers=['Agent', 'Type', 'Enabled', 'Running', 'Status', 'Last Run', 'Next Run'],
                      tablefmt='grid'))
        
        # Check recent data updates
        print("\n[RECENT DATA UPDATES]")
        cursor.execute("""
            SELECT 
                source_type,
                update_date,
                records_processed,
                records_added,
                records_updated,
                status
            FROM fl_data_updates
            ORDER BY update_date DESC
            LIMIT 10
        """)
        
        updates = cursor.fetchall()
        if updates:
            update_data = []
            for update in updates:
                update_data.append([
                    update[0],
                    update[1].strftime('%m/%d %H:%M'),
                    update[2] or 0,
                    update[3] or 0,
                    update[4] or 0,
                    update[5]
                ])
            
            print(tabulate(update_data,
                          headers=['Source', 'Update Time', 'Processed', 'Added', 'Updated', 'Status'],
                          tablefmt='grid'))
        else:
            print("No data updates recorded yet")
        
        # Check data counts in main tables
        print("\n[DATA TABLES STATUS]")
        tables_to_check = [
            ('florida_parcels', 'Property parcels'),
            ('fl_tpp_accounts', 'TPP accounts'),
            ('fl_nav_parcel_summary', 'NAV assessments'),
            ('fl_sdf_sales', 'Sales records'),
            ('sunbiz_corporate', 'Business entities'),
            ('property_entity_matches', 'Property-entity matches')
        ]
        
        table_data = []
        for table_name, description in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Get last update
            if table_name in ['florida_parcels', 'fl_tpp_accounts', 'fl_nav_parcel_summary', 'fl_sdf_sales']:
                cursor.execute(f"""
                    SELECT MAX(import_date) 
                    FROM {table_name}
                """)
                last_update = cursor.fetchone()[0]
                last_update_str = last_update.strftime('%m/%d %H:%M') if last_update else "No data"
            else:
                last_update_str = "N/A"
            
            table_data.append([table_name, description, f"{count:,}", last_update_str])
        
        print(tabulate(table_data,
                      headers=['Table', 'Description', 'Records', 'Last Update'],
                      tablefmt='grid'))
        
        # Check for any errors
        cursor.execute("""
            SELECT agent_name, last_error
            FROM fl_agent_status
            WHERE last_error IS NOT NULL
            LIMIT 5
        """)
        
        errors = cursor.fetchall()
        if errors:
            print("\n[RECENT ERRORS]")
            for error in errors:
                print(f"  {error[0]}: {error[1][:100]}...")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("[INFO] Pipeline status check complete")
        
    except Exception as e:
        print(f"[ERROR] Failed to check status: {e}")

if __name__ == "__main__":
    check_pipeline_status()