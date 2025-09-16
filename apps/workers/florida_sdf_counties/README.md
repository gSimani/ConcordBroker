# Florida Revenue SDF Counties Monitoring System

This system monitors, downloads, parses, and loads SDF (Sales Data File) for all 67 Florida counties from the Florida Revenue data portal.

## What is SDF?

SDF (Sales Data File) contains property sales transaction records for Florida properties. These files include:
- Sale prices and dates
- Buyer/seller information (grantor/grantee)
- Official record references (book/page)
- Sale qualification codes
- Property use codes
- Sale characteristics (foreclosure, REO, short sale, etc.)

## Components

### 1. SDF Counties Downloader (`sdf_counties_downloader.py`)
- Downloads SDF files for all 67 Florida counties
- URL pattern: `https://floridarevenue.com/.../SDF/[YEAR]P/SDF[CC]P[YEAR]01.txt`
- Supports all counties with two-digit codes (01-67)
- Priority counties feature for major markets
- Automatic checksum verification and update detection
- Rate limiting and retry logic

### 2. SDF Parser (`sdf_parser.py`)
- Parses fixed-width SDF text files
- Supports 31 fields including:
  - Parcel identification
  - Sale price and date
  - Grantor/grantee names
  - Official records references
  - Qualification codes
  - Sale flags (foreclosure, REO, short sale)
  - Property use codes
  - Site address information
- Calculates comprehensive sales statistics
- Validates data integrity

### 3. Database Loader (`sdf_database.py`)
- Loads parsed SDF data to Supabase PostgreSQL
- Table: `florida_sdf_sales`
- Batch processing for performance (500 records per batch)
- Uses REST API for compatibility
- Comprehensive field mapping
- Duplicate detection and handling

### 4. Monitor (`monitor.py`)
- Orchestrates download, parse, and load workflow
- Daily checks for updates (default: 3:00 AM)
- Weekly full processing of priority counties
- Tracks sales volume and statistics
- Configurable scheduling

## SDF File Format

SDF files are fixed-width text files containing property sales information:

```
Field                   Position    Length    Type
----------------------------------------------------
CO_NO                  1-2         2         County number
PARCEL_ID              3-32        30        Parcel ID
SALE_YR                33-36       4         Sale year
SALE_MO                37-38       2         Sale month
SALE_DAY               39-40       2         Sale day
SALE_PRC               41-52       12        Sale price
OR_BOOK                53-57       5         Official records book
OR_PAGE                58-62       5         Official records page
CLERK_NO               63-74       12        Clerk instrument number
QUAL_CD                75-76       2         Qualification code
VI_CD                  77          1         Vacant/improved code
GRANTOR                78-147      70        Grantor name
GRANTEE                148-217     70        Grantee name
... (31 fields total)
```

## Qualification Codes

- **Q** - Qualified (Arms length transaction)
- **U** - Unqualified (Not arms length)
- **F** - Foreclosure
- **G** - Gift
- **E** - Exchange
- **W** - Warranty deed
- **S** - Special warranty deed
- **D** - Deed
- **T** - Trustee deed

## Installation

### Required Libraries
```bash
pip install requests
pip install schedule
pip install python-dotenv
```

## Database Setup

Create the SDF table in Supabase:

```sql
CREATE TABLE IF NOT EXISTS florida_sdf_sales (
    id BIGSERIAL PRIMARY KEY,
    
    -- Key fields
    parcel_id VARCHAR(30) NOT NULL,
    county_number VARCHAR(2) NOT NULL,
    county_name VARCHAR(50),
    
    -- Sale information
    sale_date DATE,
    sale_year INTEGER,
    sale_month INTEGER,
    sale_day INTEGER,
    sale_price DECIMAL(15, 2),
    
    -- Official records
    or_book VARCHAR(10),
    or_page VARCHAR(10),
    clerk_no VARCHAR(20),
    
    -- Sale details
    qual_code VARCHAR(2),
    qual_desc VARCHAR(50),
    vi_code CHAR(1),
    grantor VARCHAR(100),
    grantee VARCHAR(100),
    
    -- Sale characteristics
    multi_parcel_sale BOOLEAN DEFAULT FALSE,
    sale_type VARCHAR(10),
    deed_type VARCHAR(10),
    
    -- Sale flags
    foreclosure_flag BOOLEAN DEFAULT FALSE,
    reo_flag BOOLEAN DEFAULT FALSE,
    short_sale_flag BOOLEAN DEFAULT FALSE,
    arms_length_flag BOOLEAN DEFAULT FALSE,
    distressed_flag BOOLEAN DEFAULT FALSE,
    
    -- Property details
    transfer_acreage DECIMAL(10, 4),
    property_use VARCHAR(10),
    
    -- Address
    site_address VARCHAR(200),
    site_city VARCHAR(100),
    site_zip VARCHAR(20),
    
    -- Metadata
    data_source VARCHAR(20) DEFAULT 'SDF',
    file_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_sdf_sale UNIQUE (parcel_id, county_number, sale_date, sale_price)
);

CREATE INDEX idx_sdf_parcel_id ON florida_sdf_sales(parcel_id);
CREATE INDEX idx_sdf_county ON florida_sdf_sales(county_number);
CREATE INDEX idx_sdf_sale_date ON florida_sdf_sales(sale_date);
CREATE INDEX idx_sdf_sale_year ON florida_sdf_sales(sale_year);
CREATE INDEX idx_sdf_sale_price ON florida_sdf_sales(sale_price);
CREATE INDEX idx_sdf_qual_code ON florida_sdf_sales(qual_code);
CREATE INDEX idx_sdf_foreclosure ON florida_sdf_sales(foreclosure_flag) WHERE foreclosure_flag = TRUE;
```

