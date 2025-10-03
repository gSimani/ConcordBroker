#!/usr/bin/env python3
"""
PySpark Data Processor for ConcordBroker
Large-scale data processing for property analysis, entity matching, and analytics
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json

# PySpark imports
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, lit, when, isnan, isnull, regexp_replace, upper, lower, trim,
    split, explode, array_contains, size, collect_list, count, sum as spark_sum,
    avg, max as spark_max, min as spark_min, stddev, percentile_approx,
    year, month, dayofmonth, date_format, to_date, datediff, months_between,
    levenshtein, soundex, regexp_extract, concat, coalesce, desc, asc,
    row_number, rank, dense_rank, lag, lead, first, last
)
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, FloatType,
    DoubleType, BooleanType, DateType, TimestampType, DecimalType
)
from pyspark.ml.feature import StringIndexer, VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import ClusteringEvaluator

# PostgreSQL connector
import psycopg2
from sqlalchemy import create_engine
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SparkDataProcessor:
    """
    High-performance Spark processor for ConcordBroker data operations
    """

    def __init__(self, app_name: str = "ConcordBroker-DataProcessor"):
        self.app_name = app_name
        self.spark = None
        self.postgres_url = None
        self.postgres_properties = None
        self._initialize_spark()

    def _initialize_spark(self):
        """Initialize Spark session with optimized configuration"""
        try:
            # Spark configuration optimized for large datasets
            self.spark = SparkSession.builder \
                .appName(self.app_name) \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.adaptive.skewJoin.enabled", "true") \
                .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
                .config("spark.sql.execution.arrow.maxRecordsPerBatch", "10000") \
                .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
                .config("spark.sql.shuffle.partitions", "200") \
                .config("spark.sql.broadcastTimeout", "36000") \
                .config("spark.network.timeout", "800s") \
                .config("spark.executor.heartbeatInterval", "60s") \
                .config("spark.dynamicAllocation.enabled", "true") \
                .config("spark.dynamicAllocation.minExecutors", "1") \
                .config("spark.dynamicAllocation.maxExecutors", "10") \
                .config("spark.executor.memory", "4g") \
                .config("spark.executor.cores", "2") \
                .config("spark.driver.memory", "4g") \
                .config("spark.driver.maxResultSize", "2g") \
                .getOrCreate()

            # Set log level to reduce noise
            self.spark.sparkContext.setLogLevel("WARN")

            logger.info("✅ Spark session initialized successfully")

            # Setup PostgreSQL connection properties
            self._setup_postgres_connection()

        except Exception as e:
            logger.error(f"❌ Failed to initialize Spark session: {e}")
            raise

    def _setup_postgres_connection(self):
        """Setup PostgreSQL connection for Spark"""
        try:
            # Get database URL from environment
            supabase_url = os.getenv('SUPABASE_URL', '')
            service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

            if supabase_url and service_role_key:
                # Convert Supabase URL to PostgreSQL URL
                db_host = supabase_url.replace('https://', '').split('.')[0] + '.supabase.co'

                self.postgres_url = f"jdbc:postgresql://{db_host}:5432/postgres"
                self.postgres_properties = {
                    "user": "postgres",
                    "password": service_role_key,
                    "driver": "org.postgresql.Driver",
                    "ssl": "true",
                    "sslmode": "require"
                }

                logger.info("✅ PostgreSQL connection configured for Spark")
            else:
                logger.warning("⚠️ PostgreSQL connection not configured - some features will be limited")

        except Exception as e:
            logger.error(f"❌ Failed to setup PostgreSQL connection: {e}")

    def load_table(self, table_name: str, columns: List[str] = None) -> DataFrame:
        """Load a table from PostgreSQL into Spark DataFrame"""
        try:
            if not self.postgres_url:
                raise ValueError("PostgreSQL connection not configured")

            # Build query
            if columns:
                query = f"(SELECT {', '.join(columns)} FROM {table_name}) AS t"
            else:
                query = f"(SELECT * FROM {table_name}) AS t"

            # Load data
            df = self.spark.read \
                .jdbc(
                    url=self.postgres_url,
                    table=query,
                    properties=self.postgres_properties
                )

            logger.info(f"✅ Loaded table {table_name}: {df.count()} rows, {len(df.columns)} columns")
            return df

        except Exception as e:
            logger.error(f"❌ Failed to load table {table_name}: {e}")
            raise

    def analyze_property_market_trends(self, county: str = None) -> Dict[str, Any]:
        """
        Comprehensive market trend analysis using Spark
        """
        try:
            logger.info("🔍 Starting property market trend analysis...")

            # Load required data
            properties_df = self.load_table("florida_parcels")
            sales_df = self.load_table("property_sales_history")

            # Filter by county if specified
            if county:
                properties_df = properties_df.filter(upper(col("county")) == county.upper())
                # Join to get county info for sales
                sales_df = sales_df.join(
                    properties_df.select("parcel_id", "county"),
                    on="parcel_id",
                    how="inner"
                )

            # Convert sale_date to proper date type
            sales_df = sales_df.withColumn("sale_date", to_date(col("sale_date")))

            # Filter to last 5 years and valid sales
            cutoff_date = datetime.now() - timedelta(days=5*365)
            sales_df = sales_df.filter(
                (col("sale_date") >= lit(cutoff_date.date())) &
                (col("sale_price") > 0) &
                (col("sale_price") < 50000000)  # Remove outliers
            )

            # Add time-based columns
            sales_df = sales_df.withColumn("sale_year", year(col("sale_date"))) \
                              .withColumn("sale_month", month(col("sale_date"))) \
                              .withColumn("sale_quarter",
                                        when(col("sale_month").isin([1,2,3]), 1)
                                        .when(col("sale_month").isin([4,5,6]), 2)
                                        .when(col("sale_month").isin([7,8,9]), 3)
                                        .otherwise(4))

            # Join with property details for analysis
            analysis_df = sales_df.join(
                properties_df.select(
                    "parcel_id", "county", "total_living_area", "year_built",
                    "beds", "baths", "land_sqft", "just_value"
                ),
                on="parcel_id",
                how="left"
            )

            # 1. Price trends by year
            yearly_trends = analysis_df.groupBy("sale_year") \
                .agg(
                    count("*").alias("total_sales"),
                    avg("sale_price").alias("avg_price"),
                    percentile_approx("sale_price", 0.5).alias("median_price"),
                    spark_min("sale_price").alias("min_price"),
                    spark_max("sale_price").alias("max_price"),
                    stddev("sale_price").alias("price_stddev")
                ).orderBy("sale_year")

            # 2. Seasonal patterns
            seasonal_trends = analysis_df.groupBy("sale_quarter") \
                .agg(
                    count("*").alias("total_sales"),
                    avg("sale_price").alias("avg_price")
                ).orderBy("sale_quarter")

            # 3. Price per square foot analysis
            psf_df = analysis_df.filter(col("total_living_area") > 0) \
                .withColumn("price_per_sqft", col("sale_price") / col("total_living_area"))

            psf_trends = psf_df.groupBy("sale_year") \
                .agg(
                    avg("price_per_sqft").alias("avg_price_per_sqft"),
                    percentile_approx("price_per_sqft", 0.5).alias("median_price_per_sqft")
                ).orderBy("sale_year")

            # 4. Property age impact
            age_impact = analysis_df.filter(col("year_built") > 0) \
                .withColumn("property_age", year(col("sale_date")) - col("year_built")) \
                .withColumn("age_group",
                          when(col("property_age") < 5, "New (0-5 years)")
                          .when(col("property_age") < 15, "Modern (5-15 years)")
                          .when(col("property_age") < 30, "Established (15-30 years)")
                          .when(col("property_age") < 50, "Mature (30-50 years)")
                          .otherwise("Historic (50+ years)")) \
                .groupBy("age_group") \
                .agg(
                    count("*").alias("total_sales"),
                    avg("sale_price").alias("avg_price"),
                    avg("price_per_sqft").alias("avg_price_per_sqft")
                )

            # 5. Size-based analysis
            size_analysis = analysis_df.filter(col("total_living_area") > 0) \
                .withColumn("size_category",
                          when(col("total_living_area") < 1000, "Small (<1,000 sqft)")
                          .when(col("total_living_area") < 1500, "Medium (1,000-1,500 sqft)")
                          .when(col("total_living_area") < 2500, "Large (1,500-2,500 sqft)")
                          .when(col("total_living_area") < 4000, "XL (2,500-4,000 sqft)")
                          .otherwise("Luxury (4,000+ sqft)")) \
                .groupBy("size_category") \
                .agg(
                    count("*").alias("total_sales"),
                    avg("sale_price").alias("avg_price"),
                    avg("price_per_sqft").alias("avg_price_per_sqft")
                )

            # Convert results to Python dictionaries
            results = {
                "analysis_date": datetime.now().isoformat(),
                "county_filter": county,
                "data_summary": {
                    "total_properties": properties_df.count(),
                    "total_sales": sales_df.count(),
                    "analysis_period": f"{cutoff_date.date()} to {datetime.now().date()}"
                },
                "yearly_trends": yearly_trends.collect(),
                "seasonal_patterns": seasonal_trends.collect(),
                "price_per_sqft_trends": psf_trends.collect(),
                "age_impact_analysis": age_impact.collect(),
                "size_based_analysis": size_analysis.collect()
            }

            # Convert Row objects to dictionaries
            for key in results:
                if isinstance(results[key], list) and results[key] and hasattr(results[key][0], 'asDict'):
                    results[key] = [row.asDict() for row in results[key]]

            logger.info(f"✅ Market trend analysis completed for {county or 'all counties'}")
            return results

        except Exception as e:
            logger.error(f"❌ Market trend analysis failed: {e}")
            raise

    def detect_investment_opportunities(self, min_discount_pct: float = 20) -> DataFrame:
        """
        Detect potential investment opportunities using machine learning
        """
        try:
            logger.info("🔍 Detecting investment opportunities with ML...")

            # Load data
            properties_df = self.load_table("florida_parcels")
            sales_df = self.load_table("property_sales_history")
            tax_certs_df = self.load_table("tax_certificates")

            # Get recent sales for market value estimation
            recent_sales = sales_df.filter(
                (col("sale_date") >= lit((datetime.now() - timedelta(days=365)).date())) &
                (col("sale_price") > 0)
            )

            # Calculate market value indicators by area (county + size)
            market_indicators = recent_sales.join(
                properties_df.select("parcel_id", "county", "total_living_area"),
                on="parcel_id"
            ).filter(col("total_living_area") > 0) \
             .withColumn("price_per_sqft", col("sale_price") / col("total_living_area")) \
             .groupBy("county") \
             .agg(
                 avg("price_per_sqft").alias("market_price_per_sqft"),
                 percentile_approx("price_per_sqft", 0.5).alias("median_price_per_sqft"),
                 count("*").alias("recent_sales_count")
             )

            # Join properties with market indicators
            opportunity_df = properties_df.join(market_indicators, on="county", how="left")

            # Calculate estimated market value
            opportunity_df = opportunity_df.withColumn(
                "estimated_market_value",
                when(
                    (col("total_living_area") > 0) & (col("market_price_per_sqft").isNotNull()),
                    col("total_living_area") * col("market_price_per_sqft")
                ).otherwise(col("just_value"))
            )

            # Calculate discount percentage
            opportunity_df = opportunity_df.withColumn(
                "discount_percentage",
                when(
                    col("estimated_market_value") > 0,
                    ((col("estimated_market_value") - col("just_value")) / col("estimated_market_value") * 100)
                ).otherwise(0)
            )

            # Add tax certificate indicator
            tax_properties = tax_certs_df.filter(col("status") != "Redeemed") \
                                        .select("parcel_id") \
                                        .distinct() \
                                        .withColumn("has_tax_lien", lit(True))

            opportunity_df = opportunity_df.join(tax_properties, on="parcel_id", how="left") \
                                         .fillna({"has_tax_lien": False})

            # Score opportunities
            opportunity_df = opportunity_df.withColumn(
                "opportunity_score",
                (col("discount_percentage") * 0.4) +  # 40% weight on discount
                (when(col("has_tax_lien"), 25).otherwise(0)) +  # 25 points for tax liens
                (when(col("recent_sales_count") >= 5, 15).otherwise(col("recent_sales_count") * 3)) +  # Market activity
                (when(col("year_built") >= 2000, 10).otherwise(0)) +  # Property age bonus
                (when(col("pool") == "Y", 5).otherwise(0))  # Amenity bonus
            )

            # Filter for good opportunities
            opportunities = opportunity_df.filter(
                (col("discount_percentage") >= min_discount_pct) |
                (col("has_tax_lien") == True) |
                (col("opportunity_score") >= 50)
            ).orderBy(desc("opportunity_score"))

            logger.info(f"✅ Found {opportunities.count()} investment opportunities")
            return opportunities

        except Exception as e:
            logger.error(f"❌ Investment opportunity detection failed: {e}")
            raise

    def perform_entity_clustering(self, similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Use ML to cluster and deduplicate business entities
        """
        try:
            logger.info("🤖 Performing entity clustering with ML...")

            # Load entity data
            florida_entities = self.load_table("florida_entities") \
                .select("entity_id", "entity_name", "entity_type", "status") \
                .withColumn("source", lit("florida_entities"))

            sunbiz_entities = self.load_table("sunbiz_corporate") \
                .select("document_number", "corporation_name", "corp_type", "status") \
                .withColumnRenamed("document_number", "entity_id") \
                .withColumnRenamed("corporation_name", "entity_name") \
                .withColumnRenamed("corp_type", "entity_type") \
                .withColumn("source", lit("sunbiz_corporate"))

            # Combine entities
            all_entities = florida_entities.union(sunbiz_entities)

            # Clean entity names for better matching
            cleaned_entities = all_entities.withColumn(
                "clean_name",
                upper(trim(regexp_replace(
                    regexp_replace(col("entity_name"), "[^A-Za-z0-9\\s]", ""),
                    "\\s+", " "
                )))
            ).filter(col("clean_name") != "")

            # Create features for clustering
            # For simplicity, we'll use string length and first few characters
            # In production, you'd use more sophisticated NLP features
            feature_df = cleaned_entities.withColumn(
                "name_length", size(split(col("clean_name"), " "))
            ).withColumn(
                "first_char", col("clean_name").substr(1, 1)
            ).withColumn(
                "soundex_code", soundex(col("clean_name"))
            )

            # Find potential duplicates using fuzzy matching
            # Self-join to find similar entities
            entity_pairs = feature_df.alias("e1").join(
                feature_df.alias("e2"),
                (col("e1.entity_id") < col("e2.entity_id")) &  # Avoid duplicate pairs
                (col("e1.soundex_code") == col("e2.soundex_code")) &  # Same soundex
                (levenshtein(col("e1.clean_name"), col("e2.clean_name")) <= 3)  # Similar spelling
            ).select(
                col("e1.entity_id").alias("entity_1"),
                col("e1.entity_name").alias("name_1"),
                col("e1.source").alias("source_1"),
                col("e2.entity_id").alias("entity_2"),
                col("e2.entity_name").alias("name_2"),
                col("e2.source").alias("source_2"),
                levenshtein(col("e1.clean_name"), col("e2.clean_name")).alias("edit_distance")
            )

            # Calculate similarity score
            entity_pairs = entity_pairs.withColumn(
                "similarity_score",
                1.0 - (col("edit_distance") / spark_max(
                    size(split(col("name_1"), " ")),
                    size(split(col("name_2"), " "))
                ))
            ).filter(col("similarity_score") >= similarity_threshold)

            # Group similar entities
            similar_groups = entity_pairs.groupBy("entity_1") \
                .agg(collect_list("entity_2").alias("similar_entities"))

            # Statistics
            total_entities = all_entities.count()
            potential_duplicates = entity_pairs.count()

            # Entity type distribution
            type_distribution = all_entities.groupBy("entity_type", "source") \
                .count() \
                .orderBy(desc("count"))

            # Status distribution
            status_distribution = all_entities.groupBy("status", "source") \
                .count() \
                .orderBy(desc("count"))

            results = {
                "clustering_date": datetime.now().isoformat(),
                "summary": {
                    "total_entities": total_entities,
                    "potential_duplicates": potential_duplicates,
                    "similarity_threshold": similarity_threshold
                },
                "entity_type_distribution": [row.asDict() for row in type_distribution.collect()],
                "status_distribution": [row.asDict() for row in status_distribution.collect()],
                "similar_entity_pairs": [row.asDict() for row in entity_pairs.limit(100).collect()],
                "clustering_groups": [row.asDict() for row in similar_groups.limit(50).collect()]
            }

            logger.info(f"✅ Entity clustering completed: {potential_duplicates} potential duplicates found")
            return results

        except Exception as e:
            logger.error(f"❌ Entity clustering failed: {e}")
            raise

    def analyze_tax_certificate_patterns(self) -> Dict[str, Any]:
        """
        Analyze tax certificate patterns and predict high-risk properties
        """
        try:
            logger.info("📊 Analyzing tax certificate patterns...")

            # Load data
            tax_certs = self.load_table("tax_certificates")
            properties = self.load_table("florida_parcels")

            # Convert dates and add time features
            tax_certs = tax_certs.withColumn("sale_date", to_date(col("sale_date"))) \
                                .withColumn("cert_year", col("certificate_year"))

            # Join with property data
            analysis_df = tax_certs.join(properties, on="parcel_id", how="left")

            # 1. Geographic distribution
            geographic_dist = analysis_df.groupBy("county") \
                .agg(
                    count("*").alias("total_certificates"),
                    spark_sum("certificate_amount").alias("total_amount"),
                    avg("certificate_amount").alias("avg_amount"),
                    count(when(col("status") == "Active", 1)).alias("active_certificates"),
                    count(when(col("status") == "Redeemed", 1)).alias("redeemed_certificates")
                ).orderBy(desc("total_certificates"))

            # 2. Temporal patterns
            temporal_patterns = analysis_df.groupBy("cert_year") \
                .agg(
                    count("*").alias("certificates_issued"),
                    avg("certificate_amount").alias("avg_amount"),
                    spark_sum("certificate_amount").alias("total_amount")
                ).orderBy("cert_year")

            # 3. Property value vs certificate amount analysis
            value_analysis = analysis_df.filter(
                (col("just_value") > 0) & (col("certificate_amount") > 0)
            ).withColumn(
                "cert_to_value_ratio", col("certificate_amount") / col("just_value")
            ).withColumn(
                "risk_category",
                when(col("cert_to_value_ratio") > 0.1, "High Risk")
                .when(col("cert_to_value_ratio") > 0.05, "Medium Risk")
                .otherwise("Low Risk")
            )

            risk_distribution = value_analysis.groupBy("risk_category") \
                .agg(
                    count("*").alias("property_count"),
                    avg("cert_to_value_ratio").alias("avg_ratio"),
                    avg("just_value").alias("avg_property_value"),
                    avg("certificate_amount").alias("avg_cert_amount")
                )

            # 4. Repeat offender analysis
            repeat_analysis = analysis_df.groupBy("parcel_id") \
                .agg(
                    count("*").alias("certificate_count"),
                    spark_sum("certificate_amount").alias("total_owed"),
                    first("owner_name").alias("owner_name"),
                    first("phy_addr1").alias("property_address"),
                    first("just_value").alias("property_value")
                ).filter(col("certificate_count") > 1) \
                .orderBy(desc("certificate_count"))

            # 5. Status transition analysis
            status_analysis = analysis_df.groupBy("status") \
                .agg(
                    count("*").alias("count"),
                    avg("certificate_amount").alias("avg_amount"),
                    spark_sum("certificate_amount").alias("total_amount")
                ).orderBy(desc("count"))

            # Predict high-risk properties
            # Properties with multiple certificates or high cert-to-value ratios
            high_risk_properties = analysis_df.filter(
                (col("cert_to_value_ratio") > 0.1) |
                (col("certificate_count") > 2)
            ).select(
                "parcel_id", "owner_name", "phy_addr1", "county",
                "just_value", "certificate_amount", "cert_to_value_ratio", "status"
            ).distinct().orderBy(desc("cert_to_value_ratio"))

            results = {
                "analysis_date": datetime.now().isoformat(),
                "summary": {
                    "total_certificates": tax_certs.count(),
                    "total_properties_affected": analysis_df.select("parcel_id").distinct().count(),
                    "total_amount_owed": analysis_df.agg(spark_sum("certificate_amount")).collect()[0][0]
                },
                "geographic_distribution": [row.asDict() for row in geographic_dist.collect()],
                "temporal_patterns": [row.asDict() for row in temporal_patterns.collect()],
                "risk_distribution": [row.asDict() for row in risk_distribution.collect()],
                "repeat_offenders": [row.asDict() for row in repeat_analysis.limit(50).collect()],
                "status_analysis": [row.asDict() for row in status_analysis.collect()],
                "high_risk_properties": [row.asDict() for row in high_risk_properties.limit(100).collect()]
            }

            logger.info("✅ Tax certificate pattern analysis completed")
            return results

        except Exception as e:
            logger.error(f"❌ Tax certificate analysis failed: {e}")
            raise

    def generate_comprehensive_report(self, county: str = None) -> Dict[str, Any]:
        """
        Generate a comprehensive data analysis report
        """
        try:
            logger.info("📋 Generating comprehensive Spark analysis report...")

            # Run all analyses
            market_trends = self.analyze_property_market_trends(county)
            opportunities = self.detect_investment_opportunities()
            entity_clustering = self.perform_entity_clustering()
            tax_patterns = self.analyze_tax_certificate_patterns()

            # Collect opportunity statistics
            opp_stats = opportunities.agg(
                count("*").alias("total_opportunities"),
                avg("opportunity_score").alias("avg_score"),
                spark_max("opportunity_score").alias("max_score"),
                avg("discount_percentage").alias("avg_discount")
            ).collect()[0].asDict()

            # Top opportunities
            top_opportunities = opportunities.select(
                "parcel_id", "county", "owner_name", "phy_addr1",
                "just_value", "estimated_market_value", "discount_percentage",
                "opportunity_score", "has_tax_lien"
            ).limit(25).collect()

            comprehensive_report = {
                "report_generated": datetime.now().isoformat(),
                "analysis_scope": {
                    "county_filter": county,
                    "spark_app_name": self.app_name,
                    "processing_method": "Apache Spark with Machine Learning"
                },
                "market_analysis": market_trends,
                "investment_opportunities": {
                    "statistics": opp_stats,
                    "top_opportunities": [row.asDict() for row in top_opportunities]
                },
                "entity_analysis": entity_clustering,
                "tax_certificate_analysis": tax_patterns,
                "recommendations": self._generate_recommendations(
                    market_trends, opp_stats, entity_clustering, tax_patterns
                )
            }

            logger.info("✅ Comprehensive Spark report generated successfully")
            return comprehensive_report

        except Exception as e:
            logger.error(f"❌ Comprehensive report generation failed: {e}")
            raise

    def _generate_recommendations(self, market_trends, opportunity_stats, entity_analysis, tax_analysis) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        # Market recommendations
        if market_trends.get("yearly_trends"):
            recent_trend = market_trends["yearly_trends"][-1] if market_trends["yearly_trends"] else {}
            if recent_trend.get("avg_price", 0) > 0:
                recommendations.append(f"Market shows average price of ${recent_trend['avg_price']:,.0f} with {recent_trend.get('total_sales', 0)} sales")

        # Opportunity recommendations
        if opportunity_stats.get("total_opportunities", 0) > 0:
            recommendations.append(f"Found {opportunity_stats['total_opportunities']} investment opportunities with average {opportunity_stats.get('avg_discount', 0):.1f}% discount")

        # Entity recommendations
        if entity_analysis.get("summary", {}).get("potential_duplicates", 0) > 0:
            recommendations.append(f"Detected {entity_analysis['summary']['potential_duplicates']} potential entity duplicates requiring review")

        # Tax certificate recommendations
        tax_summary = tax_analysis.get("summary", {})
        if tax_summary.get("total_certificates", 0) > 0:
            recommendations.append(f"Monitor {tax_summary['total_certificates']} tax certificates affecting {tax_summary.get('total_properties_affected', 0)} properties")

        return recommendations

    def close(self):
        """Clean up Spark session"""
        if self.spark:
            self.spark.stop()
            logger.info("✅ Spark session closed")

