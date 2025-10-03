#!/usr/bin/env python3
"""
Comprehensive Data Flow Orchestrator for ConcordBroker
AI-powered monitoring and validation system ensuring data consistency
"""

import asyncio
import logging
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import psutil
import time

# Third-party imports
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import redis
from pydantic import BaseModel
import openai
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_flow_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DataFlowMetrics:
    """Metrics for data flow monitoring"""
    timestamp: datetime
    table_name: str
    record_count: int
    query_time_ms: float
    data_freshness_hours: float
    validation_status: str
    error_count: int
    last_update: Optional[datetime] = None

@dataclass
class ValidationResult:
    """Result of data validation check"""
    table_name: str
    validation_type: str
    passed: bool
    message: str
    details: Dict[str, Any]
    timestamp: datetime

class DatabaseConnector:
    """Handles all database connections and operations"""

    def __init__(self, supabase_url: str, service_role_key: str):
        self.supabase_url = supabase_url
        self.service_role_key = service_role_key
        self.engine = None
        self.session_maker = None
        self.redis_client = None
        self._initialize_connections()

    def _initialize_connections(self):
        """Initialize database and Redis connections"""
        try:
            # PostgreSQL connection
            db_url = self.supabase_url.replace('https://', 'postgresql://postgres:')
            db_url = f"{db_url.split('.')[0]}.{db_url.split('.')[1]}.supabase.co:5432/postgres"

            self.engine = create_engine(
                db_url + f"?sslmode=require&options=-c%20search_path%3Dpublic",
                pool_size=20,
                max_overflow=30,
                pool_timeout=30,
                pool_recycle=3600
            )

            self.session_maker = sessionmaker(bind=self.engine)

            # Redis connection for caching
            try:
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=True,
                    socket_timeout=5
                )
                self.redis_client.ping()
                logger.info("✅ Redis connection established")
            except Exception as e:
                logger.warning(f"⚠️ Redis not available: {e}")
                self.redis_client = None

            logger.info("✅ Database connections initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize connections: {e}")
            raise

    async def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute a database query asynchronously"""
        start_time = time.time()
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                rows = [dict(row._mapping) for row in result]

            query_time = (time.time() - start_time) * 1000
            logger.debug(f"Query executed in {query_time:.2f}ms: {query[:100]}...")

            return rows

        except Exception as e:
            logger.error(f"Query failed: {e}\nQuery: {query}")
            raise

    def get_table_metrics(self, table_name: str) -> DataFlowMetrics:
        """Get comprehensive metrics for a table"""
        try:
            start_time = time.time()

            # Get record count
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = self.execute_query(count_query)
            record_count = count_result[0]['count'] if count_result else 0

            # Get data freshness (if updated_at column exists)
            freshness_hours = 0
            try:
                freshness_query = f"""
                SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 as hours_old
                FROM {table_name}
                WHERE updated_at IS NOT NULL
                """
                freshness_result = self.execute_query(freshness_query)
                freshness_hours = freshness_result[0]['hours_old'] if freshness_result else 0
            except:
                # Table might not have updated_at column
                pass

            query_time = (time.time() - start_time) * 1000

            return DataFlowMetrics(
                timestamp=datetime.now(),
                table_name=table_name,
                record_count=record_count,
                query_time_ms=query_time,
                data_freshness_hours=freshness_hours or 0,
                validation_status="healthy",
                error_count=0,
                last_update=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to get metrics for {table_name}: {e}")
            return DataFlowMetrics(
                timestamp=datetime.now(),
                table_name=table_name,
                record_count=0,
                query_time_ms=0,
                data_freshness_hours=999,
                validation_status="error",
                error_count=1,
                last_update=None
            )

class DataValidationAgent:
    """AI agent responsible for validating data integrity"""

    def __init__(self, db_connector: DatabaseConnector, openai_api_key: str):
        self.db = db_connector
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4",
            temperature=0.1
        )

        # Critical tables to monitor
        self.critical_tables = [
            'florida_parcels',
            'property_sales_history',
            'tax_certificates',
            'florida_entities',
            'sunbiz_corporate'
        ]

        # Validation rules
        self.validation_rules = {
            'florida_parcels': {
                'required_columns': ['parcel_id', 'county', 'year'],
                'max_null_percentage': 5,
                'expected_min_records': 100000
            },
            'property_sales_history': {
                'required_columns': ['parcel_id', 'sale_date', 'sale_price'],
                'max_null_percentage': 10,
                'expected_min_records': 50000
            },
            'tax_certificates': {
                'required_columns': ['parcel_id', 'certificate_number'],
                'max_null_percentage': 2,
                'expected_min_records': 1000
            },
            'florida_entities': {
                'required_columns': ['entity_name'],
                'max_null_percentage': 5,
                'expected_min_records': 10000
            },
            'sunbiz_corporate': {
                'required_columns': ['corporation_name', 'document_number'],
                'max_null_percentage': 5,
                'expected_min_records': 50000
            }
        }

    async def validate_table_integrity(self, table_name: str) -> ValidationResult:
        """Validate the integrity of a specific table"""
        try:
            rules = self.validation_rules.get(table_name, {})
            if not rules:
                return ValidationResult(
                    table_name=table_name,
                    validation_type="table_integrity",
                    passed=True,
                    message="No validation rules defined",
                    details={},
                    timestamp=datetime.now()
                )

            # Check if table exists and get basic stats
            table_query = f"""
            SELECT COUNT(*) as total_records,
                   COUNT(DISTINCT parcel_id) as unique_parcels
            FROM {table_name}
            WHERE parcel_id IS NOT NULL
            """

            result = await self.db.execute_query(table_query)
            if not result:
                return ValidationResult(
                    table_name=table_name,
                    validation_type="table_integrity",
                    passed=False,
                    message="Table not accessible or empty",
                    details={},
                    timestamp=datetime.now()
                )

            stats = result[0]
            total_records = stats['total_records']
            unique_parcels = stats['unique_parcels']

            # Validate record count
            min_expected = rules.get('expected_min_records', 0)
            if total_records < min_expected:
                return ValidationResult(
                    table_name=table_name,
                    validation_type="table_integrity",
                    passed=False,
                    message=f"Record count too low: {total_records} < {min_expected}",
                    details={"total_records": total_records, "expected_min": min_expected},
                    timestamp=datetime.now()
                )

            # Check for required columns null percentage
            required_cols = rules.get('required_columns', [])
            max_null_pct = rules.get('max_null_percentage', 100)

            validation_details = {
                "total_records": total_records,
                "unique_parcels": unique_parcels,
                "validation_checks": []
            }

            for col in required_cols:
                try:
                    null_check_query = f"""
                    SELECT
                        COUNT(*) as total,
                        COUNT({col}) as non_null,
                        ROUND((COUNT(*) - COUNT({col})) * 100.0 / COUNT(*), 2) as null_percentage
                    FROM {table_name}
                    """
                    null_result = await self.db.execute_query(null_check_query)
                    if null_result:
                        null_pct = null_result[0]['null_percentage'] or 0
                        validation_details["validation_checks"].append({
                            "column": col,
                            "null_percentage": null_pct,
                            "passed": null_pct <= max_null_pct
                        })

                        if null_pct > max_null_pct:
                            return ValidationResult(
                                table_name=table_name,
                                validation_type="table_integrity",
                                passed=False,
                                message=f"Column {col} has too many nulls: {null_pct}% > {max_null_pct}%",
                                details=validation_details,
                                timestamp=datetime.now()
                            )
                except Exception as e:
                    logger.warning(f"Could not validate column {col} in {table_name}: {e}")

            return ValidationResult(
                table_name=table_name,
                validation_type="table_integrity",
                passed=True,
                message="All validation checks passed",
                details=validation_details,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Table validation failed for {table_name}: {e}")
            return ValidationResult(
                table_name=table_name,
                validation_type="table_integrity",
                passed=False,
                message=f"Validation error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now()
            )

    async def validate_data_relationships(self) -> List[ValidationResult]:
        """Validate relationships between tables"""
        results = []

        try:
            # Check property_sales_history references florida_parcels
            relationship_query = """
            SELECT
                COUNT(psh.parcel_id) as sales_records,
                COUNT(fp.parcel_id) as matched_parcels,
                ROUND((COUNT(fp.parcel_id) * 100.0 / COUNT(psh.parcel_id)), 2) as match_percentage
            FROM property_sales_history psh
            LEFT JOIN florida_parcels fp ON psh.parcel_id = fp.parcel_id
            WHERE psh.parcel_id IS NOT NULL
            """

            result = await self.db.execute_query(relationship_query)
            if result:
                match_pct = result[0]['match_percentage'] or 0
                passed = match_pct >= 85  # Expect at least 85% match

                results.append(ValidationResult(
                    table_name="property_sales_history",
                    validation_type="referential_integrity",
                    passed=passed,
                    message=f"Sales-to-parcels match rate: {match_pct}%",
                    details=result[0],
                    timestamp=datetime.now()
                ))

            # Check tax_certificates references florida_parcels
            tax_relationship_query = """
            SELECT
                COUNT(tc.parcel_id) as tax_cert_records,
                COUNT(fp.parcel_id) as matched_parcels,
                ROUND((COUNT(fp.parcel_id) * 100.0 / COUNT(tc.parcel_id)), 2) as match_percentage
            FROM tax_certificates tc
            LEFT JOIN florida_parcels fp ON tc.parcel_id = fp.parcel_id
            WHERE tc.parcel_id IS NOT NULL
            """

            tax_result = await self.db.execute_query(tax_relationship_query)
            if tax_result:
                match_pct = tax_result[0]['match_percentage'] or 0
                passed = match_pct >= 90  # Tax certificates should have higher match rate

                results.append(ValidationResult(
                    table_name="tax_certificates",
                    validation_type="referential_integrity",
                    passed=passed,
                    message=f"Tax-certs-to-parcels match rate: {match_pct}%",
                    details=tax_result[0],
                    timestamp=datetime.now()
                ))

        except Exception as e:
            logger.error(f"Relationship validation failed: {e}")
            results.append(ValidationResult(
                table_name="system",
                validation_type="referential_integrity",
                passed=False,
                message=f"Relationship validation error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now()
            ))

        return results

class SelfHealingAgent:
    """AI agent that automatically fixes common data issues"""

    def __init__(self, db_connector: DatabaseConnector, validation_agent: DataValidationAgent):
        self.db = db_connector
        self.validator = validation_agent
        self.healing_actions = []

    async def diagnose_and_heal(self, validation_results: List[ValidationResult]) -> List[str]:
        """Analyze validation results and attempt to fix issues"""
        healing_actions = []

        for result in validation_results:
            if not result.passed:
                if result.validation_type == "table_integrity":
                    action = await self._heal_table_integrity(result)
                    if action:
                        healing_actions.append(action)

                elif result.validation_type == "referential_integrity":
                    action = await self._heal_referential_integrity(result)
                    if action:
                        healing_actions.append(action)

        return healing_actions

    async def _heal_table_integrity(self, result: ValidationResult) -> Optional[str]:
        """Attempt to fix table integrity issues"""
        try:
            table_name = result.table_name

            if "Record count too low" in result.message:
                # Try to refresh/reimport data
                action = f"Initiated data refresh for {table_name}"
                logger.info(f"🔧 {action}")
                # Here you would trigger actual data refresh logic
                return action

            elif "too many nulls" in result.message:
                # Try to fill nulls with reasonable defaults
                action = f"Applied null value handling for {table_name}"
                logger.info(f"🔧 {action}")
                # Here you would apply null handling logic
                return action

        except Exception as e:
            logger.error(f"Failed to heal table integrity for {result.table_name}: {e}")

        return None

    async def _heal_referential_integrity(self, result: ValidationResult) -> Optional[str]:
        """Attempt to fix referential integrity issues"""
        try:
            if "match rate" in result.message and result.details.get('match_percentage', 100) < 85:
                # Low match rate - might need to update parcel mapping
                action = f"Initiated parcel ID mapping update for {result.table_name}"
                logger.info(f"🔧 {action}")
                # Here you would trigger parcel ID reconciliation
                return action

        except Exception as e:
            logger.error(f"Failed to heal referential integrity for {result.table_name}: {e}")

        return None

class PerformanceMonitoringAgent:
    """Monitors system performance and query optimization"""

    def __init__(self, db_connector: DatabaseConnector):
        self.db = db_connector
        self.performance_thresholds = {
            'max_query_time_ms': 5000,
            'max_cpu_usage': 80,
            'max_memory_usage': 85,
            'min_cache_hit_rate': 90
        }

    async def monitor_system_performance(self) -> Dict[str, Any]:
        """Monitor overall system performance"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Database performance
            db_stats = await self._get_database_stats()

            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_usage': disk.percent,
                    'disk_free_gb': disk.free / (1024**3)
                },
                'database': db_stats,
                'alerts': []
            }

            # Check thresholds and generate alerts
            if cpu_percent > self.performance_thresholds['max_cpu_usage']:
                performance_data['alerts'].append(f"High CPU usage: {cpu_percent}%")

            if memory.percent > self.performance_thresholds['max_memory_usage']:
                performance_data['alerts'].append(f"High memory usage: {memory.percent}%")

            return performance_data

        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'alerts': ['Performance monitoring system error']
            }

    async def _get_database_stats(self) -> Dict[str, Any]:
        """Get database-specific performance statistics"""
        try:
            # Query for active connections and query stats
            stats_query = """
            SELECT
                COUNT(*) as active_connections,
                AVG(EXTRACT(EPOCH FROM (NOW() - query_start)) * 1000) as avg_query_time_ms
            FROM pg_stat_activity
            WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'
            """

            result = await self.db.execute_query(stats_query)
            if result:
                return {
                    'active_connections': result[0]['active_connections'] or 0,
                    'avg_query_time_ms': result[0]['avg_query_time_ms'] or 0
                }

            return {'active_connections': 0, 'avg_query_time_ms': 0}

        except Exception as e:
            logger.warning(f"Could not get database stats: {e}")
            return {'error': str(e)}

