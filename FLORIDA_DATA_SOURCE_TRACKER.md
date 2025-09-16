# Florida Data Source Tracker
## Complete Database Inventory & Status

Last Updated: 2025-01-09

---

## 1. FLORIDA REVENUE DATA PORTAL 
**URL:** https://floridarevenue.com/property/dataportal/Pages/default.aspx
**Path:** /property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files

### Downloaded Files ✅
| Database | File | Status | Size | Records | Last Updated |
|----------|------|--------|------|---------|--------------|
| **NAL** (Name/Address/Legal) | NAL16P202501.csv | ✅ Downloaded | ~500MB | 1.2M+ | 2025-01 |
| **NAP** (Non-Ad Valorem Assessment) | NAP16P202501.csv | ✅ Downloaded | ~200MB | 500K+ | 2025-01 |
| **NAV** (Value Assessment) | broward_nav_2025.zip | ✅ Downloaded | ~300MB | 800K+ | 2025-01 |
| **SDF** (Sales Data File) | SDF16P202501.csv | ✅ Downloaded | ~150MB | 300K+ | 2025-01 |
| **TPP** (Tangible Personal Property) | broward_tpp_2025.zip | ✅ Downloaded | ~100MB | 200K+ | 2025-01 |

### Pending Downloads ⏳
| Database | Status | Priority | Notes |
|----------|--------|----------|-------|
| **RER** (Real Estate Transfer) | Not Downloaded | High | Contains deed transfers |
| **CDF** (Code Definition File) | Not Downloaded | Medium | Property use codes |
| **JVS** (Just Value Study) | Not Downloaded | Low | Market analysis data |

---

## 2. MAP DATA
**URL:** https://floridarevenue.com/property/dataportal/Pages/default.aspx
**Path:** /property/dataportal/Documents/PTO+Data+Portal/Map+Data

### Status: ❌ Not Downloaded
| Dataset | Format | Priority | Use Case |
|---------|--------|----------|----------|
| Parcel Boundaries | SHP/GeoJSON | High | Property mapping |
| Plat Maps | PDF/TIF | Medium | Legal boundaries |
| Aerial Imagery | TIF/ECW | Low | Visual reference |
| Tax Maps | PDF | Medium | Assessment districts |

### Download Script Needed:
```bash
# Map data download URLs (to be implemented)
https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/Broward/
```

---

## 3. SUNBIZ BUSINESS DATA
**SFTP Details:**
- **Host:** sftp.floridados.gov
- **Username:** Public
- **Password:** PubAccess1845!
- **Protocol:** SFTP (Port 22)

### Status: ✅ Pipeline Configured
| Dataset | Status | Location | Update Frequency |
|---------|--------|----------|------------------|
| Business Entities | ✅ Pipeline Ready | /sunbiz/entities/ | Weekly |
| Officers/Directors | ✅ Pipeline Ready | /sunbiz/officers/ | Weekly |
| Annual Reports | ⏳ Pending | /sunbiz/reports/ | Monthly |
| Document Images | ❌ Not Configured | /sunbiz/images/ | On-demand |

### Active Pipeline:
- **Script:** apps/api/sunbiz_pipeline.py
- **Config:** apps/api/sunbiz_config.json
- **Schema:** apps/api/sunbiz_schema.sql

---

## 4. FLORIDA GEOSPATIAL OPEN DATA PORTAL
**URL:** https://geodata.floridagio.gov/

### Status: ❌ Not Integrated
| Dataset | API Endpoint | Priority | Use Case |
|---------|-------------|----------|----------|
| Parcel Centroids | /datasets/parcels | High | Geocoding |
| County Boundaries | /datasets/counties | Medium | Jurisdiction |
| Flood Zones | /datasets/floods | High | Risk analysis |
| School Districts | /datasets/schools | Medium | Demographics |
| Zoning | /datasets/zoning | High | Land use |

### Integration Needed:
```python
# API endpoints to implement
BASE_URL = "https://geodata.floridagio.gov/api/v1/"
DATASETS = [
    "parcels",
    "counties", 
    "floods",
    "schools",
    "zoning"
]
```

---

## 5. FLORIDA STATEWIDE CADASTRAL (ArcGIS)
**URL:** https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer

### Status: ❌ Not Connected
| Layer | ID | Fields | Records |
|-------|-----|--------|---------|
| Parcels | 0 | 50+ fields | 8M+ statewide |
| Counties | 1 | County codes | 67 counties |
| Cities | 2 | Municipal boundaries | 400+ cities |
| Tax Districts | 3 | Special districts | 1000+ |

### County Codes (Broward = 06):
```json
{
  "01": "Alachua",
  "06": "Broward",
  "13": "Dade",
  "50": "Palm Beach",
  "// ...": "67 total counties"
}
```

