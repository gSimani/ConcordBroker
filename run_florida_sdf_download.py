#!/usr/bin/env python3
"""
Run Florida SDF Download
Main executable script for downloading and processing Florida Sales Data Files.
Provides a simple command-line interface for common operations.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import json

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from florida_sdf_master_orchestrator import FloridaSdfMasterOrchestrator
from florida_counties_manager import FloridaCountiesManager
from test_florida_sdf_system import main as run_tests


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Florida SDF Data Download & Processing System             ║
║                                                                              ║
║  Download, process, and upload Sales Data Files (SDF) for all 67 Florida    ║
║  counties from the Florida Department of Revenue to Supabase database.      ║
║                                                                              ║
║  Total Properties: ~7.41 Million                                            ║
║  Data Source: https://floridarevenue.com/property/dataportal                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def list_counties():
    """List all Florida counties with information"""
    print("\nFlorida Counties Information")
    print("=" * 80)

    manager = FloridaCountiesManager()

    # Priority counties
    print("\n🏆 PRIORITY COUNTIES (Largest by population):")
    priority = manager.get_priority_counties()
    for i, county in enumerate(priority, 1):
        info = manager.get_county_info(county)
        print(f"  {i:2d}. {county:<15} (Code: {info['code']}) - High property volume")

    # Test counties
    print("\n🧪 TEST COUNTIES (Smaller, good for testing):")
    test_counties = manager.get_test_counties()
    for i, county in enumerate(test_counties, 1):
        info = manager.get_county_info(county)
        print(f"  {i:2d}. {county:<15} (Code: {info['code']}) - Small county")

    # Sample URLs
    print("\n🔗 SAMPLE DOWNLOAD URLS:")
    samples = ['MIAMI_DADE', 'BROWARD', 'ST_JOHNS']
    for county in samples:
        info = manager.get_county_info(county)
        print(f"  {county}: {info['download_url']}")

    print(f"\n📊 TOTAL: {len(manager.get_all_counties())} Florida counties")


def check_prerequisites():
    """Check system prerequisites"""
    print("\nChecking Prerequisites...")
    print("-" * 50)

    issues = []

    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        issues.append(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
    else:
        print("✅ Python version: OK")

    # Check required packages
    required_packages = [
        'requests', 'pandas', 'supabase', 'psycopg2', 'tqdm', 'chardet'
    ]

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: OK")
        except ImportError:
            issues.append(f"Missing package: {package}")
            print(f"❌ {package}: Missing")

    # Check environment variables
    env_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY',
        'POSTGRES_URL'
    ]

    for var in env_vars:
        if os.getenv(var):
            print(f"✅ {var}: OK")
        else:
            issues.append(f"Missing environment variable: {var}")
            print(f"❌ {var}: Missing")

    # Check disk space (rough estimate)
    working_dir = Path("C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP")
    try:
        stat = os.statvfs(working_dir) if hasattr(os, 'statvfs') else None
        if stat:
            free_bytes = stat.f_bavail * stat.f_frsize
            free_gb = free_bytes / (1024**3)
            if free_gb < 50:  # Need at least 50GB
                issues.append(f"Insufficient disk space: {free_gb:.1f}GB available, need 50GB+")
            else:
                print(f"✅ Disk space: {free_gb:.1f}GB available")
        else:
            print("⚠️  Disk space: Cannot check on Windows")
    except:
        print("⚠️  Disk space: Cannot check")

    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nPlease fix these issues before running the system.")
        return False
    else:
        print("\n✅ All prerequisites met!")
        return True


def run_test_mode():
    """Run system in test mode"""
    print("\nRunning Test Mode...")
    print("-" * 50)

    try:
        orchestrator = FloridaSdfMasterOrchestrator(
            max_concurrent_counties=1,
            test_mode=True,
            enable_recovery=True
        )

        print("🧪 Test mode configuration:")
        print(f"   - Working directory: {orchestrator.working_dir}")
        print(f"   - Max concurrent: {orchestrator.max_concurrent_counties}")
        print(f"   - Recovery enabled: {orchestrator.enable_recovery}")

        # Run test pipeline
        result = orchestrator.run_complete_pipeline()

        print("\n📊 Test Results:")
        summary = result['summary']
        print(f"   - Counties processed: {summary['counties_completed']}/{summary['total_counties']}")
        print(f"   - Records processed: {summary['total_records_processed']:,}")
        print(f"   - Records uploaded: {summary['total_records_uploaded']:,}")
        print(f"   - Success rate: {summary['success_rate_percent']:.1f}%")
        print(f"   - Processing time: {result['session_info']['processing_time_hours']:.2f} hours")

        if summary['counties_failed'] > 0:
            print(f"   - Failed counties: {result['failed_counties']}")

        return summary['counties_failed'] == 0

    except Exception as e:
        print(f"❌ Test mode failed: {e}")
        return False


def run_production_mode(max_concurrent=2, specific_counties=None):
    """Run system in production mode"""
    if specific_counties:
        print(f"\nRunning Production Mode for specific counties: {specific_counties}")
    else:
        print("\nRunning Production Mode for ALL 67 Florida counties...")

    print("-" * 80)
    print("⚠️  WARNING: This will download and process data for all counties.")
    print("   This process may take several hours and use significant bandwidth/storage.")

    response = input("\nDo you want to continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Operation cancelled by user.")
        return False

    try:
        orchestrator = FloridaSdfMasterOrchestrator(
            max_concurrent_counties=max_concurrent,
            test_mode=False,
            enable_recovery=True
        )

        print("🚀 Production mode configuration:")
        print(f"   - Working directory: {orchestrator.working_dir}")
        print(f"   - Max concurrent: {orchestrator.max_concurrent_counties}")
        print(f"   - Recovery enabled: {orchestrator.enable_recovery}")

        # Run production pipeline
        if specific_counties:
            # Process specific counties
            results = orchestrator.process_all_counties(specific_counties)
            result = orchestrator.generate_final_report(results)
        else:
            # Run complete pipeline
            result = orchestrator.run_complete_pipeline()

        print("\n📊 Production Results:")
        summary = result['summary']
        print(f"   - Counties processed: {summary['counties_completed']}/{summary['total_counties']}")
        print(f"   - Records processed: {summary['total_records_processed']:,}")
        print(f"   - Records uploaded: {summary['total_records_uploaded']:,}")
        print(f"   - Success rate: {summary['success_rate_percent']:.1f}%")
        print(f"   - Processing time: {result['session_info']['processing_time_hours']:.2f} hours")

        if summary['counties_failed'] > 0:
            print(f"   - Failed counties: {result['failed_counties']}")

        return summary['counties_failed'] == 0

    except Exception as e:
        print(f"❌ Production mode failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_status():
    """Show current system status"""
    print("\nSystem Status")
    print("-" * 50)

    # Check for existing state files
    working_dir = Path("C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP/FLORIDA_SDF")
    progress_file = working_dir / 'orchestration_progress.json'

    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                state = json.load(f)

            print("📊 Found existing processing state:")
            print(f"   - Session ID: {state.get('session_id', 'Unknown')}")
            print(f"   - Last updated: {state.get('last_save', 'Unknown')}")
            print(f"   - Completed counties: {len(state.get('completed_counties', []))}")
            print(f"   - Failed counties: {len(state.get('failed_counties', []))}")

            if state.get('completed_counties'):
                print(f"   - Recent completions: {state['completed_counties'][-5:]}")

            if state.get('failed_counties'):
                print(f"   - Failed: {state['failed_counties']}")

        except Exception as e:
            print(f"❌ Error reading state file: {e}")
    else:
        print("📝 No existing processing state found.")

    # Check database connection
    try:
        from supabase_uploader import SupabaseBatchUploader
        uploader = SupabaseBatchUploader()
        print("✅ Database connection: OK")
    except Exception as e:
        print(f"❌ Database connection: Failed ({e})")

    # Check disk space
    if working_dir.exists():
        print(f"📁 Working directory: {working_dir}")
        print(f"   - Exists: {working_dir.exists()}")

        # Count files in subdirectories
        subdirs = ['downloads', 'processed', 'logs', 'reports']
        for subdir in subdirs:
            subdir_path = working_dir / subdir
            if subdir_path.exists():
                file_count = len(list(subdir_path.rglob('*')))
                print(f"   - {subdir}: {file_count} files")


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description='Florida SDF Data Download & Processing System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --test                     # Run test mode with small counties
  %(prog)s --check                    # Check prerequisites
  %(prog)s --list-counties            # List all counties
  %(prog)s --production               # Run production mode (all counties)
  %(prog)s --counties MIAMI_DADE BROWARD  # Process specific counties
  %(prog)s --status                   # Show current system status
  %(prog)s --run-tests                # Run comprehensive test suite
        """
    )

    parser.add_argument('--test', action='store_true',
                       help='Run in test mode with small counties')

    parser.add_argument('--production', action='store_true',
                       help='Run in production mode (all 67 counties)')

    parser.add_argument('--counties', nargs='+',
                       help='Process specific counties')

    parser.add_argument('--max-concurrent', type=int, default=2,
                       help='Maximum concurrent county processing (default: 2)')

    parser.add_argument('--check', action='store_true',
                       help='Check system prerequisites')

    parser.add_argument('--list-counties', action='store_true',
                       help='List all Florida counties')

    parser.add_argument('--status', action='store_true',
                       help='Show current system status')

    parser.add_argument('--run-tests', action='store_true',
                       help='Run comprehensive test suite')

    args = parser.parse_args()

    # Show banner
    print_banner()

    # Handle different commands
    if args.check:
        success = check_prerequisites()
        return 0 if success else 1

    elif args.list_counties:
        list_counties()
        return 0

    elif args.status:
        show_status()
        return 0

    elif args.run_tests:
        print("\nRunning Comprehensive Test Suite...")
        print("-" * 80)
        success = run_tests()
        return 0 if success else 1

    elif args.test:
        print("\n🧪 Starting Test Mode...")
        success = run_test_mode()
        return 0 if success else 1

    elif args.production:
        print("\n🚀 Starting Production Mode...")
        success = run_production_mode(args.max_concurrent)
        return 0 if success else 1

    elif args.counties:
        print(f"\n🎯 Processing specific counties: {args.counties}")
        # Validate counties
        manager = FloridaCountiesManager()
        invalid_counties = [c for c in args.counties if not manager.validate_county(c)]
        if invalid_counties:
            print(f"❌ Invalid counties: {invalid_counties}")
            return 1

        success = run_production_mode(args.max_concurrent, args.counties)
        return 0 if success else 1

    else:
        # No specific command, show help and options
        print("\nNo command specified. Available options:")
        print("-" * 50)
        print("1. --check           - Check system prerequisites")
        print("2. --list-counties   - List all Florida counties")
        print("3. --run-tests       - Run comprehensive test suite")
        print("4. --test            - Run test mode (small counties)")
        print("5. --production      - Run production mode (all counties)")
        print("6. --counties X Y Z  - Process specific counties")
        print("7. --status          - Show current system status")
        print("\nUse --help for detailed usage information.")

        return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)