# Florida Data Agent System - Complete Architecture

## Executive Summary

This document defines the complete agent-based monitoring system for all Florida property data sources. The system automatically detects, downloads, and processes data from multiple sources, ensuring your database always has the latest information.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   MASTER ORCHESTRATOR                        │
│                 (florida_orchestrator.py)                    │
└─────────────┬───────────────────────────────────┬───────────┘
              │                                   │
    ┌─────────▼──────────┐              ┌────────▼──────────┐
    │  MONITORING AGENT   │              │  DOWNLOAD AGENT   │
    │   (Detects Updates) │              │  (Fetches Files)  │
    └─────────┬──────────┘              └────────┬──────────┘
              │                                   │
    ┌─────────▼──────────────────────────────────▼──────────┐
    │                   PROCESSING AGENT                     │
    │              (Transforms & Validates Data)             │
    └─────────────────────────┬──────────────────────────────┘
                              │
    ┌─────────────────────────▼──────────────────────────────┐
    │                    SUPABASE LOADER                      │
    │                 (Inserts/Updates Database)              │
    └──────────────────────────────────────────────────────────┘
```

## Data Sources & Agents

### 1. Florida Revenue Data Portal Agent

**Source**: https://floridarevenue.com/property/dataportal/

**Monitored Directories**:
- `/Tax%20Roll%20Data%20Files/NAL/[YEAR]/` - Name/Address/Legal
- `/Tax%20Roll%20Data%20Files/NAP/[YEAR]/` - Non-Ad Valorem Parcel
- `/Tax%20Roll%20Data%20Files/NAV/[YEAR]/NAV%20D/` - Assessment Detail
- `/Tax%20Roll%20Data%20Files/NAV/[YEAR]/NAV%20N/` - Assessment Summary
- `/Tax%20Roll%20Data%20Files/SDF/[YEAR]/` - Sales Data File
- `/Tax%20Roll%20Data%20Files/TPP/[YEAR]/` - Tangible Personal Property
- `/Map%20Data/` - GIS and mapping data

**Key Features**:
- Dynamic year detection (2024F, 2025P, etc.)
- County-specific file identification (16 = Broward)
- Automatic detection of new folders/periods

### 2. Sunbiz SFTP Agent

**Connection**:
```
Host: sftp.floridados.gov
Username: Public
Password: PubAccess1845!
Port: 22
```

**Monitored Directories**:
- `/` - Main business entity data
- `/daily/` - Daily updates
- `/quarterly/` - Quarterly snapshots

**Download Schedule**:
- Main data: Weekly (Sundays)
- Daily updates: Every morning at 2 AM
- Quarterly: First day of each quarter

### 3. Broward County Daily Index Agent

**Source**: https://www.broward.org/RecordsTaxesTreasury/Records/

**Files**:
- Daily index extract files
- Official records
- Property transactions

**Processing**:
- Parse according to ExportFilesLayout.pdf
- Extract property transfers, liens, mortgages
- Link to parcel IDs

### 4. Statewide Cadastral Agent

**Sources**:
- ArcGIS: https://services9.arcgis.com/Gh9awoU677aKree0/
- GeoData: https://geodata.floridagio.gov/

**Data Types**:
- Parcel boundaries
- County boundaries
- Flood zones
- School districts
- Zoning information

## Agent Implementation

### Core Agent Classes

```python
# Base Agent Class
class FloridaDataAgent:
    def __init__(self, source_name, config):
        self.source = source_name
        self.config = config
        self.supabase = self.init_supabase()
        self.last_check = None
        self.new_files = []
    
    def monitor(self):
        """Check for new/updated files"""
        pass
    
    def download(self, file_info):
        """Download specific file"""
        pass
    
    def process(self, file_path):
        """Process downloaded file"""
        pass
    
    def load(self, data):
        """Load to Supabase"""
        pass
```

### Florida Revenue Agent

```python
class FloridaRevenueAgent(FloridaDataAgent):
    BASE_URL = "https://floridarevenue.com/property/dataportal/"
    
    def __init__(self):
        super().__init__("Florida Revenue", config)
        self.data_types = ['NAL', 'NAP', 'NAV', 'SDF', 'TPP']
        self.current_year = self.detect_current_year()
    
    def detect_current_year(self):
        """Dynamically detect current data year/period"""
        # Check for patterns like 2024F, 2025P, TAX_ROLL_2024
        patterns = [
            f"{datetime.now().year}P",  # Preliminary
            f"{datetime.now().year}F",  # Final
            f"TAX_ROLL_{datetime.now().year}"
        ]
        # Test each pattern to find valid directories
        return self.probe_directories(patterns)
    
    def monitor_directory(self, data_type, year):
        """Monitor specific data type directory"""
        if data_type == 'NAV':
            # NAV has subdirectories
            urls = [
                f"/Tax%20Roll%20Data%20Files/NAV/{year}/NAV%20D/",
                f"/Tax%20Roll%20Data%20Files/NAV/{year}/NAV%20N/"
            ]
        else:
            urls = [f"/Tax%20Roll%20Data%20Files/{data_type}/{year}/"]
        
        for url in urls:
            files = self.list_files(url)
            new = self.detect_new_files(files)
            if new:
                self.queue_downloads(new)
