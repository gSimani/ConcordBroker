"""
PySpark Big Data Processing Pipeline for Field Mapping and Verification
Processes Property Appraiser and Sunbiz data at scale with complete field mapping validation
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import pyspark.sql.functions as F
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.stat import Correlation
import json
import asyncio
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging
import numpy as np
from pathlib import Path
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PySparkFieldMappingProcessor:
    """
    Big data processor for field mapping verification using PySpark
    Handles millions of property records with distributed computing
    """

    def __init__(self):
        # Initialize Spark Session with optimized configuration
        self.spark = SparkSession.builder \
            .appName("ConcordBroker_FieldMapping_Processor") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.adaptive.skewJoin.enabled", "true") \
            .config("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5") \
            .config("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .config("spark.sql.execution.arrow.maxRecordsPerBatch", "10000") \
            .config("spark.driver.memory", "8g") \
            .config("spark.executor.memory", "8g") \
            .config("spark.executor.cores", "4") \
            .config("spark.sql.shuffle.partitions", "200") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.databricks.delta.retentionDurationCheck.enabled", "false") \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .config("spark.kryoserializer.buffer.max", "1024m") \
            .getOrCreate()

        # Set log level
        self.spark.sparkContext.setLogLevel("WARN")

        # Load field mapping configuration
        self.field_mappings = self._load_field_mappings()

        # Database connection parameters
        self.db_config = {
            "url": "jdbc:postgresql://aws-0-us-east-1.pooler.supabase.com:6543/postgres",
            "properties": {
                "user": "postgres.pmispwtdngkcmsrsjwbp",
                "password": "vM4g2024$$Florida1",
                "driver": "org.postgresql.Driver",
                "fetchsize": "10000",
                "batchsize": "10000"
            }
        }

        # Initialize field validation rules
        self.validation_rules = self._initialize_validation_rules()

    def _load_field_mappings(self) -> Dict:
        """Load field mapping configuration"""
        config_path = Path('field_mapping_configuration.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning("Field mapping configuration not found, using defaults")
            return self._get_default_mappings()

    def _get_default_mappings(self) -> Dict:
        """Get default field mappings"""
        return {
            "property_appraiser": {
                "florida_parcels": {
                    "parcel_id": {"ui_field": "parcel-number", "tab": "overview", "required": True},
                    "phy_addr1": {"ui_field": "property-address", "tab": "overview", "required": True},
                    "phy_city": {"ui_field": "property-city", "tab": "overview", "required": True},
                    "phy_zipcd": {"ui_field": "property-zip", "tab": "overview", "required": False},
                    "owner_name": {"ui_field": "owner-name", "tab": "owner", "required": True},
                    "jv": {"ui_field": "just-value", "tab": "valuation", "required": True},
                    "av_sd": {"ui_field": "assessed-value", "tab": "valuation", "required": True},
                    "tv_sd": {"ui_field": "taxable-value", "tab": "valuation", "required": True},
                    "yr_blt": {"ui_field": "year-built", "tab": "core-property", "required": False},
                    "tot_lvg_area": {"ui_field": "living-area", "tab": "building", "required": False},
                    "bedroom_cnt": {"ui_field": "bedrooms", "tab": "building", "required": False},
                    "bathroom_cnt": {"ui_field": "bathrooms", "tab": "building", "required": False},
                    "lnd_sqfoot": {"ui_field": "land-sqft", "tab": "land", "required": False},
                    "sale_prc1": {"ui_field": "last-sale-price", "tab": "sales", "required": False},
                    "sale_yr1": {"ui_field": "last-sale-year", "tab": "sales", "required": False}
                }
            },
            "sunbiz": {
                "sunbiz_corporations": {
                    "corp_name": {"ui_field": "corporation-name", "tab": "sunbiz", "required": True},
                    "corp_number": {"ui_field": "corporation-number", "tab": "sunbiz", "required": True},
                    "status": {"ui_field": "corp-status", "tab": "sunbiz", "required": True},
                    "filing_date": {"ui_field": "filing-date", "tab": "sunbiz", "required": False}
                }
            }
        }

    def _initialize_validation_rules(self) -> Dict:
        """Initialize validation rules for data quality"""
        return {
            "numeric_fields": {
                "jv": {"min": 0, "max": 100000000},
                "av_sd": {"min": 0, "max": 100000000},
                "tv_sd": {"min": 0, "max": 100000000},
                "yr_blt": {"min": 1800, "max": datetime.now().year},
                "tot_lvg_area": {"min": 0, "max": 100000},
                "bedroom_cnt": {"min": 0, "max": 20},
                "bathroom_cnt": {"min": 0, "max": 20},
                "lnd_sqfoot": {"min": 0, "max": 10000000}
            },
            "string_fields": {
                "phy_zipcd": r"^\d{5}(-\d{4})?$",
                "owner_state": r"^[A-Z]{2}$",
                "dor_uc": r"^\d{4}$"
            },
            "required_fields": [
                "parcel_id", "phy_addr1", "phy_city", "owner_name", "jv"
            ]
        }

    def load_property_appraiser_data(self) -> DataFrame:
        """
        Load Property Appraiser data from Supabase using PySpark
        Handles 9.7M Florida property records efficiently
        """
        logger.info("Loading Property Appraiser data with PySpark...")

        # Load main parcels data
        florida_parcels_df = self.spark.read \
            .format("jdbc") \
            .option("url", self.db_config["url"]) \
            .option("dbtable", "florida_parcels") \
            .option("user", self.db_config["properties"]["user"]) \
            .option("password", self.db_config["properties"]["password"]) \
            .option("driver", self.db_config["properties"]["driver"]) \
            .option("fetchsize", self.db_config["properties"]["fetchsize"]) \
            .option("partitionColumn", "id") \
            .option("lowerBound", "1") \
            .option("upperBound", "10000000") \
            .option("numPartitions", "100") \
            .load()

        # Cache for performance
        florida_parcels_df.cache()

        # Show statistics
        total_count = florida_parcels_df.count()
        logger.info(f"Loaded {total_count:,} property records")

        # Perform data quality checks
        quality_report = self.perform_data_quality_checks(florida_parcels_df)

        return florida_parcels_df

    def load_sunbiz_data(self) -> DataFrame:
        """
        Load Sunbiz corporation data using PySpark
        """
        logger.info("Loading Sunbiz data with PySpark...")

        # Load corporations data
        sunbiz_df = self.spark.read \
            .format("jdbc") \
            .option("url", self.db_config["url"]) \
            .option("dbtable", "sunbiz_corporations") \
            .option("user", self.db_config["properties"]["user"]) \
            .option("password", self.db_config["properties"]["password"]) \
            .option("driver", self.db_config["properties"]["driver"]) \
            .option("fetchsize", self.db_config["properties"]["fetchsize"]) \
            .load()

        # Cache for performance
        sunbiz_df.cache()

        total_count = sunbiz_df.count()
        logger.info(f"Loaded {total_count:,} corporation records")

        return sunbiz_df

    def perform_data_quality_checks(self, df: DataFrame) -> Dict[str, Any]:
        """
        Perform comprehensive data quality checks using PySpark
        """
        logger.info("Performing data quality checks...")

        quality_report = {
            "total_records": df.count(),
            "null_analysis": {},
            "value_distributions": {},
            "outliers": {},
            "data_completeness": {}
        }

        # Analyze null values for required fields
        for field in self.validation_rules["required_fields"]:
            if field in df.columns:
                null_count = df.filter(col(field).isNull()).count()
                quality_report["null_analysis"][field] = {
                    "null_count": null_count,
                    "null_percentage": (null_count / quality_report["total_records"]) * 100
                }

        # Analyze numeric field distributions
        numeric_fields = list(self.validation_rules["numeric_fields"].keys())
        for field in numeric_fields:
            if field in df.columns:
                stats = df.select(
                    F.mean(col(field)).alias("mean"),
                    F.stddev(col(field)).alias("stddev"),
                    F.min(col(field)).alias("min"),
                    F.max(col(field)).alias("max"),
                    F.expr(f"percentile_approx({field}, 0.25)").alias("q1"),
                    F.expr(f"percentile_approx({field}, 0.50)").alias("median"),
                    F.expr(f"percentile_approx({field}, 0.75)").alias("q3")
                ).collect()[0]

                quality_report["value_distributions"][field] = {
                    "mean": float(stats["mean"]) if stats["mean"] else 0,
                    "stddev": float(stats["stddev"]) if stats["stddev"] else 0,
                    "min": float(stats["min"]) if stats["min"] else 0,
                    "max": float(stats["max"]) if stats["max"] else 0,
                    "q1": float(stats["q1"]) if stats["q1"] else 0,
                    "median": float(stats["median"]) if stats["median"] else 0,
                    "q3": float(stats["q3"]) if stats["q3"] else 0
                }

                # Detect outliers using IQR method
                if stats["q1"] and stats["q3"]:
                    iqr = stats["q3"] - stats["q1"]
                    lower_bound = stats["q1"] - 1.5 * iqr
                    upper_bound = stats["q3"] + 1.5 * iqr

                    outlier_count = df.filter(
                        (col(field) < lower_bound) | (col(field) > upper_bound)
                    ).count()

                    quality_report["outliers"][field] = {
                        "outlier_count": outlier_count,
                        "outlier_percentage": (outlier_count / quality_report["total_records"]) * 100,
                        "lower_bound": lower_bound,
                        "upper_bound": upper_bound
                    }

        # Calculate overall data completeness
        total_fields = len(df.columns)
        non_null_counts = []
        for col_name in df.columns:
            non_null = df.filter(col(col_name).isNotNull()).count()
            non_null_counts.append(non_null)

        avg_completeness = sum(non_null_counts) / (total_fields * quality_report["total_records"]) * 100
        quality_report["data_completeness"]["average"] = avg_completeness

        return quality_report

    def create_field_mapping_dataframe(self, source_df: DataFrame, source_type: str) -> DataFrame:
        """
        Create a DataFrame with field mappings for verification
        """
        logger.info(f"Creating field mapping DataFrame for {source_type}...")

        # Get mapping configuration
        if source_type == "property_appraiser":
            mappings = self.field_mappings.get("property_appraiser", {}).get("florida_parcels", {})
        elif source_type == "sunbiz":
            mappings = self.field_mappings.get("sunbiz", {}).get("sunbiz_corporations", {})
        else:
            mappings = {}

        # Select and rename columns based on mapping
        select_expressions = []
        for db_field, mapping_info in mappings.items():
            if db_field in source_df.columns:
                ui_field = mapping_info["ui_field"]
                tab = mapping_info["tab"]

                # Create struct with mapping information
                select_expressions.append(
                    struct(
                        col(db_field).alias("db_value"),
                        lit(ui_field).alias("ui_field"),
                        lit(tab).alias("ui_tab"),
                        lit(db_field).alias("db_field")
                    ).alias(f"mapping_{db_field}")
                )

        if select_expressions:
            # Add primary key
            if "parcel_id" in source_df.columns:
                select_expressions.insert(0, col("parcel_id"))
            elif "corp_number" in source_df.columns:
                select_expressions.insert(0, col("corp_number").alias("id"))

            mapped_df = source_df.select(*select_expressions)
            return mapped_df
        else:
            logger.warning(f"No mappings found for {source_type}")
            return source_df

    def apply_transformations(self, df: DataFrame) -> DataFrame:
        """
        Apply PySpark transformations for data formatting and validation
        """
        logger.info("Applying data transformations...")

        # Currency formatting for value fields
        currency_fields = ["jv", "av_sd", "tv_sd", "lnd_val", "sale_prc1"]
        for field in currency_fields:
            if field in df.columns:
                df = df.withColumn(
                    f"{field}_formatted",
                    concat(lit("$"), format_number(col(field), 2))
                )

        # Date formatting
        if "sale_yr1" in df.columns and "sale_mo1" in df.columns:
            df = df.withColumn(
                "sale_date",
                to_date(
                    concat(
                        col("sale_yr1"),
                        lit("-"),
                        lpad(col("sale_mo1"), 2, "0"),
                        lit("-01")
                    ),
                    "yyyy-MM-dd"
                )
            )

        # Property use code mapping
        use_code_mapping = {
            "0100": "Single Family",
            "0200": "Multi Family",
            "1000": "Commercial",
            "4000": "Industrial",
            "5000": "Agricultural",
            "0000": "Vacant Land"
        }

        if "dor_uc" in df.columns:
            # Create a mapping DataFrame
            mapping_data = [(k, v) for k, v in use_code_mapping.items()]
            mapping_df = self.spark.createDataFrame(
                mapping_data, ["code", "description"]
            )

            # Join to get descriptions
            df = df.join(
                mapping_df,
                df.dor_uc == mapping_df.code,
                "left"
            ).drop("code")

        # Calculate derived fields
        if "jv" in df.columns and "lnd_val" in df.columns:
            df = df.withColumn(
                "building_value",
                when(col("jv") > col("lnd_val"), col("jv") - col("lnd_val")).otherwise(0)
            )

        # Add data quality flags
        df = df.withColumn(
            "data_quality_score",
            when(col("parcel_id").isNotNull(), 20).otherwise(0) +
            when(col("phy_addr1").isNotNull(), 20).otherwise(0) +
            when(col("owner_name").isNotNull(), 20).otherwise(0) +
            when(col("jv").isNotNull() & (col("jv") > 0), 20).otherwise(0) +
            when(col("yr_blt").isNotNull() & (col("yr_blt") > 1800), 20).otherwise(0)
        )

        return df

    def validate_field_mappings(self, df: DataFrame) -> DataFrame:
        """
        Validate field mappings using PySpark operations
        """
        logger.info("Validating field mappings...")

        # Add validation columns
        validation_expressions = []

        # Check required fields
        for field in self.validation_rules["required_fields"]:
            if field in df.columns:
                validation_expressions.append(
                    when(col(field).isNotNull(), 1).otherwise(0).alias(f"valid_{field}")
                )

        # Check numeric ranges
        for field, rules in self.validation_rules["numeric_fields"].items():
            if field in df.columns:
                validation_expressions.append(
                    when(
                        (col(field).isNull()) |
                        ((col(field) >= rules["min"]) & (col(field) <= rules["max"])),
                        1
                    ).otherwise(0).alias(f"valid_range_{field}")
                )

        if validation_expressions:
            df = df.select("*", *validation_expressions)

            # Calculate overall validation score
            validation_cols = [col for col in df.columns if col.startswith("valid_")]
            if validation_cols:
                df = df.withColumn(
                    "validation_score",
                    sum([col(c) for c in validation_cols]) / len(validation_cols) * 100
                )

        return df

    def create_ui_verification_dataset(self, df: DataFrame) -> DataFrame:
        """
        Create dataset for UI verification with Playwright
        """
        logger.info("Creating UI verification dataset...")

        # Select sample for UI testing (stratified sampling)
        # Sample high-value properties
        high_value_sample = df.filter(col("jv") > 1000000).limit(100)

        # Sample medium-value properties
        medium_value_sample = df.filter(
            (col("jv") >= 200000) & (col("jv") <= 1000000)
        ).limit(200)

        # Sample low-value properties
        low_value_sample = df.filter(col("jv") < 200000).limit(100)

        # Combine samples
        verification_df = high_value_sample.union(medium_value_sample).union(low_value_sample)

        # Add verification metadata
        verification_df = verification_df.withColumn(
            "verification_id",
            concat(
                col("parcel_id"),
                lit("_"),
                unix_timestamp(current_timestamp())
            )
        )

        verification_df = verification_df.withColumn(
            "verification_status",
            lit("pending")
        )

        verification_df = verification_df.withColumn(
            "verification_timestamp",
            current_timestamp()
        )

        return verification_df

    def generate_field_mapping_report(self, df: DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive field mapping report using PySpark analytics
        """
        logger.info("Generating field mapping report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_records_processed": df.count(),
            "field_coverage": {},
            "validation_summary": {},
            "data_quality_metrics": {}
        }

        # Field coverage analysis
        for col_name in df.columns:
            if not col_name.startswith("valid_") and not col_name.startswith("mapping_"):
                non_null_count = df.filter(col(col_name).isNotNull()).count()
                coverage_pct = (non_null_count / report["total_records_processed"]) * 100
                report["field_coverage"][col_name] = {
                    "non_null_count": non_null_count,
                    "coverage_percentage": coverage_pct
                }

        # Validation summary
        if "validation_score" in df.columns:
            validation_stats = df.select(
                F.mean("validation_score").alias("avg_score"),
                F.min("validation_score").alias("min_score"),
                F.max("validation_score").alias("max_score"),
                F.stddev("validation_score").alias("stddev_score")
            ).collect()[0]

            report["validation_summary"] = {
                "average_validation_score": float(validation_stats["avg_score"]) if validation_stats["avg_score"] else 0,
                "min_validation_score": float(validation_stats["min_score"]) if validation_stats["min_score"] else 0,
                "max_validation_score": float(validation_stats["max_score"]) if validation_stats["max_score"] else 0,
                "stddev_validation_score": float(validation_stats["stddev_score"]) if validation_stats["stddev_score"] else 0
            }

            # Count records by validation score ranges
            score_ranges = [
                (0, 50, "poor"),
                (50, 75, "fair"),
                (75, 90, "good"),
                (90, 100, "excellent")
            ]

            for min_score, max_score, label in score_ranges:
                count = df.filter(
                    (col("validation_score") >= min_score) &
                    (col("validation_score") < max_score)
                ).count()
                report["validation_summary"][f"{label}_quality_count"] = count

        # Data quality metrics
        if "data_quality_score" in df.columns:
            quality_stats = df.select(
                F.mean("data_quality_score").alias("avg_quality"),
                F.count(when(col("data_quality_score") == 100, True)).alias("perfect_quality_count")
            ).collect()[0]

            report["data_quality_metrics"] = {
                "average_quality_score": float(quality_stats["avg_quality"]) if quality_stats["avg_quality"] else 0,
                "perfect_quality_records": int(quality_stats["perfect_quality_count"]) if quality_stats["perfect_quality_count"] else 0
            }

        return report

    def optimize_data_for_ui_display(self, df: DataFrame) -> DataFrame:
        """
        Optimize data for efficient UI display using PySpark
        """
        logger.info("Optimizing data for UI display...")

        # Partition by common query patterns
        df = df.repartition(200, "phy_city", "phy_zipcd")

        # Create aggregated views for dashboard
        city_aggregates = df.groupBy("phy_city").agg(
            count("*").alias("property_count"),
            avg("jv").alias("avg_value"),
            sum("jv").alias("total_value"),
            avg("yr_blt").alias("avg_year_built")
        ).filter(col("property_count") > 10)

        # Create property type aggregates
        if "dor_uc" in df.columns:
            type_aggregates = df.groupBy("dor_uc").agg(
                count("*").alias("count"),
                avg("jv").alias("avg_value"),
                avg("tot_lvg_area").alias("avg_living_area")
            )
        else:
            type_aggregates = None

        # Create year-over-year trends
        if "sale_yr1" in df.columns:
            year_trends = df.filter(col("sale_yr1").isNotNull()).groupBy("sale_yr1").agg(
                count("*").alias("sale_count"),
                avg("sale_prc1").alias("avg_sale_price"),
                stddev("sale_prc1").alias("stddev_sale_price")
            ).orderBy("sale_yr1")
        else:
            year_trends = None

        # Cache frequently accessed data
        df.cache()
        city_aggregates.cache()

        # Create indexed views for fast lookups
        df.createOrReplaceTempView("properties")
        city_aggregates.createOrReplaceTempView("city_stats")

        # Enable adaptive query execution
        self.spark.conf.set("spark.sql.adaptive.enabled", "true")
        self.spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

        return df

    def export_to_parquet(self, df: DataFrame, output_path: str):
        """
        Export processed data to Parquet for fast loading
        """
        logger.info(f"Exporting to Parquet: {output_path}")

        df.write \
            .mode("overwrite") \
            .option("compression", "snappy") \
            .partitionBy("phy_city", "year") \
            .parquet(output_path)

        logger.info(f"Export complete: {output_path}")

    def run_complete_processing_pipeline(self):
        """
        Run the complete PySpark processing pipeline
        """
        logger.info("="*60)
        logger.info("STARTING PYSPARK FIELD MAPPING PIPELINE")
        logger.info("="*60)

        try:
            # Load Property Appraiser data
            logger.info("\n1. Loading Property Appraiser Data...")
            property_df = self.load_property_appraiser_data()

            # Load Sunbiz data
            logger.info("\n2. Loading Sunbiz Data...")
            sunbiz_df = self.load_sunbiz_data()

            # Apply transformations
            logger.info("\n3. Applying Transformations...")
            property_df = self.apply_transformations(property_df)

            # Validate field mappings
            logger.info("\n4. Validating Field Mappings...")
            property_df = self.validate_field_mappings(property_df)

            # Create field mapping DataFrames
            logger.info("\n5. Creating Field Mapping DataFrames...")
            property_mapped = self.create_field_mapping_dataframe(property_df, "property_appraiser")
            sunbiz_mapped = self.create_field_mapping_dataframe(sunbiz_df, "sunbiz")

            # Create UI verification dataset
            logger.info("\n6. Creating UI Verification Dataset...")
            verification_df = self.create_ui_verification_dataset(property_df)

            # Optimize for UI display
            logger.info("\n7. Optimizing for UI Display...")
            optimized_df = self.optimize_data_for_ui_display(property_df)

            # Generate report
            logger.info("\n8. Generating Field Mapping Report...")
            report = self.generate_field_mapping_report(property_df)

            # Export to Parquet for fast access
            logger.info("\n9. Exporting to Parquet...")
            self.export_to_parquet(optimized_df, "data/processed/properties_optimized")

            # Print summary
            self._print_summary(report)

            return {
                "success": True,
                "report": report,
                "property_records": property_df.count(),
                "sunbiz_records": sunbiz_df.count(),
                "verification_samples": verification_df.count()
            }

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _print_summary(self, report: Dict):
        """Print processing summary"""
        print("\n" + "="*60)
        print("PYSPARK PROCESSING SUMMARY")
        print("="*60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Records Processed: {report['total_records_processed']:,}")

        if report.get('validation_summary'):
            print(f"\nValidation Summary:")
            print(f"  Average Score: {report['validation_summary']['average_validation_score']:.2f}%")
            print(f"  Excellent Quality: {report['validation_summary'].get('excellent_quality_count', 0):,}")
            print(f"  Good Quality: {report['validation_summary'].get('good_quality_count', 0):,}")
            print(f"  Fair Quality: {report['validation_summary'].get('fair_quality_count', 0):,}")
            print(f"  Poor Quality: {report['validation_summary'].get('poor_quality_count', 0):,}")

        if report.get('data_quality_metrics'):
            print(f"\nData Quality Metrics:")
            print(f"  Average Quality Score: {report['data_quality_metrics']['average_quality_score']:.2f}")
            print(f"  Perfect Quality Records: {report['data_quality_metrics']['perfect_quality_records']:,}")

    def cleanup(self):
        """Cleanup Spark resources"""
        self.spark.stop()


if __name__ == "__main__":
    processor = PySparkFieldMappingProcessor()
    try:
        result = processor.run_complete_processing_pipeline()
        print(f"\nPipeline Result: {'SUCCESS' if result['success'] else 'FAILED'}")
    finally:
        processor.cleanup()