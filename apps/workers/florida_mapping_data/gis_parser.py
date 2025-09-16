"""
Parser for Florida Revenue GIS Mapping Data
Processes shapefiles and geodatabase files for property mapping
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import csv

# Optional GIS libraries (will check availability)
try:
    import shapefile  # pyshp library
    HAS_SHAPEFILE = True
except ImportError:
    HAS_SHAPEFILE = False
    
try:
    import fiona
    HAS_FIONA = True
except ImportError:
    HAS_FIONA = False

try:
    from osgeo import ogr, osr
    HAS_GDAL = True
except ImportError:
    HAS_GDAL = False

logger = logging.getLogger(__name__)

class GISParser:
    """Parser for GIS mapping data files"""
    
    # Common shapefile components
    SHAPEFILE_EXTENSIONS = ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.cpg']
    
    # Common attribute fields in property mapping data
    COMMON_FIELDS = {
        'parcel_id': ['PARCEL_ID', 'PARCELID', 'PIN', 'PARID', 'PCL_ID'],
        'owner_name': ['OWNER', 'OWNER_NAME', 'OWNERNAME', 'OWN_NAME'],
        'address': ['ADDRESS', 'SITUS', 'SITE_ADDR', 'PROPERTY_ADDRESS'],
        'land_use': ['LANDUSE', 'LAND_USE', 'LU_CODE', 'USE_CODE'],
        'zoning': ['ZONING', 'ZONE', 'ZONE_CODE'],
        'acreage': ['ACRES', 'ACREAGE', 'LOT_SIZE', 'AREA_ACRES'],
        'assessed_value': ['ASSESSED', 'ASSESSED_VAL', 'TOTAL_VAL', 'JUST_VAL'],
        'county': ['COUNTY', 'CNTY', 'CO_NAME', 'COUNTY_NAME'],
        'subdivision': ['SUBDIVISION', 'SUBDIV', 'SUB_NAME'],
        'section': ['SECTION', 'SEC', 'SECT'],
        'township': ['TOWNSHIP', 'TWP', 'TOWN'],
        'range': ['RANGE', 'RNG', 'RGE']
    }
    
    def __init__(self):
        """Initialize GIS parser"""
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check which GIS libraries are available"""
        dependencies = {
            'shapefile': HAS_SHAPEFILE,
            'fiona': HAS_FIONA,
            'gdal': HAS_GDAL
        }
        
        logger.info("GIS library availability:")
        for lib, available in dependencies.items():
            status = "Available" if available else "Not installed"
            logger.info(f"  {lib}: {status}")
        
        if not any(dependencies.values()):
            logger.warning("No GIS libraries available. Install pyshp, fiona, or GDAL for full functionality")
    
    def parse_shapefile(self, shapefile_path: Path, max_features: Optional[int] = None) -> Dict:
        """
        Parse a shapefile and extract property data
        
        Args:
            shapefile_path: Path to .shp file
            max_features: Maximum features to parse (None for all)
            
        Returns:
            Parsed data with features and metadata
        """
        if not shapefile_path.exists():
            return {
                'success': False,
                'error': f"Shapefile not found: {shapefile_path}"
            }
        
        # Try different parsing methods based on available libraries
        if HAS_SHAPEFILE:
            return self._parse_with_pyshp(shapefile_path, max_features)
        elif HAS_FIONA:
            return self._parse_with_fiona(shapefile_path, max_features)
        elif HAS_GDAL:
            return self._parse_with_gdal(shapefile_path, max_features)
        else:
            # Fallback to DBF parsing only
            return self._parse_dbf_only(shapefile_path, max_features)
    
    def _parse_with_pyshp(self, shapefile_path: Path, max_features: Optional[int] = None) -> Dict:
        """Parse shapefile using pyshp library"""
        logger.info(f"Parsing shapefile with pyshp: {shapefile_path}")
        
        try:
            sf = shapefile.Reader(str(shapefile_path))
            
            # Get metadata
            metadata = {
                'shape_type': sf.shapeTypeName,
                'num_records': sf.numRecords,
                'bbox': sf.bbox,
                'fields': [field[0] for field in sf.fields[1:]]  # Skip deletion flag
            }
            
            # Parse features
            features = []
            field_names = [field[0] for field in sf.fields[1:]]
            
            for i, shape_record in enumerate(sf.iterShapeRecords()):
                if max_features and i >= max_features:
                    break
                
                # Get geometry
                shape = shape_record.shape
                geometry = {
                    'type': shape.shapeTypeName,
                    'bbox': shape.bbox if hasattr(shape, 'bbox') else None,
                    'points': len(shape.points) if hasattr(shape, 'points') else 0
                }
                
                # Get attributes
                attributes = dict(zip(field_names, shape_record.record))
                
                # Map to common fields
                mapped = self._map_common_fields(attributes)
                
                feature = {
                    'id': i,
                    'geometry': geometry,
                    'attributes': attributes,
                    'mapped_fields': mapped
                }
                
                features.append(feature)
                
                if (i + 1) % 1000 == 0:
                    logger.debug(f"Parsed {i + 1} features")
            
            # Calculate statistics
            stats = self._calculate_statistics(features)
            
            return {
                'success': True,
                'file': str(shapefile_path),
                'metadata': metadata,
                'total_features': len(features),
                'features': features,
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error parsing shapefile with pyshp: {e}")
            return {
                'success': False,
                'error': str(e),
                'file': str(shapefile_path)
            }
    
    def _parse_with_fiona(self, shapefile_path: Path, max_features: Optional[int] = None) -> Dict:
        """Parse shapefile using Fiona library"""
        logger.info(f"Parsing shapefile with Fiona: {shapefile_path}")
        
        try:
            import fiona
            
            features = []
            
            with fiona.open(str(shapefile_path), 'r') as src:
                # Get metadata
                metadata = {
                    'driver': src.driver,
                    'crs': src.crs,
                    'bounds': src.bounds,
                    'schema': src.schema,
                    'num_features': len(src)
                }
                
                # Parse features
                for i, feature in enumerate(src):
                    if max_features and i >= max_features:
                        break
                    
                    # Map common fields
                    mapped = self._map_common_fields(feature['properties'])
                    
                    parsed_feature = {
                        'id': feature.get('id', i),
                        'geometry': feature['geometry'],
                        'attributes': feature['properties'],
                        'mapped_fields': mapped
                    }
                    
                    features.append(parsed_feature)
                    
                    if (i + 1) % 1000 == 0:
                        logger.debug(f"Parsed {i + 1} features")
            
            # Calculate statistics
            stats = self._calculate_statistics(features)
            
            return {
                'success': True,
                'file': str(shapefile_path),
                'metadata': metadata,
                'total_features': len(features),
                'features': features,
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error parsing shapefile with Fiona: {e}")
            return {
                'success': False,
                'error': str(e),
                'file': str(shapefile_path)
            }
    
    def _parse_with_gdal(self, shapefile_path: Path, max_features: Optional[int] = None) -> Dict:
        """Parse shapefile using GDAL/OGR library"""
        logger.info(f"Parsing shapefile with GDAL: {shapefile_path}")
        
        try:
            from osgeo import ogr
            
            # Open shapefile
            driver = ogr.GetDriverByName('ESRI Shapefile')
            dataSource = driver.Open(str(shapefile_path), 0)  # 0 means read-only
            
            if not dataSource:
                return {
                    'success': False,
                    'error': f"Could not open shapefile: {shapefile_path}"
                }
            
            layer = dataSource.GetLayer()
            
            # Get metadata
            metadata = {
                'feature_count': layer.GetFeatureCount(),
                'extent': layer.GetExtent(),
                'geometry_type': layer.GetGeomType(),
                'spatial_ref': str(layer.GetSpatialRef()) if layer.GetSpatialRef() else None
            }
            
            # Get field definitions
            layerDefn = layer.GetLayerDefn()
            field_names = []
            for i in range(layerDefn.GetFieldCount()):
                field_names.append(layerDefn.GetFieldDefn(i).GetName())
            
            metadata['fields'] = field_names
            
            # Parse features
            features = []
            feature_count = 0
            
            for feature in layer:
                if max_features and feature_count >= max_features:
                    break
                
                # Get geometry
                geom = feature.GetGeometryRef()
                geometry = {
                    'type': geom.GetGeometryName() if geom else None,
                    'point_count': geom.GetPointCount() if geom else 0
                }
                
                # Get attributes
                attributes = {}
                for field_name in field_names:
                    attributes[field_name] = feature.GetField(field_name)
                
                # Map common fields
                mapped = self._map_common_fields(attributes)
                
                parsed_feature = {
                    'id': feature.GetFID(),
                    'geometry': geometry,
                    'attributes': attributes,
                    'mapped_fields': mapped
                }
                
                features.append(parsed_feature)
                feature_count += 1
                
                if feature_count % 1000 == 0:
                    logger.debug(f"Parsed {feature_count} features")
            
            # Close datasource
            dataSource = None
            
            # Calculate statistics
            stats = self._calculate_statistics(features)
            
            return {
                'success': True,
                'file': str(shapefile_path),
                'metadata': metadata,
                'total_features': len(features),
                'features': features,
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error parsing shapefile with GDAL: {e}")
            return {
                'success': False,
                'error': str(e),
                'file': str(shapefile_path)
            }
    
    def _parse_dbf_only(self, shapefile_path: Path, max_features: Optional[int] = None) -> Dict:
        """Parse only the DBF (attribute) file without geometry"""
        dbf_path = shapefile_path.with_suffix('.dbf')
        
        if not dbf_path.exists():
            return {
                'success': False,
                'error': f"DBF file not found: {dbf_path}"
            }
        
        logger.info(f"Parsing DBF attributes only: {dbf_path}")
        
        # This is a simplified DBF parser
        # For production, use dbfread or similar library
        return {
            'success': False,
            'error': "DBF-only parsing not implemented. Install pyshp, fiona, or GDAL"
        }
    
    def _map_common_fields(self, attributes: Dict) -> Dict:
        """
        Map attribute fields to common field names
        
        Args:
            attributes: Feature attributes dictionary
            
        Returns:
            Dictionary with mapped common fields
        """
        mapped = {}
        
        # Convert attribute keys to uppercase for comparison
        upper_attrs = {k.upper(): v for k, v in attributes.items()}
        
        for common_name, possible_names in self.COMMON_FIELDS.items():
            for possible_name in possible_names:
                if possible_name in upper_attrs:
                    mapped[common_name] = upper_attrs[possible_name]
                    break
        
        return mapped
    
    def _calculate_statistics(self, features: List[Dict]) -> Dict:
        """
        Calculate statistics for parsed features
        
        Args:
            features: List of parsed features
            
        Returns:
            Statistics dictionary
        """
        if not features:
            return {}
        
        stats = {
            'total_features': len(features),
            'has_parcel_id': 0,
            'has_owner_name': 0,
            'has_address': 0,
            'has_geometry': 0,
            'unique_parcels': set(),
            'land_use_counts': {},
            'zoning_counts': {}
        }
        
        for feature in features:
            mapped = feature.get('mapped_fields', {})
            
            if mapped.get('parcel_id'):
                stats['has_parcel_id'] += 1
                stats['unique_parcels'].add(mapped['parcel_id'])
            
            if mapped.get('owner_name'):
                stats['has_owner_name'] += 1
            
            if mapped.get('address'):
                stats['has_address'] += 1
            
            if feature.get('geometry'):
                stats['has_geometry'] += 1
            
            # Count land use
            if mapped.get('land_use'):
                land_use = str(mapped['land_use'])
                stats['land_use_counts'][land_use] = stats['land_use_counts'].get(land_use, 0) + 1
            
            # Count zoning
            if mapped.get('zoning'):
                zoning = str(mapped['zoning'])
                stats['zoning_counts'][zoning] = stats['zoning_counts'].get(zoning, 0) + 1
        
        stats['unique_parcels'] = len(stats['unique_parcels'])
        
        # Get top land uses
        if stats['land_use_counts']:
            stats['top_land_uses'] = dict(sorted(
                stats['land_use_counts'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])
        
        # Get top zoning
        if stats['zoning_counts']:
            stats['top_zoning'] = dict(sorted(
                stats['zoning_counts'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])
        
        return stats
    
    def extract_parcels(self, parsed_data: Dict) -> List[Dict]:
        """
        Extract parcel information from parsed GIS data
        
        Args:
            parsed_data: Parsed GIS data from parse_shapefile
            
        Returns:
            List of parcel records
        """
        if not parsed_data.get('success'):
            return []
        
        parcels = []
        
        for feature in parsed_data.get('features', []):
            mapped = feature.get('mapped_fields', {})
            
            # Only include if has parcel ID
            if not mapped.get('parcel_id'):
                continue
            
            parcel = {
                'parcel_id': mapped.get('parcel_id'),
                'owner_name': mapped.get('owner_name'),
                'address': mapped.get('address'),
                'land_use': mapped.get('land_use'),
                'zoning': mapped.get('zoning'),
                'acreage': mapped.get('acreage'),
                'assessed_value': mapped.get('assessed_value'),
                'county': mapped.get('county'),
                'subdivision': mapped.get('subdivision'),
                'section': mapped.get('section'),
                'township': mapped.get('township'),
                'range': mapped.get('range'),
                'geometry_type': feature.get('geometry', {}).get('type'),
                'has_geometry': bool(feature.get('geometry'))
            }
            
            # Add all original attributes
            parcel['original_attributes'] = feature.get('attributes', {})
            
            parcels.append(parcel)
        
        return parcels
    
    def save_as_geojson(self, parsed_data: Dict, output_path: Path):
        """
        Save parsed data as GeoJSON
        
        Args:
            parsed_data: Parsed GIS data
            output_path: Output file path
        """
        if not parsed_data.get('success'):
            logger.error("Cannot save failed parse result")
            return
        
        geojson = {
            'type': 'FeatureCollection',
            'features': []
        }
        
        for feature in parsed_data.get('features', []):
            geojson_feature = {
                'type': 'Feature',
                'id': feature.get('id'),
                'properties': feature.get('attributes', {}),
                'geometry': feature.get('geometry')
            }
            geojson['features'].append(geojson_feature)
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        logger.info(f"Saved GeoJSON to {output_path}")
    
    def save_as_csv(self, parsed_data: Dict, output_path: Path):
        """
        Save attribute data as CSV
        
        Args:
            parsed_data: Parsed GIS data
            output_path: Output file path
        """
        parcels = self.extract_parcels(parsed_data)
        
        if not parcels:
            logger.warning("No parcels to save")
            return
        
        # Get all field names
        fieldnames = set()
        for parcel in parcels:
            fieldnames.update(parcel.keys())
        
        # Remove complex fields
        fieldnames.discard('original_attributes')
        fieldnames = sorted(list(fieldnames))
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for parcel in parcels:
                row = {k: parcel.get(k) for k in fieldnames}
                writer.writerow(row)
        
        logger.info(f"Saved {len(parcels)} parcels to {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='GIS Mapping Data Parser')
    parser.add_argument('file', help='Shapefile to parse')
    parser.add_argument('--max-features', type=int, help='Maximum features to parse')
    parser.add_argument('--output-geojson', help='Save as GeoJSON')
    parser.add_argument('--output-csv', help='Save attributes as CSV')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    
    args = parser.parse_args()
    
    # Initialize parser
    gis_parser = GISParser()
    
    # Parse shapefile
    shapefile_path = Path(args.file)
    result = gis_parser.parse_shapefile(shapefile_path, max_features=args.max_features)
    
    if result['success']:
        print(f"\nSuccessfully parsed {result['total_features']} features")
        
        if args.stats or (not args.output_geojson and not args.output_csv):
            # Show statistics
            stats = result.get('statistics', {})
            print("\nStatistics:")
            print(f"  Total features: {stats.get('total_features', 0):,}")
            print(f"  Unique parcels: {stats.get('unique_parcels', 0):,}")
            print(f"  Has parcel ID: {stats.get('has_parcel_id', 0):,}")
            print(f"  Has owner name: {stats.get('has_owner_name', 0):,}")
            print(f"  Has address: {stats.get('has_address', 0):,}")
            print(f"  Has geometry: {stats.get('has_geometry', 0):,}")
            
            if stats.get('top_land_uses'):
                print("\n  Top Land Uses:")
                for land_use, count in list(stats['top_land_uses'].items())[:5]:
                    print(f"    {land_use}: {count:,}")
        
        if args.output_geojson:
            gis_parser.save_as_geojson(result, Path(args.output_geojson))
            print(f"Saved GeoJSON to {args.output_geojson}")
        
        if args.output_csv:
            gis_parser.save_as_csv(result, Path(args.output_csv))
            print(f"Saved CSV to {args.output_csv}")
    
    else:
        print(f"Error parsing file: {result.get('error')}")