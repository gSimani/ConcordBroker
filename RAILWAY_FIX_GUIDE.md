# Railway Deployment Fix Guide

## Current Issue
Railway build fails with: "Nixpacks was unable to generate a build plan" and only detects README.md

## Root Cause
Railway isn't detecting the full repository structure. It's only seeing the README.md file at the root level.

## Solution Steps

### 1. Run the Fix Script
```bash
deploy-railway-fix.bat
```

This script will:
- Check for required files
- Authenticate with Railway
- Guide you through manual configuration
- Trigger deployment

### 2. Manual Railway Dashboard Configuration

Go to your Railway dashboard: https://railway.app/project/05f5fbf4-f31c-4bdb-9022-3e987dd80fdb

#### A. Environment Variables (Variables Tab)
Add these environment variables:
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
PORT=8000
PYTHON_VERSION=3.10
NODE_ENV=production
```

#### B. Service Settings (Settings Tab)
- **Build Command**: Leave empty (let Nixpacks auto-detect)
- **Start Command**: Leave empty (uses railway.json)
- **Health Check Path**: `/health`
- **Region**: us-east4
- **Restart Policy**: ON_FAILURE
- **Max Retries**: 10

#### C. GitHub Connection (Settings Tab)
- **Repository**: gSimani/ConcordBroker
- **Branch**: main
- **Auto Deploy**: Enabled

#### D. Deploy Settings
- **Build Provider**: Nixpacks (should auto-select)
- **Root Directory**: `/` (leave as default)

### 3. Verify Files Exist in Repository

Make sure these files are committed and pushed:
```
ConcordBroker/
├── railway.json          ✓ (deployment config)
├── nixpacks.toml         ✓ (build config)
├── Procfile              ✓ (backup process definition)
├── apps/
│   └── api/
│       ├── requirements.txt     ✓ (Python dependencies)
│       └── ultimate_autocomplete_api.py  ✓ (main app)
```

### 4. Push Changes to GitHub
```bash
git add .
git commit -m "fix: Railway deployment configuration"
git push origin main
```

### 5. Trigger Deployment

Option A: From Railway Dashboard
- Go to Deployments tab
- Click "Trigger Deployment"

Option B: From Command Line
```bash
railway up --project 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb
```

### 6. Monitor Build Logs

Watch for these success indicators:
```
✓ Detecting Python application
✓ Installing Python 3.10
✓ Installing pip dependencies
✓ Starting uvicorn server
✓ Health check passing
```

## Common Issues & Fixes

### Issue: "Cannot find module ultimate_autocomplete_api"
**Fix**: The file exists at `apps/api/ultimate_autocomplete_api.py`. Make sure it's committed to Git.

### Issue: "Port binding failed"
**Fix**: Ensure PORT environment variable is set to 8000 in Railway.

### Issue: "Health check failing"
**Fix**: Verify the `/health` endpoint exists in your API.

### Issue: "Module not found" errors
**Fix**: Check `requirements.txt` has all dependencies and no version conflicts.

### Issue: "Permission denied"
**Fix**: Your Railway API token might not have deployment permissions. Generate a new token with full access.

## Alternative: Simple Python App

If issues persist, create a minimal test deployment:

1. Create `main.py` at root:
```python
from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Railway deployment working!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

2. Create minimal `requirements.txt` at root:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
```

3. Update railway.json:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python main.py"
  }
}
```

4. Push and deploy to test basic connectivity.

## Success Indicators

When deployment succeeds, you'll see:
- ✅ Build completed successfully
- ✅ Service is live
- ✅ Health checks passing
- ✅ Public URL generated (e.g., concordbroker-production.up.railway.app)

## Next Steps After Success

1. Test the API endpoints:
   - Health: https://your-railway-url.up.railway.app/health
   - Docs: https://your-railway-url.up.railway.app/docs
   - Autocomplete: https://your-railway-url.up.railway.app/api/autocomplete?q=test

2. Update frontend to use Railway backend URL

3. Set up monitoring and alerts

## Support

If deployment still fails after following this guide:
1. Check Railway Status: https://status.railway.app/
2. Review build logs in detail
3. Try deploying a minimal FastAPI app first
4. Contact Railway support with project ID: 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb