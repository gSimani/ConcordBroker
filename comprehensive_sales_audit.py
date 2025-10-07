"""
Comprehensive Supabase Sales Data Audit
Examines all sales-related tables and provides detailed structure analysis
"""

from supabase import create_client
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseSalesAudit:
    def __init__(self):
        self.supabase = create_client(
            'https://pmispwtdngkcmsrsjwbp.supabase.co',
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'
        )

        # Tables to examine
        self.sales_tables = [
            'florida_parcels',
            'property_sales_history',
            'comprehensive_sales_data',
            'sdf_sales',
            'sales_history'
        ]

        self.audit_results = {}

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get comprehensive information about a table"""
        logger.info(f"Examining table: {table_name}")

        info = {
            'table_name': table_name,
            'exists': False,
            'row_count': 0,
            'columns': [],
            'sample_data': [],
            'sales_with_price': 0,
            'price_range': {'min': None, 'max': None, 'avg': None},
            'date_range': {'earliest': None, 'latest': None},
            'errors': []
        }

        try:
            # Test if table exists by trying to query it
            result = self.supabase.table(table_name).select('*').limit(1).execute()
            info['exists'] = True

            # Get row count
            count_result = self.supabase.table(table_name).select('*', count='exact').limit(1).execute()
            info['row_count'] = count_result.count if hasattr(count_result, 'count') else 0

            # Get sample data to understand structure
            sample_result = self.supabase.table(table_name).select('*').limit(5).execute()
            info['sample_data'] = sample_result.data if sample_result.data else []

            # Extract column information from sample data
            if info['sample_data']:
                info['columns'] = list(info['sample_data'][0].keys())
                logger.info(f"Found {len(info['columns'])} columns in {table_name}")

            # Analyze sales-specific data
            self._analyze_sales_data(table_name, info)

        except Exception as e:
            error_msg = f"Error examining {table_name}: {str(e)}"
            logger.error(error_msg)
            info['errors'].append(error_msg)

        return info

    def _analyze_sales_data(self, table_name: str, info: Dict[str, Any]):
        """Analyze sales-specific data in the table"""
        try:
            # Look for price-related columns
            price_columns = [col for col in info['columns'] if 'price' in col.lower() or 'value' in col.lower()]
            date_columns = [col for col in info['columns'] if 'date' in col.lower()]

            logger.info(f"Price columns in {table_name}: {price_columns}")
            logger.info(f"Date columns in {table_name}: {date_columns}")

            # For florida_parcels, look for sale_price specifically
            if table_name == 'florida_parcels':
                self._analyze_florida_parcels_sales(info)
            else:
                # For other tables, try to find sales data
                self._analyze_generic_sales_table(table_name, info, price_columns, date_columns)

        except Exception as e:
            error_msg = f"Error analyzing sales data in {table_name}: {str(e)}"
            logger.error(error_msg)
            info['errors'].append(error_msg)

    def _analyze_florida_parcels_sales(self, info: Dict[str, Any]):
        """Analyze sales data specifically in florida_parcels table"""
        try:
            # Count properties with sale_price > 1000
            result = self.supabase.table('florida_parcels')\
                .select('sale_price', count='exact')\
                .gt('sale_price', 1000)\
                .limit(1)\
                .execute()

            info['sales_with_price'] = result.count if hasattr(result, 'count') else 0

            # Get price statistics
            price_stats = self.supabase.table('florida_parcels')\
                .select('sale_price')\
                .gt('sale_price', 0)\
                .order('sale_price', desc=False)\
                .limit(1000)\
                .execute()

            if price_stats.data:
                prices = [float(row['sale_price']) for row in price_stats.data if row['sale_price']]
                if prices:
                    info['price_range']['min'] = min(prices)
                    info['price_range']['max'] = max(prices)
                    info['price_range']['avg'] = sum(prices) / len(prices)

            # Get date range for sales
            date_stats = self.supabase.table('florida_parcels')\
                .select('sale_date')\
                .not_.is_('sale_date', 'null')\
                .order('sale_date', desc=False)\
                .limit(1)\
                .execute()

            if date_stats.data:
                info['date_range']['earliest'] = date_stats.data[0]['sale_date']

            # Get latest date
            latest_date = self.supabase.table('florida_parcels')\
                .select('sale_date')\
                .not_.is_('sale_date', 'null')\
                .order('sale_date', desc=True)\
                .limit(1)\
                .execute()

            if latest_date.data:
                info['date_range']['latest'] = latest_date.data[0]['sale_date']

        except Exception as e:
            error_msg = f"Error analyzing florida_parcels sales: {str(e)}"
            logger.error(error_msg)
            info['errors'].append(error_msg)

    def _analyze_generic_sales_table(self, table_name: str, info: Dict[str, Any], price_columns: List[str], date_columns: List[str]):
        """Analyze sales data in generic sales tables"""
        try:
            if not price_columns:
                logger.info(f"No price columns found in {table_name}")
                return

            price_col = price_columns[0]  # Use first price column found

            # Count records with meaningful prices
            result = self.supabase.table(table_name)\
                .select(price_col, count='exact')\
                .gt(price_col, 1000)\
                .limit(1)\
                .execute()

            info['sales_with_price'] = result.count if hasattr(result, 'count') else 0

            # Get price range
            if info['sales_with_price'] > 0:
                price_data = self.supabase.table(table_name)\
                    .select(price_col)\
                    .gt(price_col, 0)\
                    .limit(1000)\
                    .execute()

                if price_data.data:
                    prices = [float(row[price_col]) for row in price_data.data if row[price_col]]
                    if prices:
                        info['price_range']['min'] = min(prices)
                        info['price_range']['max'] = max(prices)
                        info['price_range']['avg'] = sum(prices) / len(prices)

            # Analyze date range if date columns exist
            if date_columns:
                date_col = date_columns[0]
                try:
                    # Get earliest date
                    earliest = self.supabase.table(table_name)\
                        .select(date_col)\
                        .not_.is_(date_col, 'null')\
                        .order(date_col, desc=False)\
                        .limit(1)\
                        .execute()

                    if earliest.data:
                        info['date_range']['earliest'] = earliest.data[0][date_col]

                    # Get latest date
                    latest = self.supabase.table(table_name)\
                        .select(date_col)\
                        .not_.is_(date_col, 'null')\
                        .order(date_col, desc=True)\
                        .limit(1)\
                        .execute()

                    if latest.data:
                        info['date_range']['latest'] = latest.data[0][date_col]

                except Exception as e:
                    logger.warning(f"Could not analyze dates in {table_name}: {e}")

        except Exception as e:
            error_msg = f"Error analyzing generic sales table {table_name}: {str(e)}"
            logger.error(error_msg)
            info['errors'].append(error_msg)

    def find_sample_properties_with_sales(self, min_price: int = 1000, limit: int = 10) -> List[Dict[str, Any]]:
        """Find sample properties with confirmed sales data"""
        logger.info(f"Finding sample properties with sales over ${min_price}")

        sample_properties = []

        # Check florida_parcels first
        try:
            result = self.supabase.table('florida_parcels')\
                .select('parcel_id, county, sale_date, sale_price, sale_qualification, owner_name, phy_addr1')\
                .gt('sale_price', min_price)\
                .not_.is_('sale_date', 'null')\
                .order('sale_price', desc=True)\
                .limit(limit)\
                .execute()

            for row in result.data:
                sample_properties.append({
                    'source_table': 'florida_parcels',
                    'parcel_id': row['parcel_id'],
                    'county': row['county'],
                    'sale_date': row['sale_date'],
                    'sale_price': float(row['sale_price']),
                    'sale_qualification': row.get('sale_qualification', ''),
                    'owner_name': row.get('owner_name', ''),
                    'address': row.get('phy_addr1', '')
                })

        except Exception as e:
            logger.error(f"Error finding sample properties: {e}")

        return sample_properties

    def test_sales_service_functions(self, test_parcel_ids: List[str]) -> Dict[str, Any]:
        """Test the sales service functions with real data"""
        logger.info("Testing sales service functions")

        test_results = {
            'single_property_tests': [],
            'batch_test_results': {},
            'errors': []
        }

        try:
            # Import the sales service
            import sys
            sys.path.append('C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\api')
            from sales_history_service import get_property_sales_history, get_last_qualified_sale, batch_fetch_qualified_sales

            # Test individual property lookups
            for parcel_id in test_parcel_ids[:3]:  # Test first 3
                try:
                    sales_history = get_property_sales_history(parcel_id)
                    last_sale = get_last_qualified_sale(parcel_id)

                    test_results['single_property_tests'].append({
                        'parcel_id': parcel_id,
                        'sales_count': len(sales_history),
                        'has_last_sale': last_sale is not None,
                        'last_sale_price': last_sale['sale_price'] if last_sale else None,
                        'sales_data': sales_history
                    })

                except Exception as e:
                    test_results['errors'].append(f"Error testing {parcel_id}: {e}")

            # Test batch lookup
            try:
                batch_results = batch_fetch_qualified_sales(test_parcel_ids)
                test_results['batch_test_results'] = batch_results

            except Exception as e:
                test_results['errors'].append(f"Error in batch test: {e}")

        except Exception as e:
            test_results['errors'].append(f"Error importing sales service: {e}")

        return test_results

    def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run the complete audit"""
        logger.info("Starting comprehensive Supabase sales data audit")

        audit_report = {
            'audit_timestamp': datetime.now().isoformat(),
            'tables_examined': {},
            'sample_properties': [],
            'service_tests': {},
            'summary': {},
            'recommendations': []
        }

        # Examine all tables
        for table in self.sales_tables:
            audit_report['tables_examined'][table] = self.get_table_info(table)

        # Find sample properties with sales
        audit_report['sample_properties'] = self.find_sample_properties_with_sales()

        # Test sales service if we have sample data
        if audit_report['sample_properties']:
            test_parcel_ids = [prop['parcel_id'] for prop in audit_report['sample_properties'][:5]]
            audit_report['service_tests'] = self.test_sales_service_functions(test_parcel_ids)

        # Generate summary
        audit_report['summary'] = self._generate_summary(audit_report)

        # Generate recommendations
        audit_report['recommendations'] = self._generate_recommendations(audit_report)

        return audit_report

    def _generate_summary(self, audit_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of audit findings"""
        existing_tables = [name for name, info in audit_report['tables_examined'].items() if info['exists']]
        tables_with_sales = [name for name, info in audit_report['tables_examined'].items()
                           if info['exists'] and info['sales_with_price'] > 0]

        total_sales_records = sum(info['sales_with_price'] for info in audit_report['tables_examined'].values()
                                if info['exists'])

        return {
            'total_tables_examined': len(self.sales_tables),
            'existing_tables': existing_tables,
            'tables_with_sales_data': tables_with_sales,
            'total_sales_records_found': total_sales_records,
            'sample_properties_found': len(audit_report['sample_properties']),
            'service_test_passed': len(audit_report.get('service_tests', {}).get('errors', [])) == 0
        }

    def _generate_recommendations(self, audit_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on audit findings"""
        recommendations = []

        existing_tables = [name for name, info in audit_report['tables_examined'].items() if info['exists']]

        if 'florida_parcels' in existing_tables:
            parcels_info = audit_report['tables_examined']['florida_parcels']
            if parcels_info['sales_with_price'] > 0:
                recommendations.append("✅ Primary sales data available in florida_parcels table")
            else:
                recommendations.append("❌ No sales data found in florida_parcels table - investigate data import")

        if 'property_sales_history' not in existing_tables:
            recommendations.append("⚠️ Consider creating property_sales_history table for enhanced sales tracking")

        if audit_report['sample_properties']:
            recommendations.append(f"✅ Found {len(audit_report['sample_properties'])} sample properties with sales data")
        else:
            recommendations.append("❌ No sample properties with sales found - check data quality")

        # Check service test results
        service_tests = audit_report.get('service_tests', {})
        if service_tests.get('errors'):
            recommendations.append("❌ Sales service functions have errors - fix before deployment")
        else:
            recommendations.append("✅ Sales service functions working correctly")

        return recommendations

if __name__ == "__main__":
    auditor = SupabaseSalesAudit()
    results = auditor.run_comprehensive_audit()

    # Print results
    print("\n" + "="*80)
    print("COMPREHENSIVE SUPABASE SALES DATA AUDIT REPORT")
    print("="*80)

    print(f"\nAudit completed at: {results['audit_timestamp']}")

    print(f"\n📊 SUMMARY:")
    summary = results['summary']
    print(f"  • Tables examined: {summary['total_tables_examined']}")
    print(f"  • Tables existing: {len(summary['existing_tables'])}")
    print(f"  • Tables with sales data: {len(summary['tables_with_sales_data'])}")
    print(f"  • Total sales records: {summary['total_sales_records_found']:,}")
    print(f"  • Sample properties found: {summary['sample_properties_found']}")

    print(f"\n🗃️ TABLE DETAILS:")
    for table_name, info in results['tables_examined'].items():
        if info['exists']:
            print(f"  ✅ {table_name}:")
            print(f"     - Rows: {info['row_count']:,}")
            print(f"     - Columns: {len(info['columns'])}")
            print(f"     - Sales records (>$1000): {info['sales_with_price']:,}")
            if info['price_range']['avg']:
                print(f"     - Price range: ${info['price_range']['min']:,.0f} - ${info['price_range']['max']:,.0f} (avg: ${info['price_range']['avg']:,.0f})")
            if info['date_range']['earliest']:
                print(f"     - Date range: {info['date_range']['earliest']} to {info['date_range']['latest']}")
        else:
            print(f"  ❌ {table_name}: Table does not exist")

    print(f"\n🏠 SAMPLE PROPERTIES WITH SALES:")
    for prop in results['sample_properties'][:5]:
        print(f"  • {prop['parcel_id']} ({prop['county']}): ${prop['sale_price']:,.0f} on {prop['sale_date']}")

    print(f"\n🧪 SERVICE TESTS:")
    service_tests = results.get('service_tests', {})
    if service_tests.get('single_property_tests'):
        for test in service_tests['single_property_tests']:
            print(f"  • {test['parcel_id']}: {test['sales_count']} sales, last sale: ${test['last_sale_price']:,.0f}" if test['last_sale_price'] else f"  • {test['parcel_id']}: No sales found")

    print(f"\n💡 RECOMMENDATIONS:")
    for rec in results['recommendations']:
        print(f"  {rec}")

    # Save detailed results to file
    with open('sales_audit_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📝 Detailed results saved to: sales_audit_results.json")