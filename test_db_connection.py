"""
Test database connection to Supabase
"""

import os
import asyncio
import asyncpg
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

async def test_connection():
    database_url = os.getenv('DATABASE_URL')
    print(f"Testing connection to Supabase...")
    print(f"URL structure: {database_url[:40]}...")
    
    # Try direct connection with the full URL
    try:
        print("\nAttempting direct connection...")
        conn = await asyncpg.connect(database_url)
        version = await conn.fetchval('SELECT version()')
        print(f"✓ Connected successfully!")
        print(f"PostgreSQL version: {version[:50]}...")
        
        # Test table creation
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                test_time TIMESTAMP DEFAULT NOW()
            )
        """)
        print("✓ Table creation successful")
        
        # Clean up
        await conn.execute("DROP TABLE IF EXISTS test_connection")
        await conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Direct connection failed: {e}")
        
        # Try parsing the URL manually
        print("\nTrying manual parsing...")
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(database_url)
        print(f"Host: {parsed.hostname}")
        print(f"Port: {parsed.port}")
        print(f"User: {parsed.username}")
        print(f"Database: {parsed.path[1:] if parsed.path else 'postgres'}")
        
        # Check for special parameters
        params = parse_qs(parsed.query)
        print(f"Parameters: {params}")
        
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())