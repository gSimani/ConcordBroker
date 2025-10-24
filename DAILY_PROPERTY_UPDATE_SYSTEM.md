# Daily Property Update System - Complete Implementation Plan

## Executive Summary

**Objective**: Automated daily updates to Supabase database for Florida county property data
**Data Source**: https://floridarevenue.com/property/dataportal/
**Update Frequency**: Daily at 2:00 AM EST
**Counties Covered**: All 67 Florida counties
**Expected Changes**: Ownership changes, tax assessments, valuations, sales

## 🎯 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Florida Revenue Portal                    │
│  https://floridarevenue.com/property/dataportal/            │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              AI Monitoring & Download Agent                  │
│  • Detects file changes (checksums)                         │
│  • Downloads updated files (NAL, NAP, NAV, SDF)             │
│  • Validates file integrity                                 │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│             Change Detection & Processing                    │
│  • Identifies changed records (ownership, value, tax)       │
│  • Computes deltas from existing data                       │
│  • Generates change logs                                    │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              Supabase Database Update                        │
│  • Incremental upsert of changed records                    │
│  • Maintains historical data                                │
│  • Updates indexes and materialized views                   │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              Notification & Reporting                        │
│  • Email alerts for significant changes                     │
│  • Daily update summary dashboard                           │
│  • Error notifications                                      │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Current State Analysis

### Database Status
**Finding**: Database is currently empty - NO TABLES EXIST
- ❌ florida_parcels - NOT FOUND
- ❌ property_sales_history - NOT FOUND
- ❌ florida_entities - NOT FOUND
- ❌ sunbiz_corporate - NOT FOUND
- ❌ tax_certificates - NOT FOUND
- ❌ property_assessments - NOT FOUND
- ❌ property_owners - NOT FOUND
- ❌ property_sales - NOT FOUND

**Action Required**: Initial database setup before implementing daily updates

### Data Source Analysis
**Florida Revenue Property Portal Structure**:
```
Tax Roll Data Files/
├── NAL/ (Name, Address, Legal description)
│   ├── 2025/
│   │   ├── ALACHUA_NAL_2025.txt
│   │   ├── BAKER_NAL_2025.txt
│   │   └── ... (67 counties)
├── NAP/ (Name, Address, Parcel)
│   └── 2025/
├── NAV/ (Non Ad Valorem assessments)
│   └── 2025/
└── SDF/ (Sales Data File)
    └── 2025/
```

**File Characteristics**:
- Format: Fixed-width text files
- Size: 10KB - 500MB per file (varies by county)
- Update Frequency: Daily (changes vary by county)
- Total Files: 268 files (67 counties × 4 file types)
- Total Data: ~9.7M properties estimated

### Access Method Analysis
**Challenge**: Files are NOT available via direct HTTP download
- ✅ Portal exists and is accessible
- ❌ No direct file URLs
- ❌ No public FTP server
- ⚠️  Requires authenticated session or manual download

**Solutions**:
1. Playwright/Selenium automated browser
2. Contact Florida DOR for API/FTP access
3. County-by-county downloads where available

## 🗄️ Database Schema Design

### Phase 1: Core Tables (REQUIRED BEFORE DAILY UPDATES)

#### 1. florida_parcels (Primary Property Table)
```sql
CREATE TABLE florida_parcels (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,

    -- Owner Information
    owner_name VARCHAR(500),
    owner_addr1 VARCHAR(255),
    owner_addr2 VARCHAR(255),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),

    -- Property Location
    phy_addr1 VARCHAR(255),
    phy_addr2 VARCHAR(255),
    city VARCHAR(100),
    zip_code VARCHAR(10),

    -- Valuation
    just_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    land_value DECIMAL(15,2),
    building_value DECIMAL(15,2),
    land_sqft DECIMAL(15,2),

    -- Property Details
    dor_uc VARCHAR(10),  -- Property use code
    property_use VARCHAR(100),
    year_built INTEGER,
    bedrooms INTEGER,
    bathrooms INTEGER,

    -- Metadata
    data_source VARCHAR(20) DEFAULT 'NAL',
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT unique_parcel_year UNIQUE(parcel_id, county, year)
);

-- Critical indexes for performance
CREATE INDEX idx_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX idx_county ON florida_parcels(county);
CREATE INDEX idx_owner_name ON florida_parcels(owner_name);
CREATE INDEX idx_property_city ON florida_parcels(city);
CREATE INDEX idx_last_updated ON florida_parcels(last_updated DESC);
```

