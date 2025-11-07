#!/usr/bin/env python3
"""
Ingest a single NAL CSV directly by file path, providing county.
Uses HistoricalDataIntegratorPG for parsing and upsert into florida_parcels.
"""
import argparse
from pathlib import Path
from integrate_historical_data_psycopg2 import HistoricalDataIntegratorPG


def main():
    ap = argparse.ArgumentParser(description='Direct NAL ingestion by file path')
    ap.add_argument('--file', required=True, help='Path to NAL CSV')
    ap.add_argument('--county', required=True, help='County name (e.g., GILCHRIST)')
    ap.add_argument('--limit', type=int, help='Optional limit of rows to upload')
    ap.add_argument('--batch-size', type=int, default=500, help='Batch size for upload')
    args = ap.parse_args()

    integrator = HistoricalDataIntegratorPG()
    try:
        df = integrator.parse_nal_file(Path(args.file), args.county)
        if args.limit:
            df = df.head(args.limit)
        if not integrator.connect():
            raise RuntimeError('DB connect failed')
        uploaded = integrator.upload_to_postgres(df, batch_size=args.batch_size)
        print(f"[COMPLETE] {args.county} (NAL): {uploaded} rows")
    finally:
        if integrator.conn:
            integrator.disconnect()


if __name__ == '__main__':
    main()

