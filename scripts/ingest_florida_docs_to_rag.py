#!/usr/bin/env python3
"""
Florida Data Documentation Ingestion Script
============================================
Downloads and ingests Florida property/business data documentation
into the RAG knowledge base for AI agent use.

This ensures AI agents understand:
- NAL/SDF/NAP column definitions
- Sunbiz data structures
- GIS/Cadastral field meanings
- Data relationships and formats

Usage:
    python scripts/ingest_florida_docs_to_rag.py              # Full ingestion
    python scripts/ingest_florida_docs_to_rag.py --download   # Download only
    python scripts/ingest_florida_docs_to_rag.py --ingest     # Ingest only (assumes downloaded)
"""

import os
import sys
import json
import logging
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Knowledge base directory
KNOWLEDGE_BASE = ROOT / "knowledge" / "florida-data-sources"

# Documentation sources to download and ingest
DOCUMENTATION_SOURCES = [
    {
        "name": "NAL_SDF_NAP_Users_Guide_2024",
        "url": "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/User%20Guides/2024%20Users%20guide%20and%20quick%20reference/2024_NAL_SDF_NAP_Users_Guide.pdf",
        "category": "property",
        "description": "Florida Revenue NAL/SDF/NAP file format definitions",
        "priority": "critical"
    },
    {
        "name": "Broward_Export_Files_Layout",
        "url": "https://www.broward.org/RecordsTaxesTreasury/Records/Documents/ExportFilesLayout.pdf",
        "category": "county-specific",
        "description": "Broward County recording export file layouts",
        "priority": "medium"
    },
    {
        "name": "FDOR_Cadastral_Metadata",
        "url": "https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0?f=json",
        "category": "gis",
        "description": "Florida Cadastral parcel boundary field definitions",
        "priority": "high",
        "format": "json"
    }
]

