"""
PySpark Configuration for Big Data Processing
Handles large-scale property data analytics
"""

import os
import sys
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SparkConfig:
    """Configuration for PySpark sessions"""

    @staticmethod
    def get_spark_config() -> Dict[str, Any]:
        """Get optimized Spark configuration"""
        return {
            "spark.app.name": "ConcordBroker-PropertyAnalytics",
            "spark.master": "local[*]",  # Use all available cores

            # Memory settings
            "spark.driver.memory": "4g",
            "spark.executor.memory": "4g",
            "spark.driver.maxResultSize": "2g",

            # Performance optimizations
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
            "spark.sql.adaptive.skewJoin.enabled": "true",
            "spark.sql.adaptive.localShuffleReader.enabled": "true",

            # Shuffle optimizations
            "spark.sql.shuffle.partitions": "200",
            "spark.default.parallelism": "8",

            # Caching
            "spark.sql.warehouse.dir": "spark-warehouse",
            "spark.sql.catalogImplementation": "in-memory",

            # UI settings
            "spark.ui.enabled": "true",
            "spark.ui.port": "4040",

            # SQL optimizations
            "spark.sql.execution.arrow.pyspark.enabled": "true",
            "spark.sql.execution.arrow.maxRecordsPerBatch": "10000"
        }

    @staticmethod
    def create_spark_session():
        """Create optimized Spark session"""
        try:
            from pyspark.sql import SparkSession

            config = SparkConfig.get_spark_config()

            builder = SparkSession.builder
            for key, value in config.items():
                builder = builder.config(key, value)

            spark = builder.getOrCreate()

            # Set log level
            spark.sparkContext.setLogLevel("WARN")

            logger.info(f"Spark session created: {spark.sparkContext.appName}")
            logger.info(f"Spark UI available at: http://localhost:4040")

            return spark

        except ImportError:
            logger.error("PySpark not installed. Install with: pip install pyspark")
            return None
        except Exception as e:
            logger.error(f"Failed to create Spark session: {e}")
            return None

