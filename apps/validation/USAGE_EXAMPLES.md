# UI Field Validation - Usage Examples

## Quick Examples

### 1. Validate Entire Production Site

```bash
python -m apps.validation.ui_field_validator \
  --url https://concordbroker.com \
  --format excel
```

**Output:**
- Excel report with all validations
- Console summary with match percentage
- Mismatch details and fix recommendations

---

### 2. Validate Specific Properties

```bash
python -m apps.validation.ui_field_validator \
  --property-ids 123456,789012,345678 \
  --format all
```

**Generates:**
- Excel, CSV, JSON, and Markdown reports
- Focused validation on 3 properties only

---

### 3. Generate All Report Formats

```bash
python -m apps.validation.ui_field_validator \
  --url https://staging.concordbroker.com \
  --format all \
  --output-dir ./my-reports
```

**Creates:**
```
my-reports/
├── validation_report_20250101_120000.xlsx
├── validation_results_20250101_120000.csv
├── validation_results_20250101_120000.json
└── validation_report_20250101_120000.md
```

---

## Advanced Examples

### 4. Custom Configuration

```python
# custom_validation.py
import asyncio
from apps.validation import UIFieldValidationOrchestrator, config

# Override configuration
config.TARGET_SITE_URL = "https://my-custom-site.com"
config.CRAWL_MAX_PAGES = 500
config.FUZZY_MATCH_THRESHOLD = 90

# Add custom mappings
config.LABEL_MAPPINGS.update({
    "owner information": "owner_name",
    "tax year": "tax_year",
    "assessment value": "av_sd"
})

async def main():
    orchestrator = UIFieldValidationOrchestrator()
    results = await orchestrator.run_validation(
        url="https://my-custom-site.com",
        output_format="excel"
    )
    print(f"✅ Validation complete: {results['summary']['match_percentage']}% match rate")

asyncio.run(main())
```

Run it:
```bash
python custom_validation.py
```

---

### 5. Programmatic Access to Results

```python
import asyncio
import json
from apps.validation import UIFieldValidationOrchestrator

async def analyze_mismatches():
    orchestrator = UIFieldValidationOrchestrator()

    results = await orchestrator.run_validation(
        url="https://concordbroker.com",
        output_format="json"
    )

    # Analyze mismatches
    critical_mismatches = []

    for result in results['results']:
        for validation in result['validations']:
            if validation['status'] == 'mismatch':
                critical_mismatches.append({
                    'page': result['page_url'],
                    'property_id': result['property_id'],
                    'label': validation['label'],
                    'displayed': validation['value'],
                    'expected': validation['expected_value'],
                    'field': validation['db_field']
                })

    # Export critical mismatches
    with open('critical_mismatches.json', 'w') as f:
        json.dump(critical_mismatches, f, indent=2)

    print(f"Found {len(critical_mismatches)} critical mismatches")
    print("Exported to: critical_mismatches.json")

asyncio.run(analyze_mismatches())
```

---

### 6. Integration with Existing Test Suite

```python
# tests/test_ui_validation.py
import pytest
import asyncio
from apps.validation import UIFieldValidationOrchestrator

@pytest.mark.asyncio
async def test_ui_field_accuracy():
    """Test that UI displays accurate database values"""

    orchestrator = UIFieldValidationOrchestrator()

    results = await orchestrator.run_validation(
        property_ids=["12345", "67890"],  # Test properties
        output_format="json"
    )

    # Assert no mismatches
    total_mismatches = sum(
        r['summary']['mismatched']
        for r in results['results']
    )

    assert total_mismatches == 0, \
        f"Found {total_mismatches} data mismatches in UI"

@pytest.mark.asyncio
async def test_field_mapping_coverage():
    """Test that all fields are properly mapped"""

    orchestrator = UIFieldValidationOrchestrator()

    results = await orchestrator.run_validation(
        property_ids=["12345"],
        output_format="json"
    )

    # Assert high mapping coverage
    total_fields = results['results'][0]['summary']['total_fields']
    unmapped = results['results'][0]['summary']['unmapped']

    coverage = ((total_fields - unmapped) / total_fields) * 100

    assert coverage >= 95, \
        f"Field mapping coverage is {coverage}%, expected >= 95%"
```

