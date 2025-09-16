"""
Property Appraiser Data Loader - Production Ready
Uses Pandas, NumPy, Matplotlib, Seaborn, scikit-learn for complete ETL pipeline
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Core data processing
import pandas as pd
import numpy as np
from supabase import create_client, Client

# Visualization and analytics
import matplotlib.pyplot as plt
import seaborn as sns

# Machine learning for data validation
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN

# Load environment
from dotenv import load_dotenv
load_dotenv('.env.mcp')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('property_appraiser_loading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PropertyAppraiserLoader:
    """Complete ETL system for Property Appraiser data loading"""

    def __init__(self):
        # Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials")

        self.supabase = create_client(self.supabase_url, self.supabase_key)

        # Florida counties (all 67)
        self.florida_counties = [
            'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD',
            'CALHOUN', 'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA',
            'DESOTO', 'DIXIE', 'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN',
            'GADSDEN', 'GILCHRIST', 'GLADES', 'GULF', 'HAMILTON', 'HARDEE',
            'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH', 'HOLMES', 'INDIAN RIVER',
            'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE', 'LEE', 'LEON',
            'LEVY', 'LIBERTY', 'MADISON', 'MANATEE', 'MARION', 'MARTIN',
            'MIAMI-DADE', 'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE', 'ORANGE',
            'OSCEOLA', 'PALM BEACH', 'PASCO', 'PINELLAS', 'POLK', 'PUTNAM',
            'SANTA ROSA', 'SARASOTA', 'SEMINOLE', 'ST. JOHNS', 'ST. LUCIE', 'SUMTER',
            'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA', 'WAKULLA', 'WALTON', 'WASHINGTON'
        ]

        # Data paths
        self.data_base_path = Path("C:/Temp/DATABASE PROPERTY APP")

        # Column mappings per CLAUDE.md specifications
        self.column_mappings = {
            'NAL': {
                'PARCEL_ID': 'parcel_id',
                'OWNER_NAME': 'owner_name',
                'OWN_ADDR1': 'owner_addr1',        # Critical mapping
                'OWN_ADDR2': 'owner_addr2',        # Critical mapping
                'OWN_CITY': 'owner_city',
                'OWN_STATE': 'owner_state',        # Critical: truncate to 2 chars
                'OWN_ZIPCD': 'owner_zip',
                'PHY_ADDR1': 'phy_addr1',          # Critical mapping
                'PHY_ADDR2': 'phy_addr2',          # Critical mapping
                'PHY_CITY': 'phy_city',
                'PHY_STATE': 'phy_state',
                'PHY_ZIPCD': 'phy_zipcd',
                'LND_SQFOOT': 'land_sqft',         # Critical mapping
                'JV': 'just_value',                # Critical mapping
                'LND_VAL': 'land_value',
                'LEGAL_DESC': 'legal_desc'
            },
            'NAP': {
                'PARCEL_ID': 'parcel_id',
                'DOR_UC': 'property_use',
                'DOR_UC_DESC': 'property_use_desc',
                'LND_USE_CD': 'land_use_code',
                'ACT_YR_BLT': 'year_built',
                'TOT_LVG_AREA': 'total_living_area',
                'NO_BULDNG': 'units',
                'NO_RES_UNTS': 'units',
                'BEDROOMS': 'bedrooms',
                'BATHROOMS': 'bathrooms',
                'STORIES': 'stories'
            },
            'NAV': {
                'PARCEL_ID': 'parcel_id',
                'JV': 'just_value',
                'AV': 'assessed_value',
                'TV': 'taxable_value',
                'LND_VAL': 'land_value'
            },
            'SDF': {
                'PARCEL_ID': 'parcel_id',
                'SALE_YR1': 'sale_year',
                'SALE_MO1': 'sale_month',
                'SALE_PRC1': 'sale_price',
                'QUAL_CD1': 'sale_qualification'
            }
        }

        # Initialize analytics tracking
        self.stats = {
            'counties_processed': 0,
            'files_processed': 0,
            'total_records': 0,
            'anomalies_detected': 0,
            'errors': []
        }

    def load_and_transform_csv(self, file_path: Path, file_type: str, county: str) -> pd.DataFrame:
        """Load and transform CSV file with comprehensive data processing"""

        logger.info(f"Loading {file_type} file: {file_path.name} for {county}")

        try:
            # Read CSV with proper handling
            df = pd.read_csv(
                file_path,
                dtype=str,  # Read as strings first
                low_memory=False,
                encoding='utf-8-sig',
                on_bad_lines='warn'
            )

            original_count = len(df)
            logger.info(f"  Loaded {original_count:,} raw records")

            # Apply column mappings
            if file_type in self.column_mappings:
                mapping = self.column_mappings[file_type]
                available_mappings = {k: v for k, v in mapping.items() if k in df.columns}
                df = df.rename(columns=available_mappings)
                logger.info(f"  Mapped {len(available_mappings)} columns")

            # Add county and year
            df['county'] = county.upper()
            df['year'] = 2025
            df['data_source'] = file_type
            df['import_date'] = datetime.now()

            # === CRITICAL DATA TRANSFORMATIONS PER CLAUDE.md ===

            # 1. State code truncation (FLORIDA → FL)
            if 'owner_state' in df.columns:
                df['owner_state'] = df['owner_state'].str[:2]
                df['owner_state'] = df['owner_state'].replace({'FL': 'FL', 'FLORIDA': 'FL'})

            # 2. Numeric conversions with error handling
            numeric_columns = [
                'just_value', 'assessed_value', 'taxable_value', 'land_value',
                'sale_price', 'land_sqft', 'total_living_area', 'year_built',
                'bedrooms', 'bathrooms', 'stories', 'units'
            ]

            for col in numeric_columns:
                if col in df.columns:
                    # Convert to numeric, coerce errors to NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 3. Sale date construction (YYYY-MM-01T00:00:00 format)
            if 'sale_year' in df.columns and 'sale_month' in df.columns:
                # Convert to proper date format per CLAUDE.md
                df['sale_date'] = pd.to_datetime(
                    df['sale_year'].astype(str) + '-' +
                    df['sale_month'].fillna('1').astype(str) + '-01',
                    errors='coerce'
                )
                # Remove temporary columns
                df = df.drop(['sale_year', 'sale_month'], axis=1, errors='ignore')

            # 4. Calculate building_value = just_value - land_value
            if 'just_value' in df.columns and 'land_value' in df.columns:
                df['building_value'] = df['just_value'] - df['land_value']
                # Ensure non-negative
                df['building_value'] = df['building_value'].clip(lower=0)

            # 5. Data quality validations
            quality_issues = 0

            # Check for null parcel_ids
            if 'parcel_id' in df.columns:
                null_parcels = df['parcel_id'].isnull().sum()
                if null_parcels > 0:
                    df = df.dropna(subset=['parcel_id'])
                    quality_issues += null_parcels
                    logger.warning(f"  Removed {null_parcels} records with null parcel_id")

            # 6. Generate data hash for deduplication
            df['data_hash'] = df.apply(
                lambda row: hashlib.sha256(
                    f"{row.get('parcel_id', '')}{county}{2025}".encode()
                ).hexdigest(),
                axis=1
            )

            # 7. Clean data - replace NaN with None for database compatibility
            df = df.replace({np.nan: None, np.inf: None, -np.inf: None})

            final_count = len(df)
            logger.info(f"  Processed to {final_count:,} clean records ({final_count-original_count:+d} change)")

            return df

        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
            self.stats['errors'].append(f"{county}/{file_type}: {str(e)}")
            return pd.DataFrame()

    def detect_anomalies_advanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced anomaly detection using multiple ML techniques"""

        if df.empty or len(df) < 100:
            return df

        logger.info(f"  Running anomaly detection on {len(df):,} records...")

        # Select features for anomaly detection
        feature_columns = ['just_value', 'land_value', 'land_sqft', 'total_living_area', 'sale_price']
        available_features = [col for col in feature_columns if col in df.columns]

        if not available_features:
            logger.warning("  No numeric features available for anomaly detection")
            return df

        try:
            # Prepare feature matrix
            X = df[available_features].copy()

            # Handle missing values
            X = X.fillna(0)

            # Remove infinite values
            X = X.replace([np.inf, -np.inf], 0)

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Method 1: Isolation Forest
            iso_forest = IsolationForest(
                contamination=0.02,  # Expect 2% anomalies
                random_state=42,
                n_estimators=100
            )
            iso_anomalies = iso_forest.fit_predict(X_scaled)

            # Method 2: DBSCAN clustering (outliers = noise points)
            dbscan = DBSCAN(eps=0.5, min_samples=10)
            clusters = dbscan.fit_predict(X_scaled)
            dbscan_anomalies = clusters == -1  # Noise points

            # Combine methods - record is anomalous if flagged by either method
            df['is_anomaly'] = (iso_anomalies == -1) | dbscan_anomalies
            df['anomaly_score'] = iso_forest.decision_function(X_scaled)

            anomaly_count = df['is_anomaly'].sum()
            anomaly_rate = anomaly_count / len(df) * 100

            logger.info(f"  Detected {anomaly_count:,} anomalies ({anomaly_rate:.2f}%)")

            self.stats['anomalies_detected'] += anomaly_count

            return df

        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
            df['is_anomaly'] = False
            df['anomaly_score'] = 0
            return df

    def batch_upsert_to_supabase(self, df: pd.DataFrame, batch_size: int = 1000) -> int:
        """Batch upsert data to Supabase with conflict handling"""

        if df.empty:
            return 0

        logger.info(f"  Upserting {len(df):,} records to Supabase...")

        # Define valid columns for the florida_parcels table
        valid_columns = [
            'parcel_id', 'county', 'year', 'owner_name', 'owner_addr1', 'owner_addr2',
            'owner_city', 'owner_state', 'owner_zip', 'phy_addr1', 'phy_addr2',
            'phy_city', 'phy_state', 'phy_zipcd', 'legal_desc', 'subdivision',
            'lot', 'block', 'property_use', 'property_use_desc', 'land_use_code',
            'zoning', 'year_built', 'total_living_area', 'bedrooms', 'bathrooms',
            'stories', 'units', 'just_value', 'assessed_value', 'taxable_value',
            'land_value', 'building_value', 'land_sqft', 'land_acres',
            'sale_date', 'sale_price', 'sale_qualification', 'match_status',
            'discrepancy_reason', 'is_redacted', 'is_anomaly', 'data_source',
            'import_date', 'update_date', 'data_hash', 'geometry', 'centroid',
            'area_sqft', 'perimeter_ft', 'anomaly_score'
        ]

        # Filter DataFrame to valid columns only
        df_filtered = df[[col for col in valid_columns if col in df.columns]].copy()

        # Convert datetime columns to ISO format strings
        for col in df_filtered.columns:
            if df_filtered[col].dtype == 'datetime64[ns]':
                df_filtered[col] = df_filtered[col].dt.strftime('%Y-%m-%dT%H:%M:%S')

        total_inserted = 0
        errors = 0

        # Process in batches
        for i in range(0, len(df_filtered), batch_size):
            batch = df_filtered.iloc[i:i+batch_size]

            try:
                # Convert to list of dictionaries
                records = batch.to_dict('records')

                # Use Supabase upsert (handles conflicts automatically)
                result = self.supabase.table('florida_parcels').upsert(
                    records,
                    on_conflict='parcel_id,county,year'
                ).execute()

                batch_inserted = len(records)
                total_inserted += batch_inserted

                # Progress reporting
                if total_inserted % 10000 == 0:
                    logger.info(f"    Processed {total_inserted:,}/{len(df_filtered):,} records")

            except Exception as e:
                errors += 1
                if errors <= 3:  # Only log first few errors
                    logger.error(f"    Batch upsert error: {str(e)[:200]}")

                # On error, try smaller batches
                if batch_size > 100:
                    smaller_batch_size = batch_size // 2
                    logger.info(f"    Retrying with smaller batch size: {smaller_batch_size}")

                    # Recursively process with smaller batches
                    partial_result = self.batch_upsert_to_supabase(batch, smaller_batch_size)
                    total_inserted += partial_result

        logger.info(f"  Upserted {total_inserted:,} records ({errors} batch errors)")
        return total_inserted

    def process_county_data(self, county: str) -> dict:
        """Process all data files for a single county"""

        logger.info(f"Processing county: {county}")

        county_stats = {
            'county': county,
            'files_found': 0,
            'files_processed': 0,
            'total_records': 0,
            'anomalies': 0,
            'processing_time': 0,
            'status': 'not_started'
        }

        start_time = time.time()

        try:
            # Check county data path
            county_path = self.data_base_path / county.upper()

            if not county_path.exists():
                # Try alternative naming conventions
                alt_paths = [
                    self.data_base_path / county.replace(' ', '_'),
                    self.data_base_path / county.replace('-', '_'),
                    Path(f"C:/Temp/{county.upper()}")
                ]

                for alt_path in alt_paths:
                    if alt_path.exists():
                        county_path = alt_path
                        break
                else:
                    logger.warning(f"County data path not found: {county}")
                    county_stats['status'] = 'path_not_found'
                    return county_stats

            # Process each file type
            all_dataframes = []

            for file_type in ['NAL', 'NAP', 'NAV', 'SDF']:
                # Find files with various extensions
                patterns = [f"{file_type}*.csv", f"{file_type}*.txt", f"*{file_type}*.csv"]
                files_found = []

                for pattern in patterns:
                    files_found.extend(list(county_path.glob(pattern)))

                county_stats['files_found'] += len(files_found)

                for file_path in files_found:
                    logger.info(f"  Processing {file_type}: {file_path.name}")

                    # Load and transform data
                    df = self.load_and_transform_csv(file_path, file_type, county)

                    if not df.empty:
                        county_stats['files_processed'] += 1
                        all_dataframes.append(df)

            # Merge all dataframes for the county
            if all_dataframes:
                logger.info(f"  Merging {len(all_dataframes)} datasets for {county}")

                # Start with the first dataframe
                merged_df = all_dataframes[0].copy()

                # Merge additional dataframes on parcel_id
                for df in all_dataframes[1:]:
                    # Identify columns to merge (exclude duplicates except parcel_id)
                    merge_columns = ['parcel_id'] + [
                        col for col in df.columns
                        if col not in merged_df.columns and col != 'parcel_id'
                    ]

                    if merge_columns:
                        merged_df = pd.merge(
                            merged_df,
                            df[merge_columns],
                            on='parcel_id',
                            how='outer',
                            suffixes=('', '_new')
                        )

                # Advanced anomaly detection
                merged_df = self.detect_anomalies_advanced(merged_df)
                county_stats['anomalies'] = merged_df['is_anomaly'].sum()

                # Upload to Supabase
                records_uploaded = self.batch_upsert_to_supabase(merged_df)
                county_stats['total_records'] = records_uploaded

                county_stats['status'] = 'completed'

            else:
                logger.warning(f"No valid data files found for {county}")
                county_stats['status'] = 'no_data'

        except Exception as e:
            logger.error(f"Error processing {county}: {e}")
            county_stats['status'] = 'error'
            county_stats['error_message'] = str(e)
            self.stats['errors'].append(f"{county}: {str(e)}")

        county_stats['processing_time'] = time.time() - start_time
        logger.info(f"  Completed {county} in {county_stats['processing_time']:.1f}s")

        return county_stats

    def parallel_process_counties(self, counties: list = None, max_workers: int = 4) -> list:
        """Process multiple counties in parallel"""

        if counties is None:
            counties = self.florida_counties

        logger.info(f"Starting parallel processing of {len(counties)} counties with {max_workers} workers")

        all_results = []
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all county processing tasks
            future_to_county = {
                executor.submit(self.process_county_data, county): county
                for county in counties
            }

            # Process completed futures
            for future in as_completed(future_to_county):
                county = future_to_county[future]

                try:
                    result = future.result()
                    all_results.append(result)

                    # Update global stats
                    self.stats['counties_processed'] += 1
                    self.stats['files_processed'] += result['files_processed']
                    self.stats['total_records'] += result['total_records']

                    logger.info(f"✓ {county}: {result['total_records']:,} records ({result['status']})")

                except Exception as e:
                    logger.error(f"✗ {county}: Processing failed - {e}")
                    all_results.append({
                        'county': county,
                        'status': 'failed',
                        'error': str(e),
                        'total_records': 0
                    })

        total_time = time.time() - start_time
        logger.info(f"Parallel processing completed in {total_time:.1f}s")

        return all_results

    def generate_comprehensive_report(self, county_results: list):
        """Generate comprehensive analytics report with visualizations"""

        logger.info("Generating comprehensive analytics report...")

        # Convert results to DataFrame for analysis
        results_df = pd.DataFrame(county_results)

        # Create visualizations
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(3, 2, figsize=(16, 18))
        fig.suptitle('Property Appraiser Data Loading - Comprehensive Report', fontsize=18, fontweight='bold')

        # 1. Records by County (Top 20)
        ax1 = axes[0, 0]
        top_counties = results_df.nlargest(20, 'total_records')
        sns.barplot(data=top_counties, y='county', x='total_records', ax=ax1, palette='viridis')
        ax1.set_title('Top 20 Counties by Records Loaded', fontweight='bold')
        ax1.set_xlabel('Records Loaded')

        # 2. Processing Status Distribution
        ax2 = axes[0, 1]
        status_counts = results_df['status'].value_counts()
        colors = ['#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
        ax2.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', colors=colors)
        ax2.set_title('Processing Status Distribution', fontweight='bold')

        # 3. Processing Time Analysis
        ax3 = axes[1, 0]
        successful_results = results_df[results_df['status'] == 'completed']
        if not successful_results.empty:
            sns.histplot(data=successful_results, x='processing_time', bins=20, ax=ax3)
            ax3.set_title('Processing Time Distribution (Successful Counties)', fontweight='bold')
            ax3.set_xlabel('Processing Time (seconds)')

        # 4. Files vs Records Correlation
        ax4 = axes[1, 1]
        if not successful_results.empty:
            sns.scatterplot(data=successful_results, x='files_processed', y='total_records', ax=ax4, s=60, alpha=0.7)
            ax4.set_title('Files Processed vs Records Loaded', fontweight='bold')
            ax4.set_xlabel('Files Processed')
            ax4.set_ylabel('Records Loaded')

        # 5. Anomaly Detection Results
        ax5 = axes[2, 0]
        anomaly_data = results_df[results_df['anomalies'] > 0]
        if not anomaly_data.empty:
            sns.barplot(data=anomaly_data.head(15), y='county', x='anomalies', ax=ax5, palette='Reds_r')
            ax5.set_title('Anomalies Detected by County (Top 15)', fontweight='bold')
            ax5.set_xlabel('Number of Anomalies')

        # 6. Summary Statistics
        ax6 = axes[2, 1]
        ax6.axis('off')

        total_records = results_df['total_records'].sum()
        successful_counties = len(results_df[results_df['status'] == 'completed'])
        failed_counties = len(results_df[results_df['status'] != 'completed'])
        total_anomalies = results_df['anomalies'].sum()

        summary_text = f"""
        DATA LOADING SUMMARY
        ══════════════════════════════════

        Total Records Loaded: {total_records:,}
        Expected Records: ~9,700,000
        Completion Rate: {(total_records/9700000)*100:.1f}%

        Counties Processed: {successful_counties}/{len(results_df)}
        Success Rate: {(successful_counties/len(results_df)*100):.1f}%
        Failed Counties: {failed_counties}

        Files Processed: {results_df['files_processed'].sum()}
        Anomalies Detected: {total_anomalies:,}
        Anomaly Rate: {(total_anomalies/max(total_records,1))*100:.3f}%

        Processing Performance:
        • Avg Time/County: {results_df['processing_time'].mean():.1f}s
        • Total Processing Time: {results_df['processing_time'].sum():.1f}s

        Data Quality Score: {self.calculate_data_quality_score(total_records, total_anomalies)}/100
        """

        ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))

        plt.tight_layout()

        # Save the report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'property_appraiser_comprehensive_report_{timestamp}.png'
        plt.savefig(report_filename, dpi=300, bbox_inches='tight')

        logger.info(f"Comprehensive report saved: {report_filename}")

        # Also save as JSON
        json_report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_records': int(total_records),
                'successful_counties': successful_counties,
                'failed_counties': failed_counties,
                'total_anomalies': int(total_anomalies),
                'completion_rate': round((total_records/9700000)*100, 2),
                'data_quality_score': self.calculate_data_quality_score(total_records, total_anomalies)
            },
            'county_details': county_results,
            'processing_stats': self.stats
        }

        json_filename = f'property_appraiser_report_{timestamp}.json'
        with open(json_filename, 'w') as f:
            json.dump(json_report, f, indent=2, default=str)

        logger.info(f"JSON report saved: {json_filename}")

        return report_filename, json_filename

    def calculate_data_quality_score(self, total_records: int, total_anomalies: int) -> int:
        """Calculate overall data quality score"""

        if total_records == 0:
            return 0

        # Base score
        score = 100

        # Penalize for low record count (expected 9.7M)
        expected_records = 9700000
        completion_rate = total_records / expected_records
        if completion_rate < 1.0:
            score -= (1.0 - completion_rate) * 30  # Up to 30 points for incompleteness

        # Penalize for high anomaly rate
        anomaly_rate = total_anomalies / total_records
        if anomaly_rate > 0.05:  # More than 5% anomalies
            score -= (anomaly_rate - 0.05) * 100  # Penalize excess anomalies

        # Penalize for errors
        error_penalty = min(len(self.stats['errors']) * 2, 20)  # Up to 20 points for errors
        score -= error_penalty

        return max(0, int(score))

    def create_florida_revenue_monitor_advanced(self):
        """Create advanced monitoring system with web scraping"""

        monitor_script = '''
"""
Advanced Florida Revenue Portal Monitor
Uses BeautifulSoup for web scraping and change detection
"""

import schedule
import time
import hashlib
import json
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class FloridaRevenueMonitorAdvanced:
    """Advanced monitoring with web scraping and notifications"""

    def __init__(self):
        self.portal_url = "https://floridarevenue.com/property/dataportal/Pages/default.aspx"
        self.checksums_file = "florida_revenue_checksums.json"
        self.alerts_file = "revenue_alerts.log"
        self.load_checksums()

    def load_checksums(self):
        """Load previous file checksums"""
        try:
            if Path(self.checksums_file).exists():
                with open(self.checksums_file, 'r') as f:
                    self.checksums = json.load(f)
            else:
                self.checksums = {}
        except Exception as e:
            print(f"Error loading checksums: {e}")
            self.checksums = {}

    def save_checksums(self):
        """Save current checksums"""
        try:
            with open(self.checksums_file, 'w') as f:
                json.dump(self.checksums, f, indent=2)
        except Exception as e:
            print(f"Error saving checksums: {e}")

    def check_portal_updates(self):
        """Scrape portal for data updates"""

        print(f"[{datetime.now()}] Checking Florida Revenue portal...")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(self.portal_url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for download links and update dates
            updates_found = []

            # Find all links that might be data downloads
            links = soup.find_all('a', href=True)

            for link in links:
                text = link.get_text(strip=True).upper()
                href = link.get('href', '')

                # Check if this looks like county data
                if any(county in text for county in ['COUNTY', 'PARCEL', 'PROPERTY', 'TAX']):
                    if any(ext in href.lower() for ext in ['.zip', '.csv', '.txt']):

                        # Generate checksum for this link
                        link_content = f"{text}{href}"
                        link_hash = hashlib.md5(link_content.encode()).hexdigest()

                        # Check if this is new or changed
                        if text not in self.checksums or self.checksums[text] != link_hash:
                            updates_found.append({
                                'name': text,
                                'url': href,
                                'timestamp': datetime.now().isoformat(),
                                'type': 'new_or_updated'
                            })

                            self.checksums[text] = link_hash

            # Look for last modified dates
            date_elements = soup.find_all(['span', 'div', 'p'],
                                        text=lambda t: t and ('updated' in t.lower() or
                                                             'modified' in t.lower() or
                                                             'last' in t.lower()))

            for element in date_elements:
                date_text = element.get_text(strip=True)
                date_hash = hashlib.md5(date_text.encode()).hexdigest()

                if 'last_modified' not in self.checksums or self.checksums['last_modified'] != date_hash:
                    updates_found.append({
                        'name': 'Portal Last Modified',
                        'content': date_text,
                        'timestamp': datetime.now().isoformat(),
                        'type': 'date_change'
                    })
                    self.checksums['last_modified'] = date_hash

            if updates_found:
                self.handle_updates(updates_found)
                self.save_checksums()
                return updates_found

            print("  No updates detected")
            return []

        except Exception as e:
            print(f"  Error checking portal: {e}")
            self.log_alert(f"Portal check failed: {e}")
            return []

    def handle_updates(self, updates):
        """Handle detected updates"""

        for update in updates:
            message = f"[UPDATE DETECTED] {update['name']}"
            print(message)

            # Log the alert
            self.log_alert(message)

            # Trigger data refresh if needed
            if update['type'] == 'new_or_updated':
                self.trigger_data_refresh(update)

    def trigger_data_refresh(self, update):
        """Trigger automated data refresh process"""

        print(f"  Triggering data refresh for: {update['name']}")

        # Create a trigger file that other systems can watch
        trigger_info = {
            'trigger_time': datetime.now().isoformat(),
            'update_detected': update,
            'refresh_required': True
        }

        with open('data_refresh_trigger.json', 'w') as f:
            json.dump(trigger_info, f, indent=2)

    def log_alert(self, message):
        """Log alerts to file"""

        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} - {message}\\n"

        with open(self.alerts_file, 'a') as f:
            f.write(log_entry)

    def run_monitoring(self):
        """Run continuous monitoring"""

        # Schedule checks every 4 hours during business hours
        schedule.every().day.at("02:00").do(self.check_portal_updates)  # 2 AM
        schedule.every().day.at("08:00").do(self.check_portal_updates)  # 8 AM
        schedule.every().day.at("14:00").do(self.check_portal_updates)  # 2 PM
        schedule.every().day.at("20:00").do(self.check_portal_updates)  # 8 PM

        print("Florida Revenue Advanced Monitor started...")
        print("Monitoring schedule: 02:00, 08:00, 14:00, 20:00 daily")

        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                print("\\nMonitoring stopped by user")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error

if __name__ == "__main__":
    monitor = FloridaRevenueMonitorAdvanced()
    monitor.run_monitoring()
'''

        # Save the advanced monitor
        with open("florida_revenue_monitor_advanced.py", 'w') as f:
            f.write(monitor_script)

        logger.info("Advanced Florida Revenue monitoring system created")

        return True

