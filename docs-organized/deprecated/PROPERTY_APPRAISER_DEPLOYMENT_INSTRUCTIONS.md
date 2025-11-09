# Property Appraiser Database Deployment Instructions

## 🚨 IMMEDIATE ACTION REQUIRED

The Property Appraiser database infrastructure is fully prepared but the tables need to be created in Supabase before data can be loaded.

## Step 1: Deploy Database Tables (REQUIRED)

### Option A: Via Supabase Dashboard (Recommended)

1. **Open Supabase Dashboard**
   - Go to: https://app.supabase.com
   - Login to your project

2. **Navigate to SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New query" button

3. **Execute the Deployment Script**
   - Open file: `deployment/DEPLOY_ALL_PROPERTY_APPRAISER_TABLES.sql`
   - Copy the entire contents
   - Paste into the SQL Editor
   - Click "Run" button

4. **Verify Success**
   - You should see "Success. No rows returned" message
   - Check the "Table Editor" to confirm tables exist

### Option B: Via Command Line (If SQL execution is enabled)

```bash
# Set environment variable to enable SQL execution
export SUPABASE_ENABLE_SQL=true

# Run automated deployment
python execute_sql_deployment.py
```

## Step 2: Verify Table Creation

Run the verification script to ensure all tables were created:

```bash
python test_property_appraiser_tables.py
```

Expected output:
```
[OK] florida_parcels      Exists: 1 Writable: Yes
[OK] nav_assessments      Exists: 1 Writable: Yes
[OK] nap_characteristics  Exists: 1 Writable: Yes
[OK] sdf_sales            Exists: 1 Writable: Yes
```

## Step 3: Load Sample Data

Once tables are verified, load BROWARD county sample data:

```bash
python load_broward_sample_data.py
```

The script will:
- Load data from `TEMP\DATABASE PROPERTY APP\BROWARD\NAL\NAL16P202501.csv`
- Insert 100 sample records
- Verify the data was loaded correctly

## Step 4: Test the System

### Check Data in Supabase
1. Go to Table Editor in Supabase Dashboard
2. Select `florida_parcels` table
3. You should see 100+ records from BROWARD county

### Test API Access
```bash
curl -X GET "http://localhost:3001/api/supabase/florida_parcels?limit=5" \
  -H "x-api-key: concordbroker-mcp-key" \
  -H "Content-Type: application/json"
```

## Step 5: Load Full Dataset (Optional)

To load all 67 Florida counties (~9.7M properties):

```bash
# Apply timeout configurations first
# In Supabase SQL Editor, run:
ALTER ROLE authenticator SET statement_timeout = 0;
ALTER ROLE anon SET statement_timeout = 0;
ALTER ROLE service_role SET statement_timeout = 0;

# Then run the full loader
python property_appraiser_fast_loader.py --counties all --parallel 4
```

## Files Created

### SQL Deployment Files
- `deployment/DEPLOY_ALL_PROPERTY_APPRAISER_TABLES.sql` - Complete deployment script
- `deployment/create_florida_parcels_schema.sql` - Main table schema
- `deployment/CREATE_INDEXES.sql` - Performance indexes
- `deployment/nav_assessments.sql` - NAV table schema
- `deployment/nap_characteristics.sql` - NAP table schema
- `deployment/sdf_sales.sql` - SDF table schema

### Python Scripts
- `deploy_property_appraiser_database.py` - Deployment preparation
- `test_property_appraiser_tables.py` - Table verification
- `load_broward_sample_data.py` - Sample data loader
- `property_appraiser_postgrest_audit.py` - Database audit tool

### Documentation
- `PROPERTY_APPRAISER_AUDIT_COMPLETE.md` - Full audit report
- `property_appraiser_audit_report.json` - Audit results
- `deployment/table_test_results.json` - Table test results

## Data Available

Your local system has BROWARD county data ready:
- **NAL File**: `TEMP\DATABASE PROPERTY APP\BROWARD\NAL\NAL16P202501.csv`
- **NAP Files**: In `TEMP\DATABASE PROPERTY APP\BROWARD\NAP\`
- **NAV Files**: In `TEMP\DATABASE PROPERTY APP\BROWARD\NAV\`
- **SDF Files**: In `TEMP\DATABASE PROPERTY APP\BROWARD\SDF\`

## Monitoring

Once deployed, monitor the system:

```sql
-- Check record counts
SELECT
    'florida_parcels' as table_name,
    COUNT(*) as record_count
FROM florida_parcels
UNION ALL
SELECT
    'nav_assessments',
    COUNT(*)
FROM nav_assessments;
```

## Troubleshooting

### If tables don't create:
1. Check for SQL syntax errors in the output
2. Ensure you have proper permissions in Supabase
3. Try creating one table at a time

### If data doesn't load:
1. Verify tables exist: `python test_property_appraiser_tables.py`
2. Check file path: `ls "TEMP/DATABASE PROPERTY APP/BROWARD/NAL"`
3. Verify credentials: Check `.env.mcp` has `SUPABASE_SERVICE_ROLE_KEY`

### If API access fails:
1. Check MCP Server: `curl http://localhost:3001/health`
2. Verify API key matches: `concordbroker-mcp-key`
3. Check Supabase connection in MCP logs

## Next Steps After Deployment

1. ✅ Tables created in Supabase
2. ✅ Sample data loaded successfully
3. ⬜ Configure daily update automation
4. ⬜ Set up monitoring alerts
5. ⬜ Load remaining 66 counties
6. ⬜ Enable frontend property search

## Support

For issues:
1. Check `deployment/table_test_results.json` for detailed errors
2. Review Supabase logs in Dashboard > Logs
3. Check MCP Server logs: `tail -f mcp-server/claude-init.log`

---

**Status**: Ready for deployment - awaiting SQL execution in Supabase Dashboard