Run tests:
```bash
pytest tests/test_ui_validation.py -v
```

---

### 7. Continuous Integration Example

```yaml
# .github/workflows/pr-validation.yml
name: PR UI Validation

on:
  pull_request:
    paths:
      - 'apps/web/**'
      - 'apps/api/**'

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd apps/validation
          pip install -r requirements.txt
          playwright install chromium

      - name: Run validation
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_KEY }}
          FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_KEY }}
        run: |
          python -m apps.validation.ui_field_validator \
            --url ${{ secrets.PREVIEW_URL }} \
            --format all

      - name: Fail on mismatches
        run: |
          # Check JSON report for mismatches
          python -c "
          import json, sys
          with open('validation_reports/*.json') as f:
              data = json.load(f)
              mismatches = sum(r['summary']['mismatched'] for r in data)
              if mismatches > 0:
                  print(f'❌ Found {mismatches} mismatches')
                  sys.exit(1)
          "
```

---

### 8. Scheduled Daily Validation

```python
# scripts/daily_validation.py
import asyncio
import smtplib
from email.mime.text import MIMEText
from apps.validation import UIFieldValidationOrchestrator

async def daily_validation():
    orchestrator = UIFieldValidationOrchestrator()

    results = await orchestrator.run_validation(
        url="https://concordbroker.com",
        output_format="all"
    )

    summary = results['summary']

    # Send email report if mismatches found
    if summary['total_mismatched'] > 0:
        send_alert_email(summary)

def send_alert_email(summary):
    msg = MIMEText(f"""
    Daily UI Validation Alert

    Found {summary['total_mismatched']} data mismatches!

    Summary:
    - Total Fields: {summary['total_fields']}
    - Match Rate: {summary['match_percentage']}%
    - Mismatched: {summary['total_mismatched']}
    - Unmapped: {summary['total_unmapped']}

    Review the reports in ./validation_reports/
    """)

    msg['Subject'] = 'UI Validation Alert - Mismatches Found'
    msg['From'] = 'alerts@concordbroker.com'
    msg['To'] = 'dev-team@concordbroker.com'

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('user', 'password')
        server.send_message(msg)

if __name__ == "__main__":
    asyncio.run(daily_validation())
```

Setup cron job:
```bash
# Run daily at 6 AM
0 6 * * * cd /path/to/project && python scripts/daily_validation.py
```

---

### 9. Validate Specific Page Types

```python
# validate_property_pages.py
import asyncio
from apps.validation import FirecrawlScraper, FieldValidator, ValidationReporter

async def validate_property_pages():
    scraper = FirecrawlScraper()
    validator = FieldValidator()
    reporter = ValidationReporter()

    # Crawl only property pages
    pages = await scraper.crawl_website(
        "https://concordbroker.com",
        max_pages=100
    )

    # Filter to property pages only
    property_pages = [
        p for p in pages
        if '/property/' in p['url']
    ]

    print(f"Found {len(property_pages)} property pages")

    # Validate each
    results = []
    for page in property_pages:
        property_id = scraper.extract_property_id(page['url'])
        if property_id:
            result = await validator.validate_page(
                page['url'],
                page['html'],
                property_id
            )
            results.append(result)

    # Generate report
    report_files = reporter.generate_reports(results, "excel")
    print(f"Report: {report_files['excel']}")

asyncio.run(validate_property_pages())
```

---

### 10. Export Fix Recommendations