#### 2. property_sales_history
```sql
CREATE TABLE property_sales_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,

    -- Sale Details
    sale_date DATE,
    sale_price DECIMAL(15,2),
    sale_type VARCHAR(50),

    -- Parties
    seller_name VARCHAR(500),
    buyer_name VARCHAR(500),

    -- Recording
    deed_book VARCHAR(50),
    deed_page VARCHAR(50),
    or_book VARCHAR(50),  -- Official Record Book
    or_page VARCHAR(50),  -- Official Record Page

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_sale UNIQUE(parcel_id, county, sale_date, or_book, or_page)
);

CREATE INDEX idx_sale_parcel ON property_sales_history(parcel_id);
CREATE INDEX idx_sale_date ON property_sales_history(sale_date DESC);
CREATE INDEX idx_sale_price ON property_sales_history(sale_price);
```

#### 3. property_change_log (NEW - for tracking daily changes)
```sql
CREATE TABLE property_change_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,
    change_date DATE NOT NULL,
    change_type VARCHAR(50) NOT NULL,  -- OWNERSHIP, VALUE, TAX, SALE, ADDRESS

    -- Change details (JSONB for flexibility)
    old_value JSONB,
    new_value JSONB,
    change_summary TEXT,

    -- Metadata
    detected_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,

    CONSTRAINT idx_change_date ON property_change_log(change_date DESC)
);

CREATE INDEX idx_change_parcel ON property_change_log(parcel_id);
CREATE INDEX idx_change_type ON property_change_log(change_type);
CREATE INDEX idx_change_processed ON property_change_log(processed);
```

#### 4. data_update_jobs (NEW - for monitoring daily updates)
```sql
CREATE TABLE data_update_jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    job_date DATE NOT NULL,
    county VARCHAR(50),
    file_type VARCHAR(10),  -- NAL, NAP, NAV, SDF

    -- Job Status
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, RUNNING, COMPLETED, FAILED
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Results
    records_processed INTEGER DEFAULT 0,
    records_changed INTEGER DEFAULT 0,
    records_new INTEGER DEFAULT 0,
    records_error INTEGER DEFAULT 0,
    error_message TEXT,

    -- File info
    file_url TEXT,
    file_checksum VARCHAR(64),
    file_size_bytes BIGINT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_job_date ON data_update_jobs(job_date DESC);
CREATE INDEX idx_job_status ON data_update_jobs(status);
CREATE INDEX idx_job_county ON data_update_jobs(county);
```

## 🤖 AI Agent System Design

### Agent 1: File Monitor Agent
**Purpose**: Monitors Florida Revenue portal for file changes
**Schedule**: Every 6 hours (02:00, 08:00, 14:00, 20:00 EST)

**Responsibilities**:
1. Navigate to Florida Revenue portal
2. List all NAL/NAP/NAV/SDF files for all 67 counties
3. Compute file checksums (or compare timestamps)
4. Detect changes from last check
5. Create download queue for changed files
6. Log monitoring results to data_update_jobs table

**Technology Stack**:
- Playwright for browser automation
- Python for scripting
- LangChain for agent orchestration
- Supabase for logging

**Key Features**:
- Retry logic for network failures
- Checksum-based change detection
- Priority queue (critical counties first)
- Alert system for major changes

