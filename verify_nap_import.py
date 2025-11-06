#!/usr/bin/env python3
"""
NAP Import Verification and Performance Testing
- Verifies data import completeness and quality
- Tests query performance for website operations
- Validates data integrity
"""

import time
from datetime import datetime
from supabase import create_client, Client`r`nimport os`r`nfrom dotenv import load_dotenv`r`n
class NAPImportVerifier:
    def __init__(self):
        # Supabase connection
        self.url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
        self.service_key = "REDACTED"
        self.supabase = load_dotenv('.env.mcp');
SUPABASE_URL = os.getenv('SUPABASE_URL') or globals().get('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY') or globals().get('SUPABASE_KEY', '')
self.url, self.service_key)

    def time_query(self, description, query_func):
        """Time a query and return results with performance metrics"""
        print(f"\n{description}")
        start_time = time.time()
        try:
            result = query_func()
            end_time = time.time()
            query_time = end_time - start_time
            print(f"  ✓ Completed in {query_time:.3f}s")
            return result, query_time, True
        except Exception as e:
            end_time = time.time()
            query_time = end_time - start_time
            print(f"  ✗ Failed in {query_time:.3f}s: {str(e)[:100]}")
            return None, query_time, False

    def verify_data_volume(self):
        """Verify data import volume and completeness"""
        print("=== DATA VOLUME VERIFICATION ===")
        
        # Total records
        def get_total_count():
            result = self.supabase.table('florida_parcels').select("*", count="exact").limit(1).execute()
            return result.count if hasattr(result, 'count') else 0
        
        total_count, query_time, success = self.time_query("Getting total record count", get_total_count)
        if success:
            print(f"  Total records: {total_count:,}")
        
        # Records with owner names (populated data)
        def get_populated_count():
            result = self.supabase.table('florida_parcels')\
                .select("*", count="exact")\
                .not_.is_('owner_name', 'null')\
                .limit(1).execute()
            return result.count if hasattr(result, 'count') else 0
        
        populated_count, query_time, success = self.time_query("Getting populated records count", get_populated_count)
        if success:
            print(f"  Records with owner names: {populated_count:,}")
            if total_count > 0:
                population_rate = (populated_count / total_count) * 100
                print(f"  Population rate: {population_rate:.1f}%")
        
        # NAP-specific records
        def get_nap_count():
            result = self.supabase.table('florida_parcels')\
                .select("*", count="exact")\
                .eq('data_source', 'NAP_2025')\
                .limit(1).execute()
            return result.count if hasattr(result, 'count') else 0
        
        nap_count, query_time, success = self.time_query("Getting NAP records count", get_nap_count)
        if success:
            print(f"  NAP 2025 records: {nap_count:,}")

    def verify_data_quality(self):
        """Verify data quality and integrity"""
        print("\n=== DATA QUALITY VERIFICATION ===")
        
        # Sample records with complete data
        def get_sample_records():
            return self.supabase.table('florida_parcels')\
                .select("parcel_id,owner_name,phy_addr1,phy_city,phy_zipcd,just_value,assessed_value,taxable_value")\
                .not_.is_('owner_name', 'null')\
                .not_.is_('phy_addr1', 'null')\
                .limit(10).execute()
        
        sample_result, query_time, success = self.time_query("Getting sample complete records", get_sample_records)
        if success and sample_result.data:
            print(f"  Sample records with complete data: {len(sample_result.data)}")
            for i, record in enumerate(sample_result.data[:3]):
                parcel_id = record.get('parcel_id', 'N/A')
                owner = record.get('owner_name', 'N/A')[:30]
                address = record.get('phy_addr1', 'N/A')[:30]
                city = record.get('phy_city', 'N/A')
                value = record.get('just_value', 0)
                print(f"    {i+1}. {parcel_id} | {owner} | {address} | {city} | ${value:,.2f}" if value else f"    {i+1}. {parcel_id} | {owner} | {address} | {city}")
        
        # Value distribution
        def get_value_stats():
            return self.supabase.table('florida_parcels')\
                .select("just_value,assessed_value,taxable_value")\
                .not_.is_('just_value', 'null')\
                .order('just_value', desc=True)\
                .limit(5).execute()
        
        value_result, query_time, success = self.time_query("Getting value statistics", get_value_stats)
        if success and value_result.data:
            print(f"  Top 5 properties by just value:")
            for i, record in enumerate(value_result.data):
                just_val = record.get('just_value', 0)
                assessed_val = record.get('assessed_value', 0)
                taxable_val = record.get('taxable_value', 0)
                print(f"    {i+1}. Just: ${just_val:,.2f} | Assessed: ${assessed_val:,.2f} | Taxable: ${taxable_val:,.2f}")

    def test_search_performance(self):
        """Test website search query performance"""
        print("\n=== SEARCH PERFORMANCE TESTING ===")
        
        # Test 1: Parcel ID lookup (most common query)
        def test_parcel_lookup():
            return self.supabase.table('florida_parcels')\
                .select("*")\
                .eq('parcel_id', '474131031040')\
                .execute()
        
        parcel_result, query_time, success = self.time_query("Test 1: Parcel ID lookup", test_parcel_lookup)
        if success:
            print(f"  Found {len(parcel_result.data) if parcel_result.data else 0} record(s)")
        
        # Test 2: Owner name search
        def test_owner_search():
            return self.supabase.table('florida_parcels')\
                .select("parcel_id,owner_name,phy_addr1,phy_city,just_value")\
                .ilike('owner_name', '%INVITATION HOMES%')\
                .limit(20).execute()
        
        owner_result, query_time, success = self.time_query("Test 2: Owner name search (INVITATION HOMES)", test_owner_search)
        if success:
            print(f"  Found {len(owner_result.data) if owner_result.data else 0} record(s)")
        
        # Test 3: City-based search
        def test_city_search():
            return self.supabase.table('florida_parcels')\
                .select("parcel_id,owner_name,phy_addr1,just_value")\
                .eq('phy_city', 'PARKLAND')\
                .limit(50).execute()
        
        city_result, query_time, success = self.time_query("Test 3: City search (PARKLAND)", test_city_search)
        if success:
            print(f"  Found {len(city_result.data) if city_result.data else 0} record(s)")
        
        # Test 4: Value range search
        def test_value_search():
            return self.supabase.table('florida_parcels')\
                .select("parcel_id,owner_name,phy_addr1,phy_city,just_value")\
                .gte('just_value', 1000000)\
                .order('just_value', desc=True)\
                .limit(25).execute()
        
        value_result, query_time, success = self.time_query("Test 4: High value properties (>$1M)", test_value_search)
        if success:
            print(f"  Found {len(value_result.data) if value_result.data else 0} record(s)")
        
        # Test 5: Zip code search  
        def test_zip_search():
            return self.supabase.table('florida_parcels')\
                .select("parcel_id,owner_name,phy_addr1,just_value")\
                .eq('phy_zipcd', '33076')\
                .limit(30).execute()
        
        zip_result, query_time, success = self.time_query("Test 5: Zip code search (33076)", test_zip_search)
        if success:
            print(f"  Found {len(zip_result.data) if zip_result.data else 0} record(s)")

    def test_aggregation_queries(self):
        """Test aggregation queries for analytics"""
        print("\n=== AGGREGATION PERFORMANCE TESTING ===")
        
        # Test 1: Property count by city
        def test_city_counts():
            return self.supabase.table('florida_parcels')\
                .select("phy_city", count="exact")\
                .not_.is_('phy_city', 'null')\
                .limit(1).execute()
        
        city_count_result, query_time, success = self.time_query("Test 1: Property count analysis", test_city_counts)
        
        # Test 2: Average values by zip code  
        def test_avg_values():
            return self.supabase.table('florida_parcels')\
                .select("phy_zipcd,just_value")\
                .not_.is_('just_value', 'null')\
                .eq('phy_zipcd', '33076')\
                .limit(100).execute()
        
        avg_result, query_time, success = self.time_query("Test 2: Average value calculation", test_avg_values)
        if success and avg_result.data:
            values = [r['just_value'] for r in avg_result.data if r.get('just_value')]
            if values:
                avg_value = sum(values) / len(values)
                print(f"  Average just value for zip 33076: ${avg_value:,.2f} (from {len(values)} properties)")

    def generate_performance_report(self):
        """Generate overall performance assessment"""
        print("\n=== PERFORMANCE ASSESSMENT REPORT ===")
        
        # Overall system status
        start_time = time.time()
        
        # Quick system health check
        def health_check():
            return self.supabase.table('florida_parcels')\
                .select("count", count="exact")\
                .limit(1).execute()
        
        health_result, health_time, health_success = self.time_query("System health check", health_check)
        
        print(f"\nSYSTEM PERFORMANCE SUMMARY:")
        print(f"  Database Connection: {'✓ HEALTHY' if health_success else '✗ ISSUES'}")
        print(f"  Basic Query Performance: {'✓ GOOD' if health_time < 1.0 else '⚠ SLOW' if health_time < 3.0 else '✗ POOR'}")
        
        if health_time < 0.5:
            performance_rating = "EXCELLENT"
        elif health_time < 1.0:
            performance_rating = "GOOD"  
        elif health_time < 2.0:
            performance_rating = "ACCEPTABLE"
        else:
            performance_rating = "NEEDS OPTIMIZATION"
        
        print(f"  Overall Performance Rating: {performance_rating}")
        
        print(f"\nRECOMMENDATIONS:")
        if health_time > 1.0:
            print("  - Consider running the performance indexes SQL script")
            print("  - Monitor concurrent query load")
        
        print("  - Create indexes using: create_performance_indexes.sql")
        print("  - Enable query optimization in Supabase dashboard")
        print("  - Consider connection pooling for high-traffic scenarios")

    def run_verification(self):
        """Execute complete verification process"""
        print("=== NAP IMPORT VERIFICATION STARTING ===")
        print(f"Target database: {self.url}")
        print(f"Verification time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all verification tests
        self.verify_data_volume()
        self.verify_data_quality()
        self.test_search_performance()
        self.test_aggregation_queries()
        self.generate_performance_report()
        
        print(f"\n=== VERIFICATION COMPLETED ===")
        print("NAP data import verification finished successfully.")

def main():
    verifier = NAPImportVerifier()
    verifier.run_verification()

if __name__ == "__main__":
    main()
