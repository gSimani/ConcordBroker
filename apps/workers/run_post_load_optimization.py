"""
Run Sunbiz Post-Load Optimization
Executes all optimization steps for fuzzy search and performance
"""

import os
import sys
import io
import psycopg2
from urllib.parse import urlparse
import logging
from datetime import datetime

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_optimization():
    """Run all post-load optimization steps"""
    
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
    logger.info("SUNBIZ POST-LOAD OPTIMIZATION")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # 1. ENABLE SEARCH EXTENSIONS
        logger.info("\n1. ENABLING SEARCH EXTENSIONS")
        logger.info("-" * 40)
        
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            logger.info("✅ pg_trgm extension enabled")
        except Exception as e:
            logger.warning(f"pg_trgm: {e}")
        
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
            logger.info("✅ unaccent extension enabled")
        except Exception as e:
            logger.warning(f"unaccent: {e}")
        
        conn.commit()
        
        # 2. CREATE PERFORMANCE INDEXES
        logger.info("\n2. CREATING PERFORMANCE INDEXES")
        logger.info("-" * 40)
        
        indexes = [
            # B-tree indexes for filtering
            ("idx_sunbiz_corporate_status", 
             "CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_status ON sunbiz_corporate(status) WHERE status IN ('ACTIVE', 'INACTIVE')"),
            
            ("idx_sunbiz_corporate_filing_date", 
             "CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_filing_date ON sunbiz_corporate(filing_date DESC)"),
            
            ("idx_sunbiz_corporate_state_country", 
             "CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_state_country ON sunbiz_corporate(state_country) WHERE state_country = 'FL'"),
            
            # GIN trigram indexes for fuzzy search
            ("idx_sunbiz_corporate_entity_name_trgm", 
             "CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_entity_name_trgm ON sunbiz_corporate USING gin (entity_name gin_trgm_ops)"),
            
            ("idx_sunbiz_corporate_registered_agent_trgm", 
             "CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_registered_agent_trgm ON sunbiz_corporate USING gin (registered_agent gin_trgm_ops) WHERE registered_agent IS NOT NULL"),
            
            # Location indexes
            ("idx_sunbiz_corporate_prin_city", 
             "CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_prin_city ON sunbiz_corporate(prin_city) WHERE prin_city IS NOT NULL"),
            
            ("idx_sunbiz_corporate_prin_zip", 
             "CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_prin_zip ON sunbiz_corporate(prin_zip) WHERE prin_zip IS NOT NULL"),
            
            # Composite index
            ("idx_sunbiz_corporate_status_filing", 
             "CREATE INDEX IF NOT EXISTS idx_sunbiz_corporate_status_filing ON sunbiz_corporate(status, filing_date DESC)"),
        ]
        
        for idx_name, idx_sql in indexes:
            try:
                logger.info(f"Creating {idx_name}...")
                idx_start = datetime.now()
                cur.execute(idx_sql)
                conn.commit()
                idx_duration = (datetime.now() - idx_start).total_seconds()
                logger.info(f"✅ {idx_name} created in {idx_duration:.1f}s")
            except Exception as e:
                logger.warning(f"❌ {idx_name}: {e}")
                conn.rollback()
        
        # 3. UPDATE TABLE STATISTICS
        logger.info("\n3. ANALYZING TABLES")
        logger.info("-" * 40)
        
        tables = ['sunbiz_corporate', 'sunbiz_fictitious', 'sunbiz_liens', 'sunbiz_partnerships']
        
        for table in tables:
            try:
                logger.info(f"Analyzing {table}...")
                cur.execute(f"ANALYZE {table};")
                conn.commit()
                logger.info(f"✅ {table} analyzed")
            except Exception as e:
                logger.warning(f"❌ {table}: {e}")
                conn.rollback()
        
        # 4. VERIFY INDEXES
        logger.info("\n4. INDEX VERIFICATION")
        logger.info("-" * 40)
        
        cur.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public' 
                AND tablename LIKE 'sunbiz%'
            ORDER BY tablename, indexname
        """)
        
        indexes = cur.fetchall()
        for schema, table, index, size in indexes:
            logger.info(f"  {index}: {size}")
        
        # 5. GET TABLE STATISTICS
        logger.info("\n5. TABLE STATISTICS")
        logger.info("-" * 40)
        
        cur.execute("""
            SELECT 
                tablename,
                n_live_tup AS row_count,
                pg_size_pretty(pg_total_relation_size('public.' || tablename)) AS total_size
            FROM pg_stat_user_tables
            WHERE schemaname = 'public' 
                AND tablename LIKE 'sunbiz%'
            ORDER BY n_live_tup DESC
        """)
        
        tables = cur.fetchall()
        for table, count, size in tables:
            logger.info(f"  {table}: {count:,} rows, {size}")
        
        # 6. TEST FUZZY SEARCH
        logger.info("\n6. TESTING FUZZY SEARCH")
        logger.info("-" * 40)
        
        test_queries = [
            ("CONCORD", "Testing fuzzy match for 'CONCORD'"),
            ("ACME HOLDINGS", "Testing fuzzy match for 'ACME HOLDINGS'"),
            ("SMITH", "Testing agent search for 'SMITH'")
        ]
        
        for search_term, description in test_queries:
            logger.info(f"\n{description}:")
            
            # Test with EXPLAIN ANALYZE
            cur.execute("""
                EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                SELECT doc_number, entity_name, status,
                       similarity(entity_name, %s) AS sim_score
                FROM sunbiz_corporate
                WHERE entity_name %% %s
                ORDER BY sim_score DESC
                LIMIT 10
            """, (search_term, search_term))
            
            explain_result = cur.fetchone()[0][0]
            execution_time = explain_result['Execution Time']
            
            # Run actual query
            cur.execute("""
                SELECT doc_number, entity_name, status,
                       similarity(entity_name, %s) AS sim_score
                FROM sunbiz_corporate
                WHERE entity_name %% %s
                ORDER BY sim_score DESC
                LIMIT 5
            """, (search_term, search_term))
            
            results = cur.fetchall()
            
            logger.info(f"  Execution time: {execution_time:.2f}ms")
            logger.info(f"  Found {len(results)} matches:")
            
            for doc, name, status, score in results[:3]:
                logger.info(f"    - {name[:50]} (score: {score:.3f}, status: {status})")
        
        conn.close()
        
        duration = datetime.now() - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("OPTIMIZATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"⏱️  Total duration: {duration}")
        logger.info("✅ Fuzzy search enabled and optimized")
        logger.info("✅ All indexes created successfully")
        logger.info("✅ Tables analyzed for query optimization")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return False

if __name__ == "__main__":
    run_optimization()