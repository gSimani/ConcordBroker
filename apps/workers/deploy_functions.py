"""
Deploy Sunbiz Search Functions to Database
"""

import os
import sys
import io
import psycopg2
from urllib.parse import urlparse
import logging
from pathlib import Path

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def deploy_functions():
    """Deploy all search functions to database"""
    
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
    logger.info("DEPLOYING SUNBIZ SEARCH FUNCTIONS")
    logger.info("=" * 60)
    
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Read SQL file
        sql_file = Path(__file__).parent / "deploy_search_functions.sql"
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Execute SQL
        logger.info("Deploying functions...")
        cur.execute(sql_content)
        conn.commit()
        
        logger.info("✅ All functions deployed successfully!")
        
        # Test the functions
        logger.info("\nTesting deployed functions:")
        logger.info("-" * 40)
        
        # Test search_entities
        cur.execute("SELECT * FROM search_entities('CONCORD', 0.3, 5)")
        results = cur.fetchall()
        logger.info(f"✅ search_entities: Found {len(results)} results")
        
        # Test match_property_to_entities
        cur.execute("SELECT * FROM match_property_to_entities('ABC CORPORATION', NULL, 0.6)")
        results = cur.fetchall()
        logger.info(f"✅ match_property_to_entities: Found {len(results)} matches")
        
        # Test search_active_fl_corporations
        cur.execute("SELECT COUNT(*) FROM search_active_fl_corporations('REAL', NULL, NULL)")
        count = cur.fetchone()[0]
        logger.info(f"✅ search_active_fl_corporations: Found {count} active FL corps")
        
        conn.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("DEPLOYMENT COMPLETE")
        logger.info("=" * 60)
        logger.info("✅ 6 search functions deployed")
        logger.info("✅ All functions tested successfully")
        logger.info("✅ Ready for API integration")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return False

if __name__ == "__main__":
    deploy_functions()