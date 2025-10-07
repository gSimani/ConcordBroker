#!/usr/bin/env python3
"""
Florida Parcels Table Analysis
===============================
Detailed analysis of the florida_parcels table which contains 9.1M property records
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import create_engine, text, inspect
import pandas as pd

# Load environment variables
load_dotenv()

def get_db_url():
    """Get cleaned database URL"""
    url = os.getenv('DATABASE_URL')
    if url:
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql+psycopg2://', 1)
        if '&supa=' in url:
            url = url.split('&supa=')[0]
        if '&pgbouncer=' in url:
            url = url.split('&pgbouncer=')[0]
        return url
    raise ValueError("No DATABASE_URL found")

def analyze_florida_parcels():
    """Comprehensive analysis of florida_parcels table"""
    db_url = get_db_url()
    engine = create_engine(db_url, pool_size=5, max_overflow=10)

    analysis_results = {
        'analysis_timestamp': datetime.now().isoformat(),
        'table_name': 'florida_parcels'
    }

    with engine.connect() as conn:
        print("Analyzing florida_parcels table...")

        # 1. Basic Statistics
        print("1. Getting basic statistics...")
        basic_stats = conn.execute(text("""
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT parcel_id) as unique_parcels,
                COUNT(DISTINCT county) as unique_counties,
                MIN(year) as earliest_year,
                MAX(year) as latest_year
            FROM florida_parcels
        """)).fetchone()

        analysis_results['basic_stats'] = {
            'total_records': basic_stats[0],
            'unique_parcels': basic_stats[1],
            'unique_counties': basic_stats[2],
            'earliest_year': basic_stats[3],
            'latest_year': basic_stats[4]
        }

        # 2. County Distribution
        print("2. Analyzing county distribution...")
        county_dist = conn.execute(text("""
            SELECT
                county,
                COUNT(*) as property_count,
                COUNT(DISTINCT year) as year_coverage,
                MIN(year) as earliest_year,
                MAX(year) as latest_year
            FROM florida_parcels
            WHERE county IS NOT NULL
            GROUP BY county
            ORDER BY property_count DESC
        """)).fetchall()

        analysis_results['county_distribution'] = [
            {
                'county': row[0],
                'property_count': row[1],
                'year_coverage': row[2],
                'earliest_year': row[3],
                'latest_year': row[4]
            } for row in county_dist
        ]

        # 3. Year Distribution
        print("3. Analyzing year distribution...")
        year_dist = conn.execute(text("""
            SELECT
                year,
                COUNT(*) as property_count,
                COUNT(DISTINCT county) as county_coverage
            FROM florida_parcels
            WHERE year IS NOT NULL
            GROUP BY year
            ORDER BY year DESC
        """)).fetchall()

        analysis_results['year_distribution'] = [
            {
                'year': row[0],
                'property_count': row[1],
                'county_coverage': row[2]
            } for row in year_dist
        ]

        # 4. Column Completeness Analysis
        print("4. Analyzing column completeness...")

        # Get all columns first
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('florida_parcels')]

        # Key fields to analyze
        key_fields = [
            'parcel_id', 'county', 'year', 'phy_addr1', 'phy_addr2',
            'owner_name1', 'owner_name2', 'just_value', 'land_value',
            'building_value', 'land_sqft', 'living_units', 'bedrooms',
            'bathrooms', 'year_built', 'property_use_code', 'deed_book',
            'deed_page', 'sale_date', 'sale_price', 'sale_year1', 'sale_mo1'
        ]

        completeness_analysis = {}

        for field in key_fields:
            if field in columns:
                try:
                    result = conn.execute(text(f"""
                        SELECT
                            COUNT(*) as total,
                            COUNT({field}) as non_null,
                            ROUND(COUNT({field}) * 100.0 / COUNT(*), 2) as completeness_percentage
                        FROM florida_parcels
                    """)).fetchone()

                    completeness_analysis[field] = {
                        'total_records': result[0],
                        'non_null_records': result[1],
                        'completeness_percentage': float(result[2])
                    }

                    print(f"  {field}: {result[2]}% complete")

                except Exception as e:
                    print(f"  Error analyzing {field}: {e}")
                    completeness_analysis[field] = {'error': str(e)}

        analysis_results['column_completeness'] = completeness_analysis

        # 5. Value Analysis
        print("5. Analyzing property values...")
        value_stats = conn.execute(text("""
            SELECT
                COUNT(CASE WHEN just_value > 0 THEN 1 END) as properties_with_value,
                AVG(CASE WHEN just_value > 0 THEN just_value END) as avg_just_value,
                MIN(CASE WHEN just_value > 0 THEN just_value END) as min_just_value,
                MAX(just_value) as max_just_value,
                COUNT(CASE WHEN land_value > 0 THEN 1 END) as properties_with_land_value,
                AVG(CASE WHEN land_value > 0 THEN land_value END) as avg_land_value,
                COUNT(CASE WHEN building_value > 0 THEN 1 END) as properties_with_building_value,
                AVG(CASE WHEN building_value > 0 THEN building_value END) as avg_building_value
            FROM florida_parcels
        """)).fetchone()

        analysis_results['value_analysis'] = {
            'properties_with_value': value_stats[0],
            'avg_just_value': float(value_stats[1]) if value_stats[1] else 0,
            'min_just_value': float(value_stats[2]) if value_stats[2] else 0,
            'max_just_value': float(value_stats[3]) if value_stats[3] else 0,
            'properties_with_land_value': value_stats[4],
            'avg_land_value': float(value_stats[5]) if value_stats[5] else 0,
            'properties_with_building_value': value_stats[6],
            'avg_building_value': float(value_stats[7]) if value_stats[7] else 0
        }

        # 6. Sales Data Analysis
        print("6. Analyzing sales data...")
        sales_stats = conn.execute(text("""
            SELECT
                COUNT(CASE WHEN sale_date IS NOT NULL THEN 1 END) as properties_with_sale_date,
                COUNT(CASE WHEN sale_price > 0 THEN 1 END) as properties_with_sale_price,
                AVG(CASE WHEN sale_price > 0 THEN sale_price END) as avg_sale_price,
                MIN(CASE WHEN sale_price > 0 THEN sale_price END) as min_sale_price,
                MAX(sale_price) as max_sale_price,
                COUNT(CASE WHEN sale_year1 IS NOT NULL THEN 1 END) as properties_with_sale_year
            FROM florida_parcels
        """)).fetchone()

        analysis_results['sales_analysis'] = {
            'properties_with_sale_date': sales_stats[0],
            'properties_with_sale_price': sales_stats[1],
            'avg_sale_price': float(sales_stats[2]) if sales_stats[2] else 0,
            'min_sale_price': float(sales_stats[3]) if sales_stats[3] else 0,
            'max_sale_price': float(sales_stats[4]) if sales_stats[4] else 0,
            'properties_with_sale_year': sales_stats[5]
        }

        # 7. Property Characteristics
        print("7. Analyzing property characteristics...")
        char_stats = conn.execute(text("""
            SELECT
                COUNT(CASE WHEN land_sqft > 0 THEN 1 END) as properties_with_land_sqft,
                AVG(CASE WHEN land_sqft > 0 THEN land_sqft END) as avg_land_sqft,
                COUNT(CASE WHEN living_units > 0 THEN 1 END) as properties_with_living_units,
                AVG(CASE WHEN living_units > 0 THEN living_units END) as avg_living_units,
                COUNT(CASE WHEN bedrooms > 0 THEN 1 END) as properties_with_bedrooms,
                AVG(CASE WHEN bedrooms > 0 THEN bedrooms END) as avg_bedrooms,
                COUNT(CASE WHEN year_built > 0 THEN 1 END) as properties_with_year_built,
                AVG(CASE WHEN year_built > 0 THEN year_built END) as avg_year_built
            FROM florida_parcels
        """)).fetchone()

        analysis_results['property_characteristics'] = {
            'properties_with_land_sqft': char_stats[0],
            'avg_land_sqft': float(char_stats[1]) if char_stats[1] else 0,
            'properties_with_living_units': char_stats[2],
            'avg_living_units': float(char_stats[3]) if char_stats[3] else 0,
            'properties_with_bedrooms': char_stats[4],
            'avg_bedrooms': float(char_stats[5]) if char_stats[5] else 0,
            'properties_with_year_built': char_stats[6],
            'avg_year_built': float(char_stats[7]) if char_stats[7] else 0
        }

        # 8. Data Quality Issues
        print("8. Identifying data quality issues...")
        quality_issues = conn.execute(text("""
            SELECT
                COUNT(CASE WHEN parcel_id IS NULL OR parcel_id = '' THEN 1 END) as missing_parcel_id,
                COUNT(CASE WHEN county IS NULL OR county = '' THEN 1 END) as missing_county,
                COUNT(CASE WHEN year IS NULL THEN 1 END) as missing_year,
                COUNT(CASE WHEN just_value < 0 THEN 1 END) as negative_just_value,
                COUNT(CASE WHEN land_value < 0 THEN 1 END) as negative_land_value,
                COUNT(CASE WHEN sale_price < 0 THEN 1 END) as negative_sale_price,
                COUNT(CASE WHEN year_built > EXTRACT(YEAR FROM CURRENT_DATE) THEN 1 END) as future_year_built,
                COUNT(CASE WHEN living_units > 100 THEN 1 END) as excessive_living_units
            FROM florida_parcels
        """)).fetchone()

        analysis_results['data_quality_issues'] = {
            'missing_parcel_id': quality_issues[0],
            'missing_county': quality_issues[1],
            'missing_year': quality_issues[2],
            'negative_just_value': quality_issues[3],
            'negative_land_value': quality_issues[4],
            'negative_sale_price': quality_issues[5],
            'future_year_built': quality_issues[6],
            'excessive_living_units': quality_issues[7]
        }

        # 9. Sample Records for Specific Properties
        print("9. Searching for specific properties...")
        specific_parcels = ['1078130000370', '504231242730']

        for parcel_id in specific_parcels:
            print(f"  Searching for parcel: {parcel_id}")
            sample_data = conn.execute(text("""
                SELECT * FROM florida_parcels
                WHERE parcel_id = :parcel_id
                LIMIT 5
            """), {'parcel_id': parcel_id}).fetchall()

            if sample_data:
                # Get column names
                columns = conn.execute(text("SELECT * FROM florida_parcels LIMIT 1")).keys()

                analysis_results[f'property_{parcel_id}'] = {
                    'found': True,
                    'record_count': len(sample_data),
                    'sample_records': [
                        {col: (row[i].isoformat() if hasattr(row[i], 'isoformat') else row[i])
                         for i, col in enumerate(columns)}
                        for row in sample_data
                    ]
                }
                print(f"    Found {len(sample_data)} records")
            else:
                analysis_results[f'property_{parcel_id}'] = {
                    'found': False,
                    'record_count': 0
                }
                print(f"    No records found")

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"florida_parcels_analysis_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)

    print(f"\nAnalysis complete! Results saved to {output_file}")

    # Print summary
    print("\n" + "="*60)
    print("FLORIDA PARCELS ANALYSIS SUMMARY")
    print("="*60)

    basic = analysis_results['basic_stats']
    print(f"Total Records: {basic['total_records']:,}")
    print(f"Unique Parcels: {basic['unique_parcels']:,}")
    print(f"Counties Covered: {basic['unique_counties']}")
    print(f"Year Range: {basic['earliest_year']} - {basic['latest_year']}")

    # Top counties by property count
    print(f"\nTop 10 Counties by Property Count:")
    for i, county in enumerate(analysis_results['county_distribution'][:10], 1):
        print(f"{i:2d}. {county['county']:<15} {county['property_count']:>8,} properties")

    # Data completeness for key fields
    print(f"\nKey Field Completeness:")
    completeness = analysis_results['column_completeness']
    key_fields = ['parcel_id', 'county', 'phy_addr1', 'owner_name1', 'just_value', 'land_sqft']
    for field in key_fields:
        if field in completeness:
            pct = completeness[field].get('completeness_percentage', 0)
            print(f"  {field:<15}: {pct:>6.1f}%")

    # Value insights
    value_analysis = analysis_results['value_analysis']
    print(f"\nValue Analysis:")
    print(f"  Properties with value: {value_analysis['properties_with_value']:,}")
    print(f"  Average just value: ${value_analysis['avg_just_value']:,.0f}")
    print(f"  Max just value: ${value_analysis['max_just_value']:,.0f}")

    # Sales insights
    sales_analysis = analysis_results['sales_analysis']
    print(f"\nSales Data:")
    print(f"  Properties with sale data: {sales_analysis['properties_with_sale_date']:,}")
    print(f"  Properties with sale price: {sales_analysis['properties_with_sale_price']:,}")
    if sales_analysis['avg_sale_price'] > 0:
        print(f"  Average sale price: ${sales_analysis['avg_sale_price']:,.0f}")

    # Data quality
    quality = analysis_results['data_quality_issues']
    total_records = basic['total_records']
    print(f"\nData Quality Issues:")
    for issue, count in quality.items():
        if count > 0:
            pct = (count / total_records * 100)
            print(f"  {issue}: {count:,} ({pct:.2f}%)")

    print("="*60)

    return analysis_results

if __name__ == "__main__":
    analyze_florida_parcels()