# 🚂 Railway Orchestrator Deployment Guide

**Purpose**: Deploy the 24/7 cloud orchestrator for autonomous agent operation

**Cost**: $5/month
**Deployment Time**: 15-20 minutes

---

## Prerequisites

✅ Railway CLI installed (v4.5.3 detected)
✅ Railway account created
✅ Supabase database credentials
✅ Docker container ready (`Dockerfile`)

---

## Step 1: Login to Railway (Manual)

Since Railway login requires a browser, please complete this step manually:

```bash
# Open a new terminal window and run:
cd "C:\Users\gsima\Documents\MyProject\ConcordBroker\railway-orchestrator"
railway login
```

This will:
1. Open your browser
2. Ask you to authorize the CLI
3. Return you to the terminal when complete

---

## Step 2: Link to Railway Project (Choose One)

### Option A: Create New Project
```bash
railway init
# Follow prompts to create a new project named "concordbroker-orchestrator"
```

### Option B: Link to Existing Project
```bash
# Use your existing project ID from .env.mcp
railway link 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb
```

---

## Step 3: Set Environment Variables

Run these commands to configure the orchestrator:

```bash
# Supabase connection
railway variables --set SUPABASE_HOST=aws-1-us-east-1.pooler.supabase.com
railway variables --set SUPABASE_DB=postgres
railway variables --set SUPABASE_USER=postgres.pmispwtdngkcmsrsjwbp
railway variables --set SUPABASE_PASSWORD="West@Boca613!"
railway variables --set SUPABASE_PORT=5432

# Connection pooling
railway variables --set DB_POOL_MIN=5
railway variables --set DB_POOL_MAX=20

# Python environment
railway variables --set PYTHONUNBUFFERED=1
```

---

## Step 4: Deploy the Container

```bash
railway up
```

This will:
1. Build the Docker container
2. Push it to Railway
3. Start the orchestrator service
4. Return a deployment URL

**Expected output**:
```
Building...
✓ Build successful
Deploying...
✓ Deployment successful
Service URL: https://concordbroker-orchestrator-production.up.railway.app
```

---

## Step 5: Verify Deployment

### Check Deployment Status
```bash
railway status
```

Expected: `Status: ACTIVE`

### View Logs
```bash
railway logs
```

**Look for**:
```
🚀 RAILWAY CLOUD ORCHESTRATOR STARTING
✅ Connected to Supabase
✅ Registered in agent_registry
⏱️  Heartbeat sent (30s interval)
📊 System health: online=8, stale=0, offline=0
```

### Test Health Endpoint
```bash
curl https://your-deployment-url.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "uptime": "5m 23s",
  "last_heartbeat": "2025-11-01T20:50:00Z"
}
```

---

## Step 6: Monitor the Orchestrator

### Real-Time Logs
```bash
railway logs --follow
```

### Check Database Registry
Connect to Supabase and run:
```sql
SELECT
    agent_id,
    agent_type,
    status,
    last_heartbeat,
    AGE(NOW(), last_heartbeat) as time_since_heartbeat
FROM agent_registry
WHERE agent_type = 'orchestrator'
ORDER BY last_heartbeat DESC;
```

Expected:
- Status: `active`
- Heartbeat: < 1 minute ago

---

## Troubleshooting

### Issue: Build Fails

**Check Dockerfile**:
```bash
# Test build locally
docker build -t railway-orchestrator .
```

### Issue: Connection Errors

**Verify environment variables**:
```bash
railway variables
```

Make sure all SUPABASE_* variables are set correctly.

### Issue: Service Won't Start

**Check logs for errors**:
```bash
railway logs --tail 100
```

Common issues:
- Missing environment variables
- Incorrect database credentials
- Port conflicts (use Railway's PORT env var)

### Issue: Health Check Fails

**Check health_check.py**:
```bash
# Test locally
python health_check.py
```

Make sure the orchestrator registered successfully in the database.

---

## Configuration Files

### Dockerfile
- ✅ Multi-stage build for efficiency
- ✅ Health check configured (30s interval)
- ✅ Auto-restart on failure

### orchestrator.py
- ✅ 24/7 monitoring loop
- ✅ Heartbeat every 30s
- ✅ System health checks every 60s
- ✅ Data freshness alerts

### railway.json
- ✅ Builder: DOCKERFILE
- ✅ Restart policy: ON_FAILURE
- ✅ Max retries: 10

---

## Expected Behavior

### On Startup:
1. Container builds (~2-3 minutes)
2. Connects to Supabase
3. Registers in `agent_registry`
4. Sends initial heartbeat
5. Starts monitoring loop

### During Operation:
- Heartbeat every 30 seconds
- System health check every 60 seconds
- Monitors 11 agents:
  - property_data_agent
  - sales_history_agent
  - sunbiz_agent
  - foreclosure_agent
  - tax_deed_agent
  - permit_agent
  - market_analysis_agent
  - investment_agent
  - data_quality_agent
  - notification_agent
  - orchestrator (self)

### Alerts Generated:
- ⚠️ Agent offline (no heartbeat >5 minutes)
- ⚠️ Data stale (>7 days old)
- ⚠️ System health degraded
- ⚠️ Database connection lost

---

## Cost & Performance

### Railway Free Tier:
- ❌ Not suitable (needs 24/7 operation)

### Railway Hobby Plan ($5/month):
- ✅ 500 hours/month (more than enough for 24/7)
- ✅ 512MB RAM (sufficient for orchestrator)
- ✅ 1GB disk (plenty for logs)
- ✅ Auto-sleep disabled
- ✅ Custom domain support

### Resource Usage:
- **CPU**: <5% (monitoring only, no heavy processing)
- **Memory**: ~50-100MB (Python + psycopg2)
- **Network**: <1GB/month (database queries only)
- **Disk**: <100MB (logs rotate)

---

## Maintenance

### Update Deployment:
```bash
# Make changes to code
git add .
git commit -m "Update orchestrator"

# Redeploy
cd railway-orchestrator
railway up
```

### Restart Service:
```bash
railway restart
```

### View Metrics:
```bash
railway metrics
```

### Delete Service:
```bash
railway down
```

---

## Success Criteria

✅ Deployment status: ACTIVE
✅ Health check: Passing
✅ Heartbeat: < 1 minute old
✅ Logs: No errors
✅ Database: Agent registered
✅ Monitoring: All 11 agents tracked
✅ Uptime: >99%

---

## Next Steps After Deployment

1. **Monitor for 24 hours** to ensure stability
2. **Set up alerts** in Railway dashboard
3. **Review logs** for any issues
4. **Add GitHub Actions** health check workflow
5. **Implement data update automation**

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Status: https://status.railway.app
- Project Dashboard: https://railway.app/project/05f5fbf4-f31c-4bdb-9022-3e987dd80fdb

---

**Deployment Guide Version**: 1.0
**Last Updated**: November 1, 2025
**Created by**: Claude Code
