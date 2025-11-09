# Florida Revenue Data Download Agent

## Overview
Intelligent Playwright-based agent for downloading property tax data files from the Florida Department of Revenue. This agent automatically navigates the website, identifies available files, and downloads NAL, NAP, and SDF data for all 67 Florida counties.

## Features
- 🤖 **Intelligent Navigation**: Uses Playwright to navigate the Florida Revenue website
- 📁 **Multi-Type Support**: Downloads NAL, NAP, and SDF files for all counties
- 🔄 **Smart Resume**: Skips already downloaded files
- 📊 **Detailed Reporting**: Generates comprehensive download reports
- 🗂️ **Organized Storage**: Automatically organizes files by county and data type
- 🔍 **Error Handling**: Robust error handling with detailed logging

## Data Types

### NAL (Non Ad Valorem)
- Contains non ad valorem assessment data
- Format: CSV files
- Location: `/COUNTY_NAME/NAL/`

### NAP (Non Ad Valorem Property)
- Contains property-specific non ad valorem data  
- Format: CSV files
- Location: `/COUNTY_NAME/NAP/`

### SDF (Sales Data File)
- Contains property sales transaction data
- Format: CSV files
- Location: `/COUNTY_NAME/SDF/`

## Installation

```bash
# Install required packages
pip install playwright aiofiles

# Install Playwright browsers
playwright install chromium
```

## Usage

### Quick Start

```bash
# Run the agent
python apps/agents/florida_revenue_agent.py
```

### Python Integration

```python
import asyncio
from apps.agents.florida_revenue_agent import FloridaRevenueAgent

async def download_florida_data():
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    agent = FloridaRevenueAgent(base_path)
    await agent.run()

# Run the agent
asyncio.run(download_florida_data())
```

### Download Specific Data Type

```python
from apps.agents.florida_revenue_agent import FloridaRevenueAgent, DataType

async def download_nal_only():
    agent = FloridaRevenueAgent(base_path)
    await agent.initialize()
    await agent.download_all_files(DataType.NAL)
    await agent.browser.close()
```

## Directory Structure

```
DATABASE PROPERTY APP/
├── ALACHUA/
│   ├── NAL/
│   │   └── NAL11P202501.csv
│   ├── NAP/
│   │   └── NAP11P202501.csv
│   └── SDF/
│       └── SDF11P202501.csv
├── BAKER/
│   ├── NAL/
│   ├── NAP/
│   └── SDF/
└── ... (all 67 counties)
```

## Counties Covered

All 67 Florida counties including:
- Alachua, Baker, Bay, Bradford, Brevard, Broward
- Calhoun, Charlotte, Citrus, Clay, Collier, Columbia
- DeSoto, Dixie, Duval, Escambia, Flagler, Franklin
- Gadsden, Gilchrist, Glades, Gulf, Hamilton, Hardee
- Hendry, Hernando, Highlands, Hillsborough, Holmes
- Indian River, Jackson, Jefferson, Lafayette, Lake
- Lee, Leon, Levy, Liberty, Madison, Manatee, Marion
- Martin, Miami-Dade, Monroe, Nassau, Okaloosa, Okeechobee
- Orange, Osceola, Palm Beach, Pasco, Pinellas, Polk
- Putnam, Santa Rosa, Sarasota, Seminole, St. Johns
- St. Lucie, Sumter, Suwannee, Taylor, Union, Volusia
- Wakulla, Walton, Washington

## Output Report

The agent generates a JSON report with:
- Download statistics
- Success/failure details for each file
- File paths for successful downloads
- Error messages for failed downloads
- Timestamps for all operations

Example report structure:
```json
{
  "timestamp": "2024-01-12T10:30:00",
  "stats": {
    "total": 201,
    "success": 195,
    "failed": 3,
    "skipped": 3
  },
  "tasks": [
    {
      "county": "ALACHUA",
      "data_type": "NAL",
      "filename": "Alachua 11 Preliminary NAL 2025.zip",
      "status": "success",
      "file_path": "C:\\...\\ALACHUA\\NAL\\NAL11P202501.csv",
      "timestamp": "2024-01-12T10:31:00"
    }
  ]
}
```

## Logging

Logs are saved to `florida_revenue_agent.log` with detailed information about:
- Navigation steps
- File discovery
- Download progress
- Extraction operations
- Error details

## Error Handling

The agent handles common issues:
- Network timeouts
- Missing files
- Invalid links
- Extraction failures
- Navigation errors

Failed downloads are logged and reported but don't stop the entire process.

## Performance

- Downloads files sequentially with 2-second delays
- Processes ~200 files in approximately 30-45 minutes
- Automatically extracts ZIP files and removes them
- Skips already downloaded files for efficient re-runs

## Troubleshooting

### Browser doesn't open
```bash
playwright install chromium
```

### Downloads fail
- Check internet connection
- Verify Florida Revenue website is accessible
- Review logs for specific error messages

### Files not organizing correctly
- Ensure base path exists and is writable
- Check county name mapping in agent code

## Manual Fallback

If automated download fails for specific files:

1. Open browser to the data page:
   - NAL: https://floridarevenue.com/.../NAL/2025P
   - NAP: https://floridarevenue.com/.../NAP/2025P  
   - SDF: https://floridarevenue.com/.../SDF/2025P

2. Download missing files manually

3. Place in correct folder structure:
   `DATABASE PROPERTY APP/COUNTY_NAME/DATA_TYPE/`

## Integration with Other Systems

This agent is designed to work with:
- Supabase database loaders
- Property data processing pipelines
- Tax analysis systems
- GIS mapping tools

## Maintenance

### Update for New Year
Change year in URLs (2025P → 2026P):
```python
self.base_urls = {
    DataType.NAL: ".../NAL/2026P",
    DataType.NAP: ".../NAP/2026P",
    DataType.SDF: ".../SDF/2026P"
}
```

### Add New Data Types
1. Add to DataType enum
2. Add URL to base_urls dict
3. Update file extraction logic if needed

## Related Documentation

- [Sunbiz Agent Guide](./SUNBIZ_AGENT_GUIDE.md)
- [Florida Data Setup](./FLORIDA_DATA_SETUP.md)
- [Database Loading Guide](./DATABASE_SETUP.md)

## Support

For issues or questions:
1. Check the log file for detailed error messages
2. Verify website structure hasn't changed
3. Ensure all dependencies are installed
4. Review the generated report for specific failures

---

*Last Updated: January 2024*
*Version: 1.0.0*