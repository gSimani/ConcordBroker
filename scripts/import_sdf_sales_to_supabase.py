"""
Import SDF sales data from local files to Supabase property_sales_history table
"""

import os
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Path to SDF data
SDF_BASE_PATH = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")

# County code mapping
COUNTY_CODES = {
    '13': 'MIAMI-DADE',
    '06': 'BROWARD',
    '50': 'PALM BEACH',
    '29': 'HILLSBOROUGH',
    '48': 'ORANGE',
    '52': 'PINELLAS',
    '17': 'DUVAL',
    '35': 'LEE',
    '53': 'POLK',
    '08': 'CHARLOTTE'
}

def parse_sale_date(year, month, day=1):
    """Parse sale date from year/month/day components"""
    try:
        if year and month:
            year = int(year) if year else 0
            month = int(month) if month else 0
            day = int(day) if day and day not in ['0', '00'] else 1

            if 1900 <= year <= 2025 and 1 <= month <= 12 and 1 <= day <= 31:
                return f"{year:04d}-{month:02d}-{day:02d}"
    except:
        pass
    return None

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def process_sdf_record(row: Dict, county_no: str) -> Optional[List[Dict]]:
    """Process a single SDF record into database format"""
    try:
        # Parse multiple sales (up to 3)
        sales = []

        # Get parcel ID
        parcel_id = row.get('PARCEL_ID', '').strip()
        if not parcel_id:
            return None

        # Also check for non-numbered sale (SALE_YR, SALE_PRC)
        if 'SALE_YR' in row and 'SALE_PRC' in row:
            sale_price = safe_float(row.get('SALE_PRC', 0))
            if sale_price >= 1000:
                sale_date = parse_sale_date(
                    row.get('SALE_YR'),
                    row.get('SALE_MO', 1),
                    row.get('SALE_DAY', 1)
                )
                if sale_date:
                    quality_code = row.get('VI_CD', '')
                    sales.append({
                        'parcel_id': parcel_id,
                        'county_no': county_no,
                        'sale_date': sale_date,
                        'sale_year': int(row.get('SALE_YR', 0) or 0),
                        'sale_month': int(row.get('SALE_MO', 0) or 0),
                        'sale_price': sale_price,
                        'or_book': row.get('OR_BOOK', '').strip()[:50],
                        'or_page': row.get('OR_PAGE', '').strip()[:50],
                        'clerk_no': row.get('CLERK_NO', '').strip()[:50],
                        'verification_code': quality_code[:10] if quality_code else '',
                        'quality_code': row.get('QUAL_CD', '').strip()[:10],
                        'sale_id_code': row.get('SALE_ID_CD', '').strip()[:10],
                        'assessment_year': 2025
                    })

        # Check numbered sales
        for i in range(1, 4):  # Check SALE_PRC1, SALE_PRC2, SALE_PRC3
            price_field = f'SALE_PRC{i}'
            year_field = f'SALE_YR{i}'
            month_field = f'SALE_MO{i}'

            if price_field not in row:
                continue

            sale_price = safe_float(row.get(price_field, 0))

            # Skip if no valid sale price or price too low
            if sale_price < 1000:
                continue

            # Parse sale date
            sale_date = parse_sale_date(
                row.get(year_field),
                row.get(month_field),
                row.get(f'SALE_DAY{i}', 1)
            )

            # Skip if no valid sale date
            if not sale_date:
                continue

            # Quality code
            quality_code = row.get(f'VI_CD{i}', '')

            sale_record = {
                'parcel_id': parcel_id,
                'county_no': county_no,
                'sale_date': sale_date,
                'sale_year': int(row.get(year_field, 0) or 0),
                'sale_month': int(row.get(month_field, 0) or 0),
                'sale_price': sale_price,
                'or_book': row.get(f'OR_BOOK{i}', '').strip()[:50],
                'or_page': row.get(f'OR_PAGE{i}', '').strip()[:50],
                'clerk_no': row.get(f'CLERK_NO{i}', '').strip()[:50],
                'verification_code': quality_code[:10] if quality_code else '',
                'quality_code': row.get(f'QUAL_CD{i}', '').strip()[:10],
                'sale_id_code': row.get(f'SALE_ID_CD{i}', '').strip()[:10],
                'assessment_year': 2025
            }

            sales.append(sale_record)

        return sales if sales else None

    except Exception as e:
        logger.error(f"Error processing SDF record: {str(e)}")
        return None

def batch_insert_sales(sales_data: List[Dict], batch_size: int = 500):
    """Batch insert sales data into Supabase"""
    total_records = len(sales_data)
    inserted = 0
    errors = 0

    logger.info(f"Inserting {total_records} sales records...")

    for i in range(0, total_records, batch_size):
        batch = sales_data[i:i + batch_size]

        try:
            # Insert batch - note the table already exists
            response = supabase.table('property_sales_history').insert(batch).execute()
            inserted += len(batch)

            if i % 5000 == 0:
                logger.info(f"Progress: {inserted}/{total_records} records inserted")

        except Exception as e:
            logger.error(f"Batch insert error: {str(e)}")
            errors += len(batch)

            # Try inserting records individually on batch failure
            for record in batch:
                try:
                    supabase.table('property_sales_history').insert(record).execute()
                    inserted += 1
                    errors -= 1
                except Exception as individual_error:
                    logger.debug(f"Individual insert failed: {individual_error}")

        # Add small delay to avoid rate limiting
        if i % 10000 == 0:
            time.sleep(1)

    logger.info(f"Insertion complete: {inserted} successful, {errors} errors")
    return inserted, errors

