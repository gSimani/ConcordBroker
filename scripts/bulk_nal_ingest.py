#!/usr/bin/env python3
"""
Bulk NAL Ingest Orchestrator with live progress bars.

- Reads our Public Records manifest (data/manifests/dor_public_records_manifest.json)
- Filters NAL zip URLs by ticket (default: ~20251103-1264400) and years
- Downloads each zip with a live progress bar
- Extracts CSVs and ingests target counties via HistoricalDataIntegratorPG
  (ingestion shows its own batch progress bars)

Usage examples:
  python scripts/bulk_nal_ingest.py --ticket ~20251103-1264400 --years 2009-2023 --county GILCHRIST
  python scripts/bulk_nal_ingest.py --ticket ~20251103-1264400 --years 2015-2020 --county GILCHRIST --limit 500
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
import zipfile
import requests

sys.path.append(str(Path(__file__).parent))
from integrate_historical_data_psycopg2 import HistoricalDataIntegratorPG, COUNTY_CODES


MANIFEST_PATH = Path('data/manifests/dor_public_records_manifest.json')
DL_DIR = Path('historical_data/nal_zips')
EXTRACT_DIR = Path('historical_data/nal_extracted')


def render_progress(done: int, total: int, prefix: str = ''):
    total = max(total, 1)
    pct = int((done / total) * 100)
    width = 30
    fill = int(width * done / total)
    bar = '#' * fill + '-' * (width - fill)
    msg = f"{prefix}[{bar}] {pct:3d}%  {done:,}/{total:,}"
    print('\r' + msg, end='', flush=True)


def stream_download(url: str, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        total = int(r.headers.get('Content-Length', '0'))
        downloaded = 0
        chunk = 1024 * 64
        with open(out_path, 'wb') as f:
            for data in r.iter_content(chunk_size=chunk):
                if not data:
                    continue
                f.write(data)
                downloaded += len(data)
                render_progress(downloaded, total or 1, prefix='[DOWN] ')
    print()


def invert_counties():
    inv = {v: k for k, v in COUNTY_CODES.items()}
    return inv


def guess_county_from_name(name: str) -> str | None:
    # Patterns like NAL_2015_31Gilchrist_F.csv or include county name
    m = re.search(r'_(\d{2})([A-Za-z ]+)_', name)
    if m:
        code = m.group(1)
        try:
            code = str(int(code))  # remove leading zeroes
        except:
            pass
        inv = invert_counties()
        county = inv.get(code)
        if county:
            return county
    # fallback on textual county name in filename
    for cname in COUNTY_CODES.keys():
        if cname.replace(' ', '').upper() in name.replace(' ', '').upper():
            return cname
    return None


def main():
    ap = argparse.ArgumentParser(description='Bulk NAL ingestion with live progress bars')
    ap.add_argument('--ticket', default='~20251103-1264400', help='Public Records ticket (e.g., ~20251103-1264400)')
    ap.add_argument('--years', default='2009-2023', help='Year range, e.g., 2009-2023')
    ap.add_argument('--county', help='Limit to a single county (e.g., GILCHRIST)')
    ap.add_argument('--limit', type=int, help='Optional row limit per CSV for ingest')
    ap.add_argument('--batch-size', type=int, default=500, help='Batch size for ingest')
    args = ap.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"[ERROR] Manifest not found: {MANIFEST_PATH}")
        sys.exit(1)

    years = []
    if '-' in args.years:
        a, b = args.years.split('-', 1)
        try:
            a, b = int(a), int(b)
            years = list(range(a, b + 1))
        except:
            pass
    if not years:
        try:
            years = [int(args.years)]
        except:
            print(f"[ERROR] Invalid years: {args.years}")
            sys.exit(1)

    data = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    # Manifest structure: manifest[year][county][dataset] = [{name,url}, ...]
    ticket = args.ticket

    nal_urls = []
    for y in data.get('manifest', {}):
        try:
            yi = int(y)
        except:
            continue
        if yi not in years:
            continue
        counties = data['manifest'][y]
        for c in counties:
            datasets = counties[c]
            if 'NAL' in datasets:
                for item in datasets['NAL']:
                    url = item.get('url', '')
                    name = item.get('name', '')
                    if ticket in url and re.match(rf'^{yi}(F|P)\.zip$', name, re.IGNORECASE):
                        nal_urls.append((yi, url, name))

    nal_urls = sorted(set(nal_urls))
    total_zips = len(nal_urls)
    print(f"[INFO] NAL zips to process: {total_zips}")
    if total_zips == 0:
        print("[WARN] No NAL zips matched the ticket and years.")
        return

    ing = HistoricalDataIntegratorPG()
    if not ing.connect():
        print('[ERROR] DB connect failed')
        return

    try:
        done = 0
        for yi, url, name in nal_urls:
            print(f"\n[ZIP] Year {yi} -> {name}")
            zip_path = DL_DIR / name
            if not zip_path.exists():
                print(f"[DL] {url}")
                stream_download(url, zip_path)
            else:
                print("[SKIP] Zip already downloaded")

            # Extract
            out_dir = EXTRACT_DIR / f"{args.ticket}_{yi}"
            out_dir.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(out_dir)
                print(f"[EXTRACT] -> {out_dir}")
            except Exception as e:
                print(f"[ERROR] Extract failed: {e}")
                continue

            # Walk CSVs
            csvs = [p for p in out_dir.rglob('*.csv') if 'NAL' in p.name.upper()]
            print(f"[FOUND] {len(csvs)} NAL CSV files")

            for csv_path in csvs:
                county = args.county or guess_county_from_name(csv_path.name)
                if not county:
                    # Attempt fallback by sampling CO_NO from filename; else skip
                    print(f"[SKIP] County undetermined for {csv_path.name}")
                    continue
                if args.county and county.upper() != args.county.upper():
                    continue
                print(f"[INGEST] {csv_path.name} -> county={county}")
                try:
                    df = ing.parse_nal_file(csv_path, county)
                    if args.limit:
                        df = df.head(args.limit)
                    ing.upload_to_postgres(df, batch_size=args.batch_size)
                except Exception as e:
                    print(f"[ERROR] Ingest failed for {csv_path.name}: {e}")
                    continue

            done += 1
            render_progress(done, total_zips, prefix='[OVERALL] ')
        print()  # newline after overall bar
        print("[COMPLETE] NAL bulk ingestion done for selected years.")
    finally:
        ing.disconnect()


if __name__ == '__main__':
    main()

