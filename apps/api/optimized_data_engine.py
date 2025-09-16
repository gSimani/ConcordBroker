"""
Optimized Data Engine for ConcordBroker
Uses PySpark, Pandas, NumPy, SQLAlchemy for high-performance data processing
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np
import redis
import pickle
import hashlib
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedDataEngine:
    """
    High-performance data engine using:
    - PySpark for big data processing
    - Pandas/NumPy for in-memory operations
    - SQLAlchemy with connection pooling
    - Redis for distributed caching
    - Multi-processing for parallel operations
    """

    def __init__(self):
        # Initialize Spark Session for big data processing
        self.spark = SparkSession.builder \
            .appName("ConcordBrokerOptimized") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.adaptive.skewJoin.enabled", "true") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g") \
            .config("spark.sql.shuffle.partitions", "200") \
            .getOrCreate()

        # Initialize SQLAlchemy with connection pooling
        self.db_url = self._get_database_url()
        self.engine = create_engine(
            self.db_url,
            poolclass=pool.QueuePool,
            pool_size=20,  # Increased pool size
            max_overflow=40,  # Allow more overflow connections
            pool_pre_ping=True,  # Test connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False
        )
        self.Session = sessionmaker(bind=self.engine)

        # Initialize Redis for caching
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=False,  # Use binary for pickle
            socket_connect_timeout=5,
            socket_timeout=5,
            connection_pool=redis.ConnectionPool(max_connections=100)
        )

        # Thread pool for parallel I/O operations
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

        # Process pool for CPU-intensive operations
        self.process_pool = ProcessPoolExecutor(max_workers=4)

        # Cache configuration
        self.cache_ttl = 3600  # 1 hour default
        self.batch_size = 5000  # Optimal batch size for operations

        # Pre-load frequently accessed data into memory
        self.preloaded_data = {}
        self._preload_critical_data()

    def _get_database_url(self) -> str:
        """Construct PostgreSQL connection URL for Supabase"""
        import os
        from dotenv import load_dotenv
        load_dotenv()

        # Use direct PostgreSQL connection for better performance
        return (
            f"postgresql://postgres.pmispwtdngkcmsrsjwbp:"
            f"{os.getenv('SUPABASE_DB_PASSWORD', 'vM4g2024$$Florida1')}@"
            f"aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        )

    def _preload_critical_data(self):
        """Preload frequently accessed data into memory"""
        try:
            # Load property type mappings
            self.preloaded_data['property_types'] = {
                '0100': 'Single Family',
                '0101': 'Single Family - Detached',
                '0102': 'Single Family - Attached',
                '0200': 'Multi Family',
                '1000': 'Commercial',
                '4000': 'Industrial',
                '5000': 'Agricultural',
                '0000': 'Vacant Land'
            }

            # Load county data
            with self.Session() as session:
                county_query = """
                    SELECT DISTINCT county, COUNT(*) as count
                    FROM florida_parcels
                    GROUP BY county
                """
                counties_df = pd.read_sql(county_query, self.engine)
                self.preloaded_data['counties'] = counties_df.to_dict('records')

            logger.info("Critical data preloaded successfully")

        except Exception as e:
            logger.error(f"Error preloading data: {e}")

    def get_cache_key(self, query_params: Dict) -> str:
        """Generate cache key from query parameters"""
        # Create a deterministic string from params
        param_str = json.dumps(query_params, sort_keys=True)
        return f"query:{hashlib.md5(param_str.encode()).hexdigest()}"

    async def search_properties_optimized(self,
                                         filters: Dict,
                                         page: int = 1,
                                         limit: int = 500) -> Dict[str, Any]:
        """
        Optimized property search using multiple strategies:
        1. Check Redis cache first
        2. Use PySpark for large dataset filtering
        3. Apply Pandas for in-memory operations
        4. Utilize parallel processing for data enrichment
        """

        # Generate cache key
        cache_key = self.get_cache_key({**filters, 'page': page, 'limit': limit})

        # Check cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for query: {cache_key}")
            return cached_result

        # Use PySpark for large-scale filtering
        df_spark = self._load_data_spark(filters)

        # Convert to Pandas for detailed operations
        df_pandas = df_spark.toPandas()

        # Apply NumPy for numerical calculations
        df_enhanced = self._enhance_with_numpy(df_pandas)

        # Paginate results
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        df_page = df_enhanced.iloc[start_idx:end_idx]

        # Format results
        properties = df_page.to_dict('records')

        # Enrich properties in parallel
        enriched_properties = await self._enrich_properties_parallel(properties)

        result = {
            'success': True,
            'data': enriched_properties,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': len(df_enhanced),
                'pages': (len(df_enhanced) + limit - 1) // limit
            },
            'cached': False,
            'query_time_ms': 0  # Will be calculated
        }

        # Cache the result
        self._set_cache(cache_key, result, ttl=self.cache_ttl)

        return result

    def _load_data_spark(self, filters: Dict):
        """Load and filter data using PySpark"""

        # Read from database using Spark JDBC
        df = self.spark.read \
            .format("jdbc") \
            .option("url", self.db_url.replace('postgresql://', 'jdbc:postgresql://')) \
            .option("dbtable", "florida_parcels") \
            .option("user", "postgres.pmispwtdngkcmsrsjwbp") \
            .option("password", "vM4g2024$$Florida1") \
            .option("driver", "org.postgresql.Driver") \
            .option("fetchsize", "10000") \
            .option("partitionColumn", "parcel_id") \
            .option("numPartitions", "4") \
            .load()

        # Apply filters using Spark SQL
        if filters.get('q'):
            search_term = filters['q'].lower()
            df = df.filter(
                F.lower(F.col("phy_addr1")).contains(search_term) |
                F.lower(F.col("phy_city")).contains(search_term) |
                F.lower(F.col("owner_name")).contains(search_term)
            )

        if filters.get('city'):
            df = df.filter(F.lower(F.col("phy_city")) == filters['city'].lower())

        if filters.get('minValue'):
            df = df.filter(F.col("jv") >= filters['minValue'])

        if filters.get('maxValue'):
            df = df.filter(F.col("jv") <= filters['maxValue'])

        if filters.get('propertyType'):
            property_codes = self._get_property_codes(filters['propertyType'])
            df = df.filter(F.col("dor_uc").isin(property_codes))

        # Optimize with column pruning
        columns_needed = [
            'parcel_id', 'phy_addr1', 'phy_city', 'phy_zipcd',
            'owner_name', 'jv', 'av_sd', 'tv_sd', 'tot_lvg_area',
            'lnd_sqfoot', 'yr_blt', 'bedroom_cnt', 'bathroom_cnt',
            'dor_uc', 'sale_prc1', 'sale_yr1'
        ]

        df = df.select(*columns_needed)

        # Cache the DataFrame in Spark memory
        df.cache()

        return df

    def _enhance_with_numpy(self, df: pd.DataFrame) -> pd.DataFrame:
        """Use NumPy for efficient numerical calculations"""

        # Convert to NumPy arrays for faster computation
        jv = df['jv'].fillna(0).values
        av_sd = df['av_sd'].fillna(0).values
        tv_sd = df['tv_sd'].fillna(0).values
        tot_lvg_area = df['tot_lvg_area'].fillna(0).values
        lnd_sqfoot = df['lnd_sqfoot'].fillna(0).values

        # Calculate investment metrics using NumPy
        with np.errstate(divide='ignore', invalid='ignore'):
            # Price per square foot
            price_per_sqft = np.where(
                tot_lvg_area > 0,
                jv / tot_lvg_area,
                0
            )

            # Cap rate estimation (simplified)
            estimated_rent = jv * 0.01 * 12  # 1% rule
            net_income = estimated_rent * 0.7  # 30% expenses
            cap_rate = np.where(
                jv > 0,
                (net_income / jv) * 100,
                0
            )

            # Investment score
            base_score = np.full(len(df), 50.0)

            # Add points for undervalued properties
            undervalued = jv < av_sd
            base_score[undervalued] += 10

            # Add points for low entry
            low_entry = jv < 100000
            base_score[low_entry] += 5

            # Add points for good size
            good_size = tot_lvg_area > 1500
            base_score[good_size] += 5

            # Clip to 0-100 range
            investment_score = np.clip(base_score, 0, 100)

        # Add calculated columns back to DataFrame
        df['price_per_sqft'] = price_per_sqft
        df['cap_rate'] = cap_rate
        df['investment_score'] = investment_score

        # Sort by investment score for better results
        df = df.sort_values('investment_score', ascending=False)

        return df

    async def _enrich_properties_parallel(self, properties: List[Dict]) -> List[Dict]:
        """Enrich properties with additional data in parallel"""

        async def enrich_single(prop):
            # Add formatted fields
            prop['formatted_address'] = f"{prop.get('phy_addr1', '')}, {prop.get('phy_city', '')}, FL {prop.get('phy_zipcd', '')}"

            # Add property type name
            prop['property_type_name'] = self.preloaded_data['property_types'].get(
                prop.get('dor_uc', ''), 'Unknown'
            )

            # Calculate age
            if prop.get('yr_blt'):
                prop['property_age'] = datetime.now().year - prop['yr_blt']

            return prop

        # Process in parallel
        tasks = [enrich_single(prop) for prop in properties]
        enriched = await asyncio.gather(*tasks)

        return enriched

    def _get_property_codes(self, property_type: str) -> List[str]:
        """Map property type to DOR codes"""
        type_mapping = {
            'single_family': ['0100', '0101', '0102', '0103'],
            'multi_family': ['0200', '0201', '0202'],
            'commercial': ['1000', '1100', '1200'],
            'industrial': ['4000', '4100', '4200'],
            'agricultural': ['5000', '5100', '5200'],
            'vacant': ['0000', '0001']
        }
        return type_mapping.get(property_type, [])

    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get data from Redis cache"""
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    def _set_cache(self, key: str, data: Dict, ttl: int = 3600):
        """Set data in Redis cache"""
        try:
            serialized = pickle.dumps(data)
            self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    def precompute_aggregations(self):
        """
        Precompute and cache common aggregations using PySpark
        Run this periodically (e.g., every hour) to keep data fresh
        """

        # Load full dataset
        df = self.spark.read \
            .format("jdbc") \
            .option("url", self.db_url.replace('postgresql://', 'jdbc:postgresql://')) \
            .option("dbtable", "florida_parcels") \
            .load()

        # City aggregations
        city_stats = df.groupBy("phy_city").agg(
            F.count("*").alias("count"),
            F.avg("jv").alias("avg_value"),
            F.min("jv").alias("min_value"),
            F.max("jv").alias("max_value")
        ).toPandas()

        self._set_cache("agg:city_stats", city_stats.to_dict('records'), ttl=7200)

        # Property type aggregations
        type_stats = df.groupBy("dor_uc").agg(
            F.count("*").alias("count"),
            F.avg("jv").alias("avg_value")
        ).toPandas()

        self._set_cache("agg:type_stats", type_stats.to_dict('records'), ttl=7200)

        # Year built distribution
        year_dist = df.filter(F.col("yr_blt").isNotNull()).groupBy("yr_blt").agg(
            F.count("*").alias("count")
        ).orderBy("yr_blt").toPandas()

        self._set_cache("agg:year_distribution", year_dist.to_dict('records'), ttl=7200)

        logger.info("Aggregations precomputed and cached")

    def optimize_database_indexes(self):
        """Create optimal indexes for common query patterns"""

        index_queries = [
            # Composite indexes for common filter combinations
            """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_search
               ON florida_parcels(phy_city, jv, yr_blt)""",

            # GIN index for full-text search
            """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_fulltext
               ON florida_parcels USING gin(
                   to_tsvector('english',
                   coalesce(phy_addr1, '') || ' ' ||
                   coalesce(phy_city, '') || ' ' ||
                   coalesce(owner_name, ''))
               )""",

            # BRIN index for large range scans
            """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_jv_brin
               ON florida_parcels USING brin(jv)""",

            # Partial indexes for common filters
            """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_residential
               ON florida_parcels(jv, yr_blt)
               WHERE dor_uc LIKE '01%'""",
        ]

        with self.engine.connect() as conn:
            for query in index_queries:
                try:
                    conn.execute(query)
                    conn.commit()
                    logger.info(f"Index created: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"Index creation failed: {e}")

    def cleanup(self):
        """Cleanup resources"""
        self.spark.stop()
        self.thread_pool.shutdown()
        self.process_pool.shutdown()
        self.engine.dispose()


# Singleton instance
data_engine = None

def get_data_engine() -> OptimizedDataEngine:
    """Get or create the data engine singleton"""
    global data_engine
    if data_engine is None:
        data_engine = OptimizedDataEngine()
    return data_engine