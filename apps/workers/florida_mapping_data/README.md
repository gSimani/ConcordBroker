# Florida Revenue Mapping Data Monitoring System

This system monitors, downloads, and processes GIS mapping data from the Florida Revenue data portal for property mapping and analysis.

## What is Florida Revenue Mapping Data?

Florida Revenue provides GIS mapping data for property analysis including:
- **Property parcel boundaries** - Exact boundaries of individual properties
- **Section, township, and range boundaries** - Public Land Survey System
- **Subdivision boundaries** - Platted subdivisions and developments  
- **Road centerlines and names** - Street network data
- **Water features and boundaries** - Lakes, rivers, wetlands
- **Municipal boundaries** - City and town limits
- **Special district boundaries** - CDD, MSBU, fire districts
- **Land use classifications** - Zoning and development types

## Components

### 1. Mapping Downloader (`mapping_downloader.py`)
- Scans Florida Revenue mapping data portal for available files
- Downloads shapefiles, geodatabases, and metadata
- Extracts ZIP archives automatically
- Tracks download history and file changes
- Supports county-specific and statewide datasets
- Rate limiting and error handling

### 2. GIS Parser (`gis_parser.py`)
- Parses shapefiles using multiple GIS libraries (pyshp, Fiona, GDAL)
- Extracts property parcel information
- Maps common field names across different datasets
- Calculates comprehensive statistics
- Exports to GeoJSON and CSV formats
- Handles large datasets with streaming

### 3. Monitor (`monitor.py`)
- Orchestrates scanning, downloading, and processing
- Daily checks for new mapping data (default: 6:00 AM)
- Weekly full scans and processing
- Priority county processing
- Tracks processing statistics and parcel counts

## GIS File Formats Supported

### Shapefiles (.shp)
- ESRI Shapefile format (most common)
- Contains geometry and attributes
- Consists of multiple files (.shp, .shx, .dbf, .prj)

### Geodatabases (.gdb)
- ESRI File Geodatabase format
- Contains multiple layers and metadata
- More advanced than shapefiles

### Metadata (.xml)
- Spatial metadata in XML format
- Describes coordinate systems and data quality

## Installation

### Required Libraries
```bash
# Core requirements
pip install requests
pip install schedule
pip install beautifulsoup4
pip install python-dotenv

# GIS libraries (install at least one)
pip install pyshp          # Simple shapefile reading
pip install fiona          # Advanced geospatial I/O
pip install gdal           # Full GIS functionality (complex install)
```

### GIS Library Notes

**pyshp (Recommended for basic use)**
- Lightweight and easy to install
- Good for reading shapefile attributes
- Limited geometry processing

**Fiona (Recommended for advanced use)**
- Clean API for geospatial data
- Better geometry handling
- Requires some system dependencies

**GDAL (Most powerful)**
- Industry standard GIS library
- Complex installation on Windows
- Full geometry and projection support

## Usage

### Download Mapping Data

```bash
# Scan for available files
python mapping_downloader.py --scan

# Download all available files
python mapping_downloader.py --download-all

# Download county-specific mapping
python mapping_downloader.py --county 06 --types parcels roads water

# Check download status
python mapping_downloader.py --status
```

### Parse GIS Files

```bash
# Parse a shapefile
python gis_parser.py parcels.shp --stats

# Parse with feature limit
python gis_parser.py parcels.shp --max-features 1000

# Export to different formats
python gis_parser.py parcels.shp --output-csv parcels.csv
python gis_parser.py parcels.shp --output-geojson parcels.geojson
```

### Monitor System

```bash
# Start continuous monitoring
python monitor.py --mode monitor --daily-time 06:00

# Run one-time scan
python monitor.py --mode scan

# Process extracted files
python monitor.py --mode process

# Process priority counties
python monitor.py --mode priority

# Show current status
python monitor.py --mode status
```

## Directory Structure

```
data/florida_mapping/
├── raw/                    # Downloaded ZIP files
│   ├── County_Parcels_2025.zip
│   ├── Road_Centerlines.zip
│   └── ...
├── extracted/              # Extracted shapefiles
│   ├── County_Parcels_2025/
│   │   ├── parcels.shp
│   │   ├── parcels.shx
│   │   ├── parcels.dbf
│   │   └── parcels.prj
│   └── ...
└── metadata/              # Download history and tracking
    └── download_history.json
```

## Common Attribute Fields

The parser automatically maps these common field variations:

### Parcel Identification
- `PARCEL_ID`, `PARCELID`, `PIN`, `PARID`, `PCL_ID`

### Owner Information
- `OWNER`, `OWNER_NAME`, `OWNERNAME`, `OWN_NAME`

### Property Address
- `ADDRESS`, `SITUS`, `SITE_ADDR`, `PROPERTY_ADDRESS`

### Land Use and Zoning
- `LANDUSE`, `LAND_USE`, `LU_CODE`, `USE_CODE`
- `ZONING`, `ZONE`, `ZONE_CODE`

### Property Characteristics
- `ACRES`, `ACREAGE`, `LOT_SIZE`, `AREA_ACRES`
- `ASSESSED`, `ASSESSED_VAL`, `TOTAL_VAL`, `JUST_VAL`

