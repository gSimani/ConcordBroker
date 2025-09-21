# Railway Deployment Guide for ConcordBroker

## Problem Fixed

The Railway deployment was failing because:
1. Nixpacks couldn't detect the project structure (only saw README.md)
2. Missing proper configuration files
3. Incorrect start commands pointing to non-existent files

## Files Created/Updated

### 1. `nixpacks.toml` (NEW)
- Configures Nixpacks to detect Python + Node.js project
- Sets up proper build phases
- Specifies dependencies and start command

### 2. `railway.json` (UPDATED)
- Simplified configuration
- Fixed start command to use `property_live_api:app`
- Added health check endpoint

### 3. `Procfile` (NEW)
- Backup deployment configuration
- Simple web process definition

### 4. `requirements.txt` (UPDATED)
- Removed problematic `asyncio==3.4.3` (built-in module)
- Added `gunicorn` for production deployment
- Updated `uvicorn` to include standard extras

## Environment Variables Needed in Railway

You need to set these in your Railway dashboard:

```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
PORT=8000
RAILWAY_ENVIRONMENT=production
```

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "fix: Railway deployment configuration"
git push origin main
```

### 2. In Railway Dashboard
1. Go to your project: `ConcordBroker-Railway`
2. Connect to your GitHub repository
3. Set the environment variables above
4. Deploy from `main` branch

### 3. Verify Deployment
Once deployed, test:
- Health check: `https://your-railway-url.up.railway.app/health`
- API docs: `https://your-railway-url.up.railway.app/docs`

## Project Structure for Railway

Railway now correctly detects:
```
ConcordBroker/
├── nixpacks.toml         # Nixpacks configuration
├── railway.json          # Railway deployment config
├── Procfile             # Process definition
├── apps/
│   ├── api/
│   │   ├── requirements.txt
│   │   ├── property_live_api.py  # Main app
│   │   └── ...
│   └── web/
│       ├── package.json
│       └── ...
```

## Next Steps

1. **Commit and push** the configuration files
2. **Set environment variables** in Railway dashboard
3. **Trigger new deployment** from Railway dashboard
4. **Monitor build logs** to ensure success

The deployment should now work properly with the FastAPI application running on Railway!