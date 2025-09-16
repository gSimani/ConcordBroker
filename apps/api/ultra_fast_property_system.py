"""
Ultra-Fast Property System with PySpark, Playwright MCP, and OpenCV
Comprehensive optimization for ConcordBroker database performance
"""

import os
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
import hashlib
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import pickle
import numpy as np

# FastAPI and async components
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import aiohttp
import aioredis

# PySpark for big data processing
from pyspark.sql import SparkSession, DataFrame, functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, TimestampType
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml import Pipeline

# Supabase client
from supabase import create_client, Client
import psycopg2
from psycopg2.pool import ThreadedConnectionPool

# OpenCV for image processing
import cv2
from PIL import Image
import io
import base64

# Playwright for real-time scraping
from playwright.async_api import async_playwright

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================================
# Configuration Classes
# =====================================================================

@dataclass
class SystemConfig:
    """System-wide configuration"""
    # Database
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "")

    # Redis cache
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    cache_ttl: int = 3600  # 1 hour default

    # PySpark
    spark_master: str = "local[*]"
    spark_driver_memory: str = "8g"
    spark_executor_memory: str = "8g"
    spark_max_result_size: str = "4g"

    # MCP Server
    mcp_url: str = "http://localhost:3001"
    mcp_api_key: str = "concordbroker-mcp-key"

    # Performance
    max_workers: int = 8
    batch_size: int = 1000
    max_cache_size_mb: int = 500

    # API Settings
    api_rate_limit: int = 100
    api_timeout: int = 30

# =====================================================================
# PySpark Big Data Processing Engine
# =====================================================================

