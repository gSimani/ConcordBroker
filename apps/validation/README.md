# UI Field Validation System

Automated system to validate that your website's UI displays the correct data from your database.

## 🎯 What It Does

1. **Crawls your entire website** using Firecrawl
2. **Extracts all label-field pairs** (e.g., "Property Owner: John Smith")
3. **Maps labels to database fields** using fuzzy matching and pattern recognition
4. **Validates displayed values** against actual database values
5. **Generates comprehensive reports** with fix recommendations

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
cd apps/validation
pip install -r requirements.txt

# Or install with Poetry (if using project-wide pyproject.toml)
poetry install
```

### Configuration

1. **Set environment variables:**

```bash
# .env file
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

2. **Update config.py:**

```python
# Set your production URL
TARGET_SITE_URL = "https://your-production-site.com"

# Add custom label mappings
LABEL_MAPPINGS = {
    "property owner": "owner_name",
    # ... add more mappings
}
```

### Usage

#### Validate Entire Website

```bash
python -m apps.validation.ui_field_validator \
  --url https://your-site.com \
  --format excel
```

#### Validate Specific Properties

```bash
python -m apps.validation.ui_field_validator \
  --property-ids 12345,67890,54321 \
  --format excel
```

#### Generate All Report Formats

```bash
python -m apps.validation.ui_field_validator \
  --url https://your-site.com \
  --format all \
  --output-dir ./reports
```

## 📊 Output Reports

### Excel Report (Recommended)

Multi-sheet workbook with:
- **All Validations**: Complete validation results
- **Mismatches**: Fields showing incorrect data
- **Unmapped Fields**: Labels without database mappings
- **Summary**: Overall statistics
- **Field Mappings**: Label → Database field analysis

### CSV Report

Single CSV file with all validation results (good for data analysis).

### JSON Report

Structured JSON with complete validation data (good for programmatic access).

### Markdown Report

Human-readable report with:
- Summary statistics
- Critical mismatches
- Unmapped fields
- Fix recommendations with code snippets

## 🔍 How It Works

### 1. HTML Extraction Patterns

The system recognizes multiple patterns:

#### Pattern 1: Label + Input
```html
<label>Property Owner</label>
<input value="John Smith" />
```

#### Pattern 2: Class-based
```html
<div class="field-label">Owner:</div>
<div class="field-value">John Smith</div>
```

#### Pattern 3: Inline Text
```html
<p>Property Owner: <strong>John Smith</strong></p>
```

#### Pattern 4: Data Attributes
```html
<div data-label="Property Owner" data-value="John Smith">
  John Smith
</div>
```

#### Pattern 5: Table Rows
```html
<tr>
  <td>Property Owner</td>
  <td>John Smith</td>
</tr>
```

### 2. Label-to-Field Mapping

Uses multiple strategies:

1. **Exact config mapping** (100% confidence)
2. **Exact schema match** (100% confidence)
3. **Fuzzy matching** (85%+ similarity)
4. **Pattern-based** (common abbreviations)

### 3. Value Comparison

Normalizes values before comparison:
- Case normalization (JOHN SMITH = john smith)
- Whitespace normalization
- Currency formatting ($450,000 = 450000)
- Date formatting (2024-01-15 = 01/15/2024)

## 📝 Example Output

### Console Output

```
🔍 UI Field Validation Started

📊 Extracting database schema...
✓ Schema extracted

🕷️  Crawling website: https://your-site.com
✓ Crawled 127 pages

🔍 Extracting and validating fields...
  [1/127] Validating https://your-site.com/property/12345
  [2/127] Validating https://your-site.com/property/67890
  ...

✓ Validated 127 pages

📝 Generating excel report...

✅ Validation Complete!

📄 Generated Reports:
  - EXCEL: ./validation_reports/validation_report_20250101_120000.xlsx

============================================================
📊 VALIDATION SUMMARY
============================================================
Pages Validated:     127
Total Fields:        1,524
Matched:             1,487 (97.57%)
Mismatched:          12
Unmapped:            25
============================================================

⚠️  WARNING: Found data mismatches!
   Review the report for details and fix recommendations.
```