```python
# export_fixes.py
import asyncio
import json
from apps.validation import UIFieldValidationOrchestrator

async def export_fix_recommendations():
    orchestrator = UIFieldValidationOrchestrator()

    results = await orchestrator.run_validation(
        url="https://concordbroker.com",
        output_format="json"
    )

    # Extract all mismatches with fix suggestions
    fixes = []

    for result in results['results']:
        for validation in result['validations']:
            if validation['status'] == 'mismatch':
                fixes.append({
                    'page_url': result['page_url'],
                    'property_id': result['property_id'],
                    'label': validation['label'],
                    'selector': validation['selector'],
                    'current_value': validation['value'],
                    'correct_value': validation['expected_value'],
                    'db_field': validation['db_field'],
                    'fix_code': f"""
// Fix for: {validation['label']}
// Page: {result['page_url']}
// Selector: {validation['selector']}

// Current (incorrect):
{validation['value']}

// Should be:
{validation['expected_value']}

// Update to use correct field:
<span>{{propertyData.{validation['db_field']}}}</span>
                    """.strip()
                })

    # Export as JSON
    with open('fix_recommendations.json', 'w') as f:
        json.dump(fixes, f, indent=2)

    print(f"✅ Exported {len(fixes)} fix recommendations")
    print("📄 File: fix_recommendations.json")

asyncio.run(export_fix_recommendations())
```

---

## Common Use Cases

### Use Case 1: Pre-Deployment Validation

```bash
# Before deploying to production
python -m apps.validation.ui_field_validator \
  --url https://staging.concordbroker.com \
  --format excel

# Review report before proceeding with deployment
```

### Use Case 2: Debug Data Mismatch

```bash
# User reports incorrect data on specific property
python -m apps.validation.ui_field_validator \
  --property-ids 123456 \
  --format markdown

# Check markdown report for detailed mismatch info
```

### Use Case 3: Audit After Database Migration

```bash
# After migrating data or updating schema
python -m apps.validation.ui_field_validator \
  --url https://concordbroker.com \
  --format all \
  --output-dir ./post-migration-audit

# Verify all fields still display correctly
```

### Use Case 4: Monitor New Features

```bash
# After adding new UI fields
python -m apps.validation.ui_field_validator \
  --url https://concordbroker.com/new-feature \
  --format excel

# Ensure new fields are properly mapped
```

---

## Tips & Tricks

### Improve Mapping Accuracy

```python
# Add domain-specific mappings
config.LABEL_MAPPINGS.update({
    "por": "parcel_id",  # Your app's specific abbreviation
    "total value": "jv",
    "millage rate": "tax_rate"
})
```

### Handle Custom Date Formats

```python
# In validator.py, add custom date format
def _normalize_date(self, date_str: str) -> str:
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%B %d, %Y',  # Add: "January 15, 2024"
        '%d-%b-%y'    # Add: "15-Jan-24"
    ]
    # ... rest of method
```

### Filter Pages by Pattern

```python
# Only validate pages matching pattern
config.PROPERTY_URL_PATTERNS = [
    r'/property/details/(\d+)',  # Match specific URL structure
    r'/parcel/([A-Z0-9-]+)'
]
```

---

## Troubleshooting

### Problem: Too many pages crawled

**Solution:**
```python
# Limit crawl depth and pages
config.CRAWL_MAX_PAGES = 100
config.CRAWL_DEPTH = 2
```

### Problem: Low match rate

**Solution:**
```bash
# Check unmapped fields in report, then add mappings
# Review markdown report → "Unmapped Fields" section
# Add to config.LABEL_MAPPINGS
```

### Problem: Validation too slow

**Solution:**
```python
# Validate specific properties instead of full crawl
python -m apps.validation.ui_field_validator \
  --property-ids 123,456,789  # Sample properties
```

---

## Next Steps

1. **Start simple:** Validate a few properties first
2. **Review reports:** Check mismatches and unmapped fields
3. **Add mappings:** Update config.py based on findings
4. **Re-validate:** Confirm improvements
5. **Automate:** Add to CI/CD pipeline
6. **Monitor:** Schedule daily validations