### Agent 2: Data Download Agent
**Purpose**: Downloads changed files from portal
**Trigger**: On-demand when File Monitor detects changes

**Responsibilities**:
1. Process download queue from File Monitor
2. Authenticate to portal (if required)
3. Download files to staging area
4. Validate file integrity (checksum, format)
5. Store raw files for audit trail
6. Trigger Data Processing Agent

**Storage Structure**:
```
data/raw/
├── 2025-10-24/
│   ├── BROWARD_NAL_2025.txt
│   ├── MIAMI-DADE_NAL_2025.txt
│   └── checksums.json
├── 2025-10-25/
│   └── ...
```

### Agent 3: Change Detection Agent
**Purpose**: Identifies changed records from new files
**Trigger**: After successful file download

**Responsibilities**:
1. Parse downloaded files (NAL/NAP/NAV/SDF format)
2. Compare with existing database records
3. Identify changes:
   - Ownership changes (owner_name, owner_address)
   - Value changes (just_value, assessed_value, taxable_value)
   - Property changes (address, use code, characteristics)
   - Tax changes (from NAV files)
   - Sale records (from SDF files)
4. Generate change records for property_change_log
5. Create update batches

**Change Detection Logic**:
```python
def detect_changes(old_record, new_record):
    changes = []

    # Ownership change
    if old_record['owner_name'] != new_record['owner_name']:
        changes.append({
            'type': 'OWNERSHIP',
            'old_value': old_record['owner_name'],
            'new_value': new_record['owner_name'],
            'summary': f"Owner changed from {old_record['owner_name']} to {new_record['owner_name']}"
        })

    # Value change (>5% threshold)
    old_value = old_record['just_value']
    new_value = new_record['just_value']
    if abs(new_value - old_value) / old_value > 0.05:
        changes.append({
            'type': 'VALUE',
            'old_value': old_value,
            'new_value': new_value,
            'summary': f"Just value changed by {((new_value - old_value) / old_value * 100):.1f}%"
        })

    return changes
```

### Agent 4: Database Update Agent
**Purpose**: Applies detected changes to Supabase
**Trigger**: After change detection completes

**Responsibilities**:
1. Batch update records (1000 records per batch)
2. Use upsert strategy (insert new, update existing)
3. Maintain historical data
4. Update property_change_log
5. Refresh materialized views and indexes
6. Mark job as COMPLETED

**Update Strategy**:
```python
async def update_database(changes, batch_size=1000):
    for i in range(0, len(changes), batch_size):
        batch = changes[i:i+batch_size]

        # Upsert to florida_parcels
        await supabase.table('florida_parcels').upsert(
            batch,
            on_conflict='parcel_id,county,year'
        ).execute()

        # Log changes
        change_logs = [create_change_log(c) for c in batch]
        await supabase.table('property_change_log').insert(
            change_logs
        ).execute()
```

### Agent 5: Notification Agent
**Purpose**: Alerts users of significant changes
**Trigger**: After database update completes

**Responsibilities**:
1. Generate daily update summary
2. Identify significant changes:
   - High-value ownership transfers (>$1M)
   - Major value changes (>20%)
   - Large batch updates
3. Send email notifications
4. Update dashboard metrics
5. Create weekly/monthly reports

**Notification Types**:
- **Critical**: Errors, failed updates
- **High**: Ownership changes for tracked properties
- **Medium**: Value changes >20%
- **Low**: Routine daily summary

## 📅 Scheduler Implementation

