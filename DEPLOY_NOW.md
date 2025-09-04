# 🚀 ConcordBroker Deployment Steps

Follow these steps to deploy ConcordBroker to production:

## Prerequisites Checklist

### 1. Create Required Accounts
- [ ] **Railway Account**: https://railway.app/signup
- [ ] **Vercel Account**: https://vercel.com/signup
- [ ] **Twilio Account**: https://www.twilio.com/try-twilio
- [ ] **GitHub Account**: https://github.com (to host your code)

### 2. Install CLI Tools
Open PowerShell as Administrator and run:

```powershell
# Install Node.js first if not installed
# Download from https://nodejs.org

# Install Railway CLI
npm install -g @railway/cli

# Install Vercel CLI
npm install -g vercel

# Verify installations
railway --version
vercel --version
```

## Step 1: Push Code to GitHub

```powershell
# Initialize git repository
cd C:\Users\gsima\Documents\MyProject\ConcordBroker
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial ConcordBroker implementation"

# Create repository on GitHub (via browser)
# Go to: https://github.com/new
# Name: ConcordBroker
# Make it private

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/ConcordBroker.git
git branch -M main
git push -u origin main
```

## Step 2: Set Up Twilio Verify

1. Go to https://console.twilio.com
2. Navigate to Verify > Services
3. Click "Create Service"
4. Name: "ConcordBroker"
5. Save the Service ID (starts with VA)
6. Get your Account SID and Auth Token from Dashboard

## Step 3: Deploy Backend to Railway

```powershell
# Login to Railway
railway login

# Initialize new project
railway init
# Choose: "Empty Project"
# Name: "ConcordBroker"

# Link your GitHub repo
# Go to https://railway.app/dashboard
# Click your project
# Click "+ New" > "GitHub Repo"
# Connect GitHub and select ConcordBroker repo

# Add PostgreSQL
# Click "+ New" > "Database" > "Add PostgreSQL"

# Add Redis
# Click "+ New" > "Database" > "Add Redis"

# Set environment variables in Railway Dashboard
# Go to each service > Variables
# Add these variables:

DATABASE_URL=(auto-filled by Railway)
REDIS_URL=(auto-filled by Railway)
JWT_SECRET=your-super-secret-jwt-key-change-this
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxx
TWILIO_VERIFY_SERVICE_ID=VAxxxxxxxxxx
ENVIRONMENT=production
PORT=8000

# Deploy
railway up
```

## Step 4: Deploy Frontend to Vercel

```powershell
# Navigate to frontend
cd apps\web

# Login to Vercel
vercel login

# Deploy
vercel

# When prompted:
# - Set up and deploy: Y
# - Which scope: Select your account
# - Link to existing project: N
# - Project name: concordbroker-web
# - Directory: ./
# - Override settings: N

# Set environment variable
vercel env add VITE_API_URL production
# Enter the Railway API URL (e.g., https://concordbroker-production.up.railway.app)

# Deploy to production
vercel --prod

# Your frontend will be available at:
# https://concordbroker-web.vercel.app
```

## Step 5: Configure Custom Domains (Optional)

### Railway (Backend API)
1. Go to Railway Dashboard > Your Project > API service
2. Click "Settings" > "Domains"
3. Add custom domain or use provided domain

### Vercel (Frontend)
1. Go to Vercel Dashboard > Your Project
2. Click "Settings" > "Domains"
3. Add custom domain

## Step 6: Initialize Database

```powershell
# Get your Railway database URL
railway variables

# Run migrations
railway run --service api "python -c 'from database import Database; import asyncio; asyncio.run(Database().create_tables())'"
```

## Step 7: Verify Deployment

### Check Backend
```powershell
# Get your API URL from Railway
# Test health endpoint
curl https://your-api.up.railway.app/health

# Should return: {"status":"healthy"}
```

### Check Frontend
```powershell
# Open in browser
start https://concordbroker-web.vercel.app

# You should see the login page
```

## Step 8: Test Authentication

1. Open frontend in browser
2. Enter your phone number
3. In demo mode, use code: 123456
4. You should be logged in and see the dashboard

## Troubleshooting

### If Railway deployment fails:
```powershell
# Check logs
railway logs

# Common issues:
# - Missing environment variables
# - Port binding issues (ensure PORT env var is set)
```

### If Vercel deployment fails:
```powershell
# Check build logs
vercel logs

# Common issues:
# - Wrong Node version (needs 18+)
# - Missing VITE_API_URL
```

### If authentication fails:
- Verify Twilio credentials are correct
- Check that TWILIO_VERIFY_SERVICE_ID starts with "VA"
- In development, the system uses demo mode (code: 123456)

## Quick Deploy Script (Windows PowerShell)

Save this as `deploy.ps1`:

```powershell
Write-Host "🚀 Deploying ConcordBroker..." -ForegroundColor Green

# Deploy backend
Write-Host "Deploying backend to Railway..." -ForegroundColor Yellow
railway up

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backend deployed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Backend deployment failed" -ForegroundColor Red
    exit 1
}

# Deploy frontend
Write-Host "Deploying frontend to Vercel..." -ForegroundColor Yellow
cd apps\web
vercel --prod

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend deployed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend deployment failed" -ForegroundColor Red
    exit 1
}

cd ..\..

Write-Host "🎉 Deployment complete!" -ForegroundColor Green
Write-Host "Backend: Check Railway dashboard for URL" -ForegroundColor Cyan
Write-Host "Frontend: Check Vercel dashboard for URL" -ForegroundColor Cyan
```

## Post-Deployment

1. **Monitor Services**:
   - Railway Dashboard: https://railway.app/dashboard
   - Vercel Dashboard: https://vercel.com/dashboard

2. **Set Up Alerts**:
   - Configure Railway notifications for service failures
   - Set up Vercel notifications for build failures

3. **Start Data Collection**:
   - Workers will automatically start collecting data
   - Sunbiz data updates daily
   - BCPA scraper runs weekly
   - Official Records scraper runs daily

## Need Help?

- Railway Discord: https://discord.gg/railway
- Vercel Support: https://vercel.com/support
- Create an issue: https://github.com/YOUR_USERNAME/ConcordBroker/issues

---

**Ready to deploy? Start with Step 1: Push Code to GitHub**