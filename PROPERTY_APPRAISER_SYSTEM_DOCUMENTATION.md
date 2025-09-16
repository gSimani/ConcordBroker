# Florida Property Appraiser Data System Documentation

## System Overview
Complete documentation for managing Florida property appraiser data from 67 counties, including download, processing, upload, and monitoring.

## Data Source
- **Primary URL**: https://floridarevenue.com/property/dataportal/Pages/default.aspx
- **Data Files Path**: `/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files`
- **Update Frequency**: Annually (major updates) with periodic corrections
- **Data Format**: NAL, NAP, NAV, SDF files in CSV format
- **Total Records**: ~9.7 million properties across Florida

## Directory Structure
```
C:\Users\gsima\Documents\MyProject\ConcordBroker\
├── TEMP\DATABASE PROPERTY APP\
│   ├── ALACHUA\
│   │   ├── NAL\         # Name, Address, Legal descriptions
│   │   ├── NAP\         # Property characteristics
│   │   ├── NAV\         # Assessed values
│   │   └── SDF\         # Sales data
│   ├── BAKER\
│   └── ... (67 counties total)
```

## Database Schema Mapping

### NAL (Name, Address, Legal) → florida_parcels table

| NAL Column | Database Column | Type | Notes |
|------------|----------------|------|-------|
| PARCEL_ID | parcel_id | varchar | Primary key component |
| CO_NO | county | varchar | County code/name |
| ASMNT_YR | year | integer | Assessment year (2025) |
| OWN_NAME | owner_name | varchar | Property owner name |
| OWN_ADDR1 | owner_addr1 | varchar | Owner address line 1 |
| OWN_ADDR2 | owner_addr2 | varchar | Owner address line 2 |
| OWN_CITY | owner_city | varchar | Owner city |
| OWN_STATE | owner_state | varchar(2) | State code (2 chars) |
| OWN_ZIPCD | owner_zip | varchar | Owner ZIP code |
| PHY_ADDR1 | phy_addr1 | varchar | Property address line 1 |
| PHY_ADDR2 | phy_addr2 | varchar | Property address line 2 |
| PHY_CITY | phy_city | varchar | Property city |
| PHY_ZIPCD | phy_zipcd | varchar | Property ZIP code |
| S_LEGAL | legal_desc | text | Legal description |
| PA_UC | property_use | varchar | Property use code |
| JV | just_value | numeric | Just/market value |
| LND_VAL | land_value | numeric | Land value |
| AV_SD | assessed_value | numeric | Assessed value |
| TV_SD | taxable_value | numeric | Taxable value |
| ACT_YR_BLT | year_built | integer | Actual year built |
| TOT_LVG_AREA | total_living_area | numeric | Living area sq ft |
| LND_SQFOOT | land_sqft | numeric | Land square footage |
| SALE_PRC1 | sale_price | numeric | Most recent sale price |
| SALE_YR1/MO1 | sale_date | timestamp | Sale date (YYYY-MM-01) |
| QUAL_CD1 | sale_qualification | varchar | Sale qualification code |

### Calculated Fields
- `building_value = just_value - land_value` (when both present)
- `land_acres = land_sqft / 43560`
- `sale_date = YYYY-MM-01T00:00:00` format for timestamps

## Upload Process

### Prerequisites
1. **Database Indexes** (CREATE_INDEXES.sql):
```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_florida_parcels_key
  ON public.florida_parcels (parcel_id, county, year);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_year
  ON public.florida_parcels (county, year);

CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name
  ON public.florida_parcels (owner_name);
```

2. **Timeout Configuration** (APPLY_TIMEOUTS_NOW.sql):
```sql
-- Apply before bulk upload
ALTER ROLE authenticated IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE authenticated IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';
ALTER ROLE anon IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE anon IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';
ALTER ROLE service_role IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE service_role IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';
```

3. **Restore Timeouts** (REVERT_TIMEOUTS_AFTER.sql):
```sql
-- Restore after upload
ALTER ROLE authenticated IN DATABASE postgres RESET statement_timeout;
ALTER ROLE authenticated IN DATABASE postgres RESET idle_in_transaction_session_timeout;
-- (repeat for anon and service_role)
```

