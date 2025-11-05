#!/usr/bin/env python3
"""
Historical DOR Data Integration (Direct PostgreSQL Connection)
Uses psycopg2 for better timeout control and bulk insert performance
"""

import os
import pandas as pd
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime
import time
from pathlib import Path

# PostgreSQL connection (direct to Supabase)
PG_CONFIG = {
    'host': 'aws-1-us-east-1.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.pmispwtdngkcmsrsjwbp',
    'password': 'West@Boca613!',
    'sslmode': 'require',
    'connect_timeout': 30,
    'options': '-c statement_timeout=300000'  # 5 minute timeout
}

# County codes mapping (31 = Gilchrist, etc.)
COUNTY_CODES = {
    'ALACHUA': '11', 'BAKER': '12', 'BAY': '13', 'BRADFORD': '14', 'BREVARD': '15',
    'BROWARD': '16', 'CALHOUN': '17', 'CHARLOTTE': '18', 'CITRUS': '19', 'CLAY': '20',
    'COLLIER': '21', 'COLUMBIA': '22', 'DADE': '23', 'DESOTO': '24', 'DIXIE': '25',
    'DUVAL': '26', 'ESCAMBIA': '27', 'FLAGLER': '28', 'FRANKLIN': '29', 'GADSDEN': '30',
    'GILCHRIST': '31', 'GLADES': '32', 'GULF': '33', 'HAMILTON': '34', 'HARDEE': '35',
    'HENDRY': '36', 'HERNANDO': '37', 'HIGHLANDS': '38', 'HILLSBOROUGH': '39', 'HOLMES': '40',
    'INDIAN RIVER': '41', 'JACKSON': '42', 'JEFFERSON': '43', 'LAFAYETTE': '44', 'LAKE': '45',
    'LEE': '46', 'LEON': '47', 'LEVY': '48', 'LIBERTY': '49', 'MADISON': '50',
    'MANATEE': '51', 'MARION': '52', 'MARTIN': '53', 'MONROE': '54', 'NASSAU': '55',
    'OKALOOSA': '56', 'OKEECHOBEE': '57', 'ORANGE': '58', 'OSCEOLA': '59', 'PALM BEACH': '60',
    'PASCO': '61', 'PINELLAS': '62', 'POLK': '63', 'PUTNAM': '64', 'ST JOHNS': '65',
    'ST LUCIE': '66', 'SANTA ROSA': '67', 'SARASOTA': '68', 'SEMINOLE': '69', 'SUMTER': '70',
    'SUWANNEE': '71', 'TAYLOR': '72', 'UNION': '73', 'VOLUSIA': '74', 'WAKULLA': '75',
    'WALTON': '76', 'WASHINGTON': '77'
}

# NAL to florida_parcels field mapping
NAL_FIELD_MAPPING = {
    'PARCEL_ID': 'parcel_id',
    'ASMNT_YR': 'year',
    'DOR_UC': 'property_use',
    'JV': 'just_value',
    'LND_VAL': 'land_value',
    'LND_SQFOOT': 'land_sqft',
    'TOT_LVG_AREA': 'total_living_area',
    'NO_RES_UNTS': 'units',
    'ACT_YR_BLT': 'year_built',
    'SALE_PRC1': 'sale_price',
    'SALE_YR1': 'last_sale_year',
    'SALE_MO1': 'last_sale_month',
    'QUAL_CD1': 'sale_qualification',
    'OWN_NAME': 'owner_name',
    'OWN_ADDR1': 'owner_addr1',
    'OWN_ADDR2': 'owner_addr2',
    'OWN_CITY': 'owner_city',
    'OWN_STATE': 'owner_state',
    'OWN_ZIPCD': 'owner_zip',
    'PHY_ADDR1': 'phy_addr1',
    'PHY_ADDR2': 'phy_addr2',
    'PHY_CITY': 'phy_city',
    'PHY_ZIPCD': 'phy_zipcd',
    'S_LEGAL': 'legal_desc',
    'LND_UNIT_CD': 'land_use_code',
}