# Text-based documentation to create (from web research)
TEXT_DOCUMENTATION = [
    {
        "name": "Sunbiz_Daily_Data_Guide",
        "category": "sunbiz",
        "content": """# Florida Sunbiz Daily Data Download Guide

## SFTP Access
- Host: sftp.floridados.gov
- Username: Public
- Password: PubAccess1845!

## Daily File Types

### Corporate Data (corporations, LLCs, limited partnerships)
- **yyyymmddc.txt** - Daily Corporate Filings
- **yyyymmddce.txt** - Daily Corporate Events

### Federal Tax Lien Data
- **yyyymmddflrf.txt** - Lien Filings
- **yyyymmddflre.txt** - Lien Events
- **yyyymmddflrd.txt** - Lien Debtors
- **yyyymmddflrs.txt** - Lien Secured Parties

### Fictitious Name Data
- **yyyymmddf.txt** - Fictitious Name Registrations
- **yyyymmddfe.txt** - Fictitious Name Events

### General Partnership Data
- **yyyymmddg.txt** - Partnership Filings
- **yyyymmddge.txt** - Partnership Events

### Trademark/Service Mark Data
- **yyyymmddtm.txt** - Mark Filings

## Update Frequency
Daily files are generated on work days and contain filings added that day.
No files created during holidays or office closures.

## Data Definitions
Detailed field definitions available at dos.sunbiz.org
"""
    },
    {
        "name": "Broward_Daily_Extract_Guide",
        "category": "county-specific",
        "content": """# Broward County Daily Index Extract Files

## Overview
Daily recording index files available for 7 days after creation.

## File Types

### CFN Files (MM-DD-YYcfn.txt)
One record per Clerk's File Number containing:
- Recording date/time
- Document type
- Consideration amount
- Book/page numbers
- Legal description
- Parcel ID

### Name Files (MM-DD-YYnme.txt)
Multiple name records per document:
- Party name
- Party type (direct or reverse)
- Name sequence

### Link Files (MM-DD-YYlnk.txt)
Links new recordings to prior related records.
Example: Satisfaction of Mortgage linked to original Mortgage

## File Format
- Delimiter: Pipe character (|)
- Trailing spaces removed
- Leading zeros removed from numeric data
- Empty fields: null (||)
- No activity: 0 byte file

## Scope
Broward County ONLY - other counties may have different systems.
"""
    },
    {
        "name": "Florida_GIS_Parcel_Data_Guide",
        "category": "gis",
        "content": """# Florida GIS Parcel Data Guide

## Statewide Parcel Data
Source: Florida Department of Revenue via Florida GIO

### Coverage
- 10.8+ million parcels across all 67 Florida counties
- Updated annually (August release from April submissions)
- Polygon and centroid versions available

### Available Formats
- CSV
- KML
- ESRI Shapefile
- GeoJSON
- File Geodatabase

### ArcGIS Feature Server Access
URL: https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer

Layer 0: FDOR Cadastral 2025
- Query Format: JSON only
- Max Records: 2000 per query
- Spatial Reference: 102967 (6439), meters
- Minimum Zoom: 1:250,000 scale

### Data Linkage
Parcel polygons are linked to NAL (Name-Address-Legal) file data.
Attribution includes FIPS county codes.

### Contact
- County Property Appraiser for parcel-specific questions
- FL DOR Property Tax Oversight: 850-717-6570
"""
    },
    {
        "name": "Florida_NAL_Column_Reference",
        "category": "property",
        "content": """# Florida NAL (Name-Address-Legal) Column Reference

## Critical Column Mappings (NAL -> florida_parcels table)

### Identifiers
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| CO_NO | county | INT | County code (11-77) |
| PARCEL_ID | parcel_id | TEXT | Primary parcel identifier |
| ASMNT_YR | year | INT | Assessment year |
| ALT_KEY | alt_key | TEXT | Alternative key |
| STATE_PAR_ID | state_par_id | TEXT | State parcel ID |

### Physical Address
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| PHY_ADDR1 | phy_addr1 | TEXT | Street address |
| PHY_ADDR2 | phy_addr2 | TEXT | Unit/Suite |
| PHY_CITY | phy_city | TEXT | City |
| PHY_ZIPCD | phy_zipcd | TEXT | ZIP code |

### Owner Information
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| OWN_NAME | owner_name | TEXT | Owner name |
| OWN_ADDR1 | owner_addr1 | TEXT | Mailing address 1 |
| OWN_ADDR2 | owner_addr2 | TEXT | Mailing address 2 |
| OWN_CITY | owner_city | TEXT | Owner city |
| OWN_STATE | owner_state | TEXT(2) | State (truncate to 2 chars!) |
| OWN_ZIPCD | owner_zip | TEXT | Owner ZIP |

### Property Values
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| JV | just_value | BIGINT | Just/Market value |
| AV_SD | assessed_value | BIGINT | Assessed value |
| TV_SD | taxable_value | BIGINT | Taxable value |
| LND_VAL | land_value | BIGINT | Land value |

### Building Characteristics
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| ACT_YR_BLT | year_built | INT | Actual year built |
| EFF_YR_BLT | eff_year_built | INT | Effective year built |
| TOT_LVG_AREA | total_living_area | INT | Living area sqft |
| LND_SQFOOT | land_sqft | BIGINT | Land square footage |
| DOR_UC | property_use | TEXT | Property use code |

### Sale Information
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| SALE_PRC1 | sale_price | BIGINT | Most recent sale price |
| SALE_YR1 | sale_yr1 | INT | Sale year |
| SALE_MO1 | sale_mo1 | INT | Sale month |
| sale_date | sale_date | DATE | Constructed: YYYY-MM-01 or NULL |

## County Codes (DOR Standard)
11=ALACHUA, 12=BAKER, 13=BAY, 14=BRADFORD, 15=BREVARD,
16=BROWARD, 17=CALHOUN, 18=CHARLOTTE, 19=CITRUS, 20=CLAY,
21=COLLIER, 22=COLUMBIA, 23=MIAMI-DADE, 24=DESOTO, 25=DIXIE,
26=DUVAL, 27=ESCAMBIA, 28=FLAGLER, 29=FRANKLIN, 30=GADSDEN,
31=GILCHRIST, 32=GLADES, 33=GULF, 34=HAMILTON, 35=HARDEE,
36=HENDRY, 37=HERNANDO, 38=HIGHLANDS, 39=HILLSBOROUGH, 40=HOLMES,
41=INDIAN RIVER, 42=JACKSON, 43=JEFFERSON, 44=LAFAYETTE, 45=LAKE,
46=LEE, 47=LEON, 48=LEVY, 49=LIBERTY, 50=MADISON,
51=MANATEE, 52=MARION, 53=MARTIN, 54=MONROE, 55=NASSAU,
56=OKALOOSA, 57=OKEECHOBEE, 58=ORANGE, 59=OSCEOLA, 60=PALM BEACH,
61=PASCO, 62=PINELLAS, 63=POLK, 64=PUTNAM, 65=ST. JOHNS,
66=ST. LUCIE, 67=SANTA ROSA, 68=SARASOTA, 69=SEMINOLE, 70=SUMTER,
71=SUWANNEE, 72=TAYLOR, 73=UNION, 74=VOLUSIA, 75=WAKULLA,
76=WALTON, 77=WASHINGTON

## Common Errors and Fixes
- owner_state too long: Truncate "FLORIDA" -> "FL"
- sale_date empty string: Use NULL instead
- NaN values: Convert to NULL for numeric, empty string for text
"""
    },
    {
        "name": "Florida_SDF_Column_Reference",
        "category": "property",
        "content": """# Florida SDF (Sales Data File) Column Reference

## Purpose
Sales Data File contains property transaction history for all 67 Florida counties.

## Key Columns

### Transaction Identifiers
| Column | Type | Description |
|--------|------|-------------|
| CO_NO | INT | County code |
| PARCEL_ID | TEXT | Parcel identifier |
| SALE_YR | INT | Year of sale |
| SALE_MO | INT | Month of sale |
| OR_BOOK | TEXT | Official Records book |
| OR_PAGE | TEXT | Official Records page |

### Sale Details
| Column | Type | Description |
|--------|------|-------------|
| SALE_PRC | BIGINT | Sale price |
| QUAL_CD | TEXT | Qualification code |
| VI_CD | TEXT | Validity indicator |
| MULTI_PAR | TEXT | Multi-parcel sale flag |

## Qualification Codes (Common)
- Q = Qualified (arm's length transaction)
- U = Unqualified
- V = Vacant land
- I = Improved property

## Validity Indicators
- 0 = Valid sale
- 1-9 = Various disqualification reasons

## Usage in ConcordBroker
Sales history is stored in `property_sales_history` table.
NAL file contains most recent 2 sales (SALE_PRC1, SALE_PRC2).
SDF contains full transaction history.
"""
    },
    {
        "name": "Data_Source_Integration_Matrix",
        "category": "reference",
        "content": """# ConcordBroker Data Source Integration Matrix

## Current Integration Status

| Source | Download | Database | RAG | API | Notes |
|--------|----------|----------|-----|-----|-------|
| FL Revenue NAL | YES | florida_parcels | NO | NO | 19M+ records |
| FL Revenue SDF | YES | property_sales_history | NO | NO | 96K+ records |
| FL Revenue NAP | YES | NOT USED | NO | NO | Tangible property |
| Sunbiz Daily | YES | florida_entities | NO | SFTP | 15M+ records |
| Sunbiz Quarterly | NO | - | NO | SFTP | Full snapshots |
| Broward Daily | NO | - | NO | HTTP | County-specific |
| GIS Cadastral | NO | - | NO | REST | 10.8M parcels |
| ArcGIS Parcels | NO | - | NO | REST | Boundaries |

## Database Tables

### florida_parcels
- Source: NAL files
- Records: 19,086,633
- Key: (parcel_id, county, year)
- Updates: Daily via monitor_florida_nal_updates.py

### property_sales_history
- Source: SDF files
- Records: 96,771
- Key: parcel_id + sale date
- Updates: Manual

### florida_entities
- Source: Sunbiz SFTP
- Records: 15,013,088
- Key: entity_id
- Updates: Daily via florida_daily_updater.py

### sunbiz_corporate
- Source: Sunbiz SFTP
- Records: 2,030,912
- Key: filing_number
- Updates: Daily

## Scheduled Updates

### GitHub Actions
- daily-property-update.yml: 2 AM EST daily
- daily-sunbiz-update.yml: Sunbiz data

### Manual Scripts
- scripts/monitor_florida_nal_updates.py
- scripts/upload_nal_to_supabase.py
- apps/agents/florida_daily_updater.py
"""
    }
]


