"""
PySpark Processor for Bulk DOR Use Code Assignment
Processes all 9.1M properties using distributed computing
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, lit, count, round as spark_round,
    sum as spark_sum, avg, max as spark_max, min as spark_min
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, BooleanType
import os

class DORUseCodeSparkProcessor:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("DOR Use Code Assignment") \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g") \
            .config("spark.sql.shuffle.partitions", "200") \
            .getOrCreate()

        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        # Build JDBC URL
        db_url = self.supabase_url.replace('https://', '').split('.')[1]
        self.jdbc_url = f"jdbc:postgresql://{self.supabase_url.replace('https://', '')}:5432/postgres"

    def load_properties(self):
        """Load florida_parcels from Supabase"""
        print("📥 Loading florida_parcels data from Supabase...")

        df = self.spark.read \
            .format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("dbtable", "florida_parcels") \
            .option("user", "postgres") \
            .option("password", self.supabase_key) \
            .option("driver", "org.postgresql.Driver") \
            .load()

        # Filter for 2025 data
        df = df.filter(col("year") == 2025)

        print(f"✅ Loaded {df.count():,} properties from 2025")
        return df

    def load_dor_codes(self):
        """Load DOR use codes reference table"""
        print("📥 Loading DOR use codes reference...")

        df = self.spark.read \
            .format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("dbtable", "dor_use_codes") \
            .option("user", "postgres") \
            .option("password", self.supabase_key) \
            .option("driver", "org.postgresql.Driver") \
            .load()

        print(f"✅ Loaded {df.count()} DOR use codes")
        return df

    def analyze_use_code_coverage(self, properties_df):
        """Analyze current DOR use code coverage"""
        print("\n📊 Analyzing DOR Use Code Coverage...")

        total_count = properties_df.count()

        with_code = properties_df.filter(
            (col("dor_uc").isNotNull()) & (col("dor_uc") != "")
        ).count()

        without_code = total_count - with_code

        coverage_pct = (with_code / total_count * 100) if total_count > 0 else 0

        print(f"Total Properties: {total_count:,}")
        print(f"With DOR Code: {with_code:,} ({coverage_pct:.2f}%)")
        print(f"Without DOR Code: {without_code:,} ({100 - coverage_pct:.2f}%)")

        # Get distribution
        distribution = properties_df \
            .filter((col("dor_uc").isNotNull()) & (col("dor_uc") != "")) \
            .groupBy("dor_uc") \
            .agg(count("*").alias("count")) \
            .orderBy(col("count").desc()) \
            .limit(20)

        print("\n🏆 Top 20 Use Codes:")
        distribution.show()

        return {
            "total": total_count,
            "with_code": with_code,
            "without_code": without_code,
            "coverage_percentage": coverage_pct
        }

    def assign_use_codes_intelligent(self, properties_df, dor_codes_df):
        """Intelligently assign DOR use codes based on property characteristics"""
        print("\n🧠 Assigning DOR Use Codes Using Intelligent Logic...")

        # Create broadcast variable for DOR codes (small lookup table)
        dor_codes_broadcast = self.spark.sparkContext.broadcast(
            dor_codes_df.select("use_code", "use_description", "category").collect()
        )

        # Apply intelligent use code assignment logic
        enhanced_df = properties_df.withColumn(
            "assigned_dor_uc",
            when(
                # Already has DOR code - keep it
                (col("dor_uc").isNotNull()) & (col("dor_uc") != ""),
                col("dor_uc")
            ).when(
                # Single Family Residential: High building value, moderate land
                (col("building_value") > 50000) &
                (col("building_value") > col("land_value")) &
                (col("just_value") < 1000000),
                lit("00")  # Single Family
            ).when(
                # Multi-Family: Very high building value
                (col("building_value") > 500000) &
                (col("building_value") > col("land_value") * 2),
                lit("02")  # Multi-Family 10+ units
            ).when(
                # Commercial: High total value, moderate building
                (col("just_value") > 500000) &
                (col("building_value") > 200000) &
                (col("building_value").between(col("land_value") * 0.5, col("land_value") * 2)),
                lit("17")  # Commercial
            ).when(
                # Industrial: Very high building value on moderate land
                (col("building_value") > 1000000) &
                (col("land_value") < 500000),
                lit("24")  # Industrial
            ).when(
                # Agricultural: High land value, low building value
                (col("land_value") > col("building_value") * 5) &
                (col("land_value") > 100000),
                lit("01")  # Agricultural
            ).when(
                # Vacant Residential: Land only, no building
                (col("land_value") > 0) &
                ((col("building_value").isNull()) | (col("building_value") == 0)),
                lit("10")  # Vacant Residential
            ).when(
                # Institutional: Specific characteristics
                (col("just_value") > 1000000) &
                (col("building_value") > 500000),
                lit("80")  # Institutional
            ).otherwise(
                lit("00")  # Default to Single Family
            )
        )

        # Update the actual dor_uc column
        enhanced_df = enhanced_df.withColumn(
            "dor_uc",
            col("assigned_dor_uc")
        ).drop("assigned_dor_uc")

        # Assign human-readable property use description
        enhanced_df = enhanced_df.withColumn(
            "property_use",
            when(col("dor_uc") == "00", lit("Single Family"))
            .when(col("dor_uc") == "01", lit("Agricultural"))
            .when(col("dor_uc") == "02", lit("Multi-Family 10+"))
            .when(col("dor_uc") == "10", lit("Vacant Residential"))
            .when(col("dor_uc") == "17", lit("Commercial"))
            .when(col("dor_uc") == "24", lit("Industrial"))
            .when(col("dor_uc") == "80", lit("Institutional"))
            .otherwise(lit("Other"))
        )

        # Assign category
        enhanced_df = enhanced_df.withColumn(
            "property_use_category",
            when(col("dor_uc").isin(["00", "01", "02", "03", "04", "05", "06", "10"]), lit("Residential"))
            .when(col("dor_uc").isin(["11", "12", "13", "14", "15", "16", "17", "18", "19"]), lit("Commercial"))
            .when(col("dor_uc").isin(["20", "21", "22", "23", "24", "25", "26", "27"]), lit("Industrial"))
            .when(col("dor_uc").isin(["30", "31", "32", "33", "34", "35", "36", "37", "38"]), lit("Agricultural"))
            .when(col("dor_uc").isin(["80", "81", "82", "83", "84", "85", "86", "87", "88", "89"]), lit("Institutional"))
            .otherwise(lit("Other"))
        )

        print("✅ DOR use codes assigned successfully")
        return enhanced_df

    def write_back_to_supabase(self, df):
        """Write updated data back to Supabase"""
        print("\n💾 Writing updated data back to Supabase...")

        df.write \
            .format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("dbtable", "florida_parcels") \
            .option("user", "postgres") \
            .option("password", self.supabase_key) \
            .option("driver", "org.postgresql.Driver") \
            .mode("overwrite") \
            .save()

        print("✅ Data written successfully")

    def generate_analytics(self, df):
        """Generate comprehensive analytics"""
        print("\n📈 Generating Analytics...")

        # Use code distribution
        use_code_dist = df.groupBy("dor_uc", "property_use") \
            .agg(
                count("*").alias("count"),
                spark_sum("just_value").alias("total_value"),
                avg("just_value").alias("avg_value"),
                spark_max("just_value").alias("max_value"),
                spark_min("just_value").alias("min_value")
            ) \
            .orderBy(col("count").desc())

        print("\n📊 Use Code Distribution:")
        use_code_dist.show(50)

        # Category distribution
        category_dist = df.groupBy("property_use_category") \
            .agg(
                count("*").alias("count"),
                spark_sum("just_value").alias("total_value")
            ) \
            .orderBy(col("count").desc())

        print("\n📊 Category Distribution:")
        category_dist.show()

        # County breakdown
        county_dist = df.groupBy("county", "property_use_category") \
            .agg(count("*").alias("count")) \
            .orderBy("county", col("count").desc())

        print("\n📊 Top Counties:")
        county_dist.show(100)

        return {
            "use_code_distribution": use_code_dist,
            "category_distribution": category_dist,
            "county_distribution": county_dist
        }

    def run_full_pipeline(self):
        """Run the complete DOR use code assignment pipeline"""
        print("🚀 Starting DOR Use Code Assignment Pipeline")
        print("=" * 80)

        try:
            # Load data
            properties_df = self.load_properties()
            dor_codes_df = self.load_dor_codes()

            # Analyze current coverage
            coverage = self.analyze_use_code_coverage(properties_df)

            # Assign use codes
            enhanced_df = self.assign_use_codes_intelligent(properties_df, dor_codes_df)

            # Analyze after assignment
            print("\n📊 Re-analyzing After Assignment...")
            final_coverage = self.analyze_use_code_coverage(enhanced_df)

            # Generate analytics
            analytics = self.generate_analytics(enhanced_df)

            # Write back (commented out for safety - uncomment to actually update)
            # self.write_back_to_supabase(enhanced_df)
            print("\n⚠️ Write-back commented out for safety. Uncomment to update database.")

            print("\n" + "=" * 80)
            print("🎉 Pipeline Complete!")
            print(f"Initial Coverage: {coverage['coverage_percentage']:.2f}%")
            print(f"Final Coverage: {final_coverage['coverage_percentage']:.2f}%")
            print(f"Improvement: {final_coverage['coverage_percentage'] - coverage['coverage_percentage']:.2f}%")
            print("=" * 80)

            return True

        except Exception as e:
            print(f"❌ Pipeline failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.spark.stop()

def main():
    processor = DORUseCodeSparkProcessor()
    success = processor.run_full_pipeline()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())