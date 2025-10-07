"""
Process Florida SDF 2025F (Final) files and import to Supabase property_sales_history table
This script processes the final 2025 SDF CSV files and imports all sales data
"""

import os
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client
import time
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_2025f_sdf.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Path to 2025F SDF data
SDF_BASE_PATH = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\FLORIDA_SDF_2025F")

def test_database_connection():
    """Test database connection"""
    try:
        result = supabase.table('property_sales_history').select('count', count='exact').limit(1).execute()
        logger.info(f"Database connected. Current records: {result.count}")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def parse_sale_date(year, month, day=1):
    """Parse sale date from year/month/day components"""
    try:
        if year and month:
            year = int(year) if year else 0
            month = int(month) if month else 0
            day = int(day) if day and day not in ['0', '00'] else 1

            if 1900 <= year <= 2025 and 1 <= month <= 12 and 1 <= day <= 31:
                # Return components for Supabase to construct the date
                return year, month
    except:
        pass
    return None, None

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if value is None or value == '':
        return default
    try:
        # Remove dollar signs and commas
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '')
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to integer"""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def process_sdf_record(row: Dict, county_name: str, county_no: str) -> List[Dict]:
    """Process a single SDF record and extract all sales"""
    sales = []

    # Get parcel ID
    parcel_id = row.get('PARCEL_ID', '').strip()
    if not parcel_id:
        return sales

    # Get county number - ensure it's a string
    co_no = str(row.get('CO_NO', county_no)).strip()
    if not co_no:
        co_no = county_no

    # Process multiple sales (check for SALE_YR, SALE_YR1, SALE_YR2, etc.)
    # First check if there's a simple SALE_YR field
    if 'SALE_YR' in row and 'SALE_PRC' in row:
        sale_price = safe_int(row.get('SALE_PRC', 0))  # Convert to integer for bigint field
        if sale_price >= 1000:
            sale_year, sale_month = parse_sale_date(
                row.get('SALE_YR'),
                row.get('SALE_MO', 1),
                row.get('SALE_DAY', 1)
            )

            if sale_year:
                sales.append({
                    'parcel_id': parcel_id,
                    'county_no': co_no,
                    'sale_year': sale_year,
                    'sale_month': sale_month,
                    'sale_price': sale_price,  # As integer
                    'or_book': row.get('OR_BOOK', '').strip()[:50],
                    'or_page': row.get('OR_PAGE', '').strip()[:50],
                    'clerk_no': row.get('CLERK_NO', '').strip()[:50],
                    'verification_code': row.get('VI_CD', '').strip()[:10],
                    'sale_id_code': row.get('SALE_ID_CD', '').strip()[:10],
                    'quality_code': row.get('QUAL_CD', '').strip()[:10],
                    'assessment_year': 2025
                })

    # Also check for numbered sales (SALE_YR1, SALE_YR2, etc.)
    for i in range(1, 4):  # Check up to 3 sales
        year_field = f'SALE_YR{i}'
        price_field = f'SALE_PRC{i}'

        if year_field not in row and price_field not in row:
            continue

        sale_price = safe_int(row.get(price_field, 0))  # Convert to integer for bigint field
        if sale_price < 1000:
            continue

        sale_year, sale_month = parse_sale_date(
            row.get(year_field),
            row.get(f'SALE_MO{i}', 1),
            row.get(f'SALE_DAY{i}', 1)
        )

        if sale_year:
            sales.append({
                'parcel_id': parcel_id,
                'county_no': co_no,
                'sale_year': sale_year,
                'sale_month': sale_month,
                'sale_price': sale_price,  # As integer
                'or_book': row.get(f'OR_BOOK{i}', '').strip()[:50],
                'or_page': row.get(f'OR_PAGE{i}', '').strip()[:50],
                'clerk_no': row.get(f'CLERK_NO{i}', '').strip()[:50],
                'verification_code': row.get(f'VI_CD{i}', '').strip()[:10],
                'sale_id_code': row.get(f'SALE_ID_CD{i}', '').strip()[:10],
                'quality_code': row.get(f'QUAL_CD{i}', '').strip()[:10],
                'assessment_year': 2025
            })

    return sales

def bulk_insert_to_supabase(sales_data: List[Dict], batch_size: int = 500):
    """Bulk insert sales data using Supabase client"""
    if not sales_data:
        return 0, 0

    inserted = 0
    errors = 0

    try:
        # Process in batches
        for i in range(0, len(sales_data), batch_size):
            batch = sales_data[i:i + batch_size]

            # Insert batch - use insert without upsert for now
            try:
                response = supabase.table('property_sales_history').insert(batch).execute()
                inserted += len(batch)
            except Exception as e:
                logger.error(f"Batch insert error: {str(e)}")
                errors += len(batch)

                # Try inserting records individually on batch failure
                for record in batch:
                    try:
                        supabase.table('property_sales_history').insert(record).execute()
                        inserted += 1
                        errors -= 1
                    except Exception as ind_error:
                        logger.debug(f"Individual insert failed for {record.get('parcel_id')}: {str(ind_error)}")

        return inserted, errors

    except Exception as e:
        logger.error(f"Bulk insert error: {str(e)}")
        return 0, len(sales_data)

def process_county_sdf(county_path: Path) -> Dict:
    """Process all SDF files for a county"""
    county_name = county_path.name
    stats = {
        'county': county_name,
        'files_processed': 0,
        'records_processed': 0,
        'sales_found': 0,
        'sales_inserted': 0,
        'errors': 0,
        'start_time': datetime.now()
    }

    # Find SDF CSV files
    sdf_path = county_path / "SDF"
    if not sdf_path.exists():
        logger.warning(f"No SDF directory found for {county_name}")
        return stats

    sdf_files = list(sdf_path.glob("*.csv"))
    if not sdf_files:
        sdf_files = list(sdf_path.glob("*.txt"))

    if not sdf_files:
        logger.warning(f"No SDF files found for {county_name}")
        return stats

    # Get county number from filename
    county_no = ""
    if sdf_files:
        filename = sdf_files[0].name
        # Extract county number from filename like SDF6F202501.csv
        if filename.startswith('SDF'):
            county_no = filename[3:].split('F')[0]

    for sdf_file in sdf_files:
        logger.info(f"Processing {county_name}: {sdf_file.name}")

        sales_batch = []

        try:
            # Detect encoding
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(sdf_file, 'r', encoding=encoding) as f:
                        # Detect delimiter
                        first_line = f.readline()
                        delimiter = '\t' if '\t' in first_line else ','
                        f.seek(0)

                        reader = csv.DictReader(f, delimiter=delimiter)

                        for row_num, row in enumerate(reader):
                            # Process record
                            sales = process_sdf_record(row, county_name, county_no)
                            if sales:
                                sales_batch.extend(sales)
                                stats['sales_found'] += len(sales)

                            stats['records_processed'] += 1

                            # Insert in batches
                            if len(sales_batch) >= 2000:
                                inserted, errors = bulk_insert_to_supabase(sales_batch)
                                stats['sales_inserted'] += inserted
                                stats['errors'] += errors
                                sales_batch = []

                            # Progress logging
                            if row_num > 0 and row_num % 10000 == 0:
                                logger.info(f"{county_name}: Processed {row_num:,} records, found {stats['sales_found']:,} sales")

                    break  # Successfully read file
                except UnicodeDecodeError:
                    continue

            # Insert remaining sales
            if sales_batch:
                inserted, errors = bulk_insert_to_supabase(sales_batch)
                stats['sales_inserted'] += inserted
                stats['errors'] += errors

            stats['files_processed'] += 1

        except Exception as e:
            logger.error(f"Error processing {sdf_file}: {str(e)}")
            stats['errors'] += 1

    stats['end_time'] = datetime.now()
    stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()

    logger.info(f"Completed {county_name}: {stats['sales_inserted']:,} sales inserted from {stats['records_processed']:,} records")

    return stats

def main():
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("PROCESSING FLORIDA SDF 2025F (FINAL) FILES")
    logger.info("=" * 80)

    # Test database connection
    if not test_database_connection():
        logger.error("Failed to connect to database")
        return

    # Find all county directories
    county_dirs = [d for d in SDF_BASE_PATH.iterdir() if d.is_dir()]
    logger.info(f"Found {len(county_dirs)} county directories")

    overall_stats = {
        'start_time': datetime.now(),
        'counties_processed': 0,
        'total_records': 0,
        'total_sales_found': 0,
        'total_sales_inserted': 0,
        'total_errors': 0,
        'county_stats': []
    }

    # Process each county
    for county_path in tqdm(county_dirs, desc="Processing counties"):
        logger.info(f"\nProcessing {county_path.name}...")
        stats = process_county_sdf(county_path)

        overall_stats['county_stats'].append(stats)
        overall_stats['counties_processed'] += 1
        overall_stats['total_records'] += stats['records_processed']
        overall_stats['total_sales_found'] += stats['sales_found']
        overall_stats['total_sales_inserted'] += stats['sales_inserted']
        overall_stats['total_errors'] += stats['errors']

    # Calculate final statistics
    overall_stats['end_time'] = datetime.now()
    overall_stats['duration_minutes'] = (overall_stats['end_time'] - overall_stats['start_time']).total_seconds() / 60

    # Log summary
    logger.info("=" * 80)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Counties Processed: {overall_stats['counties_processed']}")
    logger.info(f"Total Records Processed: {overall_stats['total_records']:,}")
    logger.info(f"Total Sales Found: {overall_stats['total_sales_found']:,}")
    logger.info(f"Total Sales Inserted: {overall_stats['total_sales_inserted']:,}")
    logger.info(f"Total Errors: {overall_stats['total_errors']:,}")
    logger.info(f"Duration: {overall_stats['duration_minutes']:.2f} minutes")
    logger.info("=" * 80)

    # Save summary
    summary_file = Path("2025f_sdf_processing_summary.txt")
    with open(summary_file, 'w') as f:
        f.write(f"Florida SDF 2025F Processing Summary\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"=" * 50 + "\n")
        f.write(f"Counties Processed: {overall_stats['counties_processed']}\n")
        f.write(f"Total Records: {overall_stats['total_records']:,}\n")
        f.write(f"Total Sales Found: {overall_stats['total_sales_found']:,}\n")
        f.write(f"Total Sales Inserted: {overall_stats['total_sales_inserted']:,}\n")
        f.write(f"\nCounty Details:\n")
        for stats in overall_stats['county_stats']:
            if stats['sales_inserted'] > 0:
                f.write(f"  {stats['county']}: {stats['sales_inserted']:,} sales from {stats['records_processed']:,} records\n")

    logger.info(f"Summary saved to: {summary_file}")

    return overall_stats

if __name__ == "__main__":
    results = main()