def create_knowledge_base_structure():
    """Create the knowledge base directory structure"""
    categories = ["property", "sunbiz", "gis", "county-specific", "reference"]

    for category in categories:
        category_dir = KNOWLEDGE_BASE / category
        category_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {category_dir}")


def download_documentation(source: Dict) -> Optional[Path]:
    """Download a documentation source"""
    try:
        category_dir = KNOWLEDGE_BASE / source["category"]
        category_dir.mkdir(parents=True, exist_ok=True)

        # Determine file extension
        if source.get("format") == "json":
            ext = ".json"
        elif source["url"].endswith(".pdf"):
            ext = ".pdf"
        else:
            ext = ".txt"

        file_path = category_dir / f"{source['name']}{ext}"

        logger.info(f"Downloading: {source['name']}")
        logger.info(f"  URL: {source['url'][:80]}...")

        response = requests.get(source["url"], timeout=60)
        response.raise_for_status()

        # Save the file
        mode = "w" if source.get("format") == "json" else "wb"
        if mode == "w":
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
        else:
            with open(file_path, "wb") as f:
                f.write(response.content)

        logger.info(f"  Saved to: {file_path}")
        logger.info(f"  Size: {file_path.stat().st_size:,} bytes")

        return file_path

    except Exception as e:
        logger.error(f"  Download failed: {e}")
        return None


