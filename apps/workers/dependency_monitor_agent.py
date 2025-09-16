"""
ConcordBroker Dependency Monitor Agent
Monitors critical Python and Node.js dependencies for updates
Integrates with MCP Server for notifications and automated updates
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import re
from dataclasses import dataclass
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PackageInfo:
    name: str
    current_version: str
    latest_version: str
    release_notes_url: str
    pypi_url: str
    update_command: str
    is_critical: bool = False
    last_checked: Optional[datetime] = None
    has_update: bool = False

class DependencyMonitorAgent:
    """Monitors and tracks dependency updates for ConcordBroker"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.mcp_url = "http://localhost:3001"
        self.mcp_api_key = "concordbroker-mcp-key"

        # Critical Python packages for ConcordBroker
        self.monitored_packages = {
            'pandas': {
                'release_notes': 'https://pandas.pydata.org/docs/whatsnew/index.html',
                'pypi': 'https://pypi.org/project/pandas/',
                'critical': True,
                'description': 'Data manipulation'
            },
            'numpy': {
                'release_notes': 'https://numpy.org/doc/stable/release.html',
                'pypi': 'https://pypi.org/project/numpy/',
                'critical': True,
                'description': 'Numerical computing'
            },
            'fastapi': {
                'release_notes': 'https://fastapi.tiangolo.com/release-notes/',
                'pypi': 'https://pypi.org/project/fastapi/',
                'critical': True,
                'description': 'API development'
            },
            'supabase': {
                'release_notes': 'https://github.com/supabase/supabase-py/releases',
                'pypi': 'https://pypi.org/project/supabase/',
                'critical': True,
                'description': 'Supabase client'
            },
            'matplotlib': {
                'release_notes': 'https://matplotlib.org/stable/users/release_notes.html',
                'pypi': 'https://pypi.org/project/matplotlib/',
                'critical': False,
                'description': 'Data visualization'
            },
            'seaborn': {
                'release_notes': 'https://seaborn.pydata.org/whatsnew.html',
                'pypi': 'https://pypi.org/project/seaborn/',
                'critical': False,
                'description': 'Data visualization'
            },
            'scikit-learn': {
                'release_notes': 'https://scikit-learn.org/stable/whats_new.html',
                'pypi': 'https://pypi.org/project/scikit-learn/',
                'critical': False,
                'description': 'Machine learning'
            },
            'tensorflow': {
                'release_notes': 'https://github.com/tensorflow/tensorflow/releases',
                'pypi': 'https://pypi.org/project/tensorflow/',
                'critical': False,
                'description': 'Deep learning'
            },
            'torch': {
                'release_notes': 'https://github.com/pytorch/pytorch/releases',
                'pypi': 'https://pypi.org/project/torch/',
                'critical': False,
                'description': 'PyTorch deep learning'
            },
            'sqlalchemy': {
                'release_notes': 'https://docs.sqlalchemy.org/en/20/changelog/index.html',
                'pypi': 'https://pypi.org/project/SQLAlchemy/',
                'critical': True,
                'description': 'Database interaction'
            },
            'beautifulsoup4': {
                'release_notes': 'https://www.crummy.com/software/BeautifulSoup/bs4/doc/#release-notes',
                'pypi': 'https://pypi.org/project/beautifulsoup4/',
                'critical': False,
                'description': 'Web scraping'
            },
            'scrapy': {
                'release_notes': 'https://docs.scrapy.org/en/latest/news.html',
                'pypi': 'https://pypi.org/project/Scrapy/',
                'critical': False,
                'description': 'Web scraping framework'
            },
            'opencv-python': {
                'release_notes': 'https://github.com/opencv/opencv-python/releases',
                'pypi': 'https://pypi.org/project/opencv-python/',
                'critical': False,
                'description': 'Computer vision'
            },
            'nltk': {
                'release_notes': 'https://www.nltk.org/changelog.html',
                'pypi': 'https://pypi.org/project/nltk/',
                'critical': False,
                'description': 'Natural language processing'
            },
            'spacy': {
                'release_notes': 'https://github.com/explosion/spaCy/releases',
                'pypi': 'https://pypi.org/project/spacy/',
                'critical': False,
                'description': 'Advanced NLP'
            },
            'pyspark': {
                'release_notes': 'https://spark.apache.org/releases.html',
                'pypi': 'https://pypi.org/project/pyspark/',
                'critical': False,
                'description': 'Big data processing'
            },
            'jupyter': {
                'release_notes': 'https://github.com/jupyter/notebook/releases',
                'pypi': 'https://pypi.org/project/notebook/',
                'critical': False,
                'description': 'Jupyter notebooks'
            },
            'keras': {
                'release_notes': 'https://github.com/keras-team/keras/releases',
                'pypi': 'https://pypi.org/project/keras/',
                'critical': False,
                'description': 'Neural networks'
            },
            'pillow': {
                'release_notes': 'https://pillow.readthedocs.io/en/stable/releasenotes/index.html',
                'pypi': 'https://pypi.org/project/Pillow/',
                'critical': False,
                'description': 'Image processing'
            }
        }

        self.report_file = self.project_root / "dependency_monitor_report.json"
        self.last_check_file = self.project_root / "dependency_last_check.json"

    async def check_all_dependencies(self) -> Dict:
        """Check all monitored dependencies for updates"""
        logger.info("🔍 Starting dependency update check...")

        # Get currently installed packages
        installed_packages = await self.get_installed_packages()

        # Check each monitored package
        results = {
            'timestamp': datetime.now().isoformat(),
            'packages': {},
            'summary': {
                'total_checked': 0,
                'updates_available': 0,
                'critical_updates': 0,
                'errors': 0
            }
        }

        for package_name, package_config in self.monitored_packages.items():
            try:
                logger.info(f"Checking {package_name}...")

                current_version = installed_packages.get(package_name, "Not installed")
                latest_version = await self.get_latest_version(package_name)

                has_update = False
                if current_version != "Not installed" and latest_version:
                    has_update = self.version_compare(current_version, latest_version)

                package_info = PackageInfo(
                    name=package_name,
                    current_version=current_version,
                    latest_version=latest_version or "Unknown",
                    release_notes_url=package_config['release_notes'],
                    pypi_url=package_config['pypi'],
                    update_command=f"py -m pip install -U {package_name}",
                    is_critical=package_config['critical'],
                    last_checked=datetime.now(),
                    has_update=has_update
                )

                results['packages'][package_name] = {
                    'current_version': package_info.current_version,
                    'latest_version': package_info.latest_version,
                    'has_update': package_info.has_update,
                    'is_critical': package_info.is_critical,
                    'description': package_config['description'],
                    'release_notes_url': package_info.release_notes_url,
                    'pypi_url': package_info.pypi_url,
                    'update_command': package_info.update_command,
                    'last_checked': package_info.last_checked.isoformat()
                }

                results['summary']['total_checked'] += 1
                if has_update:
                    results['summary']['updates_available'] += 1
                    if package_info.is_critical:
                        results['summary']['critical_updates'] += 1

            except Exception as e:
                logger.error(f"Error checking {package_name}: {e}")
                results['summary']['errors'] += 1
                results['packages'][package_name] = {
                    'error': str(e),
                    'last_checked': datetime.now().isoformat()
                }

        # Save results
        await self.save_report(results)

        # Notify MCP Server if critical updates available
        if results['summary']['critical_updates'] > 0:
            await self.notify_mcp_server(results)

        return results

    async def get_installed_packages(self) -> Dict[str, str]:
        """Get list of currently installed packages and versions"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                check=True
            )

            packages = {}
            for package in json.loads(result.stdout):
                packages[package['name'].lower().replace('-', '_')] = package['version']

            return packages

        except Exception as e:
            logger.error(f"Error getting installed packages: {e}")
            return {}

    async def get_latest_version(self, package_name: str) -> Optional[str]:
        """Get latest version from PyPI"""
        try:
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data['info']['version']
        except Exception as e:
            logger.error(f"Error getting latest version for {package_name}: {e}")

        return None

    def version_compare(self, current: str, latest: str) -> bool:
        """Compare versions to determine if update is available"""
        try:
            # Simple version comparison (could be enhanced with packaging.version)
            current_parts = [int(x) for x in current.split('.') if x.isdigit()]
            latest_parts = [int(x) for x in latest.split('.') if x.isdigit()]

            # Pad shorter version with zeros
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))

            return latest_parts > current_parts

        except Exception:
            return False

    async def save_report(self, results: Dict):
        """Save dependency report to file"""
        try:
            with open(self.report_file, 'w') as f:
                json.dump(results, f, indent=2)

            # Also save timestamp of last check
            with open(self.last_check_file, 'w') as f:
                json.dump({'last_check': datetime.now().isoformat()}, f)

            logger.info(f"Report saved to {self.report_file}")

        except Exception as e:
            logger.error(f"Error saving report: {e}")

    async def notify_mcp_server(self, results: Dict):
        """Notify MCP Server about critical updates"""
        try:
            critical_updates = [
                pkg for pkg, info in results['packages'].items()
                if info.get('has_update') and info.get('is_critical')
            ]

            notification_data = {
                'type': 'dependency_update',
                'timestamp': datetime.now().isoformat(),
                'critical_updates': critical_updates,
                'total_updates': results['summary']['updates_available'],
                'message': f"🚨 {len(critical_updates)} critical dependency updates available"
            }

            response = requests.post(
                f"{self.mcp_url}/api/notifications",
                headers={'x-api-key': self.mcp_api_key},
                json=notification_data,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("MCP Server notified about critical updates")
            else:
                logger.warning(f"Failed to notify MCP Server: {response.status_code}")

        except Exception as e:
            logger.error(f"Error notifying MCP Server: {e}")

    async def auto_update_packages(self, package_names: List[str], dry_run: bool = True) -> Dict:
        """Automatically update specified packages (with dry-run option)"""
        results = {
            'updated': [],
            'failed': [],
            'skipped': [],
            'dry_run': dry_run
        }

        for package_name in package_names:
            try:
                if dry_run:
                    logger.info(f"DRY RUN: Would update {package_name}")
                    results['skipped'].append(package_name)
                else:
                    logger.info(f"Updating {package_name}...")

                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', '-U', package_name],
                        capture_output=True,
                        text=True,
                        check=True
                    )

                    if result.returncode == 0:
                        results['updated'].append(package_name)
                        logger.info(f"✅ Successfully updated {package_name}")
                    else:
                        results['failed'].append(package_name)
                        logger.error(f"❌ Failed to update {package_name}")

            except Exception as e:
                logger.error(f"Error updating {package_name}: {e}")
                results['failed'].append(package_name)

        return results

    async def generate_update_script(self) -> str:
        """Generate a batch script to update all packages"""
        script_content = """@echo off
