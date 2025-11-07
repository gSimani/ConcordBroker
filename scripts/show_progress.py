#!/usr/bin/env python3
"""
Show up-to-date ingestion progress with percentage bars.

Sources (auto-detected):
- Supabase table public.ingestion_progress (preferred)
- Fallback: .agent/progress.json (single-file snapshot)

Usage:
- python scripts/show_progress.py --year 2023
- python scripts/show_progress.py --watch 5   # refresh every 5s
"""

from __future__ import annotations

import os
import sys
import time
import json
from pathlib import Path
from urllib.parse import urlparse
import argparse

def render_bar(pct: int, width: int = 30) -> str:
    pct = max(0, min(100, int(pct or 0)))
    fill = int(width * pct / 100)
    return '[' + ('#' * fill) + ('-' * (width - fill)) + f'] {pct:3d}%'

def try_db():
    try:
        import psycopg2
        import psycopg2.extras
    except Exception:
        return None, None

    url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')
    if url:
        try:
            u = urlparse(url)
            conn = psycopg2.connect(url)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            return conn, cur
        except Exception:
            return None, None

    # Discrete env vars
    host = os.getenv('SUPABASE_HOST')
    user = os.getenv('SUPABASE_USER')
    password = os.getenv('SUPABASE_PASSWORD')
    database = os.getenv('SUPABASE_DB') or 'postgres'
    port = int(os.getenv('SUPABASE_PORT') or '5432')
    if host and user and password:
        try:
            conn = psycopg2.connect(host=host, port=port, user=user, password=password, database=database, sslmode='require')
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            return conn, cur
        except Exception:
            return None, None
    return None, None

def fetch_progress(cur, year: int, dataset: str):
    # Find the most recent start row for this dataset/year
    cur.execute(
        """
        SELECT created_at, total
        FROM public.ingestion_progress
        WHERE current LIKE %s
          AND (years->>'start')::int = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (f'start:{dataset} %', year),
    )
    start = cur.fetchone()
    if not start:
        return None
    start_at = start['created_at']
    total = start.get('total') or 0

    # Find latest snapshot since start
    cur.execute(
        """
        SELECT MAX(done) AS done_now,
               MAX(percent) AS pct_now,
               (ARRAY_AGG(current ORDER BY created_at DESC))[1] AS current
        FROM public.ingestion_progress
        WHERE created_at >= %s
          AND (years->>'start')::int = %s
        """,
        (start_at, year),
    )
    row = cur.fetchone() or {}
    return {
        'total': total,
        'done': row.get('done_now') or 0,
        'percent': row.get('pct_now') or 0,
        'current': row.get('current') or ''
    }

def show_db(year: int):
    conn, cur = try_db()
    if not cur:
        return False
    try:
        datasets = ['NAL', 'SDF', 'NAP']
        any_data = False
        print(f"=== Year {year} Ingestion Progress ===")
        for ds in datasets:
            try:
                prog = fetch_progress(cur, year, ds)
            except Exception:
                prog = None
            if not prog:
                continue
            any_data = True
            bar = render_bar(prog['percent'])
            print(f"{ds:4} {bar}  ({prog['done']}/{prog['total']})  {prog['current']}")
        return any_data
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

def show_file():
    p = Path('.agent/progress.json')
    if not p.exists():
        return False
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        print('Malformed .agent/progress.json')
        return True
    ts = data.get('timestamp')
    phase_idx = data.get('phase_index')
    phase_total = data.get('phase_total')
    county = data.get('county')
    years = data.get('years') or {}
    done = data.get('done') or 0
    total = data.get('total') or 0
    percent = data.get('percent') or 0
    current = data.get('current') or ''
    bar = render_bar(percent)
    print("=== Orchestrator Progress (.agent/progress.json) ===")
    print(f"Time:    {ts}")
    print(f"County:  {county}")
    print(f"Phase:   {phase_idx}/{phase_total}  Years: {years.get('start')}{years.get('end')}")
    print(f"Overall: {bar}  ({done}/{total})")
    print(f"Current: {current}")
    return True

def main():
    ap = argparse.ArgumentParser(description='Show up-to-date ingestion progress with percentage bars')
    ap.add_argument('--year', type=int, default=None, help='Year to show (e.g., 2023). Defaults to latest year in telemetry or file.')
    ap.add_argument('--watch', type=int, default=0, help='Refresh every N seconds (0 = single snapshot)')
    args = ap.parse_args()

    def snapshot():
        shown = False
        y = args.year or 2023
        # Prefer DB telemetry if available
        if show_db(y):
            shown = True
        # Fallback to progress.json
        elif show_file():
            shown = True
        else:
            print('No telemetry found (ingestion_progress or .agent/progress.json).')
        return shown

    if args.watch and args.watch > 0:
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                snapshot()
                time.sleep(args.watch)
        except KeyboardInterrupt:
            pass
    else:
        snapshot()

if __name__ == '__main__':
    main()

