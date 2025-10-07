"""
Data Quality Assessment for Sales Data
Analyzes data consistency, completeness, and quality issues
"""

from supabase import create_client
import pandas as pd
from datetime import datetime, date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityAssessment:
    def __init__(self):
        self.supabase = create_client(
            'https://pmispwtdngkcmsrsjwbp.supabase.co',
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'
        )

    def analyze_florida_parcels_quality(self):
        """Analyze data quality in florida_parcels table"""
        print("Analyzing florida_parcels data quality...")

        # Get sample of data for analysis
        sample_data = self.supabase.table('florida_parcels')\
            .select('*')\
            .limit(1000)\
            .execute()

        if not sample_data.data:
            print("  No data found in florida_parcels table")
            return {}

        df = pd.DataFrame(sample_data.data)

        quality_issues = {
            'missing_values': {},
            'data_type_issues': {},
            'value_inconsistencies': {},
            'date_issues': {},
            'price_issues': {}
        }

        # Check for missing values in critical fields
        critical_fields = ['parcel_id', 'county', 'sale_price', 'sale_date', 'owner_name']
        for field in critical_fields:
            if field in df.columns:
                missing_count = df[field].isnull().sum()
                missing_percent = (missing_count / len(df)) * 100
                quality_issues['missing_values'][field] = {
                    'count': missing_count,
                    'percentage': missing_percent
                }
                if missing_percent > 10:
                    print(f"  WARNING: {field} has {missing_percent:.1f}% missing values")

        # Analyze sale price issues
        if 'sale_price' in df.columns:
            sale_prices = pd.to_numeric(df['sale_price'], errors='coerce')

            # Zero prices
            zero_prices = (sale_prices == 0).sum()
            quality_issues['price_issues']['zero_prices'] = zero_prices

            # Negative prices
            negative_prices = (sale_prices < 0).sum()
            quality_issues['price_issues']['negative_prices'] = negative_prices

            # Extremely high prices (potential data errors)
            extremely_high = (sale_prices > 100000000).sum()  # > $100M
            quality_issues['price_issues']['extremely_high'] = extremely_high

            # Very low prices (potential gift transfers)
            very_low = ((sale_prices > 0) & (sale_prices < 1000)).sum()
            quality_issues['price_issues']['very_low'] = very_low

            print(f"  Sale price analysis:")
            print(f"    Zero prices: {zero_prices}")
            print(f"    Negative prices: {negative_prices}")
            print(f"    Extremely high (>$100M): {extremely_high}")
            print(f"    Very low ($1-$999): {very_low}")

        # Analyze date consistency
        if 'sale_date' in df.columns:
            date_issues = 0
            future_dates = 0

            for idx, date_val in df['sale_date'].dropna().items():
                try:
                    if isinstance(date_val, str):
                        parsed_date = pd.to_datetime(date_val)
                        if parsed_date > pd.Timestamp.now():
                            future_dates += 1
                except:
                    date_issues += 1

            quality_issues['date_issues']['unparseable_dates'] = date_issues
            quality_issues['date_issues']['future_dates'] = future_dates

            print(f"  Date analysis:")
            print(f"    Unparseable dates: {date_issues}")
            print(f"    Future dates: {future_dates}")

        # Check for duplicate parcel IDs
        if 'parcel_id' in df.columns:
            duplicates = df['parcel_id'].duplicated().sum()
            quality_issues['value_inconsistencies']['duplicate_parcel_ids'] = duplicates
            print(f"  Duplicate parcel IDs: {duplicates}")

        return quality_issues

    def analyze_property_sales_history_quality(self):
        """Analyze data quality in property_sales_history table"""
        print("\nAnalyzing property_sales_history data quality...")

        try:
            # Get sample of data for analysis
            sample_data = self.supabase.table('property_sales_history')\
                .select('*')\
                .limit(1000)\
                .execute()

            if not sample_data.data:
                print("  No data found in property_sales_history table")
                return {}

            df = pd.DataFrame(sample_data.data)

            quality_issues = {
                'missing_values': {},
                'data_consistency': {},
                'quality_codes': {}
            }

            # Check critical fields
            critical_fields = ['parcel_id', 'sale_price', 'sale_date', 'quality_code']
            for field in critical_fields:
                if field in df.columns:
                    missing_count = df[field].isnull().sum()
                    missing_percent = (missing_count / len(df)) * 100
                    quality_issues['missing_values'][field] = {
                        'count': missing_count,
                        'percentage': missing_percent
                    }

            # Analyze quality codes
            if 'quality_code' in df.columns:
                quality_codes = df['quality_code'].value_counts()
                quality_issues['quality_codes'] = quality_codes.to_dict()

                print(f"  Quality code distribution:")
                for code, count in quality_codes.head(10).items():
                    print(f"    {code}: {count}")

            # Compare with florida_parcels for consistency
            parcel_ids_sample = df['parcel_id'].dropna().head(10).tolist()
            if parcel_ids_sample:
                # Check if these parcels exist in florida_parcels
                florida_data = self.supabase.table('florida_parcels')\
                    .select('parcel_id, sale_price, sale_date')\
                    .in_('parcel_id', parcel_ids_sample)\
                    .execute()

                florida_df = pd.DataFrame(florida_data.data)

                # Compare sale prices for consistency
                inconsistencies = 0
                for parcel_id in parcel_ids_sample:
                    history_row = df[df['parcel_id'] == parcel_id].iloc[0] if len(df[df['parcel_id'] == parcel_id]) > 0 else None
                    florida_row = florida_df[florida_df['parcel_id'] == parcel_id].iloc[0] if len(florida_df[florida_df['parcel_id'] == parcel_id]) > 0 else None

                    if history_row is not None and florida_row is not None:
                        if float(history_row['sale_price']) != float(florida_row['sale_price']):
                            inconsistencies += 1

                quality_issues['data_consistency']['price_inconsistencies'] = inconsistencies
                print(f"  Price inconsistencies with florida_parcels: {inconsistencies}/{len(parcel_ids_sample)}")

            return quality_issues

        except Exception as e:
            print(f"  Error analyzing property_sales_history: {e}")
            return {}

    def cross_table_consistency_check(self):
        """Check consistency between different sales tables"""
        print("\nChecking cross-table consistency...")

        try:
            # Get a sample of parcels that exist in both tables
            florida_sample = self.supabase.table('florida_parcels')\
                .select('parcel_id, sale_price, sale_date')\
                .gt('sale_price', 1000)\
                .limit(50)\
                .execute()

            if not florida_sample.data:
                print("  No sample data found")
                return {}

            parcels_to_check = [row['parcel_id'] for row in florida_sample.data]

            # Check if these parcels exist in property_sales_history
            history_data = self.supabase.table('property_sales_history')\
                .select('parcel_id, sale_price, sale_date')\
                .in_('parcel_id', parcels_to_check)\
                .execute()

            consistency_report = {
                'total_parcels_checked': len(parcels_to_check),
                'found_in_history_table': len(history_data.data),
                'price_matches': 0,
                'date_matches': 0,
                'discrepancies': []
            }

            # Compare data
            history_dict = {row['parcel_id']: row for row in history_data.data}

            for florida_row in florida_sample.data:
                parcel_id = florida_row['parcel_id']
                if parcel_id in history_dict:
                    history_row = history_dict[parcel_id]

                    # Compare prices
                    if abs(float(florida_row['sale_price']) - float(history_row['sale_price'])) < 0.01:
                        consistency_report['price_matches'] += 1
                    else:
                        consistency_report['discrepancies'].append({
                            'parcel_id': parcel_id,
                            'florida_price': florida_row['sale_price'],
                            'history_price': history_row['sale_price'],
                            'type': 'price_mismatch'
                        })

                    # Compare dates
                    if florida_row['sale_date'] == history_row['sale_date']:
                        consistency_report['date_matches'] += 1

            print(f"  Parcels checked: {consistency_report['total_parcels_checked']}")
            print(f"  Found in history table: {consistency_report['found_in_history_table']}")
            print(f"  Price matches: {consistency_report['price_matches']}")
            print(f"  Date matches: {consistency_report['date_matches']}")
            print(f"  Discrepancies found: {len(consistency_report['discrepancies'])}")

            return consistency_report

        except Exception as e:
            print(f"  Error in consistency check: {e}")
            return {}

    def analyze_data_completeness(self):
        """Analyze data completeness across counties"""
        print("\nAnalyzing data completeness by county...")

        try:
            # Get county-level statistics
            county_stats = self.supabase.table('florida_parcels')\
                .select('county, sale_price, sale_date', count='exact')\
                .execute()

            # Group by county manually since Supabase doesn't support GROUP BY in simple queries
            county_data = {}
            for row in county_stats.data:
                county = row['county']
                if county not in county_data:
                    county_data[county] = {
                        'total_properties': 0,
                        'properties_with_sales': 0,
                        'properties_with_dates': 0
                    }

                county_data[county]['total_properties'] += 1

                if row['sale_price'] and float(row['sale_price']) > 0:
                    county_data[county]['properties_with_sales'] += 1

                if row['sale_date']:
                    county_data[county]['properties_with_dates'] += 1

            # Calculate completeness percentages
            completeness_report = {}
            for county, stats in county_data.items():
                if stats['total_properties'] > 0:
                    completeness_report[county] = {
                        'total_properties': stats['total_properties'],
                        'sales_completeness': (stats['properties_with_sales'] / stats['total_properties']) * 100,
                        'date_completeness': (stats['properties_with_dates'] / stats['total_properties']) * 100
                    }

            # Show top and bottom counties by completeness
            sorted_counties = sorted(completeness_report.items(),
                                   key=lambda x: x[1]['sales_completeness'], reverse=True)

            print(f"  Counties with highest sales data completeness:")
            for county, stats in sorted_counties[:5]:
                print(f"    {county}: {stats['sales_completeness']:.1f}% sales, {stats['date_completeness']:.1f}% dates")

            print(f"  Counties with lowest sales data completeness:")
            for county, stats in sorted_counties[-5:]:
                print(f"    {county}: {stats['sales_completeness']:.1f}% sales, {stats['date_completeness']:.1f}% dates")

            return completeness_report

        except Exception as e:
            print(f"  Error in completeness analysis: {e}")
            return {}

    def run_full_assessment(self):
        """Run the complete data quality assessment"""
        print("="*60)
        print("DATA QUALITY ASSESSMENT FOR SALES DATA")
        print("="*60)
        print(f"Assessment time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        assessment_results = {
            'florida_parcels_quality': self.analyze_florida_parcels_quality(),
            'property_sales_history_quality': self.analyze_property_sales_history_quality(),
            'cross_table_consistency': self.cross_table_consistency_check(),
            'data_completeness': self.analyze_data_completeness()
        }

        # Generate summary and recommendations
        print("\n" + "="*60)
        print("QUALITY ASSESSMENT SUMMARY")
        print("="*60)

        recommendations = []

        # Analyze florida_parcels issues
        fp_quality = assessment_results['florida_parcels_quality']
        if fp_quality:
            price_issues = fp_quality.get('price_issues', {})
            if price_issues.get('extremely_high', 0) > 0:
                recommendations.append(f"Review {price_issues['extremely_high']} properties with sale prices >$100M for data entry errors")

            if price_issues.get('negative_prices', 0) > 0:
                recommendations.append(f"Fix {price_issues['negative_prices']} properties with negative sale prices")

        # Analyze consistency issues
        consistency = assessment_results['cross_table_consistency']
        if consistency and consistency.get('discrepancies'):
            recommendations.append(f"Investigate {len(consistency['discrepancies'])} price discrepancies between tables")

        # Analyze completeness
        completeness = assessment_results['data_completeness']
        if completeness:
            low_completeness_counties = [county for county, stats in completeness.items()
                                       if stats['sales_completeness'] < 20]
            if low_completeness_counties:
                recommendations.append(f"Improve sales data collection for {len(low_completeness_counties)} counties with <20% completeness")

        print("Key Findings:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("  No major data quality issues found")

        print(f"\nOverall Assessment: Data quality is {'GOOD' if len(recommendations) <= 2 else 'NEEDS IMPROVEMENT'}")

        return assessment_results

if __name__ == "__main__":
    assessor = DataQualityAssessment()
    assessor.run_full_assessment()