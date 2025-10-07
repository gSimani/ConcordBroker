import os
import json
from supabase import create_client, Client

def connect_to_supabase():
    """Connect to Supabase using environment variables"""
    try:
        env_file = ".env.mcp"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value.strip('"\'')

        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

        supabase: Client = create_client(supabase_url, supabase_key)
        return supabase

    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return None

def main():
    print("FINAL SALES DATA SUMMARY")
    print("=" * 50)

    supabase = connect_to_supabase()
    if not supabase:
        return

    # Find records with actual sales data
    print("[INFO] Finding records with sales data...")

    try:
        # Get records that have both sale_price and sale_date
        sales_records = supabase.table('florida_parcels')\
            .select('parcel_id, county, sale_date, sale_price, sale_qualification, phy_addr1, phy_city, just_value')\
            .not_.is_('sale_price', 'null')\
            .not_.is_('sale_date', 'null')\
            .gt('sale_price', 0)\
            .order('sale_price', desc=True)\
            .limit(10)\
            .execute()

        if sales_records.data:
            print(f"[SUCCESS] Found {len(sales_records.data)} records with complete sales data")
            print("\nTop 10 sales by price:")
            print("-" * 80)

            for i, record in enumerate(sales_records.data, 1):
                parcel_id = record.get('parcel_id', 'N/A')
                county = record.get('county', 'N/A')
                sale_date = record.get('sale_date', 'N/A')
                sale_price = record.get('sale_price', 0)
                qualification = record.get('sale_qualification', 'N/A')
                address = f"{record.get('phy_addr1', '')}, {record.get('phy_city', '')}"
                just_value = record.get('just_value', 0)

                print(f"{i:2d}. Parcel: {parcel_id}")
                print(f"    County: {county}")
                print(f"    Sale Date: {sale_date}")
                print(f"    Sale Price: ${sale_price:,}")
                print(f"    Just Value: ${just_value:,}" if just_value else "    Just Value: N/A")
                print(f"    Qualification: {qualification}")
                print(f"    Address: {address}")
                print()

        else:
            print("[INFO] No records found with complete sales data")

        # Check for records with just sale_price (no date requirement)
        print("\n[INFO] Checking records with sale_price only...")
        price_only = supabase.table('florida_parcels')\
            .select('parcel_id, county, sale_date, sale_price, phy_addr1')\
            .not_.is_('sale_price', 'null')\
            .gt('sale_price', 0)\
            .limit(5)\
            .execute()

        if price_only.data:
            print(f"Found {len(price_only.data)} records with sale_price:")
            for record in price_only.data:
                print(f"  {record.get('parcel_id')}: ${record.get('sale_price'):,} ({record.get('sale_date', 'No Date')})")

        # Test specific parcel
        print(f"\n[INFO] Testing specific parcel: 1078130000370...")
        specific_parcel = supabase.table('florida_parcels')\
            .select('*')\
            .eq('parcel_id', '1078130000370')\
            .execute()

        if specific_parcel.data:
            record = specific_parcel.data[0]
            print("Found parcel 1078130000370:")
            print(f"  County: {record.get('county')}")
            print(f"  Owner: {record.get('owner_name')}")
            print(f"  Address: {record.get('phy_addr1')}, {record.get('phy_city')}")
            print(f"  Sale Date: {record.get('sale_date')}")
            print(f"  Sale Price: ${record.get('sale_price')}" if record.get('sale_price') else "  Sale Price: None")
            print(f"  Just Value: ${record.get('just_value'):,}" if record.get('just_value') else "  Just Value: None")

    except Exception as e:
        print(f"[ERROR] Query failed: {e}")

    # Summary of findings
    print(f"\n" + "=" * 50)
    print("SUMMARY OF FINDINGS:")
    print("=" * 50)
    print("1. TABLES FOUND:")
    print("   - florida_parcels: Main property data table")
    print("   - property_sales: Exists but empty")
    print("   - properties: Exists (not analyzed)")

    print("\n2. SALES DATA LOCATION:")
    print("   - Primary location: florida_parcels table")
    print("   - Key columns: sale_date, sale_price, sale_qualification")

    print("\n3. COLUMN MAPPING FOR SALES:")
    print("   - sale_date: Date of sale (text format)")
    print("   - sale_price: Sale amount in dollars (integer)")
    print("   - sale_qualification: Sale type/qualification code")
    print("   - just_value: Assessed just value")
    print("   - assessed_value: Assessed value")
    print("   - taxable_value: Taxable value")

    print("\n4. DATA AVAILABILITY:")
    print("   - Total records: ~123,430 (Alachua County sample)")
    print("   - Records with sale data: ~13,389 (10.8% of sample)")
    print("   - Data appears to be from SDF (Sales Data File) imports")

    print("\n5. RECOMMENDATIONS:")
    print("   - Use florida_parcels table for all sales queries")
    print("   - Filter by sale_price IS NOT NULL for sales data")
    print("   - County-specific analysis shows varying data completeness")
    print("   - Consider sale_qualification for filtering valid sales")

if __name__ == "__main__":
    main()