class PropertyDataProcessor:
    """Process property data using PySpark"""

    def __init__(self, spark_session=None):
        self.spark = spark_session or SparkConfig.create_spark_session()
        if not self.spark:
            raise RuntimeError("Could not initialize Spark session")

    def load_property_data(self, file_path: str, format: str = "csv"):
        """Load property data into Spark DataFrame"""
        try:
            if format == "csv":
                df = self.spark.read.csv(
                    file_path,
                    header=True,
                    inferSchema=True,
                    multiLine=True
                )
            elif format == "json":
                df = self.spark.read.json(file_path)
            elif format == "parquet":
                df = self.spark.read.parquet(file_path)
            else:
                raise ValueError(f"Unsupported format: {format}")

            # Cache for better performance
            df.cache()

            logger.info(f"Loaded {df.count()} records from {file_path}")
            return df

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return None

    def analyze_property_values(self, df):
        """Analyze property value distributions"""
        from pyspark.sql import functions as F

        try:
            # Calculate statistics
            stats = df.select(
                F.count("just_value").alias("count"),
                F.avg("just_value").alias("avg_value"),
                F.stddev("just_value").alias("stddev_value"),
                F.min("just_value").alias("min_value"),
                F.max("just_value").alias("max_value"),
                F.expr("percentile_approx(just_value, 0.5)").alias("median_value")
            ).collect()[0]

            # Group by property type
            type_stats = df.groupBy("property_type").agg(
                F.count("*").alias("count"),
                F.avg("just_value").alias("avg_value")
            ).orderBy("count", ascending=False)

            # Group by county
            county_stats = df.groupBy("county").agg(
                F.count("*").alias("count"),
                F.avg("just_value").alias("avg_value"),
                F.sum("just_value").alias("total_value")
            ).orderBy("total_value", ascending=False)

            return {
                "overall_stats": stats.asDict(),
                "by_type": type_stats.collect(),
                "by_county": county_stats.collect()
            }

        except Exception as e:
            logger.error(f"Error analyzing values: {e}")
            return None

    def find_investment_opportunities(self, df, max_price: float = 500000):
        """Find potential investment properties"""
        from pyspark.sql import functions as F

        try:
            # Calculate ROI potential
            df_roi = df.withColumn(
                "roi_potential",
                (F.col("assessed_value") - F.col("sale_price")) / F.col("sale_price") * 100
            )

            # Filter opportunities
            opportunities = df_roi.filter(
                (F.col("sale_price") <= max_price) &
                (F.col("roi_potential") > 10) &
                (F.col("property_type").isin(["SINGLE FAMILY", "CONDO", "TOWNHOUSE"]))
            ).select(
                "parcel_id",
                "county",
                "phy_addr1",
                "sale_price",
                "assessed_value",
                "roi_potential",
                "year_built",
                "building_sqft"
            ).orderBy("roi_potential", ascending=False)

            return opportunities.limit(100).collect()

        except Exception as e:
            logger.error(f"Error finding opportunities: {e}")
            return []

    def market_comparison(self, df, target_property):
        """Compare property to market"""
        from pyspark.sql import functions as F

        try:
            # Find comparable properties
            comps = df.filter(
                (F.col("county") == target_property["county"]) &
                (F.col("property_type") == target_property["property_type"]) &
                (F.abs(F.col("building_sqft") - target_property["building_sqft"]) < 500) &
                (F.abs(F.col("year_built") - target_property["year_built"]) < 10)
            )

            # Calculate market metrics
            market_stats = comps.agg(
                F.count("*").alias("comp_count"),
                F.avg("just_value").alias("avg_market_value"),
                F.avg("sale_price").alias("avg_sale_price"),
                F.avg(F.col("just_value") / F.col("building_sqft")).alias("avg_price_per_sqft")
            ).collect()[0]

            # Calculate percentile rank
            target_value = target_property["just_value"]
            percentile = comps.filter(F.col("just_value") <= target_value).count() / comps.count() * 100

            return {
                "comparable_properties": comps.count(),
                "market_stats": market_stats.asDict(),
                "property_percentile": percentile,
                "valuation_analysis": {
                    "is_undervalued": target_value < market_stats["avg_market_value"],
                    "value_difference": target_value - market_stats["avg_market_value"],
                    "value_difference_pct": (target_value - market_stats["avg_market_value"]) / market_stats["avg_market_value"] * 100
                }
            }

        except Exception as e:
            logger.error(f"Error in market comparison: {e}")
            return None

    def batch_process_counties(self, counties: list, process_func):
        """Process multiple counties in parallel"""
        from pyspark.sql import functions as F
        import concurrent.futures

        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(process_func, county): county
                for county in counties
            }

            for future in concurrent.futures.as_completed(futures):
                county = futures[future]
                try:
                    results[county] = future.result()
                    logger.info(f"Processed {county}")
                except Exception as e:
                    logger.error(f"Error processing {county}: {e}")
                    results[county] = None

        return results

    def save_results(self, df, output_path: str, format: str = "parquet"):
        """Save processed data"""
        try:
            if format == "parquet":
                df.write.mode("overwrite").parquet(output_path)
            elif format == "csv":
                df.coalesce(1).write.mode("overwrite").csv(output_path, header=True)
            elif format == "json":
                df.write.mode("overwrite").json(output_path)

            logger.info(f"Saved results to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return False

    def cleanup(self):
        """Clean up Spark session"""
        if self.spark:
            self.spark.stop()
            logger.info("Spark session closed")

# ML Model for property valuation
class PropertyValuationModel:
    """Machine learning model for property valuation using PySpark ML"""

    def __init__(self, spark_session=None):
        self.spark = spark_session or SparkConfig.create_spark_session()
        self.model = None

    def prepare_features(self, df):
        """Prepare features for ML model"""
        from pyspark.ml.feature import VectorAssembler, StandardScaler
        from pyspark.sql import functions as F

        # Select features
        feature_cols = [
            "land_sqft", "building_sqft", "year_built",
            "bedrooms", "bathrooms", "stories",
            "latitude", "longitude"
        ]

        # Handle missing values
        for col in feature_cols:
            df = df.withColumn(col, F.when(F.col(col).isNull(), 0).otherwise(F.col(col)))

        # Create feature vector
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features_raw"
        )

        df = assembler.transform(df)

        # Scale features
        scaler = StandardScaler(
            inputCol="features_raw",
            outputCol="features"
        )

        scaler_model = scaler.fit(df)
        df = scaler_model.transform(df)

        return df, scaler_model

    def train_model(self, df):
        """Train RandomForest model"""
        from pyspark.ml.regression import RandomForestRegressor
        from pyspark.ml.evaluation import RegressionEvaluator

        try:
            # Prepare features
            df, scaler = self.prepare_features(df)

            # Split data
            train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)

            # Train model
            rf = RandomForestRegressor(
                featuresCol="features",
                labelCol="just_value",
                numTrees=100,
                maxDepth=10,
                seed=42
            )

            self.model = rf.fit(train_df)

            # Evaluate model
            predictions = self.model.transform(test_df)
            evaluator = RegressionEvaluator(
                labelCol="just_value",
                predictionCol="prediction",
                metricName="rmse"
            )

            rmse = evaluator.evaluate(predictions)
            r2 = evaluator.setMetricName("r2").evaluate(predictions)

            logger.info(f"Model trained - RMSE: {rmse}, R2: {r2}")

            return {
                "rmse": rmse,
                "r2": r2,
                "feature_importance": self.model.featureImportances.toArray().tolist()
            }

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return None

    def predict_value(self, property_features):
        """Predict property value"""
        if not self.model:
            logger.error("Model not trained")
            return None

        try:
            # Create DataFrame from features
            df = self.spark.createDataFrame([property_features])

            # Prepare features
            df, _ = self.prepare_features(df)

            # Make prediction
            prediction = self.model.transform(df).select("prediction").collect()[0]["prediction"]

            return prediction

        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None

# Example usage
if __name__ == "__main__":
    # Create Spark session
    spark = SparkConfig.create_spark_session()

    if spark:
        processor = PropertyDataProcessor(spark)

        # Example: Load and analyze data
        # df = processor.load_property_data("path/to/property_data.csv")
        # stats = processor.analyze_property_values(df)
        # opportunities = processor.find_investment_opportunities(df)

        processor.cleanup()

    print("PySpark configuration ready for big data processing")