# Florida Tax Deed Sales Aggregator

## Overview

This tool aggregates upcoming Florida tax deed sale items from multiple counties, providing a unified dataset for investment analysis. The aggregator supports both open-access sources and authenticated vendor APIs.

## Counties Covered

| County | Vendor | Authentication | Coverage |
|--------|--------|----------------|----------|
| Broward | DeedAuction | Optional | Full with auth, Limited without |
| Collier | CollierClerk | None | Full |
| Orange | RealTaxDeed | Optional | Limited |
| Lee | RealTaxDeed | Optional | Limited |
| Putnam | RealTaxDeed | Optional | Limited |
| Pinellas | RealTaxDeed | Optional | Limited |
| Miami-Dade | MiamiDadeClerk | None | Info only |

## How to Run

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run aggregator with default output directory
python -m src.fl_taxdeeds

# Specify custom output directory
python -m src.fl_taxdeeds --out ./custom_output
```

### Output Files

- `out/fl_taxdeeds_upcoming.csv` - CSV format for spreadsheet analysis
- `out/fl_taxdeeds_upcoming.parquet` - Parquet format for big data processing

## Credential Setup

Some counties require authentication for full data access. Configure credentials using one of these methods:

### Windows CMD

```cmd
setx BROWARD_USER "gSimani"
setx BROWARD_PASS "<YOUR_PASSWORD>"
setx REALAUCTION_USER "<OPTIONAL_USER>"
setx REALAUCTION_PASS "<OPTIONAL_PASS>"
echo Close and reopen your terminal to load updated env vars.
```

### PowerShell

```powershell
$env:BROWARD_USER = "gSimani"
$env:BROWARD_PASS = "<YOUR_PASSWORD>"
$env:REALAUCTION_USER = "<OPTIONAL_USER>"
$env:REALAUCTION_PASS = "<OPTIONAL_PASS>"

# Persist for future sessions
[Environment]::SetEnvironmentVariable('BROWARD_USER','gSimani','User')
[Environment]::SetEnvironmentVariable('BROWARD_PASS','<YOUR_PASSWORD>','User')
```

### .env File

Create a `.env` file in the project root:

```env
BROWARD_USER=gSimani
BROWARD_PASS=<YOUR_PASSWORD>
REALAUCTION_USER=<OPTIONAL_USER>
REALAUCTION_PASS=<OPTIONAL_PASS>
```

## Data Schema

Each tax deed record contains:

| Field | Type | Description |
|-------|------|-------------|
| county | string | County name |
| sale_date | string | Auction date (YYYY-MM-DD) |
| sale_time | string | Auction time |
| tax_deed_no | string | Tax deed number |
| case_no | string | Case number (if available) |
| parcel_id | string | Property parcel ID |
| situs_addr | string | Property address |
| opening_bid | float | Minimum bid amount |
| status | string | Sale status (upcoming/sold/cancelled) |
| source_vendor | string | Data source vendor |
| source_url | string | Source URL |
| last_seen_utc | string | Last update timestamp |

## Known Gaps

### Authentication Required
- **Broward County**: Full export requires DeedAuction login
- **RealTaxDeed Counties**: Some features require account

### Limited Coverage
- **Miami-Dade**: Currently info page only, no structured data export
- **Smaller Counties**: Not all 67 Florida counties covered yet

### Data Quality
- HTML parsing may miss updates if vendor changes layout
- Some counties don't provide parcel IDs in listings
- Opening bid amounts may not reflect final minimum bids

## API Integration

The aggregated data can be accessed via the ConcordBroker API:

```python
# Fetch upcoming tax deeds
GET /api/taxdeeds/upcoming

# Filter by county
GET /api/taxdeeds/upcoming?county=Broward

# Filter by date range
GET /api/taxdeeds/upcoming?start_date=2025-01-01&end_date=2025-02-01
```

## Future Enhancements

1. Add more Florida counties
2. Implement real-time monitoring
3. Add historical sale results
4. Include property details from assessor data
5. Add investment ROI calculations
6. Email/SMS alerts for new listings

## Support

For issues or questions, please contact the development team or file an issue in the repository.