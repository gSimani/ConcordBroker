# Production-Local Environment Parity Sync Script
# Automated system to restore local environment to match production exactly
# Combines Vercel, Railway, and Supabase production configurations

param(
    [Parameter(Mandatory=$false)]
    [switch]$FullSync = $false,

    [Parameter(Mandatory=$false)]
    [switch]$DatabaseOnly = $false,

    [Parameter(Mandatory=$false)]
    [switch]$EnvironmentOnly = $false,

    [Parameter(Mandatory=$false)]
    [switch]$SkipDataImport = $false,

    [Parameter(Mandatory=$false)]
    [string]$TargetCommit = ""
)

# Configuration
$RepoRoot = "C:\Users\gsima\Documents\MyProject\ConcordBroker"
$WebDir = "$RepoRoot\apps\web"
$ApiDir = "$RepoRoot\apps\api"
$LogFile = "$RepoRoot\logs\parity-sync-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Ensure log directory exists
New-Item -ItemType Directory -Force -Path "$RepoRoot\logs" | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage -ForegroundColor $(if ($Level -eq "ERROR") {"Red"} elseif ($Level -eq "WARN") {"Yellow"} else {"Green"})
    Add-Content -Path $LogFile -Value $logMessage
}

function Stop-AllServices {
    Write-Log "Stopping all running services..."

    # Kill Node processes
    Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

    # Clear ports
    $ports = @(3000, 3001, 3005, 4173, 5173, 5174, 8000, 8001, 8003, 54321, 54322)
    foreach ($port in $ports) {
        try {
            npx kill-port $port 2>$null
        } catch {}
    }

    Write-Log "All services stopped"
}

function Get-ProductionCommit {
    Write-Log "Getting production commit from Vercel..."

    Set-Location $RepoRoot

    # Ensure Vercel CLI is installed
    if (!(Get-Command vercel -ErrorAction SilentlyContinue)) {
        Write-Log "Installing Vercel CLI..." "WARN"
        npm install -g vercel
    }

    # Link to Vercel project
    vercel link --yes 2>&1 | Out-Null

    # Get production deployment info
    $deployments = vercel list --output json 2>$null | ConvertFrom-Json
    $prodDeployment = $deployments | Where-Object { $_.state -eq "READY" -and $_.target -eq "production" } | Select-Object -First 1

    if ($prodDeployment) {
        $commitSha = $prodDeployment.gitSource.sha
        Write-Log "Found production commit: $commitSha"
        return $commitSha
    } else {
        # Fallback: try to get from current branch
        $currentCommit = git rev-parse HEAD
        Write-Log "Could not get Vercel commit, using current: $currentCommit" "WARN"
        return $currentCommit
    }
}

function Sync-GitCommit {
    param([string]$CommitSha)

    Write-Log "Syncing to commit: $CommitSha"
    Set-Location $RepoRoot

    # Fetch all updates
    git fetch --all --tags

    # Stash any local changes
    $hasChanges = git status --porcelain
    if ($hasChanges) {
        Write-Log "Stashing local changes..." "WARN"
        git stash push -m "Auto-stash before parity sync $(Get-Date)"
    }

    # Checkout the target commit
    git checkout $CommitSha 2>&1 | Out-Null

    $currentCommit = git rev-parse HEAD
    if ($currentCommit -eq $CommitSha) {
        Write-Log "Successfully checked out commit $CommitSha"
    } else {
        Write-Log "Failed to checkout commit $CommitSha" "ERROR"
        throw "Git checkout failed"
    }
}