def process_county_sdf(county_no: str, county_name: str) -> Dict:
    """Process SDF file for a single county"""
    stats = {
        'county': county_name,
        'county_no': county_no,
        'status': 'pending',
        'records_processed': 0,
        'records_inserted': 0,
        'errors': 0,
        'start_time': datetime.now()
    }

    try:
        # Find SDF file for this county
        county_path = SDF_BASE_PATH / county_name / "SDF"
        if not county_path.exists():
            # Try alternate naming
            county_path = SDF_BASE_PATH / county_name.replace('-', '_') / "SDF"
            if not county_path.exists():
                county_path = SDF_BASE_PATH / county_name.replace('-', '') / "SDF"

        if not county_path.exists():
            logger.warning(f"SDF directory not found for {county_name} at {county_path}")
            stats['status'] = 'directory_not_found'
            return stats

        # Find CSV file
        csv_files = list(county_path.glob("*.csv"))
        if not csv_files:
            csv_files = list(county_path.glob("*.txt"))  # Some might be .txt

        if not csv_files:
            logger.warning(f"No CSV files found in {county_path}")
            stats['status'] = 'no_csv_found'
            return stats

        csv_file = csv_files[0]
        logger.info(f"Processing {county_name} SDF data from {csv_file}")

        sales_data = []

        # Read CSV with proper encoding
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            # Try to detect delimiter
            first_line = f.readline()
            f.seek(0)

            delimiter = '\t' if '\t' in first_line else ','
            reader = csv.DictReader(f, delimiter=delimiter)

            for row in reader:
                sales = process_sdf_record(row, county_no)
                if sales:
                    sales_data.extend(sales)
                stats['records_processed'] += 1

                # Insert in batches
                if len(sales_data) >= 2000:
                    inserted, errors = batch_insert_sales(sales_data)
                    stats['records_inserted'] += inserted
                    stats['errors'] += errors
                    sales_data = []

                # Log progress
                if stats['records_processed'] % 10000 == 0:
                    logger.info(f"{county_name}: Processed {stats['records_processed']} records")

        # Insert remaining records
        if sales_data:
            inserted, errors = batch_insert_sales(sales_data)
            stats['records_inserted'] += inserted
            stats['errors'] += errors

        stats['status'] = 'completed'
        stats['end_time'] = datetime.now()
        stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()

        logger.info(f"Completed {county_name}: {stats['records_inserted']} sales records inserted")

    except Exception as e:
        logger.error(f"Error processing {county_name}: {str(e)}")
        stats['status'] = 'error'
        stats['error_message'] = str(e)

    return stats

def main():
    """Main function to import sales data"""
    logger.info("=" * 80)
    logger.info("FLORIDA SALES HISTORY IMPORT FROM LOCAL SDF FILES")
    logger.info("=" * 80)

    # Start with major counties
    priority_counties = [
        ('13', 'MIAMI-DADE'),
        ('06', 'BROWARD'),
        ('50', 'PALM BEACH'),
        ('29', 'HILLSBOROUGH'),
        ('48', 'ORANGE')
    ]

    overall_stats = {
        'start_time': datetime.now(),
        'counties_processed': 0,
        'counties_failed': 0,
        'total_records': 0,
        'total_errors': 0,
        'county_stats': []
    }

    # Process each county
    for county_no, county_name in priority_counties:
        logger.info(f"\nProcessing {county_name} (County #{county_no})...")
        stats = process_county_sdf(county_no, county_name)
        overall_stats['county_stats'].append(stats)

        if stats['status'] == 'completed':
            overall_stats['counties_processed'] += 1
            overall_stats['total_records'] += stats['records_inserted']
            overall_stats['total_errors'] += stats['errors']
        else:
            overall_stats['counties_failed'] += 1

        # Log progress
        logger.info(f"Progress: {overall_stats['counties_processed'] + overall_stats['counties_failed']}/{len(priority_counties)} counties")

    # Final statistics
    overall_stats['end_time'] = datetime.now()
    overall_stats['duration_minutes'] = (overall_stats['end_time'] - overall_stats['start_time']).total_seconds() / 60

    # Log summary
    logger.info("=" * 80)
    logger.info("IMPORT COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Counties Processed: {overall_stats['counties_processed']}/{len(priority_counties)}")
    logger.info(f"Counties Failed: {overall_stats['counties_failed']}")
    logger.info(f"Total Sales Records Imported: {overall_stats['total_records']:,}")
    logger.info(f"Total Errors: {overall_stats['total_errors']:,}")
    logger.info(f"Duration: {overall_stats['duration_minutes']:.2f} minutes")

    # Log county details
    logger.info("\nCounty Details:")
    for stats in overall_stats['county_stats']:
        if stats['status'] == 'completed':
            logger.info(f"  {stats['county']}: {stats['records_inserted']:,} records")
        else:
            logger.info(f"  {stats['county']}: FAILED ({stats['status']})")

    return overall_stats

if __name__ == "__main__":
    main()