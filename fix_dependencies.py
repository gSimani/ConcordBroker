#!/usr/bin/env python3
"""
Fix Python dependency conflicts
"""

import subprocess
import sys

def run_command(cmd, description):
    """Run a pip command with error handling."""
    print(f"\n{'='*60}")
    print(f"[RUNNING] {description}")
    print(f"Command: {cmd}")
    print('='*60)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print(f"[SUCCESS] {description}")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"[WARNING] {description} - Some issues occurred")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"Error details: {result.stderr}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"[ERROR] {description} - Timeout after 5 minutes")
        return False
    except Exception as e:
        print(f"[ERROR] {description} - {str(e)}")
        return False

def main():
    print("="*80)
    print("FIXING PYTHON DEPENDENCY CONFLICTS")
    print(f"Python Version: {sys.version}")
    print("="*80)

    # Fix httpx version conflict by downgrading
    print("\n[STEP 1] Fixing httpx version conflict...")
    run_command(
        f"{sys.executable} -m pip install 'httpx==0.27.2' --force-reinstall",
        "Downgrading httpx to 0.27.2"
    )

    # Fix NumPy version conflict for memvid and numba
    print("\n[STEP 2] Fixing NumPy compatibility...")
    # Try to update numba to a version compatible with NumPy 2.x
    run_command(
        f"{sys.executable} -m pip install --upgrade numba",
        "Upgrading numba for NumPy 2.x compatibility"
    )

    # Remove the invalid Flask distribution
    print("\n[STEP 3] Cleaning up invalid Flask distribution...")
    import os
    site_packages = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages")
    invalid_flask = os.path.join(site_packages, "~lask")

    if os.path.exists(invalid_flask):
        try:
            import shutil
            shutil.rmtree(invalid_flask)
            print(f"[SUCCESS] Removed invalid Flask distribution at {invalid_flask}")
        except Exception as e:
            print(f"[WARNING] Could not remove invalid Flask distribution: {e}")
    else:
        print("[INFO] Invalid Flask distribution not found or already removed")

    # Reinstall Flask to ensure it's properly installed
    print("\n[STEP 4] Reinstalling Flask...")
    run_command(
        f"{sys.executable} -m pip uninstall -y flask",
        "Uninstalling Flask"
    )
    run_command(
        f"{sys.executable} -m pip install flask",
        "Reinstalling Flask"
    )

    # Final dependency check
    print("\n[STEP 5] Final dependency check...")
    run_command(
        f"{sys.executable} -m pip check",
        "Checking all dependencies"
    )

    print("\n" + "="*80)
    print("DEPENDENCY FIX COMPLETE")
    print("="*80)

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)