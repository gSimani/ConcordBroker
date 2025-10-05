# Complete Railway Setup Guide - Florida Data Ingestion

## Step-by-Step Manual Setup in Railway Dashboard

### Prerequisites
- Railway account logged in
- GitHub repository connected to Railway
- OpenAI API key ready

---

## Part 1: Create New Service

1. **Navigate to Project**
   - Go to: https://railway.app/project/05f5fbf4-f31c-4bdb-9022-3e987dd80fdb
   - Click **+ New** button (top right)

2. **Select Source**
   - Choose **GitHub Repo**
   - Select: `ConcordBroker` repository
   - Click **Add Service**

3. **Configure Root Directory**
   - In the new service settings, find **Root Directory**
   - Set to: `railway-deploy/florida-data-ingestion`
   - Save

4. **Rename Service**
   - Click on service name (default: "ConcordBroker")
   - Rename to: `Florida Data Ingestion`
   - Save

---

## Part 2: Configure Build & Deployment

The `railway.json` file has been created with these settings:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn florida_data_orchestrator:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300
  }
}
```

Railway will auto-detect this configuration. Verify in **Settings** → **Deploy**:
- ✅ Builder: NIXPACKS
- ✅ Start Command: `uvicorn florida_data_orchestrator:app --host 0.0.0.0 --port $PORT`
- ✅ Health Check Path: `/health`

---

## Part 3: Add Environment Variables

Go to **Variables** tab and add:

### Required Variables:
```bash
SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
```

```bash
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0
```

```bash
OPENAI_API_KEY=<paste_your_openai_api_key_here>
```

### Optional Variables:
```bash
SENTRY_DSN=<paste_your_sentry_dsn_here>
```

```bash
PORT=${{PORT}}
```
(Railway auto-provides this)

**How to add:**
1. Click **+ New Variable**
2. Enter variable name
3. Paste value
4. Click **Add**
5. Repeat for all variables

---

## Part 4: Setup Cron Job

1. **Navigate to Cron Settings**
   - Click **Settings** (gear icon)
   - Scroll to **Cron Jobs** section
   - Click **+ Add Cron Job**

2. **Configure Daily Sync**
   - **Schedule**: `0 8 * * *`
     - (Daily at 8:00 AM UTC / 3:00 AM ET)
   - **Command**: `python florida_data_orchestrator.py sync`
   - Click **Save**

**Cron Schedule Explained:**
- `0 8 * * *` = "At 8:00 AM UTC every day"
- Runs: Monday through Sunday
- EST equivalent: 3:00 AM Eastern

---

## Part 5: Generate Public Domain

1. **Navigate to Networking**
   - Click **Settings** → **Networking**
   - Find **Public Networking** section

2. **Generate Domain**
   - Click **Generate Domain**
   - Railway will create: `florida-data-ingestion-production.up.railway.app`
   - Copy this URL for testing

3. **Optional: Custom Domain**
   - If you want: `data-sync.concordbroker.com`
   - Click **+ Custom Domain**
   - Enter domain
   - Add CNAME record in your DNS:
     ```
     data-sync.concordbroker.com → florida-data-ingestion-production.up.railway.app
     ```

---

## Part 6: Deploy

1. **Trigger Deployment**
   - Railway auto-deploys when you create the service
   - If not deploying, click **Deploy** button (top right)

2. **Monitor Build Logs**
   - Click **View Logs** to see build progress
   - Expected build time: 2-4 minutes

3. **Wait for Health Check**
   - Service status will show **Deploying** → **Running**
   - Health check endpoint: `/health` must return 200 OK

---

## Part 7: Verify Deployment

### Test Health Endpoint
```bash
# Replace with your generated domain
curl https://florida-data-ingestion-production.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "supabase_connected": true,
  "storage_bucket_exists": true
}
```

### Check Ingestion Status
```bash
curl https://florida-data-ingestion-production.up.railway.app/ingest/status
```

**Expected Response:**
```json
{
  "total_runs": 0,
  "last_successful_run": null,
  "recent_runs": []
}
```

### Trigger Manual Sync (First Run)
```bash
curl -X POST https://florida-data-ingestion-production.up.railway.app/ingest/run
```

**Expected Response:**
```json
{
  "status": "started",
  "run_id": 1,
  "message": "Ingestion job started in background"
}
```

### View County Coverage
```bash
curl https://florida-data-ingestion-production.up.railway.app/coverage/counties
```

---

## Part 8: Restore Main API Service

Your main ConcordBroker API may have been overwritten. Restore it:

1. **Go to ConcordBroker Service**
   - Find the original service in your Railway project
   - Click on it

2. **Fix Root Directory**
   - Settings → **Root Directory**
   - Change to: `apps/api`
   - Save

3. **Fix Start Command**
   - Settings → Deploy → **Start Command**
   - Change to: `python production_property_api.py`
   - Save

4. **Redeploy**
   - Click **Redeploy** button
   - Verify it's running at: https://api.concordbroker.com

---

## Verification Checklist

- [ ] Florida Data Ingestion service created
- [ ] Root directory set to `railway-deploy/florida-data-ingestion`
- [ ] All environment variables added (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY)
- [ ] Cron job configured (`0 8 * * *`)
- [ ] Public domain generated
- [ ] Service deployed successfully
- [ ] Health check returns 200 OK
- [ ] Manual sync test completed
- [ ] Main API service restored and working

---

## Monitoring

### View Logs
```bash
# In Railway Dashboard
Click service → View Logs
```

### Check Cron Job Runs
- Go to service → **Cron** tab
- View execution history
- Check last run timestamp

### Monitor Ingestion Runs
```sql
-- Run in Supabase SQL Editor
SELECT * FROM recent_ingestion_activity LIMIT 10;
```

### View County Coverage
```sql
-- Run in Supabase SQL Editor
SELECT * FROM get_county_coverage() ORDER BY total_parcels DESC;
```

---

## Troubleshooting

### Build Fails
**Error**: `pip: command not found`
- **Fix**: Ensure `railway.json` exists in root directory
- Delete `nixpacks.toml` if present

### Health Check Fails
**Error**: Service won't start
- Check environment variables are set correctly
- View logs for errors
- Verify Supabase credentials

### Cron Job Not Running
**Error**: No executions shown
- Verify schedule syntax: `0 8 * * *`
- Check service is running
- View logs at scheduled time

### Main API Broken
**Error**: 404 or wrong app running
- Restore root directory to `apps/api`
- Fix start command to `python production_property_api.py`
- Redeploy service

---

## Expected Monthly Costs

- **Florida Data Ingestion Service**: $5-10/month (Pro plan)
- **Storage**: ~500 MB → Free tier
- **Build minutes**: ~30 minutes/month → Free tier
- **Total Railway**: $5-10/month

Plus existing costs:
- Supabase Pro: $25/month
- OpenAI API: $20-50/month

**Total System**: ~$50-85/month

---

## Next Steps After Deployment

1. **Monitor First Sync**
   - Wait 24 hours for first cron run
   - Check logs at 8:00 AM UTC (3:00 AM ET)

2. **Verify Data Quality**
   ```sql
   SELECT * FROM data_quality_dashboard;
   ```

3. **Setup Alerts** (optional)
   - Configure Sentry for error monitoring
   - Add email notifications for failed runs

4. **Expand Coverage**
   - Add remaining county PA URLs to orchestrator
   - Implement FGIO geometry sync
   - Add NAV (Non-Ad Valorem) processing

---

## Support

**Railway Dashboard**: https://railway.app/project/05f5fbf4-f31c-4bdb-9022-3e987dd80fdb

**Documentation**:
- Railway: https://docs.railway.app
- Supabase: https://supabase.com/docs
- Florida DOR: https://floridarevenue.com/property/dataportal

**Files Created**:
- `florida_data_orchestrator.py` - Main orchestrator
- `railway.json` - Deployment config
- `railway.toml` - Cron configuration
- `requirements.txt` - Python dependencies
- `.env.example` - Environment template
- `README.md` - Project documentation
