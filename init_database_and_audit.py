"""
Initialize Database and Run Complete Audit
Creates necessary tables if they don't exist and performs comprehensive audit
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
import httpx

# Fix proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

load_dotenv()

class DatabaseInitializer:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        print(f"Connecting to: {self.url}")
        
        if not self.url or not self.key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        
        self.client = create_client(self.url, self.key)
        self.existing_tables = []
        self.audit_results = {}
    
    def check_existing_tables(self):
        """Check which tables already exist"""
        print("\n" + "="*80)
        print("CHECKING EXISTING TABLES")
        print("="*80)
        
        # Comprehensive list of all possible tables
        all_tables = [
            # Core property tables
            'parcels', 'properties', 'florida_parcels', 'broward_parcels',
            
            # Sales
            'sales_history', 'florida_sales', 'sdf_sales',
            
            # Tax and financial
            'tax_certificates', 'property_tax_info', 'property_assessments',
            'property_valuations', 'florida_revenue', 'tpp_tangible',
            'nav_assessments', 'nap_parcels', 'nal_parcels',
            
            # Permits
            'building_permits', 'florida_permits',
            
            # Business entities
            'sunbiz_corporations', 'sunbiz_entities', 'entity_matching',
            'property_entities',
            
            # Ownership and tracking
            'property_owners', 'tracked_properties', 'user_alerts',
            'property_searches', 'property_profiles',
            
            # System tables
            'florida_nav', 'florida_nav_roll', 'broward_daily_index',
            
            # Florida specific prefixed tables
            'fl_parcels', 'fl_sales', 'fl_permits', 'fl_tax_info',
            'fl_tpp_accounts', 'fl_nav_parcel_summary', 
            'fl_nav_assessment_detail', 'fl_sdf_sales',
            'fl_data_updates', 'fl_agent_status'
        ]
        
        for table_name in all_tables:
            try:
                result = self.client.table(table_name).select('*', count='exact', head=True).execute()
                count = result.count if hasattr(result, 'count') else 0
                self.existing_tables.append({
                    'name': table_name,
                    'row_count': count,
                    'status': 'exists'
                })
                print(f"  [EXISTS] {table_name}: {count:,} rows")
            except Exception as e:
                error_msg = str(e)
                if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                    print(f"  [MISSING] {table_name}")
                else:
                    print(f"  [ERROR] {table_name}: {error_msg[:50]}")
        
        return self.existing_tables
    
    def create_core_tables_sql(self):
        """Generate SQL to create core tables"""
        sql_statements = []
        
        # 1. Main parcels table
        sql_statements.append("""
        CREATE TABLE IF NOT EXISTS parcels (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) UNIQUE NOT NULL,
            county_code VARCHAR(10),
            property_address TEXT,
            owner_name TEXT,
            owner_address TEXT,
            property_use_code VARCHAR(20),
            property_type VARCHAR(50),
            total_value DECIMAL(15,2),
            assessed_value DECIMAL(15,2),
            land_value DECIMAL(15,2),
            building_value DECIMAL(15,2),
            year_built INTEGER,
            living_area INTEGER,
            lot_size DECIMAL(10,2),
            bedrooms INTEGER,
            bathrooms DECIMAL(3,1),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """)
        
        # 2. Properties table (enhanced parcel data)
        sql_statements.append("""
        CREATE TABLE IF NOT EXISTS properties (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) REFERENCES parcels(parcel_id),
            property_name TEXT,
            property_description TEXT,
            zoning_code VARCHAR(20),
            neighborhood VARCHAR(100),
            school_district VARCHAR(100),
            latitude DECIMAL(10,7),
            longitude DECIMAL(10,7),
            features JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """)
        
        # 3. Sales history
        sql_statements.append("""
        CREATE TABLE IF NOT EXISTS sales_history (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50),
            sale_date DATE,
            sale_price DECIMAL(15,2),
            seller_name TEXT,
            buyer_name TEXT,
            sale_type VARCHAR(50),
            qualified_sale BOOLEAN,
            deed_type VARCHAR(50),
            book_page VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        
        # 4. Tax information
        sql_statements.append("""
        CREATE TABLE IF NOT EXISTS property_tax_info (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50),
            tax_year INTEGER,
            millage_rate DECIMAL(8,4),
            taxable_value DECIMAL(15,2),
            exemptions DECIMAL(15,2),
            tax_amount DECIMAL(15,2),
            paid_amount DECIMAL(15,2),
            payment_status VARCHAR(20),
            due_date DATE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        
        # 5. Building permits
        sql_statements.append("""
        CREATE TABLE IF NOT EXISTS building_permits (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50),
            permit_number VARCHAR(50) UNIQUE,
            permit_type VARCHAR(100),
            description TEXT,
            issue_date DATE,
            completion_date DATE,
            status VARCHAR(50),
            contractor_name TEXT,
            estimated_value DECIMAL(15,2),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        
        # 6. Sunbiz entities
        sql_statements.append("""
        CREATE TABLE IF NOT EXISTS sunbiz_entities (
            id SERIAL PRIMARY KEY,
            entity_id VARCHAR(50) UNIQUE,
            entity_name TEXT,
            entity_type VARCHAR(100),
            status VARCHAR(50),
            filing_date DATE,
            registered_agent TEXT,
            principal_address TEXT,
            mailing_address TEXT,
            officers JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """)
        
        # 7. Property-Entity matching
        sql_statements.append("""
        CREATE TABLE IF NOT EXISTS property_entities (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50),
            entity_id VARCHAR(50),
            relationship_type VARCHAR(50),
            confidence_score DECIMAL(3,2),
            match_details JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        
        # 8. Tracked properties (user watchlist)
        sql_statements.append("""
        CREATE TABLE IF NOT EXISTS tracked_properties (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50),
            parcel_id VARCHAR(50),
            tracking_type VARCHAR(50),
            alert_preferences JSONB,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """)
        
        # 9. Florida data updates tracking
        sql_statements.append("""
        CREATE TABLE IF NOT EXISTS fl_data_updates (
            id SERIAL PRIMARY KEY,
            data_source VARCHAR(100),
            update_type VARCHAR(50),
            records_processed INTEGER,
            status VARCHAR(50),
            error_message TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            metadata JSONB
        );
        """)
        
        # 10. Property profiles (aggregated view)
        sql_statements.append("""
        CREATE TABLE IF NOT EXISTS property_profiles (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) UNIQUE,
            profile_data JSONB,
            market_analysis JSONB,
            investment_score DECIMAL(3,2),
            last_updated TIMESTAMP DEFAULT NOW()
        );
        """)
        
        # Create indexes
        sql_statements.append("""
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_parcels_county ON parcels(county_code);
        CREATE INDEX IF NOT EXISTS idx_parcels_owner ON parcels(owner_name);
        CREATE INDEX IF NOT EXISTS idx_parcels_address ON parcels(property_address);
        CREATE INDEX IF NOT EXISTS idx_sales_parcel ON sales_history(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_history(sale_date);
        CREATE INDEX IF NOT EXISTS idx_permits_parcel ON building_permits(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_tax_parcel ON property_tax_info(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_entities_name ON sunbiz_entities(entity_name);
        """)
        
        return sql_statements
    
    def execute_sql(self, sql):
        """Execute raw SQL (would need proper SQL execution endpoint)"""
        # Note: Supabase doesn't directly support raw SQL execution via the Python client
        # You would need to run these in the Supabase SQL editor or use a direct PostgreSQL connection
        print(f"  SQL to execute: {sql[:100]}...")
        return True
    
    def analyze_database_state(self):
        """Analyze current database state"""
        print("\n" + "="*80)
        print("DATABASE STATE ANALYSIS")
        print("="*80)
        
        if not self.existing_tables:
            print("\nWARNING: No tables found in database!")
            print("\nThe database appears to be empty. You need to:")
            print("1. Go to your Supabase dashboard")
            print("2. Navigate to the SQL Editor")
            print("3. Run the table creation scripts")
            print("4. Load initial data using the data pipeline scripts")
            
            # Save SQL scripts
            sql_file = "create_all_tables.sql"
            with open(sql_file, 'w') as f:
                f.write("-- ConcordBroker Database Schema\n")
                f.write("-- Run this in Supabase SQL Editor\n\n")
                for sql in self.create_core_tables_sql():
                    f.write(sql + "\n\n")
            
            print(f"\nSQL script saved to: {sql_file}")
            print("Run this script in your Supabase SQL Editor to create all tables.")
        
        else:
            # Analyze existing tables
            total_rows = sum(t['row_count'] for t in self.existing_tables)
            empty_tables = [t for t in self.existing_tables if t['row_count'] == 0]
            populated_tables = [t for t in self.existing_tables if t['row_count'] > 0]
            
            print(f"\nSUMMARY:")
            print(f"  Total tables found: {len(self.existing_tables)}")
            print(f"  Populated tables: {len(populated_tables)}")
            print(f"  Empty tables: {len(empty_tables)}")
            print(f"  Total rows: {total_rows:,}")
            
            if populated_tables:
                print(f"\nPOPULATED TABLES:")
                for table in sorted(populated_tables, key=lambda x: x['row_count'], reverse=True):
                    print(f"  - {table['name']}: {table['row_count']:,} rows")
            
            if empty_tables:
                print(f"\nEMPTY TABLES (need data):")
                for table in empty_tables:
                    print(f"  - {table['name']}")
        
        return self.audit_results
    
    def generate_data_mapping_report(self):
        """Generate report on how data maps to UI"""
        print("\n" + "="*80)
        print("DATA TO UI MAPPING ANALYSIS")
        print("="*80)
        
        mapping = {
            "Property Search Page": {
                "tables": ["parcels", "properties"],
                "fields": ["property_address", "owner_name", "property_type", "total_value"],
                "filters": ["county_code", "property_use_code", "price_range", "year_built"]
            },
            "Property Profile Page": {
                "tables": ["parcels", "properties", "property_profiles"],
                "tabs": {
                    "Overview": ["property_address", "owner_name", "total_value", "year_built"],
                    "Sales History": ["sales_history.sale_date", "sales_history.sale_price"],
                    "Tax Info": ["property_tax_info.tax_amount", "property_tax_info.payment_status"],
                    "Permits": ["building_permits.permit_type", "building_permits.status"],
                    "Business Entities": ["sunbiz_entities.entity_name", "property_entities.relationship_type"]
                }
            },
            "Dashboard": {
                "tables": ["tracked_properties", "user_alerts", "property_profiles"],
                "widgets": ["tracked_properties_list", "recent_alerts", "market_trends"]
            },
            "Market Analysis": {
                "tables": ["sales_history", "property_valuations"],
                "metrics": ["average_sale_price", "price_per_sqft", "days_on_market"]
            }
        }
        
        print("\nUI COMPONENT DATA REQUIREMENTS:")
        for page, config in mapping.items():
            print(f"\n{page}:")
            print(f"  Required tables: {', '.join(config['tables'])}")
            
            if 'tabs' in config:
                print("  Tab data:")
                for tab, fields in config['tabs'].items():
                    print(f"    - {tab}: {', '.join(fields[:3])}...")
            
            if 'filters' in config:
                print(f"  Filters: {', '.join(config['filters'])}")
            
            if 'widgets' in config:
                print(f"  Widgets: {', '.join(config['widgets'])}")
        
        # Save mapping to file
        with open("data_ui_mapping.json", 'w') as f:
            json.dump(mapping, f, indent=2)
        
        print(f"\nMapping saved to: data_ui_mapping.json")

def main():
    print("CONCORDBROKER DATABASE INITIALIZATION & AUDIT")
    print("="*80)
    
    try:
        initializer = DatabaseInitializer()
        
        # Check existing tables
        initializer.check_existing_tables()
        
        # Analyze database state
        initializer.analyze_database_state()
        
        # Generate UI mapping report
        initializer.generate_data_mapping_report()
        
        print("\n" + "="*80)
        print("NEXT STEPS:")
        print("="*80)
        print("\n1. If database is empty:")
        print("   - Run create_all_tables.sql in Supabase SQL Editor")
        print("   - Execute data loading scripts")
        print("\n2. For empty tables:")
        print("   - Run appropriate data loader scripts from apps/workers/")
        print("   - Check FLORIDA_DATA_SETUP.md for data source details")
        print("\n3. For large tables:")
        print("   - Implement partitioning strategy")
        print("   - Add appropriate indexes")
        print("\n4. Review data_ui_mapping.json for UI integration requirements")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()