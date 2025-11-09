# Daily Property Update System - Quick Start Guide

## 🚀 Getting Started

This guide will help you get the daily property update system running in **under 30 minutes**.

## Prerequisites

1. **Python 3.11+** installed
2. **Supabase account** with project set up
3. **Git** for version control
4. **Environment variables** configured in `.env.mcp`

## Step-by-Step Setup

### 1. Install Dependencies (5 minutes)

```bash
# Navigate to project
cd C:\Users\gsima\Documents\MyProject\ConcordBroker

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### 2. Deploy Database Schema (5 minutes)

```bash
# Deploy the complete schema to Supabase
python scripts/deploy_schema.py
```

**Expected Output**:
```
================================================================================
DEPLOYING DAILY UPDATE SCHEMA TO SUPABASE
================================================================================

🧪 Testing database connection...
✅ Connection successful!

🚀 Deploying schema...
✅ Schema deployed successfully!

📋 Tables created (6):
   ✓ florida_parcels
   ✓ property_sales_history
   ✓ property_change_log
   ✓ data_update_jobs
   ✓ file_checksums
   ✓ florida_counties

⚙️  Functions created (3):
   ✓ get_daily_update_stats
   ✓ get_county_stats
   ✓ log_property_change
```

### 3. Test Portal Access (5 minutes)

```bash
# Test Florida Revenue portal with Playwright
python scripts/test_portal_access.py
```

This will:
- Launch a browser window
- Navigate to the portal
- Take screenshots
- Identify file structure
- Save screenshots to `test-screenshots/`

### 4. Download Sample County Data (10 minutes)

Let's start with **Broward County** as a test:

```bash
# Download NAL, NAP, NAV, and SDF files for Broward
python scripts/download_county.py --county BROWARD
```

**Expected Output**:
```
================================================================================
DOWNLOADING BROWARD COUNTY DATA
================================================================================

🤖 Launching browser...
📡 Navigating to portal...
🔍 Looking for Tax Roll Data Files...
✅ Found Tax Roll Data Files

📂 Processing NAL files...
   📥 Downloading BROWARD_NAL_2025...
   ✅ Downloaded: BROWARD_NAL_2025.txt
      Size: 25,000,000 bytes
      MD5: abc123def456...

📂 Processing SDF files...
   📥 Downloading BROWARD_SDF_2025...
   ✅ Downloaded: BROWARD_SDF_2025.txt
```

### 5. Parse Downloaded Files (3 minutes)

```bash
# Parse NAL and SDF files into CSV format
python scripts/parse_county_files.py --county BROWARD
```

**Expected Output**:
```
================================================================================
PARSING BROWARD COUNTY FILES
================================================================================

📄 Parsing NAL file: BROWARD_NAL_2025.txt
   Processed 10,000 lines...
   Processed 20,000 lines...
   ✅ Parsed 25,234 records

💾 Exporting to CSV: BROWARD_NAL_parsed.csv
   ✅ Exported 25,234 records

📄 Parsing SDF file: BROWARD_SDF_2025.txt
   ✅ Parsed 3,456 records
```

### 6. Load Data into Supabase (2 minutes)

```bash
# First, do a dry-run to verify
python scripts/load_county_data.py --county BROWARD --dry-run

# Then load for real
python scripts/load_county_data.py --county BROWARD
```

**Expected Output**:
```
================================================================================
LOADING BROWARD DATA INTO SUPABASE
================================================================================

📊 Loading NAL data from: BROWARD_NAL_parsed.csv
   📋 Read 25,234 records from CSV
   💾 Inserting into database (batch size: 1000)...
      Inserted batch 1: 1000 records (total: 1,000)
      Inserted batch 2: 1000 records (total: 2,000)
      ...
   ✅ Loaded 25,234 records

📊 Loading SDF data from: BROWARD_SDF_parsed.csv
   ✅ Loaded 3,456 records

🔍 Verifying data in database...
   florida_parcels: 25,234 records for BROWARD
   property_sales_history: 3,456 records for BROWARD
```

## ✅ Verification

### Check in Supabase Dashboard

1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Table Editor
4. Check `florida_parcels` table
5. Filter by county = 'BROWARD'
6. You should see 25K+ records!

### Query Examples

```sql
-- Count properties per county
SELECT county, COUNT(*) as count
FROM florida_parcels
GROUP BY county
ORDER BY count DESC;

-- Recent sales
SELECT parcel_id, sale_date, sale_price, buyer_name
FROM property_sales_history
WHERE county = 'BROWARD'
ORDER BY sale_date DESC
LIMIT 10;

