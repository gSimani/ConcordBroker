"""
Test Supabase connection with psycopg2
"""

import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

def test_connection():
    database_url = os.getenv('DATABASE_URL')
    print(f"Testing Supabase connection with psycopg2...")
    
    # Remove the supa parameter that psycopg2 doesn't understand
    if '&supa=' in database_url:
        database_url = database_url.split('&supa=')[0]
    
    print(f"Cleaned URL: {database_url[:50]}...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Test query
        cur.execute("SELECT version()")
        version = cur.fetchone()
        print(f"Connected successfully!")
        print(f"PostgreSQL version: {version[0][:50]}...")
        
        # Test table creation
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dor_properties (
                id BIGSERIAL PRIMARY KEY,
                folio VARCHAR(30) UNIQUE,
                county VARCHAR(50),
                year INTEGER,
                owner_name TEXT,
                situs_address_1 TEXT,
                situs_city VARCHAR(100),
                just_value NUMERIC(15,2),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        print("Table 'dor_properties' created/verified")
        
        # Check if table exists
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'dor_properties'
        """)
        count = cur.fetchone()[0]
        print(f"Table exists: {count > 0}")
        
        # Check current row count
        cur.execute("SELECT COUNT(*) FROM dor_properties")
        row_count = cur.fetchone()[0]
        print(f"Current rows in dor_properties: {row_count}")
        
        cur.close()
        conn.close()
        
        print("\nConnection successful! Ready to load data.")
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()