### Geographic References
- `COUNTY`, `CNTY`, `CO_NAME`, `COUNTY_NAME`
- `SUBDIVISION`, `SUBDIV`, `SUB_NAME`
- `SECTION`, `SEC`, `SECT`
- `TOWNSHIP`, `TWP`, `TOWN`
- `RANGE`, `RNG`, `RGE`

## Monitoring Schedule

- **Daily (6:00 AM)**: Scan for new files, download updates
- **Weekly (Sunday 5:00 AM)**: Full scan and process all files
- **On-demand**: Process priority counties

## Statistics Tracked

- Total mapping files downloaded
- Shapefiles processed
- Parcels extracted from GIS data
- Geographic coverage by county
- File sizes and processing times
- Common land use and zoning codes

## Performance

- **Download Speed**: ~2-10 MB/s depending on file size
- **Parse Speed**: ~5,000-50,000 features/second depending on complexity
- **Memory Usage**: Streaming processing, scales with feature complexity
- **Typical Processing Time**: 1-30 minutes per county depending on dataset size

## Data Statistics

- **File Types**: Shapefiles, Geodatabases, Metadata, Documentation
- **Typical Shapefile Size**: 5-500 MB per county
- **Features per County**: 10,000 - 2,000,000 parcels
- **Coordinate Systems**: Florida State Plane (various zones)
- **Update Frequency**: Varies (monthly to annually)

## Common Coordinate Systems

Florida mapping data typically uses:

- **Florida State Plane East (FIPS 0901)** - Miami-Dade, Broward
- **Florida State Plane West (FIPS 0902)** - Panhandle counties  
- **Florida State Plane North (FIPS 0903)** - North Florida
- **Universal Transverse Mercator (UTM) Zone 17N** - Some datasets
- **Geographic (Latitude/Longitude)** - WGS84 or NAD83

## Integration with Property System

This mapping data enhances property profiles by providing:

1. **Accurate Boundaries**
   - Exact parcel shapes for property visualization
   - Acreage calculations
   - Boundary disputes and overlaps

2. **Spatial Context**
   - Neighboring properties
   - Distance to roads, water, amenities
   - Zoning and land use patterns

3. **Geographic Analysis**
   - Property density mapping
   - Market area definition
   - Environmental constraints

4. **Address Validation**
   - Geocoding property addresses
   - Situs address standardization
   - Property location verification

## Error Handling

- **File not found**: Logged as warning, continue processing
- **Parse errors**: Feature-level errors logged, processing continues
- **Coordinate system issues**: Automatic detection and conversion
- **Large file handling**: Streaming processing to manage memory
- **Network timeouts**: Retry logic with exponential backoff

## Data Quality Considerations

### Common Issues
1. **Coordinate System Variations**
   - Different projections across counties
   - Mixed coordinate systems in single files

2. **Attribute Inconsistencies**  
   - Field name variations
   - Data type mismatches
   - Missing or null values

3. **Geometry Problems**
   - Invalid polygons
   - Self-intersecting boundaries
   - Topology errors

### Quality Checks
- Parcel ID uniqueness validation
- Geometry validity checking
- Attribute completeness scoring
- Coordinate system verification

## Troubleshooting

### Common Issues

1. **GIS Library Installation**
   ```bash
   # If pyshp fails to install
   pip install --upgrade setuptools wheel
   pip install pyshp
   
   # For Fiona on Windows
   pip install --find-links=https://girder.github.io/large_image_wheels fiona
   ```

2. **Shapefile Parse Errors**
   - Check if all shapefile components (.shp, .shx, .dbf) exist
   - Verify coordinate system file (.prj) is present
   - Try different GIS libraries if one fails

3. **Large File Processing**
   - Use `--max-features` to limit memory usage
   - Process in batches for very large datasets
   - Monitor system memory during processing

4. **Coordinate System Issues**
   - Check .prj file for projection information
   - Use GDAL for advanced coordinate transformations
   - Verify data is in expected geographic region

## Future Enhancements

- [ ] PostGIS database integration for spatial queries
- [ ] Coordinate system transformation and standardization
- [ ] Property boundary change detection
- [ ] Integration with property assessment data
- [ ] Web mapping service (WMS/WFS) support
- [ ] Mobile-friendly map visualization
- [ ] Automated topology checking and repair
- [ ] Real-time mapping data updates

## Example Use Cases

### Property Boundary Verification
```python
from gis_parser import GISParser

parser = GISParser()
result = parser.parse_shapefile("broward_parcels.shp")

# Find specific parcel
for feature in result['features']:
    if feature['mapped_fields'].get('parcel_id') == '504231242730':
        print(f"Parcel found with {feature['geometry']['points']} boundary points")
```

### Land Use Analysis
```python
# Extract parcels and analyze land use
parcels = parser.extract_parcels(result)
land_use_summary = {}

for parcel in parcels:
    land_use = parcel.get('land_use', 'Unknown')
    land_use_summary[land_use] = land_use_summary.get(land_use, 0) + 1

print("Land Use Distribution:")
for use, count in sorted(land_use_summary.items(), key=lambda x: x[1], reverse=True):
    print(f"  {use}: {count:,} parcels")
```

This mapping data system provides the spatial foundation for accurate property analysis and visualization in the ConcordBroker platform.