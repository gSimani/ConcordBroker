"""
Main UI Field Validation Script

Usage:
    python -m apps.validation.ui_field_validator --url https://your-site.com
    python -m apps.validation.ui_field_validator --property-ids 12345,67890
    python -m apps.validation.ui_field_validator --format excel
"""
import asyncio
import argparse
from typing import List, Optional
from .config import config
from .schema_mapper import SchemaMapper
from .firecrawl_scraper import FirecrawlScraper
from .validator import FieldValidator
from .reporter import ValidationReporter


class UIFieldValidationOrchestrator:
    """Orchestrates the complete validation workflow"""

    def __init__(self):
        self.schema_mapper = SchemaMapper()
        self.scraper = FirecrawlScraper()
        self.validator = FieldValidator()
        self.reporter = ValidationReporter()

    async def run_validation(
        self,
        url: Optional[str] = None,
        property_ids: Optional[List[str]] = None,
        output_format: str = "excel"
    ) -> dict:
        """Run complete validation workflow"""

        print("🔍 UI Field Validation Started\n")

        # Step 1: Extract database schema
        print("📊 Extracting database schema...")
        await self.schema_mapper.extract_schema()
        print("✓ Schema extracted\n")

        # Step 2: Crawl website or validate specific properties
        if property_ids:
            print(f"🔎 Validating {len(property_ids)} specific properties...")
            results = await self.validator.validate_all_properties(property_ids)

        else:
            target_url = url or config.TARGET_SITE_URL
            print(f"🕷️  Crawling website: {target_url}")

            pages = await self.scraper.crawl_website(target_url)
            print(f"✓ Crawled {len(pages)} pages\n")

            # Step 3: Extract and validate fields
            print("🔍 Extracting and validating fields...")

            results = []
            for i, page in enumerate(pages, 1):
                print(f"  [{i}/{len(pages)}] Validating {page['url']}")

                property_id = self.scraper.extract_property_id(page['url'])
                if property_id:
                    result = await self.validator.validate_page(
                        page['url'],
                        page['html'],
                        property_id
                    )
                    results.append(result)

        print(f"\n✓ Validated {len(results)} pages\n")

        # Step 4: Generate reports
        print(f"📝 Generating {output_format} report...")
        report_files = self.reporter.generate_reports(results, output_format)

        print("\n✅ Validation Complete!\n")
        print("📄 Generated Reports:")
        for format_type, file_path in report_files.items():
            print(f"  - {format_type.upper()}: {file_path}")

        # Print summary
        summary = self._print_summary(results)

        return {
            'results': results,
            'report_files': report_files,
            'summary': summary
        }

    def _print_summary(self, results: List[dict]) -> dict:
        """Print validation summary to console"""

        total_pages = len(results)
        total_fields = 0
        total_matched = 0
        total_mismatched = 0
        total_unmapped = 0

        for result in results:
            summary = result.get('summary', {})
            total_fields += summary.get('total_fields', 0)
            total_matched += summary.get('matched', 0)
            total_mismatched += summary.get('mismatched', 0)
            total_unmapped += summary.get('unmapped', 0)

        match_percentage = round(
            (total_matched / total_fields * 100) if total_fields > 0 else 0,
            2
        )

        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Pages Validated:     {total_pages}")
        print(f"Total Fields:        {total_fields}")
        print(f"Matched:             {total_matched} ({match_percentage}%)")
        print(f"Mismatched:          {total_mismatched}")
        print(f"Unmapped:            {total_unmapped}")
        print("=" * 60 + "\n")

        if total_mismatched > 0:
            print("⚠️  WARNING: Found data mismatches!")
            print("   Review the report for details and fix recommendations.\n")

        if total_unmapped > 0:
            print("ℹ️  INFO: Found unmapped fields")
            print("   Add mappings to validation/config.py to improve coverage.\n")

        return {
            'total_pages': total_pages,
            'total_fields': total_fields,
            'total_matched': total_matched,
            'total_mismatched': total_mismatched,
            'total_unmapped': total_unmapped,
            'match_percentage': match_percentage
        }


async def main():
    """Main CLI entry point"""

    parser = argparse.ArgumentParser(
        description="Validate UI fields against database values"
    )

    parser.add_argument(
        '--url',
        type=str,
        help='Target website URL to crawl and validate'
    )

    parser.add_argument(
        '--property-ids',
        type=str,
        help='Comma-separated list of property IDs to validate'
    )

    parser.add_argument(
        '--format',
        type=str,
        choices=['excel', 'csv', 'json', 'markdown', 'all'],
        default='excel',
        help='Output format for reports (default: excel)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        help='Directory for output reports'
    )

    args = parser.parse_args()

    # Parse property IDs if provided
    property_ids = None
    if args.property_ids:
        property_ids = [pid.strip() for pid in args.property_ids.split(',')]

    # Override output directory if specified
    if args.output_dir:
        config.OUTPUT_DIR = args.output_dir

    # Run validation
    orchestrator = UIFieldValidationOrchestrator()

    try:
        await orchestrator.run_validation(
            url=args.url,
            property_ids=property_ids,
            output_format=args.format
        )

    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
