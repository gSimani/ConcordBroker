#!/usr/bin/env python3
"""
Test the Florida Daily Update System
"""

import os
import sys
import json
from pathlib import Path

def test_system():
    """Test if the Florida update system is properly configured"""
    print("Florida Daily Update System - Configuration Test")
    print("=" * 50)
    
    # Check if directories exist
    base_dir = Path("florida_daily_updates")
    if not base_dir.exists():
        print("ERROR: florida_daily_updates directory not found")
        return False
    
    print("OK: Base directory exists")
    
    # Check for required files
    required_files = [
        "agents/monitor.py",
        "agents/downloader.py", 
        "agents/processor.py",
        "agents/database_updater.py",
        "agents/orchestrator.py",
        "config/config.yaml",
        "config/counties.json",
        "scripts/run_daily_update.py"
    ]
    
    all_files_exist = True
    for file in required_files:
        file_path = base_dir / file
        if file_path.exists():
            print(f"OK: {file}")
        else:
            print(f"MISSING: {file}")
            all_files_exist = False
    
    if not all_files_exist:
        print("\nERROR: Some required files are missing")
        return False
    
    # Check counties configuration
    counties_file = base_dir / "config" / "counties.json"
    try:
        with open(counties_file, 'r') as f:
            counties = json.load(f)
        
        # Check Broward County in the florida_counties array
        florida_counties = counties.get("florida_counties", [])
        broward = None
        for county in florida_counties:
            if county.get("name") == "Broward":
                broward = county
                break
        
        if broward and broward.get("active"):
            print(f"\nOK: Broward County is enabled")
            print(f"   Name: {broward.get('name')}")
            print(f"   Code: {broward.get('code')}")
            print(f"   Population: {broward.get('population', 'N/A'):,}")
            print(f"   Priority: {broward.get('priority', 'N/A')}")
            print(f"   Notes: {broward.get('notes', 'N/A')}")
        else:
            print("\nERROR: Broward County not enabled in configuration")
            return False
            
    except Exception as e:
        print(f"\nERROR reading counties config: {e}")
        return False
    
    # Check environment configuration
    env_file = Path(".env")
    if env_file.exists():
        print("\nOK: Environment file exists")
        # Check for required variables
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        required_vars = ["VITE_SUPABASE_URL", "VITE_SUPABASE_ANON_KEY"]
        for var in required_vars:
            if var in env_content:
                print(f"OK: {var} is configured")
            else:
                print(f"WARNING: {var} not found in .env")
    else:
        print("\nWARNING: No .env file found - using defaults")
    
    print("\n" + "=" * 50)
    print("SYSTEM STATUS: READY")
    print("\nTo run a test update for Broward County:")
    print("  python florida_daily_updates/scripts/run_daily_update.py --mode test")
    print("\nTo schedule daily updates:")
    print("  Windows: Run florida_daily_updates/scripts/schedule_task.bat as Administrator")
    print("  Linux: Run florida_daily_updates/scripts/install_cron.sh")
    
    return True

if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)