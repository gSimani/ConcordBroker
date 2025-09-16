"""
Integrated PySpark + Playwright MCP + OpenCV Verification System
Complete field mapping verification with big data processing and visual validation
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
import pyspark.sql.functions as F
from playwright.async_api import async_playwright
import cv2
import numpy as np
import asyncio
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import pandas as pd
from pathlib import Path
import hashlib
import pytesseract
from PIL import Image
import io
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PySparkPlaywrightOpenCVVerifier:
    """
    Complete verification system integrating:
    - PySpark for big data processing
    - Playwright MCP for UI automation
    - OpenCV for visual verification
    """

    def __init__(self):
        # Initialize Spark with optimized settings for verification
        self.spark = self._initialize_spark()

        # Browser and vision components
        self.browser = None
        self.page = None

        # Thread pools for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        self.process_pool = ProcessPoolExecutor(max_workers=4)

        # Load configurations
        self.field_mappings = self._load_field_mappings()
        self.verification_results = []

        # Initialize verification schemas
        self.verification_schema = self._create_verification_schema()

    def _initialize_spark(self) -> SparkSession:
        """Initialize optimized Spark session"""
        return SparkSession.builder \
            .appName("ConcordBroker_Complete_Verifier") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.adaptive.skewJoin.enabled", "true") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .config("spark.driver.memory", "12g") \
            .config("spark.executor.memory", "12g") \
            .config("spark.executor.cores", "8") \
            .config("spark.sql.shuffle.partitions", "400") \
            .config("spark.driver.maxResultSize", "4g") \
            .config("spark.network.timeout", "600s") \
            .config("spark.executor.heartbeatInterval", "120s") \
            .config("spark.sql.broadcastTimeout", "600") \
            .config("spark.sql.autoBroadcastJoinThreshold", "50MB") \
            .getOrCreate()

    def _load_field_mappings(self) -> Dict:
        """Load complete field mapping configuration"""
        config_path = Path('field_mapping_configuration.json')
        with open(config_path, 'r') as f:
            return json.load(f)

    def _create_verification_schema(self) -> StructType:
        """Create schema for verification results"""
        return StructType([
            StructField("parcel_id", StringType(), False),
            StructField("field_name", StringType(), False),
            StructField("db_value", StringType(), True),
            StructField("ui_value", StringType(), True),
            StructField("ui_tab", StringType(), True),
            StructField("ui_field_id", StringType(), True),
            StructField("is_matched", BooleanType(), True),
            StructField("visual_match_score", DoubleType(), True),
            StructField("ocr_confidence", DoubleType(), True),
            StructField("screenshot_path", StringType(), True),
            StructField("verification_timestamp", TimestampType(), True),
            StructField("error_message", StringType(), True)
        ])

    async def initialize_browser(self):
        """Initialize Playwright browser for UI verification"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized', '--disable-blink-features=AutomationControlled']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await context.new_page()

        # Add JavaScript injection for field extraction
        await self.page.add_init_script("""
            window.extractFieldData = function() {
                const fields = {};
                // Extract all input fields
                document.querySelectorAll('input, select, textarea').forEach(el => {
                    const id = el.id || el.name || el.getAttribute('data-field');
                    if (id) {
                        fields[id] = el.value;
                    }
                });
                // Extract display values
                document.querySelectorAll('[data-field]').forEach(el => {
                    const field = el.getAttribute('data-field');
                    fields[field] = el.textContent;
                });
                return fields;
            };
        """)

    def process_property_appraiser_batch(self, batch_df: DataFrame) -> DataFrame:
        """
        Process a batch of Property Appraiser records with PySpark
        """
        logger.info(f"Processing batch of {batch_df.count()} Property Appraiser records...")

        # Apply field mappings
        pa_mappings = self.field_mappings['field_mappings']['property_appraiser_to_ui']

        # Create mapping expressions for each tab
        mapping_expressions = []
        for tab_name, tab_config in pa_mappings.items():
            for section_name, section_fields in tab_config.items():
                for db_field, field_config in section_fields.items():
                    if db_field in batch_df.columns:
                        mapping_expressions.append(
                            struct(
                                col("parcel_id").alias("parcel_id"),
                                lit(db_field).alias("db_field"),
                                col(db_field).cast(StringType()).alias("db_value"),
                                lit(field_config['ui_field']).alias("ui_field"),
                                lit(field_config['label']).alias("ui_label"),
                                lit(tab_name.replace('_tab', '')).alias("ui_tab"),
                                lit(field_config['format']).alias("format_type"),
                                lit(field_config.get('required', False)).alias("is_required")
                            ).alias(f"map_{db_field}")
                        )

        if mapping_expressions:
            # Select all mapping columns
            mapped_df = batch_df.select(*mapping_expressions)

            # Convert to single column array
            mapping_array = array(*[col(c) for c in mapped_df.columns])
            mapped_df = mapped_df.withColumn("mappings", mapping_array)

            # Explode to create row per mapping
            exploded_df = mapped_df.select(
                explode(col("mappings")).alias("mapping")
            ).select("mapping.*")

            return exploded_df
        else:
            return batch_df

    def process_sunbiz_batch(self, batch_df: DataFrame) -> DataFrame:
        """
        Process a batch of Sunbiz records with PySpark
        """
        logger.info(f"Processing batch of {batch_df.count()} Sunbiz records...")

        sunbiz_mappings = self.field_mappings['field_mappings']['sunbiz_to_ui']

        mapping_expressions = []
        for tab_name, tab_config in sunbiz_mappings.items():
            for section_name, section_fields in tab_config.items():
                for db_field, field_config in section_fields.items():
                    if db_field in batch_df.columns:
                        mapping_expressions.append(
                            struct(
                                col("corp_number").alias("entity_id"),
                                lit(db_field).alias("db_field"),
                                col(db_field).cast(StringType()).alias("db_value"),
                                lit(field_config['ui_field']).alias("ui_field"),
                                lit(field_config['label']).alias("ui_label"),
                                lit(tab_name.replace('_tab', '')).alias("ui_tab"),
                                lit(field_config['format']).alias("format_type")
                            ).alias(f"map_{db_field}")
                        )

        if mapping_expressions:
            mapped_df = batch_df.select(*mapping_expressions)
            mapping_array = array(*[col(c) for c in mapped_df.columns])
            mapped_df = mapped_df.withColumn("mappings", mapping_array)
            exploded_df = mapped_df.select(
                explode(col("mappings")).alias("mapping")
            ).select("mapping.*")

            return exploded_df
        else:
            return batch_df

    async def verify_ui_field_placement(self,
                                       record_id: str,
                                       field_mapping: Dict) -> Dict:
        """
        Verify field placement in UI using Playwright
        """
        try:
            # Navigate to the property page
            url = f"http://localhost:5173/property/{record_id}"
            await self.page.goto(url, wait_until='networkidle')

            # Navigate to the correct tab
            tab_name = field_mapping['ui_tab']
            tab_selector = f'[data-tab="{tab_name}"], button:has-text("{tab_name.title()}")'
            await self.page.click(tab_selector)
            await self.page.wait_for_timeout(500)

            # Extract all field data from the page
            field_data = await self.page.evaluate("() => window.extractFieldData()")

            # Get specific field value
            ui_field_id = field_mapping['ui_field']
            ui_value = field_data.get(ui_field_id)

            # If not found, try alternative selectors
            if not ui_value:
                selectors = [
                    f'#{ui_field_id}',
                    f'[data-field="{ui_field_id}"]',
                    f'[name="{ui_field_id}"]',
                    f'text={field_mapping["ui_label"]}'
                ]

                for selector in selectors:
                    element = await self.page.query_selector(selector)
                    if element:
                        ui_value = await element.text_content()
                        break

            # Take screenshot for visual verification
            screenshot_path = await self._capture_field_screenshot(record_id, ui_field_id)

            # Perform visual verification
            visual_match_score = await self._verify_with_opencv(
                screenshot_path,
                field_mapping['db_value'],
                field_mapping['format_type']
            )

            # Compare values
            is_matched = self._compare_values(
                field_mapping['db_value'],
                ui_value,
                field_mapping['format_type']
            )

            return {
                'parcel_id': record_id,
                'field_name': field_mapping['db_field'],
                'db_value': field_mapping['db_value'],
                'ui_value': ui_value,
                'ui_tab': tab_name,
                'ui_field_id': ui_field_id,
                'is_matched': is_matched,
                'visual_match_score': visual_match_score,
                'screenshot_path': screenshot_path,
                'verification_timestamp': datetime.now()
            }

        except Exception as e:
            logger.error(f"UI verification failed for {record_id}: {e}")
            return {
                'parcel_id': record_id,
                'field_name': field_mapping.get('db_field'),
                'error_message': str(e),
                'verification_timestamp': datetime.now()
            }

    async def _capture_field_screenshot(self, record_id: str, field_id: str) -> str:
        """Capture screenshot of specific field"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_dir = Path('verification_screenshots')
        screenshot_dir.mkdir(exist_ok=True)

        screenshot_path = screenshot_dir / f"{record_id}_{field_id}_{timestamp}.png"

        # Try to capture specific element
        element = await self.page.query_selector(f'#{field_id}, [data-field="{field_id}"]')
        if element:
            await element.screenshot(path=str(screenshot_path))
        else:
            # Capture full page if element not found
            await self.page.screenshot(path=str(screenshot_path), full_page=False)

        return str(screenshot_path)

    async def _verify_with_opencv(self,
                                 screenshot_path: str,
                                 expected_value: str,
                                 format_type: str) -> float:
        """
        Verify field display using OpenCV and OCR
        """
        try:
            # Read image
            img = cv2.imread(screenshot_path)
            if img is None:
                return 0.0

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply preprocessing
            processed = self._preprocess_image_for_ocr(gray)

            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(
                processed,
                config='--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$,.-/ '
            )

            # Format expected value based on type
            formatted_expected = self._format_value_for_comparison(expected_value, format_type)

            # Calculate similarity score
            similarity_score = self._calculate_text_similarity(
                extracted_text.strip(),
                formatted_expected
            )

            # Additional verification for currency values
            if format_type == "currency" and expected_value:
                # Check if numeric value appears
                numeric_value = ''.join(filter(str.isdigit, expected_value))
                if numeric_value in extracted_text:
                    similarity_score = max(similarity_score, 0.8)

            return similarity_score

        except Exception as e:
            logger.error(f"OpenCV verification failed: {e}")
            return 0.0

    def _preprocess_image_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""

        # Apply bilateral filter to reduce noise while keeping edges sharp
        denoised = cv2.bilateralFilter(image, 9, 75, 75)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Morphological operations to connect text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        return processed

    def _format_value_for_comparison(self, value: str, format_type: str) -> str:
        """Format value based on type for comparison"""
        if not value:
            return ""

        if format_type == "currency":
            try:
                numeric_value = float(value)
                return f"${numeric_value:,.2f}"
            except:
                return value

        elif format_type == "sqft":
            try:
                numeric_value = float(value)
                return f"{numeric_value:,.0f} sq ft"
            except:
                return value

        elif format_type == "year":
            return str(value) if value else "N/A"

        elif format_type == "percentage":
            try:
                numeric_value = float(value)
                return f"{numeric_value}%"
            except:
                return value

        else:
            return str(value)

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0

        # Normalize texts
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()

        # Exact match
        if text1 == text2:
            return 1.0

        # Contains check
        if text2 in text1 or text1 in text2:
            return 0.9

        # Levenshtein distance-based similarity
        distance = self._levenshtein_distance(text1, text2)
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 0.0

        similarity = 1 - (distance / max_len)
        return max(0.0, similarity)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _compare_values(self, db_value: str, ui_value: str, format_type: str) -> bool:
        """Compare database and UI values"""
        if not db_value and not ui_value:
            return True

        if not db_value or not ui_value:
            return False

        # Normalize values
        db_normalized = str(db_value).strip().upper()
        ui_normalized = str(ui_value).strip().upper()

        # Direct comparison
        if db_normalized == ui_normalized:
            return True

        # Numeric comparison for currency and numbers
        if format_type in ["currency", "float", "integer"]:
            try:
                db_numeric = float(''.join(filter(lambda x: x.isdigit() or x == '.', db_value)))
                ui_numeric = float(''.join(filter(lambda x: x.isdigit() or x == '.', ui_value)))
                return abs(db_numeric - ui_numeric) < 0.01
            except:
                pass

        # Partial match for addresses
        if format_type == "string" and len(db_normalized) > 10:
            return db_normalized[:10] in ui_normalized or ui_normalized[:10] in db_normalized

        return False

    def create_verification_report_with_pyspark(self, verification_df: DataFrame) -> Dict:
        """
        Create comprehensive verification report using PySpark analytics
        """
        logger.info("Generating PySpark verification report...")

        # Overall statistics
        total_verifications = verification_df.count()
        successful_matches = verification_df.filter(col("is_matched") == True).count()
        failed_matches = verification_df.filter(col("is_matched") == False).count()

        # Tab-level analysis
        tab_stats = verification_df.groupBy("ui_tab").agg(
            count("*").alias("total_fields"),
            sum(when(col("is_matched") == True, 1).otherwise(0)).alias("matched_fields"),
            avg("visual_match_score").alias("avg_visual_score")
        ).collect()

        # Field-level analysis
        field_stats = verification_df.groupBy("field_name").agg(
            count("*").alias("verification_count"),
            sum(when(col("is_matched") == True, 1).otherwise(0)).alias("match_count"),
            avg("visual_match_score").alias("avg_visual_score"),
            avg("ocr_confidence").alias("avg_ocr_confidence")
        ).filter(col("match_count") < col("verification_count") * 0.8).collect()

        # Visual verification statistics
        visual_stats = verification_df.select(
            avg("visual_match_score").alias("avg_score"),
            stddev("visual_match_score").alias("stddev_score"),
            min("visual_match_score").alias("min_score"),
            max("visual_match_score").alias("max_score")
        ).collect()[0]

        # Error analysis
        error_df = verification_df.filter(col("error_message").isNotNull())
        error_stats = error_df.groupBy("error_message").count().collect()

        report = {
            "report_timestamp": datetime.now().isoformat(),
            "overall_statistics": {
                "total_verifications": total_verifications,
                "successful_matches": successful_matches,
                "failed_matches": failed_matches,
                "success_rate": (successful_matches / total_verifications * 100) if total_verifications > 0 else 0
            },
            "tab_statistics": [
                {
                    "tab": row["ui_tab"],
                    "total_fields": row["total_fields"],
                    "matched_fields": row["matched_fields"],
                    "accuracy": (row["matched_fields"] / row["total_fields"] * 100) if row["total_fields"] > 0 else 0,
                    "avg_visual_score": row["avg_visual_score"]
                }
                for row in tab_stats
            ],
            "problematic_fields": [
                {
                    "field": row["field_name"],
                    "verification_count": row["verification_count"],
                    "match_count": row["match_count"],
                    "success_rate": (row["match_count"] / row["verification_count"] * 100) if row["verification_count"] > 0 else 0
                }
                for row in field_stats
            ],
            "visual_verification": {
                "average_score": float(visual_stats["avg_score"]) if visual_stats["avg_score"] else 0,
                "std_deviation": float(visual_stats["stddev_score"]) if visual_stats["stddev_score"] else 0,
                "min_score": float(visual_stats["min_score"]) if visual_stats["min_score"] else 0,
                "max_score": float(visual_stats["max_score"]) if visual_stats["max_score"] else 0
            },
            "errors": [
                {"error": row["error_message"], "count": row["count"]}
                for row in error_stats
            ]
        }

        return report

    async def run_complete_verification_pipeline(self,
                                                sample_size: int = 1000) -> Dict:
        """
        Run complete verification pipeline with PySpark + Playwright + OpenCV
        """
        logger.info("="*60)
        logger.info("STARTING COMPLETE VERIFICATION PIPELINE")
        logger.info("PySpark + Playwright MCP + OpenCV")
        logger.info("="*60)

        try:
            # Initialize browser
            await self.initialize_browser()

            # Load data with PySpark
            logger.info("\n1. Loading data with PySpark...")
            property_df = self._load_property_data()
            sunbiz_df = self._load_sunbiz_data()

            # Sample data for verification
            logger.info(f"\n2. Sampling {sample_size} records for verification...")
            property_sample = property_df.sample(fraction=min(sample_size/property_df.count(), 1.0))
            sunbiz_sample = sunbiz_df.sample(fraction=min(sample_size/sunbiz_df.count(), 1.0))

            # Process with PySpark
            logger.info("\n3. Processing field mappings with PySpark...")
            property_mapped = self.process_property_appraiser_batch(property_sample)
            sunbiz_mapped = self.process_sunbiz_batch(sunbiz_sample)

            # Combine mappings
            all_mappings = property_mapped.union(sunbiz_mapped)

            # Convert to Pandas for UI verification
            logger.info("\n4. Starting UI verification with Playwright...")
            mappings_pd = all_mappings.toPandas()

            verification_results = []
            for idx, row in mappings_pd.iterrows():
                if idx % 100 == 0:
                    logger.info(f"  Verified {idx}/{len(mappings_pd)} fields...")

                result = await self.verify_ui_field_placement(
                    row['parcel_id'] if 'parcel_id' in row else row.get('entity_id'),
                    row.to_dict()
                )
                verification_results.append(result)

            # Convert results back to PySpark DataFrame
            logger.info("\n5. Analyzing results with PySpark...")
            results_df = self.spark.createDataFrame(verification_results, self.verification_schema)

            # Generate report
            logger.info("\n6. Generating comprehensive report...")
            report = self.create_verification_report_with_pyspark(results_df)

            # Save results
            logger.info("\n7. Saving verification results...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_df.write.mode("overwrite").parquet(f"verification_results_{timestamp}.parquet")

            with open(f"verification_report_{timestamp}.json", 'w') as f:
                json.dump(report, f, indent=2)

            # Print summary
            self._print_verification_summary(report)

            return {
                "success": True,
                "report": report,
                "results_path": f"verification_results_{timestamp}.parquet"
            }

        except Exception as e:
            logger.error(f"Verification pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

        finally:
            if self.browser:
                await self.browser.close()
            self.spark.stop()

    def _load_property_data(self) -> DataFrame:
        """Load property data from database"""
        return self.spark.read \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://aws-0-us-east-1.pooler.supabase.com:6543/postgres") \
            .option("dbtable", "florida_parcels") \
            .option("user", "postgres.pmispwtdngkcmsrsjwbp") \
            .option("password", "vM4g2024$$Florida1") \
            .option("driver", "org.postgresql.Driver") \
            .load()

    def _load_sunbiz_data(self) -> DataFrame:
        """Load Sunbiz data from database"""
        return self.spark.read \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://aws-0-us-east-1.pooler.supabase.com:6543/postgres") \
            .option("dbtable", "sunbiz_corporations") \
            .option("user", "postgres.pmispwtdngkcmsrsjwbp") \
            .option("password", "vM4g2024$$Florida1") \
            .option("driver", "org.postgresql.Driver") \
            .load()

    def _print_verification_summary(self, report: Dict):
        """Print verification summary"""
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        print(f"Timestamp: {report['report_timestamp']}")
        print(f"Total Verifications: {report['overall_statistics']['total_verifications']:,}")
        print(f"Successful Matches: {report['overall_statistics']['successful_matches']:,}")
        print(f"Failed Matches: {report['overall_statistics']['failed_matches']:,}")
        print(f"Success Rate: {report['overall_statistics']['success_rate']:.2f}%")

        print("\nTab Statistics:")
        for tab_stat in report['tab_statistics'][:5]:  # Show top 5
            print(f"  {tab_stat['tab']}: {tab_stat['accuracy']:.2f}% accuracy")

        if report['problematic_fields']:
            print("\nProblematic Fields:")
            for field in report['problematic_fields'][:5]:  # Show top 5
                print(f"  {field['field']}: {field['success_rate']:.2f}% success rate")

        print(f"\nVisual Verification Score: {report['visual_verification']['average_score']:.2f}")


async def main():
    """Main execution function"""
    verifier = PySparkPlaywrightOpenCVVerifier()

    # Run complete verification
    result = await verifier.run_complete_verification_pipeline(sample_size=100)

    if result['success']:
        print(f"\n✓ Verification completed successfully")
        print(f"  Report saved to: verification_report_*.json")
        print(f"  Results saved to: {result['results_path']}")
    else:
        print(f"\n✗ Verification failed: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())