def create_text_documentation():
    """Create text-based documentation from research"""
    for doc in TEXT_DOCUMENTATION:
        category_dir = KNOWLEDGE_BASE / doc["category"]
        category_dir.mkdir(parents=True, exist_ok=True)

        file_path = category_dir / f"{doc['name']}.md"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(doc["content"])

        logger.info(f"Created: {file_path}")


def ingest_to_rag():
    """Ingest all documentation into the RAG system"""
    try:
        # Import RAG system
        from apps.langchain_system.rag import PropertyRAGSystem

        logger.info("Initializing RAG system...")
        rag = PropertyRAGSystem()

        # Load all markdown and text files
        logger.info("Loading documentation into RAG...")
        documents = rag.load_documents(
            str(KNOWLEDGE_BASE),
            "**/*.{md,txt,json}"
        )

        if documents:
            logger.info(f"Loaded {len(documents)} documents")

            # Add to vector store
            rag.add_documents(documents, category="florida_data_docs")
            logger.info("Documents added to vector store")
        else:
            logger.warning("No documents found to ingest")

    except ImportError as e:
        logger.warning(f"RAG system not available: {e}")
        logger.info("Documentation downloaded but not ingested into RAG")
    except Exception as e:
        logger.error(f"RAG ingestion failed: {e}")


def create_manifest():
    """Create a manifest of all ingested documentation"""
    manifest = {
        "generated": datetime.now().isoformat(),
        "knowledge_base": str(KNOWLEDGE_BASE),
        "sources": []
    }

    for source in DOCUMENTATION_SOURCES:
        manifest["sources"].append({
            "name": source["name"],
            "category": source["category"],
            "description": source["description"],
            "priority": source["priority"],
            "url": source["url"]
        })

    for doc in TEXT_DOCUMENTATION:
        manifest["sources"].append({
            "name": doc["name"],
            "category": doc["category"],
            "type": "generated",
            "description": f"Text documentation for {doc['category']}"
        })

    manifest_path = KNOWLEDGE_BASE / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest saved to: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download and ingest Florida data documentation into RAG"
    )
    parser.add_argument('--download', action='store_true', help='Download only')
    parser.add_argument('--ingest', action='store_true', help='Ingest only')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("FLORIDA DATA DOCUMENTATION INGESTION")
    logger.info("=" * 70)

    # Create directory structure
    create_knowledge_base_structure()

    if not args.ingest:
        # Download external documentation
        logger.info("\n[STEP 1] Downloading external documentation...")
        downloaded = []
        for source in DOCUMENTATION_SOURCES:
            result = download_documentation(source)
            if result:
                downloaded.append(result)

        logger.info(f"Downloaded {len(downloaded)} of {len(DOCUMENTATION_SOURCES)} files")

        # Create text documentation
        logger.info("\n[STEP 2] Creating text documentation...")
        create_text_documentation()

    if not args.download:
        # Ingest into RAG
        logger.info("\n[STEP 3] Ingesting into RAG system...")
        ingest_to_rag()

    # Create manifest
    logger.info("\n[STEP 4] Creating manifest...")
    create_manifest()

    logger.info("\n" + "=" * 70)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Knowledge base: {KNOWLEDGE_BASE}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
