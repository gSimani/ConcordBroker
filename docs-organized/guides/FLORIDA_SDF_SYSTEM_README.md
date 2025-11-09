# Florida SDF Data Download & Processing System

A comprehensive, robust system to download, process, and upload all Florida Sales Data Files (SDF) from the Florida Department of Revenue for all 67 counties to your Supabase database.

## 🚀 System Overview

This system provides a complete pipeline to:
- **Download** SDF ZIP files from Florida Department of Revenue for all 67 counties
- **Extract** and process CSV/TXT files programmatically (no Excel limitations)
- **Validate** and clean sales data with comprehensive error handling
- **Upload** all sales records to Supabase `property_sales_history` table
- **Track** progress with recovery mechanisms for interrupted operations

### Key Features

✅ **Complete Coverage**: All 67 Florida counties
✅ **High Performance**: Concurrent processing with configurable workers
✅ **Robust Error Handling**: Comprehensive retry logic and recovery
✅ **Progress Tracking**: Resume interrupted operations
✅ **Data Validation**: Comprehensive data quality checks
✅ **Scalable**: Handles millions of records efficiently
✅ **Production Ready**: Logging, monitoring, and state management

## 📊 Data Source Information

- **Source**: https://floridarevenue.com/property/dataportal
- **Data Type**: Sales Data Files (SDF) for 2025
- **Coverage**: All 67 Florida counties
- **Target Properties**: ~7.41 million properties
- **Current Database**: 95,354 records (incomplete)
- **Expected Final**: Complete sales history for all properties

## 🏗️ System Architecture

### Core Components

1. **`florida_counties_manager.py`** - Counties list with proper URL formatting
2. **`sdf_downloader.py`** - Robust file downloader with retry logic
3. **`sdf_processor.py`** - CSV/TXT processor with data validation
4. **`supabase_uploader.py`** - High-performance batch uploader
5. **`florida_sdf_master_orchestrator.py`** - Master orchestrator with recovery
6. **`run_florida_sdf_download.py`** - Main executable interface

### Database Schema

The system uploads to the `property_sales_history` table with these key fields:

```sql
-- Core identification
parcel_id VARCHAR(50)
county VARCHAR(50)

-- Sale details
sale_date DATE
sale_price NUMERIC(12,2)
sale_year/month/day INTEGER

-- Transaction parties
grantor VARCHAR(255)
grantee VARCHAR(255)

-- Document info
instrument_type VARCHAR(50)
or_book/or_page VARCHAR(20)

-- Qualification flags
qualified_sale BOOLEAN
arms_length BOOLEAN
foreclosure BOOLEAN
distressed_sale BOOLEAN
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** with required packages:
   ```bash
   pip install requests pandas supabase psycopg2 tqdm chardet
   ```

2. **Environment Variables** (in `.env.mcp`):
   ```bash
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   POSTGRES_URL=your_postgres_connection_string
   ```

3. **Disk Space**: At least 50GB available for downloads and processing

### System Check

```bash
# Check prerequisites and system status
python run_florida_sdf_download.py --check
```

### Run Tests

```bash
# Run comprehensive test suite
python simple_system_test.py

# Or run through main interface
python run_florida_sdf_download.py --run-tests
```

### Test Mode (Recommended First)

```bash
# Test with small counties first
python run_florida_sdf_download.py --test
```

### Production Mode

```bash
# Process ALL 67 counties (will take several hours)
python run_florida_sdf_download.py --production

# Process specific counties
python run_florida_sdf_download.py --counties MIAMI_DADE BROWARD PALM_BEACH

# With custom concurrency
python run_florida_sdf_download.py --production --max-concurrent 4
```

## 📋 Command Reference

### Main Commands

```bash
# System information and checks
python run_florida_sdf_download.py --check           # Check prerequisites
python run_florida_sdf_download.py --list-counties   # List all counties
python run_florida_sdf_download.py --status          # Show current status

# Testing and validation
python run_florida_sdf_download.py --run-tests       # Run test suite
python run_florida_sdf_download.py --test            # Test mode (small counties)

# Production operations
python run_florida_sdf_download.py --production      # All counties
python run_florida_sdf_download.py --counties X Y Z  # Specific counties
```

### Advanced Usage

```bash
# Custom working directory
python florida_sdf_master_orchestrator.py --working-dir /custom/path

# Disable recovery (start fresh)
python florida_sdf_master_orchestrator.py --no-recovery

# High concurrency for powerful systems
python florida_sdf_master_orchestrator.py --max-concurrent 6
```

## 🏆 County Information

### Priority Counties (Largest)
1. **MIAMI_DADE** - Largest county by properties
2. **BROWARD** - Second largest
3. **PALM_BEACH** - Third largest
4. **HILLSBOROUGH** - Tampa area
5. **ORANGE** - Orlando area
6. **PINELLAS** - St. Petersburg area
7. **DUVAL** - Jacksonville area
8. **LEE** - Fort Myers area
9. **POLK** - Lakeland area
10. **VOLUSIA** - Daytona Beach area

### Test Counties (Smallest)
- **LAFAYETTE** - Very small county (~2,000 properties)
- **LIBERTY** - Small county
- **DIXIE** - Small county
- **UNION** - Small county
- **GLADES** - Small county

## 📈 Performance Expectations

### Processing Speed
- **Single Thread**: 500-1,000 records/second
- **4 Parallel Workers**: 2,000-4,000 records/second
- **Memory Usage**: 2-4 GB during processing
- **Storage**: ~20-50 GB for complete dataset

### Time Estimates
- **Test Mode**: 5-15 minutes (small counties)
- **Single Large County**: 30-60 minutes (e.g., Miami-Dade)
- **Complete Dataset**: 2-6 hours (all 67 counties)

## 🔧 Configuration

### Environment Variables

```bash
# Required for database operations
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
POSTGRES_URL=postgres://user:pass@host:port/db

