"""
Optimized Data Loader for 1.2M+ Florida Property Records
Handles large-scale data import with performance optimizations
"""

import asyncio
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch, execute_values
from contextlib import contextmanager
import os
from dotenv import load_dotenv
import hashlib
import json

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedPropertyLoader:
    """High-performance loader for Florida property data"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')
        self.batch_size = 10000  # Optimal batch size for Supabase
        self.chunk_size = 50000  # Reading chunks from CSV
        self.max_connections = 5
        
    @contextmanager
    def get_db_connection(self):
        """Get database connection with optimal settings"""
        conn = psycopg2.connect(self.db_url)
        try:
            # Optimize for bulk inserts
            with conn.cursor() as cur:
                cur.execute("SET synchronous_commit = OFF")
                cur.execute("SET maintenance_work_mem = '256MB'")
                cur.execute("SET work_mem = '256MB'")
            yield conn
        finally:
            conn.close()
    
    def create_optimized_schema(self):
        """Create optimized schema with proper indexing and partitioning"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                # Drop existing indexes temporarily for faster loading
                cur.execute("""
                    -- Create main table with partitioning by county
                    CREATE TABLE IF NOT EXISTS florida_parcels_optimized (
                        id BIGSERIAL,
                        parcel_id VARCHAR(50) NOT NULL,
                        county VARCHAR(50) NOT NULL,
                        
                        -- Core fields for search
                        phy_addr1 VARCHAR(255),
                        phy_city VARCHAR(100),
                        phy_zipcd VARCHAR(10),
                        owner_name VARCHAR(255),
                        
                        -- Denormalized frequently accessed fields
                        taxable_value FLOAT,
                        year_built INTEGER,
                        total_living_area FLOAT,
                        sale_date DATE,
                        sale_price FLOAT,
                        
                        -- JSONB for flexible additional data
                        property_data JSONB,
                        
                        -- Optimized for updates
                        data_hash VARCHAR(64),
                        import_date TIMESTAMP DEFAULT NOW(),
                        
                        PRIMARY KEY (parcel_id, county)
                    ) PARTITION BY LIST (county);
                """)
                
                # Create partitions for major counties
                counties = ['BROWARD', 'MIAMI-DADE', 'PALM BEACH', 'ORANGE', 'HILLSBOROUGH']
                for county in counties:
                    partition_name = f"florida_parcels_{county.lower().replace(' ', '_').replace('-', '_')}"
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS {partition_name} 
                        PARTITION OF florida_parcels_optimized 
                        FOR VALUES IN ('{county}');
                    """)
                
                # Create default partition for other counties
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS florida_parcels_other 
                    PARTITION OF florida_parcels_optimized DEFAULT;
                """)
                
                conn.commit()
                logger.info("Optimized schema created with partitioning")
    
    def create_indexes(self):
        """Create optimized indexes after data load"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                indexes = [
                    # Primary search indexes
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_search_text ON florida_parcels_optimized USING GIN(to_tsvector('english', coalesce(phy_addr1,'') || ' ' || coalesce(phy_city,'') || ' ' || coalesce(owner_name,'')))",
                    
                    # Covering index for common queries
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_covering ON florida_parcels_optimized(phy_city, taxable_value) INCLUDE (parcel_id, phy_addr1, owner_name, year_built, total_living_area)",
                    
                    # BRIN indexes for range queries (very efficient for large tables)
                    "CREATE INDEX IF NOT EXISTS idx_parcels_value_brin ON florida_parcels_optimized USING BRIN(taxable_value)",
                    "CREATE INDEX IF NOT EXISTS idx_parcels_date_brin ON florida_parcels_optimized USING BRIN(sale_date)",
                    "CREATE INDEX IF NOT EXISTS idx_parcels_year_brin ON florida_parcels_optimized USING BRIN(year_built)",
                    
                    # Hash indexes for exact matches (faster than btree for equality)
                    "CREATE INDEX IF NOT EXISTS idx_parcels_parcel_hash ON florida_parcels_optimized USING HASH(parcel_id)",
                    "CREATE INDEX IF NOT EXISTS idx_parcels_city_hash ON florida_parcels_optimized USING HASH(phy_city)",
                    
                    # JSONB index for property_data
                    "CREATE INDEX IF NOT EXISTS idx_parcels_data_gin ON florida_parcels_optimized USING GIN(property_data)",
                ]
                
                for index_sql in indexes:
                    logger.info(f"Creating index: {index_sql[:50]}...")
                    cur.execute(index_sql)
                    conn.commit()
                
                # Update table statistics for query planner
                cur.execute("ANALYZE florida_parcels_optimized;")
                conn.commit()
                
                logger.info("All indexes created successfully")
    
    def load_data_batch(self, df_chunk: pd.DataFrame, conn):
        """Load a batch of data efficiently"""
        with conn.cursor() as cur:
            # Prepare data for insertion
            records = []
            for _, row in df_chunk.iterrows():
                # Create hash for change detection
                row_data = row.to_dict()
                data_hash = hashlib.md5(json.dumps(row_data, default=str).encode()).hexdigest()
                
                # Extract core fields for indexing
                core_fields = {
                    'parcel_id': row.get('parcel_id', ''),
                    'county': row.get('county', 'BROWARD'),
                    'phy_addr1': row.get('phy_addr1', ''),
                    'phy_city': row.get('phy_city', ''),
                    'phy_zipcd': row.get('phy_zipcd', ''),
                    'owner_name': row.get('owner_name', ''),
                    'taxable_value': row.get('taxable_value', 0),
                    'year_built': row.get('year_built'),
                    'total_living_area': row.get('total_living_area'),
                    'sale_date': row.get('sale_date'),
                    'sale_price': row.get('sale_price'),
                }
                
                # Store remaining fields in JSONB
                jsonb_fields = {k: v for k, v in row_data.items() 
                              if k not in core_fields and pd.notna(v)}
                
                records.append((
                    core_fields['parcel_id'],
                    core_fields['county'],
                    core_fields['phy_addr1'],
                    core_fields['phy_city'],
                    core_fields['phy_zipcd'],
                    core_fields['owner_name'],
                    core_fields['taxable_value'],
                    core_fields['year_built'],
                    core_fields['total_living_area'],
                    core_fields['sale_date'],
                    core_fields['sale_price'],
                    json.dumps(jsonb_fields),
                    data_hash
                ))
            
            # Use COPY for maximum performance
            execute_values(
                cur,
                """
                INSERT INTO florida_parcels_optimized 
                (parcel_id, county, phy_addr1, phy_city, phy_zipcd, owner_name,
                 taxable_value, year_built, total_living_area, sale_date, sale_price,
                 property_data, data_hash)
                VALUES %s
                ON CONFLICT (parcel_id, county) 
                DO UPDATE SET
                    phy_addr1 = EXCLUDED.phy_addr1,
                    phy_city = EXCLUDED.phy_city,
                    phy_zipcd = EXCLUDED.phy_zipcd,
                    owner_name = EXCLUDED.owner_name,
                    taxable_value = EXCLUDED.taxable_value,
                    year_built = EXCLUDED.year_built,
                    total_living_area = EXCLUDED.total_living_area,
                    sale_date = EXCLUDED.sale_date,
                    sale_price = EXCLUDED.sale_price,
                    property_data = EXCLUDED.property_data,
                    data_hash = EXCLUDED.data_hash,
                    import_date = NOW()
                WHERE florida_parcels_optimized.data_hash != EXCLUDED.data_hash
                """,
                records,
                template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)",
                page_size=1000
            )
            conn.commit()
    
    async def load_file_async(self, file_path: str):
        """Load file asynchronously with progress tracking"""
        total_rows = sum(1 for _ in open(file_path)) - 1  # Count rows
        logger.info(f"Loading {total_rows:,} rows from {file_path}")
        
        rows_loaded = 0
        start_time = datetime.now()
        
        # Process in chunks
        for chunk_num, df_chunk in enumerate(pd.read_csv(file_path, chunksize=self.chunk_size)):
            with self.get_db_connection() as conn:
                # Process chunk in smaller batches
                for i in range(0, len(df_chunk), self.batch_size):
                    batch = df_chunk.iloc[i:i+self.batch_size]
                    self.load_data_batch(batch, conn)
                    rows_loaded += len(batch)
                    
                    # Progress reporting
                    if rows_loaded % 100000 == 0:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        rate = rows_loaded / elapsed
                        eta = (total_rows - rows_loaded) / rate
                        logger.info(f"Progress: {rows_loaded:,}/{total_rows:,} rows "
                                  f"({rows_loaded/total_rows*100:.1f}%) "
                                  f"Rate: {rate:.0f} rows/sec "
                                  f"ETA: {eta/60:.1f} minutes")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Completed loading {rows_loaded:,} rows in {elapsed/60:.1f} minutes "
                   f"({rows_loaded/elapsed:.0f} rows/sec)")
    
    def create_materialized_views(self):
        """Create materialized views for common queries"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                views = [
                    # City summary view
                    """
                    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_city_summary AS
                    SELECT 
                        phy_city,
                        COUNT(*) as property_count,
                        AVG(taxable_value) as avg_value,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY taxable_value) as median_value,
                        SUM(taxable_value) as total_value,
                        AVG(year_built) as avg_year_built
                    FROM florida_parcels_optimized
                    WHERE taxable_value > 0
                    GROUP BY phy_city
                    WITH DATA;
                    """,
                    
                    # Recent sales view
                    """
                    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_recent_sales AS
                    SELECT *
                    FROM florida_parcels_optimized
                    WHERE sale_date >= CURRENT_DATE - INTERVAL '180 days'
                        AND sale_price > 0
                    ORDER BY sale_date DESC
                    WITH DATA;
                    """,
                    
                    # High value properties
                    """
                    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_high_value_properties AS
                    SELECT *
                    FROM florida_parcels_optimized
                    WHERE taxable_value > 1000000
                    ORDER BY taxable_value DESC
                    WITH DATA;
                    """
                ]
                
                for view_sql in views:
                    logger.info(f"Creating materialized view...")
                    cur.execute(view_sql)
                
                # Create indexes on materialized views
                cur.execute("CREATE INDEX ON mv_city_summary(phy_city);")
                cur.execute("CREATE INDEX ON mv_recent_sales(sale_date);")
                cur.execute("CREATE INDEX ON mv_high_value_properties(taxable_value);")
                
                conn.commit()
                logger.info("Materialized views created")
    
    def setup_automatic_refresh(self):
        """Setup automatic refresh for materialized views"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create refresh function
                cur.execute("""
                    CREATE OR REPLACE FUNCTION refresh_materialized_views()
                    RETURNS void AS $$
                    BEGIN
                        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_city_summary;
                        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_recent_sales;
                        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_high_value_properties;
                    END;
                    $$ LANGUAGE plpgsql;
                """)
                
                conn.commit()
                logger.info("Automatic refresh setup completed")

async def main():
    """Main execution function"""
    loader = OptimizedPropertyLoader()
    
    # Step 1: Create optimized schema
    logger.info("Step 1: Creating optimized schema...")
    loader.create_optimized_schema()
    
    # Step 2: Load data (indexes will be created after)
    logger.info("Step 2: Loading data...")
    data_files = [
        "data/NAL16P202501.csv",  # Name/Address/Legal data
        "data/broward_nav_2025.csv",  # Value assessment data
    ]
    
    for file_path in data_files:
        if Path(file_path).exists():
            await loader.load_file_async(file_path)
    
    # Step 3: Create indexes after data load
    logger.info("Step 3: Creating indexes...")
    loader.create_indexes()
    
    # Step 4: Create materialized views
    logger.info("Step 4: Creating materialized views...")
    loader.create_materialized_views()
    
    # Step 5: Setup automatic refresh
    logger.info("Step 5: Setting up automatic refresh...")
    loader.setup_automatic_refresh()
    
    logger.info("Data loading completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())