def main():
    """Main execution function"""

    print("\n" + "="*70)
    print("PROPERTY APPRAISER DATA LOADING SYSTEM")
    print("Using: Pandas, NumPy, Matplotlib, Seaborn, scikit-learn")
    print("="*70 + "\n")

    # Initialize the loader
    try:
        loader = PropertyAppraiserLoader()
        print("✓ Data loader initialized")
        print(f"✓ Target counties: {len(loader.florida_counties)}")
        print(f"✓ Data path: {loader.data_base_path}")

    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return

    # Option to test with specific counties first
    test_counties = ['BROWARD', 'PALM BEACH', 'MIAMI-DADE']
    print(f"\\nStarting with test counties: {test_counties}")

    # Process counties
    results = loader.parallel_process_counties(test_counties, max_workers=2)

    # Generate comprehensive report
    report_file, json_file = loader.generate_comprehensive_report(results)

    # Create advanced monitoring
    loader.create_florida_revenue_monitor_advanced()

    # Final summary
    total_records = sum(r['total_records'] for r in results)

    print("\\n" + "="*70)
    print("DATA LOADING COMPLETED")
    print("="*70)
    print(f"Total records loaded: {total_records:,}")
    print(f"Data quality score: {loader.calculate_data_quality_score(total_records, loader.stats['anomalies_detected'])}/100")
    print(f"Report saved: {report_file}")
    print(f"JSON data: {json_file}")
    print("Advanced monitor: florida_revenue_monitor_advanced.py")
    print("="*70 + "\\n")

if __name__ == "__main__":
    main()