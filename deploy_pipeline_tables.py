"""
Deploy data pipeline tables to Supabase
"""

import os
import psycopg2
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def deploy_pipeline_tables():
    # Get database URL and clean it
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("[ERROR] DATABASE_URL not found in environment variables")
        sys.exit(1)
        
    # Fix the URL format (remove supa parameter)
    if '&supa=' in db_url:
        db_url = db_url.split('&supa=')[0]
    elif '?supa=' in db_url:
        db_url = db_url.split('?supa=')[0]
    
    print("[INFO] Connecting to database...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("[SUCCESS] Connected to database")
        print("[INFO] Creating data pipeline tables...")
        
        # Read and execute SQL file
        with open('setup_pipeline_tables.sql', 'r') as f:
            sql_content = f.read()
        
        # Execute the entire SQL content
        cursor.execute(sql_content)
        
        print("[SUCCESS] Pipeline tables created")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name LIKE 'fl_%'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n[INFO] Data pipeline tables in database:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} records")
        
        # Check agent status
        cursor.execute("SELECT agent_name, agent_type, is_enabled FROM fl_agent_status ORDER BY agent_name")
        agents = cursor.fetchall()
        
        print(f"\n[INFO] Configured agents:")
        for agent in agents:
            status = "Enabled" if agent[2] else "Disabled"
            print(f"  - {agent[0]} ({agent[1]}): {status}")
        
        cursor.close()
        conn.close()
        
        print("\n[SUCCESS] Data pipeline tables deployed successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to deploy pipeline tables: {e}")
        return False

if __name__ == "__main__":
    deploy_pipeline_tables()