echo ================================================================
echo  ConcordBroker Dependency Update Script
echo  Auto-generated on {timestamp}
echo ================================================================
echo.

echo Checking Python and pip...
python --version
py -m pip --version

echo.
echo Updating pip first...
py -m pip install -U pip

echo.
echo Updating ConcordBroker dependencies...

""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Add update commands for each package
        for package_name, config in self.monitored_packages.items():
            if config['critical']:
                script_content += f'echo Updating {package_name} ({config["description"]})...\n'
                script_content += f'py -m pip install -U {package_name}\n\n'

        script_content += """echo.
echo ================================================================
echo  Update Complete! Checking for issues...
echo ================================================================
py -m pip check

echo.
echo Generating updated requirements...
py -m pip freeze > requirements-updated.txt

echo.
echo Update script completed!
pause
"""

        # Save script
        script_path = self.project_root / "update_dependencies.bat"
        with open(script_path, 'w') as f:
            f.write(script_content)

        logger.info(f"Update script saved to {script_path}")
        return str(script_path)

async def main():
    """Main entry point for dependency monitoring"""
    monitor = DependencyMonitorAgent()

    # Check all dependencies
    results = await monitor.check_all_dependencies()

    # Print summary
    summary = results['summary']
    print(f"\n📊 Dependency Check Summary:")
    print(f"   Total packages checked: {summary['total_checked']}")
    print(f"   Updates available: {summary['updates_available']}")
    print(f"   Critical updates: {summary['critical_updates']}")
    print(f"   Errors: {summary['errors']}")

    # Show packages with updates
    if summary['updates_available'] > 0:
        print(f"\n🔄 Packages with updates available:")
        for pkg, info in results['packages'].items():
            if info.get('has_update'):
                status = "🚨 CRITICAL" if info.get('is_critical') else "📦 Optional"
                print(f"   {status} {pkg}: {info['current_version']} → {info['latest_version']}")

    # Generate update script
    script_path = await monitor.generate_update_script()
    print(f"\n📝 Update script generated: {script_path}")

    return results

if __name__ == "__main__":
    asyncio.run(main())