#!/usr/bin/env python3
"""
Reorganize Root Directory - Move 617+ Python files into organized structure
Created: 2025-11-09
Purpose: Fix critical project organization issue
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict
import json
from datetime import datetime

# Define categorization rules (order matters - first match wins)
CATEGORIES = {
    'analysis': {
        'patterns': ['analyze_', 'analysis_', 'comprehensive_'],
        'description': 'Data analysis and reporting scripts'
    },
    'verification': {
        'patterns': ['verify_', 'validation_', 'validate_'],
        'description': 'Data verification and validation scripts'
    },
    'data-checking': {
        'patterns': ['check_', 'count_', 'compare_', 'trace_'],
        'description': 'Data checking and inspection scripts'
    },
    'data-loading': {
        'patterns': ['load_', 'upload_', 'import_'],
        'description': 'Data loading and upload scripts'
    },
    'deployment': {
        'patterns': ['deploy_', 'create_table', 'create_schema'],
        'description': 'Database deployment and schema creation'
    },
    'fixes': {
        'patterns': ['fix_', 'update_', 'migrate_', 'upgrade_'],
        'description': 'Data fixing and migration scripts'
    },
    'debugging': {
        'patterns': ['debug_', 'test_', 'demo_'],
        'description': 'Debugging and testing utilities'
    },
    'audit': {
        'patterns': ['audit_'],
        'description': 'Database and system audit scripts'
    },
    'automation': {
        'patterns': ['auto_'],
        'description': 'Automated processes and workflows'
    },
    'scraping': {
        'patterns': ['scrape_', 'scraper_', 'download_', 'fetch_'],
        'description': 'Web scraping and data download scripts'
    },
}

# Files to keep in root (critical or actively used)
KEEP_IN_ROOT = [
    'production_property_api.py',  # Production API
    'manage.py',  # Django management (if exists)
    'setup.py',  # Package setup
    'conftest.py',  # Pytest config
    '__init__.py',  # Package marker
]

# Folders to skip
SKIP_FOLDERS = {
    'apps', 'scripts', 'agents', 'supabase', 'database', 'data',
    'node_modules', '.git', '__pycache__', '.venv', 'venv',
    'backups', 'archive', 'archived_agents_20250910_224956',
    'analysis-scripts-archived', 'analysis-scripts-cleaned',
    'env_backup_2025-09-05_18-41-53', 'florida_property_data',
    'historical_data', 'mcp_servers', 'railway-orchestrator',
    'sunbiz_data', 'vector_stores', '.railway', '.memory', '.claude',
    'archive-cleanup-2025', 'db'
}

class DirectoryReorganizer:
    def __init__(self, root_dir, dry_run=True):
        self.root_dir = Path(root_dir)
        self.dry_run = dry_run
        self.moves = defaultdict(list)
        self.skipped = []
        self.errors = []
        self.kept_in_root = []

    def categorize_file(self, filename):
        """Determine which category a file belongs to"""
        name_lower = filename.lower()

        # Check if should keep in root
        if filename in KEEP_IN_ROOT:
            return 'root'

        # Check each category
        for category, info in CATEGORIES.items():
            for pattern in info['patterns']:
                if name_lower.startswith(pattern):
                    return category

        return 'misc'  # Uncategorized

    def scan_root_files(self):
        """Scan root directory for Python files"""
        python_files = []

        for item in self.root_dir.iterdir():
            # Skip directories
            if item.is_dir():
                if item.name not in SKIP_FOLDERS:
                    # Check if it's a folder we're skipping
                    pass
                continue

            # Only process .py files
            if item.suffix == '.py':
                python_files.append(item.name)

        return python_files

    def create_directory_structure(self):
        """Create the new directory structure"""
        scripts_dir = self.root_dir / 'scripts-organized'

        if not self.dry_run:
            scripts_dir.mkdir(exist_ok=True)

        for category, info in CATEGORIES.items():
            category_dir = scripts_dir / category
            if not self.dry_run:
                category_dir.mkdir(exist_ok=True)

                # Create README in each category
                readme_path = category_dir / 'README.md'
                readme_content = f"# {category.replace('-', ' ').title()}\n\n{info['description']}\n"
                readme_path.write_text(readme_content)

        # Create misc folder for uncategorized
        misc_dir = scripts_dir / 'misc'
        if not self.dry_run:
            misc_dir.mkdir(exist_ok=True)
            readme_path = misc_dir / 'README.md'
            readme_content = "# Miscellaneous Scripts\n\nUncategorized scripts that don't fit other categories.\n"
            readme_path.write_text(readme_content)

        return scripts_dir

    def move_file(self, filename, category, scripts_dir):
        """Move a file to its category folder"""
        source = self.root_dir / filename

        if category == 'root':
            self.kept_in_root.append(filename)
            return

        dest_folder = scripts_dir / category
        dest = dest_folder / filename

        try:
            if not self.dry_run:
                shutil.move(str(source), str(dest))

            self.moves[category].append(filename)

        except Exception as e:
            self.errors.append({
                'file': filename,
                'category': category,
                'error': str(e)
            })

    def generate_report(self):
        """Generate reorganization report"""
        total_moved = sum(len(files) for files in self.moves.values())

        report = []
        report.append("=" * 80)
        report.append("  ROOT DIRECTORY REORGANIZATION REPORT")
        report.append("=" * 80)
        report.append(f"  Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        report.append(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 80)
        report.append(f"  Files moved:        {total_moved}")
        report.append(f"  Files kept in root: {len(self.kept_in_root)}")
        report.append(f"  Files skipped:      {len(self.skipped)}")
        report.append(f"  Errors:             {len(self.errors)}")
        report.append("")

        # Files by category
        report.append("📁 FILES BY CATEGORY")
        report.append("-" * 80)
        for category in sorted(self.moves.keys()):
            files = self.moves[category]
            category_name = category.replace('-', ' ').title()
            report.append(f"\n  {category_name} ({len(files)} files):")
            report.append(f"  → scripts-organized/{category}/")
            for file in sorted(files)[:5]:  # Show first 5
                report.append(f"     - {file}")
            if len(files) > 5:
                report.append(f"     ... and {len(files) - 5} more")

        report.append("")

        # Kept in root
        if self.kept_in_root:
            report.append("✅ FILES KEPT IN ROOT")
            report.append("-" * 80)
            for file in sorted(self.kept_in_root):
                report.append(f"  - {file}")
            report.append("")

        # Errors
        if self.errors:
            report.append("❌ ERRORS")
            report.append("-" * 80)
            for error in self.errors:
                report.append(f"  - {error['file']}: {error['error']}")
            report.append("")

        # Next steps
        if self.dry_run:
            report.append("🎯 NEXT STEPS")
            report.append("-" * 80)
            report.append("  This was a DRY RUN - no files were moved.")
            report.append("  Review the report above, then run with dry_run=False to apply changes.")
            report.append("")
            report.append("  To apply changes:")
            report.append("    python reorganize_root_directory.py --apply")
        else:
            report.append("✅ REORGANIZATION COMPLETE")
            report.append("-" * 80)
            report.append("  All files have been moved to scripts-organized/")
            report.append("")
            report.append("  Next steps:")
            report.append("    1. Review the new structure: scripts-organized/")
            report.append("    2. Update any imports that reference moved files")
            report.append("    3. Commit changes: git add . && git commit -m 'refactor: reorganize root Python files'")
            report.append("    4. Optional: Rename scripts-organized/ to scripts/ after verification")

        report.append("=" * 80)

        return "\n".join(report)

    def save_manifest(self, scripts_dir):
        """Save a JSON manifest of all moves"""
        manifest = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'total_moved': sum(len(files) for files in self.moves.values()),
            'categories': {
                category: {
                    'count': len(files),
                    'files': sorted(files)
                }
                for category, files in self.moves.items()
            },
            'kept_in_root': sorted(self.kept_in_root),
            'errors': self.errors
        }

        manifest_path = scripts_dir / 'REORGANIZATION_MANIFEST.json'
        if not self.dry_run:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            print(f"\n📄 Manifest saved to: {manifest_path}")

        return manifest

    def run(self):
        """Execute the reorganization"""
        print("🔍 Scanning root directory...")
        python_files = self.scan_root_files()

        if not python_files:
            print("✅ No Python files found in root directory!")
            return

        print(f"📦 Found {len(python_files)} Python files in root")

        print("📁 Creating directory structure...")
        scripts_dir = self.create_directory_structure()

        print("🚀 Categorizing and moving files...")
        for filename in python_files:
            category = self.categorize_file(filename)
            self.move_file(filename, category, scripts_dir)

        print("📊 Generating report...")
        report = self.generate_report()
        print("\n" + report)

        # Save manifest
        self.save_manifest(scripts_dir)

        # Save report to file
        report_filename = f"reorganization_report_{'dryrun' if self.dry_run else 'applied'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = self.root_dir / report_filename
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n>>> Report saved to: {report_path}")


def main():
    import argparse
    import sys

    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Reorganize root directory Python files')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    parser.add_argument('--root', default='.', help='Root directory path (default: current directory)')

    args = parser.parse_args()

    dry_run = not args.apply
    root_dir = Path(args.root).resolve()

    print(f"\n>>> Root Directory: {root_dir}")
    print(f">>> Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")

    if not dry_run:
        print("\n!!! WARNING: This will move files! Press Ctrl+C to cancel...")
        import time
        time.sleep(3)

    reorganizer = DirectoryReorganizer(root_dir, dry_run=dry_run)
    reorganizer.run()

    print("\n=== Done!")


if __name__ == '__main__':
    main()
