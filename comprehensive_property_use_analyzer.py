#!/usr/bin/env python3
"""
Comprehensive Property Use Analyzer for Florida Parcels Database
Analyzes 9.1M properties to identify ALL unique property uses/types
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Optional
import logging
from dataclasses import dataclass, asdict

# Database imports
import psycopg2
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker
import asyncpg
import asyncio

# Analytics imports
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, count, desc, when, regexp_replace, trim, upper
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    print("PySpark not available - using pandas for analysis")

# Web framework imports
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.mcp')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('property_use_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PropertyUseStats:
    """Statistics for a property use type"""
    use_code: str
    use_description: str
    count: int
    percentage: float
    counties: List[str]
    avg_just_value: Optional[float] = None
    avg_building_value: Optional[float] = None
    avg_land_value: Optional[float] = None

@dataclass
class CategoryMapping:
    """Mapping of property uses to filter categories"""
    category: str
    use_codes: List[str]
    count: int
    percentage: float

class PropertyUseAnalyzer:
    """Main analyzer class for property use analysis"""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.db_url = f"postgresql://postgres.{self.supabase_url.split('//')[1].split('.')[0]}:{os.getenv('SUPABASE_DB_PASSWORD', '')}@{self.supabase_url.split('//')[1]}/postgres"

        self.engine = None
        self.spark = None
        self.property_uses = {}
        self.dor_codes = {}
        self.category_mappings = {}

        # Current filter categories from the frontend
        self.current_categories = [
            "Residential", "Commercial", "Industrial", "Agricultural",
            "Vacant Land", "Government", "Conservation", "Religious",
            "Vacant/Special", "Tax Deed Sales"
        ]

    def initialize_connections(self):
        """Initialize database and Spark connections"""
        try:
            # SQLAlchemy connection
            self.engine = create_engine(
                self.db_url,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600
            )
            logger.info("SQLAlchemy connection established")

            # PySpark connection (if available)
            if PYSPARK_AVAILABLE:
                self.spark = SparkSession.builder \
                    .appName("PropertyUseAnalyzer") \
                    .config("spark.driver.memory", "4g") \
                    .config("spark.executor.memory", "4g") \
                    .config("spark.sql.adaptive.enabled", "true") \
                    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                    .getOrCreate()
                logger.info("PySpark session created")

        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise

    def query_unique_property_uses(self) -> pd.DataFrame:
        """Query all unique property_use values from florida_parcels"""
        query = """
        SELECT
            property_use,
            COUNT(*) as count,
            COUNT(DISTINCT county) as county_count,
            ARRAY_AGG(DISTINCT county ORDER BY county) as counties,
            AVG(CASE WHEN just_value > 0 THEN just_value END) as avg_just_value,
            AVG(CASE WHEN building_value > 0 THEN building_value END) as avg_building_value,
            AVG(CASE WHEN land_value > 0 THEN land_value END) as avg_land_value,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 4) as percentage
        FROM florida_parcels
        WHERE property_use IS NOT NULL
            AND property_use != ''
        GROUP BY property_use
        ORDER BY count DESC
        """

        logger.info("Querying unique property uses...")
        try:
            df = pd.read_sql(query, self.engine)
            logger.info(f"Found {len(df)} unique property use types")
            return df
        except Exception as e:
            logger.error(f"Error querying property uses: {e}")
            raise

    def query_dor_use_codes(self) -> pd.DataFrame:
        """Query DOR use codes if they exist in the database"""
        # Check if DOR use codes table exists
        try:
            query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE '%dor%' OR table_name LIKE '%use_code%'
            """
            tables = pd.read_sql(query, self.engine)
            logger.info(f"Found DOR-related tables: {tables['table_name'].tolist()}")

            # Try to query DOR codes
            if 'dor_use_codes' in tables['table_name'].values:
                dor_query = """
                SELECT
                    use_code,
                    use_description,
                    category,
                    COUNT(*) as usage_count
                FROM dor_use_codes d
                LEFT JOIN florida_parcels f ON d.use_code = f.property_use
                GROUP BY use_code, use_description, category
                ORDER BY usage_count DESC NULLS LAST
                """
                return pd.read_sql(dor_query, self.engine)
            else:
                logger.info("No DOR use codes table found")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error querying DOR codes: {e}")
            return pd.DataFrame()

    def analyze_with_pyspark(self) -> Dict[str, Any]:
        """Use PySpark for large-scale analysis if available"""
        if not PYSPARK_AVAILABLE or not self.spark:
            logger.info("PySpark not available, skipping Spark analysis")
            return {}

        try:
            # Read data into Spark DataFrame
            df = self.spark.read.format("jdbc") \
                .option("url", self.db_url) \
                .option("dbtable", "florida_parcels") \
                .option("driver", "org.postgresql.Driver") \
                .load()

            # Analyze property uses with Spark
            property_use_analysis = df.filter(
                (col("property_use").isNotNull()) &
                (col("property_use") != "")
            ).groupBy("property_use") \
            .agg(
                count("*").alias("count"),
                avg("just_value").alias("avg_just_value"),
                avg("building_value").alias("avg_building_value"),
                avg("land_value").alias("avg_land_value")
            ).orderBy(desc("count"))

            # Convert to pandas for easier handling
            spark_results = property_use_analysis.toPandas()

            logger.info(f"Spark analysis completed for {len(spark_results)} property types")
            return {"spark_analysis": spark_results.to_dict('records')}

        except Exception as e:
            logger.error(f"Error in Spark analysis: {e}")
            return {}

    def create_category_mappings(self, property_uses_df: pd.DataFrame) -> Dict[str, CategoryMapping]:
        """Create comprehensive mapping of property uses to categories"""

        # Define mapping rules based on common property use patterns
        mapping_rules = {
            "Residential": [
                "SINGLE FAMILY", "CONDO", "MOBILE", "TOWNHOUSE", "DUPLEX",
                "APARTMENT", "RESIDENTIAL", "HOME", "HOUSE", "DWELLING"
            ],
            "Commercial": [
                "RETAIL", "OFFICE", "STORE", "SHOPPING", "COMMERCIAL", "BUSINESS",
                "RESTAURANT", "HOTEL", "MOTEL", "WAREHOUSE", "PARKING"
            ],
            "Industrial": [
                "INDUSTRIAL", "MANUFACTURING", "FACTORY", "PLANT", "DISTRIBUTION",
                "PROCESSING", "PRODUCTION", "UTILITY"
            ],
            "Agricultural": [
                "AGRICULTURAL", "FARM", "RANCH", "GROVE", "PASTURE", "CROP",
                "LIVESTOCK", "DAIRY", "POULTRY", "TIMBER"
            ],
            "Vacant Land": [
                "VACANT", "UNDEVELOPED", "RAW LAND", "IMPROVED VACANT",
                "ACREAGE", "LOT"
            ],
            "Government": [
                "GOVERNMENT", "PUBLIC", "MUNICIPAL", "COUNTY", "STATE", "FEDERAL",
                "SCHOOL", "LIBRARY", "FIRE", "POLICE"
            ],
            "Conservation": [
                "CONSERVATION", "PRESERVE", "ENVIRONMENTAL", "WETLAND",
                "NATURAL", "PARK", "RECREATION"
            ],
            "Religious": [
                "CHURCH", "RELIGIOUS", "TEMPLE", "MOSQUE", "SYNAGOGUE",
                "MONASTERY", "CONVENT"
            ],
            "Infrastructure": [
                "ROAD", "BRIDGE", "CANAL", "DRAINAGE", "RIGHT OF WAY",
                "EASEMENT", "RAILROAD"
            ],
            "Special Use": [
                "CEMETERY", "HOSPITAL", "NURSING", "AIRPORT", "MARINA",
                "GOLF", "CLUB", "STADIUM"
            ]
        }

        # Initialize category mappings
        category_mappings = {}
        unmatched_uses = []

        for category, keywords in mapping_rules.items():
            matched_uses = []
            total_count = 0

            for _, row in property_uses_df.iterrows():
                use = str(row['property_use']).upper()
                if any(keyword in use for keyword in keywords):
                    matched_uses.append(row['property_use'])
                    total_count += row['count']

            if matched_uses:
                percentage = (total_count / property_uses_df['count'].sum()) * 100
                category_mappings[category] = CategoryMapping(
                    category=category,
                    use_codes=matched_uses,
                    count=total_count,
                    percentage=percentage
                )

        # Find unmatched property uses
        all_matched = set()
        for mapping in category_mappings.values():
            all_matched.update(mapping.use_codes)

        for _, row in property_uses_df.iterrows():
            if row['property_use'] not in all_matched:
                unmatched_uses.append({
                    'property_use': row['property_use'],
                    'count': row['count'],
                    'percentage': row['percentage']
                })

        logger.info(f"Mapped {len(all_matched)} property uses to {len(category_mappings)} categories")
        logger.info(f"Found {len(unmatched_uses)} unmatched property uses")

        return category_mappings, unmatched_uses

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        logger.info("Starting comprehensive property use analysis...")

        # Query unique property uses
        property_uses_df = self.query_unique_property_uses()

        # Query DOR codes
        dor_codes_df = self.query_dor_use_codes()

        # PySpark analysis
        spark_results = self.analyze_with_pyspark()

        # Create category mappings
        category_mappings, unmatched_uses = self.create_category_mappings(property_uses_df)

        # Calculate statistics
        total_properties = property_uses_df['count'].sum()
        unique_uses = len(property_uses_df)

        # Prepare comprehensive report
        report = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_properties": int(total_properties),
                "unique_property_uses": unique_uses,
                "analysis_method": "SQLAlchemy + PySpark" if PYSPARK_AVAILABLE else "SQLAlchemy only"
            },
            "property_uses": property_uses_df.to_dict('records'),
            "dor_codes": dor_codes_df.to_dict('records') if not dor_codes_df.empty else [],
            "category_mappings": {k: asdict(v) for k, v in category_mappings.items()},
            "unmatched_uses": unmatched_uses,
            "current_filter_categories": self.current_categories,
            "spark_analysis": spark_results,
            "recommendations": self._generate_recommendations(category_mappings, unmatched_uses)
        }

        logger.info("Comprehensive analysis completed")
        return report

    def _generate_recommendations(self, category_mappings: Dict[str, CategoryMapping],
                                unmatched_uses: List[Dict]) -> Dict[str, Any]:
        """Generate recommendations for filter improvements"""
        recommendations = {
            "missing_categories": [],
            "filter_updates": [],
            "new_filter_suggestions": []
        }

        # Analyze unmatched uses for new categories
        high_volume_unmatched = [
            use for use in unmatched_uses
            if use['count'] > 1000  # Properties with >1000 occurrences
        ]

        if high_volume_unmatched:
            recommendations["missing_categories"] = high_volume_unmatched

        # Suggest filter updates
        for category, mapping in category_mappings.items():
            if category not in self.current_categories:
                recommendations["new_filter_suggestions"].append({
                    "category": category,
                    "count": mapping.count,
                    "percentage": mapping.percentage,
                    "justification": f"Represents {mapping.percentage:.2f}% of all properties"
                })

        return recommendations

    def save_results(self, report: Dict[str, Any]):
        """Save analysis results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save main report
        report_file = f"comprehensive_property_use_analysis_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        # Save CSV exports
        if report['property_uses']:
            df = pd.DataFrame(report['property_uses'])
            df.to_csv(f"property_uses_analysis_{timestamp}.csv", index=False)

        logger.info(f"Results saved to {report_file}")
        return report_file

# FastAPI Application
app = FastAPI(title="Property Use Analyzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = PropertyUseAnalyzer()

class AnalysisRequest(BaseModel):
    include_spark: bool = True
    county_filter: Optional[str] = None
    min_count: int = 1

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    analyzer.initialize_connections()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/analyze/property-uses")
async def analyze_property_uses(
    include_spark: bool = Query(True, description="Include PySpark analysis"),
    county_filter: Optional[str] = Query(None, description="Filter by specific county"),
    min_count: int = Query(1, description="Minimum property count threshold")
):
    """Analyze all property uses in the database"""
    try:
        report = analyzer.generate_comprehensive_report()

        # Apply filters if specified
        if county_filter:
            # Filter results by county
            filtered_uses = []
            for use in report['property_uses']:
                if county_filter.upper() in [c.upper() for c in use.get('counties', [])]:
                    filtered_uses.append(use)
            report['property_uses'] = filtered_uses

        if min_count > 1:
            # Filter by minimum count
            report['property_uses'] = [
                use for use in report['property_uses']
                if use['count'] >= min_count
            ]

        return report

    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories/current")
async def get_current_categories():
    """Get current filter categories"""
    return {"categories": analyzer.current_categories}

@app.get("/categories/mapping")
async def get_category_mapping():
    """Get property use to category mapping"""
    try:
        property_uses_df = analyzer.query_unique_property_uses()
        category_mappings, unmatched_uses = analyzer.create_category_mappings(property_uses_df)

        return {
            "mappings": {k: asdict(v) for k, v in category_mappings.items()},
            "unmatched": unmatched_uses
        }
    except Exception as e:
        logger.error(f"Error getting category mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Main execution function"""
    analyzer = PropertyUseAnalyzer()
    analyzer.initialize_connections()

    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report()

    # Save results
    report_file = analyzer.save_results(report)

    print(f"\n{'='*60}")
    print("COMPREHENSIVE PROPERTY USE ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Total Properties Analyzed: {report['analysis_metadata']['total_properties']:,}")
    print(f"Unique Property Uses Found: {report['analysis_metadata']['unique_property_uses']:,}")
    print(f"Report saved to: {report_file}")
    print(f"{'='*60}\n")

    # Print top 20 property uses
    print("TOP 20 PROPERTY USES:")
    print("-" * 40)
    for i, use in enumerate(report['property_uses'][:20], 1):
        print(f"{i:2d}. {use['property_use']:<30} {use['count']:>8,} ({use['percentage']:>6.2f}%)")

    return report

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "api":
        # Run FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # Run analysis
        main()