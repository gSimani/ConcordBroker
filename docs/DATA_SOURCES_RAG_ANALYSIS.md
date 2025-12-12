# Florida Data Sources & RAG Integration Analysis

## Executive Summary

**Current Status**: RAG infrastructure EXISTS but is NOT populated with critical Florida data documentation.

The project has a production-ready LangChain RAG system (`apps/langchain_system/`) with FAISS vector stores, but only contains placeholder test documents. **No actual Florida data documentation has been ingested.**

---

## Data Sources Analysis

### 1. Florida Revenue NAL/SDF/NAP User Guide
**URL**: `https://floridarevenue.com/.../2024_NAL_SDF_NAP_Users_Guide.pdf`

| Aspect | Status | Priority |
|--------|--------|----------|
| Currently Ingested | NO | **HIGH** |
| Needed For | Column definitions, data types, file formats | |
| AI Agent Use | Property data parsing, field validation | |

**Recommendation**: MUST ingest. This is the authoritative source for understanding NAL (Name-Address-Legal), SDF (Sales Data File), and NAP (Tangible Personal Property) formats used in our upload scripts.

---

### 2. Broward County Export Files Layout
**URL**: `https://www.broward.org/.../ExportFilesLayout.pdf`

| Aspect | Status | Priority |
|--------|--------|----------|
| Currently Ingested | NO | MEDIUM |
| Scope | Broward County ONLY | |
| Contents | Recording data formats | |

**Recommendation**: Useful for Broward-specific queries. Not universal - each county may have different formats.

---

### 3. Broward County Daily Index Extract Files
**URL**: `https://www.broward.org/.../DailyIndexExtractFiles.aspx`

| Aspect | Status | Priority |
|--------|--------|----------|
| Currently Ingested | NO | MEDIUM |
| Scope | Broward County ONLY | |
| Update Frequency | Daily, retained 7 days | |

**Data Available**:
- **CFN Files** (MM-DD-YYcfn.txt): Recording data, document types, consideration amounts, parcel IDs
- **Name Files** (MM-DD-YYnme.txt): Party names and types
- **Link Files** (MM-DD-YYlnk.txt): Links between recordings

**Format**: Pipe-delimited (|), trailing spaces removed, null = empty field (||)

**Recommendation**: Research if other counties offer similar services. Useful for tracking recent recordings.

---

### 4. Florida Revenue Map Data
**URL**: `https://floridarevenue.com/.../Map+Data`

| Aspect | Status | Priority |
|--------|--------|----------|
| Currently Ingested | NO | HIGH |
| Data Type | GIS/Parcel boundaries | |

**Recommendation**: Important for geographic queries and parcel visualization.

---

### 5. Sunbiz Data Downloads (Florida DOS)
**URL**: `https://dos.fl.gov/sunbiz/other-services/data-downloads/`

| Aspect | Status | Priority |
|--------|--------|----------|
| Currently Ingested | PARTIAL (updater exists) | HIGH |
| SFTP Access | sftp.floridados.gov | |
| Credentials | Public / PubAccess1845! | |

**Already Integrated**: `apps/agents/florida_daily_updater.py` downloads Sunbiz data!

**Data Categories**:
| File Type | Filename Format | Contents |
|-----------|-----------------|----------|
| Corporate | yyyymmddc.txt | Corps, LLCs, LPs |
| Corp Events | yyyymmddce.txt | Filing events |
| Federal Tax Liens | yyyymmddflrf.txt | Lien filings |
| Lien Events | yyyymmddflre.txt | Lien events |
| Lien Debtors | yyyymmddflrd.txt | Debtor info |
| Lien Secured | yyyymmddflrs.txt | Secured parties |
| Fictitious Names | yyyymmddf.txt | DBA registrations |
| Fictitious Events | yyyymmddfe.txt | DBA events |
| Partnerships | yyyymmddg.txt | GP filings |
| Partnership Events | yyyymmddge.txt | GP events |
| Marks | yyyymmddtm.txt | Trademarks/service marks |

**Recommendation**: Documentation should be ingested for AI agents to understand data structures.

---

### 6. Sunbiz Daily Data
**URL**: `https://dos.fl.gov/sunbiz/other-services/data-downloads/daily-data/`

| Aspect | Status | Priority |
|--------|--------|----------|
| Integration | EXISTS in florida_daily_updater.py | |
| Documentation Ingested | NO | HIGH |

**Recommendation**: Ingest data definitions for AI to properly interpret entity statuses, filing types, etc.

---

### 7. Sunbiz Quarterly Data
**URL**: `https://dos.fl.gov/sunbiz/other-services/data-downloads/quarterly-data/`

| Aspect | Status | Priority |
|--------|--------|----------|
| Integration | NOT implemented | MEDIUM |
| Use Case | Full data snapshots | |

**Recommendation**: Consider implementing quarterly full refresh capability.

---

### 8. Florida GIO Open Data Portal
**URL**: `https://geodata.floridagio.gov/`

| Aspect | Status | Priority |
|--------|--------|----------|
| Currently Ingested | NO | HIGH |
| Data Volume | 10.8M parcels across 67 counties | |
| Formats | CSV, KML, Shapefile, GeoJSON | |

