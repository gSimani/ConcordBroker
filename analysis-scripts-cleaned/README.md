# Analysis Scripts - Cleaned and Organized

Date: 2025-11-07

## Purpose
This directory contains 10 core analysis scripts for ConcordBroker database analysis.

## Scripts

| Script | Purpose |
|--------|---------|
| 01_database_structure.py | Complete database overview and table analysis |
| 02_property_use_codes.py | Property type classification (residential, commercial, etc.) |
| 03_large_buildings.py | Large commercial properties (7500+ sqft) |
| 04_sales_analysis.py | Sales data and transaction history |
| 05_county_inventory.py | County file inventory and coverage |
| 06_missing_data_check.py | Data gap analysis and completeness checks |
| 07_county_deep_dive_template.py | Template for county-specific deep dive analysis |
| 08_contact_extraction.py | Extract contact information from entities |
| 09_proforma_analysis.py | Financial analysis and proformas |
| 10_exemption_fields.py | Tax exemption analysis |

## [!] CRITICAL: Security Configuration Required

ALL scripts need `.env` file with credentials. **NEVER commit .env to git!**

### Setup (ONE TIME):

```bash
# 1. Create .env file in project root
# See parent directory for .env.example

# 2. Verify .env is in .gitignore
echo ".env" >> ../.gitignore

# 3. Scripts will automatically load from root .env
```

## Usage

```bash
# Run individual script
python 01_database_structure.py

# Run all scripts sequentially
python run_all_analysis.py

# Run specific analysis
python 03_large_buildings.py > output/large_buildings_2025-11-07.json
```

## Output

All scripts output JSON reports to current directory. Archive outputs regularly.

## Archived Scripts

See `../analysis-scripts-archived/` for older versions and duplicates.

## Maintenance

- Update scripts when database schema changes
- Archive old outputs monthly
- Review data quality issues from 06_missing_data_check.py weekly