### Option 1: Node-Cron (Simple, In-Process)
```javascript
// .claude/scheduler.cjs
const cron = require('node-cron');
const { exec } = require('child_process');

// Daily update at 2:00 AM EST
cron.schedule('0 2 * * *', () => {
    console.log('[SCHEDULER] Starting daily property update...');
    exec('python scripts/daily_property_update.py', (error, stdout, stderr) => {
        if (error) {
            console.error(`[SCHEDULER] Error: ${error}`);
            return;
        }
        console.log(`[SCHEDULER] Output: ${stdout}`);
    });
}, {
    timezone: "America/New_York"
});

// File monitor every 6 hours
cron.schedule('0 */6 * * *', () => {
    console.log('[SCHEDULER] Running file monitor...');
    exec('python scripts/monitor_file_changes.py', (error, stdout, stderr) => {
        if (error) {
            console.error(`[SCHEDULER] Error: ${error}`);
            return;
        }
        console.log(`[SCHEDULER] Output: ${stdout}`);
    });
}, {
    timezone: "America/New_York"
});

console.log('[SCHEDULER] Property update scheduler started');
console.log('[SCHEDULER] Daily updates: 2:00 AM EST');
console.log('[SCHEDULER] File monitoring: Every 6 hours');
```

### Option 2: GitHub Actions (Cloud-Based)
```yaml
# .github/workflows/daily-property-update.yml
name: Daily Property Update

on:
  schedule:
    # Run at 2:00 AM EST (7:00 AM UTC) every day
    - cron: '0 7 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  update-properties:
    runs-on: ubuntu-latest
    timeout-minutes: 180  # 3 hours max

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run property update
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
        run: |
          python scripts/daily_property_update.py

      - name: Send notification
        if: failure()
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.EMAIL_USERNAME }}
          password: ${{ secrets.EMAIL_PASSWORD }}
          subject: 'Property Update Failed'
          body: 'Daily property update failed. Check GitHub Actions logs.'
          to: admin@concordbroker.com
```

### Option 3: Railway Deployment (Dedicated Service)
```dockerfile
# Dockerfile.property-updater
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/
COPY .env.mcp .env

# Install cron
RUN apt-get update && apt-get install -y cron

# Add cron job
RUN echo "0 2 * * * cd /app && python scripts/daily_property_update.py >> /var/log/cron.log 2>&1" | crontab -

CMD ["cron", "-f"]
```

## 🔄 Daily Update Workflow

### Step-by-Step Process

**02:00 AM EST - File Monitor Agent**
```
1. Wake up and log start time
2. Navigate to Florida Revenue portal
3. For each county:
   a. Check NAL file (timestamp/checksum)
   b. Check NAP file
   c. Check NAV file
   d. Check SDF file
4. Compare with last known state
5. Create download queue for changed files
6. Log results to data_update_jobs
```

**02:15 AM EST - Data Download Agent**
```
1. Read download queue
2. For each file in queue:
   a. Download file to staging
   b. Validate checksum
   c. Store in data/raw/YYYY-MM-DD/
3. Mark files as ready for processing
```

**02:30 AM EST - Change Detection Agent**
```
1. Read downloaded files
2. Parse records (NAL/NAP/NAV/SDF)
3. For each record:
   a. Lookup existing record in database
   b. Compare fields
   c. Identify changes
   d. Create change record
4. Generate change batches
```

**03:00 AM EST - Database Update Agent**
```
1. Process change batches
2. For each batch (1000 records):
   a. Upsert to florida_parcels
   b. Insert to property_change_log
   c. Update related tables
3. Refresh materialized views
4. Update statistics
```

**04:00 AM EST - Notification Agent**
```
1. Query daily changes
2. Generate summary report
3. Identify significant changes
4. Send email notifications
5. Update dashboard
```

## 📈 Monitoring & Observability

### Key Metrics
- **Update Success Rate**: Target >99%
- **Processing Time**: Target <2 hours
- **Change Detection Rate**: Expected 0.1% - 1% daily
- **Error Rate**: Target <0.1%