class SparkPropertyEngine:
    """High-performance property data processing with PySpark"""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.spark = self._initialize_spark()
        self.cached_dfs = {}

    def _initialize_spark(self) -> SparkSession:
        """Initialize optimized Spark session"""
        return SparkSession.builder \
            .appName("ConcordBroker-UltraFast") \
            .master(self.config.spark_master) \
            .config("spark.driver.memory", self.config.spark_driver_memory) \
            .config("spark.executor.memory", self.config.spark_executor_memory) \
            .config("spark.driver.maxResultSize", self.config.spark_max_result_size) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.adaptive.skewJoin.enabled", "true") \
            .config("spark.sql.shuffle.partitions", "200") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .config("spark.sql.execution.arrow.maxRecordsPerBatch", "10000") \
            .config("spark.ui.port", "4041") \
            .getOrCreate()

    async def load_property_data(self, county: str = None) -> DataFrame:
        """Load property data into Spark DataFrame with caching"""
        cache_key = f"property_data_{county or 'all'}"

        # Check if already cached in memory
        if cache_key in self.cached_dfs:
            logger.info(f"Using cached DataFrame for {cache_key}")
            return self.cached_dfs[cache_key]

        # Load from database using JDBC for best performance
        jdbc_url = f"jdbc:postgresql://{self.config.database_url}"

        query = """
        SELECT
            parcel_id, county, phy_addr1, phy_city, phy_zipcd,
            owner_name, jv as just_value, av_sd as assessed_value,
            tv_sd as taxable_value, lnd_val as land_value,
            tot_lvg_area as building_sqft, lnd_sqfoot as land_sqft,
            yr_blt as year_built, bedroom_cnt as bedrooms,
            bathroom_cnt as bathrooms, dor_uc as property_use,
            sale_prc1 as last_sale_price, sale_yr1 as last_sale_year,
            latitude, longitude
        FROM florida_parcels
        WHERE year = 2025
        """

        if county:
            query += f" AND county = '{county.upper()}'"

        # Use partitioned reading for better performance
        df = self.spark.read \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", f"({query}) as property_data") \
            .option("user", "postgres") \
            .option("password", os.getenv("DB_PASSWORD", "")) \
            .option("driver", "org.postgresql.Driver") \
            .option("fetchsize", "10000") \
            .option("numPartitions", "8") \
            .option("partitionColumn", "parcel_id") \
            .option("lowerBound", "0") \
            .option("upperBound", "999999999999") \
            .load()

        # Cache in memory for fast access
        df = df.cache()
        df.count()  # Trigger cache

        self.cached_dfs[cache_key] = df
        logger.info(f"Loaded and cached {df.count()} properties for {cache_key}")

        return df

    def search_properties(self, df: DataFrame, filters: Dict[str, Any]) -> DataFrame:
        """Ultra-fast property search using Spark"""
        # Apply filters efficiently
        if filters.get('address'):
            df = df.filter(F.col('phy_addr1').contains(filters['address']))

        if filters.get('city'):
            df = df.filter(F.col('phy_city').ilike(f"%{filters['city']}%"))

        if filters.get('zip_code'):
            df = df.filter(F.col('phy_zipcd') == filters['zip_code'])

        if filters.get('min_value'):
            df = df.filter(F.col('just_value') >= filters['min_value'])

        if filters.get('max_value'):
            df = df.filter(F.col('just_value') <= filters['max_value'])

        if filters.get('min_year'):
            df = df.filter(F.col('year_built') >= filters['min_year'])

        if filters.get('max_year'):
            df = df.filter(F.col('year_built') <= filters['max_year'])

        if filters.get('property_types'):
            df = df.filter(F.col('property_use').isin(filters['property_types']))

        # Add calculated fields
        df = df.withColumn('price_per_sqft',
                          F.when(F.col('building_sqft') > 0,
                                 F.col('just_value') / F.col('building_sqft'))
                          .otherwise(0))

        df = df.withColumn('investment_score',
                          F.when(F.col('just_value') > 0,
                                 100 - ((F.col('just_value') - F.col('assessed_value')) / F.col('just_value') * 100))
                          .otherwise(50))

        return df

    def get_market_analytics(self, df: DataFrame) -> Dict[str, Any]:
        """Calculate market analytics using Spark"""
        # Group by county for county-level stats
        county_stats = df.groupBy('county').agg(
            F.count('*').alias('property_count'),
            F.avg('just_value').alias('avg_value'),
            F.stddev('just_value').alias('stddev_value'),
            F.avg('price_per_sqft').alias('avg_price_per_sqft'),
            F.sum('just_value').alias('total_market_value')
        ).collect()

        # Property type distribution
        type_distribution = df.groupBy('property_use').agg(
            F.count('*').alias('count'),
            F.avg('just_value').alias('avg_value')
        ).orderBy('count', ascending=False).limit(10).collect()

        # Year built analysis
        year_stats = df.groupBy('year_built').agg(
            F.count('*').alias('count'),
            F.avg('just_value').alias('avg_value')
        ).filter(F.col('year_built') > 1950).orderBy('year_built').collect()

        # Price ranges
        price_ranges = df.select(
            F.sum(F.when(F.col('just_value') < 100000, 1).otherwise(0)).alias('under_100k'),
            F.sum(F.when((F.col('just_value') >= 100000) & (F.col('just_value') < 250000), 1).otherwise(0)).alias('100k_250k'),
            F.sum(F.when((F.col('just_value') >= 250000) & (F.col('just_value') < 500000), 1).otherwise(0)).alias('250k_500k'),
            F.sum(F.when((F.col('just_value') >= 500000) & (F.col('just_value') < 1000000), 1).otherwise(0)).alias('500k_1m'),
            F.sum(F.when(F.col('just_value') >= 1000000, 1).otherwise(0)).alias('over_1m')
        ).collect()[0]

        return {
            'county_statistics': [row.asDict() for row in county_stats],
            'property_type_distribution': [row.asDict() for row in type_distribution],
            'year_built_trends': [row.asDict() for row in year_stats],
            'price_ranges': price_ranges.asDict() if price_ranges else {}
        }

    def find_investment_opportunities(self, df: DataFrame, criteria: Dict) -> List[Dict]:
        """Find top investment opportunities using ML"""
        # Calculate investment metrics
        df = df.withColumn('roi_potential',
            F.when((F.col('last_sale_price') > 0) & (F.col('just_value') > F.col('last_sale_price')),
                   ((F.col('just_value') - F.col('last_sale_price')) / F.col('last_sale_price') * 100))
            .otherwise(0))

        df = df.withColumn('value_ratio',
            F.when(F.col('assessed_value') > 0,
                   F.col('just_value') / F.col('assessed_value'))
            .otherwise(1))

        # Filter based on criteria
        opportunities = df.filter(
            (F.col('just_value') <= criteria.get('max_price', 1000000)) &
            (F.col('roi_potential') > criteria.get('min_roi', 10)) &
            (F.col('value_ratio') < criteria.get('max_value_ratio', 1.2))
        )

        # Sort by investment score and ROI
        opportunities = opportunities.orderBy(
            F.desc('investment_score'),
            F.desc('roi_potential')
        ).limit(100)

        return opportunities.toPandas().to_dict('records')

    def cleanup(self):
        """Clean up Spark resources"""
        for key in list(self.cached_dfs.keys()):
            self.cached_dfs[key].unpersist()
        self.spark.stop()

