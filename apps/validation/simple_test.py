"""
Simple test - no Unicode
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from validation.config import config

print("=" * 60)
print("UI FIELD VALIDATION - SETUP TEST")
print("=" * 60)

print("\n1. Configuration:")
print(f"  Target URL: {config.TARGET_SITE_URL}")
print(f"  Staging URL: {config.STAGING_URL}")
print(f"  Supabase URL: {config.SUPABASE_URL[:40]}...")
print(f"  Firecrawl API: {'OK' if config.FIRECRAWL_API_KEY else 'NOT SET'}")
print(f"  Output Dir: {config.OUTPUT_DIR}")
print(f"  Max Pages: {config.CRAWL_MAX_PAGES}")
print(f"  Crawl Depth: {config.CRAWL_DEPTH}")
print(f"  Fuzzy Threshold: {config.FUZZY_MATCH_THRESHOLD}%")
print(f"  Label Mappings: {len(config.LABEL_MAPPINGS)} configured")

print("\n2. Sample Label Mappings:")
sample_mappings = list(config.LABEL_MAPPINGS.items())[:10]
for label, field in sample_mappings:
    print(f"  '{label}' -> {field}")

print("\n3. Validation Tables:")
for table in config.VALIDATION_TABLES:
    print(f"  - {table}")

print("\n=" * 60)
print("SETUP TEST COMPLETE")
print("=" * 60)

print("\nNEXT STEPS:")
print("1. Ensure FIRECRAWL_API_KEY is set in .env")
print("2. Run: python -m apps.validation.ui_field_validator --help")
print("3. Test with one property: --property-ids <ID>")
print("4. Review validation/config.py for custom mappings")

print("\n")