## Usage

### Download SDF Files

```bash
# Download Broward County (default)
python sdf_counties_downloader.py

# Download specific counties
python sdf_counties_downloader.py --counties 06 13 29

# Download priority counties only
python sdf_counties_downloader.py --priority

# Download all counties
python sdf_counties_downloader.py --all

# Check download status
python sdf_counties_downloader.py --status

# Check for updates
python sdf_counties_downloader.py --check-updates
```

### Parse SDF Files

```bash
# Parse a single SDF file
python sdf_parser.py SDF06P202501.txt

# Parse with validation
python sdf_parser.py SDF06P202501.txt --validate

# Show statistics
python sdf_parser.py SDF06P202501.txt --stats

# Save parsed output
python sdf_parser.py SDF06P202501.txt --output parsed_sales.json
```

### Load to Database

```python
from sdf_parser import SDFParser
from sdf_database import SDFDatabaseLoader

# Parse file
parser = SDFParser()
parsed = parser.parse_file("SDF06P202501.txt")

# Load to database
loader = SDFDatabaseLoader()
result = loader.load_file(
    file_path="SDF06P202501.txt",
    parsed_data=parsed,
    county_number='06',
    county_name='Broward'
)
```

### Monitor System

```bash
# Start continuous monitoring
python monitor.py --mode monitor --daily-time 03:00

# Run one-time check for updates
python monitor.py --mode once

# Process priority counties
python monitor.py --mode priority

# Process specific counties
python monitor.py --counties 06 13 --year 2025

# Show current status
python monitor.py --mode status
```

## Directory Structure

```
data/florida_sdf_counties/
├── raw/                    # Downloaded SDF text files
│   ├── SDF01P202501.txt   # Alachua County
│   ├── SDF06P202501.txt   # Broward County
│   └── ...
├── extracted/              # Parsed data (optional)
│   └── parsed_sales.json
└── metadata/              # Download history and tracking
    └── download_history.json
```

## Monitoring Schedule

- **Daily (3:00 AM)**: Check for updates, process up to 10 counties with new data
- **Weekly (Sunday 2:00 AM)**: Full processing of priority counties
- **Monthly**: Check for new year data availability

## Statistics Tracked

- Total sales volume by county
- Average and median sale prices
- Arms length vs non-arms length sales
- Foreclosure and distressed sales counts
- Sale price distribution by ranges
- Monthly and yearly sales trends
- Property use code breakdown

## Performance

- **Download Speed**: ~1-5 MB/s depending on file size
- **Parse Speed**: ~20,000 records/second
- **Database Load**: ~5,000 records/second with batch processing
- **Memory Usage**: Streaming processing keeps memory under 500MB
- **Typical County Processing Time**: 2-10 minutes depending on size

## Data Statistics

- **Total Counties**: 67
- **Priority Counties**: 6 (Broward, Miami-Dade, Hillsborough, Orange, Palm Beach, Pinellas)
- **Typical SDF File Size**: 10-500 MB
- **Records per County**: 10,000 - 500,000 sales
- **Total Fields**: 31
- **Update Frequency**: Monthly

## Common Property Use Codes

- **0100** - Single Family Residential
- **0200** - Mobile Homes
- **0300** - Multi-Family (10+ units)
- **0400** - Condominiums
- **0500** - Cooperatives
- **0600** - Retirement Homes
- **0700** - Miscellaneous Residential
- **0800** - Multi-Family (less than 10 units)
- **1000** - Vacant Land
- **2000-8999** - Commercial and Industrial

## Sale Types

1. **Arms Length Sales**
   - Normal market transactions
   - Qualified sales (Q code)
   - Best for market analysis

2. **Distressed Sales**
   - Foreclosures
   - REO (bank-owned)
   - Short sales

3. **Non-Arms Length**
   - Family transfers
   - Gifts
   - Corporate transfers

## Error Handling

- Network errors: Automatic retry with exponential backoff
- Parse errors: Logged and skipped, processing continues
- Database errors: Batch retry logic, failed batches logged
- File not found: Logged as warning, county skipped
- Rate limiting: Built-in delays between requests

## Integration Points

This system integrates with:
- Florida Revenue NAL (Name Address Library) system
- Florida Revenue NAP (Non-Ad Valorem Parcel) system
- Florida Revenue NAV (Non-Ad Valorem) system
- Supabase property database
- Property profile display system
- Market analysis tools

## Logging

Logs are written to:
- Console output (INFO level and above)
- `florida_sdf_monitor.log` file (all levels)
- Status tracking in `florida_sdf_monitor_status.json`

## Maintenance

1. **Check logs regularly**: Review `florida_sdf_monitor.log` for errors
2. **Monitor coverage**: Use `--status` flag to check county coverage
3. **Update year**: System automatically handles year transitions
4. **Database cleanup**: Periodically remove duplicate sales if needed
5. **URL changes**: Update BASE_URL if Florida Revenue changes structure

## Troubleshooting

### Common Issues

1. **File not found (404)**
   - Check if county has released current year data
   - Verify URL pattern is correct

2. **Parse errors**
   - File format may have changed
   - Check for extra headers or footers

3. **Database connection errors**
   - Verify Supabase credentials in .env
   - Check network connectivity

4. **Duplicate sales**
   - Normal for multi-parcel sales
   - Same property may sell multiple times

5. **Large file processing**
   - Monitor memory usage
   - Consider increasing batch size for speed

## Future Enhancements

- [ ] Support for historical SDF data (prior years)
- [ ] Market trend analysis
- [ ] Price prediction models
- [ ] Integration with MLS data
- [ ] Automated market reports
- [ ] REST API for sales data access
- [ ] Real-time update notifications
- [ ] Cloud deployment support