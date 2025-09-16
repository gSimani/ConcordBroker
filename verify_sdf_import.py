#!/usr/bin/env python3
"""
Verification script for SDF Sales Data Import
Tests common query patterns and performance
"""

import os
import psycopg2
import time
from pathlib import Path

def load_environment():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def test_queries():
    """Test common query patterns on the imported data"""
    load_environment()
    
    # Connect to database
    database_url = os.getenv('POSTGRES_URL_NON_POOLING')
    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()
    
    try:
        print("=== SDF Sales Data Verification ===\n")
        
        # Test queries
        queries = [
            # Basic statistics
            ("Total sales records", "SELECT COUNT(*) FROM property_sales_history"),
            ("Unique properties with sales", "SELECT COUNT(DISTINCT parcel_id) FROM property_sales_history"),
            ("Date range", "SELECT MIN(sale_date), MAX(sale_date) FROM property_sales_history WHERE sale_date IS NOT NULL"),
            ("Price range", "SELECT MIN(sale_price), MAX(sale_price) FROM property_sales_history WHERE sale_price > 0"),
            
            # Sample parcel search (performance test)
            ("Sample parcel sales", """
                SELECT parcel_id, sale_date, sale_price, quality_code 
                FROM property_sales_history 
                WHERE parcel_id = '474119030010' 
                ORDER BY sale_date DESC
                LIMIT 5
            """),
            
            # Date range query (performance test)
            ("Recent sales (2024-2025)", """
                SELECT COUNT(*), AVG(sale_price), MAX(sale_price)
                FROM property_sales_history 
                WHERE sale_year >= 2024 AND sale_price > 0
            """),
            
            # Price range query
            ("High-value sales (>$1M)", """
                SELECT parcel_id, sale_price, sale_date
                FROM property_sales_history 
                WHERE sale_price > 100000000
                ORDER BY sale_price DESC
                LIMIT 5
            """),
            
            # Quality code distribution
            ("Sales by quality code", """
                SELECT quality_code, COUNT(*) as count,
                       ROUND(AVG(sale_price)/100.0, 2) as avg_price
                FROM property_sales_history 
                WHERE sale_price > 0 AND quality_code IS NOT NULL
                GROUP BY quality_code 
                ORDER BY count DESC 
                LIMIT 10
            """),
            
            # Monthly sales trend
            ("Sales by month (2024)", """
                SELECT sale_month, COUNT(*) as sales_count,
                       ROUND(AVG(sale_price)/100.0, 2) as avg_price
                FROM property_sales_history 
                WHERE sale_year = 2024 AND sale_price > 0
                GROUP BY sale_month 
                ORDER BY sale_month
            """)
        ]
        
        for description, query in queries:
            print(f"Testing: {description}")
            start_time = time.time()
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            elapsed = time.time() - start_time
            print(f"  Query time: {elapsed:.3f} seconds")
            
            if len(results) > 5:
                print(f"  Results: {len(results)} rows (showing first 5)")
                for row in results[:5]:
                    print(f"      {row}")
            else:
                print(f"  Results:")
                for row in results:
                    print(f"      {row}")
            print()
        
        # Test joining with florida_parcels (if exists)
        print("Testing join with florida_parcels table...")
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM property_sales_history s
                INNER JOIN florida_parcels p ON s.parcel_id = p.parcel_id
                LIMIT 1
            """)
            join_count = cursor.fetchone()[0]
            print(f"  Join successful: {join_count:,} matched records")
        except Exception as e:
            print(f"  Join test failed (table may not exist): {e}")
        
        print("\n=== Index Performance Test ===")
        
        # Test index performance
        performance_queries = [
            ("Parcel ID lookup", "SELECT COUNT(*) FROM property_sales_history WHERE parcel_id = '474119030010'"),
            ("Date range", "SELECT COUNT(*) FROM property_sales_history WHERE sale_date >= '2024-01-01'"),
            ("Price range", "SELECT COUNT(*) FROM property_sales_history WHERE sale_price > 50000000"),
            ("Quality filter", "SELECT COUNT(*) FROM property_sales_history WHERE quality_code = '01'"),
        ]
        
        for description, query in performance_queries:
            start_time = time.time()
            cursor.execute(query)
            result = cursor.fetchone()[0]
            elapsed = time.time() - start_time
            
            if elapsed < 0.1:
                status = "Excellent"
            elif elapsed < 0.5:
                status = "Good"
            elif elapsed < 1.0:
                status = "Acceptable"
            else:
                status = "Slow"
                
            print(f"  {description}: {result:,} results in {elapsed:.3f}s ({status})")
        
        print("\n=== Summary ===")
        cursor.execute("SELECT COUNT(*) FROM property_sales_history")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT parcel_id) FROM property_sales_history")
        unique_parcels = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(sale_price) FROM property_sales_history WHERE sale_price > 0")
        avg_price = cursor.fetchone()[0]
        
        print(f"Import verification completed successfully!")
        print(f"Total sales records: {total_records:,}")
        print(f"Unique properties: {unique_parcels:,}")
        print(f"Average sale price: ${avg_price/100:,.2f}")
        
    except Exception as e:
        print(f"Verification failed: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    test_queries()