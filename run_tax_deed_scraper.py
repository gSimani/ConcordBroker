"""
Run Tax Deed Scraper with proper environment configuration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path('.env')
if env_path.exists():
    load_dotenv(env_path)
    print("[OK] Loaded environment variables from .env")
else:
    print("[ERROR] .env file not found!")
    sys.exit(1)

# Verify required environment variables
required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)
    else:
        print(f"[OK] {var}: {os.getenv(var)[:50]}...")

if missing_vars:
    print(f"[ERROR] Missing environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Change to workers directory and import the module
sys.path.insert(0, str(Path('apps/workers').absolute()))
os.chdir('apps/workers')

# Import and run the sync
import asyncio
from tax_deed_supabase_agent import run_sync

print("\n" + "="*60)
print("Starting Tax Deed Auction Scraper")
print("="*60 + "\n")

# Run the sync
asyncio.run(run_sync())