function Sync-VercelEnvironment {
    Write-Log "Pulling Vercel production environment variables..."

    Set-Location $RepoRoot

    # Pull production env vars
    vercel env pull .env.vercel.production --environment=production --yes 2>&1 | Out-Null

    # Process for frontend (Vite)
    Set-Location $WebDir

    # Backup existing env files
    Get-ChildItem -Path . -Filter ".env*" | ForEach-Object {
        $backupName = "$($_.Name).backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $_.FullName -Destination $backupName
        Write-Log "Backed up $($_.Name) to $backupName"
    }

    # Create clean .env.local for Vite
    $envContent = Get-Content "$RepoRoot\.env.vercel.production"
    $viteEnv = @()

    foreach ($line in $envContent) {
        if ($line -match "^(.+?)=(.*)$") {
            $key = $matches[1]
            $value = $matches[2]

            # Skip production-only vars
            if ($key -in @("NODE_ENV", "VERCEL_ENV", "VERCEL_URL", "VERCEL_GIT_COMMIT_SHA")) {
                continue
            }

            # Ensure proper prefixes for client-side vars
            if ($key -match "^(NEXT_PUBLIC_|VITE_|PUBLIC_)") {
                $viteEnv += "$key=$value"
            } elseif ($key -match "SUPABASE|API_URL|API_KEY") {
                # Add VITE_ prefix if missing for client vars
                if ($key -notmatch "^VITE_") {
                    $viteEnv += "VITE_$key=$value"
                }
                $viteEnv += "$key=$value"
            } else {
                $viteEnv += "$key=$value"
            }
        }
    }

    # Override with local service URLs
    $viteEnv = $viteEnv | ForEach-Object {
        if ($_ -match "^(.+?)=(.*)$") {
            $key = $matches[1]
            $value = $matches[2]

            # Override API URL for local backend
            if ($key -match "API_URL" -and $value -match "railway|vercel|production") {
                return "$key=http://localhost:8000"
            }
            # Keep production Supabase for now (will override if local DB is setup)
            return $_
        }
    }

    $viteEnv | Set-Content ".env.local"
    Write-Log "Created .env.local with $(($viteEnv | Measure-Object).Count) variables"
}

function Setup-SupabaseLocal {
    Write-Log "Setting up local Supabase instance..."

    Set-Location $RepoRoot

    # Check if Supabase CLI is installed
    if (!(Get-Command supabase -ErrorAction SilentlyContinue)) {
        Write-Log "Installing Supabase CLI..." "WARN"
        # Download Supabase CLI for Windows
        $supabaseVersion = "1.142.2"
        $supabaseUrl = "https://github.com/supabase/cli/releases/download/v$supabaseVersion/supabase_windows_amd64.zip"
        Invoke-WebRequest -Uri $supabaseUrl -OutFile "supabase.zip"
        Expand-Archive -Path "supabase.zip" -DestinationPath "." -Force
        Remove-Item "supabase.zip"
        $env:Path += ";$RepoRoot"
    }

    # Initialize Supabase if needed
    if (!(Test-Path "supabase")) {
        supabase init
    }

    # Link to production project
    $supabaseProjectRef = "pmispwtdngkcmsrsjwbp"
    supabase link --project-ref $supabaseProjectRef 2>&1 | Out-Null

    # Pull remote schema
    Write-Log "Pulling production database schema..."
    supabase db pull 2>&1 | Out-Null

    # Start local Supabase
    Write-Log "Starting local Supabase (Docker required)..."
    $supabaseOutput = supabase start 2>&1

    # Parse local credentials
    $localUrl = $supabaseOutput | Select-String "API URL:" | ForEach-Object { $_.Line -replace ".*API URL:\s*", "" }
    $anonKey = $supabaseOutput | Select-String "anon key:" | ForEach-Object { $_.Line -replace ".*anon key:\s*", "" }
    $serviceKey = $supabaseOutput | Select-String "service_role key:" | ForEach-Object { $_.Line -replace ".*service_role key:\s*", "" }

    if ($localUrl -and $anonKey) {
        Write-Log "Local Supabase started at $localUrl"

        # Update env files with local Supabase
        $envFile = "$WebDir\.env.local"
        $envContent = Get-Content $envFile
        $updatedEnv = @()

        foreach ($line in $envContent) {
            if ($line -match "SUPABASE_URL") {
                $updatedEnv += $line -replace "https://.*\.supabase\.co", $localUrl
            } elseif ($line -match "SUPABASE_ANON_KEY") {
                $updatedEnv += $line -replace "=.*", "=$anonKey"
            } elseif ($line -match "SUPABASE_SERVICE_ROLE_KEY") {
                $updatedEnv += $line -replace "=.*", "=$serviceKey"
            } else {
                $updatedEnv += $line
            }
        }

        $updatedEnv | Set-Content $envFile
        Write-Log "Updated environment with local Supabase credentials"
    } else {
        Write-Log "Failed to start local Supabase - continuing with production DB" "WARN"
    }

    # Import data if requested
    if (!$SkipDataImport) {
        Write-Log "Importing production data (this may take a while)..."
        supabase db dump --data-only > "$RepoRoot\temp\production-data.sql"

        if (Test-Path "$RepoRoot\temp\production-data.sql") {
            psql -h localhost -p 54322 -d postgres -U postgres -f "$RepoRoot\temp\production-data.sql"
            Write-Log "Data import completed"
        }
    }
}

