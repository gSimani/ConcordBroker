#!/usr/bin/env python3
"""
Ingest a single SDF CSV directly by file path, providing county and year.
Uses the HistoricalDataIntegratorPG from integrate_historical_data_psycopg2.py
for parsing and upload with ON CONFLICT de-duplication.
"""
import argparse
from pathlib import Path
from integrate_historical_data_psycopg2 import HistoricalDataIntegratorPG


def main():
    ap = argparse.ArgumentParser(description='Direct SDF ingestion by file path')
    ap.add_argument('--file', required=True, help='Path to SDF CSV')
    ap.add_argument('--county', required=True, help='County name (e.g., CLAY)')
    ap.add_argument('--year', required=True, type=int, help='Assessment year (e.g., 2024)')
    ap.add_argument('--limit', type=int, help='Optional limit of rows to upload')
    ap.add_argument('--batch-size', type=int, default=100, help='Batch size for upload')
    ap.add_argument('--all-sales', action='store_true', help='Include unqualified SDF sales')
    ap.add_argument('--simple-sdf-key', action='store_true', help='Use simple ON CONFLICT key (parcel_id,county,sale_date)')
    args = ap.parse_args()

    integrator = HistoricalDataIntegratorPG()
    try:
        df = integrator.parse_sdf_file(Path(args.file), args.county, args.year, qualified_only=not args.all_sales)
        if args.limit:
            df = df.head(args.limit)
        if not integrator.connect():
            raise RuntimeError('DB connect failed')
        uploaded = integrator.upload_sdf_to_postgres(df, batch_size=args.batch_size, use_strong_key=not args.simple_sdf_key)
        print(f"[COMPLETE] {args.county} {args.year} (SDF): {uploaded} rows")
    finally:
        if integrator.conn:
            integrator.disconnect()


if __name__ == '__main__':
    main()

