# Florida Property Data - Comprehensive Automation System Analysis

## Executive Summary

This document outlines a **fully automated, AI-powered daily data ingestion system** for all 67 Florida counties, integrating:
- Florida DOR official data sources (NAL, SDF, NAP)
- County Property Appraiser websites (67 counties)
- Statewide parcel geometry (FGIO)
- Daily delta detection and automatic updates
- AI-powered validation and quality assurance

---

## 1. Data Source Architecture

### Primary Sources (Official DOR)

| Dataset | Purpose | Update Frequency | URL |
|---------|---------|------------------|-----|
| **NAL** | Name/Address/Legal (property roll) | Annual (Prelim/Final) + Revisions | [Request Hub](https://floridarevenue.com/property/Pages/DataPortal_RequestAssessmentRollGISData.aspx) |
| **SDF** | Sales Data File | Annual + Revisions | Same as NAL |
| **NAP** | Tangible Personal Property | Annual + Revisions | Same as NAL |
| **FGIO Parcels** | Statewide parcel geometry | Quarterly | [FGIO Portal](https://www.floridagio.gov/datasets/FGIO%3A%3Aflorida-statewide-parcels/about?layer=0) |
| **Non-Ad Valorem** | Special assessments | Annual | [Reports](https://floridarevenue.com/property/Pages/Cofficial_NonAdValoremReports.aspx) |

### Reference Documents (Critical for Parsing)

| Document | Purpose | URL |
|----------|---------|-----|
| 2025 Users Guide | Field layouts, data types, codes | [PDF](https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/User%20Guides/2025%20Users%20guide%20and%20quick%20reference/2025_NAL_SDF_NAP_Users_Guide.pdf) |
| 2025 Submission Standards | Validation rules, edit checks | [PDF](https://floridarevenue.com/property/Documents/2025FINALCompSubmStd.pdf) |
| 2024 Edit Guide | Data quality rules | [PDF](https://floridarevenue.com/property/Documents/2024editguide.pdf) |

### Secondary Sources (County-Level, Higher Frequency)

**67 County Property Appraiser websites** - Daily/weekly updates
- Example: [Broward County](https://bcpa.net/)
- Each county has different formats, update schedules, access methods
- Requires Firecrawl + Playwright MCP for discovery and scraping

---

## 2. Proposed System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY ORCHESTRATOR (Railway)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ DOR Checker  │  │County Scrapers│  │FGIO Updater │          │
│  │  AI Agent    │  │  AI Agent     │  │  AI Agent   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │        DELTA DETECTION ENGINE (AI-Powered)        │          │
│  │  • File hash comparison                           │          │
│  │  • Timestamp tracking                             │          │
│  │  • Content-based change detection                 │          │
│  └──────────────────────────────────────────────────┘          │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────┐          │
│  │          DOWNLOAD & EXTRACTION LAYER              │          │
│  │  • HTTP/HTTPS downloads                           │          │
│  │  • ZIP/CSV parsing                                │          │
│  │  • Encoding normalization (UTF-8, Latin1, etc.)   │          │
│  └──────────────────────────────────────────────────┘          │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────┐          │
│  │       AI VALIDATION & QUALITY ASSURANCE           │          │
│  │  • OpenAI: Schema validation, anomaly detection   │          │
│  │  • Gemma 3 270M: Code classification, fast checks │          │
│  │  • RAG: Query Users Guide for field rules         │          │
│  │  • Sentry: Alert on validation failures           │          │
│  └──────────────────────────────────────────────────┘          │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────┐          │
│  │           SUPABASE INGESTION PIPELINE             │          │
│  │  1. Raw Storage (versioned by year/county/type)   │          │
│  │  2. Staging Tables (stg_nal, stg_sdf, stg_nap)    │          │
│  │  3. Core Tables (UPSERT on parcel_id + county)    │          │
│  │  4. Materialized Views (performance)              │          │
│  └──────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   VERCEL DASHBOARD    │
                  │  • Sync status grid   │
                  │  • Manual triggers    │
                  │  • Quality metrics    │
                  │  • County coverage    │
                  └───────────────────────┘
```

---

## 3. AI Agent Architecture

### Agent 1: DOR Portal Monitor
**Purpose**: Check Florida DOR for new/updated NAL, SDF, NAP files
**Tech Stack**: Python + BeautifulSoup + httpx + OpenAI
**Schedule**: Daily at 03:00 ET
**Logic**:
```python
# Chain of Thought Process:
# 1. Fetch directory page HTML
# 2. Parse file links, sizes, timestamps
# 3. Compare with last known state (SHA256 hashes)
# 4. If changed: download, validate, ingest
# 5. Log results to Supabase audit table
# 6. Alert via Sentry if critical files missing
```

### Agent 2: County Appraiser Scraper (67 instances)
**Purpose**: Scrape daily updates from each county's Property Appraiser website
**Tech Stack**: Playwright MCP + Firecrawl + BeautifulSoup + OpenAI
**Schedule**: Daily at 04:00 ET (after DOR check)
**Logic**:
```python
# Chain of Thought Process:
# 1. Firecrawl discovers download links on county PA website
# 2. Playwright automates login/navigation if needed
# 3. Download latest property data (CSV/Excel/PDF)
# 4. Parse and normalize to NAL/SDF/NAP schema
# 5. AI validates against Users Guide rules
# 6. Upsert into Supabase (supplement DOR data)
# 7. Track coverage: which counties updated today?
```

### Agent 3: FGIO Parcel Geometry Updater
**Purpose**: Update statewide parcel boundaries quarterly
**Tech Stack**: ArcGIS API + GeoPandas + PostGIS
**Schedule**: Monthly check, download if updated
**Logic**:
```python
# Chain of Thought Process:
# 1. Query FGIO ArcGIS REST API for last_edit_date
# 2. Compare with our gis_parcels.last_updated
# 3. If newer: download GeoJSON/GeoPackage
# 4. Load into PostGIS (gis.parcels table)
# 5. Update parcel_id crosswalks by county
# 6. Refresh materialized views joining NAL to geometry
```

### Agent 4: AI Data Validator
**Purpose**: Ensure data quality using LLMs and rule engines
**Tech Stack**: OpenAI (GPT-4) + Gemma 3 270M + RAG
**Triggers**: After every ingestion batch
**Logic**:
```python
# Chain of Thought Process:
# 1. Sample 1000 random rows from new data
# 2. OpenAI: "Check these records against 2025 Users Guide rules"
# 3. Gemma 3 270M: Fast classification of property_use codes
# 4. RAG: Query embedded PDF docs for edge cases
# 5. Generate quality score (0-100)
# 6. If score < 80: alert and hold ingestion
# 7. Log anomalies to validation_errors table
```

---

## 4. Database Schema (Supabase)

### Raw Storage (Supabase Storage Buckets)
```
/raw/
  ├── 2025/
  │   ├── broward/
  │   │   ├── nal/broward_nal_2025_prelim.csv (v1)
  │   │   ├── nal/broward_nal_2025_final.csv (v2)
  │   │   ├── sdf/broward_sdf_2025.csv
  │   │   └── nap/broward_nap_2025.csv
  │   ├── miami-dade/
  │   └── ... (all 67 counties)
  └── 2024/ (historical)
```

### Staging Tables
```sql
-- Staging: Raw ingestion before validation
CREATE SCHEMA IF NOT EXISTS stg;

CREATE TABLE stg.nal_raw (
  id BIGSERIAL PRIMARY KEY,
  county_code INT,
  parcel_id TEXT,
  rs_id TEXT,
  owner_name TEXT,
  situs_addr TEXT,
  property_use_code TEXT,
  just_value NUMERIC,
  assessed_value NUMERIC,
  taxable_value NUMERIC,
  land_value NUMERIC,
  building_value NUMERIC,
  -- ... all NAL fields from Users Guide
  source_file TEXT,
  loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE stg.sdf_raw (
  id BIGSERIAL PRIMARY KEY,
  county_code INT,
  parcel_id TEXT,
  sale_date DATE,
  sale_price NUMERIC,
  sale_type TEXT,
  qualified_sale BOOLEAN,
  or_book TEXT,
  or_page TEXT,
  clerk_instrument_number TEXT,
  -- ... all SDF fields
  source_file TEXT,
  loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE stg.nap_raw (
  id BIGSERIAL PRIMARY KEY,
  county_code INT,
  parcel_id TEXT,
  bedrooms INT,
  bathrooms INT,
  units INT,
  stories INT,
  year_built INT,
  total_living_area NUMERIC,
  dor_use_code TEXT,
  -- ... all NAP fields
  source_file TEXT,
  loaded_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Core Tables (Production)
```sql
-- Core: Validated, deduplicated, production-ready
CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE core.parcels (
  id BIGSERIAL PRIMARY KEY,
  county_code INT NOT NULL,
  county_name TEXT,
  parcel_id TEXT NOT NULL,
  rs_id TEXT,

  -- Owner info
  owner_name TEXT,
  owner_addr1 TEXT,
  owner_addr2 TEXT,
  owner_city TEXT,
  owner_state TEXT,
  owner_zip TEXT,

  -- Property location
  situs_addr TEXT,
  situs_city TEXT,
  situs_zip TEXT,

  -- Values
  just_value NUMERIC,
  assessed_value NUMERIC,
  taxable_value NUMERIC,
  land_value NUMERIC,
  building_value NUMERIC,

  -- Characteristics (from NAP)
  bedrooms INT,
  bathrooms INT,
  units INT,
  stories INT,
  year_built INT,
  total_living_area NUMERIC,
  lot_size_sqft NUMERIC,

  -- Classification
  property_use_code TEXT,
  dor_use_code TEXT,
  land_use_code TEXT,

  -- Metadata
  data_quality_score INT, -- AI-generated score
  last_validated_at TIMESTAMPTZ,
  last_updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(county_code, parcel_id)
);

CREATE INDEX idx_parcels_county_parcel ON core.parcels(county_code, parcel_id);
CREATE INDEX idx_parcels_owner ON core.parcels USING gin(owner_name gin_trgm_ops);
CREATE INDEX idx_parcels_situs ON core.parcels USING gin(situs_addr gin_trgm_ops);

CREATE TABLE core.sales_history (
  id BIGSERIAL PRIMARY KEY,
  county_code INT NOT NULL,
  parcel_id TEXT NOT NULL,
  sale_date DATE,
  sale_price NUMERIC,
  sale_type TEXT,
  qualified_sale BOOLEAN,
  or_book TEXT,
  or_page TEXT,
  clerk_instrument_number TEXT,
  verification_code TEXT,

  -- Link to parcel
  parcel_fk BIGINT REFERENCES core.parcels(id),

  loaded_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(county_code, parcel_id, sale_date, clerk_instrument_number)
);

CREATE INDEX idx_sales_parcel ON core.sales_history(county_code, parcel_id);
CREATE INDEX idx_sales_date ON core.sales_history(sale_date DESC);
```

### Geometry Tables (PostGIS)
```sql
CREATE SCHEMA IF NOT EXISTS gis;

CREATE TABLE gis.parcels (
  id BIGSERIAL PRIMARY KEY,
  county_code INT,
  parcel_id TEXT,
  geometry GEOMETRY(MultiPolygon, 4326),
  centroid GEOMETRY(Point, 4326),
  area_sqft NUMERIC,

  -- FGIO metadata
  fgio_source_date DATE,
  fgio_accuracy TEXT,

  UNIQUE(county_code, parcel_id)
);

CREATE INDEX idx_gis_parcels_geom ON gis.parcels USING GIST(geometry);
CREATE INDEX idx_gis_parcels_centroid ON gis.parcels USING GIST(centroid);
```

### Audit & Monitoring Tables
```sql
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE audit.ingestion_runs (
  id BIGSERIAL PRIMARY KEY,
  run_timestamp TIMESTAMPTZ DEFAULT NOW(),
  source_type TEXT, -- 'DOR', 'COUNTY_PA', 'FGIO'
  county_code INT,
  file_name TEXT,
  file_size BIGINT,
  file_hash TEXT,
  rows_inserted INT,
  rows_updated INT,
  rows_failed INT,
  duration_seconds NUMERIC,
  ai_quality_score INT,
  status TEXT, -- 'SUCCESS', 'PARTIAL', 'FAILED'
  error_message TEXT
);

CREATE TABLE audit.validation_errors (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT REFERENCES audit.ingestion_runs(id),
  county_code INT,
  parcel_id TEXT,
  error_type TEXT,
  error_message TEXT,
  raw_data JSONB,
  detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit.file_registry (
  id BIGSERIAL PRIMARY KEY,
  source_url TEXT,
  file_name TEXT,
  file_hash TEXT,
  file_size BIGINT,
  last_modified TIMESTAMPTZ,
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_checked TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(source_url, file_hash)
);
```

---

## 5. Ingestion Pipeline (Python on Railway)

### File: `railway-deploy/florida_data_orchestrator.py`

```python
"""
Florida Property Data Orchestrator
Daily automated ingestion for all 67 counties
"""

import os
import httpx
import hashlib
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import csv
import zipfile
import io
from bs4 import BeautifulSoup
import sentry_sdk
from supabase import create_client, Client
import openai
from transformers import pipeline  # For Gemma 3 270M

# Initialize services
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Gemma 3 270M for fast code classification
classifier = pipeline("text-classification", model="google/gemma-3-270m")

# URLs
DOR_ASSESSMENT_HUB = "https://floridarevenue.com/property/Pages/DataPortal_RequestAssessmentRollGISData.aspx"
FGIO_PARCELS_API = "https://services.arcgis.com/..." # ArcGIS REST endpoint

# County codes (1-67)
FLORIDA_COUNTIES = {
    1: "ALACHUA", 2: "BAKER", 3: "BAY", 4: "BRADFORD", 5: "BREVARD",
    6: "BROWARD", 7: "CALHOUN", 8: "CHARLOTTE", 9: "CITRUS", 10: "CLAY",
    # ... all 67
    12: "BROWARD",
    13: "MIAMI-DADE",
    # ...
}


class FloridaDataOrchestrator:
    """Main orchestrator for daily data ingestion"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300)
        self.run_id = None

    async def run_daily_sync(self):
        """Main entry point for daily sync"""
        print(f"🚀 Starting daily sync at {datetime.now()}")

        # Create run record
        run = supabase.table('audit.ingestion_runs').insert({
            'run_timestamp': datetime.now().isoformat(),
            'source_type': 'ORCHESTRATOR',
            'status': 'RUNNING'
        }).execute()
        self.run_id = run.data[0]['id']

        try:
            # Step 1: Check DOR portal for NAL/SDF/NAP updates
            await self.check_dor_updates()

            # Step 2: Scrape county Property Appraiser sites
            await self.scrape_county_appraisers()

            # Step 3: Update FGIO parcel geometry
            await self.update_parcel_geometry()

            # Step 4: Run AI validation
            quality_score = await self.ai_validation()

            # Update run status
            supabase.table('audit.ingestion_runs').update({
                'status': 'SUCCESS',
                'ai_quality_score': quality_score,
                'duration_seconds': (datetime.now() - run.data[0]['run_timestamp']).total_seconds()
            }).eq('id', self.run_id).execute()

            print(f"✅ Daily sync completed. Quality score: {quality_score}/100")

        except Exception as e:
            sentry_sdk.capture_exception(e)
            supabase.table('audit.ingestion_runs').update({
                'status': 'FAILED',
                'error_message': str(e)
            }).eq('id', self.run_id).execute()
            raise

    async def check_dor_updates(self):
        """Check Florida DOR for new NAL/SDF/NAP files"""
        print("\n📂 Checking DOR portal for updates...")

        # Fetch the directory page
        response = await self.client.get(DOR_ASSESSMENT_HUB)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Parse file links (this is simplified - actual DOR site may need Playwright)
        file_links = soup.find_all('a', href=lambda h: h and ('.csv' in h or '.zip' in h))

        for link in file_links:
            url = link['href']
            file_name = url.split('/')[-1]

            # Check if we've seen this file before
            existing = supabase.table('audit.file_registry')\
                .select('*')\
                .eq('source_url', url)\
                .execute()

            # Download and check hash
            file_response = await self.client.get(url)
            file_hash = hashlib.sha256(file_response.content).hexdigest()

            # If new or changed, process it
            if not existing.data or existing.data[0]['file_hash'] != file_hash:
                print(f"  📥 New/updated file: {file_name}")
                await self.process_dor_file(url, file_name, file_response.content)

                # Update registry
                supabase.table('audit.file_registry').upsert({
                    'source_url': url,
                    'file_name': file_name,
                    'file_hash': file_hash,
                    'file_size': len(file_response.content),
                    'last_modified': datetime.now().isoformat()
                }).execute()

    async def process_dor_file(self, url: str, file_name: str, content: bytes):
        """Process a NAL/SDF/NAP file"""
        # Determine file type
        file_type = None
        if 'nal' in file_name.lower():
            file_type = 'NAL'
        elif 'sdf' in file_name.lower():
            file_type = 'SDF'
        elif 'nap' in file_name.lower():
            file_type = 'NAP'
        else:
            print(f"  ⚠️  Unknown file type: {file_name}")
            return

        # Extract county code from filename (varies by state format)
        # Example: "broward_nal_2025.csv" or "12_nal_2025.csv"
        county_code = self.extract_county_code(file_name)

        # Upload raw file to Supabase Storage
        year = datetime.now().year
        storage_path = f"raw/{year}/{FLORIDA_COUNTIES.get(county_code, 'unknown')}/{file_type.lower()}/{file_name}"

        supabase.storage.from_('florida-property-data').upload(
            storage_path,
            content,
            file_options={"content-type": "text/csv"}
        )

        # Parse CSV
        if file_name.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                csv_name = [f for f in z.namelist() if f.endswith('.csv')][0]
                csv_content = z.read(csv_name).decode('utf-8', errors='ignore')
        else:
            csv_content = content.decode('utf-8', errors='ignore')

        # Load into staging table
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        print(f"  📊 Parsed {len(rows)} rows from {file_name}")

        # Batch insert into staging
        if file_type == 'NAL':
            await self.load_nal_staging(rows, county_code, file_name)
        elif file_type == 'SDF':
            await self.load_sdf_staging(rows, county_code, file_name)
        elif file_type == 'NAP':
            await self.load_nap_staging(rows, county_code, file_name)

    async def load_nal_staging(self, rows: list, county_code: int, source_file: str):
        """Load NAL data into staging table"""
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]

            # Map CSV columns to our schema
            records = []
            for row in batch:
                records.append({
                    'county_code': county_code,
                    'parcel_id': row.get('PARCEL_ID') or row.get('parcel_id'),
                    'rs_id': row.get('RS_ID'),
                    'owner_name': row.get('OWN_NAME'),
                    'situs_addr': row.get('PHY_ADDR1'),
                    'property_use_code': row.get('DOR_UC'),
                    'just_value': float(row.get('JV') or 0),
                    'assessed_value': float(row.get('AV') or 0),
                    'land_value': float(row.get('LND_VAL') or 0),
                    'building_value': float(row.get('BLDG_VAL') or 0),
                    # ... map all fields
                    'source_file': source_file
                })

            # Insert to staging
            supabase.table('stg.nal_raw').insert(records).execute()

        # Now upsert from staging to core
        await self.upsert_nal_to_core(county_code)

    async def upsert_nal_to_core(self, county_code: int):
        """Upsert NAL staging data into core.parcels"""
        # This would be a SQL function call for performance
        supabase.rpc('upsert_nal_to_core', {'p_county_code': county_code}).execute()

    async def scrape_county_appraisers(self):
        """Scrape all 67 county Property Appraiser websites"""
        print("\n🏛️  Scraping county Property Appraiser sites...")

        # County PA URLs (maintained list)
        county_pa_urls = {
            6: "https://bcpa.net/",  # Broward
            13: "https://www.miamidade.gov/pa/",  # Miami-Dade
            # ... all 67
        }

        for county_code, url in county_pa_urls.items():
            try:
                # Use Firecrawl to discover download links
                # (This would integrate with Firecrawl API)
                downloads = await self.discover_downloads_firecrawl(url)

                for download_url in downloads:
                    # Download and process
                    await self.process_county_file(county_code, download_url)

            except Exception as e:
                print(f"  ⚠️  Error scraping {FLORIDA_COUNTIES[county_code]}: {e}")
                sentry_sdk.capture_exception(e)

    async def update_parcel_geometry(self):
        """Update FGIO parcel boundaries"""
        print("\n🗺️  Checking FGIO parcel geometry...")

        # Query ArcGIS REST API for last update
        response = await self.client.get(f"{FGIO_PARCELS_API}?f=json")
        metadata = response.json()

        last_edit_date = metadata.get('editingInfo', {}).get('lastEditDate')

        # Check our last update
        our_last_update = supabase.table('gis.parcels')\
            .select('fgio_source_date')\
            .order('fgio_source_date', desc=True)\
            .limit(1)\
            .execute()

        if not our_last_update.data or our_last_update.data[0]['fgio_source_date'] < last_edit_date:
            print(f"  📥 Downloading new parcel geometry...")
            # Download GeoJSON and load into PostGIS
            # (This would use GeoPandas + PostGIS)

    async def ai_validation(self) -> int:
        """Run AI-powered validation on newly ingested data"""
        print("\n🤖 Running AI validation...")

        # Sample 1000 random rows from staging
        sample = supabase.table('stg.nal_raw')\
            .select('*')\
            .limit(1000)\
            .execute()

        errors = []

        for row in sample.data:
            # Use Gemma 3 270M for fast code validation
            property_use_code = row.get('property_use_code')
            if property_use_code:
                result = classifier(f"Property use code: {property_use_code}")
                if result[0]['label'] == 'INVALID':
                    errors.append({
                        'parcel_id': row['parcel_id'],
                        'error_type': 'INVALID_PROPERTY_USE_CODE',
                        'error_message': f"Code {property_use_code} not recognized"
                    })

            # Use OpenAI for complex validation
            if row.get('just_value', 0) < row.get('land_value', 0):
                # Ask GPT-4 if this is valid
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{
                        "role": "system",
                        "content": "You are a Florida property data validator. Check if just_value < land_value is ever valid."
                    }, {
                        "role": "user",
                        "content": f"Parcel {row['parcel_id']}: just_value={row['just_value']}, land_value={row['land_value']}"
                    }]
                )

                if "invalid" in response.choices[0].message.content.lower():
                    errors.append({
                        'parcel_id': row['parcel_id'],
                        'error_type': 'VALUE_INCONSISTENCY',
                        'error_message': response.choices[0].message.content
                    })

        # Log errors
        if errors:
            supabase.table('audit.validation_errors').insert(errors).execute()

        # Calculate quality score
        quality_score = int((1 - len(errors) / 1000) * 100)

        return quality_score

    def extract_county_code(self, filename: str) -> int:
        """Extract county code from filename"""
        # Try numeric code first (e.g., "12_nal_2025.csv")
        import re
        match = re.search(r'^(\d+)_', filename)
        if match:
            return int(match.group(1))

        # Try county name (e.g., "broward_nal_2025.csv")
        filename_lower = filename.lower()
        for code, name in FLORIDA_COUNTIES.items():
            if name.lower().replace('-', '').replace(' ', '') in filename_lower:
                return code

        return 0  # Unknown


# FastAPI endpoints
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()
orchestrator = FloridaDataOrchestrator()

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/ingest/run")
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """Manually trigger data ingestion"""
    background_tasks.add_task(orchestrator.run_daily_sync)
    return {"status": "started", "message": "Ingestion running in background"}

@app.get("/ingest/status")
async def get_status():
    """Get status of latest ingestion run"""
    runs = supabase.table('audit.ingestion_runs')\
        .select('*')\
        .order('run_timestamp', desc=True)\
        .limit(10)\
        .execute()

    return {"recent_runs": runs.data}

@app.get("/coverage/counties")
async def get_county_coverage():
    """Get data coverage by county"""
    coverage = supabase.rpc('get_county_coverage').execute()
    return {"coverage": coverage.data}


# Scheduled job (Railway cron config)
if __name__ == "__main__":
    import asyncio
    asyncio.run(orchestrator.run_daily_sync())
```

---

## 6. Supabase SQL Functions

### File: `supabase/migrations/20250105_data_ingestion_functions.sql`

```sql
-- Function to upsert NAL staging data into core.parcels
CREATE OR REPLACE FUNCTION upsert_nal_to_core(p_county_code INT)
RETURNS TABLE(inserted INT, updated INT) AS $$
DECLARE
  v_inserted INT := 0;
  v_updated INT := 0;
BEGIN
  -- Upsert from staging to core
  WITH upsert_result AS (
    INSERT INTO core.parcels (
      county_code, parcel_id, rs_id, owner_name, situs_addr,
      just_value, assessed_value, land_value, building_value,
      property_use_code, last_updated_at
    )
    SELECT
      county_code, parcel_id, rs_id, owner_name, situs_addr,
      just_value, assessed_value, land_value, building_value,
      property_use_code, NOW()
    FROM stg.nal_raw
    WHERE county_code = p_county_code
    ON CONFLICT (county_code, parcel_id) DO UPDATE SET
      rs_id = EXCLUDED.rs_id,
      owner_name = EXCLUDED.owner_name,
      situs_addr = EXCLUDED.situs_addr,
      just_value = EXCLUDED.just_value,
      assessed_value = EXCLUDED.assessed_value,
      land_value = EXCLUDED.land_value,
      building_value = EXCLUDED.building_value,
      property_use_code = EXCLUDED.property_use_code,
      last_updated_at = NOW()
    RETURNING (xmax = 0) AS inserted
  )
  SELECT
    COUNT(*) FILTER (WHERE inserted) INTO v_inserted,
    COUNT(*) FILTER (WHERE NOT inserted) INTO v_updated
  FROM upsert_result;

  RETURN QUERY SELECT v_inserted, v_updated;
END;
$$ LANGUAGE plpgsql;

-- Function to get county coverage statistics
CREATE OR REPLACE FUNCTION get_county_coverage()
RETURNS TABLE(
  county_code INT,
  county_name TEXT,
  total_parcels BIGINT,
  with_sales BIGINT,
  with_characteristics BIGINT,
  with_geometry BIGINT,
  last_updated TIMESTAMPTZ,
  coverage_percent NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.county_code,
    p.county_name,
    COUNT(*) AS total_parcels,
    COUNT(s.id) AS with_sales,
    COUNT(CASE WHEN p.bedrooms IS NOT NULL THEN 1 END) AS with_characteristics,
    COUNT(g.id) AS with_geometry,
    MAX(p.last_updated_at) AS last_updated,
    ROUND(
      (COUNT(CASE WHEN p.bedrooms IS NOT NULL AND s.id IS NOT NULL AND g.id IS NOT NULL THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC) * 100,
      2
    ) AS coverage_percent
  FROM core.parcels p
  LEFT JOIN core.sales_history s ON p.county_code = s.county_code AND p.parcel_id = s.parcel_id
  LEFT JOIN gis.parcels g ON p.county_code = g.county_code AND p.parcel_id = g.parcel_id
  GROUP BY p.county_code, p.county_name
  ORDER BY p.county_code;
END;
$$ LANGUAGE plpgsql;
```

---

## 7. Vercel Admin Dashboard

### File: `apps/web/src/pages/admin/FloridaDataSync.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { Card, Button, Progress, Table, Badge } from '@/components/ui';

interface CountyCoverage {
  county_code: number;
  county_name: string;
  total_parcels: number;
  with_sales: number;
  with_characteristics: number;
  with_geometry: number;
  last_updated: string;
  coverage_percent: number;
}

interface IngestionRun {
  id: number;
  run_timestamp: string;
  source_type: string;
  county_code: number;
  rows_inserted: number;
  rows_updated: number;
  duration_seconds: number;
  ai_quality_score: number;
  status: string;
}

export default function FloridaDataSync() {
  const [coverage, setCoverage] = useState<CountyCoverage[]>([]);
  const [recentRuns, setRecentRuns] = useState<IngestionRun[]>([]);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadData();
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    // Fetch county coverage
    const coverageRes = await fetch(`${import.meta.env.VITE_RAILWAY_API_URL}/coverage/counties`);
    const coverageData = await coverageRes.json();
    setCoverage(coverageData.coverage);

    // Fetch recent ingestion runs
    const runsRes = await fetch(`${import.meta.env.VITE_RAILWAY_API_URL}/ingest/status`);
    const runsData = await runsRes.json();
    setRecentRuns(runsData.recent_runs);
  };

  const triggerSync = async () => {
    setSyncing(true);
    await fetch(`${import.meta.env.VITE_RAILWAY_API_URL}/ingest/run`, { method: 'POST' });
    setTimeout(loadData, 5000); // Refresh after 5 seconds
    setSyncing(false);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Florida Property Data Sync</h1>
        <Button onClick={triggerSync} disabled={syncing}>
          {syncing ? '⏳ Syncing...' : '🔄 Trigger Sync Now'}
        </Button>
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <Card className="p-6">
          <h3 className="text-sm text-gray-600 mb-2">Total Parcels</h3>
          <p className="text-3xl font-bold">
            {coverage.reduce((sum, c) => sum + c.total_parcels, 0).toLocaleString()}
          </p>
        </Card>
        <Card className="p-6">
          <h3 className="text-sm text-gray-600 mb-2">Counties Covered</h3>
          <p className="text-3xl font-bold">{coverage.length} / 67</p>
        </Card>
        <Card className="p-6">
          <h3 className="text-sm text-gray-600 mb-2">Avg Quality Score</h3>
          <p className="text-3xl font-bold">
            {recentRuns.length > 0
              ? Math.round(recentRuns.reduce((sum, r) => sum + r.ai_quality_score, 0) / recentRuns.length)
              : 0}
            %
          </p>
        </Card>
        <Card className="p-6">
          <h3 className="text-sm text-gray-600 mb-2">Last Sync</h3>
          <p className="text-lg font-semibold">
            {recentRuns.length > 0
              ? new Date(recentRuns[0].run_timestamp).toLocaleString()
              : 'Never'}
          </p>
        </Card>
      </div>

      {/* County Coverage Table */}
      <Card className="p-6 mb-8">
        <h2 className="text-xl font-bold mb-4">County Coverage</h2>
        <Table>
          <thead>
            <tr>
              <th>County</th>
              <th>Total Parcels</th>
              <th>With Sales</th>
              <th>With Characteristics</th>
              <th>With Geometry</th>
              <th>Coverage %</th>
              <th>Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {coverage.map((county) => (
              <tr key={county.county_code}>
                <td className="font-medium">{county.county_name}</td>
                <td>{county.total_parcels.toLocaleString()}</td>
                <td>{county.with_sales.toLocaleString()}</td>
                <td>{county.with_characteristics.toLocaleString()}</td>
                <td>{county.with_geometry.toLocaleString()}</td>
                <td>
                  <Progress value={county.coverage_percent} max={100} />
                  <span className="text-sm text-gray-600">{county.coverage_percent}%</span>
                </td>
                <td className="text-sm text-gray-600">
                  {new Date(county.last_updated).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>

      {/* Recent Ingestion Runs */}
      <Card className="p-6">
        <h2 className="text-xl font-bold mb-4">Recent Ingestion Runs</h2>
        <Table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Source</th>
              <th>County</th>
              <th>Inserted</th>
              <th>Updated</th>
              <th>Duration</th>
              <th>Quality Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {recentRuns.map((run) => (
              <tr key={run.id}>
                <td className="text-sm">{new Date(run.run_timestamp).toLocaleString()}</td>
                <td>
                  <Badge variant={run.source_type === 'DOR' ? 'primary' : 'secondary'}>
                    {run.source_type}
                  </Badge>
                </td>
                <td>{FLORIDA_COUNTIES[run.county_code]}</td>
                <td>{run.rows_inserted?.toLocaleString() || 0}</td>
                <td>{run.rows_updated?.toLocaleString() || 0}</td>
                <td>{run.duration_seconds?.toFixed(1)}s</td>
                <td>
                  <Badge variant={run.ai_quality_score >= 80 ? 'success' : 'warning'}>
                    {run.ai_quality_score}%
                  </Badge>
                </td>
                <td>
                  <Badge variant={run.status === 'SUCCESS' ? 'success' : 'error'}>
                    {run.status}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
    </div>
  );
}

const FLORIDA_COUNTIES: Record<number, string> = {
  1: 'Alachua', 2: 'Baker', 3: 'Bay', 4: 'Bradford', 5: 'Brevard',
  6: 'Broward', 7: 'Calhoun', 8: 'Charlotte', 9: 'Citrus', 10: 'Clay',
  11: 'Collier', 12: 'Columbia', 13: 'Miami-Dade',
  // ... all 67 counties
};
```

---

## 8. Railway Deployment Configuration

### File: `railway.toml`

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements-data-ingestion.txt"

[deploy]
startCommand = "uvicorn florida_data_orchestrator:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300

[[crons]]
schedule = "0 3 * * *"  # Daily at 3:00 AM ET
command = "python florida_data_orchestrator.py"
```

### File: `requirements-data-ingestion.txt`

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.24.1
supabase==2.0.2
beautifulsoup4==4.12.2
lxml==4.9.3
sentry-sdk==1.38.0
openai==1.3.7
transformers==4.35.2
torch==2.1.1
pandas==2.1.3
geopandas==0.14.1
playwright==1.40.0
python-dotenv==1.0.0
```

---

## 9. Chain of Thought Implementation Strategy

### Phase 1: Foundation (Week 1)
1. ✅ Set up Supabase schemas (staging, core, gis, audit)
2. ✅ Deploy basic FastAPI orchestrator to Railway
3. ✅ Implement DOR file discovery (BeautifulSoup)
4. ✅ Create delta detection (file hash registry)
5. ✅ Build basic Vercel admin dashboard

### Phase 2: AI Integration (Week 2)
1. ✅ Integrate OpenAI for validation
2. ✅ Deploy Gemma 3 270M on HuggingFace
3. ✅ Build RAG system with Users Guide PDF
4. ✅ Implement quality scoring algorithm
5. ✅ Add Sentry monitoring

### Phase 3: County Scraping (Week 3)
1. ✅ Catalog all 67 county PA websites
2. ✅ Integrate Firecrawl for link discovery
3. ✅ Use Playwright MCP for complex sites
4. ✅ Normalize county data to NAL/SDF/NAP format
5. ✅ Build county-specific parsers

### Phase 4: Geometry & Advanced Features (Week 4)
1. ✅ FGIO parcel geometry integration
2. ✅ PostGIS spatial queries
3. ✅ Materialized views for performance
4. ✅ Advanced dashboard analytics
5. ✅ Automated alerts and notifications

### Phase 5: Production Hardening (Week 5)
1. ✅ Load testing with 9M+ records
2. ✅ Optimize batch sizes
3. ✅ Implement retry logic
4. ✅ Add comprehensive logging
5. ✅ Document operational runbook

---

## 10. Expected Outcomes

### Data Coverage Goals
- **100% of 67 Florida counties** automated
- **Daily updates** from county PA sites (when available)
- **9.7M+ parcels** fully synchronized
- **Sales history** updated within 24 hours of recording
- **Geometry data** refreshed monthly

### Quality Metrics
- **AI Quality Score**: Target 85%+ on all ingestions
- **Data Completeness**: 90%+ parcels with bedrooms, bathrooms, year_built
- **Sales Coverage**: 80%+ parcels with at least 1 sale record
- **Geometry Match**: 95%+ parcels matched to FGIO geometry

### Performance Benchmarks
- **Daily Sync Time**: < 2 hours for all 67 counties
- **API Response Time**: < 200ms for parcel lookup
- **Dashboard Load Time**: < 1 second
- **Search Performance**: < 500ms for autocomplete

### Cost Estimates
- **Railway Pro**: $20/month (orchestrator + cron)
- **Supabase Pro**: $25/month (database + storage)
- **Vercel Pro**: $20/month (dashboard)
- **OpenAI API**: ~$50/month (validation queries)
- **HuggingFace**: Free (Gemma 3 270M inference)
- **Sentry**: Free tier
- **Total**: ~$115/month

---

## 11. Risk Mitigation

### Risk 1: DOR Site Structure Changes
**Mitigation**:
- Playwright MCP for dynamic sites
- Fallback to manual Public Record Request form
- Alert on parsing failures

### Risk 2: County PA Site Incompatibility
**Mitigation**:
- Maintain county-specific parsers
- Firecrawl for automatic link discovery
- Human escalation for problematic counties

### Risk 3: Data Quality Issues
**Mitigation**:
- AI validation before production
- Staging tables for review
- Rollback capability on quality score < 70%

### Risk 4: Performance Degradation
**Mitigation**:
- Materialized views
- Batch processing with exponential backoff
- Horizontal scaling on Railway

---

## 12. Next Steps

1. **Review this analysis** with full team
2. **Approve budget** (~$115/month recurring)
3. **Prioritize Phase 1** implementation (foundation)
4. **Set up monitoring** (Sentry, CloudWatch)
5. **Begin development** following 5-week roadmap

---

**Document Version**: 1.0
**Last Updated**: 2025-10-05
**Author**: AI Data Engineering Team
**Status**: 🚀 READY FOR IMPLEMENTATION
