"""
Analyze all sales data available in various files
"""

import csv
import os

def analyze_sdf_file():
    """Analyze the SDF sales file"""
    print("ANALYZING SDF FILE (SDF16P202501.csv)")
    print("=" * 60)
    
    if not os.path.exists('SDF16P202501.csv'):
        print("SDF file not found")
        return
    
    total_records = 0
    unique_parcels = set()
    sales_by_year = {}
    price_ranges = {
        '0-100k': 0,
        '100k-500k': 0,
        '500k-1M': 0,
        '1M+': 0
    }
    
    with open('SDF16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            total_records += 1
            
            parcel_id = row.get('PARCEL_ID', '').strip()
            if parcel_id:
                unique_parcels.add(parcel_id)
            
            try:
                price = int(float(row.get('SALE_PRC', 0) or 0))
                year = int(float(row.get('SALE_YR', 0) or 0))
                
                if year >= 2000:
                    sales_by_year[year] = sales_by_year.get(year, 0) + 1
                
                if price > 0:
                    if price < 100000:
                        price_ranges['0-100k'] += 1
                    elif price < 500000:
                        price_ranges['100k-500k'] += 1
                    elif price < 1000000:
                        price_ranges['500k-1M'] += 1
                    else:
                        price_ranges['1M+'] += 1
            except:
                pass
    
    print(f"Total sale records: {total_records:,}")
    print(f"Unique properties with sales: {len(unique_parcels):,}")
    print(f"Average sales per property: {total_records/len(unique_parcels) if unique_parcels else 0:.1f}")
    
    print("\nSales by year (recent):")
    for year in sorted(sales_by_year.keys())[-10:]:
        print(f"  {year}: {sales_by_year[year]:,} sales")
    
    print("\nPrice ranges:")
    for range_name, count in price_ranges.items():
        print(f"  {range_name}: {count:,} sales")

def analyze_nal_sales():
    """Check how many properties have sales in NAL file"""
    print("\n\nANALYZING NAL FILE SALES DATA")
    print("=" * 60)
    
    if not os.path.exists('NAL16P202501.csv'):
        print("NAL file not found")
        return
    
    properties_with_sale1 = 0
    properties_with_sale2 = 0
    total_properties = 0
    
    with open('NAL16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            total_properties += 1
            
            # Check first sale
            if row.get('SALE_PRC1') and row['SALE_PRC1'].strip():
                try:
                    price = float(row['SALE_PRC1'])
                    if price > 0:
                        properties_with_sale1 += 1
                except:
                    pass
            
            # Check second sale
            if row.get('SALE_PRC2') and row['SALE_PRC2'].strip():
                try:
                    price = float(row['SALE_PRC2'])
                    if price > 0:
                        properties_with_sale2 += 1
                except:
                    pass
    
    print(f"Total properties: {total_properties:,}")
    print(f"Properties with Sale 1 data: {properties_with_sale1:,}")
    print(f"Properties with Sale 2 data: {properties_with_sale2:,}")
    print(f"Total potential sales: {properties_with_sale1 + properties_with_sale2:,}")

def main():
    print("COMPREHENSIVE SALES DATA ANALYSIS")
    print("=" * 60)
    
    # Analyze SDF file
    analyze_sdf_file()
    
    # Analyze NAL file
    analyze_nal_sales()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("The SDF file contains detailed sales transaction records.")
    print("Each property can have multiple sales (hence 95k records).")
    print("The NAL file may also contain the two most recent sales per property.")
    print("\nTo get complete sales history:")
    print("1. Load all SDF records (transaction-level data)")
    print("2. Also extract SALE_PRC1/SALE_YR1 and SALE_PRC2/SALE_YR2 from NAL")
    print("3. Combine both sources for comprehensive sales history")

if __name__ == "__main__":
    main()