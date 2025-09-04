# ConcordBroker – PDR (Project Design & Runbook) v0.2 ENHANCED

**Owner:** Guy Simani  
**Repo:** https://github.com/gSimani/ConcordBroker  
**Local path:** C:\Users\gsima\Documents\MyProject\ConcordBroker  
**Date:** 2025-09-03 (Updated with Data Source Specifications)

This PDR is the single source of truth. All agents (Claude Code, etc.) must save and keep referencing this file. Every change must go through PRs against this document first.

## CRITICAL DATA SOURCE SPECIFICATIONS

### 🔴 PRIMARY DATA SOURCES - EXACT ACCESS METHODS

#### 1. Florida DOR (Department of Revenue) - Property Tax Data
**Access Method:** Email/Phone Request → Download Directory
- **Contact:** PTOTechnology@floridarevenue.com / 850-717-6570
- **Files:** NAL (Name-Address-Legal), SDF (Sale Data File)
- **Format:** Fixed-width text files (no headers)
- **County Code:** 16 (Broward County)
- **Release Schedule:**
  - July 1: Preliminary assessment rolls
  - October: Initial final assessment rolls
  - After VAB: Final rolls with Value Adjustment Board changes
- **Documentation:** https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/User%20Guides/2024%20Users%20guide%20and%20quick%20reference/2024_NAL_SDF_NAP_Users_Guide.pdf

**ETL Instructions:**
1. Request files via email with "Broward County NAL/SDF Request - County 16"
2. Files >10MB provided via temporary download link
3. Parse as fixed-width format per User Guide specifications
4. Store raw files in /data/raw/dor/YYYY-MM-DD/

#### 2. Florida Sunbiz - Corporate Entity Data
**SFTP Access:** CONFIRMED CREDENTIALS
- **Host:** sftp.floridados.gov
- **Username:** Public
- **Password:** PubAccess1845!
- **Directory Structure:**
  - /public/daily/ - Work day filings
  - /public/quarterly/ - Full dataset (Jan/Apr/Jul/Oct)
- **File Types:** 
  - CORDATA - Corporate entities (fixed-width)
  - Corporate Officers/Agents files
  - Event files for changes
- **Format:** Fixed-length text files, no headers
- **Documentation:** https://dos.fl.gov/sunbiz/other-services/data-downloads/data-usage-guide/

**ETL Instructions:**
1. Connect via SFTP using Paramiko/aioftp
2. Navigate from /public/ to appropriate directory
3. Download daily files every morning at 8:00 AM ET
4. Parse fixed-width format - trim whitespace
5. Document number (6-12 chars) is unique identifier
6. Store in /data/raw/sunbiz/YYYY-MM-DD/

#### 3. Broward County Official Records
**Status:** ⚠️ NO PUBLIC FTP CONFIRMED
**Alternative Access Methods:**
- **Web Portal:** https://officialrecords.broward.org/AcclaimWeb (1978-present)
- **Recording Notification Service:** Free email alerts for new recordings
- **Data Purchase:** Contact Records office for bulk export
- **Contact:** 954-357-5100

**Fallback Strategy:**
1. Use Playwright to scrape web portal daily
2. Monitor Recording Notification Service emails
3. Contact office for bulk data purchase arrangement
4. Parse HTML tables from web interface

#### 4. Broward County Property Appraiser (BCPA)
**Status:** ⚠️ NO PUBLIC API AVAILABLE
**Access Methods:**
- **Web Search:** https://web.bcpa.net/BcpaClient/
- **GIS Map:** https://gisweb-adapters.bcpa.net/bcpawebmap_ex/bcpawebmap.aspx
- **GeoHub:** https://geohub-bcgis.opendata.arcgis.com/ (BETA)
- **Data Purchase:** Contact 954-357-6830 for GIS/parcel data

**Web Scraping Strategy:**
1. Use Playwright to automate searches
2. Iterate through city + use code combinations
3. Parse result tables for folio numbers
4. Extract building cards/sketches via direct URLs
5. Cache results in /data/cache/bcpa/

### 🔴 MISSING DATA & GAPS IDENTIFIED

#### Critical Missing Fields:
1. **Phone Numbers:** Not in DOR/Sunbiz - need third-party enrichment
2. **Email Addresses:** Not in public records - need enrichment service
3. **Building Permits:** Separate system - need municipal access
4. **Code Violations:** Municipal data - varies by city
5. **Mortgage Details:** In OR but needs special parsing
6. **HOA Information:** Not in public records
7. **Insurance Claims:** Not publicly available

