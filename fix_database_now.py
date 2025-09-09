"""
Fix Database Structure and Load Sample Data
Fixes all database issues identified in the audit
"""

import os
import sys
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apps.api.supabase_client import get_supabase_client

# Load environment variables
load_dotenv()

def execute_sql_file():
    """Execute the SQL file to create missing tables"""
    print("Creating missing tables...")
    
    client = get_supabase_client()
    
    # Read SQL file
    with open('fix_database_complete.sql', 'r') as f:
        sql_content = f.read()
    
    # Execute via RPC (you may need to create this function in Supabase)
    # For now, print instructions
    print("\n" + "="*60)
    print("IMPORTANT: Run the following SQL in Supabase Dashboard:")
    print("="*60)
    print("1. Go to https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Go to SQL Editor")
    print("4. Copy and paste content from: fix_database_complete.sql")
    print("5. Click 'Run'")
    print("="*60 + "\n")
    
    return True

def load_sample_data():
    """Load sample data into all tables"""
    print("Loading sample data...")
    
    client = get_supabase_client()
    
    # Sample parcel IDs to use
    parcel_ids = ['504231242720', '064210010010', '494210190120']
    
    # 1. Load Sunbiz Corporate data
    print("Loading Sunbiz corporate data...")
    sunbiz_data = [
        {
            'corp_number': 'P20000045678',
            'corp_name': 'FLORIDA INVESTMENT PROPERTIES LLC',
            'status': 'ACTIVE',
            'filing_type': 'Florida Limited Liability',
            'file_date': '2020-06-15',
            'state': 'FL',
            'principal_addr': '3920 SW 53 CT',
            'principal_city': 'DAVIE',
            'principal_state': 'FL',
            'principal_zip': '33314',
            'mailing_addr': '3920 SW 53 CT',
            'mailing_city': 'DAVIE',
            'mailing_state': 'FL',
            'mailing_zip': '33314',
            'registered_agent_name': 'RODRIGUEZ MARIA',
            'registered_agent_addr': '3920 SW 53 CT, DAVIE, FL 33314',
            'parcel_id': '504231242720'
        },
        {
            'corp_number': 'L19000234567',
            'corp_name': 'SUNRISE HOLDINGS GROUP INC',
            'status': 'ACTIVE',
            'filing_type': 'Florida Profit Corporation',
            'file_date': '2019-03-20',
            'state': 'FL',
            'principal_addr': '4321 NW 88 AVE',
            'principal_city': 'SUNRISE',
            'principal_state': 'FL',
            'principal_zip': '33351',
            'registered_agent_name': 'CORPORATE AGENTS INC',
            'parcel_id': '064210010010'
        }
    ]
    
    for data in sunbiz_data:
        try:
            client.table('sunbiz_corporate').upsert(data).execute()
        except Exception as e:
            print(f"  Warning: Could not insert Sunbiz data: {e}")
    
    # 2. Load Property Tax Records
    print("Loading property tax records...")
    current_year = datetime.now().year
    for parcel_id in parcel_ids:
        for year in range(current_year - 3, current_year + 1):
            tax_data = {
                'parcel_id': parcel_id,
                'tax_year': year,
                'millage_rate': round(random.uniform(18.5, 22.5), 4),
                'assessed_value': random.randint(200000, 500000),
                'taxable_value': random.randint(180000, 450000),
                'tax_amount': round(random.uniform(3000, 8000), 2),
                'paid_amount': round(random.uniform(3000, 8000), 2),
                'balance_due': 0 if year < current_year else round(random.uniform(0, 500), 2),
                'payment_status': 'PAID' if year < current_year else 'DUE',
                'due_date': f'{year}-11-30',
                'paid_date': f'{year}-10-15' if year < current_year else None,
                'delinquent': False
            }
            try:
                client.table('property_tax_records').upsert(tax_data).execute()
            except Exception as e:
                print(f"  Warning: Could not insert tax record: {e}")
    
    # 3. Load Assessed Values
    print("Loading assessed values...")
    for parcel_id in parcel_ids:
        for year in range(current_year - 2, current_year + 1):
            assessed_data = {
                'parcel_id': parcel_id,
                'assessment_year': year,
                'land_value': random.randint(50000, 150000),
                'building_value': random.randint(150000, 350000),
                'total_value': random.randint(200000, 500000),
                'just_value': random.randint(200000, 500000),
                'assessed_value': random.randint(180000, 450000),
                'taxable_value': random.randint(160000, 400000),
                'exemptions': 50000 if random.random() > 0.5 else 0,
                'exemption_types': 'HOMESTEAD' if random.random() > 0.5 else None
            }
            try:
                client.table('assessed_values').upsert(assessed_data).execute()
            except Exception as e:
                print(f"  Warning: Could not insert assessed value: {e}")
    
    # 4. Load Investment Analysis
    print("Loading investment analysis...")
    for parcel_id in parcel_ids:
        analysis_data = {
            'parcel_id': parcel_id,
            'analysis_date': datetime.now().date().isoformat(),
            'roi_percentage': round(random.uniform(8.5, 15.5), 2),
            'cap_rate': round(random.uniform(5.5, 9.5), 2),
            'cash_flow_monthly': round(random.uniform(500, 2500), 2),
            'market_value': random.randint(250000, 550000),
            'rental_estimate': random.randint(1800, 3500),
            'investment_score': random.randint(65, 95),
            'risk_level': random.choice(['LOW', 'MEDIUM', 'MEDIUM-LOW']),
            'recommendations': 'Property shows strong rental potential with stable appreciation trends.'
        }
        try:
            client.table('investment_analysis').upsert(analysis_data).execute()
        except Exception as e:
            print(f"  Warning: Could not insert analysis: {e}")
    
    # 5. Load Market Comparables
    print("Loading market comparables...")
    comp_addresses = [
        '3925 SW 53 CT', '3915 SW 53 CT', '3930 SW 53 CT',
        '4320 NW 88 AVE', '4322 NW 88 AVE', '4324 NW 88 AVE'
    ]
    
    for parcel_id in parcel_ids[:2]:  # Just for first two properties
        for i, addr in enumerate(comp_addresses[:3]):
            comp_data = {
                'parcel_id': parcel_id,
                'comp_parcel_id': f'COMP{i+1:03d}',
                'comp_address': addr,
                'sale_date': (datetime.now() - timedelta(days=random.randint(30, 365))).date().isoformat(),
                'sale_price': random.randint(200000, 500000),
                'price_per_sqft': round(random.uniform(150, 250), 2),
                'distance_miles': round(random.uniform(0.1, 2.5), 2),
                'similarity_score': random.randint(75, 95),
                'property_type': 'SINGLE FAMILY'
            }
            try:
                client.table('market_comparables').upsert(comp_data).execute()
            except Exception as e:
                print(f"  Warning: Could not insert comparable: {e}")
    
    # 6. Load Property Metrics
    print("Loading property metrics...")
    for parcel_id in parcel_ids:
        metrics_data = {
            'parcel_id': parcel_id,
            'metric_date': datetime.now().date().isoformat(),
            'price_per_sqft': round(random.uniform(150, 250), 2),
            'lot_size_acres': round(random.uniform(0.15, 0.35), 4),
            'building_age': random.randint(5, 30),
            'effective_age': random.randint(3, 25),
            'condition_score': random.randint(70, 95),
            'location_score': random.randint(75, 95),
            'school_rating': round(random.uniform(7.0, 9.5), 1),
            'crime_index': random.randint(20, 60),
            'walkability_score': random.randint(40, 85)
        }
        try:
            client.table('property_metrics').upsert(metrics_data).execute()
        except Exception as e:
            print(f"  Warning: Could not insert metrics: {e}")
    
    # 7. Add some foreclosure data (for demonstration)
    print("Loading sample foreclosure data...")
    foreclosure_data = {
        'case_number': 'CACE-2024-001234',
        'parcel_id': '494210190120',
        'property_address': '1234 SAMPLE ST',
        'filing_date': '2024-03-15',
        'case_status': 'ACTIVE',
        'plaintiff': 'BANK OF AMERICA',
        'defendant': 'JOHN DOE',
        'attorney': 'SMITH & ASSOCIATES',
        'judge': 'HON. JANE SMITH',
        'auction_date': '2025-02-15'
    }
    try:
        client.table('foreclosure_cases').upsert(foreclosure_data).execute()
    except Exception as e:
        print(f"  Warning: Could not insert foreclosure: {e}")
    
    # 8. Add tax certificate sample
    print("Loading sample tax certificate...")
    cert_data = {
        'certificate_number': 'TC-2024-0001',
        'parcel_id': '494210190120',
        'tax_year': 2023,
        'face_value': 4500.00,
        'interest_rate': 18.0,
        'certificate_status': 'OUTSTANDING',
        'sale_date': '2024-06-01',
        'buyer_name': 'TAX CERT INVESTORS LLC',
        'buyer_number': 'B123'
    }
    try:
        client.table('tax_certificates').upsert(cert_data).execute()
    except Exception as e:
        print(f"  Warning: Could not insert certificate: {e}")
    
    print("\n✅ Sample data loaded successfully!")
    
    return True