# SDF to property_sales_history field mapping
# NOTE: Mapped to ACTUAL database column names (verified 2025-11-05)
SDF_FIELD_MAPPING = {
    'PARCEL_ID': 'parcel_id',
    'SALE_YR': 'sale_year',
    'SALE_MO': 'sale_month',
    'SALE_PRC': 'sale_price',
    'QUAL_CD': 'quality_code',  # Actual column: quality_code (not qualified_code)
    'OR_BOOK': 'or_book',  # Actual column: or_book (not official_record_book)
    'OR_PAGE': 'or_page',  # Actual column: or_page (not official_record_page)
    'CLERK_NO': 'clerk_no',  # Actual column: clerk_no (not clerk_file_number)
    'VI_CD': 'verification_code',
}

# NAP to tangible personal property field mapping
NAP_FIELD_MAPPING = {
    'ACCT_ID': 'account_id',
    'ASMNT_YR': 'year',
    'NAICS_CD': 'naics_code',
    'JV_TOTAL': 'just_value_total',
    'AV_TOTAL': 'assessed_value_total',
    'TAX_VAL': 'taxable_value',
    'OWN_NAM': 'business_owner_name',
    'OWN_ADDR': 'business_owner_addr',
    'OWN_CITY': 'business_owner_city',
    'OWN_STATE': 'business_owner_state',
    'OWN_ZIPCD': 'business_owner_zip',
    'PHY_ADDR': 'business_phy_addr',
    'PHY_CITY': 'business_phy_city',
    'PHY_ZIPCD': 'business_phy_zip',
}


