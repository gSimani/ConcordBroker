# DOWNLOAD MISSING DATA COMMANDS
# Run these in PowerShell from the ConcordBroker directory

# 1. Navigate to project directory
cd C:\Users\gsima\Documents\MyProject\ConcordBroker

# 2. Install dependencies (if not done already)
.\start_florida_agents.ps1 -InstallDependencies

# 3. Download all missing data (SDF sales, NAV assessments, Sunbiz)
.\start_florida_agents.ps1 -Mode once

# If the above fails, try downloading each source individually:

# Download only Florida Revenue data (SDF, NAV, NAP)
.\start_florida_agents.ps1 -Mode once -Agent florida_revenue

# Download only Sunbiz data
.\start_florida_agents.ps1 -Mode once -Agent sunbiz

# Download only Broward daily index
.\start_florida_agents.ps1 -Mode once -Agent broward_daily

# 4. Check status after download
.\start_florida_agents.ps1 -Mode status

# 5. Start continuous monitoring (optional - runs forever)
# .\start_florida_agents.ps1 -Mode continuous