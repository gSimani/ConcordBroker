import os
import json
from supabase import create_client, Client
from datetime import datetime

def connect_to_supabase():
    """Connect to Supabase using environment variables"""
    try:
        # Try to read from .env.mcp first
        env_file = ".env.mcp"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value.strip('"\'')

        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            print("[ERROR] Missing Supabase credentials")
            return None

        print(f"[INFO] Connecting to: {supabase_url}")
        supabase: Client = create_client(supabase_url, supabase_key)
        return supabase

    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return None

def analyze_florida_parcels_sales(supabase):
    """Detailed analysis of sales data in florida_parcels table"""
    print("\n[ANALYSIS] florida_parcels table - Sales Data")
    print("=" * 50)

    try:
        # Get count of records with sales data
        print("[INFO] Checking sales data availability...")

        # Count total records
        total_count = supabase.table('florida_parcels').select('id', count='exact').execute()
        print(f"Total records: {total_count.count}")

        # Count records with sale_price
        with_price = supabase.table('florida_parcels').select('id', count='exact').not_.is_('sale_price', 'null').execute()
        print(f"Records with sale_price: {with_price.count}")

        # Count records with sale_date
        with_date = supabase.table('florida_parcels').select('id', count='exact').not_.is_('sale_date', 'null').execute()
        print(f"Records with sale_date: {with_date.count}")

        # Get sample records with sales data
        print("\n[SAMPLE] Records with complete sales data:")
        sales_records = supabase.table('florida_parcels').select('*').not_.is_('sale_price', 'null').not_.is_('sale_date', 'null').limit(5).execute()

        if sales_records.data:
            for i, record in enumerate(sales_records.data, 1):
                print(f"\nSample {i}:")
                print(f"  Parcel ID: {record.get('parcel_id')}")
                print(f"  County: {record.get('county')}")
                print(f"  Sale Date: {record.get('sale_date')}")
                print(f"  Sale Price: ${record.get('sale_price'):,}" if record.get('sale_price') else "N/A")
                print(f"  Sale Qualification: {record.get('sale_qualification')}")
                print(f"  Property Address: {record.get('phy_addr1')}, {record.get('phy_city')}")
                print(f"  Just Value: ${record.get('just_value'):,}" if record.get('just_value') else "N/A")
        else:
            print("  No records found with complete sales data")

        # Check for different sale qualifications
        print("\n[INFO] Sale qualification types:")
        try:
            qual_query = supabase.table('florida_parcels').select('sale_qualification').not_.is_('sale_qualification', 'null').limit(100).execute()
            qualifications = set()
            for record in qual_query.data:
                if record.get('sale_qualification'):
                    qualifications.add(record['sale_qualification'])

            for qual in sorted(qualifications):
                print(f"  - {qual}")
        except Exception as e:
            print(f"  [ERROR] Could not retrieve qualifications: {e}")

        # Price ranges
        print("\n[INFO] Price analysis:")
        try:
            price_stats = supabase.table('florida_parcels').select('sale_price').not_.is_('sale_price', 'null').order('sale_price', desc=False).limit(1000).execute()
            if price_stats.data:
                prices = [r['sale_price'] for r in price_stats.data if r['sale_price'] and r['sale_price'] > 0]
                if prices:
                    print(f"  Sample size: {len(prices)}")
                    print(f"  Min price: ${min(prices):,}")
                    print(f"  Max price: ${max(prices):,}")
                    print(f"  Avg price: ${sum(prices)//len(prices):,}")
        except Exception as e:
            print(f"  [ERROR] Price analysis failed: {e}")

    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")

def analyze_property_sales_table(supabase):
    """Detailed analysis of property_sales table"""
    print("\n[ANALYSIS] property_sales table")
    print("=" * 50)

    try:
        # Get sample data to understand structure
        sample = supabase.table('property_sales').select('*').limit(10).execute()

        if not sample.data:
            print("[ERROR] No data found in property_sales table")
            return

        print(f"[INFO] Found {len(sample.data)} sample records")

        # Show structure
        first_record = sample.data[0]
        print("\n[SCHEMA] Column structure:")
        for key, value in first_record.items():
            value_type = type(value).__name__
            sample_val = str(value)[:50] if value is not None else "NULL"
            print(f"  {key}: {value_type} - Sample: {sample_val}")

        # Test with our parcel IDs
        test_parcels = ['1078130000370', '5032100100120', '5032100200010', '3218460080100']

        print(f"\n[TEST] Searching for test parcels:")
        for parcel_id in test_parcels:
            try:
                # Try different column names that might contain parcel ID
                potential_columns = ['parcel_id', 'parcel', 'id', 'property_id', 'pcn']
                found = False

                for col in potential_columns:
                    if col in first_record:
                        result = supabase.table('property_sales').select('*').eq(col, parcel_id).limit(5).execute()
                        if result.data:
                            print(f"  [FOUND] {len(result.data)} records for {parcel_id} in column {col}")
                            # Show sales data
                            for record in result.data[:2]:  # Show first 2 records
                                sales_info = {}
                                for k, v in record.items():
                                    if any(kw in k.lower() for kw in ['sale', 'price', 'date', 'amount']):
                                        sales_info[k] = v
                                if sales_info:
                                    print(f"    Sales data: {json.dumps(sales_info, default=str)}")
                            found = True
                            break

                if not found:
                    print(f"  [NOT FOUND] {parcel_id}")

            except Exception as e:
                print(f"  [ERROR] Error searching for {parcel_id}: {e}")

    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")

def check_sales_by_county(supabase):
    """Check sales data availability by county"""
    print("\n[ANALYSIS] Sales Data by County")
    print("=" * 50)

    try:
        # Get counties and their sales data counts
        counties_query = supabase.table('florida_parcels').select('county', count='exact').not_.is_('county', 'null').execute()

        print("[INFO] Analyzing sales data by county...")

        # Get unique counties
        counties = supabase.table('florida_parcels').select('county').not_.is_('county', 'null').limit(100).execute()

        if counties.data:
            county_set = set()
            for record in counties.data:
                if record.get('county'):
                    county_set.add(record['county'])

            print(f"\n[COUNTIES] Found {len(county_set)} counties:")

            # Sample a few counties and check their sales data
            sample_counties = list(county_set)[:10]  # First 10 counties

            for county in sample_counties:
                try:
                    # Count total records for county
                    total = supabase.table('florida_parcels').select('id', count='exact').eq('county', county).execute()

                    # Count records with sales data
                    with_sales = supabase.table('florida_parcels').select('id', count='exact').eq('county', county).not_.is_('sale_price', 'null').execute()

                    sales_pct = (with_sales.count / total.count * 100) if total.count > 0 else 0

                    print(f"  {county}: {total.count:,} total, {with_sales.count:,} with sales ({sales_pct:.1f}%)")

                except Exception as e:
                    print(f"  {county}: [ERROR] {e}")

    except Exception as e:
        print(f"[ERROR] County analysis failed: {e}")

def main():
    print("Detailed Sales Data Analysis")
    print("=" * 50)

    # Connect to Supabase
    supabase = connect_to_supabase()
    if not supabase:
        return

    print("[SUCCESS] Connected to Supabase!")

    # Analyze florida_parcels sales data
    analyze_florida_parcels_sales(supabase)

    # Analyze property_sales table
    analyze_property_sales_table(supabase)

    # Check sales data by county
    check_sales_by_county(supabase)

    print("\n[COMPLETE] Analysis finished!")

if __name__ == "__main__":
    main()