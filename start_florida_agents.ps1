# Florida Data Agent System - Startup Script
# Comprehensive monitoring and download system for all Florida property data

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("once", "continuous", "status", "test", "setup")]
    [string]$Mode = "once",
    
    [Parameter(Mandatory=$false)]
    [string]$Agent = "",
    
    [switch]$InstallDependencies,
    [switch]$CreateDatabase,
    [switch]$ShowDashboard
)

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  FLORIDA DATA AGENT SYSTEM" -ForegroundColor Cyan
Write-Host "  Comprehensive Property Data Monitoring" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Install dependencies if requested
if ($InstallDependencies) {
    Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
    
    $requirements = @"
pandas>=1.5.0
requests>=2.28.0
beautifulsoup4>=4.11.0
paramiko>=2.12.0
schedule>=1.1.0
supabase>=2.0.0
python-dotenv>=0.21.0
aiohttp>=3.8.0
httpx>=0.24.0
lxml>=4.9.0
openpyxl>=3.0.0
"@
    
    $requirements | Out-File -FilePath "requirements_agents.txt" -Encoding UTF8
    
    pip install -r requirements_agents.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to install dependencies!" -ForegroundColor Red
        exit 1
    }
}

# Create database tables if requested
if ($CreateDatabase) {
    Write-Host "`nCreating database tables..." -ForegroundColor Yellow
    
    $sqlScript = @"
-- Florida Data Agent System - Database Schema

-- Agent monitoring table
CREATE TABLE IF NOT EXISTS agent_monitoring (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100),
    activity_type VARCHAR(50),
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50),
    last_run TIMESTAMP,
    files_found INTEGER,
    files_downloaded INTEGER,
    files_processed INTEGER,
    error_message TEXT,
    next_scheduled_run TIMESTAMP
);

-- Florida Revenue NAL data
CREATE TABLE IF NOT EXISTS florida_nal (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    county_code VARCHAR(10),
    year INTEGER,
    owner_name TEXT,
    owner_addr1 TEXT,
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    phy_addr1 TEXT,
    phy_city VARCHAR(100),
    phy_state VARCHAR(2),
    phy_zipcd VARCHAR(10),
    property_use VARCHAR(20),
    property_use_desc TEXT,
    just_value NUMERIC,
    assessed_value NUMERIC,
    taxable_value NUMERIC,
    land_value NUMERIC,
    building_value NUMERIC,
    year_built INTEGER,
    total_living_area INTEGER,
    bedrooms INTEGER,
    bathrooms NUMERIC,
    import_date TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(50)
);

-- Florida Revenue SDF sales data
CREATE TABLE IF NOT EXISTS florida_sdf (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    sale_date DATE,
    sale_price NUMERIC,
    vi_code VARCHAR(10),
    qualified_sale BOOLEAN,
    grantor TEXT,
    grantee TEXT,
    or_book VARCHAR(20),
    or_page VARCHAR(20),
    import_date TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(50)
);

-- Sunbiz entities
CREATE TABLE IF NOT EXISTS sunbiz_entities (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(50),
    corporate_name TEXT,
    entity_type VARCHAR(100),
    status VARCHAR(50),
    filing_date DATE,
    principal_address TEXT,
    principal_city VARCHAR(100),
    principal_state VARCHAR(2),
    principal_zip VARCHAR(10),
    registered_agent TEXT,
    officers JSONB,
    import_date TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(50)
);

