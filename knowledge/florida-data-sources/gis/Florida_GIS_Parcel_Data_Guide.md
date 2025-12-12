# Florida GIS Parcel Data Guide

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
