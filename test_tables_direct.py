#!/usr/bin/env python3
"""
Direct SQL test for Property Appraiser tables
"""

import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Parse database URL
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
if not DATABASE_URL:
    print("No database URL found in environment")
    exit(1)

# Parse the URL
parsed = urlparse(DATABASE_URL)
db_config = {
    'host': parsed.hostname,
    'port': parsed.port or 5432,
    'database': parsed.path[1:],  # Remove leading '/'
    'user': parsed.username,
    'password': parsed.password
}

print("Testing direct database connection...")
print("=" * 60)

try:
    # Connect to database
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    # Check tables exist
    cur.execute("""
        SELECT table_name, 
               (SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = t.table_name) as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'public' 
          AND table_name IN (
            'property_assessments',
            'property_owners',
            'property_sales',
            'nav_summaries',
            'nav_details',
            'properties_master'
          )
        ORDER BY table_name;
    """)
    
    results = cur.fetchall()
    
    if results:
        print("✅ Tables successfully created:")
        print("-" * 40)
        for table, cols in results:
            print(f"  • {table}: {cols} columns")
    else:
        print("❌ No tables found - please run the schema SQL first")
    
    # Close connection
    cur.close()
    conn.close()
    
    print("\n✅ Database connection successful!")
    print("\nNext step: Run python property_appraiser_supabase_loader.py")
    
except Exception as e:
    print(f"Error: {e}")