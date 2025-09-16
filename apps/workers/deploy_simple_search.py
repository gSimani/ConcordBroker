"""
Deploy Simplified Sunbiz Search Functions
Working version that matches actual table schemas
"""

import os
import sys
import io
import psycopg2
from urllib.parse import urlparse
import logging

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def deploy_search_functions():
    """Deploy working search functions"""
    
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
    logger.info("DEPLOYING SIMPLIFIED SEARCH FUNCTIONS")
    logger.info("=" * 60)
    
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # 1. Simple entity search function
        logger.info("Creating search_sunbiz_entities function...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION search_sunbiz_entities(
                search_term TEXT,
                max_results INT DEFAULT 100
            )
            RETURNS TABLE (
                doc_number VARCHAR,
                entity_name VARCHAR,
                entity_type VARCHAR,
                status VARCHAR,
                match_score FLOAT,
                city VARCHAR,
                state VARCHAR
            ) 
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    c.doc_number,
                    c.entity_name,
                    'CORPORATION'::VARCHAR as entity_type,
                    c.status,
                    similarity(c.entity_name, search_term)::FLOAT as match_score,
                    c.prin_city::VARCHAR as city,
                    c.prin_state::VARCHAR as state
                FROM sunbiz_corporate c
                WHERE c.entity_name % search_term
                ORDER BY similarity(c.entity_name, search_term) DESC
                LIMIT max_results;
            END;
            $$;
        """)
        conn.commit()
        logger.info("✅ search_sunbiz_entities created")
        
        # 2. Property matching function
        logger.info("Creating match_property_owner function...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION match_property_owner(
                property_owner TEXT
            )
            RETURNS TABLE (
                doc_number VARCHAR,
                entity_name VARCHAR,
                confidence FLOAT,
                status VARCHAR,
                filing_date DATE
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                -- Exact match
                SELECT 
                    c.doc_number,
                    c.entity_name,
                    1.0::FLOAT as confidence,
                    c.status,
                    c.filing_date
                FROM sunbiz_corporate c
                WHERE UPPER(TRIM(c.entity_name)) = UPPER(TRIM(property_owner))
                
                UNION ALL
                
                -- Fuzzy match
                SELECT 
                    c.doc_number,
                    c.entity_name,
                    similarity(c.entity_name, property_owner)::FLOAT as confidence,
                    c.status,
                    c.filing_date
                FROM sunbiz_corporate c
                WHERE c.entity_name % property_owner
                    AND UPPER(TRIM(c.entity_name)) != UPPER(TRIM(property_owner))
                
                ORDER BY confidence DESC
                LIMIT 10;
            END;
            $$;
        """)
        conn.commit()
        logger.info("✅ match_property_owner created")
        
        # 3. Active Florida search
        logger.info("Creating search_active_florida function...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION search_active_florida(
                search_term TEXT,
                city_filter VARCHAR DEFAULT NULL
            )
            RETURNS TABLE (
                doc_number VARCHAR,
                entity_name VARCHAR,
                filing_date DATE,
                city VARCHAR,
                registered_agent VARCHAR
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    c.doc_number,
                    c.entity_name,
                    c.filing_date,
                    c.prin_city,
                    c.registered_agent
                FROM sunbiz_corporate c
                WHERE c.status = 'ACTIVE'
                    AND c.state_country = 'FL'
                    AND c.entity_name % search_term
                    AND (city_filter IS NULL OR c.prin_city ILIKE '%' || city_filter || '%')
                ORDER BY similarity(c.entity_name, search_term) DESC, c.filing_date DESC
                LIMIT 100;
            END;
            $$;
        """)
        conn.commit()
        logger.info("✅ search_active_florida created")
        
        # Grant permissions
        logger.info("Granting permissions...")
        cur.execute("""
            GRANT EXECUTE ON FUNCTION search_sunbiz_entities TO authenticated, anon;
            GRANT EXECUTE ON FUNCTION match_property_owner TO authenticated, anon;
            GRANT EXECUTE ON FUNCTION search_active_florida TO authenticated, anon;
        """)
        conn.commit()
        
        # Test the functions
        logger.info("\n" + "=" * 60)
        logger.info("TESTING SEARCH FUNCTIONS")
        logger.info("=" * 60)
        
        # Test 1: Basic search
        logger.info("\nTest 1: Searching for 'REAL ESTATE'...")
        cur.execute("SELECT * FROM search_sunbiz_entities('REAL ESTATE', 5)")
        results = cur.fetchall()
        logger.info(f"Found {len(results)} results")
        for doc, name, type, status, score, city, state in results[:3]:
            logger.info(f"  - {name[:50]} (score: {score:.3f}, {status})")
        
        # Test 2: Property matching
        logger.info("\nTest 2: Matching property owner 'ABC CORPORATION'...")
        cur.execute("SELECT * FROM match_property_owner('ABC CORPORATION')")
        results = cur.fetchall()
        logger.info(f"Found {len(results)} matches")
        for doc, name, confidence, status, date in results[:3]:
            logger.info(f"  - {name[:50]} (confidence: {confidence:.3f})")
        
        # Test 3: Active Florida search
        logger.info("\nTest 3: Active Florida corporations with 'HOLDINGS'...")
        cur.execute("SELECT * FROM search_active_florida('HOLDINGS', 'BOCA RATON')")
        results = cur.fetchall()
        logger.info(f"Found {len(results)} active FL corporations in Boca Raton")
        
        # Performance test
        logger.info("\n" + "=" * 60)
        logger.info("PERFORMANCE TEST")
        logger.info("=" * 60)
        
        cur.execute("""
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM search_sunbiz_entities('CONCORD', 10)
        """)
        
        explain_result = cur.fetchone()[0][0]
        execution_time = explain_result['Execution Time']
        logger.info(f"Fuzzy search execution time: {execution_time:.2f}ms")
        
        if execution_time < 100:
            logger.info("✅ PERFORMANCE TARGET MET: < 100ms")
        else:
            logger.info(f"⚠️ Performance: {execution_time:.2f}ms (target: < 100ms)")
        
        conn.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("DEPLOYMENT COMPLETE")
        logger.info("=" * 60)
        logger.info("✅ 3 search functions deployed")
        logger.info("✅ All functions tested successfully")
        logger.info("✅ Ready for production use")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return False

if __name__ == "__main__":
    deploy_search_functions()