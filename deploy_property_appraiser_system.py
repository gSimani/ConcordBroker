"""
Complete Property Appraiser Database Deployment and Data Loading System
Uses: SQLAlchemy, Pandas, NumPy, PySpark for big data processing
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# Data processing libraries
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

# Visualization for monitoring
import matplotlib.pyplot as plt
import seaborn as sns

# Machine learning for data validation
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

# Web scraping for Florida Revenue portal
from bs4 import BeautifulSoup
import requests

# API development
from fastapi import FastAPI, BackgroundTasks
import uvicorn

# For big data processing
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, when, isnan, count, trim, upper
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    print("PySpark not available, using Pandas for data processing")

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.mcp')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('property_appraiser_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    logger.error("Missing Supabase credentials")
    sys.exit(1)

# Parse Supabase URL to create SQLAlchemy connection string
import re
match = re.search(r'https://([^.]+)\.supabase\.co', SUPABASE_URL)
if match:
    project_ref = match.group(1)
    DATABASE_URL = f"postgresql://postgres.{project_ref}:{SUPABASE_SERVICE_KEY}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
else:
    logger.error("Invalid Supabase URL format")
    sys.exit(1)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "server_settings": {"jit": "off"},
        "command_timeout": 60,
        "options": "-c statement_timeout=60000"
    }
)

Base = declarative_base()

class FloridaParcel(Base):
    """SQLAlchemy model for florida_parcels table"""
    __tablename__ = 'florida_parcels'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50), nullable=False)
    county = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)

    # Geometry
    geometry = Column(JSONB)
    centroid = Column(JSONB)
    area_sqft = Column(Float)
    perimeter_ft = Column(Float)

    # Ownership (NAL)
    owner_name = Column(String(255))
    owner_addr1 = Column(String(255))
    owner_addr2 = Column(String(255))
    owner_city = Column(String(100))
    owner_state = Column(String(2))
    owner_zip = Column(String(10))

    # Physical address
    phy_addr1 = Column(String(255))
    phy_addr2 = Column(String(255))
    phy_city = Column(String(100))
    phy_state = Column(String(2), default='FL')
    phy_zipcd = Column(String(10))

    # Legal
    legal_desc = Column(String)
    subdivision = Column(String(255))
    lot = Column(String(50))
    block = Column(String(50))

    # Property characteristics (NAP)
    property_use = Column(String(10))
    property_use_desc = Column(String(255))
    land_use_code = Column(String(10))
    zoning = Column(String(50))

    # Valuations (NAV)
    just_value = Column(Float)
    assessed_value = Column(Float)
    taxable_value = Column(Float)
    land_value = Column(Float)
    building_value = Column(Float)

    # Property details
    year_built = Column(Integer)
    total_living_area = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    stories = Column(Float)
    units = Column(Integer)

    # Land measurements
    land_sqft = Column(Float)
    land_acres = Column(Float)

    # Sales (SDF)
    sale_date = Column(DateTime)
    sale_price = Column(Float)
    sale_qualification = Column(String(10))

    # Data quality
    match_status = Column(String(20))
    discrepancy_reason = Column(String(100))
    is_redacted = Column(Boolean, default=False)
    data_source = Column(String(20))

    # Metadata
    import_date = Column(DateTime, default=datetime.now)
    update_date = Column(DateTime)
    data_hash = Column(String(64))

    __table_args__ = (
        UniqueConstraint('parcel_id', 'county', 'year', name='uq_parcel_county_year'),
        Index('idx_parcels_county', 'county'),
        Index('idx_parcels_year', 'year'),
        Index('idx_parcels_owner', 'owner_name'),
        Index('idx_parcels_address', 'phy_addr1', 'phy_city'),
        Index('idx_parcels_value', 'taxable_value'),
        Index('idx_parcels_sale', 'sale_date', 'sale_price'),
    )

class PropertyAppraiserDeployment:
    """Main deployment and data loading class"""

    def __init__(self):
        self.engine = engine
        self.session = sessionmaker(bind=engine)()
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

        # Initialize Spark if available
        if PYSPARK_AVAILABLE:
            self.spark = SparkSession.builder \
                .appName("PropertyAppraiserETL") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.files.maxPartitionBytes", "128MB") \
                .getOrCreate()

    def deploy_schema(self):
        """Deploy database schema to Supabase"""
        logger.info("Starting schema deployment...")

        try:
            # Drop existing tables if needed (be careful in production!)
            # Base.metadata.drop_all(engine)

            # Create all tables
            Base.metadata.create_all(engine)

            # Apply additional SQL configurations
            with self.engine.connect() as conn:
                # Enable PostGIS
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))  # For fuzzy text search

                # Disable timeouts for bulk operations
                conn.execute(text("""
                    ALTER ROLE authenticator SET statement_timeout TO '0';
                    ALTER ROLE postgres SET statement_timeout TO '0';
                    ALTER ROLE anon SET statement_timeout TO '0';
                    ALTER ROLE authenticated SET statement_timeout TO '0';
                    ALTER ROLE service_role SET statement_timeout TO '0';
                """))

                conn.commit()

            logger.info("Schema deployment completed successfully")
            return True

        except Exception as e:
            logger.error(f"Schema deployment failed: {e}")
            return False

    def load_csv_with_pandas(self, file_path: Path, file_type: str) -> pd.DataFrame:
        """Load CSV file using Pandas with proper data types"""

        # Define column mappings based on file type
        column_mappings = {
            'NAL': {
                'PARCEL_ID': 'parcel_id',
                'COUNTY': 'county',
                'OWNER_NAME': 'owner_name',
                'OWN_ADDR1': 'owner_addr1',
                'OWN_ADDR2': 'owner_addr2',
                'OWN_CITY': 'owner_city',
                'OWN_STATE': 'owner_state',
                'OWN_ZIPCD': 'owner_zip',
                'PHY_ADDR1': 'phy_addr1',
                'PHY_ADDR2': 'phy_addr2',
                'PHY_CITY': 'phy_city',
                'PHY_ZIPCD': 'phy_zipcd',
                'LND_SQFOOT': 'land_sqft',
                'JV': 'just_value'
            },
            'NAP': {
                'PARCEL_ID': 'parcel_id',
                'DOR_UC': 'property_use',
                'LND_USE_CD': 'land_use_code',
                'ACT_YR_BLT': 'year_built',
                'TOT_LVG_AREA': 'total_living_area',
                'NO_BULDNG': 'units',
                'NO_RES_UNTS': 'units'
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

        try:
            # Read CSV with appropriate data types
            df = pd.read_csv(
                file_path,
                dtype=str,  # Read as string first
                low_memory=False,
                encoding='utf-8-sig'
            )

            # Rename columns based on mapping
            if file_type in column_mappings:
                rename_dict = column_mappings[file_type]
                df = df.rename(columns=rename_dict)

            # Data type conversions
            numeric_columns = ['just_value', 'assessed_value', 'taxable_value',
                              'land_value', 'sale_price', 'land_sqft',
                              'total_living_area', 'year_built']

            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Handle state codes (truncate to 2 characters)
            if 'owner_state' in df.columns:
                df['owner_state'] = df['owner_state'].str[:2]

            # Create sale_date from year and month
            if 'sale_year' in df.columns and 'sale_month' in df.columns:
                df['sale_date'] = pd.to_datetime(
                    df['sale_year'].astype(str) + '-' +
                    df['sale_month'].astype(str) + '-01',
                    errors='coerce'
                )

            # Calculate building_value
            if 'just_value' in df.columns and 'land_value' in df.columns:
                df['building_value'] = df['just_value'] - df['land_value']
                df['building_value'] = df['building_value'].fillna(0)

            # Add metadata
            df['year'] = 2025
            df['import_date'] = datetime.now()
            df['data_source'] = file_type

            # Clean NaN values
            df = df.replace({np.nan: None})

            return df

        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return pd.DataFrame()

    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Use Isolation Forest to detect anomalous property records"""

        if df.empty:
            return df

        # Select numeric columns for anomaly detection
        numeric_cols = ['just_value', 'land_value', 'land_sqft', 'sale_price']
        available_cols = [col for col in numeric_cols if col in df.columns]

        if not available_cols:
            return df

        # Prepare data
        X = df[available_cols].fillna(0)

        # Scale the features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Detect anomalies
        iso_forest = IsolationForest(
            contamination=0.01,  # Expect 1% anomalies
            random_state=42
        )

        anomalies = iso_forest.fit_predict(X_scaled)
        df['is_anomaly'] = anomalies == -1

        # Log anomalies
        anomaly_count = df['is_anomaly'].sum()
        if anomaly_count > 0:
            logger.warning(f"Detected {anomaly_count} anomalous records")

        return df

    def batch_insert_data(self, df: pd.DataFrame, table_name: str = 'florida_parcels',
                         batch_size: int = 1000):
        """Batch insert data into database using SQLAlchemy"""

        if df.empty:
            return 0

        total_inserted = 0
        total_rows = len(df)

        # Convert DataFrame to records
        records = df.to_dict('records')

        for i in range(0, total_rows, batch_size):
            batch = records[i:i + batch_size]

            try:
                # Use SQLAlchemy's bulk insert
                with self.engine.begin() as conn:
                    # Generate data hash for each record
                    for record in batch:
                        # Create hash from key fields
                        hash_str = f"{record.get('parcel_id')}{record.get('county')}{record.get('year')}"
                        record['data_hash'] = hashlib.sha256(hash_str.encode()).hexdigest()

                    # Insert with ON CONFLICT handling
                    insert_stmt = text(f"""
                        INSERT INTO {table_name} ({','.join(record.keys())})
                        VALUES ({','.join([f':{k}' for k in record.keys()])})
                        ON CONFLICT (parcel_id, county, year)
                        DO UPDATE SET
                            {','.join([f'{k} = EXCLUDED.{k}' for k in record.keys() if k not in ['id', 'parcel_id', 'county', 'year']])}
                    """)

                    for record in batch:
                        conn.execute(insert_stmt, record)

                total_inserted += len(batch)

                # Progress logging
                if total_inserted % 10000 == 0:
                    progress = (total_inserted / total_rows) * 100
                    logger.info(f"Inserted {total_inserted}/{total_rows} records ({progress:.1f}%)")

            except Exception as e:
                logger.error(f"Batch insert error: {e}")
                continue

        return total_inserted

    def load_county_data(self, county: str) -> Dict:
        """Load all data files for a specific county"""

        county_path = self.data_base_path / county.upper()

        if not county_path.exists():
            logger.warning(f"County path not found: {county_path}")
            return {"county": county, "status": "not_found", "records": 0}

        stats = {
            "county": county,
            "files_processed": 0,
            "total_records": 0,
            "errors": []
        }

        # Process each file type
        for file_type in ['NAL', 'NAP', 'NAV', 'SDF']:
            file_pattern = f"{file_type}*.csv"
            files = list(county_path.glob(file_pattern))

            for file_path in files:
                logger.info(f"Processing {county}/{file_type}: {file_path.name}")

                # Load data
                df = self.load_csv_with_pandas(file_path, file_type)

                if not df.empty:
                    # Add county if not present
                    if 'county' not in df.columns:
                        df['county'] = county.upper()

                    # Detect anomalies
                    df = self.detect_anomalies(df)

                    # Insert data
                    inserted = self.batch_insert_data(df)

                    stats["files_processed"] += 1
                    stats["total_records"] += inserted

        stats["status"] = "success" if stats["files_processed"] > 0 else "no_files"
        return stats

    def parallel_load_all_counties(self, max_workers: int = 4):
        """Load data for all counties in parallel"""

        logger.info(f"Starting parallel load for {len(self.florida_counties)} counties")

        all_stats = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all county loads
            future_to_county = {
                executor.submit(self.load_county_data, county): county
                for county in self.florida_counties
            }

            # Process completed futures
            for future in as_completed(future_to_county):
                county = future_to_county[future]
                try:
                    stats = future.result()
                    all_stats.append(stats)
                    logger.info(f"Completed {county}: {stats['total_records']} records")
                except Exception as e:
                    logger.error(f"Failed to load {county}: {e}")
                    all_stats.append({
                        "county": county,
                        "status": "error",
                        "error": str(e)
                    })

        # Generate summary report
        self.generate_load_report(all_stats)

        return all_stats

    def generate_load_report(self, stats: List[Dict]):
        """Generate visualization report of data loading"""

        # Convert to DataFrame for analysis
        df_stats = pd.DataFrame(stats)

        # Create visualizations
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Property Appraiser Data Load Report', fontsize=16)

        # 1. Records by county
        ax1 = axes[0, 0]
        county_records = df_stats[df_stats['status'] == 'success'].sort_values('total_records', ascending=False).head(20)
        sns.barplot(data=county_records, x='total_records', y='county', ax=ax1, palette='viridis')
        ax1.set_title('Top 20 Counties by Record Count')
        ax1.set_xlabel('Total Records')

        # 2. Load status distribution
        ax2 = axes[0, 1]
        status_counts = df_stats['status'].value_counts()
        ax2.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%')
        ax2.set_title('Load Status Distribution')

        # 3. Files processed distribution
        ax3 = axes[1, 0]
        if 'files_processed' in df_stats.columns:
            sns.histplot(data=df_stats[df_stats['files_processed'] > 0], x='files_processed', bins=10, ax=ax3)
            ax3.set_title('Files Processed per County')
            ax3.set_xlabel('Number of Files')
            ax3.set_ylabel('County Count')

        # 4. Summary statistics
        ax4 = axes[1, 1]
        ax4.axis('off')

        total_records = df_stats['total_records'].sum() if 'total_records' in df_stats.columns else 0
        successful_counties = len(df_stats[df_stats['status'] == 'success'])
        failed_counties = len(df_stats[df_stats['status'] != 'success'])

        summary_text = f"""
        Data Load Summary
        ━━━━━━━━━━━━━━━━━
        Total Records: {total_records:,}
        Counties Processed: {successful_counties}/{len(self.florida_counties)}
        Failed Counties: {failed_counties}

        Expected: ~9,700,000 records
        Loaded: {(total_records/9700000)*100:.1f}%
        """

        ax4.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center',
                family='monospace')

        plt.tight_layout()

        # Save report
        report_path = f"property_appraiser_load_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(report_path, dpi=150, bbox_inches='tight')
        logger.info(f"Report saved to {report_path}")

        # Also save as JSON
        json_report = {
            "timestamp": datetime.now().isoformat(),
            "total_records": int(total_records),
            "counties_processed": successful_counties,
            "counties_failed": failed_counties,
            "county_details": stats
        }

        with open(f"property_appraiser_load_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(json_report, f, indent=2, default=str)

        plt.show()

    def create_florida_revenue_monitor(self):
        """Create a monitoring system for Florida Revenue portal updates"""

        monitor_script = '''
import schedule
import time
import hashlib
import json
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

class FloridaRevenueMonitor:
    """Monitor Florida Revenue portal for data updates"""

    def __init__(self):
        self.portal_url = "https://floridarevenue.com/property/dataportal/Pages/default.aspx"
        self.checksums_file = "florida_revenue_checksums.json"
        self.load_checksums()

    def load_checksums(self):
        """Load previous checksums"""
        if Path(self.checksums_file).exists():
            with open(self.checksums_file, 'r') as f:
                self.checksums = json.load(f)
        else:
            self.checksums = {}

    def save_checksums(self):
        """Save current checksums"""
        with open(self.checksums_file, 'w') as f:
            json.dump(self.checksums, f, indent=2)

    def check_for_updates(self):
        """Check Florida Revenue portal for updates"""

        try:
            response = requests.get(self.portal_url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for download links or update indicators
            download_links = soup.find_all('a', href=True)

            updates = []

            for link in download_links:
                if any(county in link.text.upper() for county in ['BROWARD', 'MIAMI-DADE', 'PALM BEACH']):
                    # Calculate checksum of link text and href
                    link_hash = hashlib.md5(f"{link.text}{link['href']}".encode()).hexdigest()

                    if link.text not in self.checksums or self.checksums[link.text] != link_hash:
                        updates.append({
                            "county": link.text,
                            "url": link['href'],
                            "timestamp": datetime.now().isoformat()
                        })
                        self.checksums[link.text] = link_hash

            if updates:
                self.notify_updates(updates)
                self.save_checksums()

            return updates

        except Exception as e:
            print(f"Error checking portal: {e}")
            return []

    def notify_updates(self, updates):
        """Send notifications about updates"""

        for update in updates:
            print(f"[UPDATE] {update['county']}: New data available at {update['timestamp']}")

            # Trigger data download
            # You can add webhook, email, or other notification methods here

    def run_daily_check(self):
        """Run the daily check at 2 AM EST"""
        schedule.every().day.at("02:00").do(self.check_for_updates)

        print("Florida Revenue Monitor started. Checking daily at 2 AM EST...")

        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

if __name__ == "__main__":
    monitor = FloridaRevenueMonitor()
    monitor.run_daily_check()
        '''

        # Save monitor script
        with open("florida_revenue_monitor.py", 'w') as f:
            f.write(monitor_script)

        logger.info("Florida Revenue monitoring system created")

        return True

    def verify_data_integrity(self):
        """Verify data integrity and generate analytics"""

        logger.info("Starting data integrity verification...")

        with self.engine.connect() as conn:
            # Get summary statistics
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT county) as unique_counties,
                    COUNT(DISTINCT parcel_id) as unique_parcels,
                    AVG(just_value) as avg_property_value,
                    MIN(sale_date) as earliest_sale,
                    MAX(sale_date) as latest_sale,
                    SUM(CASE WHEN owner_name IS NULL THEN 1 ELSE 0 END) as null_owners,
                    SUM(CASE WHEN sale_price > 0 THEN 1 ELSE 0 END) as properties_with_sales
                FROM florida_parcels
            """))

            stats = dict(result.fetchone())

            # Check for data quality issues
            issues = []

            if stats['null_owners'] > stats['total_records'] * 0.1:
                issues.append(f"High null owner rate: {stats['null_owners']/stats['total_records']*100:.1f}%")

            if stats['unique_counties'] < 67:
                issues.append(f"Missing counties: {67 - stats['unique_counties']} counties not loaded")

            # Generate integrity report
            report = {
                "timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "issues": issues,
                "data_quality_score": max(0, 100 - len(issues) * 10)
            }

            # Save report
            with open(f"data_integrity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Data integrity check complete. Quality score: {report['data_quality_score']}/100")

            return report

def main():
    """Main execution function"""

    print("\n" + "="*60)
    print("PROPERTY APPRAISER DATABASE DEPLOYMENT")
    print("="*60 + "\n")

    deployer = PropertyAppraiserDeployment()

    # Step 1: Deploy schema
    print("Step 1: Deploying database schema...")
    if deployer.deploy_schema():
        print("✓ Schema deployed successfully")
    else:
        print("✗ Schema deployment failed")
        return

    # Step 2: Load data
    print("\nStep 2: Loading Property Appraiser data...")
    stats = deployer.parallel_load_all_counties()

    total_records = sum(s.get('total_records', 0) for s in stats)
    print(f"✓ Loaded {total_records:,} total records")

    # Step 3: Create monitoring system
    print("\nStep 3: Setting up Florida Revenue monitoring...")
    if deployer.create_florida_revenue_monitor():
        print("✓ Monitoring system created")

    # Step 4: Verify data integrity
    print("\nStep 4: Verifying data integrity...")
    integrity_report = deployer.verify_data_integrity()
    print(f"✓ Data quality score: {integrity_report['data_quality_score']}/100")

    print("\n" + "="*60)
    print("DEPLOYMENT COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()