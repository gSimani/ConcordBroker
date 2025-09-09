# 🚨 EMERGENCY DATA PIPELINE FIX PLAN

## Critical Issues Found
1. **Florida Revenue Portal Access BROKEN** - All NAL/NAP/NAV/SDF URLs return 401 Unauthorized
2. **Database Field Mismatch** - UI expects `phy_addr1` but DB has `property_address`
3. **No Real Data** - Only 3 mock properties instead of millions of Florida records
4. **All Agents Dead** - 40+ monitoring scripts exist but NONE are running

## Immediate Actions Required

### Phase 1: Fix Field Mappings (2 hours)
```sql
-- Add missing columns to florida_parcels
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS phy_addr1 VARCHAR(255),
ADD COLUMN IF NOT EXISTS phy_city VARCHAR(100),
ADD COLUMN IF NOT EXISTS phy_zipcd VARCHAR(10),
ADD COLUMN IF NOT EXISTS av_sd NUMERIC,
ADD COLUMN IF NOT EXISTS tv_sd NUMERIC,
ADD COLUMN IF NOT EXISTS lnd_val NUMERIC,
ADD COLUMN IF NOT EXISTS tot_lvg_area NUMERIC,
ADD COLUMN IF NOT EXISTS act_yr_blt INTEGER;

-- Copy data from existing columns
UPDATE florida_parcels SET
  phy_addr1 = property_address,
  phy_city = property_city,
  phy_zipcd = property_zip,
  av_sd = assessed_value,
  tv_sd = taxable_value,
  lnd_val = land_value,
  tot_lvg_area = total_living_area,
  act_yr_blt = year_built;
```

### Phase 2: Download Real Data (8 hours)

#### Option A: Direct Download (Recommended)
```python
# Download Broward County NAL file directly
import requests

# NAL 2025 Preliminary
url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P/broward_nal_2025.zip"

# Try with session and headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://floridarevenue.com/'
})

response = session.get(url)
if response.status_code == 200:
    with open('broward_nal_2025.zip', 'wb') as f:
        f.write(response.content)
```

#### Option B: Alternative Sources
1. **Broward Property Appraiser Direct API**
   - https://bcpa.net/api/
   
2. **Florida Geographic Data Library**
   - https://www.fgdl.org/metadataexplorer/explorer.jsp
   
3. **County Tax Collector**
   - https://www.broward.org/RecordsTaxesTreasury/

### Phase 3: Fix the Assessment Value Issue

The property shows $180 assessed value instead of $601,370 because:

```python
# WRONG - What's happening now
data = {
    "assessed_value": 180  # Some test value or partial data
}

# CORRECT - What should happen
data = {
    "assessed_value": 601370,  # From NAV file
    "just_value": 628040,      # From NAL file  
    "taxable_value": 601370,   # From NAP file
    "land_value": 85580,       # From NAL file
    "building_value": 542460   # Calculated: just_value - land_value
}
```

### Phase 4: Restart Data Pipeline

```bash
# 1. Start the master orchestrator
cd apps/workers
python florida_master_orchestrator.py

# 2. Start individual monitors
python florida_nav/nav_monitor.py
python florida_nal_counties/nal_processor.py
python sunbiz_sftp/sunbiz_downloader.py

# 3. Start the comprehensive monitor
python florida_comprehensive_monitor.py
```

### Phase 5: Fix Sunbiz Integration

```python
# Correct SFTP credentials
import paramiko

sftp_config = {
    'hostname': 'sftp.floridados.gov',
    'username': 'Public',
    'password': 'PubAccess1845!',
    'port': 22
}

# Download corporate data
sftp = paramiko.SSHClient()
sftp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sftp.connect(**sftp_config)

# Navigate to /business_entity/
sftp_client = sftp.open_sftp()
sftp_client.chdir('/business_entity/')

# Download weekly updates
sftp_client.get('weekly_update.zip', 'local_weekly_update.zip')
```

## Data Source Priority

### Must Have (Critical)
1. **NAL** - Name, Address, Legal description
2. **NAV** - Name, Address, Values (assessed, just, taxable)
3. **SDF** - Sales Data File (transaction history)

### Should Have (Important)
4. **NAP** - Name, Address, Portability
5. **Sunbiz** - Corporate entity data
6. **Broward Daily Index** - Recording updates

### Nice to Have
7. **TPP** - Tangible Personal Property
8. **Cadastral** - GIS boundaries
9. **Permits** - Building permits

## Expected Results After Fix

| Field | Current (Wrong) | After Fix (Correct) |
|-------|----------------|---------------------|
| Owner | INVITATION HOMES | IH3 PROPERTY FLORIDA LP |
| Assessed | $180 | $601,370 |
| Land Value | $145,000 | $85,580 |
| Building | $435,000 | $542,460 |
| Living Area | N/A | 3,012 sq ft |
| Year Built | N/A | 2003 |

## Monitoring Dashboard

Create a monitoring dashboard to track:
- Last successful download per data source
- Record count per table
- Data freshness (days since update)
- Failed download attempts
- Field mapping validation

## Timeline

- **Hour 1-2**: Fix database field mappings
- **Hour 3-4**: Deploy missing tables
- **Hour 5-8**: Download Broward NAL/NAV/SDF files
- **Hour 9-10**: Process and load data
- **Hour 11-12**: Verify UI displays correctly
- **Day 2**: Full Florida counties
- **Day 3**: Sunbiz integration
- **Week 2**: Automated monitoring

## Success Metrics

✅ Property 474131031040 shows:
- Correct owner: IH3 PROPERTY FLORIDA LP
- Correct assessed value: $601,370
- Complete sales history (5 transactions)
- Active Sunbiz entity data
- No "N/A" values for existing data

## Contact for Data Issues

- Florida Revenue Portal: dor.servicecenter@floridarevenue.com
- Broward Property Appraiser: webmaster@bcpa.net
- Sunbiz Data: DataRequests@dos.myflorida.com