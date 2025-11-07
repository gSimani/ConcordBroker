#!/usr/bin/env python3
"""
Watch ingestion progress in real-time from Supabase.
"""
import sys
import time
import os
sys.path.insert(0, '.')
from scripts.integrate_historical_data_psycopg2 import HistoricalDataIntegratorPG

def watch_progress(run_id='2023-full-load', interval=10):
    """Watch progress for a specific run ID."""
    ing = HistoricalDataIntegratorPG()
    if not ing.connect():
        print('[ERROR] Failed to connect to Supabase')
        return

    print(f'Monitoring run: {run_id}')
    print(f'Refresh interval: {interval} seconds')
    print('Press Ctrl+C to stop\n')

    try:
        while True:
            # Get latest progress
            ing.cursor.execute('''
                SELECT
                    created_at,
                    county,
                    done,
                    total,
                    percent,
                    current
                FROM public.ingestion_progress
                WHERE run_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            ''', (run_id,))

            row = ing.fetchone()
            if row:
                timestamp, county, done, total, pct, current = row
                bar_width = 40
                filled = int(bar_width * pct / 100)
                bar = '█' * filled + '░' * (bar_width - filled)

                os.system('cls' if os.name == 'nt' else 'clear')
                print(f'=== INGESTION PROGRESS ===')
                print(f'Run ID: {run_id}')
                print(f'Last Update: {timestamp}')
                print(f'County: {county or "N/A"}')
                print(f'Progress: {done}/{total} files ({pct}%)')
                print(f'[{bar}] {pct}%')
                print(f'Current: {current}')
                print(f'\nRefreshing in {interval}s... (Ctrl+C to stop)')
            else:
                print(f'No progress data found for run_id: {run_id}')

            time.sleep(interval)

    except KeyboardInterrupt:
        print('\n\nStopped monitoring.')
    finally:
        ing.disconnect()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Watch ingestion progress')
    parser.add_argument('--run-id', default='2023-full-load', help='Run ID to monitor')
    parser.add_argument('--interval', type=int, default=10, help='Refresh interval (seconds)')
    args = parser.parse_args()

    watch_progress(args.run_id, args.interval)
