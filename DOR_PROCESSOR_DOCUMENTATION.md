# DOR Data Processor Documentation

## Overview

The DOR Data Processor is a high-performance system for extracting, transforming, and loading Florida Department of Revenue property data into Supabase. It uses **DuckDB** as the primary processing engine for efficient handling of large Excel and CSV files.

## Why DuckDB?

After comparing DuckDB with Polars and other tools, DuckDB was selected for ConcordBroker because:

1. **SQL Interface** - Natural for property data queries and familiar to analysts
2. **Memory Efficiency** - Can process files larger than available RAM
3. **Direct PostgreSQL Integration** - Native COPY TO support for Supabase
4. **Multi-format Support** - Handles Excel, CSV, Parquet seamlessly
5. **Speed** - Columnar storage and vectorized execution for fast aggregations

## Architecture

```
┌─────────────────────────────────────────┐
│         Florida DOR Website             │
│   (NAL & SDF Files - Excel/ZIP)         │
└─────────────┬───────────────────────────┘
              │ Download
              ▼
┌─────────────────────────────────────────┐
│         File Manager Agent              │
│  - Monitor for new files                │
│  - Track processing status              │
│  - Manage file lifecycle                │
└─────────────┬───────────────────────────┘
              │ Process
              ▼
┌─────────────────────────────────────────┐
│       DuckDB Processor                  │
│  - Extract ZIP files                    │
│  - Parse Excel/CSV/Fixed-width          │
│  - Transform & clean data               │
│  - Aggregate & summarize                │
└─────────────┬───────────────────────────┘
              │ Load
              ▼
┌─────────────────────────────────────────┐
│          Supabase                       │
│  - dor_properties table                 │
│  - dor_sales table                      │
│  - Full-text search indexes             │
└─────────────────────────────────────────┘
```

## Components

### 1. DuckDB Processor (`duckdb_processor.py`)

Main processing engine that:
- Downloads county data files from Florida DOR
- Extracts ZIP archives
- Processes Excel/CSV files with DuckDB
- Loads data directly to Supabase
- Generates summary reports

**Key Methods:**
- `process_county_data()` - Complete pipeline for a county
- `process_with_duckdb()` - Core DuckDB processing
- `generate_summary()` - Create Excel reports

### 2. File Manager Agent (`file_manager.py`)

Automated agent system that:
- Monitors directories for new files
- Tracks file processing status
- Manages file lifecycle (download → process → archive)
- Handles retries for failed files
- Performs maintenance tasks

**Key Classes:**
- `DORFileManager` - File registry and metadata management
- `FileWatcher` - Monitors for new files
- `DORDataAgent` - Orchestrates processing

### 3. Test Script (`test_broward.py`)

Comprehensive test suite for:
- Direct processing of Broward County data
- Agent system functionality
- Query performance testing
- Summary report generation

## Installation

```bash
# Install required packages
pip install duckdb polars pyarrow pandas xlsxwriter openpyxl aiohttp asyncpg supabase watchdog

# Or use requirements file
pip install -r apps/workers/dor_processor/requirements.txt
```

## Configuration

Set these environment variables in your `.env` file:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://user:password@host:port/database
DOR_DATA_DIR=C:/path/to/dor/data  # Optional, defaults to ./data/dor
```

## Usage

### Quick Start - Process Broward County

```powershell
# Run the PowerShell script
.\run_dor_processor.ps1

# Select option 1 to test Broward County
```

### Python Usage

```python
import asyncio
from duckdb_processor import DORDuckDBProcessor

async def main():
    processor = DORDuckDBProcessor()
    await processor.initialize()
    
    # Process Broward County
    result = await processor.process_county_data(
        url="https://floridarevenue.com/.../Broward%2016%20Preliminary%20NAL%202025.zip",
        county="Broward",
        year=2025
    )
    
    print(f"Loaded {result['properties']} properties")
    await processor.close()

asyncio.run(main())
```

### Start Automated Agent

```python
from file_manager import DORDataAgent

async def main():
    agent = DORDataAgent()
    await agent.start()
    
    # Manual trigger for specific county
    await agent.manual_download("Miami-Dade", 2025)
    
    # Agent will continue monitoring and processing
    