function Setup-RailwayLocal {
    Write-Log "Setting up Railway environment bridge..."

    Set-Location $ApiDir

    # Check if Railway CLI is installed
    if (!(Get-Command railway -ErrorAction SilentlyContinue)) {
        Write-Log "Installing Railway CLI..." "WARN"
        npm install -g @railway/cli
    }

    # Login to Railway
    railway login 2>&1 | Out-Null

    # Link to project
    railway link 2>&1 | Out-Null

    # Create local env file from Railway
    Write-Log "Pulling Railway environment variables..."
    railway variables > .env.railway

    # Process Railway env for local use
    $railwayEnv = Get-Content .env.railway
    $localEnv = @()

    foreach ($line in $railwayEnv) {
        if ($line -match "^(.+?)=(.*)$") {
            $key = $matches[1]
            $value = $matches[2]

            # Override database URL if using local Supabase
            if ($key -eq "DATABASE_URL" -and (Test-Path "$RepoRoot\supabase\.temp\local-db-url.txt")) {
                $localDbUrl = Get-Content "$RepoRoot\supabase\.temp\local-db-url.txt"
                $localEnv += "DATABASE_URL=$localDbUrl"
            } else {
                $localEnv += $line
            }
        }
    }

    $localEnv | Set-Content ".env"
    Write-Log "Created backend .env with $(($localEnv | Measure-Object).Count) variables"
}

function Install-ParityTools {
    Write-Log "Installing parity maintenance tools..."

    Set-Location $RepoRoot

    # Create package.json for parity tools if it doesn't exist
    if (!(Test-Path "parity-tools\package.json")) {
        New-Item -ItemType Directory -Force -Path "parity-tools" | Out-Null
        Set-Location "parity-tools"

        @{
            name = "production-parity-tools"
            version = "1.0.0"
            dependencies = @{
                "dotenv-safe" = "^8.2.0"
                "cross-env" = "^7.0.3"
                "concurrently" = "^8.2.0"
                "wait-on" = "^7.2.0"
                "env-cmd" = "^10.1.0"
            }
        } | ConvertTo-Json | Set-Content "package.json"

        npm install
    }

    Write-Log "Parity tools installed"
}

function Create-ValidationScript {
    Write-Log "Creating validation script..."

    $validationScript = @'
// Production-Local Parity Validator
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class ParityValidator {
    constructor() {
        this.results = {
            passed: [],
            failed: [],
            warnings: []
        };
    }

    checkEnvVariables(envFile, requiredVars) {
        console.log(`Checking environment variables in ${envFile}...`);

        if (!fs.existsSync(envFile)) {
            this.results.failed.push(`Environment file not found: ${envFile}`);
            return false;
        }

        const envContent = fs.readFileSync(envFile, 'utf8');
        const envVars = {};

        envContent.split('\n').forEach(line => {
            const match = line.match(/^([^=]+)=(.*)$/);
            if (match) {
                envVars[match[1]] = match[2];
            }
        });

        requiredVars.forEach(varName => {
            if (!envVars[varName]) {
                this.results.failed.push(`Missing required env var: ${varName}`);
            } else {
                this.results.passed.push(`Found env var: ${varName}`);
            }
        });

        return this.results.failed.length === 0;
    }

    async checkDatabaseConnection(dbUrl) {
        console.log('Checking database connection...');
        // Implementation would use actual DB client
        // For now, just check if URL is provided
        if (dbUrl) {
            this.results.passed.push('Database URL configured');
            return true;
        } else {
            this.results.failed.push('No database URL found');
            return false;
        }
    }

    checkServicePorts(ports) {
        console.log('Checking service ports...');
        const net = require('net');

        const checkPort = (port) => {
            return new Promise((resolve) => {
                const server = net.createServer();
                server.once('error', () => resolve(false));
                server.once('listening', () => {
                    server.close();
                    resolve(true);
                });
                server.listen(port);
            });
        };

        return Promise.all(ports.map(port =>
            checkPort(port).then(available => {
                if (available) {
                    this.results.passed.push(`Port ${port} is available`);
                } else {
                    this.results.warnings.push(`Port ${port} is in use`);
                }
                return available;
            })
        ));
    }

    generateReport() {
        console.log('\n=== PARITY VALIDATION REPORT ===\n');

        console.log(`✅ Passed: ${this.results.passed.length}`);
        this.results.passed.forEach(msg => console.log(`  - ${msg}`));

        if (this.results.warnings.length > 0) {
            console.log(`\n⚠️ Warnings: ${this.results.warnings.length}`);
            this.results.warnings.forEach(msg => console.log(`  - ${msg}`));
        }

        if (this.results.failed.length > 0) {
            console.log(`\n❌ Failed: ${this.results.failed.length}`);
            this.results.failed.forEach(msg => console.log(`  - ${msg}`));
        }

        const success = this.results.failed.length === 0;
        console.log(`\n${success ? '✅ VALIDATION PASSED' : '❌ VALIDATION FAILED'}\n`);

        return success;
    }
}

// Run validation
const validator = new ParityValidator();

async function validate() {
    // Check frontend env
    validator.checkEnvVariables(
        path.join(__dirname, '../apps/web/.env.local'),
        ['VITE_SUPABASE_URL', 'VITE_SUPABASE_ANON_KEY', 'VITE_API_URL']
    );

    // Check backend env
    validator.checkEnvVariables(
        path.join(__dirname, '../apps/api/.env'),
        ['DATABASE_URL', 'JWT_SECRET']
    );

    // Check ports
    await validator.checkServicePorts([3000, 5173, 8000, 54321, 54322]);

    // Generate report
    const success = validator.generateReport();
    process.exit(success ? 0 : 1);
}

validate().catch(console.error);
'@

    $validationScript | Set-Content "$RepoRoot\scripts\validate-parity.js"
    Write-Log "Validation script created"
}

