#!/usr/bin/env python3
"""
Setup script for NAL data import pipeline
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'pandas',
        'asyncpg',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} - MISSING")
    
    if missing_packages:
        print(f"\nInstall missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_environment():
    """Check environment variables"""
    required_vars = [
        'DATABASE_URL',
        'SUPABASE_URL', 
        'SUPABASE_KEY'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}")
        else:
            missing_vars.append(var)
            print(f"✗ {var} - MISSING")
    
    if missing_vars:
        print(f"\nSet missing environment variables:")
        for var in missing_vars:
            print(f"export {var}=your_value_here")
        return False
    
    return True

def check_nal_file():
    """Check if NAL file exists"""
    project_root = Path(__file__).parent.parent
    nal_file = project_root / "TEMP" / "NAL16P202501.csv"
    
    if nal_file.exists():
        print(f"✓ NAL file found: {nal_file}")
        print(f"  File size: {nal_file.stat().st_size / (1024*1024):.1f} MB")
        return str(nal_file)
    else:
        print(f"✗ NAL file not found: {nal_file}")
        print("  Download NAL data file and place it in TEMP directory")
        return None

def main():
    print("=" * 50)
    print("NAL DATA IMPORT SETUP")
    print("=" * 50)
    
    print("\n1. Checking Python dependencies...")
    deps_ok = check_dependencies()
    
    print("\n2. Checking environment variables...")
    env_ok = check_environment()
    
    print("\n3. Checking NAL data file...")
    nal_file = check_nal_file()
    
    print("\n" + "=" * 50)
    
    if deps_ok and env_ok and nal_file:
        print("✓ SETUP COMPLETE - Ready to import!")
        print("\nTo run the import:")
        print(f"python scripts/import_nal_data.py {nal_file}")
        
        # Ask if user wants to run import now
        response = input("\nRun import now? (y/N): ").lower().strip()
        if response == 'y':
            print("\nStarting import...")
            import_script = Path(__file__).parent / "import_nal_data.py"
            subprocess.run([sys.executable, str(import_script), nal_file])
    else:
        print("✗ SETUP INCOMPLETE - Fix issues above and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()