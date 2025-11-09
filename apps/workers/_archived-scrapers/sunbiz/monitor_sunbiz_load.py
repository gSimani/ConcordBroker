"""
Monitor Sunbiz data loading progress
"""

import os
import sys
import io
from supabase import create_client
from datetime import datetime
import time

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Initialize Supabase
supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

supabase = create_client(supabase_url, supabase_key)

def get_table_counts():
    """Get record counts for Sunbiz tables"""
    tables = {
        'sunbiz_corporate': 'Corporations',
        'sunbiz_fictitious': 'Fictitious Names',
        'sunbiz_liens': 'Liens',
        'sunbiz_partnerships': 'Partnerships'
    }
    
    counts = {}
    for table, name in tables.items():
        try:
            # Get count using aggregation
            result = supabase.table(table).select('*', count='exact').limit(0).execute()
            count = result.count if hasattr(result, 'count') else 0
            counts[name] = count
        except Exception as e:
            counts[name] = f"Error: {e}"
    
    return counts

def monitor_progress(interval=30):
    """Monitor loading progress"""
    print("=" * 60)
    print("SUNBIZ DATA LOADING MONITOR")
    print("=" * 60)
    print(f"Monitoring every {interval} seconds (Ctrl+C to stop)\n")
    
    previous_counts = {}
    
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            counts = get_table_counts()
            
            print(f"\n[{current_time}] Current Status:")
            print("-" * 40)
            
            total = 0
            for name, count in counts.items():
                if isinstance(count, int):
                    total += count
                    # Calculate rate if we have previous data
                    rate = ""
                    if name in previous_counts and isinstance(previous_counts[name], int):
                        diff = count - previous_counts[name]
                        if diff > 0:
                            rate = f" (+{diff:,} @ {diff/interval:.0f}/sec)"
                    
                    print(f"  {name:20}: {count:>12,}{rate}")
                else:
                    print(f"  {name:20}: {count}")
            
            if total > 0:
                print("-" * 40)
                print(f"  {'TOTAL':20}: {total:>12,}")
            
            # Store current counts for rate calculation
            previous_counts = counts
            
            # Check recent corporation sample
            try:
                result = supabase.table('sunbiz_corporate').select('entity_name, filing_date').order('filing_date', desc=True).limit(3).execute()
                if result.data:
                    print("\n  Recent corporations:")
                    for corp in result.data:
                        print(f"    - {corp.get('entity_name', 'N/A')[:50]} ({corp.get('filing_date', 'N/A')})")
            except:
                pass
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        
        # Final summary
        final_counts = get_table_counts()
        print("\nFinal counts:")
        print("-" * 40)
        total = 0
        for name, count in final_counts.items():
            if isinstance(count, int):
                total += count
                print(f"  {name:20}: {count:>12,}")
        
        if total > 0:
            print("-" * 40)
            print(f"  {'TOTAL':20}: {total:>12,}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Monitor Sunbiz data loading')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    
    args = parser.parse_args()
    monitor_progress(args.interval)