# Optional performance tuning
SUPABASE_ENABLE_SQL=true               # Enable direct SQL operations
RATE_LIMIT_WINDOW_MS=60000            # API rate limiting
RATE_LIMIT_MAX=100                    # Max requests per window
```

### System Settings

```python
# In orchestrator initialization
max_concurrent_counties = 2           # Concurrent county processing
batch_size = 1000                     # Records per batch upload
enable_recovery = True                # Resume interrupted operations
test_mode = False                     # Full vs. test mode
```

## 📊 Monitoring and Logging

### Log Files

All operations create detailed logs in:
- `TEMP/FLORIDA_SDF/logs/orchestrator_[session].log` - Main orchestration log
- `TEMP/SDF_DATA/logs/sdf_downloader_[timestamp].log` - Download operations
- `TEMP/SDF_PROCESSED/logs/sdf_processor_[timestamp].log` - Processing operations
- `TEMP/UPLOAD_LOGS/supabase_uploader_[timestamp].log` - Upload operations

### Progress Tracking

The system automatically saves progress to:
- `orchestration_progress.json` - Current overall progress
- `download_progress.json` - Download status per county
- `final_report_[session].json` - Complete session report

### State Recovery

Interrupted operations can be resumed automatically. The system tracks:
- ✅ Completed counties
- ❌ Failed counties (with retry)
- 📊 Processing statistics
- 🔄 Recovery attempts

## 🚨 Error Handling

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Download timeout | Network/server issues | Automatic retry with backoff |
| Invalid ZIP file | Corrupted download | Re-download with validation |
| CSV parsing error | Malformed data | Skip invalid records, log errors |
| Database timeout | Large batch upload | Use smaller batches, connection pooling |
| Disk space full | Large dataset | Cleanup old files, increase storage |

### Recovery Mechanisms

1. **Automatic Retry**: Failed operations retry with exponential backoff
2. **State Persistence**: Progress saved continuously for resume capability
3. **Graceful Degradation**: Switch to fallback methods on errors
4. **Partial Success**: Complete successful counties even if some fail
5. **Cleanup**: Automatic cleanup of temporary files

## 📋 Data Quality Assurance

### Validation Rules

- **Parcel ID**: Non-empty, minimum 5 characters, contains numbers
- **Sale Price**: Positive number, reasonable range ($1 - $1B)
- **Sale Date**: Valid date, 1900-2025 range
- **Quality Codes**: Florida DOR standard codes (01-19)
- **Text Fields**: Cleaned, truncated to field limits

### Quality Metrics

The system tracks:
- **Valid Records**: Pass all validation rules
- **Invalid Records**: Fail validation (logged but skipped)
- **Duplicate Records**: Handled via database constraints
- **Data Quality Score**: Percentage of valid records

### Qualified Sales Determination

Based on Florida DOR quality codes:
- **Qualified (01-05)**: Arms-length market sales
- **Unqualified (06-19)**: Non-market sales (foreclosure, family, etc.)

## 🔒 Security Considerations

### Data Protection
- Environment variables for credentials (never hardcoded)
- Service role key for database operations
- API key validation for all requests
- No sensitive data in logs

### Access Control
- Supabase RLS policies apply to all operations
- Service role required for bulk operations
- Rate limiting to prevent abuse
- Audit trail in all logs

## 🎯 Success Metrics

### Key Performance Indicators

- **Completion Rate**: Target 95%+ counties successfully processed
- **Data Quality**: Target 90%+ records pass validation
- **Upload Success**: Target 98%+ records uploaded to database
- **Processing Speed**: Target 2,000+ records/second
- **Recovery Rate**: Target 90%+ failed counties recovered on retry

### Validation Checklist

Before considering the operation complete:

- [ ] All 67 counties attempted
- [ ] 95%+ counties completed successfully
- [ ] 90%+ data quality score achieved
- [ ] Database record count increased significantly
- [ ] No critical errors in final report
- [ ] Failed counties documented with reasons
- [ ] System logs saved for audit

## 📞 Support and Troubleshooting

### Quick Diagnostics

```bash
# Check system status
python run_florida_sdf_download.py --status

# Validate individual components
python simple_system_test.py

# Check environment
python run_florida_sdf_download.py --check
```

### Common Commands

```bash
# Restart failed counties only
python florida_sdf_master_orchestrator.py --counties [FAILED_LIST]

# Force clean restart (no recovery)
python florida_sdf_master_orchestrator.py --no-recovery

# Monitor live progress
tail -f TEMP/FLORIDA_SDF/logs/orchestrator_*.log
```

### Debug Information

For support, provide:
1. Session ID from logs
2. Final report JSON file
3. Error messages from logs
4. System configuration (counties, concurrency, etc.)
5. Environment details (OS, Python version, available resources)

---

## 🎉 System Complete!

This comprehensive system provides everything needed to download, process, and upload complete Florida sales data. The modular architecture allows for easy maintenance and enhancement, while robust error handling ensures reliable operation even with network issues or data problems.

**Next Steps:**
1. ✅ Run system check: `python run_florida_sdf_download.py --check`
2. ✅ Test with small counties: `python run_florida_sdf_download.py --test`
3. ✅ Run production mode: `python run_florida_sdf_download.py --production`
4. ✅ Monitor progress and handle any failures
5. ✅ Validate final database contents

The system is designed to handle the full 7.41M properties across all 67 Florida counties efficiently and reliably.