# Broward County Building & Trade Permit Monitoring System

This system monitors, scrapes, and processes building and trade permits from multiple Broward County permit sources for property analysis and compliance tracking.

## What are Broward County Permits?

Broward County building and trade permits include:
- **Building permits** - New construction, additions, renovations
- **Trade permits** - Electrical, plumbing, HVAC, roofing
- **Environmental permits** - Water management, environmental compliance
- **Right-of-way permits** - Street work, utility installations
- **Demolition permits** - Structure demolition and site clearing
- **Certificate of Occupancy** - Building completion and occupancy

## Permit Sources Monitored

### 1. BCS (Building Code Services)
- **Coverage**: Unincorporated Broward County
- **URL**: `https://www.broward.org/Development/Building/Pages/permitinquiry.aspx`
- **Data**: Building permits, trade permits, inspections
- **Technology**: ASP.NET forms with ViewState
- **Update Frequency**: Real-time

### 2. Hollywood Accela System  
- **Coverage**: City of Hollywood ONLY (not countywide)
- **URL**: `https://aca.hollywoodfl.org/citizenaccess/`
- **Data**: Building permits, code enforcement, land development
- **Technology**: Accela Citizen Access portal
- **Update Frequency**: Real-time
- **Note**: This covers only Hollywood city limits, not other municipalities

### 3. ENVIROS Environmental Portal
- **Coverage**: Broward environmental permits
- **URL**: `https://www.broward.org/Environment/WaterResources/Pages/EnvironmentalPermitSearch.aspx`
- **Data**: Environmental permits, water management permits
- **Technology**: ASP.NET forms with ViewState
- **Update Frequency**: Daily

## Components

### 1. Permit Scraper (`permit_scraper.py`)
- Scrapes permits from BCS, Hollywood Accela, and ENVIROS
- Handles complex ASP.NET form submissions with ViewState
- Extracts permit details, property information, and status
- Rate limiting and error handling
- Saves scraped data as JSON files

### 2. Database Loader (`permit_db_loader.py`)
- Loads scraped permit data into Supabase database
- Standardizes permit data across different sources
- Handles permit updates and deduplication
- Creates comprehensive permit tables with indexes
- Tracks processing statistics and errors

### 3. Monitor (`permit_monitor.py`)
- Orchestrates scraping, loading, and processing
- Daily checks for new permits (default: 6:00 AM)
- Weekly full scans (default: Sunday 5:00 AM)
- Status tracking and error logging
- Supports one-time runs and continuous monitoring

## Installation

### Required Libraries
```bash
# Core requirements
pip install requests
pip install beautifulsoup4
pip install schedule
pip install python-dotenv
pip install pandas

# Database
pip install supabase
```

### Environment Setup
Ensure your `.env` file contains:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Usage

### Initialize System
```bash
# Create database tables and perform initial scrape
python permit_monitor.py --mode init
```

### Daily Permit Monitoring
```bash
# Run daily check (last 2 days)
python permit_monitor.py --mode daily

# Custom days back
python permit_monitor.py --mode custom --days-back 7
```

### Continuous Monitoring
```bash
# Start continuous monitoring service
python permit_monitor.py --mode monitor --daily-time 06:00 --weekly-day sunday
```

### Manual Scraping
```bash
# Scrape BCS permits
python permit_scraper.py --source bcs --days-back 7

# Scrape Hollywood permits  
python permit_scraper.py --source hollywood --days-back 7

# Scrape environmental permits
python permit_scraper.py --source enviros --days-back 7
```

### Database Loading
```bash
# Load all permit files
python permit_db_loader.py --load-files

# Load specific file
python permit_db_loader.py --load-file permit_bcs_20250107_120000.json

# Show statistics
python permit_db_loader.py --stats
```

### Status Monitoring
```bash
# Show current status
python permit_monitor.py --mode status
```

## Directory Structure

```
data/broward_permits/
├── raw/                    # Scraped permit JSON files
│   ├── permit_bcs_20250107_120000.json
│   ├── permit_hollywood_20250107_120000.json
│   └── permit_enviros_20250107_120000.json
├── processed/              # Processed files (after loading)
│   └── ...
└── logs/                   # Log files
    ├── broward_permit_monitor.log
    └── permit_scraper.log
```

## Database Schema

### `broward_permits` Table
- **permit_number** (VARCHAR) - Unique permit identifier
- **permit_type** (VARCHAR) - Building, Electrical, Plumbing, etc.
- **description** (TEXT) - Permit description
- **status** (VARCHAR) - Issued, Pending, Expired, etc.
- **applicant_name** (VARCHAR) - Permit applicant
- **contractor_name** (VARCHAR) - Licensed contractor
- **property_address** (VARCHAR) - Property location
- **parcel_id** (VARCHAR) - Property parcel identifier
- **folio_number** (VARCHAR) - Tax folio number
- **issue_date** (DATE) - Permit issue date
- **expiration_date** (DATE) - Permit expiration
- **final_date** (DATE) - Final inspection date
- **valuation** (DECIMAL) - Construction valuation
- **permit_fee** (DECIMAL) - Permit fee amount
- **source_system** (VARCHAR) - BCS, hollywood_accela, enviros
- **jurisdiction** (VARCHAR) - Permit jurisdiction
- **raw_data** (JSONB) - Original scraped data
- **scraped_at** (TIMESTAMP) - When data was scraped

