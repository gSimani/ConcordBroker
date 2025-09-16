# DETAILED STEP-BY-STEP SETUP INSTRUCTIONS

## Current Location
You are in: `C:\Users\gsima\Documents\MyProject\ConcordBroker\`

## Files Created and Their Locations

### 🔍 Finding Your Files:

1. **SQL Optimization File**: 
   - **Location**: `C:\Users\gsima\Documents\MyProject\ConcordBroker\optimize_database_complete.sql`
   - **How to find it**: It's in your main project folder

2. **Agent Startup Script**:
   - **Location**: `C:\Users\gsima\Documents\MyProject\ConcordBroker\start_florida_agents.ps1`
   - **How to find it**: It's in your main project folder

3. **Master Agent System**:
   - **Location**: `C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\workers\florida_master_agent.py`
   - **How to find it**: Navigate to `apps\workers\` folder

---

## 📋 STEP-BY-STEP INSTRUCTIONS

### STEP 1: Run Database Optimization (MOST IMPORTANT - DO THIS FIRST!)

#### 1A. Open the SQL file:
```powershell
# In PowerShell, type:
notepad optimize_database_complete.sql

# OR just navigate to your folder and double-click the file
```

#### 1B. Copy all the SQL code:
- Press `Ctrl+A` to select all
- Press `Ctrl+C` to copy

#### 1C. Open Supabase SQL Editor:
1. Go to: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql
2. Login if needed
3. Click the **"+ New query"** button (top of the page)

#### 1D. Paste and run the SQL:
1. Click in the query editor
2. Press `Ctrl+V` to paste
3. Click the **"RUN"** button (or press `Ctrl+Enter`)

#### 1E. What you should see:
- Multiple "CREATE INDEX" success messages
- "CREATE MATERIALIZED VIEW" success
- Final message: "DATABASE OPTIMIZATION COMPLETE!"
- This will take 1-2 minutes to complete

#### 1F. Verify it worked:
Run this test query in a new SQL tab:
```sql
SELECT * FROM property_search_fast LIMIT 5;
```
You should see 5 property records instantly.

---

### STEP 2: Install Dependencies for Data Agents

#### 2A. Open PowerShell as Administrator:
1. Right-click on Start Menu
2. Select "Windows PowerShell (Admin)"

#### 2B. Navigate to your project:
```powershell
cd C:\Users\gsima\Documents\MyProject\ConcordBroker
```

#### 2C. Install Python packages:
```powershell
# This installs all required packages
.\start_florida_agents.ps1 -InstallDependencies
```

You should see:
- "Installing dependencies..."
- Package installations
- "Dependencies installed successfully!"

If you get an error about execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### STEP 3: Create Database Tables for Agents

#### 3A. Generate the SQL:
```powershell
.\start_florida_agents.ps1 -CreateDatabase
```

This creates: `create_agent_tables.sql`

#### 3B. Run in Supabase:
1. Open the file: `notepad create_agent_tables.sql`
2. Copy all content
3. Go to Supabase SQL Editor
4. Create new query
5. Paste and RUN

---

### STEP 4: Download Missing Data

#### 4A. Test the agent system first:
```powershell
# This checks if everything is configured correctly
.\start_florida_agents.ps1 -Mode test
```

You should see:
- "Testing florida_revenue..."
- "Testing sunbiz..."
- "Testing broward_daily..."

#### 4B. Run data download (ONE TIME):
```powershell
# This downloads all missing data
.\start_florida_agents.ps1 -Mode once
```

**IMPORTANT**: This will:
- Download SDF sales data (may take 5-10 minutes)
- Download NAV/NAP assessment data
- Connect to Sunbiz SFTP and download business entities
- Download Broward daily index

You'll see progress like:
```
Downloading NAL...
  ✓ Downloaded NAL: 125.34 MB
  Processing NAL...
    Loaded 10000 NAL records

Downloading SDF...
  ✓ Downloaded SDF: 89.12 MB
  Processing SDF...
    Loaded 10000 SDF records
```

#### 4C. If downloads fail:
Try individual agents:
```powershell
# Download only Florida Revenue data
.\start_florida_agents.ps1 -Mode once -Agent florida_revenue

