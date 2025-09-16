# Florida Revenue NAL Counties Monitoring System

This system monitors, downloads, parses, and loads NAL (Name Address Library) data files for all 67 Florida counties from the Florida Revenue data portal.

## Components

### 1. NAL Counties Downloader (`nal_counties_downloader.py`)
- Downloads NAL files for all Florida counties
- URL pattern: `https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/[YEAR]P/NAL[COUNTY_CODE]P[YEAR].txt`
- Supports all 67 Florida counties with two-digit codes
- Priority counties feature for major population centers (Broward, Miami-Dade, Hillsborough, Orange, Palm Beach, Pinellas)
- Automatic checksum verification and update detection
- Rate limiting and retry logic

### 2. NAL Parser (`nal_parser.py`)
- Parses fixed-width NAL text files
- Supports 50+ fields including:
  - Owner names and addresses
  - Mailing addresses
  - Property locations
  - Assessment values
  - Exemptions
  - Tax districts
- Handles large files with streaming
- Data validation and error reporting

### 3. Database Loader (`nal_database.py`)
- Loads parsed NAL data to Supabase PostgreSQL database
- Table: `florida_nal_owners`
- Batch processing for performance (500 records per batch)
- Upsert logic to handle updates
- Comprehensive field mapping
- Row Level Security enabled

### 4. Monitor (`monitor.py`)
- Orchestrates download, parse, and load workflow
- Daily checks for updates (default: 3:00 AM)
- Weekly full processing of priority counties
- Tracks processing statistics and errors
- Configurable scheduling

## NAL File Format

NAL files are fixed-width text files containing property owner information:

```
Field                   Position    Length    Type
----------------------------------------------------
PARCEL_ID              1-30        30        String
OWNER_NAME1            31-100      70        String
OWNER_NAME2            101-170     70        String
MAIL_ADDR1             171-240     70        String
MAIL_CITY              241-290     50        String
MAIL_STATE             291-292     2         String
MAIL_ZIPCODE           293-302     10        String
... (50+ more fields)
```

## Florida County Codes

| Code | County | Priority |
|------|--------|----------|
| 01 | Alachua | No |
| 02 | Baker | No |
| 03 | Bay | No |
| 04 | Bradford | No |
| 05 | Brevard | No |
| 06 | Broward | **Yes** |
| 07 | Calhoun | No |
| 08 | Charlotte | No |
| 09 | Citrus | No |
| 10 | Clay | No |
| 11 | Collier | No |
| 12 | Columbia | No |
| 13 | Miami-Dade | **Yes** |
| ... | ... | ... |
| 29 | Hillsborough | **Yes** |
| 48 | Orange | **Yes** |
| 50 | Palm Beach | **Yes** |
| 52 | Pinellas | **Yes** |
| ... | ... | ... |
| 67 | Washington | No |

## Installation

### Required Libraries
```bash
pip install requests
pip install schedule
pip install python-dotenv
pip install supabase
```

## Database Setup

Create the NAL table in Supabase:

```sql
CREATE TABLE IF NOT EXISTS florida_nal_owners (
    id BIGSERIAL PRIMARY KEY,
    
    -- Key fields
    parcel_id VARCHAR(30) NOT NULL,
    county_code VARCHAR(2) NOT NULL,
    county_name VARCHAR(50),
    tax_year INTEGER,
    
    -- Owner information
    owner_name1 VARCHAR(100),
    owner_name2 VARCHAR(100),
    owner_name3 VARCHAR(100),
    owner_name4 VARCHAR(100),
    
    -- Mailing address
    mail_addr1 VARCHAR(100),
    mail_addr2 VARCHAR(100),
    mail_addr3 VARCHAR(100),
    mail_city VARCHAR(50),
    mail_state VARCHAR(2),
    mail_zip VARCHAR(10),
    mail_country VARCHAR(50),
    
    -- Property details
    site_addr_street VARCHAR(100),
    site_city VARCHAR(50),
    site_zip VARCHAR(10),
    
    -- Assessment values
    assessed_value DECIMAL(15, 2),
    taxable_value DECIMAL(15, 2),
    just_value DECIMAL(15, 2),
    
    -- Exemptions
    homestead_exemption DECIMAL(15, 2),
    exemption_codes TEXT,
    
    -- Metadata
    data_source VARCHAR(20) DEFAULT 'NAL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_nal_parcel_county_year UNIQUE (parcel_id, county_code, tax_year)
);

CREATE INDEX idx_nal_parcel_id ON florida_nal_owners(parcel_id);
CREATE INDEX idx_nal_county_code ON florida_nal_owners(county_code);
CREATE INDEX idx_nal_owner_name ON florida_nal_owners(owner_name1);
```