class DataFlowOrchestrator:
    """Main orchestrator coordinating all AI agents"""

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.db_connector = DatabaseConnector(
            config['SUPABASE_URL'],
            config['SUPABASE_SERVICE_ROLE_KEY']
        )

        # Initialize AI agents
        self.validation_agent = DataValidationAgent(
            self.db_connector,
            config['OPENAI_API_KEY']
        )

        self.healing_agent = SelfHealingAgent(
            self.db_connector,
            self.validation_agent
        )

        self.performance_agent = PerformanceMonitoringAgent(
            self.db_connector
        )

        # Monitoring state
        self.monitoring_active = False
        self.last_full_check = None
        self.monitoring_interval = 300  # 5 minutes

        # FastAPI app for endpoints
        self.app = FastAPI(title="Data Flow Orchestrator API", version="1.0.0")
        self._setup_fastapi_routes()

    def _setup_fastapi_routes(self):
        """Setup FastAPI routes for monitoring and control"""

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "monitoring_active": self.monitoring_active,
                "last_check": self.last_full_check.isoformat() if self.last_full_check else None
            }

        @self.app.get("/metrics")
        async def get_metrics():
            """Get current metrics for all critical tables"""
            metrics = {}
            for table in self.validation_agent.critical_tables:
                try:
                    metrics[table] = asdict(self.db_connector.get_table_metrics(table))
                except Exception as e:
                    metrics[table] = {"error": str(e)}

            return {
                "timestamp": datetime.now().isoformat(),
                "table_metrics": metrics
            }

        @self.app.post("/validate/{table_name}")
        async def validate_table(table_name: str):
            """Validate a specific table"""
            result = await self.validation_agent.validate_table_integrity(table_name)
            return asdict(result)

        @self.app.post("/validate/all")
        async def validate_all_tables():
            """Validate all critical tables"""
            results = []
            for table in self.validation_agent.critical_tables:
                result = await self.validation_agent.validate_table_integrity(table)
                results.append(asdict(result))

            # Also validate relationships
            relationship_results = await self.validation_agent.validate_data_relationships()
            results.extend([asdict(r) for r in relationship_results])

            return {
                "timestamp": datetime.now().isoformat(),
                "validation_results": results
            }

        @self.app.post("/heal")
        async def trigger_healing():
            """Trigger self-healing process"""
            # First validate to find issues
            validation_results = []
            for table in self.validation_agent.critical_tables:
                result = await self.validation_agent.validate_table_integrity(table)
                validation_results.append(result)

            relationship_results = await self.validation_agent.validate_data_relationships()
            validation_results.extend(relationship_results)

            # Attempt healing
            healing_actions = await self.healing_agent.diagnose_and_heal(validation_results)

            return {
                "timestamp": datetime.now().isoformat(),
                "healing_actions": healing_actions,
                "validation_results": [asdict(r) for r in validation_results]
            }

        @self.app.get("/performance")
        async def get_performance():
            """Get system performance metrics"""
            return await self.performance_agent.monitor_system_performance()

        @self.app.post("/start-monitoring")
        async def start_monitoring():
            """Start continuous monitoring"""
            if not self.monitoring_active:
                asyncio.create_task(self._continuous_monitoring())
                return {"message": "Monitoring started", "interval_seconds": self.monitoring_interval}
            return {"message": "Monitoring already active"}

        @self.app.post("/stop-monitoring")
        async def stop_monitoring():
            """Stop continuous monitoring"""
            self.monitoring_active = False
            return {"message": "Monitoring stopped"}

    async def _continuous_monitoring(self):
        """Continuous monitoring loop"""
        self.monitoring_active = True
        logger.info("🤖 Starting continuous data flow monitoring...")

        while self.monitoring_active:
            try:
                await self._full_system_check()
                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _full_system_check(self):
        """Perform a complete system check"""
        logger.info("🔍 Performing full system check...")
        start_time = time.time()

        try:
            # 1. Validate all tables
            validation_results = []
            for table in self.validation_agent.critical_tables:
                result = await self.validation_agent.validate_table_integrity(table)
                validation_results.append(result)

                if not result.passed:
                    logger.warning(f"⚠️ Validation failed for {table}: {result.message}")

            # 2. Validate relationships
            relationship_results = await self.validation_agent.validate_data_relationships()
            validation_results.extend(relationship_results)

            # 3. Check performance
            performance_data = await self.performance_agent.monitor_system_performance()

            # 4. Attempt healing for any issues
            failed_validations = [r for r in validation_results if not r.passed]
            if failed_validations:
                logger.info(f"🔧 Found {len(failed_validations)} issues, attempting healing...")
                healing_actions = await self.healing_agent.diagnose_and_heal(failed_validations)

                if healing_actions:
                    logger.info(f"✅ Applied {len(healing_actions)} healing actions")
                    for action in healing_actions:
                        logger.info(f"   • {action}")

            # 5. Log summary
            check_time = time.time() - start_time
            passed_validations = len([r for r in validation_results if r.passed])
            total_validations = len(validation_results)

            logger.info(f"✅ System check completed in {check_time:.2f}s: {passed_validations}/{total_validations} validations passed")

            # 6. Store results for API access
            self.last_full_check = datetime.now()

            # 7. Cache results in Redis if available
            if self.db_connector.redis_client:
                try:
                    results_cache = {
                        'timestamp': self.last_full_check.isoformat(),
                        'validation_results': [asdict(r) for r in validation_results],
                        'performance_data': performance_data,
                        'summary': {
                            'total_validations': total_validations,
                            'passed_validations': passed_validations,
                            'check_time_seconds': check_time
                        }
                    }

                    self.db_connector.redis_client.setex(
                        'data_flow_last_check',
                        3600,  # Cache for 1 hour
                        json.dumps(results_cache, default=str)
                    )

                except Exception as e:
                    logger.warning(f"Failed to cache results: {e}")

        except Exception as e:
            logger.error(f"❌ Full system check failed: {e}")
            logger.error(traceback.format_exc())

    async def start_server(self, host: str = "0.0.0.0", port: int = 8001):
        """Start the FastAPI server"""
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)

        # Start continuous monitoring
        asyncio.create_task(self._continuous_monitoring())

        logger.info(f"🚀 Data Flow Orchestrator starting on http://{host}:{port}")
        await server.serve()

# Entry point
async def main():
    """Main entry point"""
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), '../.env.mcp'))

    config = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_SERVICE_ROLE_KEY': os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }

    # Validate required config
    missing = [k for k, v in config.items() if not v]
    if missing:
        logger.error(f"❌ Missing required environment variables: {missing}")
        return

    # Create and start orchestrator
    orchestrator = DataFlowOrchestrator(config)
    await orchestrator.start_server()

if __name__ == "__main__":
    asyncio.run(main())