```

### Sunbiz SFTP Agent

```python
class SunbizAgent(FloridaDataAgent):
    def __init__(self):
        super().__init__("Sunbiz", config)
        self.sftp = self.init_sftp()
    
    def init_sftp(self):
        """Initialize SFTP connection"""
        import paramiko
        
        transport = paramiko.Transport(("sftp.floridados.gov", 22))
        transport.connect(username="Public", password="PubAccess1845!")
        return paramiko.SFTPClient.from_transport(transport)
    
    def download_main_data(self):
        """Download complete business entity dataset"""
        files = [
            'corpfilecopy.txt',    # Corporations
            'llcfilecopy.txt',     # LLCs
            'lpfilecopy.txt',      # Limited Partnerships
            'ficfilecopy.txt',     # Fictitious names
            'officefilecopy.txt'   # Officers/Directors
        ]
        
        for file in files:
            local_path = f"data/sunbiz/{file}"
            self.sftp.get(file, local_path)
            self.process_sunbiz_file(local_path)
    
    def process_sunbiz_file(self, file_path):
        """Process Sunbiz fixed-width format files"""
        # Parse according to Sunbiz documentation
        # Load to sunbiz_corporate table
        pass
```

### Broward Daily Index Agent

```python
class BrowardDailyAgent(FloridaDataAgent):
    def __init__(self):
        super().__init__("Broward Daily", config)
        self.base_url = "https://www.broward.org/RecordsTaxesTreasury/"
    
    def download_daily_index(self):
        """Download today's index file"""
        today = datetime.now().strftime("%Y%m%d")
        url = f"{self.base_url}/Records/DailyIndex/DailyIndex_{today}.csv"
        
        response = requests.get(url)
        if response.status_code == 200:
            self.process_daily_index(response.content)
    
    def process_daily_index(self, content):
        """Process daily index according to layout spec"""
        # Parse CSV according to ExportFilesLayout.pdf
        df = pd.read_csv(io.StringIO(content))
        
        # Extract relevant transactions
        property_transfers = df[df['DOCUMENT_TYPE'] == 'DEED']
        
        # Load to database
        self.load_to_supabase('broward_daily_index', property_transfers)
```

## Master Orchestrator

```python
class FloridaMasterOrchestrator:
    def __init__(self):
        self.agents = [
            FloridaRevenueAgent(),
            SunbizAgent(),
            BrowardDailyAgent(),
            CadastralAgent(),
            GeoDataAgent()
        ]
        self.scheduler = self.init_scheduler()
    
    def init_scheduler(self):
        """Initialize schedule for all agents"""
        schedule = {
            'florida_revenue': {
                'NAL': 'weekly',  # Monday 3 AM
                'SDF': 'daily',   # 4 AM
                'NAV': 'weekly',  # Tuesday 3 AM
                'NAP': 'weekly',  # Wednesday 3 AM
            },
            'sunbiz': {
                'main': 'weekly',     # Sunday 2 AM
                'daily': 'daily',     # 2 AM
                'quarterly': 'quarterly'  # First of quarter
            },
            'broward': {
                'daily_index': 'daily'  # 6 AM
            }
        }
        return schedule
    
    def run(self):
        """Main orchestration loop"""
        while True:
            for agent in self.agents:
                if self.should_run(agent):
                    try:
                        agent.monitor()
                        agent.download_new_files()
                        agent.process_downloads()
                        agent.load_to_database()
                        self.log_success(agent)
                    except Exception as e:
                        self.handle_error(agent, e)
            
            time.sleep(3600)  # Check every hour
