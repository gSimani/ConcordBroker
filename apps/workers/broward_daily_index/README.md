# Broward County Daily Index Extract Files System

Complete system for downloading, parsing, and monitoring Broward County Daily Index Extract Files from:
https://www.broward.org/RecordsTaxesTreasury/Records/Pages/DailyIndexExtractFiles.aspx

## Features

- **Automated Download**: Fetches daily index files from Broward County website
- **Multi-format Parser**: Handles CSV, TXT, XML, and JSON formats
- **Database Integration**: Stores records in Supabase with property linking
- **Daily Monitoring**: Automated daily checks for new files
- **Historical Loading**: Can load historical data for any date range
- **Error Handling**: Robust error handling and retry mechanisms
- **Progress Tracking**: Detailed logging and status reporting

## Components

### 1. Downloader (`downloader.py`)
- Scrapes the Broward County website for available files
- Downloads ZIP files and extracts contents
- Maintains download history and checksums
- Supports batch downloading

### 2. Parser (`parser.py`)
- Parses multiple file formats (CSV, TXT, XML, JSON)
- Standardizes field names across formats
- Extracts key information:
  - Document details (type, number, book, page)
  - Party information (grantor, grantee)
  - Property data (parcel ID, address, legal description)
  - Transaction details (consideration, stamps)

### 3. Database (`database.py`)
- Manages Supabase integration
- Inserts parsed records in batches
- Links records to existing properties
- Tracks metadata and statistics

### 4. Pipeline (`pipeline.py`)
- Orchestrates the complete workflow
- Coordinates download, parse, and load operations
- Provides summary statistics
- Handles error recovery

### 5. Monitor (`monitor.py`)
- Runs as a background service
- Performs daily checks at scheduled times
- Logs all operations
- Saves status to JSON file

## Database Schema

The system uses three main tables:

1. **broward_daily_records**: Stores all daily index records
2. **broward_daily_metadata**: Tracks file downloads and processing
3. **broward_daily_properties**: Links records to properties

## Installation

1. Install required packages:
```bash
pip install requests beautifulsoup4 schedule
```

2. Create database tables in Supabase:
```sql
-- Run the SQL from broward_daily_index_tables.sql
```

3. Ensure environment variables are set:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

## Usage

### One-time Run (Download latest day)
```bash
python apps/workers/broward_daily_index/monitor.py --mode once --days 1
```

### Initial Historical Load (Last 30 days)
```bash
python apps/workers/broward_daily_index/monitor.py --mode initial --days 30
```

### Start Daily Monitoring Service
```bash
python apps/workers/broward_daily_index/monitor.py --mode monitor --time "02:00"
```

### Direct Pipeline Usage
```python
from apps.workers.broward_daily_index.pipeline import BrowardDailyIndexPipeline

pipeline = BrowardDailyIndexPipeline()
result = pipeline.run_full_pipeline(days_back=7)
print(result)
```

## Monitoring

The monitor service:
- Runs daily checks at specified time (default 2:00 AM)
- Logs all operations to `broward_daily_monitor.log`
- Saves status to `broward_monitor_status.json`
- Automatically retries on failures

## Data Flow

1. **Download**: Files are downloaded from Broward County website
2. **Extract**: ZIP files are extracted to processed directory
3. **Parse**: Each file is parsed based on its format
4. **Transform**: Records are standardized to common schema
5. **Load**: Records are inserted into database in batches
6. **Link**: Records are linked to existing properties by parcel ID

## File Structure

```
data/broward_daily_index/
├── raw/              # Downloaded ZIP files
├── processed/        # Extracted files
├── archive/          # Archived old files
└── metadata/         # Download history and metadata
```

## Record Types Handled

- DEED - Real Estate Deed
- MTG - Mortgage
- SAT - Satisfaction of Mortgage
- LIS - Lis Pendens
- LIEN - Lien
- JUDG - Judgment
- And many more...

## Error Handling

- Network failures: Automatic retry with exponential backoff
- Parse errors: Logged and skipped, processing continues
- Database errors: Batches are retried, failures logged
- Missing files: Logged and skipped

## Performance

- Batch processing: 500 records per database insert
- Parallel downloads: Multiple files downloaded concurrently
- Efficient parsing: Streaming parsers for large files
- Progress reporting: Regular status updates during processing

## Maintenance

- Logs rotate automatically
- Old files can be archived after processing
- Database indexes optimize query performance
- Regular status checks ensure system health