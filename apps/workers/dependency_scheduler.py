"""
ConcordBroker Dependency Scheduler
Runs both Python and NPM dependency monitors on a schedule
Integrates with MCP Server for automated notifications
"""

import asyncio
import schedule
import time
import subprocess
import sys
import logging
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DependencyScheduler:
    """Schedules and runs dependency monitoring tasks"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.python_monitor = self.project_root / "apps" / "workers" / "dependency_monitor_agent.py"
        self.npm_monitor = self.project_root / "apps" / "workers" / "npm_dependency_monitor.js"

        # Schedule configuration
        self.check_interval_hours = 6  # Check every 6 hours
        self.daily_report_time = "09:00"  # Daily report at 9 AM

        self.last_results = {
            'python': None,
            'npm': None,
            'last_check': None
        }

    def run_python_monitor(self):
        """Run the Python dependency monitor"""
        try:
            logger.info("🐍 Running Python dependency monitor...")
            result = subprocess.run(
                [sys.executable, str(self.python_monitor)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode == 0:
                logger.info("✅ Python dependency check completed successfully")
                return True
            else:
                logger.error(f"❌ Python dependency check failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error running Python monitor: {e}")
            return False

    def run_npm_monitor(self):
        """Run the NPM dependency monitor"""
        try:
            logger.info("📦 Running NPM dependency monitor...")
            result = subprocess.run(
                ['node', str(self.npm_monitor)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode == 0:
                logger.info("✅ NPM dependency check completed successfully")
                return True
            else:
                logger.error(f"❌ NPM dependency check failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error running NPM monitor: {e}")
            return False

    def run_full_check(self):
        """Run both Python and NPM dependency checks"""
        logger.info(f"🔍 Starting scheduled dependency check at {datetime.now()}")

        python_success = self.run_python_monitor()
        npm_success = self.run_npm_monitor()

        # Load results
        self.load_latest_results()

        # Log summary
        if python_success and npm_success:
            logger.info("✅ All dependency checks completed successfully")
            self.generate_summary_report()
        else:
            logger.warning("⚠️ Some dependency checks failed")

        self.last_results['last_check'] = datetime.now().isoformat()

    def load_latest_results(self):
        """Load the latest results from both monitors"""
        try:
            # Load Python results
            python_report = self.project_root / "dependency_monitor_report.json"
            if python_report.exists():
                with open(python_report, 'r') as f:
                    self.last_results['python'] = json.load(f)

            # Load NPM results
            npm_report = self.project_root / "npm_dependency_report.json"
            if npm_report.exists():
                with open(npm_report, 'r') as f:
                    self.last_results['npm'] = json.load(f)

        except Exception as e:
            logger.error(f"Error loading results: {e}")

    def generate_summary_report(self):
        """Generate a combined summary report"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'python': {
                    'total_checked': 0,
                    'updates_available': 0,
                    'critical_updates': 0
                },
                'npm': {
                    'total_projects': 0,
                    'total_packages': 0,
                    'updates_available': 0,
                    'critical_updates': 0
                },
                'combined': {
                    'total_updates': 0,
                    'total_critical': 0,
                    'needs_attention': False
                }
            }

            # Process Python results
            if self.last_results['python']:
                py_summary = self.last_results['python'].get('summary', {})
                summary['python'].update(py_summary)

            # Process NPM results
            if self.last_results['npm']:
                npm_summary = self.last_results['npm'].get('summary', {})
                summary['npm'].update(npm_summary)

            # Calculate combined totals
            summary['combined']['total_updates'] = (
                summary['python']['updates_available'] +
                summary['npm']['updates_available']
            )
            summary['combined']['total_critical'] = (
                summary['python']['critical_updates'] +
                summary['npm']['critical_updates']
            )
            summary['combined']['needs_attention'] = summary['combined']['total_critical'] > 0

            # Save summary
            summary_file = self.project_root / "dependency_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)

            # Print summary
            self.print_summary(summary)

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None

    def print_summary(self, summary):
        """Print a formatted summary to console"""
        print("\n" + "="*60)
        print("  ConcordBroker Dependency Check Summary")
        print("="*60)
        print(f"  Timestamp: {summary['timestamp']}")
        print()

        print("📊 Python Dependencies:")
        print(f"   Total checked: {summary['python']['total_checked']}")
        print(f"   Updates available: {summary['python']['updates_available']}")
        print(f"   Critical updates: {summary['python']['critical_updates']}")
        print()

        print("📦 NPM Dependencies:")
        print(f"   Projects checked: {summary['npm']['total_projects']}")
        print(f"   Packages checked: {summary['npm']['total_packages']}")
        print(f"   Updates available: {summary['npm']['updates_available']}")
        print(f"   Critical updates: {summary['npm']['critical_updates']}")
        print()

        print("🎯 Combined Summary:")
        print(f"   Total updates: {summary['combined']['total_updates']}")
        print(f"   Critical updates: {summary['combined']['total_critical']}")

        if summary['combined']['needs_attention']:
            print("   🚨 ACTION REQUIRED: Critical updates available!")
        else:
            print("   ✅ All dependencies up to date")

        print("="*60)

    def setup_schedule(self):
        """Setup the monitoring schedule"""
        # Schedule regular checks every 6 hours
        schedule.every(self.check_interval_hours).hours.do(self.run_full_check)

        # Schedule daily report
        schedule.every().day.at(self.daily_report_time).do(self.run_full_check)

        # Run an initial check
        logger.info("🚀 Starting dependency scheduler...")
        logger.info(f"   - Regular checks: Every {self.check_interval_hours} hours")
        logger.info(f"   - Daily report: {self.daily_report_time}")

        # Run initial check
        self.run_full_check()

    def run_scheduler(self):
        """Main scheduler loop"""
        self.setup_schedule()

        logger.info("⏰ Dependency scheduler is running...")
        logger.info("   Press Ctrl+C to stop")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("🛑 Dependency scheduler stopped by user")

def create_startup_script():
    """Create a startup script for the dependency scheduler"""
    project_root = Path(__file__).parent.parent.parent

    script_content = f"""@echo off
echo ================================================================
echo  ConcordBroker Dependency Monitor Scheduler
echo  Monitors Python and NPM dependencies automatically
echo ================================================================
echo.

title ConcordBroker Dependency Monitor

echo Starting dependency scheduler...
cd /d "{project_root}"
python apps\\workers\\dependency_scheduler.py

echo.
echo Dependency scheduler stopped.
pause
"""

    script_path = project_root / "start_dependency_monitor.bat"
    with open(script_path, 'w') as f:
        f.write(script_content)

    logger.info(f"📝 Startup script created: {script_path}")
    return script_path

def main():
    """Main entry point"""
    # Create startup script
    create_startup_script()

    # Run scheduler
    scheduler = DependencyScheduler()

    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run once for testing
        scheduler.run_full_check()
    else:
        # Run continuous scheduler
        scheduler.run_scheduler()

if __name__ == "__main__":
    main()