## Usage

### Download NAL Files

```bash
# Download Broward County (default)
python nal_counties_downloader.py

# Download specific counties
python nal_counties_downloader.py --counties 06 13 29

# Download priority counties only
python nal_counties_downloader.py --priority

# Download all counties
python nal_counties_downloader.py --all

# Check download status
python nal_counties_downloader.py --status

# Check for updates
python nal_counties_downloader.py --check-updates
```

### Parse NAL Files

```bash
# Parse a single NAL file
python nal_parser.py NAL06P2025.txt

# Parse with validation
python nal_parser.py NAL06P2025.txt --validate

# Show statistics
python nal_parser.py NAL06P2025.txt --stats
```

### Load to Database

```python
from nal_parser import NALParser
from nal_database import NALDatabaseLoader

# Parse file
parser = NALParser()
parsed = parser.parse_file("NAL06P2025.txt")

# Load to database
loader = NALDatabaseLoader()
result = loader.load_file(
    file_path="NAL06P2025.txt",
    parsed_data=parsed,
    county_code='06',
    county_name='Broward',
    year=2025
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
data/florida_nal_counties/
├── raw/                    # Downloaded NAL text files
│   ├── NAL01P2025.txt     # Alachua County
│   ├── NAL06P2025.txt     # Broward County
│   └── ...
├── extracted/              # Parsed data (optional)
│   └── parsed_records.json
└── metadata/              # Download history and tracking
    ├── download_history.json
    └── processing_log.json
```

## Monitoring Schedule

- **Daily (3:00 AM)**: Check for updates, process up to 10 counties with new data
- **Weekly (Sunday 2:00 AM)**: Full processing of priority counties
- **Monthly**: Check for new year data availability

## Performance

- **Download Speed**: ~1-5 MB/s depending on file size
- **Parse Speed**: ~10,000 records/second
- **Database Load**: ~5,000 records/second with batch processing
- **Memory Usage**: Streaming processing keeps memory under 500MB
- **Typical County Processing Time**: 2-10 minutes depending on size

## Data Statistics

- **Total Counties**: 67
- **Priority Counties**: 6 (major population centers)
- **Typical NAL File Size**: 10-500 MB
- **Records per County**: 100,000 - 2,000,000
- **Total Fields**: 50+
- **Update Frequency**: Varies by county (monthly to annually)

## Error Handling

- Network errors: Automatic retry with exponential backoff
- Parse errors: Logged and skipped, processing continues
- Database errors: Batch retry logic, failed batches logged
- File not found: Logged as warning, county skipped
- Rate limiting: Built-in delays between requests

## Integration Points

This system integrates with:
- Broward County property data pipeline
- Florida Revenue SDF (Sales Data File) system
- Supabase property database
- Property profile display system

## Logging

Logs are written to:
- Console output (INFO level and above)
- `florida_nal_monitor.log` file (all levels)
- Status tracking in `florida_nal_monitor_status.json`

## Maintenance

1. **Check logs regularly**: Review `florida_nal_monitor.log` for errors
2. **Monitor coverage**: Use `--status` flag to check county coverage
3. **Update year**: System automatically detects new year data
4. **Database cleanup**: Periodically remove old year data if needed
5. **URL changes**: Update BASE_URL if Florida Revenue changes structure

## Troubleshooting

### Common Issues

1. **File not found (404)**
   - County may not have published NAL file yet
   - Check URL pattern is correct for year

2. **Parse errors**
   - File format may have changed
   - Check for extra headers or footers in file

3. **Database connection errors**
   - Verify Supabase credentials in .env
   - Check network connectivity

4. **Memory issues with large files**
   - Parser uses streaming, but very large counties may need increased limits
   - Consider processing in smaller chunks

5. **Rate limiting**
   - Adjust sleep timers in code if getting 429 errors
   - Default delays should be sufficient

## Future Enhancements

- [ ] Support for historical NAL data (prior years)
- [ ] Differential updates (only changed records)
- [ ] Data quality scoring
- [ ] Automated anomaly detection
- [ ] REST API for data access
- [ ] Real-time update notifications
- [ ] Cloud deployment support
- [ ] Parallel county processing