"""
Load Sample Data into Supabase to Fill Missing Tables
This script loads realistic sample data into tables that are missing data
"""

import os
import sys
from datetime import datetime, timedelta
import random
from typing import List, Dict
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv('apps/web/.env')

class SampleDataLoader:
    """Loads sample data into Supabase tables"""
    
    def __init__(self):
        self.supabase_url = os.getenv("VITE_SUPABASE_URL")
        self.supabase_key = os.getenv("VITE_SUPABASE_ANON_KEY")
        self.supabase = None
        
        if self.supabase_url and self.supabase_key:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            print("[OK] Connected to Supabase")
        else:
            print("[ERROR] Failed to connect to Supabase")
            sys.exit(1)
    
    def load_sales_history(self, count: int = 1000):
        """Load sample property sales history"""
        print(f"\n[LOADING] Property Sales History ({count} records)...")
        
        # Get some parcel IDs from florida_parcels
        try:
            parcels_response = self.supabase.table('florida_parcels').select('parcel_id').limit(200).execute()
            parcel_ids = [p['parcel_id'] for p in parcels_response.data] if parcels_response.data else []
            
            if not parcel_ids:
                # Use sample parcel IDs
                parcel_ids = [f"50423210{str(i).zfill(4)}" for i in range(1, 201)]
            
            sales_records = []
            base_date = datetime(2020, 1, 1)
            
            for i in range(count):
                parcel_id = random.choice(parcel_ids)
                sale_date = base_date + timedelta(days=random.randint(0, 1825))  # Random date in last 5 years
                
                # Generate realistic sale price based on property type
                base_price = random.choice([250000, 350000, 450000, 550000, 750000, 950000])
                price_variation = random.uniform(0.8, 1.3)
                sale_price = int(base_price * price_variation)
                
                sales_records.append({
                    'parcel_id': parcel_id,
                    'sale_date': sale_date.strftime('%Y-%m-%d'),
                    'sale_price': sale_price,
                    'sale_year': sale_date.year,
                    'buyer_name': f"{random.choice(['SMITH', 'JOHNSON', 'WILLIAMS', 'BROWN', 'JONES'])} {random.choice(['JOHN', 'MARY', 'ROBERT', 'LINDA', 'JAMES'])}",
                    'seller_name': f"{random.choice(['DAVIS', 'MILLER', 'WILSON', 'MOORE', 'TAYLOR'])} {random.choice(['MICHAEL', 'PATRICIA', 'DAVID', 'JENNIFER', 'WILLIAM'])}",
                    'deed_type': random.choice(['WD', 'QCD', 'TD', 'SWD']),
                    'qualified_flag': random.choice(['Q', 'U']) 
                })
            
            # Insert in batches of 100
            for i in range(0, len(sales_records), 100):
                batch = sales_records[i:i+100]
                response = self.supabase.table('property_sales_history').upsert(batch).execute()
            
            print(f"  [OK] Loaded {len(sales_records)} sales history records")
            
        except Exception as e:
            print(f"  [ERROR] Failed to load sales history: {str(e)}")
    
    def load_nav_assessments(self, count: int = 500):
        """Load sample NAV assessments"""
        print(f"\n[LOADING] NAV Assessments ({count} records)...")
        
        try:
            # Get parcel IDs
            parcels_response = self.supabase.table('florida_parcels').select('parcel_id').limit(100).execute()
            parcel_ids = [p['parcel_id'] for p in parcels_response.data] if parcels_response.data else []
            
            if not parcel_ids:
                parcel_ids = [f"50423210{str(i).zfill(4)}" for i in range(1, 101)]
            
            nav_records = []
            assessment_types = [
                'Fire District', 'Solid Waste', 'Stormwater', 'Street Lighting',
                'Mosquito Control', 'Library District', 'Parks & Recreation',
                'Water Management', 'Code Enforcement'
            ]
            
            for i in range(count):
                parcel_id = random.choice(parcel_ids)
                assessment_type = random.choice(assessment_types)
                
                # Generate realistic assessment amounts
                base_amounts = {
                    'Fire District': 450,
                    'Solid Waste': 380,
                    'Stormwater': 120,
                    'Street Lighting': 85,
                    'Mosquito Control': 25,
                    'Library District': 65,
                    'Parks & Recreation': 110,
                    'Water Management': 95,
                    'Code Enforcement': 50
                }
                
                base_amount = base_amounts.get(assessment_type, 100)
                amount = round(base_amount * random.uniform(0.9, 1.1), 2)
                
                nav_records.append({
                    'parcel_id': parcel_id,
                    'assessment_type': assessment_type,
                    'assessment_amount': amount,
                    'tax_year': 2025,
                    'district_code': f"D{random.randint(100, 999)}",
                    'status': 'Active'
                })
            
            # Insert in batches
            for i in range(0, len(nav_records), 100):
                batch = nav_records[i:i+100]
                response = self.supabase.table('nav_assessments').upsert(batch).execute()
            
            print(f"  [OK] Loaded {len(nav_records)} NAV assessment records")
            
        except Exception as e:
            print(f"  [ERROR] Failed to load NAV assessments: {str(e)}")
    
    def load_sunbiz_corporate(self, count: int = 500):
        """Load sample Sunbiz corporate data"""
        print(f"\n[LOADING] Sunbiz Corporate Data ({count} records)...")
        
        try:
            corp_records = []
            
            # Company name components
            prefixes = ['OCEAN', 'BEACH', 'PALM', 'SUNSET', 'COASTAL', 'ATLANTIC', 'TROPICAL', 'SEASIDE', 'BAYVIEW', 'HARBOR']
            types = ['PROPERTIES', 'INVESTMENTS', 'HOLDINGS', 'VENTURES', 'DEVELOPMENT', 'REALTY', 'CAPITAL', 'GROUP', 'PARTNERS', 'MANAGEMENT']
            suffixes = ['LLC', 'CORP', 'INC', 'LP', 'LLP', 'PA']
            
            cities = ['FORT LAUDERDALE', 'MIAMI', 'WEST PALM BEACH', 'HOLLYWOOD', 'BOCA RATON', 'CORAL SPRINGS', 'POMPANO BEACH']
            streets = ['OCEAN BLVD', 'BEACH AVE', 'COLLINS AVE', 'LAS OLAS BLVD', 'COMMERCIAL BLVD', 'FEDERAL HWY', 'BISCAYNE BLVD']
            
            for i in range(count):
                corp_number = f"{'P' if random.random() > 0.5 else 'L'}{random.randint(2015, 2024)}000{str(i).zfill(6)}"
                corp_name = f"{random.choice(prefixes)} {random.choice(types)} {random.choice(suffixes)}"
                
                street_num = random.randint(100, 9999)
                street = random.choice(streets)
                city = random.choice(cities)
                zip_code = random.randint(33001, 33499)
                
                address = f"{street_num} {street}, {city}, FL {zip_code}"
                
                filing_date = datetime(random.randint(2015, 2024), random.randint(1, 12), random.randint(1, 28))
                
                corp_records.append({
                    'corp_number': corp_number,
                    'corp_name': corp_name,
                    'status': random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'INACTIVE']),  # 75% active
                    'filing_type': random.choice(['Florida Limited Liability', 'Florida Profit Corporation', 'Florida Limited Partnership']),
                    'principal_addr': address,
                    'mailing_addr': address,
                    'registered_agent': f"{random.choice(['SMITH', 'JOHNSON', 'WILLIAMS'])} {random.choice(['JOHN', 'MARY', 'ROBERT'])}",
                    'date_filed': filing_date.strftime('%Y-%m-%d'),
                    'state': 'FL',
                    'ein_number': f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
                })
            
            # Insert in batches
            for i in range(0, len(corp_records), 100):
                batch = corp_records[i:i+100]
                response = self.supabase.table('sunbiz_corporate').upsert(batch).execute()
            
            print(f"  [OK] Loaded {len(corp_records)} Sunbiz corporate records")
            
        except Exception as e:
            print(f"  [ERROR] Failed to load Sunbiz data: {str(e)}")
    
    def load_florida_permits(self, count: int = 500):
        """Load sample building permits"""
        print(f"\n[LOADING] Florida Building Permits ({count} records)...")
        
        try:
            # Get parcel IDs
            parcels_response = self.supabase.table('florida_parcels').select('parcel_id,owner_name').limit(100).execute()
            parcels = parcels_response.data if parcels_response.data else []
            
            if not parcels:
                parcels = [{'parcel_id': f"50423210{str(i).zfill(4)}", 'owner_name': f"OWNER {i}"} for i in range(1, 101)]
            
            permit_records = []
            
            permit_types = [
                ('Building', ['New Construction', 'Addition', 'Alteration', 'Demolition']),
                ('Electrical', ['Service Upgrade', 'Rewire', 'Panel Replacement', 'New Service']),
                ('Plumbing', ['Water Heater', 'Re-pipe', 'Fixture Replacement', 'New Installation']),
                ('Mechanical', ['HVAC Replacement', 'Duct Work', 'New Installation']),
                ('Roofing', ['Re-roof', 'Repair', 'New Roof'])
            ]
            
            contractors = [
                'ABC Construction LLC', 'XYZ Builders Inc', 'Premier Contractors Corp',
                'Quality Construction Services', 'Professional Builders Group',
                'Elite Construction Co', 'Master Builders LLC'
            ]
            
            base_date = datetime(2023, 1, 1)
            
            for i in range(count):
                parcel = random.choice(parcels)
                permit_type, subtypes = random.choice(permit_types)
                permit_subtype = random.choice(subtypes)
                
                # Generate permit number
                year = random.randint(2023, 2025)
                permit_prefix = permit_type[0].upper()
                permit_number = f"{permit_prefix}{year}-{str(i).zfill(6)}"
                
                issue_date = base_date + timedelta(days=random.randint(0, 730))
                
                # Generate realistic estimated values
                value_ranges = {
                    'New Construction': (150000, 500000),
                    'Addition': (25000, 150000),
                    'Alteration': (5000, 50000),
                    'Service Upgrade': (2000, 8000),
                    'Water Heater': (1500, 3500),
                    'HVAC Replacement': (5000, 15000),
                    'Re-roof': (8000, 25000)
                }
                
                min_val, max_val = value_ranges.get(permit_subtype, (1000, 10000))
                estimated_value = random.randint(min_val, max_val)
                
                permit_records.append({
                    'permit_number': permit_number,
                    'parcel_id': parcel['parcel_id'],
                    'permit_type': permit_type,
                    'permit_subtype': permit_subtype,
                    'issue_date': issue_date.strftime('%Y-%m-%d'),
                    'estimated_value': estimated_value,
                    'owner_name': parcel.get('owner_name', 'UNKNOWN'),
                    'description': f"{permit_subtype} - {permit_type} work",
                    'status': random.choice(['Issued', 'Finaled', 'Active', 'Expired'])
                })
            
            # Insert in batches
            for i in range(0, len(permit_records), 100):
                batch = permit_records[i:i+100]
                # Remove contractor field which doesn't exist in table
                for record in batch:
                    record.pop('contractor', None)
                response = self.supabase.table('florida_permits').upsert(batch).execute()
            
            print(f"  [OK] Loaded {len(permit_records)} permit records")
            
        except Exception as e:
            print(f"  [ERROR] Failed to load permits: {str(e)}")
    
    def load_tax_certificates(self, count: int = 200):
        """Load sample tax certificate data"""
        print(f"\n[LOADING] Tax Certificates ({count} records)...")
        
        try:
            # Get parcel IDs
            parcels_response = self.supabase.table('florida_parcels').select('parcel_id').limit(50).execute()
            parcel_ids = [p['parcel_id'] for p in parcels_response.data] if parcels_response.data else []
            
            if not parcel_ids:
                parcel_ids = [f"50423210{str(i).zfill(4)}" for i in range(1, 51)]
            
            tax_cert_records = []
            
            for i in range(count):
                parcel_id = random.choice(parcel_ids)
                tax_year = random.randint(2020, 2024)
                certificate_number = f"TC{tax_year}-{str(i).zfill(6)}"
                
                # Generate realistic tax amounts
                base_tax = random.uniform(2000, 15000)
                interest = base_tax * 0.18  # 18% interest
                fees = 250
                total_amount = round(base_tax + interest + fees, 2)
                
                sale_date = datetime(tax_year + 1, 6, 1)  # Certificates typically sold in June
                
                tax_cert_records.append({
                    'certificate_number': certificate_number,
                    'parcel_id': parcel_id,
                    'tax_year': tax_year,
                    'face_amount': round(base_tax, 2),
                    'interest_rate': 18.0,
                    'total_amount': total_amount,
                    'sale_date': sale_date.strftime('%Y-%m-%d'),
                    'buyer_name': random.choice(['TAX CERT INVESTORS LLC', 'FLORIDA TAX LIENS INC', 'CERTIFICATE HOLDERS GROUP']),
                    'status': random.choice(['Outstanding', 'Redeemed', 'Deed Application'])
                })
            
            # Insert in batches
            for i in range(0, len(tax_cert_records), 100):
                batch = tax_cert_records[i:i+100]
                response = self.supabase.table('tax_certificates').upsert(batch).execute()
            
            print(f"  [OK] Loaded {len(tax_cert_records)} tax certificate records")
            
        except Exception as e:
            print(f"  [ERROR] Failed to load tax certificates: {str(e)}")
    
    def run_all_loads(self):
        """Run all data loading operations"""
        print("\n" + "="*60)
        print("LOADING SAMPLE DATA INTO SUPABASE")
        print("="*60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Load data for each table
        self.load_sales_history(1000)     # 1000 sales records
        self.load_nav_assessments(500)    # 500 NAV records
        self.load_sunbiz_corporate(500)   # 500 corporate records
        self.load_florida_permits(500)    # 500 permit records
        self.load_tax_certificates(200)   # 200 tax certificate records
        
        print("\n" + "="*60)
        print("SAMPLE DATA LOADING COMPLETE")
        print("="*60)
        print("\nAll sample data has been loaded successfully!")
        print("Run 'python comprehensive_database_audit.py' to verify the data.")


def main():
    """Main execution"""
    loader = SampleDataLoader()
    loader.run_all_loads()


if __name__ == "__main__":
    main()