### Dashboard Components
```
┌───────────────────────────────────────┐
│      Daily Update Dashboard           │
├───────────────────────────────────────┤
│  Last Update: 2025-10-24 04:15 AM    │
│  Status: ✅ COMPLETED                 │
│  Duration: 1h 45m                     │
├───────────────────────────────────────┤
│  📊 Records Processed: 15,234         │
│  🔄 Records Changed: 1,523            │
│  ➕ Records New: 45                   │
│  ❌ Records Error: 2                  │
├───────────────────────────────────────┤
│  🏠 Ownership Changes: 234            │
│  💰 Value Changes: 1,123              │
│  📍 Address Changes: 89               │
│  🏷️ Tax Changes: 77                   │
├───────────────────────────────────────┤
│  Counties Processed: 67 / 67         │
│  Files Downloaded: 268 / 268         │
│  Total Data Size: 1.2 GB             │
└───────────────────────────────────────┘
```

### Alerting Rules
```yaml
alerts:
  - name: update_failed
    condition: status == 'FAILED'
    severity: critical
    action: email + slack

  - name: high_error_rate
    condition: error_rate > 5%
    severity: high
    action: email

  - name: long_duration
    condition: duration > 3 hours
    severity: medium
    action: slack

  - name: large_change_volume
    condition: records_changed > 50000
    severity: medium
    action: email
```

## 🚀 Implementation Phases

### Phase 0: Initial Setup (CURRENT) - 1 Week
- [x] Audit database (completed)
- [ ] Deploy database schema
- [ ] Set up staging environment
- [ ] Create initial data load scripts

### Phase 1: Core Infrastructure - 2 Weeks
- [ ] Implement File Monitor Agent
- [ ] Implement Data Download Agent
- [ ] Create file parsing utilities
- [ ] Set up local testing environment

### Phase 2: Change Detection - 2 Weeks
- [ ] Implement Change Detection Agent
- [ ] Create comparison algorithms
- [ ] Build change log system
- [ ] Test with sample data

### Phase 3: Database Updates - 1 Week
- [ ] Implement Database Update Agent
- [ ] Optimize batch processing
- [ ] Add transaction management
- [ ] Performance testing

### Phase 4: Scheduler & Automation - 1 Week
- [ ] Set up scheduler (GitHub Actions)
- [ ] Implement Notification Agent
- [ ] Create monitoring dashboard
- [ ] End-to-end testing

### Phase 5: Production Deployment - 1 Week
- [ ] Deploy to production
- [ ] Monitor first week of updates
- [ ] Fine-tune performance
- [ ] Documentation and training

## 🔐 Security Considerations

1. **API Keys & Credentials**
   - Store in GitHub Secrets (for GitHub Actions)
   - Use environment variables
   - Never commit to git

2. **Database Access**
   - Use Supabase Service Role Key for updates
   - Implement Row Level Security (RLS)
   - Audit all write operations

3. **File Downloads**
   - Validate file checksums
   - Scan for malware
   - Store in secure location

4. **Data Privacy**
   - Comply with public records laws
   - Implement data retention policies
   - Log all access

## 📝 Next Immediate Steps

1. **Deploy Database Schema** (TODAY)
   ```bash
   psql $DATABASE_URL -f property_appraiser_schema.sql
   ```

2. **Create File Monitor Agent** (THIS WEEK)
   ```bash
   python scripts/create_file_monitor_agent.py
   ```

3. **Test with Single County** (THIS WEEK)
   ```bash
   python scripts/test_broward_update.py
   ```

4. **Set Up GitHub Actions** (NEXT WEEK)
   ```bash
   cp .github/workflows/daily-property-update.yml.example .github/workflows/daily-property-update.yml
   ```

## 📚 Additional Resources

- Florida Revenue Data Portal: https://floridarevenue.com/property/dataportal/
- Supabase Documentation: https://supabase.com/docs
- LangChain Agents: https://python.langchain.com/docs/modules/agents/
- Playwright Automation: https://playwright.dev/python/

---

**Status**: READY FOR IMPLEMENTATION
**Priority**: HIGH
**Estimated Timeline**: 8 weeks to full production
**Created**: 2025-10-24
**Last Updated**: 2025-10-24
