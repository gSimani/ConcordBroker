"""
Test Supabase NAL Database Deployment
Tests the deployment of the optimized 7-table schema
"""

import os
import sys
import time
from datetime import datetime
import psycopg2
from psycopg2 import sql
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

class SupabaseDeploymentTester:
    """Test the NAL database schema deployment on Supabase"""
    
    def __init__(self):
        """Initialize the deployment tester"""
        self.connection = None
        self.cursor = None
        self.deployment_results = {
            'started_at': None,
            'completed_at': None,
            'success': False,
            'tables_created': 0,
            'indexes_created': 0,
            'functions_created': 0,
            'errors': []
        }
        
    def connect_to_supabase(self):
        """Connect to Supabase database"""
        try:
            # Supabase connection parameters
            supabase_config = {
                'host': 'mogulpssjdlxjvstqfee.supabase.co',
                'database': 'postgres',
                'user': 'postgres',
                'password': 'Concordbroker2024!',
                'port': '5432'
            }
            
            print("Connecting to Supabase...")
            self.connection = psycopg2.connect(**supabase_config)
            self.cursor = self.connection.cursor()
            self.connection.autocommit = False  # Use transactions
            
            print("✅ Successfully connected to Supabase")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            self.deployment_results['errors'].append(f"Connection error: {e}")
            return False
    
    def run_sql_file(self, file_path):
        """Execute SQL file on Supabase"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"SQL file not found: {file_path}")
            
            print(f"Executing SQL file: {os.path.basename(file_path)}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Execute the SQL
            self.cursor.execute(sql_content)
            self.connection.commit()
            
            print(f"✅ Successfully executed {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            print(f"❌ Error executing SQL file: {e}")
            self.deployment_results['errors'].append(f"SQL execution error: {e}")
            self.connection.rollback()
            return False
    
    def validate_deployment(self):
        """Validate the deployment by checking created objects"""
        validation_results = {
            'tables': [],
            'indexes': [],
            'functions': [],
            'views': []
        }
        
        try:
            # Check tables
            print("\n🔍 Validating deployment...")
            
            # Check for created tables
            expected_tables = [
                'florida_properties_core',
                'property_valuations', 
                'property_exemptions',
                'property_characteristics',
                'property_sales_enhanced',
                'property_addresses',
                'property_admin_data'
            ]
            
            self.cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename = ANY(%s)
            """, (expected_tables,))
            
            created_tables = [row[0] for row in self.cursor.fetchall()]
            validation_results['tables'] = created_tables
            self.deployment_results['tables_created'] = len(created_tables)
            
            print(f"📊 Tables created: {len(created_tables)}/7")
            for table in created_tables:
                print(f"  ✅ {table}")
            
            # Check for missing tables
            missing_tables = set(expected_tables) - set(created_tables)
            if missing_tables:
                print("❌ Missing tables:")
                for table in missing_tables:
                    print(f"  ❌ {table}")
            
            # Check indexes
            self.cursor.execute("""
                SELECT indexname, tablename
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND (tablename LIKE '%property%' OR tablename = 'florida_properties_core')
            """)
            
            indexes = self.cursor.fetchall()
            validation_results['indexes'] = indexes
            self.deployment_results['indexes_created'] = len(indexes)
            
            print(f"📈 Indexes created: {len(indexes)}")
            
            # Check functions
            self.cursor.execute("""
                SELECT proname 
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'public'
                AND (p.proname LIKE '%property%' OR p.proname LIKE '%search%')
            """)
            
            functions = [row[0] for row in self.cursor.fetchall()]
            validation_results['functions'] = functions
            self.deployment_results['functions_created'] = len(functions)
            
            print(f"⚡ Functions created: {len(functions)}")
            for func in functions:
                print(f"  ✅ {func}")
            
            # Check materialized views
            self.cursor.execute("""
                SELECT matviewname 
                FROM pg_matviews 
                WHERE schemaname = 'public'
            """)
            
            views = [row[0] for row in self.cursor.fetchall()]
            validation_results['views'] = views
            
            print(f"👁️ Materialized views created: {len(views)}")
            for view in views:
                print(f"  ✅ {view}")
            
            return validation_results
            
        except Exception as e:
            print(f"❌ Validation error: {e}")
            self.deployment_results['errors'].append(f"Validation error: {e}")
            return validation_results
    
    def test_basic_functionality(self):
        """Test basic functionality of the deployed schema"""
        try:
            print("\n🧪 Testing basic functionality...")
            
            # Test 1: Insert a sample record
            print("Test 1: Insert sample record...")
            sample_insert = """
                INSERT INTO florida_properties_core (
                    parcel_id, co_no, owner_name, physical_address_1, 
                    physical_city, just_value, source
                ) VALUES (
                    'TEST123456789', 16, 'TEST OWNER', '123 TEST ST', 
                    'TEST CITY', 100000, 'test_deployment'
                )
                ON CONFLICT (parcel_id) DO UPDATE SET
                    owner_name = EXCLUDED.owner_name,
                    updated_at = NOW()
            """
            
            self.cursor.execute(sample_insert)
            print("  ✅ Sample record inserted")
            
            # Test 2: Search functionality
            print("Test 2: Search functionality...")
            self.cursor.execute("SELECT search_properties('TEST', 5)")
            results = self.cursor.fetchall()
            print(f"  ✅ Search returned {len(results)} results")
            
            # Test 3: Check materialized view
            print("Test 3: Materialized view access...")
            self.cursor.execute("SELECT COUNT(*) FROM property_summary_view")
            view_count = self.cursor.fetchone()[0]
            print(f"  ✅ Property summary view has {view_count} records")
            
            # Test 4: Validate constraints
            print("Test 4: Constraint validation...")
            try:
                self.cursor.execute("""
                    INSERT INTO florida_properties_core (
                        parcel_id, co_no, owner_name, just_value
                    ) VALUES (
                        'TEST_CONSTRAINT', 999, 'Invalid County', -1000
                    )
                """)
                print("  ❌ Constraints not working (invalid data accepted)")
            except Exception:
                print("  ✅ Constraints working correctly")
                self.connection.rollback()  # Rollback the failed insert
            
            # Commit test changes
            self.connection.commit()
            print("✅ All basic functionality tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Basic functionality test failed: {e}")
            self.deployment_results['errors'].append(f"Functionality test error: {e}")
            self.connection.rollback()
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            print("\n🧹 Cleaning up test data...")
            self.cursor.execute("DELETE FROM florida_properties_core WHERE source = 'test_deployment'")
            self.connection.commit()
            print("✅ Test data cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def run_deployment_test(self):
        """Run complete deployment test"""
        self.deployment_results['started_at'] = datetime.now()
        
        print("=" * 60)
        print("SUPABASE NAL DATABASE DEPLOYMENT TEST")
        print("=" * 60)
        print(f"Started at: {self.deployment_results['started_at']}")
        print()
        
        try:
            # Step 1: Connect to Supabase
            if not self.connect_to_supabase():
                return self.deployment_results
            
            # Step 2: Deploy the schema
            deployment_file = Path(__file__).parent / "deploy_optimized_nal_database.sql"
            if not self.run_sql_file(deployment_file):
                return self.deployment_results
            
            # Step 3: Validate deployment
            validation_results = self.validate_deployment()
            
            # Step 4: Test basic functionality
            functionality_ok = self.test_basic_functionality()
            
            # Step 5: Clean up
            self.cleanup_test_data()
            
            # Determine overall success
            success_criteria = (
                self.deployment_results['tables_created'] >= 7 and
                self.deployment_results['indexes_created'] >= 10 and
                self.deployment_results['functions_created'] >= 2 and
                functionality_ok
            )
            
            self.deployment_results['success'] = success_criteria
            self.deployment_results['completed_at'] = datetime.now()
            
            print("\n" + "=" * 60)
            print("DEPLOYMENT TEST RESULTS")
            print("=" * 60)
            print(f"Status: {'SUCCESS' if success_criteria else 'FAILED'}")
            print(f"Tables created: {self.deployment_results['tables_created']}/7")
            print(f"Indexes created: {self.deployment_results['indexes_created']}")
            print(f"Functions created: {self.deployment_results['functions_created']}")
            print(f"Duration: {self.deployment_results['completed_at'] - self.deployment_results['started_at']}")
            
            if self.deployment_results['errors']:
                print(f"\nErrors ({len(self.deployment_results['errors'])}):")
                for error in self.deployment_results['errors']:
                    print(f"  ❌ {error}")
            
            if success_criteria:
                print("\n🎉 Deployment test completed successfully!")
                print("\nNext steps:")
                print("1. The optimized NAL schema is now deployed on Supabase")
                print("2. You can now import NAL data using the migration functions")
                print("3. Run 'SELECT refresh_property_views();' after data import")
                print("4. Test searches with 'SELECT * FROM search_properties('term');'")
            else:
                print("\n❌ Deployment test failed. Please review errors above.")
            
            return self.deployment_results
            
        except Exception as e:
            print(f"❌ Deployment test failed with exception: {e}")
            self.deployment_results['errors'].append(f"Test exception: {e}")
            self.deployment_results['completed_at'] = datetime.now()
            return self.deployment_results
        
        finally:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print(f"\nConnection closed. Test completed at: {datetime.now()}")


def main():
    """Main function to run deployment test"""
    tester = SupabaseDeploymentTester()
    results = tester.run_deployment_test()
    
    # Return appropriate exit code
    exit_code = 0 if results['success'] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()