#### Data Enrichment Strategy:
1. **Contact Info:** Integrate with Clearbit/ZoomInfo API
2. **Property Details:** Cross-reference with Zillow/Redfin APIs
3. **Municipal Data:** Direct API requests to city systems
4. **Social Profiles:** LinkedIn Sales Navigator for officers

### 🔴 ENHANCED ETL PIPELINE SPECIFICATIONS

#### Pipeline Architecture:
```
┌─────────────────────────────────────────────────────┐
│                   ORCHESTRATOR                       │
│            (Airflow/Prefect on Railway)              │
└──────┬────────────┬────────────┬────────────┬───────┘
       │            │            │            │
   ┌───▼───┐   ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
   │  DOR  │   │SUNBIZ │   │  OR   │   │ BCPA  │
   │Loader │   │Loader │   │Scraper│   │Scraper│
   └───┬───┘   └───┬───┘   └───┬───┘   └───┬───┘
       │            │            │            │
   ┌───▼────────────▼────────────▼────────────▼───┐
   │          RAW DATA LAKE (S3/MinIO)            │
   └───────────────────┬───────────────────────────┘
                       │
   ┌───────────────────▼───────────────────────────┐
   │         TRANSFORMATION LAYER (DBT)            │
   │     - Deduplication                           │
   │     - Entity Resolution                       │
   │     - Address Normalization                   │
   │     - Score Calculation                       │
   └───────────────────┬───────────────────────────┘
                       │
   ┌───────────────────▼───────────────────────────┐
   │          SUPABASE (PostgreSQL)                │
   │     - Normalized Tables                       │
   │     - Materialized Views                      │
   │     - Vector Embeddings                       │
   └───────────────────────────────────────────────┘
```

## 0) Kickoff – Claude Code control prompts

### Prompt 0.1 — Save and pin the PDR
[Previous content remains]

### Prompt 0.2 — Repo bootstrapping
[Previous content remains]

## 1) Scope & Goals

**Goal:** Acquire Broward investment properties by automating data collection (DOR assessment roll + Broward Official Records + Sunbiz), normalizing owners/entities, scoring and surfacing candidates via a Vercel UI. Avoid brittle scraping; use Playwright fallback for gaps only.

