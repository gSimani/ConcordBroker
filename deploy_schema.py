"""
Deploy Florida Business Database Schema to Supabase
"""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def deploy_schema():
    """Deploy the Florida business schema to Supabase"""
    
    # Get database URL and clean it
    db_url = os.getenv('DATABASE_URL')
    if '&supa=' in db_url:
        db_url = db_url.split('&supa=')[0]
    elif '?supa=' in db_url:
        db_url = db_url.split('?supa=')[0]
    
    print(f"Deploying Florida Business Schema to Supabase")
    print(f"Connecting to database...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print(f"Connected successfully!")
        
        # Enable required extensions first
        print(f"Enabling required extensions...")
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            print(f"pgvector extension enabled!")
        except Exception as e:
            print(f"Warning: Could not enable pgvector extension: {e}")
            print(f"Continuing without vector support...")
        
        # Read schema file
        schema_file = Path("florida_business_schema.sql")
        if not schema_file.exists():
            print(f"Schema file not found: {schema_file}")
            return False
        
        print(f"Reading schema from: {schema_file}")
        schema_sql = schema_file.read_text(encoding='utf-8')
        
        # Execute schema
        print(f"Executing schema deployment...")
        cursor.execute(schema_sql)
        
        print(f"Schema deployed successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 'florida_%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"\nCreated Tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Create vector similarity function if needed
        print(f"\nSetting up vector search...")
        try:
            cursor.execute("""
                CREATE OR REPLACE FUNCTION match_documents (
                    query_embedding vector(1536),
                    match_threshold float,
                    match_count int
                )
                RETURNS table (
                    entity_id text,
                    raw_content text,
                    similarity float
                )
                LANGUAGE sql STABLE
                AS $$
                    SELECT 
                        entity_id,
                        raw_content,
                        1 - (embedding <=> query_embedding) as similarity
                    FROM florida_raw_records
                    WHERE 1 - (embedding <=> query_embedding) > match_threshold
                    ORDER BY similarity DESC
                    LIMIT match_count;
                $$;
            """)
            print(f"Vector search function created!")
        except Exception as e:
            print(f"Vector function setup (optional): {e}")
        
        return True
        
    except Exception as e:
        print(f"Schema deployment failed: {e}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = deploy_schema()
    if success:
        print(f"\nSchema deployment completed successfully!")
        print(f"Ready to start uploading Florida business data.")
    else:
        print(f"\nSchema deployment failed. Check errors above.")