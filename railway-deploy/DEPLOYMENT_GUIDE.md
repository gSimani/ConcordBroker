# ConcordBroker Railway Deployment Guide

## Overview
ConcordBroker uses Railway for hosting backend services. This guide documents the complete deployment process for both services.

## Services Architecture

### 1. Meilisearch Service
- **Purpose**: High-performance search engine
- **URL**: https://meilisearch-concordbrokerproduction.up.railway.app
- **Builder**: Dockerfile
- **Port**: Dynamic (Railway provides `PORT` variable)

### 2. ConcordBroker API Service
- **Purpose**: FastAPI backend for property data
- **URL**: https://concordbroker.com
- **Builder**: Nixpacks (auto-detects Python)
- **Port**: Dynamic (Railway provides `PORT` variable)

## Prerequisites

### Required Tools
```bash
# Railway CLI v4.10.0 or higher
npm install -g @railway/cli

# Verify installation
railway version
```

### Required Files
```
railway-deploy/
├── Dockerfile.meilisearch      # Meilisearch container
├── production_property_api.py  # FastAPI application
├── requirements.txt            # Python dependencies
├── railway.json                # Railway configuration
└── .env.railway                # Environment variables (not in git)
```

## Project Setup

### 1. Link to Railway Project
```bash
cd railway-deploy

# Link to existing project
railway link

# Select from the list:
# ✓ ConcordBroker-Railway
# ✓ concordbrokerproduction (environment)
```

### 2. Verify Project Status
```bash
railway status

# Should show:
# Project: ConcordBroker-Railway
# Environment: concordbrokerproduction
```

## Deployment Process

### Service 1: Meilisearch

#### Step 1: Create Meilisearch Service
```bash
# Add new service
railway add

# When prompted:
# ? Create a new service?
#   ✓ Empty service
#   Name: meilisearch
```

#### Step 2: Link CLI to Meilisearch Service
```bash
railway service meilisearch
```

#### Step 3: Set Environment Variables
```bash
railway variables --set MEILI_MASTER_KEY=concordbroker-meili-railway-prod-key-2025
railway variables --set MEILI_ENV=production
railway variables --set MEILI_NO_ANALYTICS=true
```

#### Step 4: Configure Railway for Docker Build
Create `railway.json` for Meilisearch:
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.meilisearch"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE"
  }
}
```

#### Step 5: Deploy
```bash
railway up

# Wait for build to complete
# Railway will automatically assign a domain
```

#### Step 6: Verify Deployment
```bash
# Health check (no auth required)
curl https://meilisearch-concordbrokerproduction.up.railway.app/health

# Expected response:
# {"status":"available"}

# Stats (requires auth)
curl -H "Authorization: Bearer concordbroker-meili-railway-prod-key-2025" \
  https://meilisearch-concordbrokerproduction.up.railway.app/stats
```

### Service 2: ConcordBroker API

#### Step 1: Switch to API Service
```bash
railway service ConcordBroker
```

#### Step 2: Set Environment Variables
```bash
railway variables --set SUPABASE_URL=your_supabase_url
railway variables --set SUPABASE_ANON_KEY=your_anon_key
railway variables --set SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
railway variables --set REDIS_URL=your_redis_url
railway variables --set MEILISEARCH_URL=https://meilisearch-concordbrokerproduction.up.railway.app
railway variables --set MEILISEARCH_KEY=concordbroker-meili-railway-prod-key-2025
```

#### Step 3: Configure Railway for Nixpacks
Create `railway.json` for API:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn production_property_api:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/dataset/summary",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

#### Step 4: Verify Python Dependencies
Check `requirements.txt`:
```txt
fastapi==0.104.1
uvicorn==0.24.0
supabase==2.0.2
redis==5.0.1
python-dotenv==1.0.0
pydantic==2.5.0
httpx==0.24.1  # CRITICAL: Must be <0.25.0 for supabase compatibility
```

#### Step 5: Deploy
```bash
railway up

# Nixpacks will auto-detect Python and install dependencies
# Build time: ~90-120 seconds
```

#### Step 6: Verify Deployment
```bash
# Health check
curl https://concordbroker.com/api/dataset/summary

# Expected response: JSON with dataset information
# Status code: 200 OK
```

## Common Issues and Solutions

### Issue 1: Port Conflicts
**Error**: Container fails to start, port-related errors

**Solution**: Ensure Dockerfile and start commands use Railway's `PORT` variable:
```dockerfile
# Meilisearch Dockerfile
RUN printf '#!/bin/sh\nexport MEILI_HTTP_ADDR="0.0.0.0:${PORT:-7700}"\nexec meilisearch\n' > /start.sh
CMD ["/bin/sh", "/start.sh"]
```

```json
// railway.json for API
{
  "deploy": {
    "startCommand": "uvicorn production_property_api:app --host 0.0.0.0 --port $PORT"
  }
}
```

### Issue 2: Python Dependency Conflicts
**Error**: `Cannot install httpx==0.25.2 because supabase 2.0.2 depends on httpx<0.25.0`

**Solution**: Downgrade httpx in `requirements.txt`:
```txt
httpx==0.24.1  # Changed from 0.25.2
```

### Issue 3: Nixpacks Not Detecting Python
**Error**: `pip: command not found` or `uvicorn: command not found`

**Root Cause**: Custom build configurations override Nixpacks auto-detection

**Solution**:
1. Remove any `nixpacks.toml` files
2. Remove custom `buildCommand` from `railway.json`
3. Let Nixpacks auto-detect Python:
```json
{
  "build": {
    "builder": "NIXPACKS"
  }
}
```

### Issue 4: Wrong railway.json for Service
**Error**: Meilisearch service trying to build Python, or vice versa

**Solution**: Each service needs its own configuration. When switching services:
```bash
# Before deploying, verify correct railway.json exists
cat railway.json

