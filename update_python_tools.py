#!/usr/bin/env python3
"""
Python Environment Update Script
Updates outdated packages and installs missing tools
"""

import subprocess
import sys
import time

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
            timeout=300  # 5 minute timeout
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
    print("PYTHON ENVIRONMENT UPDATE SCRIPT")
    print(f"Python Version: {sys.version}")
    print("="*80)

    # First, upgrade pip itself
    print("\n[STEP 1] Upgrading pip to latest version...")
    run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Upgrading pip"
    )

    # Update outdated packages
    print("\n[STEP 2] Updating outdated packages...")
    outdated_packages = [
        ("numpy", "NumPy - Numerical computing"),
        ("matplotlib", "Matplotlib - Data visualization"),
        ("beautifulsoup4", "BeautifulSoup - Web scraping"),
        ("scrapy", "Scrapy - Web scraping framework"),
        ("pillow", "Pillow - Image processing")
    ]

    for package, description in outdated_packages:
        run_command(
            f"{sys.executable} -m pip install --upgrade {package}",
            f"Updating {description}"
        )
        time.sleep(1)  # Small delay between installations

    # Install missing tools
    print("\n[STEP 3] Installing missing tools...")
    missing_tools = [
        ("tensorflow", "TensorFlow - Deep learning framework"),
        ("keras", "Keras - Neural network API"),
        ("spacy", "spaCy - Advanced NLP library"),
        ("pyspark", "PySpark - Big data processing"),
        ("jupyter", "Jupyter - Interactive computing"),
        ("notebook", "Notebook - Jupyter notebook server")
    ]

    for package, description in missing_tools:
        run_command(
            f"{sys.executable} -m pip install {package}",
            f"Installing {description}"
        )
        time.sleep(1)

    # Special case: Download spaCy language model
    print("\n[STEP 4] Downloading spaCy English language model...")
    run_command(
        f"{sys.executable} -m spacy download en_core_web_sm",
        "Downloading spaCy English model"
    )

    # Fix dependency conflicts
    print("\n[STEP 5] Attempting to fix dependency conflicts...")

    # Try to fix httpx version conflict
    run_command(
        f"{sys.executable} -m pip install 'httpx>=0.24,<0.28'",
        "Fixing httpx version conflict"
    )

    # Try to fix cryptography version conflict
    run_command(
        f"{sys.executable} -m pip install 'cryptography>=38.0.0,<42'",
        "Fixing cryptography version conflict"
    )

    # Clean up invalid distribution
    print("\n[STEP 6] Cleaning up invalid distributions...")
    run_command(
        f"{sys.executable} -m pip check",
        "Checking for remaining dependency issues"
    )

    print("\n" + "="*80)
    print("UPDATE COMPLETE")
    print("="*80)
    print("\nRecommended next steps:")
    print("1. Run 'python python_audit.py' to verify all installations")
    print("2. Restart any Python kernels or IDEs to use updated packages")
    print("3. Test critical functionality with updated packages")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)