### Upload Configuration
```python
# Optimized parameters
BATCH_SIZE = 1000          # Records per batch
PARALLEL_WORKERS = 4        # Concurrent upload threads
MAX_RETRIES = 3            # Retry attempts for failed batches
RETRY_DELAY = 2            # Base delay for exponential backoff

# Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SERVICE_ROLE_KEY = "eyJhbG..."  # Use service_role for bulk operations

# Performance headers
headers = {
    'Prefer': 'return=minimal,resolution=merge-duplicates,count=none',
    'Content-Type': 'application/json'
}
```

### Data Validation Rules

1. **Required Fields**:
   - parcel_id (non-empty string)
   - county (uppercase, valid Florida county)
   - year (integer, typically current or previous year)

2. **Data Cleaning**:
   - Truncate owner_state to 2 characters
   - Convert empty strings to NULL for timestamp fields
   - Handle NaN values appropriately (NULL for numeric, empty string for text)
   - Calculate building_value only when both JV and LND_VAL present

3. **Conflict Resolution**:
   - Upsert on conflict: `(parcel_id, county, year)`
   - Merge duplicates using `resolution=merge-duplicates`

## Error Handling

### Common Issues and Solutions

| Error Code | Issue | Solution |
|------------|-------|----------|
| 57014 | Statement timeout | Apply timeout removal SQL before upload |
| 22001 | Value too long | Truncate fields (e.g., owner_state to 2 chars) |
| PGRST204 | Column not found | Map to correct column names (e.g., land_sqft not land_square_footage) |
| 429 | Rate limiting | Use exponential backoff with jitter |

### Retry Strategy
```python
for attempt in range(MAX_RETRIES):
    try:
        # Upload batch
        result = client.table('florida_parcels').upsert(records).execute()
        break
    except Exception as e:
        if '429' in str(e):  # Rate limited
            delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
        elif '57014' in str(e):  # Timeout
            delay = RETRY_DELAY * (attempt + 1)
            time.sleep(delay)
```

## Monitoring Agent Configuration

### Update Check Frequency
- Daily check at 2 AM EST
- Weekly deep verification on Sundays
- Annual major update expected in January

### Files to Monitor
1. NAL files (primary property data)
2. NAP files (property characteristics)
3. NAV files (assessed values)
4. SDF files (sales data)

### Change Detection
- Compare file timestamps
- Track file sizes
- Store checksums for change detection
- Log all download attempts and results

## Performance Metrics

### Expected Throughput
- Single thread: ~500-1000 records/second
- 4 parallel workers: ~2000-4000 records/second
- Full dataset (9.7M): 1.5-3 hours with optimizations

### Resource Usage
- Memory: ~2-4 GB for parallel processing
- Network: ~50-100 Mbps during upload
- Disk: ~5-10 GB for CSV files

## Maintenance Tasks

### Daily
- Check monitoring agent logs
- Verify upload progress if running
- Monitor error rates

### Weekly
- Compare local vs database record counts
- Check for new counties or schema changes
- Review failed batch logs

### Monthly
- Full data validation sample (1% random check)
- Performance metric review
- Storage cleanup (old CSV files)

### Annual
- Major update processing (January)
- Schema migration if needed
- Historical data archival

## Security Considerations

1. **Credentials**:
   - Never commit SERVICE_ROLE_KEY to version control
   - Use environment variables for production
   - Rotate keys periodically

2. **Data Privacy**:
   - Property data is public record
   - Ensure PII handling complies with regulations
   - Log access for audit purposes

3. **Rate Limiting**:
   - Respect API rate limits
   - Implement backoff strategies
   - Monitor for 429 responses

## Troubleshooting Guide

### Upload Failures
1. Check timeout settings are disabled
2. Verify indexes exist
3. Confirm column mappings match schema
4. Review error logs for specific issues

### Data Inconsistencies
1. Compare source CSV to database
2. Check for transformation errors
3. Verify calculated fields
4. Review upsert conflict handling

### Performance Issues
1. Increase batch size (max 5000)
2. Add more parallel workers (max 8)
3. Check network connectivity
4. Verify database isn't under load

## Contact Information

### Data Source Support
- Florida Department of Revenue
- Website: https://floridarevenue.com
- Data Portal: Property Tax Oversight

### Database Support
- Platform: Supabase
- Project ID: pmispwtdngkcmsrsjwbp
- Support: via dashboard tickets

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-14 | Initial documentation |
| 1.1 | 2025-01-14 | Added monitoring agent specs |

---

*This documentation should be updated whenever schema changes, new counties are added, or upload processes are modified.*