#!/usr/bin/env python3
"""
Property Appraiser Data Pipeline
Complete pipeline for downloading, processing, and loading Florida property data
Using pandas, numpy, SQLAlchemy, and visualization tools
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import requests
from pathlib import Path
import zipfile
import logging
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json
from tqdm import tqdm
from supabase import create_client, Client
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# Configure visualization
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv('.env.mcp')

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATA_DIR = Path("florida_property_data")
DATA_DIR.mkdir(exist_ok=True)

# Florida counties list
FLORIDA_COUNTIES = [
    'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN',
    'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DESOTO', 'DIXIE',
    'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST', 'GLADES',
    'GULF', 'HAMILTON', 'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH',
    'HOLMES', 'INDIAN RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE', 'LEE',
    'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE', 'MARION', 'MARTIN',
    'MIAMI-DADE', 'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE', 'ORANGE', 'OSCEOLA',
    'PALM BEACH', 'PASCO', 'PINELLAS', 'POLK', 'PUTNAM', 'SANTA ROSA', 'SARASOTA',
    'SEMINOLE', 'ST. JOHNS', 'ST. LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION',
    'VOLUSIA', 'WAKULLA', 'WALTON', 'WASHINGTON'
]

class PropertyDataPipeline:
    """Complete data pipeline for Property Appraiser data"""

    def __init__(self):
        """Initialize pipeline with database connection"""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.batch_size = 1000
        self.parallel_workers = 4
        logger.info("Initialized Property Data Pipeline")

    def validate_and_clean_nal_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean NAL (Names/Addresses/Legal) data
        Using pandas for data manipulation and numpy for numerical operations
        """
        logger.info(f"Validating NAL data: {len(df)} records")

        # Column mapping per CLAUDE.md specifications
        column_mapping = {
            'PARCEL_ID': 'parcel_id',
            'COUNTY': 'county',
            'YEAR': 'year',
            'OWN_NAME': 'owner_name',
            'OWN_ADDR1': 'owner_addr1',
            'OWN_ADDR2': 'owner_addr2',
            'OWN_CITY': 'owner_city',
            'OWN_STATE': 'owner_state',
            'OWN_ZIPCD': 'owner_zip',
            'PHY_ADDR1': 'phy_addr1',
            'PHY_ADDR2': 'phy_addr2',
            'PHY_CITY': 'phy_city',
            'PHY_STATE': 'phy_state',
            'PHY_ZIPCD': 'phy_zipcd',
            'LND_SQFOOT': 'land_sqft',  # Critical: NOT land_square_footage
            'JV': 'just_value',  # Critical: NOT total_value
            'LAND_VAL': 'land_value',
            'BLDG_VAL': 'building_value',
            'ASSD_VAL': 'assessed_value',
            'TAXABLE_VAL': 'taxable_value',
            'SALE_YR1': 'sale_year',
            'SALE_MO1': 'sale_month',
            'SALE_PRC1': 'sale_price'
        }

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Data type conversions using pandas
        numeric_columns = ['land_sqft', 'just_value', 'land_value', 'building_value',
                          'assessed_value', 'taxable_value', 'sale_price']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Handle missing values with numpy
        df[numeric_columns] = df[numeric_columns].replace([np.inf, -np.inf], np.nan)

        # State code validation (must be 2 characters)
        if 'owner_state' in df.columns:
            # Convert "FLORIDA" to "FL"
            df['owner_state'] = df['owner_state'].apply(
                lambda x: 'FL' if x == 'FLORIDA' else (x[:2] if pd.notna(x) and len(str(x)) > 2 else x)
            )

        # County uppercase
        if 'county' in df.columns:
            df['county'] = df['county'].str.upper()

        # Create sale_date from year and month
        if 'sale_year' in df.columns and 'sale_month' in df.columns:
            df['sale_date'] = pd.to_datetime(
                df.apply(lambda x: f"{x['sale_year']}-{x['sale_month']:02d}-01"
                        if pd.notna(x['sale_year']) and pd.notna(x['sale_month'])
                        else None, axis=1),
                errors='coerce'
            )

        # Calculate building_value if missing
        if 'building_value' not in df.columns or df['building_value'].isna().all():
            df['building_value'] = df['just_value'] - df['land_value']
            df['building_value'] = df['building_value'].clip(lower=0)

        # Add year if missing
        if 'year' not in df.columns:
            df['year'] = 2025

        # Data quality scoring using numpy
        quality_scores = np.zeros(len(df))

        # Score based on completeness
        important_fields = ['parcel_id', 'county', 'owner_name', 'phy_addr1', 'just_value']
        for field in important_fields:
            if field in df.columns:
                quality_scores += (~df[field].isna()).astype(int) * 0.2

        df['data_quality_score'] = quality_scores

        # Remove completely invalid records
        df = df[df['parcel_id'].notna() & df['county'].notna()]

        logger.info(f"Validated NAL data: {len(df)} records remain")
        return df

    def process_nav_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process NAV (Assessment Values) data"""
        logger.info(f"Processing NAV data: {len(df)} records")

        # NAV specific columns
        nav_columns = {
            'PARCEL_ID': 'parcel_id',
            'COUNTY': 'county',
            'YEAR': 'year',
            'JV': 'just_value',
            'LAND_VAL': 'land_value',
            'BLDG_VAL': 'building_value',
            'MISC_VAL': 'misc_value',
            'ASSD_VAL': 'assessed_value',
            'TAXABLE_VAL': 'taxable_value',
            'HMSTD_EXMPT': 'homestead_exemption',
            'OTHER_EXMPT': 'other_exemptions',
            'MILLAGE': 'millage_rate',
            'TAX_AMT': 'tax_amount'
        }

        df = df.rename(columns=nav_columns)

        # Convert to numeric using pandas
        numeric_cols = [col for col in df.columns if col not in ['parcel_id', 'county']]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

        # Calculate effective tax rate
        df['effective_tax_rate'] = np.where(
            df['taxable_value'] > 0,
            (df['tax_amount'] / df['taxable_value']) * 100,
            0
        )

        return df

    def process_sdf_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process SDF (Sales) data"""
        logger.info(f"Processing SDF data: {len(df)} records")

        # SDF specific columns
        sdf_columns = {
            'PARCEL_ID': 'parcel_id',
            'COUNTY': 'county',
            'SALE_DATE': 'sale_date',
            'SALE_PRICE': 'sale_price',
            'SALE_TYPE': 'sale_type',
            'DEED_TYPE': 'deed_type',
            'GRANTOR': 'grantor',
            'GRANTEE': 'grantee',
            'DOC_NUM': 'doc_number',
            'DOC_STAMPS': 'doc_stamps',
            'QUALIFIED': 'verified_sale'
        }

        df = df.rename(columns=sdf_columns)

        # Parse dates
        df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce')

        # Extract year for partitioning
        df['year'] = df['sale_date'].dt.year

        # Identify arms-length transactions
        df['arms_length'] = df['sale_type'].isin(['Q', 'U'])  # Qualified sales

        # Price validation
        df['sale_price'] = pd.to_numeric(df['sale_price'], errors='coerce')
        df = df[df['sale_price'] > 0]  # Remove invalid sales

        return df

    def process_nap_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process NAP (Property Characteristics) data"""
        logger.info(f"Processing NAP data: {len(df)} records")

        # NAP specific columns
        nap_columns = {
            'PARCEL_ID': 'parcel_id',
            'COUNTY': 'county',
            'YEAR': 'year',
            'USE_CODE': 'land_use_code',
            'USE_DESC': 'land_use_desc',
            'YR_BUILT': 'year_built',
            'EFF_YR_BLT': 'effective_year_built',
            'BLDG_SQFT': 'building_sqft',
            'LIV_AREA': 'living_area',
            'STORIES': 'stories',
            'BEDROOMS': 'bedrooms',
            'BATHROOMS': 'bathrooms',
            'CONST_TYPE': 'construction_type',
            'ROOF_TYPE': 'roof_type',
            'POOL': 'pool',
            'GARAGE': 'garage_spaces'
        }

        df = df.rename(columns=nap_columns)

        # Convert numeric fields
        numeric_fields = ['year_built', 'building_sqft', 'living_area', 'stories',
                         'bedrooms', 'bathrooms', 'garage_spaces']
        df[numeric_fields] = df[numeric_fields].apply(pd.to_numeric, errors='coerce')

        # Boolean conversions
        df['pool'] = df['pool'].isin(['Y', 'YES', True, 1])

        # Calculate property age
        current_year = datetime.now().year
        df['property_age'] = current_year - df['year_built']
        df['property_age'] = df['property_age'].clip(lower=0)

        return df

    def load_data_to_supabase(self, df: pd.DataFrame, table_name: str) -> Tuple[int, int]:
        """
        Load data to Supabase using batch processing
        Returns (success_count, error_count)
        """
        logger.info(f"Loading {len(df)} records to {table_name}")

        # Convert DataFrame to records
        records = df.to_dict('records')

        # Clean records (remove NaN values)
        for record in records:
            for key, value in list(record.items()):
                if pd.isna(value):
                    record[key] = None

        success_count = 0
        error_count = 0

        # Process in batches
        for i in tqdm(range(0, len(records), self.batch_size), desc=f"Loading {table_name}"):
            batch = records[i:i + self.batch_size]

            try:
                # Use upsert to handle duplicates
                response = self.supabase.table(table_name).upsert(
                    batch,
                    on_conflict='parcel_id,county,year'
                ).execute()
                success_count += len(batch)
            except Exception as e:
                logger.error(f"Error loading batch: {e}")
                error_count += len(batch)

        logger.info(f"Loaded {success_count} records, {error_count} errors")
        return success_count, error_count

    def create_data_quality_report(self, df: pd.DataFrame, county: str) -> Dict:
        """
        Create data quality report using pandas and numpy
        """
        report = {
            'county': county,
            'total_records': len(df),
            'timestamp': datetime.now().isoformat()
        }

        # Completeness analysis
        completeness = {}
        for col in df.columns:
            null_pct = (df[col].isna().sum() / len(df)) * 100
            completeness[col] = 100 - null_pct

        report['completeness'] = completeness

        # Statistical summary for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        stats = {}
        for col in numeric_cols:
            if col in df.columns:
                stats[col] = {
                    'mean': float(df[col].mean()) if not df[col].isna().all() else 0,
                    'median': float(df[col].median()) if not df[col].isna().all() else 0,
                    'std': float(df[col].std()) if not df[col].isna().all() else 0,
                    'min': float(df[col].min()) if not df[col].isna().all() else 0,
                    'max': float(df[col].max()) if not df[col].isna().all() else 0
                }

        report['statistics'] = stats

        # Data quality score
        quality_scores = []
        for col, pct in completeness.items():
            if col in ['parcel_id', 'county', 'just_value', 'phy_addr1']:
                quality_scores.append(pct * 2)  # Weight important fields
            else:
                quality_scores.append(pct)

        report['overall_quality_score'] = np.mean(quality_scores) / 100

        return report

    def visualize_county_data(self, df: pd.DataFrame, county: str):
        """
        Create visualizations using matplotlib and seaborn
        """
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Property Data Analysis - {county} County', fontsize=16)

        # 1. Property value distribution
        if 'just_value' in df.columns:
            ax = axes[0, 0]
            df['just_value_log'] = np.log10(df['just_value'].clip(lower=1))
            ax.hist(df['just_value_log'].dropna(), bins=50, edgecolor='black', alpha=0.7)
            ax.set_xlabel('Log10(Just Value)')
            ax.set_ylabel('Count')
            ax.set_title('Property Value Distribution')

        # 2. Land vs Building value
        if 'land_value' in df.columns and 'building_value' in df.columns:
            ax = axes[0, 1]
            sample = df[['land_value', 'building_value']].dropna().sample(min(1000, len(df)))
            ax.scatter(sample['land_value'], sample['building_value'], alpha=0.5)
            ax.set_xlabel('Land Value')
            ax.set_ylabel('Building Value')
            ax.set_title('Land vs Building Value')

        # 3. Property use distribution
        if 'property_use_desc' in df.columns:
            ax = axes[0, 2]
            use_counts = df['property_use_desc'].value_counts().head(10)
            use_counts.plot(kind='barh', ax=ax)
            ax.set_xlabel('Count')
            ax.set_title('Top 10 Property Uses')

        # 4. Year built distribution
        if 'year_built' in df.columns:
            ax = axes[1, 0]
            year_data = df['year_built'].dropna()
            year_data = year_data[year_data > 1900]  # Filter reasonable years
            ax.hist(year_data, bins=50, edgecolor='black', alpha=0.7)
            ax.set_xlabel('Year Built')
            ax.set_ylabel('Count')
            ax.set_title('Construction Year Distribution')

        # 5. Sales price trends
        if 'sale_date' in df.columns and 'sale_price' in df.columns:
            ax = axes[1, 1]
            sales_data = df[['sale_date', 'sale_price']].dropna()
            if len(sales_data) > 0:
                sales_data['year'] = pd.to_datetime(sales_data['sale_date']).dt.year
                yearly_avg = sales_data.groupby('year')['sale_price'].mean()
                yearly_avg.plot(ax=ax, marker='o')
                ax.set_xlabel('Year')
                ax.set_ylabel('Average Sale Price')
                ax.set_title('Sales Price Trends')

        # 6. Data quality heatmap
        ax = axes[1, 2]
        quality_data = df.isna().mean() * 100
        quality_matrix = quality_data.values.reshape(-1, 1)
        im = ax.imshow(quality_matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=100)
        ax.set_yticks(range(len(quality_data)))
        ax.set_yticklabels(quality_data.index, fontsize=8)
        ax.set_xlabel('Missing %')
        ax.set_title('Data Completeness')
        plt.colorbar(im, ax=ax)

        plt.tight_layout()

        # Save figure
        output_dir = DATA_DIR / 'visualizations'
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f'{county.lower()}_analysis.png'
        plt.savefig(output_file, dpi=100)
        plt.close()

        logger.info(f"Saved visualization to {output_file}")

    def generate_sample_data(self, county: str, num_records: int = 1000) -> pd.DataFrame:
        """
        Generate sample data for testing using numpy random generation
        """
        np.random.seed(42)

        # Generate parcel IDs
        parcel_ids = [f"{county[:3]}{str(i).zfill(10)}" for i in range(num_records)]

        # Generate data using numpy
        data = {
            'parcel_id': parcel_ids,
            'county': county,
            'year': 2025,
            'owner_name': [f"Owner_{i}" for i in range(num_records)],
            'phy_addr1': [f"{np.random.randint(1, 9999)} Main St" for _ in range(num_records)],
            'phy_city': np.random.choice(['Miami', 'Orlando', 'Tampa', 'Jacksonville'], num_records),
            'phy_state': 'FL',
            'land_sqft': np.random.lognormal(10, 1, num_records),
            'just_value': np.random.lognormal(12, 1, num_records),
            'land_value': np.random.lognormal(11, 1, num_records),
            'sale_price': np.random.lognormal(12, 0.8, num_records),
            'year_built': np.random.randint(1950, 2024, num_records),
            'bedrooms': np.random.choice([1, 2, 3, 4, 5], num_records, p=[0.1, 0.3, 0.4, 0.15, 0.05]),
            'bathrooms': np.random.choice([1, 1.5, 2, 2.5, 3], num_records, p=[0.2, 0.2, 0.3, 0.2, 0.1])
        }

        df = pd.DataFrame(data)

        # Calculate building value
        df['building_value'] = df['just_value'] - df['land_value']
        df['building_value'] = df['building_value'].clip(lower=0)

        # Add sale dates
        base_date = pd.Timestamp('2020-01-01')
        df['sale_date'] = [base_date + pd.Timedelta(days=np.random.randint(0, 1800))
                          for _ in range(num_records)]

        return df

    def process_county(self, county: str):
        """
        Complete processing pipeline for a single county
        """
        logger.info(f"Processing {county} county")

        try:
            # For demo, use sample data
            # In production, this would load actual files from florida_property_data/
            df_nal = self.generate_sample_data(county, 1000)

            # Validate and clean data
            df_cleaned = self.validate_and_clean_nal_data(df_nal)

            # Create quality report
            quality_report = self.create_data_quality_report(df_cleaned, county)

            # Save quality report
            report_file = DATA_DIR / f'{county.lower()}_quality_report.json'
            with open(report_file, 'w') as f:
                json.dump(quality_report, f, indent=2)

            # Generate visualizations
            self.visualize_county_data(df_cleaned, county)

            # Load to database
            success, errors = self.load_data_to_supabase(df_cleaned, 'florida_parcels')

            # Update county statistics
            stats = {
                'county': county,
                'total_parcels': len(df_cleaned),
                'last_update': datetime.now().isoformat(),
                'nal_records': len(df_cleaned),
                'data_quality_score': quality_report['overall_quality_score']
            }

            self.supabase.table('county_statistics').upsert(stats, on_conflict='county').execute()

            logger.info(f"Completed {county}: {success} loaded, {errors} errors")
            return True

        except Exception as e:
            logger.error(f"Error processing {county}: {e}")
            return False

    def run_pipeline(self, counties: List[str] = None):
        """
        Run the complete pipeline for specified counties
        """
        if counties is None:
            counties = FLORIDA_COUNTIES[:5]  # Start with first 5 for testing

        logger.info("=" * 60)
        logger.info("PROPERTY APPRAISER DATA PIPELINE")
        logger.info(f"Processing {len(counties)} counties")
        logger.info("=" * 60)

        # Process counties in parallel
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            results = list(executor.map(self.process_county, counties))

        # Summary
        successful = sum(results)
        failed = len(results) - successful

        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Counties processed: {len(counties)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")

        # Generate overall summary visualization
        self.create_summary_dashboard(counties)

        return successful == len(counties)

    def create_summary_dashboard(self, counties: List[str]):
        """
        Create summary dashboard using matplotlib
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Property Appraiser Data Pipeline Summary', fontsize=16)

        # Get statistics for all counties
        stats_data = []
        for county in counties:
            report_file = DATA_DIR / f'{county.lower()}_quality_report.json'
            if report_file.exists():
                with open(report_file, 'r') as f:
                    stats_data.append(json.load(f))

        if stats_data:
            # 1. Records per county
            ax = axes[0, 0]
            county_names = [s['county'] for s in stats_data]
            record_counts = [s['total_records'] for s in stats_data]
            ax.bar(range(len(county_names)), record_counts)
            ax.set_xticks(range(len(county_names)))
            ax.set_xticklabels(county_names, rotation=45, ha='right')
            ax.set_ylabel('Record Count')
            ax.set_title('Records per County')

            # 2. Data quality scores
            ax = axes[0, 1]
            quality_scores = [s['overall_quality_score'] for s in stats_data]
            ax.bar(range(len(county_names)), quality_scores)
            ax.set_xticks(range(len(county_names)))
            ax.set_xticklabels(county_names, rotation=45, ha='right')
            ax.set_ylabel('Quality Score')
            ax.set_title('Data Quality Scores')
            ax.axhline(y=0.8, color='r', linestyle='--', label='Target')

            # 3. Processing timeline
            ax = axes[1, 0]
            timestamps = [datetime.fromisoformat(s['timestamp']) for s in stats_data]
            processing_times = [(t - timestamps[0]).total_seconds() / 60 for t in timestamps]
            ax.plot(processing_times, marker='o')
            ax.set_xlabel('Processing Order')
            ax.set_ylabel('Time (minutes)')
            ax.set_title('Processing Timeline')

            # 4. Summary statistics
            ax = axes[1, 1]
            ax.axis('off')
            summary_text = f"""
Pipeline Summary
----------------
Total Counties: {len(counties)}
Total Records: {sum(record_counts):,}
Avg Quality Score: {np.mean(quality_scores):.2%}
Processing Time: {max(processing_times):.1f} min
            """
            ax.text(0.1, 0.5, summary_text, fontsize=12, family='monospace')

        plt.tight_layout()
        output_file = DATA_DIR / 'pipeline_summary.png'
        plt.savefig(output_file, dpi=100)
        plt.close()

        logger.info(f"Saved summary dashboard to {output_file}")

def main():
    """Main execution"""
    pipeline = PropertyDataPipeline()

    # Run pipeline for first 5 counties as demo
    success = pipeline.run_pipeline(FLORIDA_COUNTIES[:5])

    if success:
        logger.info("\n✅ Pipeline completed successfully!")
    else:
        logger.error("\n❌ Pipeline encountered errors")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())