**Key Datasets**:
- 2025 Statewide Parcel Data (polygon + centroid)
- Boundaries
- Planning & Surveying
- Structure data

**Recommendation**: Critical for GIS capabilities. Should integrate with mapping features.

---

### 9. Florida Statewide Cadastral Feature Server
**URL**: `https://services9.arcgis.com/.../Florida_Statewide_Cadastral/FeatureServer`

| Aspect | Status | Priority |
|--------|--------|----------|
| Currently Integrated | NO | HIGH |
| Layer | FDOR Cadastral 2025 (Layer 0) | |
| Records | 10.8M+ parcels | |
| Query Limit | 2000 records per query | |

**Data Attributes**:
- Linked to NAL file data
- FIPS county codes
- Updated August 2025 from April submissions

**Access**: JSON queries, max 2000 records, requires zoom to 1:250,000 scale

**Recommendation**: Implement ArcGIS REST API integration for parcel boundary queries.

---

## Current RAG System Status

### Infrastructure (EXISTS)
```
apps/langchain_system/
├── rag.py           # PropertyRAGSystem with FAISS
├── core.py          # LangChain core setup
├── config.py        # Configuration
└── enhanced_rag_service.py  # Graph-enhanced RAG
```

### Vector Stores (EMPTY except smoke_test)
```
vector_stores/
└── smoke_test/      # Only placeholder data
    ├── index.faiss
    └── index.pkl
```

### What's Missing
1. **No documentation ingested** for any Florida data source
2. **No field definitions** for NAL/SDF/NAP columns
3. **No Sunbiz data structure** documentation
4. **No GIS metadata** or parcel field definitions

---

## Recommendations

### Priority 1: CRITICAL (Ingest Immediately)

| Document | Why | Impact |
|----------|-----|--------|
| 2024 NAL/SDF/NAP Users Guide | Defines ALL property data columns | Upload script accuracy |
| Sunbiz Data Definitions | Defines entity fields | Entity matching accuracy |
| FDOR Cadastral Metadata | Parcel boundary attributes | GIS integration |

### Priority 2: HIGH (Within 1 Week)

| Action | Description |
|--------|-------------|
| Download all PDFs | Cache locally for RAG ingestion |
| Create knowledge base folder | `knowledge/florida-data-sources/` |
| Implement PDF ingestion pipeline | Use PyPDF2 or similar |
| Populate vector stores | Chunk and embed documentation |

### Priority 3: MEDIUM (Within 1 Month)

| Action | Description |
|--------|-------------|
| Research county-specific APIs | Check if other counties offer Broward-style daily extracts |
| Implement ArcGIS integration | Query parcel boundaries via REST API |
| Add quarterly Sunbiz refresh | Full data snapshots |

---

## Implementation Plan

### Step 1: Create Knowledge Base Directory
```bash
mkdir -p knowledge/florida-data-sources/{property,sunbiz,gis,county-specific}
```

### Step 2: Download Documentation
```python
# URLs to download and ingest
DOCS_TO_INGEST = [
    {
        "name": "NAL_SDF_NAP_Users_Guide",
        "url": "https://floridarevenue.com/property/dataportal/Documents/...",
        "category": "property"
    },
    {
        "name": "Sunbiz_Data_Usage_Guide",
        "url": "https://dos.fl.gov/sunbiz/other-services/data-downloads/",
        "category": "sunbiz"
    },
    {
        "name": "FDOR_Cadastral_Metadata",
        "url": "https://services9.arcgis.com/.../Florida_Statewide_Cadastral/FeatureServer/0?f=json",
        "category": "gis"
    }
]
```

### Step 3: Ingest into RAG
```python
from apps.langchain_system.rag import PropertyRAGSystem

rag = PropertyRAGSystem()
rag.load_documents("knowledge/florida-data-sources/", "**/*.{pdf,txt,md}")
rag.add_documents(documents, category="property_docs")
```

### Step 4: Update AI Agent Prompts
- Add context about available data sources
- Include field definitions in system prompts
- Reference documentation for data interpretation

---

## Data Source Integration Matrix

| Source | Download | Database | RAG | API |
|--------|----------|----------|-----|-----|
| FL Revenue NAL | YES | YES | NO | NO |
| FL Revenue SDF | YES | YES | NO | NO |
| FL Revenue NAP | YES | NO | NO | NO |
| Sunbiz Daily | YES | YES | NO | YES |
| Sunbiz Quarterly | NO | NO | NO | NO |
| Broward Daily | NO | NO | NO | NO |
| GIS Cadastral | NO | NO | NO | NO |
| ArcGIS REST | NO | NO | NO | NO |

**Legend**: YES = Implemented, NO = Not Implemented

---

## Next Steps

1. **Immediate**: Download the NAL/SDF/NAP Users Guide PDF and extract text
2. **This Week**: Create knowledge base structure and begin ingestion
3. **Next Sprint**: Implement ArcGIS REST API for parcel boundaries
4. **Ongoing**: Monitor for documentation updates annually

---

*Generated: 2025-12-12*
*Last Updated: 2025-12-12*
