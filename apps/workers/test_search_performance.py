"""
Test Sunbiz Search Performance
Verifies that fuzzy search meets <100ms target
"""

import os
import sys
import io
import psycopg2
from urllib.parse import urlparse
import logging
import time
from statistics import mean, median

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_search_performance():
    """Test search performance with various queries"""
    
    # Database connection
    db_url = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    parsed = urlparse(db_url)
    conn_params = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
        'user': parsed.username,
        'password': parsed.password.replace('%40', '@') if parsed.password else None,
        'sslmode': 'require'
    }
    
    logger.info("=" * 60)
    logger.info("SUNBIZ SEARCH PERFORMANCE TEST")
    logger.info("=" * 60)
    
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Get current database stats
        cur.execute("SELECT COUNT(*) FROM sunbiz_corporate")
        total_records = cur.fetchone()[0]
        logger.info(f"Testing against {total_records:,} corporation records\n")
        
        # Test queries
        test_cases = [
            ("Simple word", "HOLDINGS", 10),
            ("Two words", "REAL ESTATE", 10),
            ("Company name", "CONCORD BROKER", 10),
            ("Common term", "LLC", 20),
            ("Partial match", "INVEST", 15),
            ("Exact company", "ABC CORPORATION", 5),
            ("Agent search", "SMITH", 10),
            ("City specific", "BOCA", 10)
        ]
        
        results = []
        
        logger.info("PERFORMANCE TESTS")
        logger.info("-" * 60)
        
        for test_name, search_term, limit in test_cases:
            logger.info(f"\nTest: {test_name} - '{search_term}'")
            
            # Warm up query (first run often slower)
            cur.execute("""
                SELECT doc_number, entity_name, 
                       similarity(entity_name, %s) as score
                FROM sunbiz_corporate
                WHERE entity_name %% %s
                ORDER BY score DESC
                LIMIT %s
            """, (search_term, search_term, limit))
            
            # Measure multiple runs
            times = []
            for i in range(5):
                start = time.perf_counter()
                
                cur.execute("""
                    SELECT doc_number, entity_name, 
                           similarity(entity_name, %s) as score
                    FROM sunbiz_corporate
                    WHERE entity_name %% %s
                    ORDER BY score DESC
                    LIMIT %s
                """, (search_term, search_term, limit))
                
                results_found = cur.fetchall()
                
                elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
                times.append(elapsed)
            
            avg_time = mean(times)
            med_time = median(times)
            
            logger.info(f"  Results: {len(results_found)} matches found")
            logger.info(f"  Average: {avg_time:.2f}ms")
            logger.info(f"  Median: {med_time:.2f}ms")
            logger.info(f"  Min/Max: {min(times):.2f}ms / {max(times):.2f}ms")
            
            if avg_time < 100:
                logger.info(f"  ✅ PASS - Under 100ms target")
            else:
                logger.info(f"  ⚠️ SLOW - {avg_time:.2f}ms (target: < 100ms)")
            
            results.append({
                'test': test_name,
                'search': search_term,
                'avg_ms': avg_time,
                'median_ms': med_time,
                'matches': len(results_found)
            })
            
            # Show sample results
            if results_found:
                logger.info("  Top matches:")
                for doc, name, score in results_found[:3]:
                    logger.info(f"    - {name[:50]} (score: {score:.3f})")
        
        # Test function performance
        logger.info("\n" + "=" * 60)
        logger.info("FUNCTION PERFORMANCE TEST")
        logger.info("-" * 60)
        
        # Test search function
        start = time.perf_counter()
        cur.execute("SELECT * FROM search_sunbiz_entities('INVESTMENT GROUP', 20)")
        func_results = cur.fetchall()
        func_time = (time.perf_counter() - start) * 1000
        
        logger.info(f"\nsearch_sunbiz_entities('INVESTMENT GROUP'):")
        logger.info(f"  Results: {len(func_results)} matches")
        logger.info(f"  Time: {func_time:.2f}ms")
        
        if func_time < 100:
            logger.info(f"  ✅ PASS - Function meets performance target")
        
        # Test property matching function
        start = time.perf_counter()
        cur.execute("SELECT * FROM match_property_owner('SUNSHINE PROPERTIES LLC')")
        prop_results = cur.fetchall()
        prop_time = (time.perf_counter() - start) * 1000
        
        logger.info(f"\nmatch_property_owner('SUNSHINE PROPERTIES LLC'):")
        logger.info(f"  Results: {len(prop_results)} matches")
        logger.info(f"  Time: {prop_time:.2f}ms")
        
        if prop_time < 200:
            logger.info(f"  ✅ PASS - Property matching is fast")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("=" * 60)
        
        all_times = [r['avg_ms'] for r in results]
        overall_avg = mean(all_times)
        
        logger.info(f"Total tests: {len(results)}")
        logger.info(f"Overall average: {overall_avg:.2f}ms")
        logger.info(f"Fastest query: {min(all_times):.2f}ms")
        logger.info(f"Slowest query: {max(all_times):.2f}ms")
        
        passed = sum(1 for t in all_times if t < 100)
        logger.info(f"\nTests under 100ms: {passed}/{len(results)}")
        
        if overall_avg < 100:
            logger.info("\n🎉 SUCCESS: Search performance meets <100ms target!")
        else:
            logger.info(f"\n⚠️ Performance needs optimization: {overall_avg:.2f}ms average")
        
        conn.close()
        
        return overall_avg < 100
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return False

if __name__ == "__main__":
    test_search_performance()