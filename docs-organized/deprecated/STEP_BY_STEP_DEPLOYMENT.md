# 🚀 Step-by-Step Railway Deployment Guide

## ✅ Prerequisites (Already Complete!)

- ✅ Railway CLI installed (v4.5.3)
- ✅ Logged in as GuySimani@gmail.com
- ✅ Local proof-of-concept working (964 properties indexed)
- ✅ All deployment files ready

---

## 📋 Step-by-Step Instructions

### STEP 1: Open Terminal
**Action**: Open a new Command Prompt or PowerShell window

**Command**:
```bash
cd C:\Users\gsima\Documents\MyProject\ConcordBroker\railway-deploy
```

**Expected Output**: You should be in the railway-deploy directory

---

### STEP 2: Initialize Railway Project
**Action**: Create a new Railway project

**Command**:
```bash
railway init
```

**What Will Happen**:
- Railway will ask: "Project Name?"
- **Type**: `concordbroker-search` (then press Enter)
- Railway will ask: "Select a workspace"
- **Select**: `gSimani Railway` (should be pre-selected)

**Expected Output**:
```
✔ Project created: concordbroker-search
```

---

### STEP 3: Deploy Meilisearch Service
**Action**: Upload Meilisearch container to Railway

**Command**:
```bash
railway up --dockerfile Dockerfile.meilisearch
```

**What Will Happen**:
- Railway will build the Docker image
- Upload to Railway servers
- Takes 2-3 minutes

**Expected Output**:
```
✔ Build completed
✔ Deployment live
Service: <service-id>
```

---

### STEP 4: Set Meilisearch Environment Variables
**Action**: Configure Meilisearch with security keys

**Commands** (run one at a time):
```bash
railway variables set MEILI_MASTER_KEY=concordbroker-meili-railway-prod-key-2025
```
**Expected**: `✔ Variable set`

```bash
railway variables set MEILI_ENV=production
```
**Expected**: `✔ Variable set`

```bash
railway variables set MEILI_NO_ANALYTICS=true
```
**Expected**: `✔ Variable set`

---

### STEP 5: Generate Public URL for Meilisearch
**Action**: Get the public URL for your Meilisearch service

**Command**:
```bash
railway domain
```

**Expected Output**:
```
✔ Domain created
https://concordbroker-meilisearch-production.up.railway.app
```

**IMPORTANT**: Copy this URL! You'll need it in Step 8.

**Write it here**: _________________________________

---

### STEP 6: Test Meilisearch is Running
**Action**: Verify Meilisearch deployed successfully

**Command** (replace `<YOUR-MEILISEARCH-URL>` with URL from Step 5):
```bash
curl https://<YOUR-MEILISEARCH-URL>/health
```

**Expected Output**:
```json
{"status":"available"}
```

**If you see this**: ✅ Meilisearch is working!
**If you see an error**: Wait 1-2 minutes for deployment to complete, then try again

---

### STEP 7: Create Search API Service
**Action**: Add a second service to the same project

**Command**:
```bash
railway service create search-api
```

**Expected Output**:
```
✔ Service created: search-api
```

---

### STEP 8: Deploy Search API
**Action**: Upload Search API container to Railway

**Command**:
```bash
railway up --dockerfile Dockerfile.search-api --service search-api
```

**What Will Happen**:
- Railway will build the FastAPI Docker image
- Upload to Railway servers
- Takes 2-3 minutes

**Expected Output**:
```
✔ Build completed
✔ Deployment live
Service: search-api
```

---

### STEP 9: Set Search API Environment Variables
**Action**: Configure Search API to connect to Meilisearch and Supabase

**Commands** (run one at a time, replace `<YOUR-MEILISEARCH-URL>`):

```bash
railway variables set MEILISEARCH_URL=https://<YOUR-MEILISEARCH-URL> --service search-api
```
**Example**: `railway variables set MEILISEARCH_URL=https://concordbroker-meilisearch-production.up.railway.app --service search-api`

**Expected**: `✔ Variable set`

```bash
railway variables set MEILISEARCH_KEY=concordbroker-meili-railway-prod-key-2025 --service search-api
```
**Expected**: `✔ Variable set`

```bash
railway variables set SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co --service search-api
```
**Expected**: `✔ Variable set`

```bash
railway variables set SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0 --service search-api
```
**Expected**: `✔ Variable set`

---

### STEP 10: Generate Public URL for Search API
**Action**: Get the public URL for your Search API service

**Command**:
```bash
railway domain --service search-api
```

**Expected Output**:
```
✔ Domain created
https://concordbroker-search-api-production.up.railway.app
```

**IMPORTANT**: Copy this URL! You'll need it for frontend integration.

**Write it here**: _________________________________

---

### STEP 11: Test Search API is Running
**Action**: Verify Search API deployed successfully

**Command** (replace `<YOUR-SEARCH-API-URL>` with URL from Step 10):
```bash
curl https://<YOUR-SEARCH-API-URL>/health
```

