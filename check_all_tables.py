import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_database():
    # Get database URL
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("Missing DATABASE_URL")
        return
        
    # Remove the supa parameter if present
    if '&supa=' in db_url:
        db_url = db_url.split('&supa=')[0]
    elif '?supa=' in db_url:
        db_url = db_url.split('?supa=')[0]
    
    print("Connecting to database...")
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Check all tables in public schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print("\n=== EXISTING TABLES ===")
            for table in tables:
                table_name = table[0]
                
                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  {table_name}: {count} records")
                except:
                    print(f"  {table_name}: (system table)")
        else:
            print("\n=== NO TABLES FOUND ===")
            print("The database appears to be empty.")
        
        # Check database size
        cursor.execute("SELECT pg_database_size(current_database())")
        size = cursor.fetchone()[0]
        size_mb = size / (1024 * 1024)
        print(f"\n=== DATABASE SIZE: {size_mb:.2f} MB ===")
        
        cursor.close()
        conn.close()
        
        print("\n=== CONNECTION SUCCESSFUL ===")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_database()