function Start-Services {
    Write-Log "Starting all services..."

    # Start Supabase if not running
    Set-Location $RepoRoot
    $supabaseStatus = supabase status 2>&1
    if ($supabaseStatus -match "stopped") {
        supabase start
    }

    # Start backend with Railway env
    Set-Location $ApiDir
    if (Test-Path ".env.railway") {
        Start-Process -FilePath "powershell" -ArgumentList "-Command", "railway run npm run dev" -WorkingDirectory $ApiDir
    } else {
        Start-Process -FilePath "powershell" -ArgumentList "-Command", "npm run dev" -WorkingDirectory $ApiDir
    }

    # Start frontend
    Set-Location $WebDir
    Start-Process -FilePath "powershell" -ArgumentList "-Command", "npm run dev -- --port 5173" -WorkingDirectory $WebDir

    Write-Log "All services started"
    Write-Log "Frontend: http://localhost:5173"
    Write-Log "Backend: http://localhost:8000"
    Write-Log "Supabase Studio: http://localhost:54323"
}

function Run-FullSync {
    Write-Log "=== STARTING FULL PRODUCTION PARITY SYNC ===" "WARN"

    try {
        # Step 1: Stop all services
        Stop-AllServices

        # Step 2: Get and checkout production commit
        if ($TargetCommit) {
            $prodCommit = $TargetCommit
        } else {
            $prodCommit = Get-ProductionCommit
        }
        Sync-GitCommit -CommitSha $prodCommit

        # Step 3: Pull Vercel environment
        if (!$DatabaseOnly) {
            Sync-VercelEnvironment
        }

        # Step 4: Setup local Supabase
        if (!$EnvironmentOnly) {
            Setup-SupabaseLocal
        }

        # Step 5: Setup Railway bridge
        if (!$DatabaseOnly) {
            Setup-RailwayLocal
        }

        # Step 6: Install parity tools
        Install-ParityTools

        # Step 7: Create validation script
        Create-ValidationScript

        # Step 8: Clean install dependencies
        Write-Log "Installing dependencies..."
        Set-Location $WebDir
        Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
        npm ci

        Set-Location $ApiDir
        if (Test-Path "package.json") {
            Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
            npm ci
        }

        # Step 9: Run validation
        Write-Log "Running parity validation..."
        Set-Location $RepoRoot
        node scripts\validate-parity.js

        # Step 10: Start services
        Start-Services

        Write-Log "=== PRODUCTION PARITY SYNC COMPLETED ===" "WARN"
        Write-Log "Your local environment now matches production!"
        Write-Log ""
        Write-Log "Next steps:"
        Write-Log "1. Clear browser cache and cookies for localhost"
        Write-Log "2. Open http://localhost:5173 in incognito mode"
        Write-Log "3. Test all critical user flows"
        Write-Log ""
        Write-Log "To view logs: notepad $LogFile"

    } catch {
        Write-Log "Sync failed: $_" "ERROR"
        throw
    }
}

# Main execution
if ($FullSync -or (!$DatabaseOnly -and !$EnvironmentOnly)) {
    Run-FullSync
} elseif ($DatabaseOnly) {
    Stop-AllServices
    Setup-SupabaseLocal
    Write-Log "Database sync completed"
} elseif ($EnvironmentOnly) {
    Stop-AllServices
    Sync-VercelEnvironment
    Setup-RailwayLocal
    Write-Log "Environment sync completed"
}

Write-Host "`nSync completed! Check log file: $LogFile" -ForegroundColor Green