#!/usr/bin/env python3
"""
Python Environment Audit Tool
Checks for commonly used Python libraries and their versions
"""

import subprocess
import sys
import json
from datetime import datetime
import importlib.metadata as metadata

# Define the tools to check with their package names and latest stable versions (as of Jan 2025)
TOOLS_TO_CHECK = {
    # Data manipulation & numerical
    "pandas": {"import_name": "pandas", "latest": "2.2.3"},
    "numpy": {"import_name": "numpy", "latest": "2.2.1"},

    # Visualization
    "matplotlib": {"import_name": "matplotlib", "latest": "3.9.3"},
    "seaborn": {"import_name": "seaborn", "latest": "0.13.2"},

    # Machine Learning
    "scikit-learn": {"import_name": "sklearn", "latest": "1.5.2"},
    "tensorflow": {"import_name": "tensorflow", "latest": "2.18.0"},
    "torch": {"import_name": "torch", "latest": "2.5.1"},
    "keras": {"import_name": "keras", "latest": "3.7.0"},

    # Database & Web
    "sqlalchemy": {"import_name": "sqlalchemy", "latest": "2.0.36"},
    "flask": {"import_name": "flask", "latest": "3.1.0"},
    "django": {"import_name": "django", "latest": "5.1.4"},
    "fastapi": {"import_name": "fastapi", "latest": "0.115.6"},

    # Web scraping
    "beautifulsoup4": {"import_name": "bs4", "latest": "4.12.3"},
    "scrapy": {"import_name": "scrapy", "latest": "2.12.0"},

    # Computer Vision & NLP
    "opencv-python": {"import_name": "cv2", "latest": "4.11.0.86"},
    "nltk": {"import_name": "nltk", "latest": "3.9.1"},
    "spacy": {"import_name": "spacy", "latest": "3.8.3"},

    # Big Data
    "pyspark": {"import_name": "pyspark", "latest": "3.5.4"},

    # Development tools
    "jupyter": {"import_name": "jupyter", "latest": "1.1.1"},
    "notebook": {"import_name": "notebook", "latest": "7.3.2"},
    "pillow": {"import_name": "PIL", "latest": "11.0.0"},
}

def get_package_version(package_name):
    """Get the installed version of a package."""
    try:
        version = metadata.version(package_name)
        return version
    except metadata.PackageNotFoundError:
        return None

def compare_versions(installed, latest):
    """Compare installed version with latest version."""
    try:
        installed_parts = list(map(int, installed.split('.')[:3]))
        latest_parts = list(map(int, latest.split('.')[:3]))

        for i in range(min(len(installed_parts), len(latest_parts))):
            if installed_parts[i] < latest_parts[i]:
                return "outdated"
            elif installed_parts[i] > latest_parts[i]:
                return "newer"
        return "up-to-date"
    except:
        return "unknown"

def check_dependencies(package_name):
    """Check if all dependencies are satisfied."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if package_name.lower() in result.stdout.lower() or package_name.lower() in result.stderr.lower():
            return False, result.stdout + result.stderr
        return True, "All dependencies satisfied"
    except subprocess.TimeoutExpired:
        return None, "Timeout checking dependencies"
    except Exception as e:
        return None, str(e)

def main():
    print("=" * 80)
    print("PYTHON ENVIRONMENT AUDIT REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version}")
    print("=" * 80)
    print()

    results = {
        "installed": [],
        "not_installed": [],
        "outdated": [],
        "up_to_date": [],
        "dependency_issues": []
    }

    # Check each tool
    for package_name, info in TOOLS_TO_CHECK.items():
        print(f"Checking {package_name}...", end=" ")

        version = get_package_version(package_name)

        if version:
            status = compare_versions(version, info["latest"])

            result_info = {
                "package": package_name,
                "installed_version": version,
                "latest_version": info["latest"],
                "status": status
            }

            results["installed"].append(result_info)

            if status == "outdated":
                results["outdated"].append(result_info)
                print(f"[INSTALLED] (v{version}) - OUTDATED (latest: v{info['latest']})")
            elif status == "up-to-date":
                results["up_to_date"].append(result_info)
                print(f"[INSTALLED] (v{version}) - UP TO DATE")
            else:
                print(f"[INSTALLED] (v{version}) - {status.upper()}")
        else:
            results["not_installed"].append({
                "package": package_name,
                "latest_version": info["latest"]
            })
            print(f"[NOT INSTALLED] (latest: v{info['latest']})")

    # Check for dependency issues
    print("\n" + "=" * 80)
    print("DEPENDENCY CHECK")
    print("=" * 80)

    result = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("[OK] All package dependencies are satisfied")
    else:
        print("[WARNING] Dependency issues found:")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        results["dependency_issues"].append(result.stdout + result.stderr)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tools checked: {len(TOOLS_TO_CHECK)}")
    print(f"Installed: {len(results['installed'])}")
    print(f"Not installed: {len(results['not_installed'])}")
    print(f"Up to date: {len(results['up_to_date'])}")
    print(f"Outdated: {len(results['outdated'])}")
    print(f"Dependency issues: {len(results['dependency_issues'])}")

    # Recommendations
    if results['outdated']:
        print("\n" + "=" * 80)
        print("UPDATE RECOMMENDATIONS")
        print("=" * 80)
        print("The following packages can be updated:")
        for pkg in results['outdated']:
            print(f"  pip install --upgrade {pkg['package']}")

    if results['not_installed']:
        print("\n" + "=" * 80)
        print("INSTALLATION RECOMMENDATIONS")
        print("=" * 80)
        print("The following packages are not installed:")
        for pkg in results['not_installed']:
            print(f"  pip install {pkg['package']}")

    # Save detailed report
    with open('python_audit_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n[SAVED] Detailed report saved to python_audit_report.json")

    return results

if __name__ == "__main__":
    main()