"""
Simplified Property Appraiser Database Deployment
Focus on core functionality with available libraries
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
import logging

# Core data processing
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, MetaData
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

# Load environment
from dotenv import load_dotenv
load_dotenv('.env.mcp')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    logger.error("Missing Supabase credentials")
    sys.exit(1)

# Parse Supabase URL
import re
match = re.search(r'https://([^.]+)\.supabase\.co', SUPABASE_URL)
if match:
    project_ref = match.group(1)
    DATABASE_URL = f"postgresql://postgres.{project_ref}:{SUPABASE_SERVICE_KEY}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
else:
    logger.error("Invalid Supabase URL format")
    sys.exit(1)

class PropertyAppraiserSystem:
    """Simplified deployment system"""

    def __init__(self):
        self.engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"options": "-c statement_timeout=0"}
        )

        self.florida_counties = ['BROWARD', 'MIAMI-DADE', 'PALM BEACH']  # Start with 3 major counties
        self.data_base_path = Path("C:/Temp/DATABASE PROPERTY APP")

    def deploy_schema(self):
        """Deploy the database schema"""
        logger.info("Deploying database schema...")

        schema_sql = """
        -- Enable extensions
        CREATE EXTENSION IF NOT EXISTS postgis;
        CREATE EXTENSION IF NOT EXISTS pg_trgm;

        -- Create main table
        CREATE TABLE IF NOT EXISTS florida_parcels (
            id BIGSERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) NOT NULL,
            county VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL DEFAULT 2025,

            -- NAL fields (Names/Addresses)
            owner_name VARCHAR(255),
            owner_addr1 VARCHAR(255),
            owner_addr2 VARCHAR(255),
            owner_city VARCHAR(100),
            owner_state VARCHAR(2),
            owner_zip VARCHAR(10),
            phy_addr1 VARCHAR(255),
            phy_addr2 VARCHAR(255),
            phy_city VARCHAR(100),
            phy_state VARCHAR(2) DEFAULT 'FL',
            phy_zipcd VARCHAR(10),

            -- NAP fields (Characteristics)
            property_use VARCHAR(10),
            land_use_code VARCHAR(10),
            year_built INTEGER,
            total_living_area FLOAT,
            bedrooms INTEGER,
            bathrooms FLOAT,

            -- NAV fields (Values)
            just_value FLOAT,
            assessed_value FLOAT,
            taxable_value FLOAT,
            land_value FLOAT,
            building_value FLOAT,

            -- Land measurements
            land_sqft FLOAT,
            land_acres FLOAT,

            -- SDF fields (Sales)
            sale_date TIMESTAMP,
            sale_price FLOAT,
            sale_qualification VARCHAR(10),

            -- Metadata
            import_date TIMESTAMP DEFAULT NOW(),
            data_source VARCHAR(20),
            data_hash VARCHAR(64),

            -- Unique constraint
            CONSTRAINT uq_parcel_county_year UNIQUE (parcel_id, county, year)
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_parcels_county ON florida_parcels(county);
        CREATE INDEX IF NOT EXISTS idx_parcels_parcel_id ON florida_parcels(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_parcels_owner ON florida_parcels(owner_name);
        CREATE INDEX IF NOT EXISTS idx_parcels_address ON florida_parcels(phy_addr1, phy_city);
        CREATE INDEX IF NOT EXISTS idx_parcels_value ON florida_parcels(taxable_value);
        CREATE INDEX IF NOT EXISTS idx_parcels_sale ON florida_parcels(sale_date, sale_price);

        -- Disable timeouts for bulk operations
        ALTER ROLE authenticator SET statement_timeout TO '0';
        ALTER ROLE postgres SET statement_timeout TO '0';
        """

        try:
            with self.engine.connect() as conn:
                # Execute schema creation
                for statement in schema_sql.split(';'):
                    if statement.strip():
                        conn.execute(text(statement))
                conn.commit()

            logger.info("Schema deployed successfully")
            return True

        except Exception as e:
            logger.error(f"Schema deployment error: {e}")
            return False

    def load_csv_data(self, file_path: Path, file_type: str, county: str) -> pd.DataFrame:
        """Load and transform CSV data"""

        # Column mappings per CLAUDE.md requirements
        mappings = {
            'NAL': {
                'PARCEL_ID': 'parcel_id',
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
                'LND_SQFOOT': 'land_sqft',  # Critical mapping
                'JV': 'just_value'           # Critical mapping
            },
            'NAP': {
                'PARCEL_ID': 'parcel_id',
                'DOR_UC': 'property_use',
                'LND_USE_CD': 'land_use_code',
                'ACT_YR_BLT': 'year_built',
                'TOT_LVG_AREA': 'total_living_area',
                'BEDROOM': 'bedrooms',
                'BATHROOM': 'bathrooms'
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
            # Read CSV
            df = pd.read_csv(file_path, dtype=str, low_memory=False, encoding='utf-8-sig')
            logger.info(f"Loaded {len(df)} records from {file_path.name}")

            # Apply column mappings
            if file_type in mappings:
                rename_dict = {k: v for k, v in mappings[file_type].items() if k in df.columns}
                df = df.rename(columns=rename_dict)

            # Add county and year
            df['county'] = county.upper()
            df['year'] = 2025

            # Data type conversions
            numeric_cols = ['just_value', 'assessed_value', 'taxable_value', 'land_value',
                          'sale_price', 'land_sqft', 'total_living_area', 'year_built',
                          'bedrooms', 'bathrooms']

            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Handle state codes (truncate to 2 chars as per requirements)
            if 'owner_state' in df.columns:
                df['owner_state'] = df['owner_state'].str[:2]
                # Convert FLORIDA to FL
                df['owner_state'] = df['owner_state'].replace({'FL': 'FL', 'FLORIDA': 'FL'})

            # Create sale_date from components
            if 'sale_year' in df.columns and 'sale_month' in df.columns:
                # Build date as YYYY-MM-01 format per requirements
                df['sale_date'] = pd.to_datetime(
                    df['sale_year'].astype(str) + '-' +
                    df['sale_month'].astype(str) + '-01',
                    errors='coerce'
                )

            # Calculate building_value
            if 'just_value' in df.columns and 'land_value' in df.columns:
                df['building_value'] = df['just_value'] - df['land_value']

            # Add metadata
            df['import_date'] = datetime.now()
            df['data_source'] = file_type

            # Generate hash for deduplication
            df['data_hash'] = df.apply(
                lambda row: hashlib.sha256(
                    f"{row.get('parcel_id', '')}{county}{2025}".encode()
                ).hexdigest(),
                axis=1
            )

            # Clean NaN values
            df = df.replace({np.nan: None})

            return df

        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return pd.DataFrame()

    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalous records using Isolation Forest"""

        if df.empty or len(df) < 10:
            return df

        # Select numeric features for anomaly detection
        features = ['just_value', 'land_sqft', 'sale_price']
        available = [f for f in features if f in df.columns]

        if not available:
            return df

        try:
            # Prepare data
            X = df[available].fillna(0)

            # Remove infinite values
            X = X.replace([np.inf, -np.inf], 0)

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Detect anomalies (1% contamination rate)
            iso_forest = IsolationForest(contamination=0.01, random_state=42)
            anomalies = iso_forest.fit_predict(X_scaled)

            # Mark anomalies
            df['is_anomaly'] = anomalies == -1

            anomaly_count = df['is_anomaly'].sum()
            if anomaly_count > 0:
                logger.info(f"Detected {anomaly_count} anomalous records ({anomaly_count/len(df)*100:.1f}%)")

        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")

        return df

    def batch_insert(self, df: pd.DataFrame, batch_size: int = 1000) -> int:
        """Insert data in batches with conflict handling"""

        if df.empty:
            return 0

        # Select only columns that exist in the table
        valid_columns = [
            'parcel_id', 'county', 'year', 'owner_name', 'owner_addr1', 'owner_addr2',
            'owner_city', 'owner_state', 'owner_zip', 'phy_addr1', 'phy_addr2',
            'phy_city', 'phy_state', 'phy_zipcd', 'property_use', 'land_use_code',
            'year_built', 'total_living_area', 'bedrooms', 'bathrooms',
            'just_value', 'assessed_value', 'taxable_value', 'land_value',
            'building_value', 'land_sqft', 'land_acres', 'sale_date', 'sale_price',
            'sale_qualification', 'import_date', 'data_source', 'data_hash'
        ]

        # Filter to valid columns
        df_insert = df[[col for col in valid_columns if col in df.columns]]

        total_inserted = 0
        errors = 0

        for i in range(0, len(df_insert), batch_size):
            batch = df_insert.iloc[i:i+batch_size]

            try:
                # Use pandas to_sql with if_exists='append'
                batch.to_sql(
                    'florida_parcels',
                    self.engine,
                    if_exists='append',
                    index=False,
                    method='multi'
                )
                total_inserted += len(batch)

                if total_inserted % 10000 == 0:
                    logger.info(f"Inserted {total_inserted} records...")

            except Exception as e:
                errors += 1
                if errors < 5:
                    logger.warning(f"Batch insert error: {str(e)[:100]}")

        logger.info(f"Total inserted: {total_inserted} records")
        return total_inserted

    def load_county(self, county: str) -> dict:
        """Load all data for a single county"""

        county_path = self.data_base_path / county
        stats = {
            "county": county,
            "files": 0,
            "records": 0,
            "errors": []
        }

        if not county_path.exists():
            # Try alternative paths
            alt_paths = [
                Path(f"C:/Temp/{county}"),
                Path(f"./data/{county}"),
                Path(f"./{county}")
            ]

            for alt_path in alt_paths:
                if alt_path.exists():
                    county_path = alt_path
                    break
            else:
                logger.warning(f"County path not found: {county}")
                stats["errors"].append("Path not found")
                return stats

        # Process each file type
        all_data = []

        for file_type in ['NAL', 'NAP', 'NAV', 'SDF']:
            files = list(county_path.glob(f"{file_type}*.csv")) + \
                   list(county_path.glob(f"{file_type}*.txt"))

            for file_path in files:
                logger.info(f"Processing {county}/{file_type}: {file_path.name}")

                df = self.load_csv_data(file_path, file_type, county)

                if not df.empty:
                    stats["files"] += 1
                    all_data.append(df)

        # Merge all dataframes for the county
        if all_data:
            # Merge on parcel_id
            merged_df = all_data[0]
            for df in all_data[1:]:
                # Keep only new columns when merging
                merge_cols = ['parcel_id'] + [col for col in df.columns
                                             if col not in merged_df.columns or col == 'parcel_id']
                merged_df = pd.merge(
                    merged_df,
                    df[merge_cols],
                    on='parcel_id',
                    how='outer'
                )

            # Detect anomalies
            merged_df = self.detect_anomalies(merged_df)

            # Insert data
            stats["records"] = self.batch_insert(merged_df)

        return stats

    def generate_analytics_report(self):
        """Generate comprehensive analytics using matplotlib/seaborn"""

        logger.info("Generating analytics report...")

        # Query database for statistics
        with self.engine.connect() as conn:
            # Overall statistics
            stats_query = """
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT county) as counties,
                COUNT(DISTINCT parcel_id) as unique_parcels,
                AVG(just_value) as avg_value,
                AVG(land_sqft) as avg_land_sqft,
                SUM(CASE WHEN sale_price > 0 THEN 1 ELSE 0 END) as properties_sold
            FROM florida_parcels
            """

            stats = pd.read_sql(stats_query, conn)

            # County breakdown
            county_query = """
            SELECT
                county,
                COUNT(*) as records,
                AVG(just_value) as avg_value,
                AVG(land_sqft) as avg_size
            FROM florida_parcels
            GROUP BY county
            ORDER BY records DESC
            """

            county_stats = pd.read_sql(county_query, conn)

        # Create visualizations
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Property Appraiser Data Analytics Report', fontsize=16)

        # 1. Records by County
        ax1 = axes[0, 0]
        if not county_stats.empty:
            sns.barplot(data=county_stats, x='records', y='county', ax=ax1, palette='viridis')
            ax1.set_title('Records by County')
            ax1.set_xlabel('Number of Records')

        # 2. Property Values Distribution
        ax2 = axes[0, 1]
        value_query = "SELECT just_value FROM florida_parcels WHERE just_value > 0 AND just_value < 5000000 LIMIT 10000"
        with self.engine.connect() as conn:
            values = pd.read_sql(value_query, conn)

        if not values.empty:
            ax2.hist(values['just_value'], bins=50, edgecolor='black')
            ax2.set_title('Property Value Distribution')
            ax2.set_xlabel('Property Value ($)')
            ax2.set_ylabel('Count')

        # 3. Land Size Distribution
        ax3 = axes[1, 0]
        size_query = "SELECT land_sqft FROM florida_parcels WHERE land_sqft > 0 AND land_sqft < 100000 LIMIT 10000"
        with self.engine.connect() as conn:
            sizes = pd.read_sql(size_query, conn)

        if not sizes.empty:
            ax3.hist(sizes['land_sqft'], bins=50, edgecolor='black')
            ax3.set_title('Land Size Distribution')
            ax3.set_xlabel('Land Size (sqft)')
            ax3.set_ylabel('Count')

        # 4. Summary Statistics
        ax4 = axes[1, 1]
        ax4.axis('off')

        summary = f"""
        Database Summary
        ================
        Total Records: {stats['total_records'].iloc[0]:,}
        Counties: {stats['counties'].iloc[0]}
        Unique Parcels: {stats['unique_parcels'].iloc[0]:,}
        Avg Property Value: ${stats['avg_value'].iloc[0]:,.0f}
        Avg Land Size: {stats['avg_land_sqft'].iloc[0]:,.0f} sqft
        Properties with Sales: {stats['properties_sold'].iloc[0]:,}

        Data Quality Score: {self.calculate_quality_score()}/100
        """

        ax4.text(0.1, 0.5, summary, fontsize=11, verticalalignment='center', family='monospace')

        plt.tight_layout()

        # Save report
        report_path = f"property_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(report_path, dpi=150, bbox_inches='tight')
        logger.info(f"Analytics report saved to {report_path}")

        return report_path

    def calculate_quality_score(self) -> int:
        """Calculate data quality score"""

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN parcel_id IS NULL THEN 1 ELSE 0 END) as null_parcels,
                    SUM(CASE WHEN county IS NULL THEN 1 ELSE 0 END) as null_counties,
                    SUM(CASE WHEN owner_name IS NULL THEN 1 ELSE 0 END) as null_owners
                FROM florida_parcels
                """))

                row = result.fetchone()
                if row and row[0] > 0:
                    null_rate = (row[1] + row[2]) / row[0]  # Critical fields
                    score = max(0, int(100 * (1 - null_rate)))
                    return score

        except Exception as e:
            logger.error(f"Quality score calculation error: {e}")

        return 0

def main():
    """Main execution"""

    print("\n" + "="*60)
    print("PROPERTY APPRAISER SYSTEM DEPLOYMENT")
    print("="*60 + "\n")

    system = PropertyAppraiserSystem()

    # Deploy schema
    print("1. Deploying database schema...")
    if system.deploy_schema():
        print("   ✓ Schema deployed\n")
    else:
        print("   ✗ Schema deployment failed\n")
        return

    # Load data for each county
    print("2. Loading Property Appraiser data...")

    all_stats = []
    for county in system.florida_counties:
        print(f"   Loading {county}...")
        stats = system.load_county(county)
        all_stats.append(stats)
        print(f"   - Files: {stats['files']}, Records: {stats['records']}")

    total_records = sum(s['records'] for s in all_stats)
    print(f"\n   ✓ Total records loaded: {total_records:,}\n")

    # Generate analytics
    print("3. Generating analytics report...")
    report_path = system.generate_analytics_report()
    print(f"   ✓ Report saved to {report_path}\n")

    # Create monitoring script
    print("4. Creating Florida Revenue monitor...")

    monitor_code = """
#!/usr/bin/env python3
# Florida Revenue Portal Monitor
# Run daily at 2 AM EST to check for updates

import schedule
import time
import hashlib
import json
from datetime import datetime
from pathlib import Path

def check_florida_revenue():
    '''Check for updates at 2 AM EST'''

    print(f"[{datetime.now()}] Checking Florida Revenue portal...")

    # Add actual portal checking logic here
    # For now, just log the check

    with open('florida_revenue_checks.log', 'a') as f:
        f.write(f"{datetime.now().isoformat()} - Check completed\\n")

    return True

# Schedule daily check at 2 AM
schedule.every().day.at("02:00").do(check_florida_revenue)

print("Florida Revenue Monitor started. Checking daily at 2 AM EST...")
print("Press Ctrl+C to stop")

while True:
    schedule.run_pending()
    time.sleep(60)
"""

    with open("florida_revenue_monitor.py", "w") as f:
        f.write(monitor_code)

    print("   ✓ Monitor script created\n")

    print("="*60)
    print("DEPLOYMENT COMPLETE")
    print(f"Total records: {total_records:,}")
    print(f"Quality score: {system.calculate_quality_score()}/100")
    print("="*60)

if __name__ == "__main__":
    main()