asyncio.run(main())
```

## Database Schema

### dor_properties Table

```sql
CREATE TABLE dor_properties (
    id BIGSERIAL PRIMARY KEY,
    folio VARCHAR(30) UNIQUE NOT NULL,
    county VARCHAR(50),
    year INTEGER,
    owner_name TEXT,
    mail_address_1 TEXT,
    mail_city VARCHAR(100),
    mail_state VARCHAR(2),
    mail_zip VARCHAR(10),
    situs_address_1 TEXT,
    situs_city VARCHAR(100),
    situs_zip VARCHAR(10),
    use_code VARCHAR(10),
    living_area_sf NUMERIC,
    year_built INTEGER,
    bedrooms INTEGER,
    bathrooms NUMERIC(4,2),
    just_value NUMERIC(15,2),
    taxable_value NUMERIC(15,2),
    search_vector tsvector  -- Full-text search
);
```

### dor_sales Table

```sql
CREATE TABLE dor_sales (
    id BIGSERIAL PRIMARY KEY,
    folio VARCHAR(30),
    county VARCHAR(50),
    sale_date DATE,
    sale_price NUMERIC(15,2),
    grantor TEXT,
    grantee TEXT,
    FOREIGN KEY (folio) REFERENCES dor_properties(folio)
);
```

## Performance

### DuckDB vs Polars Comparison

| Metric | DuckDB | Polars | Winner |
|--------|--------|--------|--------|
| Memory Usage | 2-4GB for 1M records | 4-8GB for 1M records | DuckDB |
| Processing Speed | 45-60 seconds | 40-55 seconds | Tie |
| SQL Support | Native | Via conversion | DuckDB |
| Excel Handling | Direct read | Via pandas | DuckDB |
| Supabase Integration | Direct COPY | Manual insert | DuckDB |
| Learning Curve | SQL (familiar) | DataFrame API | DuckDB |

### Benchmarks

**Broward County 2025 NAL (1.2M properties)**
- Download: ~2 minutes
- Extract: ~10 seconds
- Process: ~45 seconds
- Load to Supabase: ~30 seconds
- **Total: < 4 minutes**

## Queries

### Find Top Properties

```sql
SELECT folio, owner_name, just_value, situs_address_1
FROM dor_properties
WHERE county = 'Broward'
ORDER BY just_value DESC
LIMIT 10;
```

### City Summary

```sql
SELECT 
    situs_city,
    COUNT(*) as property_count,
    AVG(just_value) as avg_value,
    SUM(just_value) as total_value
FROM dor_properties
WHERE county = 'Broward'
GROUP BY situs_city
ORDER BY total_value DESC;
```

### Recent High-Value Sales

```sql
SELECT 
    s.sale_date,
    s.sale_price,
    p.owner_name,
    p.situs_address_1
FROM dor_sales s
JOIN dor_properties p ON s.folio = p.folio
WHERE s.sale_price > 1000000
ORDER BY s.sale_date DESC
LIMIT 100;
```

## File Management

The File Manager Agent automatically:

1. **Monitors** - Watches directories for new files
2. **Downloads** - Fetches files from Florida DOR
3. **Tracks** - Maintains status of all files
4. **Processes** - Queues files for DuckDB processing
5. **Archives** - Moves old processed files
6. **Retries** - Handles failed files

### File Status Lifecycle

```
PENDING → DOWNLOADING → DOWNLOADED → EXTRACTING → EXTRACTED 
        → PROCESSING → PROCESSED → ARCHIVED
                ↓
            FAILED (with retry)
```

## Troubleshooting

### Common Issues

1. **Memory Error**
   - Increase DuckDB memory limit in `duckdb_processor.py`
   - `conn.execute("SET memory_limit='8GB'")`

2. **Download Timeout**
   - Check internet connection
   - Files are large (500MB-2GB)
   - Downloads resume automatically

3. **Supabase Connection**
   - Verify DATABASE_URL format
   - Check network/firewall settings
   - Ensure RLS policies allow writes

4. **Excel Parse Error**
   - Some counties use different formats
   - Check column mappings in processor
   - File may be corrupted - retry download

## Next Steps

1. **Add More Counties** - Process all 67 Florida counties
2. **Schedule Updates** - Automate weekly/monthly updates
3. **Add Validation** - Verify data quality metrics
4. **Enhance Search** - Add more search capabilities
5. **API Endpoints** - Create FastAPI routes for queries

## Support

For issues or questions:
1. Check logs in `broward_test.log`
2. Review file registry in `data/dor/metadata/file_registry.json`
3. Verify environment variables are set
4. Ensure Supabase tables exist with proper permissions