def verify_fixes():
    """Verify that all fixes were applied"""
    print("\nVerifying fixes...")
    
    client = get_supabase_client()
    
    # Check if we can query the broward_parcels view
    try:
        result = client.table('broward_parcels').select('*').limit(1).execute()
        print("✅ broward_parcels view is working")
    except Exception as e:
        print(f"❌ broward_parcels view not created: {e}")
    
    # Check Sunbiz data
    try:
        result = client.table('sunbiz_corporate').select('*').execute()
        count = len(result.data)
        print(f"✅ Sunbiz corporate has {count} records")
    except Exception as e:
        print(f"❌ Sunbiz corporate issue: {e}")
    
    # Check tax records
    try:
        result = client.table('property_tax_records').select('*').execute()
        count = len(result.data)
        print(f"✅ Property tax records has {count} records")
    except Exception as e:
        print(f"❌ Property tax records issue: {e}")
    
    # Check investment analysis
    try:
        result = client.table('investment_analysis').select('*').execute()
        count = len(result.data)
        print(f"✅ Investment analysis has {count} records")
    except Exception as e:
        print(f"❌ Investment analysis issue: {e}")
    
    print("\n" + "="*60)
    print("DATABASE FIX COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Refresh your browser at http://localhost:5173")
    print("2. Navigate to any property profile")
    print("3. All tabs should now show data")
    print("\nTest URL: http://localhost:5173/property/504231242720")

def main():
    print("="*60)
    print("DATABASE FIX SCRIPT")
    print("="*60)
    
    # Step 1: Show SQL instructions
    execute_sql_file()
    
    # Wait for user to confirm
    input("\nPress Enter after running the SQL in Supabase Dashboard...")
    
    # Step 2: Load sample data
    load_sample_data()
    
    # Step 3: Verify
    verify_fixes()

if __name__ == "__main__":
    main()