### Indexes
- permit_number (unique)
- source_system
- jurisdiction  
- issue_date
- parcel_id
- permit_type
- status

## Scraped Data Fields

### BCS Permits
- Permit number and type
- Property address and parcel ID
- Applicant and contractor information
- Issue, expiration, and inspection dates
- Construction valuation and fees
- Permit status and description

### Hollywood Permits
- Application number and type
- Property details and address
- Applicant and contractor names
- Permit dates and status
- Project valuation
- Inspection schedules

### Environmental Permits
- Permit number and type
- Environmental compliance details
- Property location
- Permit dates and status
- Regulatory requirements

## Monitoring Schedule

- **Daily (6:00 AM)**: Check for new permits from last 2 days
- **Weekly (Sunday 5:00 AM)**: Full scan of last 30 days
- **On-demand**: Custom date ranges and specific sources

## Performance

- **Scraping Speed**: ~50-200 permits/minute depending on source
- **Processing Speed**: ~1,000 permits/minute for database loading
- **Memory Usage**: Efficient streaming processing
- **Typical Daily Volume**: 100-500 new permits

## Data Quality & Validation

### Permit Number Validation
- Ensures unique permit numbers per source
- Validates permit number formats
- Checks for duplicate applications

### Date Validation
- Parses multiple date formats
- Validates date ranges and logic
- Handles missing or invalid dates

### Address Standardization
- Standardizes property addresses
- Links to parcel IDs when available
- Geocoding for location verification

## Integration with Property System

This permit data enhances property profiles by providing:

1. **Construction History**
   - Building permits and renovations
   - Property improvements and additions
   - Compliance and inspection records

2. **Contractor Activity**
   - Licensed contractor relationships
   - Work quality and compliance history
   - Permit frequency and types

3. **Property Value Insights**
   - Construction valuations
   - Improvement investments
   - Market activity indicators

4. **Compliance Monitoring**
   - Permit status tracking
   - Expiration monitoring
   - Violation and compliance history

## Error Handling

- **Network timeouts**: Retry logic with exponential backoff
- **Form submission errors**: ViewState and validation handling
- **Parse errors**: Graceful error handling with logging
- **Database errors**: Transaction rollback and retry
- **Rate limiting**: Respectful request spacing

## Common Issues & Troubleshooting

### Scraping Issues
1. **ViewState Errors**: ASP.NET forms require proper ViewState handling
2. **Session Timeouts**: Forms may timeout during long scraping sessions
3. **CAPTCHA**: Some systems may implement CAPTCHA protection
4. **Rate Limiting**: Servers may block rapid requests

### Solutions
```bash
# Check scraper logs
tail -f permit_scraper.log

# Test specific source
python permit_scraper.py --source bcs --days-back 1 --debug

# Verify database connection
python permit_db_loader.py --stats
```

### Database Issues
1. **Connection timeouts**: Check Supabase connectivity
2. **Duplicate records**: Permit number uniqueness constraints
3. **Data type errors**: Field validation and parsing

## API Integration

The permit data is available through the property API:

```javascript
// Get permits for a property
fetch(`/api/properties/${parcelId}/permits`)

// Get recent permits by type
fetch(`/api/permits?type=building&days=30`)

// Get permits by contractor
fetch(`/api/permits?contractor=ABC+Construction`)
```

## Coverage Limitations & Future Enhancements

### Current Coverage:
- **BCS**: Unincorporated Broward County
- **Hollywood**: City of Hollywood only
- **ENVIROS**: County-wide environmental permits

### Missing Municipalities:
- Fort Lauderdale
- Pompano Beach  
- Coral Springs
- Plantation
- Sunrise
- Davie
- Miramar
- Pembroke Pines
- Weston
- Cooper City
- Deerfield Beach
- Lighthouse Point
- Other incorporated cities

### Future Enhancements:
- [ ] Additional municipalities (Fort Lauderdale, Pompano Beach, etc.)
- [ ] Permit document downloads (plans, certificates)
- [ ] Real-time permit status updates
- [ ] Permit expiration alerts
- [ ] Contractor performance analytics
- [ ] GIS mapping integration
- [ ] Mobile permit lookup
- [ ] Permit fee tracking and analysis

## Example Use Cases

### Property Due Diligence
```python
from permit_db_loader import BrowardPermitDBLoader

loader = BrowardPermitDBLoader()

# Get all permits for a property
permits = loader.fetch_data(
    "broward_permits",
    filters={"parcel_id": "504231242730"}
)

print(f"Found {len(permits)} permits for property")
for permit in permits:
    print(f"  {permit['permit_type']}: {permit['status']} - ${permit['valuation']:,}")
```

### Contractor Analysis
```python
# Find active contractors
contractors = loader.fetch_data(
    "broward_permits",
    select="contractor_name, COUNT(*) as permit_count, AVG(valuation) as avg_valuation",
    filters={"issue_date__gte": "2024-01-01"},
    group_by="contractor_name",
    order_by="permit_count DESC",
    limit=20
)
```

This Broward permit monitoring system provides comprehensive building and trade permit data for property analysis, compliance tracking, and market insights in the ConcordBroker platform.