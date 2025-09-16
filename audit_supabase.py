"""
Complete Supabase Database Audit Script
Tests connection and audits all database components
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()

class SupabaseAuditor:
    def __init__(self):
        # Get database URL and clean it
        self.db_url = os.getenv('DATABASE_URL')
        
        if not self.db_url:
            print("ERROR: DATABASE_URL not found in environment variables")
            sys.exit(1)
            
        # Fix the URL format (remove supa parameter)
        if '&supa=' in self.db_url:
            self.db_url = self.db_url.split('&supa=')[0]
        elif '?supa=' in self.db_url:
            self.db_url = self.db_url.split('?supa=')[0]
            
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        try:
            print("[INFO] Connecting to Supabase database...")
            self.conn = psycopg2.connect(self.db_url)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("[SUCCESS] Successfully connected to database")
            return True
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False
    
    def audit_tables(self):
        """Audit all tables in the database"""
        print("\nDATABASE TABLES AUDIT")
        print("=" * 60)
        
        query = """
        SELECT 
            schemaname as schema,
            tablename as table_name,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, tablename;
        """
        
        try:
            self.cursor.execute(query)
            tables = self.cursor.fetchall()
            
            if tables:
                table_data = []
                for table in tables:
                    # Get row count
                    count_query = f"SELECT COUNT(*) FROM {table['schema']}.{table['table_name']}"
                    try:
                        self.cursor.execute(count_query)
                        count = self.cursor.fetchone()['count']
                    except:
                        count = 'N/A'
                    
                    table_data.append([
                        table['schema'],
                        table['table_name'],
                        count,
                        table['size']
                    ])
                
                print(tabulate(table_data, headers=['Schema', 'Table', 'Rows', 'Size'], tablefmt='grid'))
                return len(tables)
            else:
                print("[WARNING] No tables found in database")
                return 0
                
        except Exception as e:
            print(f"[ERROR] Error auditing tables: {e}")
            return 0
    
    def check_expected_tables(self):
        """Check for expected tables based on schema files"""
        print("\nCHECKING EXPECTED TABLES")
        print("=" * 60)
        
        expected_tables = {
            'Florida Parcels': [
                'florida_parcels',
                'florida_condo_units',
                'data_source_monitor',
                'parcel_update_history',
                'monitoring_agents',
                'agent_activity_logs'
            ],
            'Sunbiz Business': [
                'sunbiz_corporate',
                'sunbiz_corporate_events',
                'sunbiz_fictitious',
                'sunbiz_fictitious_events',
                'sunbiz_liens',
                'sunbiz_lien_debtors',
                'sunbiz_partnerships'
            ],
            'Entity Matching': [
                'property_entity_matches',
                'entity_relationships',
                'property_ownership_history',
                'match_audit_log',
                'entity_search_cache'
            ],
            'Data Pipeline': [
                'fl_tpp_accounts',
                'fl_nav_parcel_summary',
                'fl_nav_assessment_detail',
                'fl_sdf_sales',
                'fl_data_updates',
                'fl_agent_status'
            ]
        }
        
        results = {}
        
        for category, tables in expected_tables.items():
            print(f"\n{category}:")
            for table in tables:
                query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
                """
                self.cursor.execute(query, (table,))
                exists = self.cursor.fetchone()['exists']
                
                if exists:
                    # Get row count
                    self.cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = self.cursor.fetchone()['count']
                    status = f"[EXISTS] ({count} rows)"
                else:
                    status = "[MISSING]"
                
                print(f"  {table:40} {status}")
                results[table] = exists
        
        return results
    
    def check_indexes(self):
        """Check database indexes"""
        print("\nDATABASE INDEXES")
        print("=" * 60)
        
        query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size
        FROM pg_indexes
        JOIN pg_stat_user_indexes ON indexrelname = indexname
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname;
        """
        
        try:
            self.cursor.execute(query)
            indexes = self.cursor.fetchall()
            
            if indexes:
                current_table = None
                for idx in indexes:
                    if idx['tablename'] != current_table:
                        current_table = idx['tablename']
                        print(f"\n{current_table}:")
                    print(f"  - {idx['indexname']} ({idx['index_size']})")
            else:
                print("[WARNING] No indexes found")
                
        except Exception as e:
            print(f"[ERROR] Error checking indexes: {e}")
    
    def check_views(self):
        """Check database views"""
        print("\nDATABASE VIEWS")
        print("=" * 60)
        
        query = """
        SELECT 
            schemaname,
            viewname
        FROM pg_views
        WHERE schemaname = 'public'
        ORDER BY viewname;
        """
        
        try:
            self.cursor.execute(query)
            views = self.cursor.fetchall()
            
            if views:
                for view in views:
                    print(f"  - {view['viewname']}")
            else:
                print("[WARNING] No views found")
                
        except Exception as e:
            print(f"[ERROR] Error checking views: {e}")
    
    def check_data_freshness(self):
        """Check data freshness"""
        print("\nDATA FRESHNESS CHECK")
        print("=" * 60)
        
        freshness_queries = {
            'fl_data_updates': "SELECT source_type, MAX(update_date) as last_update FROM fl_data_updates GROUP BY source_type",
            'monitoring_agents': "SELECT agent_name, last_run, next_run FROM monitoring_agents",
            'florida_parcels': "SELECT MAX(import_date) as last_import FROM florida_parcels"
        }
        
        for table, query in freshness_queries.items():
            try:
                self.cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                if self.cursor.fetchone()['exists']:
                    print(f"\n{table}:")
                    self.cursor.execute(query)
                    results = self.cursor.fetchall()
                    for row in results:
                        print(f"  {dict(row)}")
                else:
                    print(f"\n{table}: Table not found")
            except Exception as e:
                print(f"\n{table}: Error - {e}")
    
    def generate_summary(self):
        """Generate audit summary"""
        print("\nAUDIT SUMMARY")
        print("=" * 60)
        
        # Database size
        self.cursor.execute("SELECT pg_database_size(current_database())")
        db_size = self.cursor.fetchone()['pg_database_size']
        db_size_mb = db_size / (1024 * 1024)
        
        # Table count
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = self.cursor.fetchone()['count']
        
        # Total rows
        self.cursor.execute("""
            SELECT SUM(n_live_tup) as total_rows
            FROM pg_stat_user_tables
        """)
        total_rows = self.cursor.fetchone()['total_rows'] or 0
        
        print(f"Database Size: {db_size_mb:.2f} MB")
        print(f"Total Tables: {table_count}")
        print(f"Total Rows: {total_rows:,}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def run_audit(self):
        """Run complete audit"""
        if not self.connect():
            return False
        
        try:
            table_count = self.audit_tables()
            
            if table_count > 0:
                self.check_expected_tables()
                self.check_indexes()
                self.check_views()
                self.check_data_freshness()
            
            self.generate_summary()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Audit error: {e}")
            return False
            
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
                print("\n[INFO] Database connection closed")

if __name__ == "__main__":
    print("SUPABASE DATABASE AUDIT")
    print("=" * 60)
    
    auditor = SupabaseAuditor()
    success = auditor.run_audit()
    
    if success:
        print("\nAUDIT COMPLETED SUCCESSFULLY")
    else:
        print("\nAUDIT FAILED")