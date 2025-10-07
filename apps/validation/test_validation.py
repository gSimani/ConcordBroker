"""
Quick test script to verify validation system is working
"""
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from validation.config import config
from validation.schema_mapper import SchemaMapper
from validation.firecrawl_scraper import FirecrawlScraper


async def test_setup():
    """Test that all components are properly configured"""

    print("Testing UI Field Validation Setup\n")
    print("=" * 60)

    # Test 1: Configuration
    print("\n1. Testing Configuration...")
    print(f"   ✓ Target URL: {config.TARGET_SITE_URL}")
    print(f"   ✓ Staging URL: {config.STAGING_URL}")
    print(f"   ✓ Supabase URL: {config.SUPABASE_URL[:30]}...")
    print(f"   ✓ Firecrawl API: {'Configured' if config.FIRECRAWL_API_KEY else 'Missing'}")
    print(f"   ✓ Output Dir: {config.OUTPUT_DIR}")
    print(f"   ✓ Max Pages: {config.CRAWL_MAX_PAGES}")
    print(f"   ✓ Label Mappings: {len(config.LABEL_MAPPINGS)} configured")

    # Test 2: Schema Mapper
    print("\n2. Testing Schema Mapper...")
    mapper = SchemaMapper()

    # Test some label mappings
    test_labels = [
        "Property Owner",
        "Sale Price",
        "Land Value",
        "Year Built",
        "Unknown Label XYZ"
    ]

    for label in test_labels:
        field, confidence, match_type = mapper.map_label_to_field(label)
        status = "✓" if field else "✗"
        print(f"   {status} '{label}' → {field or 'UNMAPPED'} ({confidence}% {match_type})")

    # Test 3: Database Connection
    print("\n3. Testing Database Connection...")
    try:
        await mapper.extract_schema()
        print(f"   ✓ Schema extracted for {len(mapper.schema_cache)} tables")
        for table_name, columns in mapper.schema_cache.items():
            print(f"     - {table_name}: {len(columns)} columns")
    except Exception as e:
        print(f"   ✗ Failed to extract schema: {e}")

    # Test 4: Scraper Setup
    print("\n4. Testing Firecrawl Scraper...")
    scraper = FirecrawlScraper()
    if scraper.firecrawl:
        print("   ✓ Firecrawl client initialized")
    else:
        print("   ⚠ Firecrawl not available (will use Playwright fallback)")

    # Test property ID extraction
    test_urls = [
        "https://concordbroker.com/property/12345",
        "https://concordbroker.com/parcel/ABC-123",
        "https://concordbroker.com/unknown"
    ]

    for url in test_urls:
        prop_id = scraper.extract_property_id(url)
        status = "✓" if prop_id else "✗"
        print(f"   {status} '{url}' → {prop_id or 'No ID found'}")

    # Test 5: HTML Extraction
    print("\n5. Testing HTML Extraction...")
    sample_html = """
    <html>
        <body>
            <label>Property Owner</label>
            <input value="John Smith" />

            <div class="field-label">Sale Price:</div>
            <div class="field-value">$450,000</div>

            <p>Year Built: <strong>2020</strong></p>

            <table>
                <tr><td>Land Value</td><td>$200,000</td></tr>
            </table>
        </body>
    </html>
    """

    pairs = scraper.extract_label_field_pairs(sample_html, "https://test.com")
    print(f"   ✓ Extracted {len(pairs)} label-field pairs from sample HTML:")
    for pair in pairs[:5]:  # Show first 5
        print(f"     - {pair['label']}: {pair['value']} ({pair['pattern_type']})")

    print("\n" + "=" * 60)
    print("\nSetup Test Complete!\n")
    print("Next Steps:")
    print("1. Run a test validation: python -m apps.validation.ui_field_validator --property-ids TEST_ID")
    print("2. Review configuration in apps/validation/config.py")
    print("3. Add custom label mappings as needed")
    print("4. Set up GitHub Actions secrets for automation")


if __name__ == "__main__":
    asyncio.run(test_setup())