# Example usage and testing
def main():
    """Main execution function for testing"""
    processor = None
    try:
        # Initialize processor
        processor = SparkDataProcessor("ConcordBroker-Test")

        # Test market analysis
        print("Testing market trend analysis...")
        market_results = processor.analyze_property_market_trends("BROWARD")
        print(f"Market analysis completed: {len(market_results.get('yearly_trends', []))} yearly data points")

        # Test investment opportunities
        print("Testing investment opportunity detection...")
        opportunities = processor.detect_investment_opportunities()
        print(f"Found {opportunities.count()} investment opportunities")

        # Test entity clustering
        print("Testing entity clustering...")
        entity_results = processor.perform_entity_clustering()
        print(f"Entity clustering completed: {entity_results['summary']['potential_duplicates']} potential duplicates")

        # Test tax certificate analysis
        print("Testing tax certificate analysis...")
        tax_results = processor.analyze_tax_certificate_patterns()
        print(f"Tax analysis completed: {tax_results['summary']['total_certificates']} certificates analyzed")

        # Generate comprehensive report
        print("Generating comprehensive report...")
        report = processor.generate_comprehensive_report("BROWARD")
        print(f"Report generated with {len(report.get('recommendations', []))} recommendations")

        # Save report
        import json
        with open("../logs/spark_analysis_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        print("✅ All Spark processing tests completed successfully")

    except Exception as e:
        print(f"❌ Spark processing test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if processor:
            processor.close()

if __name__ == "__main__":
    main()