### Markdown Report Extract

```markdown
## Critical Mismatches

### https://your-site.com/property/12345
**Property ID:** 12345

- **Sale Price**
  - UI shows: `$350,000`
  - Database has: `450000`
  - Field: `sale_prc1`
  - Issue: UI shows '$350,000' but database has '450000'

## Fix Recommendations

### Data Mismatches

Found 12 fields displaying incorrect data. Review the database queries
in your components to ensure correct field mapping.

```tsx
// Fix for: Sale Price
// Current value is incorrect
// Should display: 450000

// Ensure you're using the correct database field:
<div>
  <span className="label">Sale Price:</span>
  <span className="value">{propertyData.sale_prc1}</span>
</div>
```
```

## 🔧 Advanced Configuration

### Custom Extraction Patterns

Add to `config.py`:

```python
EXTRACTION_PATTERNS.append({
    "type": "custom_pattern",
    "label_selector": ".custom-label",
    "value_selector": ".custom-value",
    "proximity": "sibling"
})
```

### Custom Label Mappings

```python
LABEL_MAPPINGS.update({
    "owner information": "owner_name",
    "tax assessment": "tax_amount",
    "property classification": "property_use"
})
```

### Fuzzy Match Threshold

```python
# Stricter matching (90% similarity required)
FUZZY_MATCH_THRESHOLD = 90

# More lenient (70% similarity)
FUZZY_MATCH_THRESHOLD = 70
```

## 🤖 Automation

### GitHub Actions Workflow

Create `.github/workflows/validate-ui.yml`:

```yaml
name: Validate UI Fields

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

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

      - name: Run validation
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_KEY }}
          FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_KEY }}
        run: |
          python -m apps.validation.ui_field_validator \
            --url ${{ secrets.STAGING_URL }} \
            --format all

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: validation-reports
          path: ./validation_reports/
```

### Scheduled Validation

Run daily at midnight:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
```

## 📚 API Usage

Use programmatically in Python:

```python
from apps.validation import UIFieldValidationOrchestrator

async def validate():
    orchestrator = UIFieldValidationOrchestrator()

    results = await orchestrator.run_validation(
        url="https://your-site.com",
        output_format="excel"
    )

    print(f"Match rate: {results['summary']['match_percentage']}%")

    # Access specific mismatches
    for result in results['results']:
        for validation in result['validations']:
            if validation['status'] == 'mismatch':
                print(f"Mismatch: {validation['label']}")

import asyncio
asyncio.run(validate())
```

## 🐛 Troubleshooting

### Issue: Firecrawl not installed

```bash
pip install firecrawl-py
```

### Issue: Playwright browsers not installed

```bash
playwright install chromium
```

### Issue: Permission denied on Supabase

Make sure you're using the `SUPABASE_SERVICE_ROLE_KEY` (not anon key).

### Issue: No pages found

Check your `PROPERTY_URL_PATTERNS` in config.py to match your URL structure.

### Issue: Low match rate

1. Review unmapped fields in the report
2. Add custom mappings to `LABEL_MAPPINGS`
3. Adjust `FUZZY_MATCH_THRESHOLD`

## 🎯 Next Steps

1. **Run initial validation**: `python -m apps.validation.ui_field_validator --url https://your-site.com`
2. **Review the Excel report**: Check mismatches and unmapped fields
3. **Add custom mappings**: Update `config.py` with unmapped labels
4. **Fix mismatches**: Update your UI components
5. **Re-run validation**: Verify improvements
6. **Set up automation**: Add to CI/CD pipeline

## 📞 Support

For issues or questions:
- Check the generated Markdown report for fix recommendations
- Review extraction patterns in `config.py`
- Examine logs for specific error messages

## 🔗 Related Tools

- **Firecrawl**: https://firecrawl.dev
- **Playwright**: https://playwright.dev
- **Supabase**: https://supabase.com
- **Pandas**: https://pandas.pydata.org
