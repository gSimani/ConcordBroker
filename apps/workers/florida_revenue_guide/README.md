# Florida Revenue NAL/SDF/NAP Users Guide Monitoring System

This system monitors the Florida Revenue NAL/SDF/NAP Users Guide PDF for updates, extracts schema definitions, and validates data files against the official specifications.

## Components

### 1. Guide Downloader (`guide_downloader.py`)
- Downloads the Users Guide PDF from Florida Revenue website
- Checks for updates based on file headers (size, etag, last-modified)
- Automatically detects new year versions (e.g., 2025 guide when available)
- Maintains version history with SHA256 checksums
- URL: https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/User%20Guides/2024%20Users%20guide%20and%20quick%20reference/2024_NAL_SDF_NAP_Users_Guide.pdf

### 2. Guide Parser (`guide_parser.py`)
- Extracts field definitions from the PDF using pdfplumber and PyPDF2
- Parses schema for NAL, SDF, NAP, NAV, and TPP file types
- Extracts:
  - Field names, types, lengths, and positions
  - Validation rules and patterns
  - Code tables (qualification codes, use codes, etc.)
  - Record layouts

### 3. Data Validator (`data_validator.py`)
- Validates Florida Revenue data files against extracted schema
- Supports multiple formats:
  - CSV files
  - Tab-delimited text files
  - Pipe-delimited text files
  - Fixed-width text files
  - JSON files
- Performs field-level validation:
  - Data type checking
  - Pattern matching (parcel IDs, ZIP codes, etc.)
  - Range validation
  - Required field checking
  - Code validation

### 4. Monitor (`monitor.py`)
- Orchestrates the entire system
- Daily checks for PDF updates (default: 4:00 AM)
- Monthly checks for new year guides
- Automatic re-parsing when updates detected
- Validates sample data files after schema updates

## File Types Supported

### NAL (Name Address Library)
- Property owner names and addresses
- Mailing information
- Contact details

### SDF (Sales Data File)
- Property sales transactions
- Sale prices and dates
- Qualification codes
- Official record references

### NAP (Non-Ad Valorem Parcel)
- Non-ad valorem assessments
- Special district information
- Assessment values

### NAV (Non-Ad Valorem Assessment)
- Assessment details
- Tax information
- Exemptions

### TPP (Tangible Personal Property)
- Business personal property
- Equipment and inventory
- Assessment values

## Usage

### One-time Check
```bash
python monitor.py --mode once
```

### Continuous Monitoring
```bash
python monitor.py --mode monitor --time 04:00
```

### Validate Data File
```bash
# Auto-detect file type
python monitor.py --mode validate --file NAL16P202501.csv

# Specify file type
python monitor.py --mode validate --file data.csv --type SDF
```

### Direct Validation
```bash
python data_validator.py NAL16P202501.csv
```

## Installation

### Required Libraries
```bash
pip install requests
pip install pdfplumber
pip install PyPDF2
pip install schedule
```

## Directory Structure
```
data/florida_revenue_guide/
├── pdfs/                    # Downloaded PDF files
│   ├── NAL_SDF_NAP_Users_Guide_latest.pdf
│   └── NAL_SDF_NAP_Users_Guide_2024_*.pdf
├── extracted/               # Extracted schemas
│   └── schema.json
└── metadata/               # Version history and logs
    ├── version_history.json
    ├── update_log.json
    └── sample_validation.json
```

## Schema Format

The extracted schema contains:
```json
{
  "version": "extracted",
  "source": "Florida Revenue NAL/SDF/NAP Users Guide",
  "file_schemas": {
    "NAL": {
      "name": "Name Address Library",
      "fields": [...]
    },
    "SDF": {
      "name": "Sales Data File",
      "fields": [...]
    }
  },
  "field_definitions": [...],
  "data_types": {...},
  "statistics": {...}
}
```

## Validation Output

Validation results include:
- File type detection
- Format identification
- Row/record counts
- Error details with line numbers
- Warning messages
- Field-level validation errors

## Features

- **Automatic Updates**: Checks for new PDF versions daily
- **Year Detection**: Automatically finds new year guides
- **Schema Extraction**: Parses PDF tables and text for field definitions
- **Multi-Format Support**: Handles various data file formats
- **Comprehensive Validation**: Field-level validation with detailed error reporting
- **Integration Ready**: Can be integrated with data pipelines
- **Logging**: Detailed logging for monitoring and debugging

## Error Handling

- Network errors during download are logged and retried
- PDF parsing errors are caught and reported
- Validation continues even with errors (up to limits)
- All errors are logged with context

## Performance

- Large file support with streaming
- Progress reporting for downloads
- Validation limited to 100,000 rows for performance
- Batch error reporting to avoid memory issues

## Integration with Existing Systems

This monitor can be integrated with:
- Broward County Daily Index system
- Property data pipelines
- Supabase database loaders
- Data quality monitoring systems

## Maintenance

- Check logs regularly: `florida_revenue_monitor.log`
- Review update history: `data/florida_revenue_guide/metadata/update_log.json`
- Monitor validation results for data quality trends
- Update URL patterns if Florida Revenue changes structure