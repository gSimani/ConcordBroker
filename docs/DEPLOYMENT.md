# ConcordBroker Deployment Guide

## Overview

ConcordBroker is deployed using:
- **Railway**: Backend API and workers
- **Vercel**: React frontend
- **Supabase**: PostgreSQL database (optional)
- **Redis Cloud**: Caching and queues

## Prerequisites

1. **Accounts Required:**
   - [Railway](https://railway.app) account
   - [Vercel](https://vercel.com) account
   - [Supabase](https://supabase.com) account (or use Railway PostgreSQL)
   - [Twilio](https://twilio.com) account for phone verification
   - [Redis Cloud](https://redis.com) account (or use Railway Redis)

2. **CLI Tools:**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Install Vercel CLI
   npm install -g vercel
   
   # Install Docker
   # Visit https://docker.com for installation
   ```

## Environment Variables

Create a `.env` file with:

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/concordbroker
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Redis
REDIS_URL=redis://default:password@host:port

# Authentication
JWT_SECRET=your-secure-jwt-secret
TWILIO_ACCOUNT_SID=ACxxxxxx
TWILIO_AUTH_TOKEN=xxxxxx
TWILIO_VERIFY_SERVICE_ID=VAxxxxxx

# API Keys
SENTRY_DSN=https://xxxxxx@sentry.io/xxxxxx

# Environment
ENVIRONMENT=production
```

## Railway Deployment (Backend)

### 1. Initial Setup

```bash
# Login to Railway
railway login

# Create new project
railway init

# Link to existing project
railway link
```

### 2. Add Services

In Railway dashboard:

1. **PostgreSQL Database:**
   - Click "+ New"
   - Select "Database"
   - Choose "PostgreSQL"
   - Copy DATABASE_URL

2. **Redis:**
   - Click "+ New"
   - Select "Database"
   - Choose "Redis"
   - Copy REDIS_URL

3. **Backend Services:**
   - Click "+ New"
   - Select "GitHub Repo"
   - Choose your repository
   - Railway will auto-detect services

### 3. Configure Services

For each service in Railway:

```yaml
# API Service
Service: api
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Health Check: /health
Variables: (Set all required env vars)

# Worker Services
Service: sunbiz-worker
Start Command: python worker.py
Variables: (Share from API service)

Service: bcpa-worker
Start Command: python worker.py
Variables: (Share from API service)

Service: records-worker
Start Command: python worker.py
Variables: (Share from API service)
```

### 4. Deploy

```bash
# Deploy all services
railway up

# Deploy specific service
railway up --service api

# View logs
railway logs
```

## Vercel Deployment (Frontend)

### 1. Initial Setup

```bash
cd apps/web

# Login to Vercel
vercel login

# Link project
vercel link
```

### 2. Configure Environment

```bash
# Set production variables
vercel env add VITE_API_URL production
# Enter: https://your-api.up.railway.app
```

### 3. Deploy

```bash
# Production deployment
vercel --prod

# Preview deployment
vercel

# With specific environment
vercel --env production
```

## Database Migrations

### Local Development

```bash
# Create migration
cd apps/api
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Production

```bash
# Via Railway
railway run python -m alembic upgrade head

# Via Docker
docker run --rm \
  -e DATABASE_URL=$DATABASE_URL \
  concordbroker-api \
  python -m alembic upgrade head
```

## Monitoring & Maintenance

### Health Checks

- API Health: `https://api.your-domain.com/health`
- Detailed Health: `https://api.your-domain.com/health/detailed`
- System Status: `https://api.your-domain.com/status`

### Logs

```bash
# Railway logs
railway logs --service api
railway logs --service sunbiz-worker

# Vercel logs
vercel logs
```

### Scaling

#### Railway
```bash
# Scale replicas
railway scale --replicas 3 --service api

# Scale resources
railway scale --memory 2048 --service api
```

#### Vercel
- Auto-scales by default
- Configure in vercel.json for limits

## Backup & Recovery

### Database Backup

```bash
# Manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Scheduled backups (add to cron)
0 2 * * * pg_dump $DATABASE_URL | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

### Restore

```bash
# Restore from backup
psql $DATABASE_URL < backup_20240101.sql
```

## SSL/TLS Configuration

### Railway
- SSL enabled by default
- Custom domains: Add in Railway dashboard

### Vercel
- SSL enabled by default
- Custom domains: Add in Vercel dashboard

## CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-railway:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: railway/deploy-action@v1
        with:
          token: ${{ secrets.RAILWAY_TOKEN }}
          
  deploy-vercel:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: |
          cd apps/web
          npm ci
          npm run build
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed:**
   ```bash
   # Check DATABASE_URL format
   postgresql://user:password@host:port/database
   
   # Test connection
   psql $DATABASE_URL -c "SELECT 1"
   ```

2. **Worker Not Processing:**
   ```bash
   # Check worker logs
   railway logs --service worker-name
   
   # Restart worker
   railway restart --service worker-name
   ```

3. **Frontend API Calls Failing:**
   - Verify VITE_API_URL is set correctly
   - Check CORS settings in backend
   - Ensure API is running and healthy

### Support

- Railway Discord: https://discord.gg/railway
- Vercel Support: https://vercel.com/support
- GitHub Issues: https://github.com/your-repo/issues

## Security Checklist

- [ ] All secrets in environment variables
- [ ] JWT_SECRET is strong and unique
- [ ] Database has strong password
- [ ] Twilio credentials are secure
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Authentication required for sensitive endpoints
- [ ] Regular security updates applied
- [ ] Backups configured and tested
- [ ] Monitoring and alerts set up