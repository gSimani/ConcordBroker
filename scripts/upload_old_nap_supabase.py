#!/usr/bin/env python3
"""
Upload old NAP (tangible personal property) data into Supabase safely.

Features
- Parses NAP and uploads to public.florida_tangible_personal_property using
  ON CONFLICT (county, year, account_id).
- Auto-detect county from filename using COUNTY_CODES unless --county specified.
- Optional env-based DB override for PG_CONFIG (DATABASE_URL or SUPABASE_* vars).

Usage:
- python scripts/upload_old_nap_supabase.py \
    --year 2023 \
    --folders "C:\\path\\to\\2023NAP" \
    --batch-size 500
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse
import argparse

from scripts.integrate_historical_data_psycopg2 import (
    HistoricalDataIntegratorPG,
    COUNTY_CODES,
    PG_CONFIG as BASE_PG_CONFIG,
)


def apply_env_pg_config():
    pg = BASE_PG_CONFIG
    url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if url:
        try:
            u = urlparse(url)
            if u.scheme.startswith("postgres"):
                if u.hostname:
                    pg['host'] = u.hostname
                if u.port:
                    pg['port'] = u.port
                if u.path and len(u.path) > 1:
                    pg['database'] = u.path.lstrip('/')
                if u.username:
                    pg['user'] = u.username
                if u.password:
                    pg['password'] = u.password
        except Exception:
            pass
    pg['host'] = os.getenv('SUPABASE_HOST', pg['host'])
    pg['port'] = int(os.getenv('SUPABASE_PORT', pg['port']))
    pg['database'] = os.getenv('SUPABASE_DB', pg['database'])
    pg['user'] = os.getenv('SUPABASE_USER', pg['user'])
    pg['password'] = os.getenv('SUPABASE_PASSWORD', pg['password'])


def guess_county_from_name(name: str) -> str | None:
    u = name.upper().replace(' ', '')
    for cname in COUNTY_CODES.keys():
        if cname.replace(' ', '') in u:
            return cname
    return None


def iter_csvs(folder: Path):
    for p in folder.rglob("*.csv"):
        if p.is_file():
            yield p


def main():
    parser = argparse.ArgumentParser(description="Upload old NAP (TPP) files into Supabase")
    parser.add_argument('--year', type=int, required=True, help='Assessment year for NAP (e.g., 2023)')
    parser.add_argument('--folders', nargs='+', required=True, help='One or more folders to process')
    parser.add_argument('--batch-size', type=int, default=500, help='Upload batch size (default 500)')
    parser.add_argument('--county', help='Restrict to a specific county (e.g., GILCHRIST)')
    parser.add_argument('--limit', type=int, help='Limit rows per file (for testing)')
    parser.add_argument('--progress', action='store_true', help='Emit progress snapshots to public.ingestion_progress')

    args = parser.parse_args()

    apply_env_pg_config()

    year = args.year
    batch_size = args.batch_size
    county_filter = args.county.upper() if args.county else None

    ing = HistoricalDataIntegratorPG()
    if not ing.connect():
        print('[ERROR] DB connect failed')
        sys.exit(1)

    total_files = 0
    total_rows = 0
    considered = []
    try:
        for folder_str in args.folders:
            folder = Path(folder_str)
            if not folder.exists():
                print(f"[SKIP] Folder not found: {folder}")
                continue

            print(f"\n=== Processing NAP folder: {folder} ===")
            for csv in iter_csvs(folder):
                c = county_filter or guess_county_from_name(csv.name)
                if county_filter and (c is None or c != county_filter):
                    continue
                if not c:
                    print(f"[SKIP] No county match: {csv.name}")
                    continue
                considered.append((folder, csv, c))

        total_considered = len(considered)
        done_files = 0
        if args.progress and total_considered > 0:
            try:
                ing.cursor.execute(
                    "INSERT INTO public.ingestion_progress(created_at, phase_index, phase_total, county, years, done, total, percent, current)"
                    " VALUES (NOW(), NULL, NULL, %s, %s, %s, %s, %s, %s)",
                    (county_filter or None, {"start": year, "end": year}, 0, total_considered, 0, f"start:NAP {year}")
                )
                ing.conn.commit()
            except Exception:
                pass

        for folder, csv, c in considered:
            try:
                    df = ing.parse_nap_file(csv, c)
                    if df is None or len(df) == 0:
                        continue
                    # Ensure year if missing
                    if 'year' not in df.columns or df['year'].isna().all():
                        df['year'] = year
                    if args.limit:
                        df = df.head(args.limit)
                    uploaded = ing.upload_nap_to_postgres(df, batch_size=batch_size)
                    total_rows += uploaded
                    total_files += 1
                    done_files += 1
                    if args.progress and total_considered > 0:
                        try:
                            pct = int(done_files * 100 / max(total_considered, 1))
                            ing.cursor.execute(
                                "INSERT INTO public.ingestion_progress(created_at, phase_index, phase_total, county, years, done, total, percent, current)"
                                " VALUES (NOW(), NULL, NULL, %s, %s, %s, %s, %s, %s)",
                                (c, {"start": year, "end": year}, done_files, total_considered, pct, f"ingested:{csv.name}")
                            )
                            ing.conn.commit()
                        except Exception:
                            pass
                except Exception as e:
                    print(f"[ERROR] Failed file {csv.name}: {e}")
                    continue

        print(f"\n=== NAP upload complete: files={total_files}, rows={total_rows:,} ===")
    finally:
        ing.disconnect()


if __name__ == '__main__':
    main()