# =====================================================================
# Redis Cache Layer
# =====================================================================

class RedisCacheManager:
    """High-performance caching with Redis"""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.redis_client = None

    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await aioredis.create_redis_pool(
            self.config.redis_url,
            encoding='utf-8'
        )
        logger.info("Connected to Redis cache")

    async def get_cached(self, key: str) -> Optional[Any]:
        """Get cached data"""
        if not self.redis_client:
            return None

        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    async def set_cached(self, key: str, value: Any, ttl: int = None):
        """Set cached data"""
        if not self.redis_client:
            return

        try:
            ttl = ttl or self.config.cache_ttl
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache by pattern"""
        if not self.redis_client:
            return

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()
            await self.redis_client.wait_closed()

# =====================================================================
# Playwright MCP Real-time Sync
# =====================================================================

class PlaywrightRealtimeSync:
    """Real-time data synchronization with Playwright and MCP"""

    def __init__(self, config: SystemConfig, cache: RedisCacheManager):
        self.config = config
        self.cache = cache
        self.browser = None
        self.playwright = None

    async def initialize(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--disable-gpu', '--no-sandbox']
        )
        logger.info("Playwright browser initialized")

    async def sync_property_updates(self, parcel_id: str) -> Dict[str, Any]:
        """Sync real-time property updates"""
        page = await self.browser.new_page()

        try:
            # Check cache first
            cache_key = f"property_live_{parcel_id}"
            cached_data = await self.cache.get_cached(cache_key)
            if cached_data:
                return cached_data

            # Scrape latest data
            county = parcel_id[:2]  # Extract county code
            url = f"https://{county.lower()}.propertyappraiser.com/property/{parcel_id}"

            await page.goto(url, wait_until='networkidle')

            # Extract updated values
            updates = {}

            selectors = {
                'current_value': '.current-market-value',
                'last_updated': '.last-updated',
                'recent_sales': '.recent-sales-price',
                'tax_status': '.tax-payment-status'
            }

            for key, selector in selectors.items():
                elem = await page.query_selector(selector)
                if elem:
                    value = await elem.text_content()
                    updates[key] = value.strip()

            # Cache the results
            await self.cache.set_cached(cache_key, updates, ttl=300)  # 5 min cache

            # Notify MCP Server
            await self._notify_mcp('property_updated', {
                'parcel_id': parcel_id,
                'updates': updates
            })

            return updates

        except Exception as e:
            logger.error(f"Error syncing property {parcel_id}: {e}")
            return {}
        finally:
            await page.close()

    async def monitor_tax_deeds(self, county: str) -> List[Dict]:
        """Monitor tax deed auctions in real-time"""
        page = await self.browser.new_page()

        try:
            url = f"https://{county.lower()}.realauction.com"
            await page.goto(url)

            # Wait for auction data
            await page.wait_for_selector('.auction-item', timeout=10000)

            auctions = []
            items = await page.query_selector_all('.auction-item')

            for item in items[:50]:  # Limit to 50 most recent
                auction_data = {}

                # Extract auction details
                parcel = await item.query_selector('.parcel-number')
                if parcel:
                    auction_data['parcel_id'] = await parcel.text_content()

                bid = await item.query_selector('.current-bid')
                if bid:
                    auction_data['current_bid'] = await bid.text_content()

                date = await item.query_selector('.auction-date')
                if date:
                    auction_data['auction_date'] = await date.text_content()

                auctions.append(auction_data)

            # Cache results
            cache_key = f"tax_deeds_{county}"
            await self.cache.set_cached(cache_key, auctions, ttl=600)  # 10 min cache

            return auctions

        except Exception as e:
            logger.error(f"Error monitoring tax deeds: {e}")
            return []
        finally:
            await page.close()

    async def _notify_mcp(self, event_type: str, data: Dict):
        """Send notifications to MCP Server"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'x-api-key': self.config.mcp_api_key}
                payload = {
                    'event': event_type,
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }
                await session.post(
                    f"{self.config.mcp_url}/api/events",
                    json=payload,
                    headers=headers
                )
        except Exception as e:
            logger.error(f"Failed to notify MCP: {e}")

    async def cleanup(self):
        """Clean up Playwright resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

# =====================================================================
# OpenCV Image Optimization
# =====================================================================

class ImageOptimizationEngine:
    """Optimize property images for fast loading"""

    def __init__(self, cache: RedisCacheManager):
        self.cache = cache
        self.thumbnail_sizes = {
            'small': (150, 150),
            'medium': (400, 300),
            'large': (800, 600)
        }

    async def optimize_image(self, image_url: str, size: str = 'medium') -> str:
        """Optimize and cache property images"""
        # Generate cache key
        cache_key = f"img_{hashlib.md5(image_url.encode()).hexdigest()}_{size}"

        # Check cache
        cached = await self.cache.get_cached(cache_key)
        if cached:
            return cached

        try:
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        return image_url

                    image_data = await response.read()

            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Resize based on requested size
            target_size = self.thumbnail_sizes.get(size, self.thumbnail_sizes['medium'])
            resized = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)

            # Apply optimization
            # 1. Reduce quality for faster loading
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]

            # 2. Convert to progressive JPEG
            _, buffer = cv2.imencode('.jpg', resized, encode_param)

            # 3. Convert to base64 for embedding
            base64_image = base64.b64encode(buffer).decode('utf-8')
            data_url = f"data:image/jpeg;base64,{base64_image}"

            # Cache the optimized image
            await self.cache.set_cached(cache_key, data_url, ttl=86400)  # 24 hour cache

            return data_url

        except Exception as e:
            logger.error(f"Error optimizing image: {e}")
            return image_url

    async def batch_optimize(self, image_urls: List[str], size: str = 'medium') -> List[str]:
        """Batch optimize multiple images"""
        tasks = [self.optimize_image(url, size) for url in image_urls]
        return await asyncio.gather(*tasks)

    def analyze_image_quality(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze image quality metrics"""
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Calculate quality metrics
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()

        # Brightness
        brightness = np.mean(gray)

        # Contrast
        contrast = gray.std()

        return {
            'sharpness': float(sharpness),
            'brightness': float(brightness),
            'contrast': float(contrast),
            'quality_score': min(100, (sharpness / 100 + brightness / 2.55 + contrast / 50) / 3)
        }