```

## Database Schema Updates

```sql
-- Florida Revenue data tables
CREATE TABLE IF NOT EXISTS florida_nal (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    county_code VARCHAR(10),
    year INTEGER,
    owner_name TEXT,
    owner_addr1 TEXT,
    owner_city VARCHAR(100),
    phy_addr1 TEXT,
    phy_city VARCHAR(100),
    -- All NAL fields from user guide
    data_source VARCHAR(50),
    import_date TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS florida_sdf (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    sale_date DATE,
    sale_price NUMERIC,
    vi_code VARCHAR(10),
    qualified_sale BOOLEAN,
    -- All SDF fields
    data_source VARCHAR(50),
    import_date TIMESTAMP DEFAULT NOW()
);

-- Sunbiz business entities
CREATE TABLE IF NOT EXISTS sunbiz_entities (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(50) UNIQUE,
    corporate_name TEXT,
    entity_type VARCHAR(100),
    status VARCHAR(50),
    filing_date DATE,
    principal_address TEXT,
    officers JSONB,
    -- All Sunbiz fields
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Broward daily index
CREATE TABLE IF NOT EXISTS broward_daily_index (
    id SERIAL PRIMARY KEY,
    record_date DATE,
    document_type VARCHAR(50),
    book INTEGER,
    page INTEGER,
    parcel_id VARCHAR(50),
    grantor TEXT,
    grantee TEXT,
    -- All daily index fields
    import_date TIMESTAMP DEFAULT NOW()
);

-- Agent monitoring table
CREATE TABLE IF NOT EXISTS agent_monitoring (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100),
    source_url TEXT,
    last_check TIMESTAMP,
    files_found INTEGER,
    files_downloaded INTEGER,
    files_processed INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    next_scheduled_run TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_nal_parcel ON florida_nal(parcel_id);
CREATE INDEX idx_sdf_parcel ON florida_sdf(parcel_id);
CREATE INDEX idx_sdf_date ON florida_sdf(sale_date);
CREATE INDEX idx_sunbiz_name ON sunbiz_entities(corporate_name);
CREATE INDEX idx_broward_parcel ON broward_daily_index(parcel_id);
```

## Deployment Configuration

### Environment Variables
```env
# Florida Revenue
FLORIDA_REVENUE_BASE_URL=https://floridarevenue.com/property/dataportal/

# Sunbiz SFTP
SUNBIZ_SFTP_HOST=sftp.floridados.gov
SUNBIZ_SFTP_USER=Public
SUNBIZ_SFTP_PASS=PubAccess1845!

# Broward County
BROWARD_BASE_URL=https://www.broward.org/RecordsTaxesTreasury/

# ArcGIS
ARCGIS_BASE_URL=https://services9.arcgis.com/Gh9awoU677aKree0/

# GeoData
GEODATA_BASE_URL=https://geodata.floridagio.gov/

# Supabase
SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# Monitoring
ALERT_EMAIL=admin@concordbroker.com
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK
```

### Scheduling (cron format)
```yaml
schedules:
  florida_revenue:
    NAL: "0 3 * * 1"  # Monday 3 AM
    SDF: "0 4 * * *"  # Daily 4 AM
    NAV: "0 3 * * 2"  # Tuesday 3 AM
    NAP: "0 3 * * 3"  # Wednesday 3 AM
    TPP: "0 3 * * 4"  # Thursday 3 AM
  
  sunbiz:
    main: "0 2 * * 0"     # Sunday 2 AM
    daily: "0 2 * * *"    # Daily 2 AM
    quarterly: "0 2 1 */3 *"  # First day of quarter
  
  broward:
    daily_index: "0 6 * * *"  # Daily 6 AM
  
  cadastral:
    boundaries: "0 1 * * 0"  # Weekly Sunday 1 AM
  
  geodata:
    updates: "0 1 * * 1"  # Weekly Monday 1 AM
```

## Monitoring & Alerts

### Health Checks
- Agent status dashboard
- File download success rates
- Data processing metrics
- Database load statistics

### Alert Conditions
- New year/period folder detected
- Large file size changes (>20%)
- Failed downloads after retries
- Data validation errors
- Missing expected files

### Performance Metrics
- Download speed
- Processing time per file
- Database insert rates
- Storage usage trends

## Testing & Validation

### Unit Tests
```python
def test_year_detection():
    """Test dynamic year/period detection"""
    agent = FloridaRevenueAgent()
    year = agent.detect_current_year()
    assert year in ['2024F', '2025P', 'TAX_ROLL_2024']

def test_sunbiz_connection():
    """Test SFTP connection to Sunbiz"""
    agent = SunbizAgent()
    assert agent.sftp.listdir() is not None

def test_data_processing():
    """Test data transformation and validation"""
    processor = DataProcessor()
    sample_data = load_sample_nal_file()
    processed = processor.process_nal(sample_data)
    assert len(processed) > 0
```

## Maintenance & Operations

### Daily Tasks
- Review agent monitoring dashboard
- Check for failed downloads
- Verify data completeness

### Weekly Tasks
- Analyze new data patterns
- Update year/period detection if needed
- Review and clear old downloaded files

### Monthly Tasks
- Performance optimization review
- Database maintenance (VACUUM, ANALYZE)
- Storage cleanup

## Success Metrics

### Key Performance Indicators
- **Data Freshness**: <24 hours from source update
- **Completeness**: 100% of available files downloaded
- **Accuracy**: <0.1% data validation errors
- **Availability**: 99.9% agent uptime
- **Performance**: <5 minutes processing per file

### Business Value
- Always have latest property data
- Automatic detection of new opportunities
- Complete business entity matching
- Real-time market insights
- Reduced manual data management

## Next Steps

1. **Deploy agents** to production environment
2. **Configure scheduling** for optimal performance
3. **Setup monitoring** dashboards and alerts
4. **Run initial data load** for all sources
5. **Validate data** completeness and accuracy
6. **Train team** on monitoring and maintenance