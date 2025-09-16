"""
Create Sunbiz Cloud Tables in Supabase
This creates the necessary tables for the cloud-native daily update system
"""

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection from environment
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Try to construct from individual components
    host = os.getenv('SUPABASE_DB_HOST')
    database = os.getenv('SUPABASE_DB_NAME', 'postgres')
    user = os.getenv('SUPABASE_DB_USER', 'postgres')
    password = os.getenv('SUPABASE_DB_PASSWORD')
    port = os.getenv('SUPABASE_DB_PORT', '5432')
    
    if host and password:
        DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    else:
        print("ERROR: Database connection details not found in environment variables")
        exit(1)

def create_tables():
    """Create necessary tables for Sunbiz cloud updates"""
    
    conn = None
    cursor = None
    
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Create florida_daily_processed_files table
        print("Creating florida_daily_processed_files table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS florida_daily_processed_files (
                id SERIAL PRIMARY KEY,
                file_name VARCHAR(255) UNIQUE NOT NULL,
                file_type VARCHAR(50),
                file_date DATE,
                records_processed INTEGER DEFAULT 0,
                entities_created INTEGER DEFAULT 0,
                entities_updated INTEGER DEFAULT 0,
                processing_time_seconds FLOAT,
                processed_at TIMESTAMP DEFAULT NOW(),
                status VARCHAR(50) DEFAULT 'completed',
                error_message TEXT
            )
        """)
        
        # Create sunbiz_supervisor_status table
        print("Creating sunbiz_supervisor_status table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sunbiz_supervisor_status (
                id SERIAL PRIMARY KEY,
                status VARCHAR(50) NOT NULL,
                last_update TIMESTAMP DEFAULT NOW(),
                metrics JSONB,
                error_log JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes for performance
        print("Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_processed_files_date 
            ON florida_daily_processed_files(file_date DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_supervisor_status_created 
            ON sunbiz_supervisor_status(created_at DESC)
        """)
        
        # Commit changes
        conn.commit()
        print("✅ All tables created successfully!")
        
        # Verify tables
        print("\nVerifying tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('florida_daily_processed_files', 'sunbiz_supervisor_status')
        """)
        
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if florida_entities table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'florida_entities'
            )
        """)
        
        if cursor.fetchone()[0]:
            print("✅ florida_entities table already exists")
        else:
            print("⚠️  florida_entities table does not exist (will be created by edge function)")
        
        print("\n✅ Database setup complete for cloud-native Sunbiz updates!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_tables()