-- Broward daily index
CREATE TABLE IF NOT EXISTS broward_daily_index (
    id SERIAL PRIMARY KEY,
    record_date DATE,
    document_type VARCHAR(100),
    document_number VARCHAR(50),
    book INTEGER,
    page INTEGER,
    parcel_id VARCHAR(50),
    grantor TEXT,
    grantee TEXT,
    consideration NUMERIC,
    import_date TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(50)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_agent_monitoring_name ON agent_monitoring(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_monitoring_timestamp ON agent_monitoring(timestamp);
CREATE INDEX IF NOT EXISTS idx_florida_nal_parcel ON florida_nal(parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_nal_county ON florida_nal(county_code);
CREATE INDEX IF NOT EXISTS idx_florida_sdf_parcel ON florida_sdf(parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_sdf_date ON florida_sdf(sale_date);
CREATE INDEX IF NOT EXISTS idx_sunbiz_name ON sunbiz_entities(corporate_name);
CREATE INDEX IF NOT EXISTS idx_broward_parcel ON broward_daily_index(parcel_id);
CREATE INDEX IF NOT EXISTS idx_broward_date ON broward_daily_index(record_date);

-- Enable RLS
ALTER TABLE agent_monitoring ENABLE ROW LEVEL SECURITY;
ALTER TABLE florida_nal ENABLE ROW LEVEL SECURITY;
ALTER TABLE florida_sdf ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE broward_daily_index ENABLE ROW LEVEL SECURITY;

-- Create read policies
CREATE POLICY "Public read" ON agent_monitoring FOR SELECT USING (true);
CREATE POLICY "Public read" ON florida_nal FOR SELECT USING (true);
CREATE POLICY "Public read" ON florida_sdf FOR SELECT USING (true);
CREATE POLICY "Public read" ON sunbiz_entities FOR SELECT USING (true);
CREATE POLICY "Public read" ON broward_daily_index FOR SELECT USING (true);

SELECT 'Database tables created successfully!' as status;
"@
    
    $sqlScript | Out-File -FilePath "create_agent_tables.sql" -Encoding UTF8
    
    Write-Host "SQL script created: create_agent_tables.sql" -ForegroundColor Green
    Write-Host "Please run this in your Supabase SQL Editor" -ForegroundColor Yellow
}

# Check environment variables
Write-Host "`nChecking environment variables..." -ForegroundColor Yellow

$requiredEnvVars = @(
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY"
)

$missingVars = @()
foreach ($var in $requiredEnvVars) {
    if (-not (Test-Path env:$var)) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "Missing environment variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "  - $var" -ForegroundColor Red
    }
    Write-Host "`nPlease set these in your .env file" -ForegroundColor Yellow
    exit 1
}

Write-Host "Environment variables OK" -ForegroundColor Green

# Run the agent system
Write-Host "`nStarting Florida Data Agent System..." -ForegroundColor Cyan
Write-Host "Mode: $Mode" -ForegroundColor Yellow

if ($Agent) {
    Write-Host "Agent: $Agent" -ForegroundColor Yellow
}

# Change to workers directory
Set-Location -Path "apps\workers"

# Build command
$command = "python florida_master_agent.py --mode $Mode"
if ($Agent) {
    $command += " --agent $Agent"
}

# Show dashboard if requested
if ($ShowDashboard) {
    Write-Host "`nOpening monitoring dashboard..." -ForegroundColor Cyan
    Start-Process "http://localhost:8000/agent-dashboard"
}

# Execute based on mode
switch ($Mode) {
    "once" {
        Write-Host "`nRunning all agents once..." -ForegroundColor Green
        Invoke-Expression $command
    }
    
    "continuous" {
        Write-Host "`nStarting continuous monitoring..." -ForegroundColor Green
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
        Invoke-Expression $command
    }
    
    "status" {
        Write-Host "`nGetting agent status..." -ForegroundColor Green
        $status = Invoke-Expression $command
        Write-Host $status
    }
    
    "test" {
        Write-Host "`nRunning test mode..." -ForegroundColor Green
        
        # Test each agent
        $agents = @("florida_revenue", "sunbiz", "broward_daily")
        foreach ($testAgent in $agents) {
            Write-Host "`nTesting $testAgent..." -ForegroundColor Yellow
            python florida_master_agent.py --mode once --agent $testAgent
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "$testAgent OK" -ForegroundColor Green
            } else {
                Write-Host "$testAgent FAILED" -ForegroundColor Red
            }
        }
    }
    
    "setup" {
        Write-Host "`nSetup mode - Creating configuration..." -ForegroundColor Green
        
        # Create config file
        $config = @{
            agents = @{
                florida_revenue = @{
                    enabled = $true
                    schedule = "0 3 * * 1"
                    data_types = @("NAL", "NAP", "NAV", "SDF", "TPP")
                }
                sunbiz = @{
                    enabled = $true
                    schedule = "0 2 * * 0"
                    sftp = @{
                        host = "sftp.floridados.gov"
                        username = "Public"
                        password = "PubAccess1845!"
                    }
                }
                broward_daily = @{
                    enabled = $true
                    schedule = "0 6 * * *"
                }
            }
            monitoring = @{
                alert_email = "admin@concordbroker.com"
                check_interval = 3600
            }
        }
        
        $config | ConvertTo-Json -Depth 4 | Out-File -FilePath "agent_config.json" -Encoding UTF8
        Write-Host "Configuration created: agent_config.json" -ForegroundColor Green
    }
}

Write-Host "`n===========================================" -ForegroundColor Cyan
Write-Host "  Agent system execution completed" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Return to original directory
Set-Location -Path "..\.."