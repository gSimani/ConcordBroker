# 🚀 Production Deployment Guide - Optimized Agent System

**Complete guide for deploying the optimized agent system to production**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Testing with Docker](#local-testing-with-docker)
3. [Railway Deployment](#railway-deployment)
4. [Environment Configuration](#environment-configuration)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Monitoring Setup](#monitoring-setup)
7. [Security Hardening](#security-hardening)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Services

- **Railway Account** (or AWS/GCP for alternative deployment)
- **Docker & Docker Compose** (for local testing)
- **GitHub** (for CI/CD)
- **Supabase** (PostgreSQL database)
- **Redis** (state persistence)
- **OpenAI API Key** (for LLM operations)

### Required Tools

```bash
# Install Docker
https://docs.docker.com/get-docker/

# Install Railway CLI
npm install -g @railway/cli

# Install Python 3.11+
https://www.python.org/downloads/

# Install Git
https://git-scm.com/downloads
```

---

## 🐳 Local Testing with Docker

### Step 1: Build and Test Locally

```bash
# 1. Copy environment template
cp .env.orchestrator.example .env.orchestrator

# 2. Fill in your environment variables
nano .env.orchestrator  # Or use your favorite editor

# 3. Build Docker images
docker-compose -f docker-compose.orchestrator.yml build

# 4. Start all services
docker-compose -f docker-compose.orchestrator.yml up

# 5. Verify health (in another terminal)
curl http://localhost:8000/health  # Orchestrator
curl http://localhost:8001/health  # Florida Worker
curl http://localhost:8002/health  # Data Quality
curl http://localhost:8003/health  # SunBiz
curl http://localhost:8004/health  # Entity Matching
curl http://localhost:8005/health  # Performance
curl http://localhost:8006/health  # AI/ML

# All should return: {"status": "healthy"}
```

### Step 2: Run Integration Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
cd mcp-server/orchestrator/tests
pytest -v -s

# Should see: 19 tests passing
```

### Step 3: Stop Services

```bash
# Stop all containers
docker-compose -f docker-compose.orchestrator.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.orchestrator.yml down -v
```

---

## 🚂 Railway Deployment

### Option 1: Deploy via Railway CLI

#### 1. Login to Railway

```bash
railway login
```

#### 2. Create New Project

```bash
railway init
# Select "Create a new project"
# Name it: concordbroker-agent-system
```

#### 3. Add Redis Service

```bash
railway add
# Select: Redis
```

#### 4. Deploy Orchestrator

```bash
cd mcp-server/orchestrator

# Create service
railway service create orchestrator

# Set environment variables
railway variables --set REDIS_URL=$REDIS_URL
railway variables --set DATABASE_URL=$DATABASE_URL
railway variables --set SUPABASE_URL=$SUPABASE_URL
railway variables --set SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY
railway variables --set OPENAI_API_KEY=$OPENAI_API_KEY
railway variables --set CONFIDENCE_THRESHOLD=0.7

# Deploy
railway up --service orchestrator
```

#### 5. Deploy Workers

```bash
cd workers

# Deploy each worker
for worker in florida-data data-quality sunbiz entity-matching performance aiml; do
  railway service create ${worker}-worker
  railway up --service ${worker}-worker
done
```

#### 6. Verify Deployment

```bash
# Get orchestrator URL
railway open orchestrator

# Test health endpoint
curl https://your-orchestrator-url.railway.app/health
```

### Option 2: Deploy via GitHub (Recommended)

#### 1. Push Code to GitHub

```bash
git add .
git commit -m "Add production deployment configuration"
git push origin production
```

#### 2. Configure GitHub Secrets

Go to Repository Settings → Secrets and Variables → Actions

Add these secrets:
- `RAILWAY_TOKEN` - Your Railway API token
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password (or token)
- `PRODUCTION_ORCHESTRATOR_URL` - Railway orchestrator URL (after first manual deploy)

#### 3. Trigger Deployment

```bash
# Push to production branch
git push origin production

# Or trigger manually via GitHub Actions UI
```

#### 4. Monitor Deployment

- Go to GitHub Actions tab
- Watch the deployment pipeline
- All jobs should complete successfully

---

## 🔐 Environment Configuration

### Required Environment Variables

#### For Master Orchestrator:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/concordbroker
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Redis
REDIS_URL=redis://default:pass@redis.railway.internal:6379

# AI/LLM
OPENAI_API_KEY=sk-...
LANGCHAIN_API_KEY=lc_...
LANGSMITH_API_KEY=ls_...

# Configuration
CONFIDENCE_THRESHOLD=0.7
ENABLE_CONTEXT_COMPRESSION=true
ENABLE_REWOO_PLANNING=true

# Security
API_KEY=your-secure-api-key
CORS_ORIGINS=https://www.concordbroker.com

# Railway will automatically set:
# PORT=8000 (or assigned by Railway)
```

#### For Workers:

Workers inherit most environment variables from orchestrator. Additional worker-specific variables:

```bash
# Florida Data Worker
FLORIDA_DATA_DOWNLOAD_PATH=/tmp/florida_data

# AI/ML Worker
OPENAI_API_KEY=sk-...  # Required for AI operations
```

### Setting Variables on Railway

```bash
# Via CLI
railway variables --set KEY=VALUE

# Via Dashboard
# 1. Go to project dashboard
# 2. Select service
# 3. Go to "Variables" tab
# 4. Add key-value pairs
```

---

## ⚙️ CI/CD Pipeline

### GitHub Actions Workflow

The deployment pipeline (`.github/workflows/deploy-orchestrator.yml`) includes:

**1. Testing**
- Linting (flake8, black, isort)
- Unit tests with coverage
- Integration tests
- E2E workflow tests

**2. Building**
- Build Docker images
- Push to Docker Hub
- Tag with commit SHA

**3. Deployment**
- Deploy to Railway (production branch only)
- Run health checks
- Verify deployment

**4. Validation**
- Smoke tests on production
- Performance validation
- Notification on success/failure

### Triggering Deployments

```bash
# Automatic (on push to main/production)
git push origin production

# Manual (via GitHub Actions)
# 1. Go to Actions tab
# 2. Select "Deploy Optimized Agent System"
# 3. Click "Run workflow"
# 4. Select branch
# 5. Click "Run workflow"
```

### Monitoring Pipeline

```bash
# Watch logs in real-time
gh run watch

# View recent runs
gh run list

# View specific run
gh run view <run-id>
```

---

## 📊 Monitoring Setup

### Prometheus Metrics (Optional)

Add Prometheus endpoint to orchestrator:

```python
# In master_orchestrator.py
from prometheus_client import Counter, Histogram, generate_latest

operations_counter = Counter('operations_total', 'Total operations')
operation_duration = Histogram('operation_duration_seconds', 'Operation duration')

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### Grafana Dashboard (Optional)

Create dashboard with these panels:
- Operations per minute
- Average response time
- Token usage per operation
- Error rate
- Worker health status
- Redis connection pool

### Railway Metrics (Built-in)

Railway provides:
- CPU usage
- Memory usage
- Network traffic
- Request count
- Error rates

Access via: Railway Dashboard → Service → Metrics

### Log Aggregation

```bash
# View logs via Railway CLI
railway logs --service orchestrator

# View specific worker logs
railway logs --service florida-data-worker

# Follow logs in real-time
railway logs --service orchestrator --follow

# Filter logs
railway logs --service orchestrator --filter "ERROR"
```

---

## 🔒 Security Hardening

### 1. API Authentication

Add API key validation:

```python
# In master_orchestrator.py
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == os.getenv("API_KEY"):
        return api_key
    raise HTTPException(status_code=403, detail="Invalid API Key")

@app.post("/operations", dependencies=[Depends(get_api_key)])
async def create_operation(request: OperationRequest):
    # ... existing code
```

### 2. Rate Limiting

Add rate limiting:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/operations")
@limiter.limit("10/minute")
async def create_operation(request: Request, ...):
    # ... existing code
```

### 3. CORS Configuration

```python
# Restrict CORS to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 4. Input Validation

All inputs are validated via Pydantic models (already implemented).

### 5. Secrets Management

**Never commit secrets to Git!**

Use Railway's secret management:

```bash
# Add secrets via CLI
railway variables --set SECRET_NAME=secret_value

# Or use Railway dashboard
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Services Not Starting

```bash
# Check logs
railway logs --service orchestrator

# Common causes:
# - Missing environment variables
# - Redis not connected
# - Port conflict

# Solution:
# Verify all required env vars are set
railway variables
```

#### 2. Health Checks Failing

```bash
# Test locally first
curl http://localhost:8000/health

# Check if Redis is accessible
redis-cli ping

# Verify database connection
psql $DATABASE_URL -c "SELECT 1;"
```

#### 3. Workers Not Connecting

```bash
# Check worker logs
railway logs --service florida-data-worker

# Verify worker can reach orchestrator
# Workers should use internal Railway URLs
```

#### 4. High Token Usage

```bash
# Check if context compression is enabled
echo $ENABLE_CONTEXT_COMPRESSION  # Should be "true"

# Check if ReWOO planning is enabled
echo $ENABLE_REWOO_PLANNING  # Should be "true"

# Review operation logs for token usage
railway logs --service orchestrator --filter "Token usage"
```

#### 5. Deployment Failures

```bash
# Check GitHub Actions logs
gh run view

# Common causes:
# - Test failures
# - Docker build errors
# - Railway token expired

# Re-run failed jobs
gh run rerun <run-id>
```

### Getting Help

- **Railway Support**: https://railway.app/support
- **GitHub Issues**: Create issue in repository
- **Documentation**: Check all .md files in project root

---

## ✅ Production Deployment Checklist

### Pre-Deployment

- [ ] All tests passing locally
- [ ] Docker compose working locally
- [ ] Environment variables configured
- [ ] Secrets added to Railway/GitHub
- [ ] CI/CD pipeline tested
- [ ] Security hardening implemented

### Deployment

- [ ] Code pushed to production branch
- [ ] CI/CD pipeline completed successfully
- [ ] All services deployed to Railway
- [ ] Health checks passing
- [ ] Smoke tests completed

### Post-Deployment

- [ ] Production URL accessible
- [ ] API responding correctly
- [ ] Workers communicating with orchestrator
- [ ] Token usage within targets
- [ ] Response times acceptable
- [ ] Logs show no errors
- [ ] Monitoring dashboards working
- [ ] Team notified of deployment

---

## 📊 Performance Targets

**Production SLAs:**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Uptime | 99.9% | < 99.5% |
| Response Time | < 3s | > 5s |
| Token Usage | < 10K/op | > 15K/op |
| Error Rate | < 0.1% | > 1% |
| CPU Usage | < 70% | > 85% |
| Memory Usage | < 80% | > 90% |

---

## 🚀 Next Steps After Deployment

1. **Monitor for 24 hours**
   - Watch logs for errors
   - Check performance metrics
   - Verify token usage

2. **Run Load Tests**
   - Test 100+ concurrent operations
   - Verify system handles load
   - Check for memory leaks

3. **Optimize Based on Metrics**
   - Adjust worker counts if needed
   - Tune timeout values
   - Optimize slow operations

4. **Set Up Alerts**
   - High error rate
   - Service down
   - High latency
   - High token usage

5. **Document Learnings**
   - Update troubleshooting guide
   - Add common issues
   - Share with team

---

**Created**: October 20, 2025
**Last Updated**: October 20, 2025
**Status**: ✅ READY FOR PRODUCTION
**Deployment Type**: Railway (recommended) or AWS/GCP

**The optimized agent system is ready for production deployment!** 🚀