**Primary Filters:** City (Broward list), Main Use (00–99 family), Sub-Use (e.g., Industrial→43 Lumber Yards).  
**Outputs:** Ranked property list with links (BCPA record, Google Maps, Building Card/Sketch, Instrument #), and contact graph (entity → officers/agents / phones/emails when available).

### Enhanced Data Collection Goals:
- **Real-time Updates:** Daily sync with all sources
- **Data Quality:** 99.9% accuracy through validation
- **Performance:** <5 min for daily updates
- **Completeness:** Enrich with third-party data

## 2) Architecture (Modern Full-Stack)

- **Frontend:** Vercel (Vite/React + Tailwind + shadcn)
- **Backend API:** FastAPI on Railway
- **Data Workers (ETL):** Railway cron containers (Python, Polars/DuckDB)
- **DB:** Supabase (Postgres + [pgvector])
- **Vector/RAG:** for docs/rules only (not parcel facts)
- **Auth/Verify:** Twilio Verify (SMS + Email/SendGrid)
- **Email:** Twilio SendGrid (domain verified)
- **CDN/Protection:** Cloudflare
- **Scraping Fallback:** Playwright MCP runners on Railway
- **Error Tracking:** Sentry (+ CodeCo if required)
- **Data Lake:** MinIO/S3 for raw file storage
- **Orchestration:** Prefect/Airflow for pipeline management
- **Data Quality:** Great Expectations for validation

### Data Sources (ENHANCED)
- **Florida DOR:** NAL/SDF via email request → parse fixed-width
- **Broward Official Records:** Web scraping (no FTP available)
- **Sunbiz:** SFTP bulk download (credentials confirmed)
- **BCPA:** Web scraping + GeoHub API exploration
- **Enrichment:** Clearbit, ZoomInfo, LinkedIn APIs

## 3) Security & Secrets (MANDATORY)

[Previous content remains]

## 4) Data Model (Supabase)

### 4.1 Core tables (ENHANCED)

Previous tables plus:
- `data_sources`(id, name, type, config, last_sync, status)
- `field_mappings`(source, source_field, target_table, target_field, transform)
- `data_quality_checks`(id, table_name, check_type, threshold, last_run, passed)
- `enrichment_queue`(id, folio, enrichment_type, status, attempts)

### 4.2 Indexing
[Previous content remains]

## 5) ETL Pipelines (Railway workers) - ENHANCED SPECIFICATIONS

### 5.1 DOR Assessment Roll Loader (NAL/SDF)

**Schedule:** Manual trigger + July 1, October, Post-VAB

**Detailed Implementation:**
```python
# NAL Field Mapping (positions from User Guide)
NAL_FIELDS = {
    'parcel_id': (1, 25),          # Unique identifier
    'county_code': (26, 28),       # Should be '16' for Broward
    'assessment_year': (29, 32),   # YYYY format
    'owner_name': (33, 113),       # 80 chars, trim whitespace
    'mailing_addr1': (114, 174),   # 60 chars
    'mailing_addr2': (175, 235),   # 60 chars
    'mailing_city': (236, 276),    # 40 chars
    'mailing_state': (277, 279),   # 2 chars
    'mailing_zip': (280, 289),     # 9 chars (5+4)
    'situs_addr1': (290, 350),     # Property address
    'situs_city': (351, 391),      
    'main_use_code': (392, 394),   # 00-99
    'sub_use_code': (395, 399),    # Detailed use
    'land_value': (400, 412),      # Right-aligned, implied decimal
    'building_value': (413, 425),
    'just_value': (426, 438),
    'assessed_value': (439, 451),
    'exemption_value': (452, 464),
    'taxable_value': (465, 477),
    'land_area_sf': (478, 490),
    'living_area': (491, 503),
    'effective_year': (504, 507),
    'actual_year': (508, 511),
    'bedroom_count': (512, 514),
    'bathroom_count': (515, 517),
    'units_count': (518, 522)
}

# SDF Field Mapping
SDF_FIELDS = {
    'parcel_id': (1, 25),
    'sale_date': (26, 33),         # YYYYMMDD
    'sale_price': (34, 46),        # Right-aligned
    'instrument_number': (47, 67),
    'deed_type': (68, 72),
    'qualification_code': (73, 74),
    'vacant_flag': (75, 75),
    'multi_parcel_flag': (76, 76)
}
```

**Tasks:**
1. Request files from PTOTechnology@floridarevenue.com
2. Download from provided temporary link
3. Parse using Polars with fixed-width reader
4. Validate county_code == '16'
5. Convert numeric fields (divide by 100 for decimals)
6. Normalize city names and use codes
7. Batch upsert to Supabase (1000 records/batch)
8. Log statistics to jobs table

### 5.2 Broward Official Records Loader (daily)

**Schedule:** Every morning 7:15 AM ET

**Web Scraping Implementation:**
```python
# Since FTP not available, use web scraping
async def scrape_official_records():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Login if required
        await page.goto('https://officialrecords.broward.org/AcclaimWeb')
        
        # Search yesterday's recordings
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%m/%d/%Y')
        await page.fill('#dateFrom', yesterday)
        await page.fill('#dateTo', yesterday)
        
        # Select document types: Deed, Mortgage, Lien, etc.
        doc_types = ['DEED', 'MORTGAGE', 'LIEN', 'LIS PENDENS']
        for doc_type in doc_types:
            await page.select('#docType', doc_type)
            await page.click('#searchButton')
            
            # Parse results table
            results = await page.query_selector_all('table.results tr')
            for row in results:
                data = await parse_or_row(row)
                await store_recorded_doc(data)
```

### 5.3 Sunbiz Loader (daily + quarterly)

**Schedule:** Daily 8:00 AM ET; Quarterly full refresh

**SFTP Implementation:**
```python
import paramiko
from datetime import datetime

def download_sunbiz_data():
    # CONFIRMED CREDENTIALS
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    sftp_config = {
        'hostname': 'sftp.floridados.gov',
        'username': 'Public',
        'password': 'PubAccess1845!',
        'port': 22
    }
    
    ssh.connect(**sftp_config)
    sftp = ssh.open_sftp()
    
    # Navigate to daily directory
    sftp.chdir('/public/daily/')
    
    # Download today's files
    today = datetime.now().strftime('%Y%m%d')
    files = sftp.listdir()
    
    for filename in files:
        if today in filename:
            local_path = f'/data/raw/sunbiz/{today}/{filename}'
            sftp.get(filename, local_path)
            
    # Parse fixed-width corporate data
    parse_corporate_files(local_path)
    
    sftp.close()
    ssh.close()

def parse_corporate_files(filepath):
    # Fixed-width parsing based on Data Usage Guide
    CORP_LAYOUT = {
        'document_number': (0, 12),
        'entity_name': (12, 212),
        'status': (212, 222),
        'filing_type': (222, 232),
        'principal_addr': (232, 372),
        'mailing_addr': (372, 512),
        'fei_number': (512, 522),
        'date_filed': (522, 530)  # YYYYMMDD
    }
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            record = {}
            for field, (start, end) in CORP_LAYOUT.items():
                record[field] = line[start:end].strip()
            
            # Store to database
            upsert_entity(record)
```

### 5.4 Playwright Fallback Scraper (BCPA)

**Use when:** No API available, need specific property details

**Implementation:**
```python
async def scrape_bcpa_properties(city: str, use_code: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        await page.goto('https://web.bcpa.net/BcpaClient/')
        
        # Use advanced search
        await page.click('#advancedSearchLink')
        await page.select('#city', city)
        await page.select('#useCode', use_code)
        await page.click('#searchButton')
        
        # Handle pagination
        while True:
            # Extract folios from current page
            folios = await page.query_selector_all('.folio-link')
            for folio in folios:
                folio_num = await folio.inner_text()
                await extract_property_details(page, folio_num)
            
            # Check for next page
            next_btn = await page.query_selector('.pagination-next:not(.disabled)')
            if not next_btn:
                break
            await next_btn.click()
            await page.wait_for_load_state('networkidle')
```

## 6) Scoring & Selection (ENHANCED)

### Rule-based Scoring Algorithm:
```python
def calculate_property_score(parcel: dict, comparables: list) -> tuple[float, dict]:
    """
    Enhanced scoring with detailed breakdown
    Returns: (score, breakdown)
    """
    score = 50.0  # Base score
    breakdown = {}
    
    # 1. Use Code Weight (0-30 points)
    use_scores = {
        '48': 30,  # Industrial warehouses - highest
        '43': 28,  # Lumber yards
        '39': 25,  # Hotels/motels
        '17': 25,  # Office buildings
        '03': 22,  # Multi-family 10+ units
        '04': 20,  # Condominiums
        '01': 15,  # Single family
        '00': 10   # Vacant residential
    }
    use_score = use_scores.get(parcel['main_use'], 5)
    score += use_score
    breakdown['use_code'] = use_score
    
    # 2. Value Assessment Gap (0-20 points)
    if parcel['just_value'] and parcel['assessed_value']:
        gap_ratio = (parcel['just_value'] - parcel['assessed_value']) / parcel['just_value']
        gap_score = min(20, gap_ratio * 50)
        score += gap_score
        breakdown['value_gap'] = gap_score
    
    # 3. Recent Sales Activity (0-15 points)
    recent_sales = [s for s in parcel.get('sales', []) 
                   if s['sale_date'] > datetime.now() - timedelta(days=730)]
    sales_score = min(15, len(recent_sales) * 5)
    score += sales_score
    breakdown['sales_activity'] = sales_score
    
    # 4. Price per Square Foot vs Comparables (0-15 points)
    if comparables and parcel.get('land_sf'):
        parcel_ppsf = parcel['just_value'] / parcel['land_sf']
        comp_ppsf = np.median([c['just_value']/c['land_sf'] 
                               for c in comparables if c.get('land_sf')])
        if parcel_ppsf < comp_ppsf * 0.7:  # 30% below median
            ppsf_score = 15
        elif parcel_ppsf < comp_ppsf * 0.85:  # 15% below median
            ppsf_score = 10
        elif parcel_ppsf < comp_ppsf:
            ppsf_score = 5
        else:
            ppsf_score = 0
        score += ppsf_score
        breakdown['price_comparison'] = ppsf_score
    
    # 5. Age Factor (0-10 points)
    if parcel.get('eff_year'):
        age = datetime.now().year - parcel['eff_year']
        if age > 50:  # Very old - redevelopment opportunity
            age_score = 10
        elif age > 30:
            age_score = 7
        elif age < 5:  # Very new
            age_score = 8
        else:
            age_score = 3
        score += age_score
        breakdown['age_factor'] = age_score
    
    # 6. Entity Ownership (0-10 points)
    if parcel.get('owner_entity_id'):
        # Corporate ownership often indicates investment property
        entity_score = 10
    else:
        entity_score = 0
    score += entity_score
    breakdown['entity_ownership'] = entity_score
    
    # Ensure score is 0-100
    score = max(0, min(100, score))
    
    return score, breakdown
```

## 7) Backend API (FastAPI on Railway) - ENHANCED

### Additional Endpoints:
```python
# Data source monitoring
GET /data-sources/status
GET /data-sources/{source}/sync
POST /data-sources/{source}/trigger

# Data quality
GET /data-quality/report
GET /data-quality/checks/{table}

# Enrichment
POST /enrichment/queue/{folio}
GET /enrichment/status/{job_id}

# Analytics
GET /analytics/market-trends
GET /analytics/comparable/{folio}
GET /analytics/entity-network/{entity_id}
```

## 8) Frontend (Vercel) - ENHANCED

### Additional Features:
- **Data Source Monitor:** Real-time sync status dashboard
- **Quality Metrics:** Data completeness indicators
- **Entity Graph:** D3.js visualization of ownership networks
- **Heat Map:** Mapbox GL with scoring overlay
- **Alert Configuration:** Custom thresholds and notifications

## 9) RAG System for Dataset Management

### Vector Database Configuration:
```python
# Using pgvector for embeddings
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding vector(1536),  # OpenAI ada-002
    doc_type VARCHAR(50),
    created_at TIMESTAMP
);

CREATE INDEX ON rag_documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Document Types to Index:
- User guides (NAL/SDF specifications)
- Legal definitions
- Use code descriptions
- Municipal regulations
- Market reports
- Historical trends

## 10) AI Agent Orchestration System

### Agent Types:
```yaml
agents:
  - name: DataSourceMonitor
    schedule: "*/15 * * * *"  # Every 15 minutes
    tasks:
      - check_source_availability
      - validate_credentials
      - alert_on_failure
      
  - name: QualityValidator
    trigger: on_data_load
    tasks:
      - check_completeness
      - validate_formats
      - detect_anomalies
      
  - name: EnrichmentAgent
    trigger: on_new_records
    tasks:
      - lookup_contact_info
      - fetch_social_profiles
      - get_property_images
      
  - name: ScoringOptimizer
    schedule: "0 2 * * *"  # Daily at 2 AM
    tasks:
      - recalculate_scores
      - update_comparables
      - generate_insights
```

### Agent Implementation:
```python
from typing import Dict, Any
import asyncio
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config['name']
        
    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        pass
    
    async def log_result(self, result: Dict[str, Any]):
        await store_agent_task_result(self.name, result)

class DataSourceMonitorAgent(BaseAgent):
    async def execute(self) -> Dict[str, Any]:
        results = {}
        
        # Check DOR availability
        dor_status = await self.check_dor_portal()
        results['dor'] = dor_status
        
        # Check Sunbiz SFTP
        sunbiz_status = await self.check_sunbiz_sftp()
        results['sunbiz'] = sunbiz_status
        
        # Check BCPA website
        bcpa_status = await self.check_bcpa_website()
        results['bcpa'] = bcpa_status
        
        # Alert if any source is down
        if any(not status['available'] for status in results.values()):
            await self.send_alert(results)
        
        return results
```

## 11) Missing Fields Resolution Strategy

### Fields We Cannot Obtain:
1. **Private Sale Details:** Non-recorded cash transactions
2. **Detailed Financials:** Rent rolls, NOI (need owner cooperation)
3. **Environmental Issues:** Phase I/II reports (paid service)
4. **Internal Condition:** Requires physical inspection

### Mitigation Strategy:
- Partner with local real estate professionals
- Integrate MLS data where available
- Use street view APIs for external condition
- Crowdsource information from users

## 12) Performance Optimizations

### Data Pipeline Performance:
- **Parallel Processing:** Use Ray/Dask for large files
- **Incremental Updates:** Only process changed records
- **Caching:** Redis for frequently accessed data
- **CDN:** CloudFlare for static assets
- **Database:** Partition large tables by date/county

### Query Optimization:
```sql
-- Materialized view for fast search
CREATE MATERIALIZED VIEW mv_property_search AS
SELECT 
    p.folio,
    p.city,
    p.main_use,
    p.owner_raw,
    p.score,
    p.just_value,
    MAX(s.sale_date) as last_sale,
    COUNT(d.instrument_no) as doc_count
FROM parcels p
LEFT JOIN sales s ON p.folio = s.folio
LEFT JOIN doc_parcels d ON p.folio = d.folio
GROUP BY p.folio, p.city, p.main_use, p.owner_raw, p.score, p.just_value
WITH DATA;

CREATE INDEX ON mv_property_search(city, main_use, score DESC);
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_property_search;
```

## NEXT STEPS FOR IMPLEMENTATION

1. **Immediate Actions:**
   - Set up Sunbiz SFTP daily sync (credentials confirmed)
   - Email DOR for NAL/SDF file access
   - Build Playwright scrapers for BCPA and Official Records

2. **Week 1 Priorities:**
   - Implement core ETL pipelines
   - Set up data quality monitoring
   - Create base scoring algorithm

3. **Week 2 Priorities:**
   - Build FastAPI endpoints
   - Implement entity resolution
   - Add enrichment services

4. **Week 3 Priorities:**
   - Deploy frontend with search
   - Add authentication
   - Configure alerts

5. **Week 4 Priorities:**
   - Optimize performance
   - Add AI agents
   - Complete documentation

## APPENDICES

### A. Broward County Cities List
```python
BROWARD_CITIES = [
    'COCONUT CREEK', 'COOPER CITY', 'CORAL SPRINGS', 'DANIA BEACH',
    'DAVIE', 'DEERFIELD BEACH', 'FORT LAUDERDALE', 'HALLANDALE BEACH',
    'HILLSBORO BEACH', 'HOLLYWOOD', 'LAUDERDALE-BY-THE-SEA',
    'LAUDERDALE LAKES', 'LAUDERHILL', 'LAZY LAKE', 'LIGHTHOUSE POINT',
    'MARGATE', 'MIRAMAR', 'NORTH LAUDERDALE', 'OAKLAND PARK',
    'PARKLAND', 'PEMBROKE PARK', 'PEMBROKE PINES', 'PLANTATION',
    'POMPANO BEACH', 'SEA RANCH LAKES', 'SOUTHWEST RANCHES', 'SUNRISE',
    'TAMARAC', 'WEST PARK', 'WESTON', 'WILTON MANORS'
]
```

### B. Use Code Reference (Partial)
```python
USE_CODES = {
    '00': 'Vacant Residential',
    '01': 'Single Family',
    '02': 'Mobile Homes',
    '03': 'Multi-family (10+ units)',
    '04': 'Condominiums',
    '05': 'Cooperatives',
    '08': 'Multi-family (< 10 units)',
    '09': 'Residential Common Elements',
    '10': 'Vacant Commercial',
    '11': 'Stores (one story)',
    '12': 'Mixed use (store/residential)',
    '13': 'Department Stores',
    '14': 'Supermarkets',
    '15': 'Regional Shopping Centers',
    '16': 'Community Shopping Centers',
    '17': 'Office Buildings (one story)',
    '18': 'Office Buildings (multi-story)',
    '19': 'Professional Service Buildings',
    '20': 'Airports',
    '21': 'Restaurants/Cafeterias',
    '22': 'Drive-in Restaurants',
    '23': 'Financial Institutions',
    '24': 'Insurance Company Offices',
    '25': 'Repair Service Shops',
    '26': 'Service Stations',
    '27': 'Auto Sales/Service/Rental',
    '28': 'Parking Lots (commercial)',
    '29': 'Wholesale Outlets',
    '30': 'Florist/Greenhouses',
    '33': 'Nightclubs/Lounges/Bars',
    '34': 'Bowling Alleys',
    '35': 'Theaters',
    '38': 'Golf Courses',
    '39': 'Hotels/Motels',
    '40': 'Vacant Industrial',
    '41': 'Light Manufacturing',
    '42': 'Heavy Manufacturing',
    '43': 'Lumber Yards',
    '44': 'Packing Plants',
    '45': 'Canneries/Distilleries',
    '46': 'Other Food Processing',
    '47': 'Mineral Processing',
    '48': 'Warehousing/Storage',
    '49': 'Open Storage'
    # ... continue for all 00-99
}
```

### C. Data Quality Rules
```python
QUALITY_RULES = {
    'parcels': {
        'folio': {'required': True, 'pattern': r'^\d{10,20}$'},
        'county_code': {'required': True, 'value': '16'},
        'city': {'required': True, 'in': BROWARD_CITIES},
        'main_use': {'required': True, 'pattern': r'^\d{2}$'},
        'just_value': {'min': 0, 'max': 1000000000}
    },
    'sales': {
        'sale_date': {'required': True, 'after': '1950-01-01'},
        'price': {'min': 0, 'max': 1000000000}
    }
}
```

---

END OF ENHANCED PDR v0.2