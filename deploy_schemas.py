"""
Deploy all database schemas to Supabase
This script creates all necessary tables for ConcordBroker
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

class SchemaDeployer:
    def __init__(self):
        # Get database URL and clean it
        self.db_url = os.getenv('DATABASE_URL')
        
        if not self.db_url:
            print("[ERROR] DATABASE_URL not found in environment variables")
            sys.exit(1)
            
        # Fix the URL format (remove supa parameter)
        if '&supa=' in self.db_url:
            self.db_url = self.db_url.split('&supa=')[0]
        elif '?supa=' in self.db_url:
            self.db_url = self.db_url.split('?supa=')[0]
            
        self.conn = None
        self.cursor = None
        
        # Schema files to deploy
        self.schema_files = [
            'apps/api/supabase_schema.sql',
            'apps/api/sunbiz_schema.sql',
            'apps/api/entity_matching_schema.sql'
        ]
    
    def connect(self):
        """Establish database connection"""
        try:
            print("[INFO] Connecting to Supabase database...")
            self.conn = psycopg2.connect(self.db_url)
            self.conn.autocommit = True  # Important for DDL statements
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("[SUCCESS] Connected to database")
            return True
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False
    
    def deploy_schema_file(self, filepath):
        """Deploy a single schema file"""
        print(f"\n[INFO] Deploying {filepath}...")
        
        if not os.path.exists(filepath):
            print(f"[ERROR] File not found: {filepath}")
            return False
        
        try:
            # Read the SQL file
            with open(filepath, 'r') as f:
                sql_content = f.read()
            
            # Split into individual statements
            statements = self.split_sql_statements(sql_content)
            
            success_count = 0
            error_count = 0
            
            for i, statement in enumerate(statements, 1):
                if statement.strip():
                    try:
                        # Execute the statement
                        self.cursor.execute(statement)
                        
                        # Try to extract what was created
                        stmt_lower = statement.lower()
                        if 'create table' in stmt_lower:
                            # Extract table name
                            parts = statement.split()
                            for j, part in enumerate(parts):
                                if part.lower() in ['table', 'table if not exists']:
                                    if j + 1 < len(parts):
                                        table_name = parts[j + 1].strip('(').replace('"', '')
                                        print(f"  [OK] Created table: {table_name}")
                                        break
                        elif 'create index' in stmt_lower:
                            print(f"  [OK] Created index")
                        elif 'create view' in stmt_lower or 'create or replace view' in stmt_lower:
                            print(f"  [OK] Created view")
                        elif 'create function' in stmt_lower or 'create or replace function' in stmt_lower:
                            print(f"  [OK] Created function")
                        elif 'create trigger' in stmt_lower:
                            print(f"  [OK] Created trigger")
                        elif 'create policy' in stmt_lower:
                            print(f"  [OK] Created policy")
                        elif 'insert into' in stmt_lower:
                            print(f"  [OK] Inserted data")
                        elif 'grant' in stmt_lower:
                            print(f"  [OK] Granted permissions")
                        elif 'alter table' in stmt_lower:
                            print(f"  [OK] Altered table")
                        elif 'create extension' in stmt_lower:
                            print(f"  [OK] Created extension")
                        
                        success_count += 1
                        
                    except psycopg2.errors.DuplicateTable:
                        print(f"  [SKIP] Table already exists")
                    except psycopg2.errors.DuplicateObject:
                        print(f"  [SKIP] Object already exists")
                    except Exception as e:
                        error_msg = str(e).replace('\n', ' ')
                        if 'already exists' in error_msg:
                            print(f"  [SKIP] Already exists")
                        else:
                            print(f"  [ERROR] Statement {i}: {error_msg[:100]}")
                            error_count += 1
            
            print(f"\n[SUMMARY] {filepath}:")
            print(f"  Success: {success_count} statements")
            print(f"  Errors: {error_count} statements")
            
            return error_count == 0
            
        except Exception as e:
            print(f"[ERROR] Failed to deploy {filepath}: {e}")
            return False
    
    def split_sql_statements(self, sql_content):
        """Split SQL content into individual statements"""
        # Remove comments but preserve SQL strings
        lines = []
        in_string = False
        string_char = None
        
        for line in sql_content.split('\n'):
            cleaned_line = ""
            i = 0
            while i < len(line):
                if not in_string:
                    # Check for comment start
                    if i < len(line) - 1 and line[i:i+2] == '--':
                        break  # Rest of line is comment
                    # Check for string start
                    if line[i] in ["'", '"']:
                        in_string = True
                        string_char = line[i]
                    cleaned_line += line[i]
                else:
                    # We're in a string
                    cleaned_line += line[i]
                    if line[i] == string_char:
                        # Check if it's escaped
                        if i == 0 or line[i-1] != '\\':
                            in_string = False
                            string_char = None
                i += 1
            
            if cleaned_line.strip():
                lines.append(cleaned_line)
        
        # Join lines and split by semicolon
        full_sql = ' '.join(lines)
        
        # Split statements (basic splitting, may need refinement)
        statements = []
        current = ""
        depth = 0  # Track parentheses depth
        
        for char in full_sql:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ';' and depth == 0:
                if current.strip():
                    statements.append(current.strip())
                current = ""
                continue
            current += char
        
        if current.strip():
            statements.append(current.strip())
        
        return statements
    
    def verify_tables(self):
        """Verify that tables were created"""
        print("\n[INFO] Verifying table creation...")
        
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name NOT IN ('schema_migrations')
        ORDER BY table_name;
        """
        
        self.cursor.execute(query)
        tables = self.cursor.fetchall()
        
        if tables:
            print(f"\n[SUCCESS] Created {len(tables)} tables:")
            for table in tables:
                print(f"  - {table['table_name']}")
        else:
            print("[WARNING] No tables found in public schema")
        
        return len(tables)
    
    def run_deployment(self):
        """Run complete deployment"""
        if not self.connect():
            return False
        
        try:
            print("\n" + "="*60)
            print("DEPLOYING DATABASE SCHEMAS")
            print("="*60)
            
            # Deploy each schema file
            for schema_file in self.schema_files:
                self.deploy_schema_file(schema_file)
            
            # Verify tables were created
            table_count = self.verify_tables()
            
            print("\n" + "="*60)
            print("DEPLOYMENT SUMMARY")
            print("="*60)
            print(f"Total tables created: {table_count}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Deployment failed: {e}")
            return False
            
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
                print("\n[INFO] Database connection closed")

if __name__ == "__main__":
    print("SUPABASE SCHEMA DEPLOYMENT")
    print("="*60)
    
    deployer = SchemaDeployer()
    success = deployer.run_deployment()
    
    if success:
        print("\n[SUCCESS] DEPLOYMENT COMPLETED SUCCESSFULLY")
        print("\nNext steps:")
        print("1. Run data loaders to populate tables")
        print("2. Start the orchestrator for continuous updates")
        print("3. Test the API endpoints")
    else:
        print("\n[ERROR] DEPLOYMENT FAILED")