**Expected Output**:
```json
{"status":"healthy"}
```

**If you see this**: ✅ Search API is working!

---

### STEP 12: View Your Deployment
**Action**: Check Railway dashboard to see both services running

**Command**:
```bash
railway status
```

**Expected Output**:
```
Project: concordbroker-search
Services:
  - meilisearch: https://<meilisearch-url>
  - search-api: https://<search-api-url>
```

**Or visit**: https://railway.app/dashboard

---

## 🎉 Deployment Complete!

You now have:
- ✅ Meilisearch running on Railway
- ✅ Search API running on Railway
- ✅ Both services publicly accessible
- ✅ All environment variables configured

---

## 📝 What You Need for Next Steps

**Save these URLs**:
1. Meilisearch URL: _________________________________
2. Search API URL: _________________________________

---

## ⏭️ Next Steps (After Deployment)

### A. Index Properties to Railway (2-3 minutes)

1. Open `apps/api/railway_indexer.py`
2. Change line 12:
   ```python
   MEILI_URL = 'https://<YOUR-MEILISEARCH-URL>'
   ```
3. Save the file
4. Run:
   ```bash
   cd C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\api
   python railway_indexer.py 100000
   ```
5. Wait for indexing to complete (2-3 minutes)

**Expected Output**:
```
================================================================================
RAILWAY PRODUCTION INDEXER
================================================================================
Target: 100,000 properties
...
Documents indexed: 100,000
================================================================================
```

---

### B. Update Frontend (5 minutes)

1. Open `apps/web/src/pages/properties/PropertySearch.tsx`
2. Add at the top (after imports):
   ```typescript
   const SEARCH_API_URL = 'https://<YOUR-SEARCH-API-URL>';
   ```
3. Find the `searchProperties` function (around line 750-800)
4. Replace the Supabase count query with:
   ```typescript
   // NEW: Meilisearch via Railway
   const getPropertyCount = async (filters: any) => {
     const meilisearchFilters: any = {};

     if (filters.buildingSqFtMin || filters.buildingSqFtMax) {
       meilisearchFilters.tot_lvg_area = {
         ...(filters.buildingSqFtMin && { gte: filters.buildingSqFtMin }),
         ...(filters.buildingSqFtMax && { lte: filters.buildingSqFtMax })
       };
     }

     const response = await fetch(`${SEARCH_API_URL}/search/count`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ filters: meilisearchFilters })
     });

     const { count } = await response.json();
     return count;
   };

   // Use it:
   const count = await getPropertyCount(filters);
   setTotalCount(count);
   ```
5. Save the file

---

### C. Test Everything (2 minutes)

1. Start dev server:
   ```bash
   cd C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web
   npm run dev
   ```
2. Open http://localhost:5173/properties
3. Open Filters panel
4. Set Building SqFt: Min=10000, Max=20000
5. Click "Apply Filters"
6. **Expected**: Shows 964 results (not 7.3M!)
7. **Success**: Bug is fixed! 🎉

---

## 🆘 Troubleshooting

### Issue: "Command not found: railway"
**Solution**: Railway CLI not in PATH
```bash
npm install -g @railway/cli
```

### Issue: "Unauthorized"
**Solution**: Login again
```bash
railway login
```

### Issue: "Build failed"
**Solution**: Check Docker files exist
```bash
dir Dockerfile.meilisearch
dir Dockerfile.search-api
```

### Issue: "Service not responding"
**Solution**: Wait 2-3 minutes for deployment, then check:
```bash
railway logs
```

### Issue: "Variables not set"
**Solution**: List current variables:
```bash
railway variables
```

---

## 📊 Expected Costs

**Railway Pro**: $10-15/month
- Meilisearch: $5-8/month
- Search API: $5-7/month

Monitor usage at: https://railway.app/dashboard

---

## ✅ Checklist

Use this to track your progress:

- [ ] Step 1: Open terminal in railway-deploy directory
- [ ] Step 2: Initialize Railway project
- [ ] Step 3: Deploy Meilisearch
- [ ] Step 4: Set Meilisearch environment variables
- [ ] Step 5: Generate Meilisearch public URL
- [ ] Step 6: Test Meilisearch is running
- [ ] Step 7: Create Search API service
- [ ] Step 8: Deploy Search API
- [ ] Step 9: Set Search API environment variables
- [ ] Step 10: Generate Search API public URL
- [ ] Step 11: Test Search API is running
- [ ] Step 12: View deployment status

**After deployment**:
- [ ] A: Index properties to Railway
- [ ] B: Update frontend code
- [ ] C: Test Building SqFt filter

---

## 🎯 Success Criteria

When complete, you should have:
- ✅ Two services running on Railway
- ✅ Public URLs for both services
- ✅ Health checks passing
- ✅ 100K properties indexed
- ✅ Frontend showing accurate counts (964, not 7.3M!)

---

**Ready to start? Begin with Step 1! Open a new terminal.**
