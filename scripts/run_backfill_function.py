"""
Execute the backfill_property_use_desc_batch function via Supabase RPC
Uses SERVICE_ROLE_KEY for write access
"""
import os
import time
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable not set")

# Initialize Supabase client with SERVICE_ROLE_KEY (has write access)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def run_backfill(county: str = None, batch_size: int = 10000):
    """
    Run the backfill function for a specific county or all counties

    Args:
        county: County name (e.g., 'BROWARD') or None for all counties
        batch_size: Number of rows per batch
    """
    print("="*80)
    print(f"BACKFILL PROPERTY USE DESCRIPTIONS")
    print("="*80)
    print(f"County: {county or 'ALL COUNTIES'}")
    print(f"Batch size: {batch_size:,}")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # Call the PostgreSQL function via RPC
        # The function returns a table, so we need to use rpc()
        params = {
            'p_county': county,
            'p_batch_size': batch_size
        }

        print(f"\nCalling backfill_property_use_desc_batch...")
        print(f"Parameters: {params}\n")

        response = supabase.rpc('backfill_property_use_desc_batch', params).execute()

        if response.data:
            print(f"\n{'Batch':<8} {'Rows Updated':<15} {'Total Processed':<20} {'Duration (s)':<15}")
            print("-" * 80)

            total_rows = 0
            for row in response.data:
                batch_num = row.get('batch_number', 0)
                rows_updated = row.get('rows_updated', 0)
                total_processed = row.get('total_processed', 0)
                duration = row.get('duration_seconds', 0)

                print(f"{batch_num:<8} {rows_updated:<15,} {total_processed:<20,} {duration:<15.2f}")
                total_rows = total_processed

            print("-" * 80)
            print(f"\nBACKFILL COMPLETE")
            print(f"Total rows updated: {total_rows:,}")
            print(f"Total batches: {len(response.data)}")

            if len(response.data) > 0:
                final_duration = response.data[-1].get('duration_seconds', 0)
                rate = total_rows / final_duration if final_duration > 0 else 0
                print(f"Total duration: {final_duration:.2f} seconds ({final_duration/60:.2f} minutes)")
                print(f"Average rate: {rate:.1f} rows/second")
        else:
            print("\nNo rows needed updating (all property_use_desc values already populated)")

    except Exception as e:
        print(f"\nERROR: {e}")
        print(f"\nException details:")
        import traceback
        traceback.print_exc()
        return False

    print(f"\nCompleted at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    return True

if __name__ == '__main__':
    import sys

    # Get county from command line argument if provided
    county = sys.argv[1] if len(sys.argv) > 1 else 'BROWARD'
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10000

    print(f"\nEnvironment:")
    print(f"  SUPABASE_URL: {SUPABASE_URL}")
    print(f"  SERVICE_ROLE_KEY: {'Set' if SUPABASE_SERVICE_KEY else 'Not set'}")
    print()

    success = run_backfill(county, batch_size)

    if success:
        print("\nSUCCESS - Property use descriptions backfilled!")
    else:
        print("\nFAILED - Check error messages above")
        sys.exit(1)