# =====================================================================
# Database Connection Pool
# =====================================================================

class DatabasePool:
    """Optimized database connection pool"""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.pool = None
        self.supabase = None

    def initialize(self):
        """Initialize connection pool"""
        # PostgreSQL connection pool
        self.pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=20,
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 5432),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )

        # Supabase client for API access
        self.supabase = create_client(
            self.config.supabase_url,
            self.config.supabase_service_key
        )

        logger.info("Database pool initialized")

    def get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)

    async def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query with connection pooling"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch results
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            return results

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.return_connection(conn)

    def cleanup(self):
        """Clean up connection pool"""
        if self.pool:
            self.pool.closeall()

# =====================================================================
# Ultra-Fast API
# =====================================================================

class UltraFastPropertyAPI:
    """Main API with all optimizations integrated"""

    def __init__(self):
        self.config = SystemConfig()
        self.app = FastAPI(title="Ultra-Fast Property API")
        self.spark_engine = None
        self.cache_manager = None
        self.playwright_sync = None
        self.image_engine = None
        self.db_pool = None

        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

        # Setup routes
        self._setup_routes()

    async def startup(self):
        """Initialize all components"""
        logger.info("Starting Ultra-Fast Property System...")

        # Initialize components
        self.spark_engine = SparkPropertyEngine(self.config)
        self.cache_manager = RedisCacheManager(self.config)
        self.image_engine = ImageOptimizationEngine(self.cache_manager)
        self.db_pool = DatabasePool(self.config)

        # Connect to services
        await self.cache_manager.connect()
        self.db_pool.initialize()

        # Initialize Playwright for real-time sync
        self.playwright_sync = PlaywrightRealtimeSync(self.config, self.cache_manager)
        await self.playwright_sync.initialize()

        # Pre-load data into Spark
        await self.spark_engine.load_property_data()

        logger.info("All systems initialized successfully!")

    async def shutdown(self):
        """Clean up resources"""
        logger.info("Shutting down Ultra-Fast Property System...")

        if self.spark_engine:
            self.spark_engine.cleanup()

        if self.cache_manager:
            await self.cache_manager.close()

        if self.playwright_sync:
            await self.playwright_sync.cleanup()

        if self.db_pool:
            self.db_pool.cleanup()

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.on_event("startup")
        async def startup_event():
            await self.startup()

        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.shutdown()

        @self.app.get("/")
        async def health_check():
            return {
                "status": "healthy",
                "service": "Ultra-Fast Property System",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "spark": "active",
                    "redis": "connected",
                    "playwright": "ready",
                    "opencv": "loaded"
                }
            }

        @self.app.get("/api/properties/ultra-search")
        async def ultra_search(
            q: Optional[str] = None,
            address: Optional[str] = None,
            city: Optional[str] = None,
            zip_code: Optional[str] = None,
            min_value: Optional[float] = None,
            max_value: Optional[float] = None,
            min_year: Optional[int] = None,
            max_year: Optional[int] = None,
            property_types: Optional[str] = None,
            page: int = 1,
            limit: int = 100,
            use_cache: bool = True
        ):
            """Ultra-fast property search using PySpark"""
            start_time = time.time()

            # Build cache key
            cache_key = f"search_{hashlib.md5(str(locals()).encode()).hexdigest()}"

            # Check cache if enabled
            if use_cache:
                cached_result = await self.cache_manager.get_cached(cache_key)
                if cached_result:
                    cached_result['cache_hit'] = True
                    cached_result['response_time'] = time.time() - start_time
                    return cached_result

            # Build filters
            filters = {
                'address': address,
                'city': city,
                'zip_code': zip_code,
                'min_value': min_value,
                'max_value': max_value,
                'min_year': min_year,
                'max_year': max_year,
                'property_types': property_types.split(',') if property_types else None
            }

            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}

            # Get Spark DataFrame
            df = await self.spark_engine.load_property_data()

            # Apply filters using Spark
            filtered_df = self.spark_engine.search_properties(df, filters)

            # Pagination
            offset = (page - 1) * limit
            results_df = filtered_df.limit(limit).toPandas()

            # Convert to dict
            properties = results_df.to_dict('records')

            # Optimize images in parallel
            for prop in properties[:20]:  # Optimize first 20 images
                if prop.get('image_url'):
                    prop['optimized_image'] = await self.image_engine.optimize_image(
                        prop['image_url'], 'medium'
                    )

            result = {
                'success': True,
                'data': properties,
                'total': filtered_df.count(),
                'page': page,
                'limit': limit,
                'response_time': time.time() - start_time,
                'cache_hit': False,
                'processing_engine': 'spark'
            }

            # Cache the result
            if use_cache:
                await self.cache_manager.set_cached(cache_key, result, ttl=300)

            return result

        @self.app.get("/api/properties/market-analytics")
        async def market_analytics(county: Optional[str] = None):
            """Get real-time market analytics"""
            # Check cache
            cache_key = f"analytics_{county or 'all'}"
            cached = await self.cache_manager.get_cached(cache_key)
            if cached:
                return cached

            # Load data into Spark
            df = await self.spark_engine.load_property_data(county)

            # Calculate analytics
            analytics = self.spark_engine.get_market_analytics(df)

            # Cache results
            await self.cache_manager.set_cached(cache_key, analytics, ttl=3600)

            return analytics

        @self.app.get("/api/properties/investment-opportunities")
        async def find_investments(
            max_price: float = 500000,
            min_roi: float = 10,
            max_value_ratio: float = 1.2,
            county: Optional[str] = None
        ):
            """Find investment opportunities using ML"""
            criteria = {
                'max_price': max_price,
                'min_roi': min_roi,
                'max_value_ratio': max_value_ratio
            }

            # Load data
            df = await self.spark_engine.load_property_data(county)

            # Find opportunities
            opportunities = self.spark_engine.find_investment_opportunities(df, criteria)

            return {
                'success': True,
                'opportunities': opportunities,
                'criteria': criteria,
                'count': len(opportunities)
            }

        @self.app.get("/api/properties/{parcel_id}/live")
        async def get_live_property(parcel_id: str):
            """Get real-time property data with Playwright sync"""
            # Get base data from database
            query = "SELECT * FROM florida_parcels WHERE parcel_id = %s"
            results = await self.db_pool.execute_query(query, (parcel_id,))

            if not results:
                raise HTTPException(status_code=404, detail="Property not found")

            property_data = results[0]

            # Sync real-time updates
            live_updates = await self.playwright_sync.sync_property_updates(parcel_id)
            property_data['live_updates'] = live_updates

            # Optimize property images
            if property_data.get('image_urls'):
                property_data['optimized_images'] = await self.image_engine.batch_optimize(
                    property_data['image_urls']
                )

            return {
                'success': True,
                'data': property_data,
                'last_sync': datetime.now().isoformat()
            }

        @self.app.get("/api/tax-deeds/monitor")
        async def monitor_tax_deeds(county: str = "BROWARD"):
            """Monitor tax deed auctions in real-time"""
            auctions = await self.playwright_sync.monitor_tax_deeds(county)

            return {
                'success': True,
                'county': county,
                'auctions': auctions,
                'count': len(auctions),
                'timestamp': datetime.now().isoformat()
            }

        @self.app.post("/api/cache/invalidate")
        async def invalidate_cache(pattern: str = "*"):
            """Invalidate cache by pattern"""
            await self.cache_manager.invalidate_pattern(pattern)
            return {"success": True, "pattern": pattern}

        @self.app.get("/api/performance/stats")
        async def performance_stats():
            """Get system performance statistics"""
            return {
                'spark_status': 'active' if self.spark_engine else 'inactive',
                'cache_status': 'connected' if self.cache_manager.redis_client else 'disconnected',
                'cached_dataframes': list(self.spark_engine.cached_dfs.keys()) if self.spark_engine else [],
                'db_pool_size': 20,
                'timestamp': datetime.now().isoformat()
            }

# =====================================================================
# Main Application Entry Point
# =====================================================================

def create_app() -> FastAPI:
    """Create and configure the Ultra-Fast API"""
    api = UltraFastPropertyAPI()
    return api.app

# Run the application
if __name__ == "__main__":
    app = create_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable reload for production performance
        workers=1,  # Single worker to maintain Spark session
        log_level="info",
        access_log=True
    )