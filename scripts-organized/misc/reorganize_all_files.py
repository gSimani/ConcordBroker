#!/usr/bin/env python3
"""
Complete Root Directory Reorganization
Organizes Python, SQL, Markdown, CSV, and other files
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict
import json
from datetime import datetime
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Python file categories
PY_CATEGORIES = {
    'analysis': ['analyze_', 'analysis_', 'comprehensive_'],
    'verification': ['verify_', 'validation_', 'validate_'],
    'data-checking': ['check_', 'count_', 'compare_', 'trace_'],
    'data-loading': ['load_', 'upload_', 'import_'],
    'deployment': ['deploy_', 'create_table', 'create_schema'],
    'fixes': ['fix_', 'update_', 'migrate_', 'upgrade_'],
    'debugging': ['debug_', 'test_', 'demo_'],
    'audit': ['audit_'],
    'automation': ['auto_'],
    'scraping': ['scrape_', 'scraper_', 'download_', 'fetch_'],
}

# SQL file categories
SQL_CATEGORIES = {
    'migrations': ['migration', 'create_table', 'add_column', 'alter_'],
    'indexes': ['index', 'idx_'],
    'queries': ['select_', 'query_', 'report_'],
    'fixes': ['fix_', 'update_', 'patch_'],
}

# Markdown categories
MD_CATEGORIES = {
    'audit-reports': ['audit', 'report', 'analysis', 'review'],
    'guides': ['guide', 'quick_start', 'getting_started', 'setup'],
    'completed-work': ['complete', 'completed', 'done', 'finished', 'ready'],
    'documentation': ['readme', 'doc', 'documentation'],
    'plans': ['plan', 'roadmap', 'strategy', 'architecture'],
}

# Files to keep in root
KEEP_IN_ROOT = {
    # Python
    'production_property_api.py',
    'manage.py',
    'setup.py',
    'conftest.py',
    '__init__.py',
    # Markdown
    'README.md',
    'CONTRIBUTING.md',
    'LICENSE.md',
    'CHANGELOG.md',
    'CODE_OF_CONDUCT.md',
    'CLAUDE.md',
}

SKIP_FOLDERS = {
    'apps', 'scripts', 'agents', 'supabase', 'database', 'data',
    'node_modules', '.git', '__pycache__', '.venv', 'venv',
    'backups', 'archive', 'scripts-organized', 'docs-organized',
    'archived_agents_20250910_224956',
    'analysis-scripts-archived', 'analysis-scripts-cleaned',
    'env_backup_2025-09-05_18-41-53', 'florida_property_data',
    'historical_data', 'mcp_servers', 'railway-orchestrator',
    'sunbiz_data', 'vector_stores', '.railway', '.memory', '.claude',
    'archive-cleanup-2025', 'db', 'sql'
}

class ComprehensiveReorganizer:
    def __init__(self, root_dir, dry_run=True):
        self.root_dir = Path(root_dir)
        self.dry_run = dry_run
        self.moves = defaultdict(lambda: defaultdict(list))  # {file_type: {category: [files]}}
        self.kept_in_root = []
        self.errors = []

    def categorize_python(self, filename):
        """Categorize Python file"""
        if filename in KEEP_IN_ROOT:
            return 'root'

        name_lower = filename.lower()
        for category, patterns in PY_CATEGORIES.items():
            if any(name_lower.startswith(p) for p in patterns):
                return category
        return 'misc'

    def categorize_sql(self, filename):
        """Categorize SQL file"""
        name_lower = filename.lower()
        for category, patterns in SQL_CATEGORIES.items():
            if any(p in name_lower for p in patterns):
                return category
        return 'misc'

    def categorize_markdown(self, filename):
        """Categorize Markdown file"""
        if filename in KEEP_IN_ROOT:
            return 'root'

        name_lower = filename.lower().replace('_', ' ').replace('-', ' ')
        for category, patterns in MD_CATEGORIES.items():
            if any(p in name_lower for p in patterns):
                return category
        return 'misc'

    def scan_files(self):
        """Scan root directory for files to organize"""
        files_by_type = defaultdict(list)

        for item in self.root_dir.iterdir():
            if item.is_dir() or item.name in SKIP_FOLDERS:
                continue

            ext = item.suffix.lower()
            if ext in ['.py', '.sql', '.md', '.csv']:
                files_by_type[ext].append(item.name)

        return files_by_type

    def create_structure(self):
        """Create organized directory structure"""
        structures = {
            '.py': self.root_dir / 'scripts-organized',
            '.sql': self.root_dir / 'sql',
            '.md': self.root_dir / 'docs',
            '.csv': self.root_dir / 'data' / 'raw',
        }

        for file_type, base_dir in structures.items():
            if not self.dry_run:
                base_dir.mkdir(parents=True, exist_ok=True)

            # Create category subdirectories
            categories = {
                '.py': list(PY_CATEGORIES.keys()) + ['misc'],
                '.sql': list(SQL_CATEGORIES.keys()) + ['misc'],
                '.md': list(MD_CATEGORIES.keys()) + ['misc'],
                '.csv': ['import'],
            }

            for category in categories.get(file_type, ['misc']):
                cat_dir = base_dir / category
                if not self.dry_run:
                    cat_dir.mkdir(exist_ok=True)

        return structures

    def move_file(self, filename, file_type, category, base_dir):
        """Move file to organized location"""
        if category == 'root':
            self.kept_in_root.append(filename)
            return

        source = self.root_dir / filename
        dest_folder = base_dir / category
        dest = dest_folder / filename

        try:
            if not self.dry_run:
                shutil.move(str(source), str(dest))
            self.moves[file_type][category].append(filename)
        except Exception as e:
            self.errors.append({'file': filename, 'error': str(e)})

    def generate_report(self):
        """Generate comprehensive report"""
        total_moved = sum(
            len(files)
            for categories in self.moves.values()
            for files in categories.values()
        )

        report = []
        report.append("=" * 80)
        report.append("  COMPLETE ROOT DIRECTORY REORGANIZATION")
        report.append("=" * 80)
        report.append(f"  Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        report.append(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")

        # Summary by file type
        report.append("SUMMARY BY FILE TYPE")
        report.append("-" * 80)
        for file_type in ['.py', '.sql', '.md', '.csv']:
            count = sum(len(files) for files in self.moves.get(file_type, {}).values())
            if count > 0:
                type_name = {'.py': 'Python', '.sql': 'SQL', '.md': 'Markdown', '.csv': 'CSV'}[file_type]
                report.append(f"  {type_name}: {count} files")
        report.append(f"  Kept in root: {len(self.kept_in_root)}")
        report.append(f"  Errors: {len(self.errors)}")
        report.append("")

        # Detailed breakdown
        report.append("DETAILED BREAKDOWN")
        report.append("-" * 80)

        for file_type, categories in sorted(self.moves.items()):
            type_name = {'.py': 'Python', '.sql': 'SQL', '.md': 'Markdown', '.csv': 'CSV'}.get(file_type, file_type)
            base_dir = {'.py': 'scripts-organized', '.sql': 'sql', '.md': 'docs', '.csv': 'data/raw'}.get(file_type, 'organized')

            report.append(f"\n{type_name} Files:")
            for category, files in sorted(categories.items()):
                report.append(f"  {category}/ ({len(files)} files) -> {base_dir}/{category}/")
                for file in sorted(files)[:3]:
                    report.append(f"    - {file}")
                if len(files) > 3:
                    report.append(f"    ... and {len(files) - 3} more")

        # Kept in root
        if self.kept_in_root:
            report.append("\nFILES KEPT IN ROOT")
            report.append("-" * 80)
            for file in sorted(self.kept_in_root):
                report.append(f"  - {file}")

        # Errors
        if self.errors:
            report.append("\nERRORS")
            report.append("-" * 80)
            for error in self.errors:
                report.append(f"  - {error['file']}: {error['error']}")

        # Next steps
        report.append("")
        if self.dry_run:
            report.append("NEXT STEPS")
            report.append("-" * 80)
            report.append("  This was a DRY RUN - no files were moved.")
            report.append("  To apply changes:")
            report.append("    python reorganize_all_files.py --apply")
        else:
            report.append("REORGANIZATION COMPLETE")
            report.append("-" * 80)
            report.append("  Files organized into:")
            report.append("    - scripts-organized/ (Python files)")
            report.append("    - sql/ (SQL files)")
            report.append("    - docs/ (Markdown files)")
            report.append("    - data/raw/ (CSV files)")
            report.append("")
            report.append("  Next steps:")
            report.append("    1. Review organized structure")
            report.append("    2. Update any file references in code")
            report.append("    3. Commit changes to git")

        report.append("=" * 80)
        return "\n".join(report)

    def run(self):
        """Execute reorganization"""
        print(">>> Scanning root directory...")
        files_by_type = self.scan_files()

        total_files = sum(len(files) for files in files_by_type.values())
        if total_files == 0:
            print("=== No files to organize!")
            return

        print(f">>> Found:")
        for file_type, files in files_by_type.items():
            type_name = {'.py': 'Python', '.sql': 'SQL', '.md': 'Markdown', '.csv': 'CSV'}.get(file_type, file_type)
            print(f"    {len(files)} {type_name} files")

        print("\n>>> Creating directory structure...")
        structures = self.create_structure()

        print(">>> Organizing files...")
        categorizers = {
            '.py': self.categorize_python,
            '.sql': self.categorize_sql,
            '.md': self.categorize_markdown,
            '.csv': lambda f: 'import',  # All CSVs go to import folder
        }

        for file_type, files in files_by_type.items():
            categorizer = categorizers.get(file_type, lambda f: 'misc')
            base_dir = structures[file_type]

            for filename in files:
                category = categorizer(filename)
                self.move_file(filename, file_type, category, base_dir)

        print("\n>>> Generating report...")
        report = self.generate_report()
        print("\n" + report)

        # Save report
        report_filename = f"complete_reorganization_{'dryrun' if self.dry_run else 'applied'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = self.root_dir / report_filename
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n>>> Report saved to: {report_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Reorganize all root directory files')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    parser.add_argument('--root', default='.', help='Root directory (default: current)')

    args = parser.parse_args()
    dry_run = not args.apply
    root_dir = Path(args.root).resolve()

    print(f"\n>>> Root Directory: {root_dir}")
    print(f">>> Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}\n")

    if not dry_run:
        print("!!! WARNING: This will move files! Press Ctrl+C to cancel...")
        import time
        time.sleep(3)

    reorganizer = ComprehensiveReorganizer(root_dir, dry_run=dry_run)
    reorganizer.run()

    print("\n=== Done!")


if __name__ == '__main__':
    main()
