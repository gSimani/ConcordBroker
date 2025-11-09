# Tax Deed Auction Scraper System

## Overview
A sophisticated web scraping agent designed to monitor and extract comprehensive property data from Broward County tax deed auctions at https://broward.deedauction.net

## Components

### 1. **tax_deed_auction_scraper.py**
Main scraper module that:
- Scrapes upcoming auction list
- Expands each property to get detailed information
- Extracts all property details including:
  - Tax Deed Number
  - Parcel Number with BCPA link
  - Tax Certificate Number
  - Legal Description
  - Situs Address
  - Homestead Status
  - Assessed/SOH Value
  - Applicant Information (parsed for Sunbiz matching)
  - GIS Map Links
  - Opening Bid
  - Best Bid
  - Close Time
  - Property Status (Upcoming/Canceled/Removed)

### 2. **tax_deed_database.py**
Database integration layer that:
- Manages Supabase connections
- Stores auction and property data
- Tracks historical changes
- Provides search capabilities:
  - By address
  - By parcel number
  - By applicant/company
  - High-value properties
  - Homestead properties

### 3. **tax_deed_monitor.py**
Monitoring and alerting system that:
- Runs scheduled scraping (default: every 6 hours)
- Detects changes in auction data
- Sends alerts for:
  - New auctions
  - High-value properties (>$100k)
  - Homestead properties
  - Mass cancellations
  - Status changes
  - Bid updates
- Generates comprehensive reports

## Installation

```bash
# Install required packages
pip install aiohttp beautifulsoup4 supabase asyncio

# Set environment variables
export SUPABASE_URL="your_supabase_url"
export SUPABASE_ANON_KEY="your_supabase_key"
export ALERT_EMAIL="your_email@example.com"  # Optional
export ALERT_WEBHOOK_URL="your_webhook_url"  # Optional
```

## Database Schema

Create these tables in Supabase:

```sql
-- Auctions table
CREATE TABLE tax_deed_auctions (
    auction_id TEXT PRIMARY KEY,
    description TEXT,
    auction_date TIMESTAMP,
    total_items INTEGER,
    available_items INTEGER,
    advertised_items INTEGER,
    canceled_items INTEGER,
    status TEXT,
    auction_url TEXT,
    last_updated TIMESTAMP,
    metadata JSONB
);

-- Properties table
CREATE TABLE tax_deed_properties (
    composite_key TEXT PRIMARY KEY,  -- auction_id_item_id
    auction_id TEXT REFERENCES tax_deed_auctions(auction_id),
    item_id TEXT,
    tax_deed_number TEXT,
    parcel_number TEXT,
    parcel_url TEXT,
    tax_certificate_number TEXT,
    legal_description TEXT,
    situs_address TEXT,
    homestead BOOLEAN,
    assessed_value NUMERIC,
    soh_value NUMERIC,
    applicant TEXT,
    applicant_companies TEXT[],
    gis_map_url TEXT,
    opening_bid NUMERIC,
    best_bid NUMERIC,
    close_time TIMESTAMP,
    status TEXT,
    extracted_at TIMESTAMP,
    metadata JSONB
);

-- Property history table
CREATE TABLE tax_deed_property_history (
    id SERIAL PRIMARY KEY,
    composite_key TEXT,
    auction_id TEXT,
    item_id TEXT,
    snapshot_time TIMESTAMP,
    -- All other fields from tax_deed_properties
    tax_deed_number TEXT,
    parcel_number TEXT,
    status TEXT,
    opening_bid NUMERIC,
    best_bid NUMERIC,
    metadata JSONB
);

-- Indexes for performance
CREATE INDEX idx_properties_auction ON tax_deed_properties(auction_id);
CREATE INDEX idx_properties_parcel ON tax_deed_properties(parcel_number);
CREATE INDEX idx_properties_address ON tax_deed_properties(situs_address);
CREATE INDEX idx_properties_status ON tax_deed_properties(status);
CREATE INDEX idx_properties_homestead ON tax_deed_properties(homestead);
CREATE INDEX idx_properties_opening_bid ON tax_deed_properties(opening_bid);
```

## Usage

### Test the Scraper
```python
python test_tax_deed_scraper.py
```

### Run One-Time Scrape
```python
import asyncio
from apps.workers.tax_deed_auction_scraper import TaxDeedAuctionScraper

async def scrape():
    async with TaxDeedAuctionScraper() as scraper:
        auctions = await scraper.scrape_all_auctions()
        scraper.save_to_json(auctions, 'auctions.json')
        return auctions

auctions = asyncio.run(scrape())
```

### Start Monitoring Service
```python
import asyncio
from apps.workers.tax_deed_monitor import TaxDeedMonitor

async def monitor():
    monitor = TaxDeedMonitor()
    await monitor.monitor_loop()  # Runs continuously

asyncio.run(monitor())
```

### Query Database
```python
import asyncio
from apps.workers.tax_deed_database import TaxDeedDatabase

async def query():
    db = TaxDeedDatabase()
    
    # Get upcoming auctions
    auctions = await db.get_upcoming_auctions()
    
    # Search by address
    properties = await db.search_properties_by_address("123 Main St")
    
    # Get high-value properties
    high_value = await db.get_high_value_properties(min_value=150000)
    
    # Get homestead properties
    homestead = await db.get_homestead_properties()
    
    return properties

results = asyncio.run(query())
```

## Configuration

Create `tax_deed_monitor_config.json`:
```json
{
    "scrape_interval_hours": 6,
    "alert_thresholds": {
        "high_value_min": 100000,
        "homestead_alert": true,
        "new_auction_alert": true,
        "canceled_threshold": 5
    }
}
```

## Features

### Comprehensive Data Extraction
- ✅ Auction listings with item counts
- ✅ Property expansion for detailed data
- ✅ Parcel numbers with BCPA links
- ✅ Legal descriptions
- ✅ Homestead status
- ✅ Assessed values
- ✅ Applicant parsing for Sunbiz matching
- ✅ GIS map links
- ✅ Real-time bid tracking
- ✅ Status monitoring (Upcoming/Canceled/Removed)

### Intelligent Monitoring
- ✅ Scheduled scraping
- ✅ Change detection
- ✅ Alert generation
- ✅ Historical tracking
- ✅ Statistical analysis
- ✅ JSON and database storage

### Search Capabilities
- ✅ By address
- ✅ By parcel number
- ✅ By applicant/company
- ✅ High-value properties
- ✅ Homestead properties
- ✅ Status filtering

## Output Files

- `tax_deed_auctions_YYYYMMDD_HHMMSS.json` - Full scrape results
- `tax_deed_latest_report.json` - Latest monitoring report
- `tax_deed_alerts.jsonl` - Alert log
- `tax_deed_report_YYYYMMDD_HHMMSS.json` - Timestamped reports

## Error Handling

The system includes:
- Retry logic for failed requests
- Graceful degradation
- Comprehensive logging
- JSON backups
- Database transaction safety

## Performance

- Async/await for concurrent operations
- Rate limiting to avoid blocking
- Efficient HTML parsing
- Batch database operations
- Indexed database queries

## Integration Points

### Sunbiz Matching
The `applicant_companies` field is parsed to extract company names for matching with Sunbiz data.

### Property Profile Integration
Parcel numbers can be cross-referenced with existing property data in the main ConcordBroker system.

### Alert Webhooks
Configure webhooks to integrate with:
- Slack
- Discord
- Email services
- Custom APIs

## Maintenance

- Monitor logs for errors
- Check JSON backups
- Verify database consistency
- Update scraping logic if website changes
- Adjust alert thresholds as needed