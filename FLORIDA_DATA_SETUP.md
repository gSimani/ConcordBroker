# Florida Parcel Data Integration Setup Guide

## Overview
Complete system for downloading, storing, and monitoring Florida Property Tax Oversight (PTO) parcel data with automated update detection.

## System Components

### 1. Data Pipeline (`florida_parcel_pipeline.py`)
- Handles PIN (geometry) and PAR (full attributes) shapefiles
- Processes NAL files with proper DBF format handling
- Special handling for Miami-Dade and St. Johns condo files
- Chapter 119 redaction compliance
- Manages all known discrepancy reasons

### 2. Supabase Integration (`supabase_parcel_setup.py`)
- Automated download from Florida Revenue portal
- Real-time change detection
- Batch processing with progress tracking
- Error recovery and retry logic

### 3. Monitoring Agents
- **Florida_PTO_Monitor**: Checks for data updates every 24 hours
- **Data_Quality_Agent**: Validates data quality every 6 hours
- **Update_Scheduler**: Manages scheduled sync operations

### 4. Web Dashboard (`ParcelMonitor.tsx`)
- Real-time monitoring interface
- Agent control panel
- Update history tracking
- Manual sync triggers

## Setup Instructions

### Step 1: Configure Supabase

1. Create a new Supabase project at https://supabase.com

2. Run the schema SQL in Supabase SQL Editor:
```bash
# Copy contents of apps/api/supabase_schema.sql
# Paste into Supabase SQL Editor
# Execute the script
```

3. Get your Supabase credentials:
- Project URL: `https://your-project-id.supabase.co`
- Anon Key: Found in Settings > API
- Service Key: Found in Settings > API (keep secure!)

### Step 2: Configure Environment

1. Update `.env.supabase` with your credentials:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here
DATABASE_URL=postgresql://postgres:password@db.your-project-id.supabase.co:5432/postgres
```

### Step 3: Install Dependencies

```bash
cd apps/api
pip install -r requirements.txt

# Additional dependencies for parcel data
pip install geopandas shapely dbf supabase aiohttp schedule
```

### Step 4: Initial Data Download

```bash
# Run initial setup (creates tables, downloads priority counties)
python run_parcel_sync.py setup

# Check status
python run_parcel_sync.py status

# Download specific county
python run_parcel_sync.py download --county BROWARD
```

### Step 5: Start Monitoring

```bash
# Start continuous monitoring (runs in foreground)
python run_parcel_sync.py monitor

# Or run as background service (Linux/Mac)
nohup python run_parcel_sync.py monitor &

# Or use systemd service (recommended for production)
```

### Step 6: Access Web Dashboard

1. Navigate to: http://localhost:5173/admin/parcel-monitor
2. Login with admin credentials
3. Monitor agents and data updates in real-time

## Data Sources

The system monitors and downloads from:
- **Base URL**: https://floridarevenue.com/property/Documents/GISData
- **File Types**:
  - PIN_[COUNTY]_2024.zip (geometry only)
  - PAR_[COUNTY]_2024.zip (geometry + attributes)
  - NAL_[COUNTY]_2024.dbf (tax roll attributes)
  - CONDO_[COUNTY]_2024.zip (Miami-Dade & St. Johns only)

## Monitored Counties

### Priority Counties (Downloaded First)
- BROWARD
- MIAMI-DADE
- PALM BEACH

### Additional Counties
- MONROE
- MARTIN
- ST. LUCIE
- INDIAN RIVER
- OKEECHOBEE
- HENDRY
- COLLIER
- LEE
- CHARLOTTE
- SARASOTA
- MANATEE
- DESOTO
- GLADES

## Monitoring Features

### Automatic Update Detection
- Checks Florida Revenue portal every 24 hours
- Detects file changes via:
  - HTTP Last-Modified headers
  - File size comparison
  - SHA-256 hash verification

### Data Quality Checks
- Geometry validation
- Join success rates (PARCELNO ↔ PARCEL_ID)
- Duplicate detection
- Redaction compliance verification

### Notifications
- Email alerts to: admin@westbocaexecutiveoffice.com
- Slack integration (optional)
- Web dashboard real-time updates

## Database Schema

### Main Tables
- `florida_parcels`: Core parcel data with 60+ attributes
- `florida_condo_units`: Separate condo unit details
- `data_source_monitor`: Track source files and changes
- `parcel_update_history`: Update audit trail
- `monitoring_agents`: Agent configuration

### Useful Views
- `latest_parcels`: Most recent data per county
- `recent_sales`: Properties sold in last 6 months
- `high_value_properties`: Properties > $1M taxable value
- `data_quality_dashboard`: Quality metrics overview

## API Endpoints

```python
# Trigger sync for all counties
POST /api/trigger-parcel-sync

# Trigger sync for specific county
POST /api/trigger-parcel-sync
Body: { "county": "BROWARD" }

# Get monitoring status
GET /api/parcel-monitor/status

# Get update history
GET /api/parcel-monitor/history
```

## Troubleshooting

### Common Issues

1. **Missing parcels after import**
   - Check `discrepancy_reason` field
   - Common reasons: redacted, public ROW, phantom polygons

2. **Geometry errors**
   - System auto-repairs with `buffer(0)`
   - Check `data_quality_reports` table

3. **Download failures**
   - Check `data_source_monitor.status` and `notes`
   - Verify Florida Revenue portal is accessible

### Monitoring Commands

```bash
# Check agent status
python run_parcel_sync.py status

# View logs
tail -f logs/parcel_sync.log

# Database queries (in Supabase SQL Editor)
SELECT * FROM monitoring_status;
SELECT * FROM data_quality_dashboard;
SELECT check_for_updates();
```

## Data Update Schedule

- **Florida PTO Updates**: Annually in April (shapefiles) and July (tax rolls)
- **System Checks**: Daily at 2:00 AM and 2:00 PM
- **Quality Validation**: Every 6 hours
- **Manual Sync**: Available anytime via dashboard

## Security & Compliance

- Chapter 119 Florida Statutes compliance
- Automatic redaction of sensitive records
- Row Level Security (RLS) policies
- Audit trail for all operations

## Support

For issues or questions:
- Check logs: `logs/parcel_sync.log`
- Dashboard: `/admin/parcel-monitor`
- Database: Supabase SQL Editor
- Florida Revenue: https://floridarevenue.com/property

---

System configured to automatically monitor and update Florida parcel data with minimal manual intervention.