class HistoricalDataIntegratorPG:
    def __init__(self):
        self.download_dir = Path('historical_data')
        self.download_dir.mkdir(exist_ok=True)
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish PostgreSQL connection"""
        try:
            self.conn = psycopg2.connect(**PG_CONFIG)
            self.conn.autocommit = False
            self.cursor = self.conn.cursor()
            print('[CONNECT] PostgreSQL connection established')
            return True
        except Exception as e:
            print(f'[ERROR] Connection failed: {str(e)}')
            return False

    def disconnect(self):
        """Close PostgreSQL connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print('[DISCONNECT] PostgreSQL connection closed')

    def get_local_file_path(self, county: str, year: int, file_type: str) -> Path:
        """Get path to local NAL/SDF file if it exists"""
        county_upper = county.upper()
        county_code = COUNTY_CODES.get(county_upper)

        if not county_code:
            return None

        # Check in TEMP directory first (where 2025 files are)
        temp_path = Path(f'C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP/DATABASE PROPERTY APP/{county_upper}/{file_type}')

        if temp_path.exists():
            # Look for file matching pattern
            for file in temp_path.glob(f'{file_type}{county_code}*.csv'):
                # Extract year from filename if possible
                if str(year) in file.name or (year == 2025 and '2025' in file.name):
                    return file

        return None

    def parse_nal_file(self, file_path: Path, county: str) -> pd.DataFrame:
        """Parse NAL file and map to florida_parcels schema"""
        print(f'[PARSE] Reading NAL file: {file_path}')

        try:
            # Read CSV
            df = pd.read_csv(file_path, dtype=str, low_memory=False)
            print(f'[INFO] Loaded {len(df):,} rows from NAL file')

            # Create mapped dataframe
            mapped_data = {}

            # Map fields according to NAL_FIELD_MAPPING
            for nal_field, schema_field in NAL_FIELD_MAPPING.items():
                if nal_field in df.columns:
                    mapped_data[schema_field] = df[nal_field]

            result_df = pd.DataFrame(mapped_data)

            # Add county name
            result_df['county'] = county.upper()

            # Data type conversions - separate integer and numeric fields
            integer_fields = ['units', 'year_built', 'last_sale_year', 'last_sale_month', 'year']
            numeric_fields = ['just_value', 'land_value', 'land_sqft', 'total_living_area', 'sale_price']

            # Convert integer fields to Int64 (nullable integer)
            for field in integer_fields:
                if field in result_df.columns:
                    result_df[field] = pd.to_numeric(result_df[field], errors='coerce').astype('Int64')

            # Convert numeric fields (can remain float)
            for field in numeric_fields:
                if field in result_df.columns:
                    result_df[field] = pd.to_numeric(result_df[field], errors='coerce')

            # Clean owner_state to 2 characters
            if 'owner_state' in result_df.columns:
                result_df['owner_state'] = result_df['owner_state'].str[:2]

            # Build sale_date from year/month (as string, not datetime)
            if 'last_sale_year' in result_df.columns and 'last_sale_month' in result_df.columns:
                def build_sale_date(row):
                    if pd.notna(row['last_sale_year']) and pd.notna(row['last_sale_month']):
                        try:
                            year = int(row['last_sale_year'])
                            month = int(row['last_sale_month'])
                            return f"{year}-{month:02d}-01T00:00:00"
                        except:
                            return None
                    return None

                result_df['sale_date'] = result_df.apply(build_sale_date, axis=1)
                result_df = result_df.drop(columns=['last_sale_year', 'last_sale_month'])

            # Calculate building_value if possible
            if 'just_value' in result_df.columns and 'land_value' in result_df.columns:
                result_df['building_value'] = result_df['just_value'] - result_df['land_value']

            # Replace NaN with None for database
            result_df = result_df.where(pd.notna(result_df), None)

            print(f'[SUCCESS] Parsed {len(result_df):,} properties')
            return result_df

        except Exception as e:
            print(f'[ERROR] Failed to parse NAL file: {str(e)}')
            raise

    def parse_sdf_file(self, file_path: Path, county: str, year: int, qualified_only: bool = True) -> pd.DataFrame:
        """Parse SDF file and map to property_sales_history schema"""
        print(f'[PARSE] Reading SDF file: {file_path}')

        try:
            # Read CSV
            df = pd.read_csv(file_path, dtype=str, low_memory=False)
            print(f'[INFO] Loaded {len(df):,} rows from SDF file')

            # Create mapped dataframe
            mapped_data = {}

            # Map fields according to SDF_FIELD_MAPPING
            for sdf_field, schema_field in SDF_FIELD_MAPPING.items():
                if sdf_field in df.columns:
                    mapped_data[schema_field] = df[sdf_field]

            result_df = pd.DataFrame(mapped_data)

            # Add county and county_no if required by schema
            result_df['county'] = county.upper()
            try:
                code = COUNTY_CODES.get(county.upper())
                if code is not None:
                    result_df['county_no'] = int(code)
            except Exception:
                pass

            # Data type conversions
            integer_fields = ['sale_year', 'sale_month']
            numeric_fields = ['sale_price']

            for field in integer_fields:
                if field in result_df.columns:
                    result_df[field] = pd.to_numeric(result_df[field], errors='coerce').astype('Int64')

            for field in numeric_fields:
                if field in result_df.columns:
                    result_df[field] = pd.to_numeric(result_df[field], errors='coerce')

            # Build sale_date from year/month
            if 'sale_year' in result_df.columns and 'sale_month' in result_df.columns:
                def build_sale_date(row):
                    if pd.notna(row['sale_year']) and pd.notna(row['sale_month']):
                        try:
                            year = int(row['sale_year'])
                            month = int(row['sale_month'])
                            return f"{year}-{month:02d}-01T00:00:00"
                        except:
                            return None
                    return None

                result_df['sale_date'] = result_df.apply(build_sale_date, axis=1)

            # Replace NaN with None
            result_df = result_df.where(pd.notna(result_df), None)

            # Optionally keep only qualified sales (QUAL_CD == '01')
            col = 'quality_code' if 'quality_code' in result_df.columns else 'qualified_code' if 'qualified_code' in result_df.columns else None
            if qualified_only and col:
                before = len(result_df)
                result_df = result_df[result_df[col] == '01']
                print(f'[FILTER] Qualified-only sales: {len(result_df):,}/{before:,}')

            print(f'[SUCCESS] Parsed {len(result_df):,} sales records')
            return result_df

        except Exception as e:
            print(f'[ERROR] Failed to parse SDF file: {str(e)}')
            raise

    def parse_nap_file(self, file_path: Path, county: str) -> pd.DataFrame:
        """Parse NAP file and map to tangible personal property schema"""
        print(f'[PARSE] Reading NAP file: {file_path}')

        try:
            # Read CSV
            df = pd.read_csv(file_path, dtype=str, low_memory=False)
            print(f'[INFO] Loaded {len(df):,} rows from NAP file')

            # Create mapped dataframe
            mapped_data = {}

            # Map fields according to NAP_FIELD_MAPPING
            for nap_field, schema_field in NAP_FIELD_MAPPING.items():
                if nap_field in df.columns:
                    mapped_data[schema_field] = df[nap_field]

            result_df = pd.DataFrame(mapped_data)

            # Add county name
            result_df['county'] = county.upper()

            # Data type conversions
            integer_fields = ['year']
            numeric_fields = ['just_value_total', 'assessed_value_total', 'taxable_value']

            for field in integer_fields:
                if field in result_df.columns:
                    result_df[field] = pd.to_numeric(result_df[field], errors='coerce').astype('Int64')

            for field in numeric_fields:
                if field in result_df.columns:
                    result_df[field] = pd.to_numeric(result_df[field], errors='coerce')

            # Clean state to 2 characters
            if 'business_owner_state' in result_df.columns:
                result_df['business_owner_state'] = result_df['business_owner_state'].str[:2]

            # Replace NaN with None
            result_df = result_df.where(pd.notna(result_df), None)

            print(f'[SUCCESS] Parsed {len(result_df):,} tangible property records')
            return result_df

        except Exception as e:
            print(f'[ERROR] Failed to parse NAP file: {str(e)}')
            raise

    def upload_to_postgres(self, df: pd.DataFrame, batch_size: int = 100) -> int:
        """Upload dataframe to florida_parcels using PostgreSQL COPY"""
        total_rows = len(df)
        uploaded = 0

        print(f'[UPLOAD] Starting upload of {total_rows:,} rows (batch size: {batch_size})')

        # Get column names
        columns = df.columns.tolist()

        # Prepare INSERT ... ON CONFLICT statement
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))

        update_set = ', '.join([f'{col} = EXCLUDED.{col}' for col in columns if col not in ['parcel_id', 'county', 'year']])

        sql = f"""
            INSERT INTO florida_parcels ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (parcel_id, county, year)
            DO UPDATE SET {update_set}
        """

        try:
            for i in range(0, total_rows, batch_size):
                batch = df.iloc[i:i+batch_size]

                # Convert to list of tuples, replacing pandas NA with None
                batch_data = []
                for row in batch.values:
                    # Convert each row, replacing pd.NA with None
                    cleaned_row = tuple(
                        None if pd.isna(val) or (hasattr(pd, 'NA') and val is pd.NA) else val
                        for val in row
                    )
                    batch_data.append(cleaned_row)

                try:
                    # Use execute_batch for better performance
                    psycopg2.extras.execute_batch(self.cursor, sql, batch_data, page_size=batch_size)
                    self.conn.commit()

                    uploaded += len(batch_data)

                    if (i + batch_size) % 1000 == 0:
                        print(f'[PROGRESS] Uploaded {uploaded:,}/{total_rows:,} ({uploaded/total_rows*100:.1f}%)')

                except Exception as e:
                    print(f'[ERROR] Batch upload failed at row {i}: {str(e)}')
                    self.conn.rollback()
                    # Continue with next batch
                    continue

            print(f'[SUCCESS] Upload complete: {uploaded:,} rows')
            return uploaded

        except Exception as e:
            print(f'[ERROR] Upload failed: {str(e)}')
            self.conn.rollback()
            raise

    def upload_sdf_to_postgres(self, df: pd.DataFrame, batch_size: int = 100, use_strong_key: bool = True) -> int:
        """Upload dataframe to property_sales_history with dedup via ON CONFLICT.
        Requires the corresponding UNIQUE index to exist on the target columns.
        """
        total_rows = len(df)
        uploaded = 0

        print(f'[UPLOAD] SDF: Starting upload of {total_rows:,} rows (batch size: {batch_size})')

        columns = df.columns.tolist()
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))

        # Build conflict target
        if use_strong_key:
            conflict_cols = ['parcel_id', 'county', 'sale_date', 'sale_price', 'or_book', 'or_page', 'clerk_no']
        else:
            conflict_cols = ['parcel_id', 'county', 'sale_date']

        conflict_str = ', '.join(conflict_cols)
        update_set = ', '.join([f'{col} = EXCLUDED.{col}' for col in columns if col not in conflict_cols])

        sql = f"""
            INSERT INTO property_sales_history ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_str})
            DO UPDATE SET {update_set}
        """

        try:
            for i in range(0, total_rows, batch_size):
                batch = df.iloc[i:i+batch_size]
                batch_data = []
                for row in batch.values:
                    cleaned_row = tuple(
                        None if pd.isna(val) or (hasattr(pd, 'NA') and val is pd.NA) else val
                        for val in row
                    )
                    batch_data.append(cleaned_row)

                try:
                    psycopg2.extras.execute_batch(self.cursor, sql, batch_data, page_size=batch_size)
                    self.conn.commit()
                    uploaded += len(batch_data)
                    if (i + batch_size) % 1000 == 0:
                        print(f'[PROGRESS] SDF Uploaded {uploaded:,}/{total_rows:,} ({uploaded/total_rows*100:.1f}%)')
                except Exception as e:
                    self.conn.rollback()
                    # Surface missing unique constraint clearly
                    msg = str(e)
                    if 'there is no unique or exclusion constraint matching the ON CONFLICT specification' in msg.lower():
                        print('[ERROR] Missing UNIQUE index for SDF ON CONFLICT target. See sql/ensure_unique_constraints.sql to add it.')
                        raise
                    print(f'[ERROR] SDF batch failed at row {i}: {msg}')
                    continue

            print(f'[SUCCESS] SDF upload complete: {uploaded:,} rows')
            return uploaded

        except Exception:
            raise

    def upload_nap_to_postgres(self, df: pd.DataFrame, batch_size: int = 100) -> int:
        """Upload dataframe to florida_tangible_personal_property with ON CONFLICT.
        Requires UNIQUE (county, year, account_id) to exist.
        """
        total_rows = len(df)
        uploaded = 0

        print(f'[UPLOAD] NAP: Starting upload of {total_rows:,} rows (batch size: {batch_size})')

        columns = df.columns.tolist()
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))

        conflict_cols = ['county', 'year', 'account_id']
        update_set = ', '.join([f'{col} = EXCLUDED.{col}' for col in columns if col not in conflict_cols])

        sql = f"""
            INSERT INTO florida_tangible_personal_property ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (county, year, account_id)
            DO UPDATE SET {update_set}
        """

        try:
            for i in range(0, total_rows, batch_size):
                batch = df.iloc[i:i+batch_size]
                batch_data = []
                for row in batch.values:
                    cleaned_row = tuple(
                        None if pd.isna(val) or (hasattr(pd, 'NA') and val is pd.NA) else val
                        for val in row
                    )
                    batch_data.append(cleaned_row)

                try:
                    psycopg2.extras.execute_batch(self.cursor, sql, batch_data, page_size=batch_size)
                    self.conn.commit()
                    uploaded += len(batch_data)
                except Exception as e:
                    self.conn.rollback()
                    msg = str(e)
                    if 'relation "florida_tangible_personal_property" does not exist' in msg:
                        print('[ERROR] NAP table missing. Run the DDL from DOR_PORTAL_DOWNLOAD_AND_DEDUP.md or sql/ensure_unique_constraints.sql to create it.')
                        raise
                    print(f'[ERROR] NAP batch failed at row {i}: {msg}')
                    continue

            print(f'[SUCCESS] NAP upload complete: {uploaded:,} rows')
            return uploaded

        except Exception:
            raise

    def integrate_county_year(self, county: str, year: int, types=(
        'NAL','SDF','NAP'), dry_run: bool = False, batch_size: int = 100, qualified_only: bool = True, limit: int = None,
        use_strong_sdf_key: bool = True) -> bool:
        """Integrate selected data types for a single county and year."""
        print(f'\n{"="*70}')
        print(f'INTEGRATING: {county.upper()} - Year {year}')
        print(f'{"="*70}\n')

        try:
            any_success = False

            # NAL
            if 'NAL' in types:
                nal_path = self.get_local_file_path(county, year, 'NAL')
                if nal_path and nal_path.exists():
                    nal_df = self.parse_nal_file(nal_path, county)
                    if limit:
                        nal_df = nal_df.head(limit)
                    if nal_df is not None and len(nal_df) > 0:
                        if dry_run:
                            print(f'[DRY-RUN] florida_parcels would receive {len(nal_df):,} rows')
                            any_success = True
                        else:
                            # Lazy-connect only when uploading
                            if not self.conn:
                                if not self.connect():
                                    return False
                            uploaded = self.upload_to_postgres(nal_df, batch_size=batch_size)
                            print(f'[COMPLETE] {county} {year} (NAL): {uploaded:,} rows')
                            any_success = True
                else:
                    print(f'[SKIP] NAL file not available for {county} {year}')

            # SDF
            if 'SDF' in types:
                sdf_path = self.get_local_file_path(county, year, 'SDF')
                if sdf_path and sdf_path.exists():
                    sdf_df = self.parse_sdf_file(sdf_path, county, year, qualified_only=qualified_only)
                    if limit:
                        sdf_df = sdf_df.head(limit)
                    if sdf_df is not None and len(sdf_df) > 0:
                        if dry_run:
                            print(f'[DRY-RUN] property_sales_history would receive {len(sdf_df):,} rows')
                            any_success = True
                        else:
                            if not self.conn:
                                if not self.connect():
                                    return False
                            uploaded = self.upload_sdf_to_postgres(sdf_df, batch_size=batch_size, use_strong_key=use_strong_sdf_key)
                            print(f'[COMPLETE] {county} {year} (SDF): {uploaded:,} rows')
                            any_success = True
                else:
                    print(f'[SKIP] SDF file not available for {county} {year}')

            # NAP
            if 'NAP' in types:
                nap_path = self.get_local_file_path(county, year, 'NAP')
                if nap_path and nap_path.exists():
                    nap_df = self.parse_nap_file(nap_path, county)
                    if limit:
                        nap_df = nap_df.head(limit)
                    if nap_df is not None and len(nap_df) > 0:
                        if dry_run:
                            print(f'[DRY-RUN] florida_tangible_personal_property would receive {len(nap_df):,} rows')
                            any_success = True
                        else:
                            if not self.conn:
                                if not self.connect():
                                    return False
                            uploaded = self.upload_nap_to_postgres(nap_df, batch_size=batch_size)
                            print(f'[COMPLETE] {county} {year} (NAP): {uploaded:,} rows')
                            any_success = True
                else:
                    print(f'[SKIP] NAP file not available for {county} {year}')

            if self.conn:
                self.disconnect()
            return any_success

        except Exception as e:
            print(f'[ERROR] Failed to integrate {county} {year}: {str(e)}')
            self.disconnect()
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Historical DOR Data Integration (PostgreSQL)')
    parser.add_argument('--county', help='County name (e.g., GILCHRIST)', default='GILCHRIST')
    parser.add_argument('--year', type=int, help='Year to integrate', default=2025)
    parser.add_argument('--types', default='NAL,SDF', help='Comma-separated types to process (NAL,NAP,SDF)')
    parser.add_argument('--dry-run', action='store_true', help='Parse only, do not upload')
    parser.add_argument('--batch-size', type=int, default=100, help='Upload batch size')
    parser.add_argument('--limit', type=int, help='Limit rows per file for testing')
    parser.add_argument('--all-sales', action='store_true', help='Include unqualified SDF sales')
    parser.add_argument('--simple-sdf-key', action='store_true', help='Use simpler ON CONFLICT key for SDF (parcel_id,county,sale_date)')

    args = parser.parse_args()

    integrator = HistoricalDataIntegratorPG()
    types = tuple([t.strip().upper() for t in (args.types or '').split(',') if t.strip()])
    integrator.integrate_county_year(
        args.county,
        args.year,
        types=types,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        qualified_only=not args.all_sales,
        limit=args.limit,
        use_strong_sdf_key=not args.simple_sdf_key,
    )


if __name__ == '__main__':
    main()