# Download only Sunbiz data
.\start_florida_agents.ps1 -Mode once -Agent sunbiz

# Download only Broward data
.\start_florida_agents.ps1 -Mode once -Agent broward_daily
```

---

### STEP 5: Start Continuous Monitoring (OPTIONAL - After testing)

#### 5A. Start the monitoring system:
```powershell
# This runs continuously and checks for updates
.\start_florida_agents.ps1 -Mode continuous
```

**NOTE**: 
- This runs forever until you stop it with `Ctrl+C`
- It checks hourly for new data
- Downloads updates automatically
- Best to run in a separate PowerShell window

#### 5B. Check agent status:
```powershell
# In a new PowerShell window
.\start_florida_agents.ps1 -Mode status
```

This shows:
- Last check time for each agent
- Files found/downloaded
- Any errors

---

### STEP 6: Verify Everything Works

#### 6A. Check database in Supabase:
Go to Table Editor: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/editor

You should see:
- `florida_parcels`: 789,884 rows ✓
- `property_sales_history`: 10,000+ rows (after download)
- `nav_assessments`: 10,000+ rows (after download)
- `sunbiz_corporate`: 1,000+ rows (after download)
- `property_search_fast`: Materialized view with data

#### 6B. Test a search query:
In SQL Editor, run:
```sql
-- Test the search function
SELECT * FROM search_properties('main street', 10, 0);

-- Should return properties instantly
```

#### 6C. Test your website:
1. Start your local server:
```powershell
cd apps\web
npm run dev
```

2. Go to: http://localhost:5173/properties

3. Search for a property - should be FAST now!

---

## 🔧 TROUBLESHOOTING

### If SQL optimization fails:
- Error: "already exists" - It's OK, indexes were already created
- Error: "permission denied" - Make sure you're using the service role key
- Takes too long - Normal for 789K records, wait 2-3 minutes

### If agent downloads fail:
- Check internet connection
- Try running individual agents (Step 4C)
- Check `florida_agent_system.log` for errors

### If website is still slow:
1. Make sure you ran the optimization SQL (Step 1)
2. Check if materialized view was created:
```sql
SELECT * FROM property_search_fast LIMIT 1;
```
3. Refresh the materialized view:
```sql
REFRESH MATERIALIZED VIEW property_search_fast;
```

### If PowerShell scripts won't run:
```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
```

---

## ✅ SUCCESS CHECKLIST

After completing all steps, verify:

- [ ] Optimization SQL ran successfully
- [ ] `property_search_fast` view exists
- [ ] Search function works (`search_properties`)
- [ ] Agent dependencies installed
- [ ] Agent tables created
- [ ] Data downloaded (at least once)
- [ ] Website searches are fast (<1 second)
- [ ] Property profiles load completely

---

## 📊 EXPECTED RESULTS

After everything is set up:

1. **Search Performance**: 
   - Before: 5-10 seconds
   - After: <100 milliseconds

2. **Data Completeness**:
   - Sales history: Populated
   - Tax assessments: Populated
   - Business entities: Populated

3. **Automatic Updates**:
   - Daily: Sales data (SDF)
   - Weekly: Property data (NAL)
   - Daily: Sunbiz entities

---

## 🚀 QUICK COMMANDS REFERENCE

```powershell
# From C:\Users\gsima\Documents\MyProject\ConcordBroker\

# Install dependencies
.\start_florida_agents.ps1 -InstallDependencies

# Create database tables
.\start_florida_agents.ps1 -CreateDatabase

# Download all data once
.\start_florida_agents.ps1 -Mode once

# Start continuous monitoring
.\start_florida_agents.ps1 -Mode continuous

# Check status
.\start_florida_agents.ps1 -Mode status

# Test individual agents
.\start_florida_agents.ps1 -Mode test
```

---

## 📞 NEXT STEPS

Once everything is working:

1. **Schedule automatic updates** (Windows Task Scheduler)
2. **Monitor data quality** (check agent_monitoring table)
3. **Optimize further** if needed (add more specific indexes)
4. **Deploy to production** when ready

The system is now ready for production use with fast, accurate, and automatically updated Florida property data!