-- Property with highest value
SELECT parcel_id, owner_name, phy_addr1, city, just_value
FROM florida_parcels
WHERE county = 'BROWARD'
ORDER BY just_value DESC
LIMIT 10;
```

## 🤖 Enable Daily Automation

### Option 1: GitHub Actions (Recommended)

1. Add secrets to your GitHub repository:
   ```
   Settings → Secrets and variables → Actions → New repository secret

   Add these secrets:
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE_KEY
   - EMAIL_USERNAME
   - EMAIL_PASSWORD
   - ADMIN_EMAIL
   ```

2. The workflow is already configured in `.github/workflows/daily-property-update.yml`

3. It will run automatically at **2:00 AM EST every day**

4. Manual trigger:
   ```
   GitHub → Actions → Daily Property Update → Run workflow
   ```

### Option 2: Local Scheduler (Alternative)

```bash
# Run daily update manually
python scripts/daily_property_update.py

# Dry run (no database changes)
python scripts/daily_property_update.py --dry-run

# Force update all counties
python scripts/daily_property_update.py --force

# Specific county only
python scripts/daily_property_update.py --county MIAMI-DADE
```

## 📊 Monitoring

### View Update Status

```bash
# Check last update job
python -c "from supabase import create_client; from dotenv import load_dotenv; import os; load_dotenv('.env.mcp'); s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY')); print(s.table('data_update_jobs').select('*').order('created_at', desc=True).limit(5).execute())"
```

### Dashboard Metrics

Access in Supabase dashboard:
```sql
-- Daily update statistics
SELECT * FROM get_daily_update_stats(CURRENT_DATE);

-- County statistics
SELECT * FROM get_county_stats('BROWARD');

-- Recent changes
SELECT *
FROM property_change_log
WHERE change_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY detected_at DESC
LIMIT 100;
```

## 🔧 Troubleshooting

### Issue: Database connection failed

**Solution**:
1. Check `.env.mcp` has correct credentials
2. Verify IP is allowed in Supabase dashboard
3. Test: `python scripts/deploy_schema.py`

### Issue: Portal navigation fails

**Solution**:
1. Portal structure may have changed
2. Check screenshots in `test-screenshots/`
3. May need manual download from portal
4. Contact Florida DOR for API access

### Issue: File parsing errors

**Solution**:
1. File format may have changed
2. Check sample files manually
3. Update parser format specification in `parse_county_files.py`
4. Add more error handling

### Issue: Slow data loading

**Solution**:
1. Increase batch size in `load_county_data.py` (default: 1000)
2. Check database indexes are created
3. Use faster internet connection
4. Load during off-peak hours

## 📞 Getting Help

### Documentation
- **Complete Guide**: `DAILY_PROPERTY_UPDATE_SYSTEM.md`
- **Implementation Summary**: `PROPERTY_UPDATE_IMPLEMENTATION_SUMMARY.md`
- **AI Agent Spec**: `.claude/agents/property-update-monitor.md`

### Common Commands
```bash
# Test everything without changes
python scripts/daily_property_update.py --dry-run

# View logs
tail -f logs/daily_update_$(date +%Y-%m-%d).log

# Check database
python scripts/deploy_schema.py  # Redeploy if needed

# Manual county update
python scripts/download_county.py --county MIAMI-DADE
python scripts/parse_county_files.py --county MIAMI-DADE
python scripts/load_county_data.py --county MIAMI-DADE
```

## 🎯 Next Steps

Now that you have data for one county:

1. **Test on Frontend**:
   - Query properties in your web app
   - Verify search filters work
   - Check property details display correctly

2. **Add More Counties**:
   ```bash
   # Process priority counties
   for county in MIAMI-DADE PALM-BEACH HILLSBOROUGH ORANGE DUVAL; do
       python scripts/download_county.py --county $county
       python scripts/parse_county_files.py --county $county
       python scripts/load_county_data.py --county $county
   done
   ```

3. **Monitor Daily Updates**:
   - Check GitHub Actions runs
   - Review email notifications
   - Monitor change logs

4. **Optimize Performance**:
   - Add more database indexes if queries slow
   - Tune batch sizes
   - Implement caching

## 🎉 Success Criteria

You're all set when:
- ✅ Database schema deployed
- ✅ At least 1 county loaded (25K+ properties)
- ✅ Daily automation configured
- ✅ Monitoring working
- ✅ Frontend showing live data

**Congratulations!** Your daily property update system is now operational! 🚀

---

**Total Setup Time**: ~30 minutes
**Maintenance**: Automated (2:00 AM daily)
**Data Freshness**: Within 24 hours of Florida Revenue updates
**Coverage**: All 67 Florida counties available
