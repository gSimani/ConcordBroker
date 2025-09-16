# Florida Revenue Comprehensive Data Downloader

## Overview
This Playwright-based agent automatically downloads all NAL, NAP, and SDF files from Florida Revenue for all 67 counties. The system handles file extraction, directory management, error recovery, and progress tracking.

## Features
- **Comprehensive Coverage**: Downloads all 3 data types (NAL, NAP, SDF) for all 67 Florida counties
- **Smart Skip Logic**: Automatically skips already downloaded files
- **Automatic Extraction**: Extracts ZIP files and removes them after extraction
- **Error Handling**: Gracefully handles errors and continues with next file
- **Detailed Logging**: Creates comprehensive logs with timestamps
- **Progress Tracking**: Shows real-time download progress and statistics
- **Recovery Capability**: Saves failed downloads for retry

## Files Created

### Main Files
- `florida_comprehensive_downloader.py` - Main downloader agent
- `setup_florida_comprehensive_downloader.ps1` - Setup script
- `run_florida_downloader.ps1` - Simple runner script
- `test_florida_downloader.py` - Test script for verification

### Dependencies
- `requirements-florida-comprehensive.txt` - Updated with Playwright dependency

## Installation & Setup

### 1. Run Setup Script
```powershell
# Open PowerShell as Administrator
cd "C:\Users\gsima\Documents\MyProject\ConcordBroker"
.\setup_florida_comprehensive_downloader.ps1
```

### 2. Manual Installation (Alternative)
```bash
# Install Python dependencies
pip install playwright aiohttp aiofiles

# Install Playwright browser
python -m playwright install chromium
```

## Usage

### Quick Start
```powershell
# Simple method - run the launcher
.\run_florida_downloader.ps1
```

### Advanced Usage
```python
# Direct Python execution
python florida_comprehensive_downloader.py
```

### Test Mode
```python
# Test link extraction only
python test_florida_downloader.py
```

## Directory Structure

Files are organized as follows:
```
C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\
├── ALACHUA\
│   ├── NAL\
│   │   └── [extracted files]
│   ├── NAP\
│   │   └── [extracted files]
│   └── SDF\
│       └── [extracted files]
├── BAKER\
│   ├── NAL\
│   ├── NAP\
│   └── SDF\
... (continues for all 67 counties)
```

## Data Sources

The agent downloads from these URLs:

### NAL (Net Assessed Listed)
- **URL**: https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P
- **Description**: Net assessed values and property listings

### NAP (Name and Address of Property Owner) 
- **URL**: https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025P
- **Description**: Property owner names and addresses

### SDF (Sales Data File)
- **URL**: https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025P
- **Description**: Property sales transaction data

## Features Detail

### Smart File Management
- **Skip Existing**: Checks for existing files before downloading
- **Extraction**: Automatically extracts ZIP files
- **Cleanup**: Removes ZIP files after successful extraction
- **Validation**: Checks file integrity before processing

### Error Handling
- **Graceful Recovery**: Continues downloading even if some files fail
- **Detailed Logging**: Records all errors with context
- **Retry Information**: Saves failed downloads for manual retry
- **Timeout Management**: Handles network timeouts appropriately

### Progress Tracking
- **Real-time Stats**: Shows download progress as it happens
- **Summary Report**: Provides final statistics
- **Log Files**: Creates timestamped log files for each run

## Logging

The system creates detailed logs with format:
```
florida_download_YYYYMMDD_HHMMSS.log
```

Log includes:
- Start/end timestamps
- Download URLs and filenames
- Success/failure status
- Error messages with context
- Final statistics summary

## Statistics Tracked

- **Total Files**: Number of files processed
- **Downloaded**: Successfully downloaded files
- **Skipped**: Files already existing
- **Failed**: Files that failed to download
- **Extracted**: ZIP files successfully extracted

## Error Recovery

Failed downloads are saved to:
```
failed_downloads_YYYYMMDD_HHMMSS.json
```

This file contains:
- Failed download URLs
- Filenames
- Data types
- County information
- Can be used for manual retry

## Configuration

### County List
The system includes all 67 Florida counties:
```python
florida_counties = [
    'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN',
    'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DADE', 'DESOTO',
    # ... (complete list in code)
]
```

### File Paths
- **Base Directory**: `C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP`
- **Structure**: `[BASE]\[COUNTY]\[DATA_TYPE]\[files]`

## Testing

### Verification Test
```bash
python test_florida_downloader.py
```

This test:
- Verifies link extraction works
- Tests county name detection
- Validates URL formation
- Confirms Playwright functionality

### Expected Output
```
Testing link extraction...

Testing NAL at https://floridarevenue.com/...
Found 3 links:
  1. Alachua 11 Preliminary NAL 2025.zip -> County: ALACHUA
  2. Bay 13 Preliminary NAL 2025.zip -> County: BAY  
  3. Broward 16 Preliminary NAL 2025.zip -> County: BROWARD
```

## Troubleshooting

### Common Issues

1. **Playwright Browser Not Found**
   ```bash
   python -m playwright install chromium
   ```

2. **Permission Errors**
   - Run PowerShell as Administrator
   - Check directory permissions

3. **Network Timeouts**
   - The system has built-in retry logic
   - Check internet connection
   - Failed downloads are logged for retry

4. **Disk Space**
   - Each county's data can be several MB
   - Ensure adequate disk space (estimate 1-2GB total)

### Debug Mode
Add debug logging by modifying the logger level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

### Download Speed
- Uses async/await for concurrent operations  
- 1-second delay between downloads to avoid overwhelming server
- Respects server response times

### Resource Usage
- Headless browser for minimal resource usage
- Efficient memory management
- Automatic cleanup of temporary files

### Scalability
- Designed to handle all 67 counties (200+ files)
- Handles large file sizes efficiently
- Robust error recovery

## Maintenance

### Regular Updates
- Check Florida Revenue site for URL changes
- Update county list if needed
- Monitor for new data types

### Log Monitoring
- Review logs for recurring errors
- Monitor download success rates
- Check disk space usage

## Security Notes

- No sensitive data stored
- All downloads are public Florida data
- Respects server rate limits
- No authentication required

---

## Quick Reference

### Start Download
```powershell
.\run_florida_downloader.ps1
```

### View Progress
Watch the console output for real-time progress

### Check Results
- Files in: `C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\`
- Logs in: `florida_download_*.log`
- Failed downloads: `failed_downloads_*.json`

### Estimated Runtime
- Full download: 2-4 hours (depending on connection)
- Test run: 1-2 minutes
- Retry failed: 10-30 minutes

This comprehensive downloader ensures you have all Florida property data needed for the ConcordBroker system.