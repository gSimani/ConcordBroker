# ConcordBroker Deployment Script for Windows
# Run this in PowerShell as Administrator

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   ConcordBroker Deployment Script" -ForegroundColor Cyan  
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command($command) {
    try {
        Get-Command $command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Step 1: Check prerequisites
Write-Host "Step 1: Checking prerequisites..." -ForegroundColor Yellow

$missingTools = @()

if (-not (Test-Command "git")) {
    $missingTools += "Git"
}

if (-not (Test-Command "node")) {
    $missingTools += "Node.js"
}

if (-not (Test-Command "railway")) {
    $missingTools += "Railway CLI"
}

if (-not (Test-Command "vercel")) {
    $missingTools += "Vercel CLI"
}

if ($missingTools.Count -gt 0) {
    Write-Host "❌ Missing tools: $($missingTools -join ', ')" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install missing tools:" -ForegroundColor Yellow
    
    if ($missingTools -contains "Git") {
        Write-Host "  Git: https://git-scm.com/download/win" -ForegroundColor White
    }
    if ($missingTools -contains "Node.js") {
        Write-Host "  Node.js: https://nodejs.org" -ForegroundColor White
    }
    if ($missingTools -contains "Railway CLI") {
        Write-Host "  Railway CLI: Run 'npm install -g @railway/cli'" -ForegroundColor White
    }
    if ($missingTools -contains "Vercel CLI") {
        Write-Host "  Vercel CLI: Run 'npm install -g vercel'" -ForegroundColor White
    }
    
    exit 1
}

Write-Host "✅ All prerequisites installed" -ForegroundColor Green
Write-Host ""

# Step 2: Environment setup
Write-Host "Step 2: Setting up environment..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env from template" -ForegroundColor Green
        Write-Host "⚠️  Please edit .env file with your credentials before continuing" -ForegroundColor Yellow
        Write-Host "Press Enter when ready..." -ForegroundColor White
        Read-Host
    } else {
        Write-Host "❌ No .env.example file found" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ .env file exists" -ForegroundColor Green
}
Write-Host ""

# Step 3: GitHub setup
Write-Host "Step 3: Setting up GitHub repository..." -ForegroundColor Yellow

if (-not (Test-Path ".git")) {
    git init
    git add .
    git commit -m "Initial ConcordBroker implementation"
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Please create a repository on GitHub:" -ForegroundColor Yellow
    Write-Host "1. Go to https://github.com/new" -ForegroundColor White
    Write-Host "2. Name it 'ConcordBroker'" -ForegroundColor White
    Write-Host "3. Make it private" -ForegroundColor White
    Write-Host "4. Don't initialize with README" -ForegroundColor White
    Write-Host ""
    
    $githubUrl = Read-Host "Enter your GitHub repository URL (e.g., https://github.com/username/ConcordBroker.git)"
    
    git remote add origin $githubUrl
    git branch -M main
    git push -u origin main
    
    Write-Host "✅ Code pushed to GitHub" -ForegroundColor Green
} else {
    Write-Host "✅ Git repository already exists" -ForegroundColor Green
    
    # Check if remote exists
    $remoteUrl = git remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  No remote repository set" -ForegroundColor Yellow
        $githubUrl = Read-Host "Enter your GitHub repository URL"
        git remote add origin $githubUrl
    }
    
    # Push latest changes
    git add .
    git commit -m "Update ConcordBroker" 2>$null
    git push origin main
    Write-Host "✅ Latest changes pushed to GitHub" -ForegroundColor Green
}
Write-Host ""

# Step 4: Railway deployment
Write-Host "Step 4: Deploying backend to Railway..." -ForegroundColor Yellow
Write-Host "This will open Railway in your browser" -ForegroundColor White
Write-Host ""

$deployRailway = Read-Host "Deploy to Railway? (y/n)"
if ($deployRailway -eq "y") {
    # Login to Railway
    railway login
    
    # Check if project exists
    $railwayStatus = railway status 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Creating new Railway project..." -ForegroundColor Yellow
        railway init
    }
    
    # Deploy
    Write-Host "Deploying to Railway..." -ForegroundColor Yellow
    railway up
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Backend deployed to Railway" -ForegroundColor Green
        Write-Host "Visit https://railway.app/dashboard to configure services" -ForegroundColor White
    } else {
        Write-Host "❌ Railway deployment failed" -ForegroundColor Red
    }
}
Write-Host ""

# Step 5: Vercel deployment
Write-Host "Step 5: Deploying frontend to Vercel..." -ForegroundColor Yellow

$deployVercel = Read-Host "Deploy to Vercel? (y/n)"
if ($deployVercel -eq "y") {
    Push-Location apps\web
    
    # Install dependencies
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
    
    # Build frontend
    Write-Host "Building frontend..." -ForegroundColor Yellow
    npm run build
    
    # Deploy to Vercel
    Write-Host "Deploying to Vercel..." -ForegroundColor Yellow
    vercel --prod
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Frontend deployed to Vercel" -ForegroundColor Green
    } else {
        Write-Host "❌ Vercel deployment failed" -ForegroundColor Red
    }
    
    Pop-Location
}
Write-Host ""

# Step 6: Summary
Write-Host "================================================" -ForegroundColor Green
Write-Host "   Deployment Summary" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

if ($deployRailway -eq "y") {
    Write-Host "Backend Status:" -ForegroundColor Yellow
    Write-Host "  ✅ Deployed to Railway" -ForegroundColor Green
    Write-Host "  📍 Dashboard: https://railway.app/dashboard" -ForegroundColor White
    Write-Host ""
    Write-Host "  Next steps for Railway:" -ForegroundColor Yellow
    Write-Host "  1. Add PostgreSQL database" -ForegroundColor White
    Write-Host "  2. Add Redis" -ForegroundColor White
    Write-Host "  3. Set environment variables" -ForegroundColor White
    Write-Host ""
}

if ($deployVercel -eq "y") {
    Write-Host "Frontend Status:" -ForegroundColor Yellow
    Write-Host "  ✅ Deployed to Vercel" -ForegroundColor Green
    Write-Host "  📍 Dashboard: https://vercel.com/dashboard" -ForegroundColor White
    Write-Host ""
    Write-Host "  Next steps for Vercel:" -ForegroundColor Yellow
    Write-Host "  1. Set VITE_API_URL environment variable" -ForegroundColor White
    Write-Host "  2. Configure custom domain (optional)" -ForegroundColor White
    Write-Host ""
}

Write-Host "📚 Full deployment guide: DEPLOY_NOW.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 Deployment script complete!" -ForegroundColor Green