# For Meilisearch:
# "builder": "DOCKERFILE"
# "dockerfilePath": "Dockerfile.meilisearch"

# For API:
# "builder": "NIXPACKS"
```

### Issue 5: Health Check Failures
**Error**: Deployment succeeds but Railway shows unhealthy

**Solution**: Verify health check path is accessible:
```json
{
  "deploy": {
    "healthcheckPath": "/api/dataset/summary"  // Must return 200 OK
  }
}
```

Test locally first:
```bash
uvicorn production_property_api:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/api/dataset/summary
```

## Railway CLI Command Reference (v4.10.0+)

### Project Management
```bash
railway login                         # Login to Railway
railway link                          # Link to existing project
railway unlink                        # Unlink from project
railway status                        # View project status
railway service [name]                # Switch to specific service
```

### Deployment
```bash
railway up                            # Deploy current directory
railway up -d                         # Deploy with detached mode
railway redeploy                      # Redeploy current deployment
```

### Environment Variables
```bash
railway variables                     # List all variables
railway variables --set KEY=VALUE     # Set a variable (NEW SYNTAX)
railway variables --unset KEY         # Remove a variable
```

### Logs and Monitoring
```bash
railway logs                          # View logs for current service
railway logs -s [service]             # View logs for specific service
railway logs --follow                 # Stream logs in real-time
```

### Service Management
```bash
railway add                           # Add new service
railway service list                  # List all services
railway service [name]                # Switch to service
railway delete                        # Delete current service
```

## Best Practices

### 1. Builder Selection
- **Use Dockerfile when**:
  - You need custom system dependencies
  - Using official images (e.g., Meilisearch)
  - Specific build requirements

- **Use Nixpacks when**:
  - Standard Python/Node.js/Go applications
  - Want automatic dependency detection
  - Prefer simplified configuration

### 2. Environment Variables
- Never commit `.env` files to git
- Use Railway's built-in secrets management
- Reference secrets in code via `os.getenv()`
- Set production values via `railway variables --set`

### 3. Health Checks
- Always implement a health check endpoint
- Keep it lightweight (simple status check)
- Return 200 OK for healthy, 5xx for unhealthy
- Test locally before deploying

### 4. Port Configuration
- Always use Railway's `PORT` environment variable
- Never hardcode ports in production code
- Provide fallback for local development:
  ```python
  PORT = int(os.getenv("PORT", 8000))
  ```

### 5. Deployment Verification
After every deployment:
```bash
# 1. Check Railway dashboard
railway status

# 2. Test health endpoint
curl https://your-service.railway.app/health

# 3. View recent logs
railway logs --tail 50

# 4. Monitor for errors
railway logs --follow
```

## Rollback Procedures

### Quick Rollback
```bash
# View recent deployments
railway logs

# Redeploy previous working version
railway redeploy [deployment-id]
```

### Manual Rollback
1. Check out previous working commit
2. Deploy from that commit:
```bash
git checkout [working-commit-hash]
railway up
```

## Monitoring and Maintenance

### Daily Checks
```bash
# Check service health
curl https://concordbroker.com/api/dataset/summary
curl https://meilisearch-concordbrokerproduction.up.railway.app/health

# View error logs
railway logs -s ConcordBroker | grep ERROR
railway logs -s meilisearch | grep ERROR
```

### Weekly Maintenance
- Review Railway usage metrics
- Check for dependency updates
- Monitor error rates in logs
- Verify backup procedures

### Monthly Tasks
- Update dependencies (test locally first)
- Review and optimize resource usage
- Update documentation with any changes
- Security audit of environment variables

## Emergency Procedures

### Service Down
1. Check Railway dashboard for status
2. View logs: `railway logs --follow`
3. Check environment variables: `railway variables`
4. Verify domain configuration
5. Contact Railway support if infrastructure issue

### Deployment Failed
1. Check build logs in Railway dashboard
2. Verify all environment variables are set
3. Test build locally first
4. Check for dependency conflicts
5. Rollback to last working deployment

### Database Connection Issues
1. Verify Supabase URL and keys
2. Check network connectivity
3. Review connection pool settings
4. Check Supabase status page
5. Verify firewall/security rules

## Support and Resources

### Railway Resources
- Dashboard: https://railway.com/project/05f5fbf4-f31c-4bdb-9022-3e987dd80fdb
- Documentation: https://docs.railway.com
- Status: https://status.railway.com
- Discord: https://discord.gg/railway

### Project Resources
- Deployment Status: `railway-deploy/DEPLOYMENT_STATUS.txt`
- Meilisearch Info: `railway-deploy/MEILISEARCH_URL.txt`
- Local Setup: `start-session.bat`

### Getting Help
1. Check this guide first
2. Review Railway logs: `railway logs`
3. Check Railway dashboard for build errors
4. Consult Railway documentation
5. Ask in Railway Discord community

---

**Last Updated**: 2025-09-30
**Railway CLI Version**: v4.10.0+
**Project**: ConcordBroker-Railway
**Environment**: concordbrokerproduction