### REST API Query Example:
```python
# Query Broward parcels
url = "https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0/query"
params = {
    "where": "CNTYCD='06'",  # Broward County
    "outFields": "*",
    "f": "json",
    "returnGeometry": True
}
```

---

## 6. COUNTY PROPERTY APPRAISER SITES

### Broward County (BCPA)
- **URL:** https://web.bcpa.net/
- **API:** Limited public API
- **Status:** ✅ Web scraping configured

### Miami-Dade County
- **URL:** https://www.miamidade.gov/pa/
- **Status:** ❌ Not configured

### Palm Beach County  
- **URL:** https://www.pbcgov.com/papa/
- **Status:** ❌ Not configured

---

## 7. DATA PIPELINE STATUS

### Active Agents ✅
```python
ACTIVE_AGENTS = {
    'tpp_agent': 'apps/workers/tpp/main.py',
    'nav_agent': 'apps/workers/nav_assessments/main.py', 
    'sdf_agent': 'apps/workers/sdf_sales/main.py',
    'sunbiz_agent': 'apps/api/sunbiz_pipeline.py',
    'bcpa_agent': 'apps/workers/bcpa_scraper.py'
}
```

### Pending Agents ⏳
```python
PENDING_AGENTS = {
    'map_agent': None,  # GIS/Map data
    'geodata_agent': None,  # Florida Geospatial
    'arcgis_agent': None,  # ArcGIS REST API
    'flood_agent': None,  # FEMA flood zones
    'census_agent': None  # Demographics
}
```

---

## 8. DATABASE STORAGE

### Supabase Tables Created ✅
- florida_parcels (main)
- fl_tpp_accounts
- fl_nav_parcel_summary  
- fl_sdf_sales
- fl_nal_name_address
- fl_nap_assessments
- sunbiz_entities
- sunbiz_officers
- entity_property_matches

### Missing Tables ❌
- map_parcels (GIS geometry)
- flood_zones
- school_districts
- zoning_districts
- property_images

---

## 9. DOWNLOAD AUTOMATION SCRIPT

```python
# Master download script needed
import asyncio
from pathlib import Path

FLORIDA_DATA_SOURCES = {
    'revenue_portal': {
        'base_url': 'https://floridarevenue.com/property/dataportal/',
        'datasets': ['NAL', 'NAP', 'NAV', 'SDF', 'TPP', 'RER', 'CDF', 'JVS'],
        'frequency': 'monthly'
    },
    'sunbiz_sftp': {
        'host': 'sftp.floridados.gov',
        'credentials': {'user': 'Public', 'pass': 'PubAccess1845!'},
        'datasets': ['entities', 'officers', 'reports'],
        'frequency': 'weekly'
    },
    'geodata_api': {
        'base_url': 'https://geodata.floridagio.gov/api/v1/',
        'datasets': ['parcels', 'floods', 'zoning'],
        'frequency': 'quarterly'
    },
    'arcgis_rest': {
        'base_url': 'https://services9.arcgis.com/Gh9awoU677aKree0/',
        'service': 'Florida_Statewide_Cadastral',
        'frequency': 'on_demand'
    }
}

async def download_all_florida_data():
    """Master function to download all Florida datasets"""
    # Implementation needed
    pass
```

---

## 10. QUICK REFERENCE LINKS

### Essential URLs
1. **Florida Revenue Data Portal:** https://floridarevenue.com/property/dataportal
2. **Sunbiz SFTP:** sftp://Public:PubAccess1845!@sftp.floridados.gov
3. **Florida Geospatial:** https://geodata.floridagio.gov
4. **ArcGIS Cadastral:** https://services9.arcgis.com/Gh9awoU677aKree0
5. **BCPA:** https://web.bcpa.net

### Documentation
- [DOR File Layouts](https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/File%20Layouts/)
- [Sunbiz Data Dictionary](https://dos.myflorida.com/sunbiz/data-download/)
- [ArcGIS REST API](https://developers.arcgis.com/rest/)

---

## ACTION ITEMS

### Immediate Priority 🔴
1. [ ] Download Map Data from Florida Revenue
2. [ ] Connect to ArcGIS REST API for cadastral data
3. [ ] Integrate Florida Geospatial Portal API
4. [ ] Download RER (Real Estate Transfer) files

### Medium Priority 🟡
1. [ ] Set up automated SFTP sync for Sunbiz
2. [ ] Configure flood zone data ingestion
3. [ ] Add school district boundaries
4. [ ] Download CDF (Code Definition) files

### Low Priority 🟢
1. [ ] Historical data archives
2. [ ] Property images from appraisers
3. [ ] Aerial imagery integration
4. [ ] Census demographic data

---

## NOTES
- County Code 06 = Broward County
- All Florida Revenue files use YYPMMMMMDD format (YY=year, P=period, MMMMMM=county, DD=day)
- Sunbiz data updates weekly on Sundays
- ArcGIS has rate limits: 1000 records per query
- Map data files can be very large (>1GB per county)