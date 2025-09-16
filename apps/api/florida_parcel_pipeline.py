"""
Florida Parcel Data Pipeline
Handles integration of Florida Property Tax Oversight (PTO) shapefiles and NAL data
Based on Florida Revenue Property Data Portal specifications
"""

import os
import zipfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from shapely.geometry import shape
import fiona
import dbf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ParcelDataConfig:
    """Configuration for Florida parcel data processing"""
    base_path: str = "./data/florida_parcels"
    database_url: str = "postgresql://user:password@localhost/concord_broker"
    redaction_compliance: bool = True
    handle_condos_separately: bool = True
    special_counties: List[str] = None
    
    def __post_init__(self):
        if self.special_counties is None:
            # Counties with separate condo files
            self.special_counties = ["MIAMI-DADE", "ST. JOHNS"]

class FloridaParcelPipeline:
    """
    Pipeline for processing Florida PTO parcel shapefiles and NAL data
    Handles both PIN (geometry only) and PAR (geometry + attributes) files
    """
    
    def __init__(self, config: ParcelDataConfig):
        self.config = config
        self.engine = create_engine(config.database_url)
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary directory structure"""
        paths = [
            Path(self.config.base_path),
            Path(self.config.base_path) / "raw",
            Path(self.config.base_path) / "processed",
            Path(self.config.base_path) / "staging"
        ]
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
    
    def download_county_data(self, county: str, year: int = 2024) -> Dict[str, Path]:
        """
        Download shapefile and NAL data for a specific county
        Returns paths to downloaded files
        """
        logger.info(f"Downloading data for {county} County, Year: {year}")
        
        downloads = {}
        base_url = "https://floridarevenue.com/property/Documents/GISData"
        
        # Download PIN shapefile (basic geometry)
        pin_url = f"{base_url}/{year}/PIN_{county}_{year}.zip"
        pin_path = Path(self.config.base_path) / "raw" / f"PIN_{county}_{year}.zip"
        
        # Download PAR shapefile (geometry + attributes)
        par_url = f"{base_url}/{year}/PAR_{county}_{year}.zip"
        par_path = Path(self.config.base_path) / "raw" / f"PAR_{county}_{year}.zip"
        
        # Download NAL file (DBF format preferred to avoid CSV formatting issues)
        nal_url = f"{base_url}/{year}/NAL_{county}_{year}.dbf"
        nal_path = Path(self.config.base_path) / "raw" / f"NAL_{county}_{year}.dbf"
        
        # Handle special counties with separate condo files
        if county.upper() in self.config.special_counties:
            condo_url = f"{base_url}/{year}/CONDO_{county}_{year}.zip"
            condo_path = Path(self.config.base_path) / "raw" / f"CONDO_{county}_{year}.zip"
            downloads['condo'] = condo_path
        
        downloads.update({
            'pin': pin_path,
            'par': par_path,
            'nal': nal_path
        })
        
        # TODO: Implement actual download logic using requests or urllib
        logger.info(f"Downloaded files: {downloads}")
        return downloads
    
    def process_shapefile(self, shapefile_path: Path, file_type: str = "PAR") -> gpd.GeoDataFrame:
        """
        Process a shapefile and return as GeoDataFrame
        Handles both PIN (geometry only) and PAR (full attributes) files
        """
        logger.info(f"Processing {file_type} shapefile: {shapefile_path}")
        
        # Extract if zipped
        if shapefile_path.suffix == '.zip':
            extract_dir = Path(self.config.base_path) / "staging" / shapefile_path.stem
            with zipfile.ZipFile(shapefile_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Find the actual shapefile
            shp_files = list(extract_dir.glob("*.shp"))
            if not shp_files:
                raise ValueError(f"No shapefile found in {shapefile_path}")
            shapefile_path = shp_files[0]
        
        # Read shapefile
        gdf = gpd.read_file(shapefile_path)
        
        # Standardize column names
        if 'PARCELNO' in gdf.columns:
            gdf['parcel_id_geo'] = gdf['PARCELNO']
        
        # Add processing metadata
        gdf['import_date'] = datetime.now()
        gdf['source_file'] = shapefile_path.name
        gdf['file_type'] = file_type
        
        return gdf
    
    def process_nal_file(self, nal_path: Path) -> pd.DataFrame:
        """
        Process Name, Address, Legal (NAL) file
        Uses DBF format to avoid CSV formatting issues with parcel IDs
        """
        logger.info(f"Processing NAL file: {nal_path}")
        
        if nal_path.suffix == '.dbf':
            # Use dbf library for proper handling
            table = dbf.Table(str(nal_path))
            table.open()
            
            # Convert to pandas DataFrame
            records = []
            for record in table:
                records.append(dict(record))
            table.close()
            
            df = pd.DataFrame(records)
        else:
            # Fallback to CSV with careful handling
            df = pd.read_csv(nal_path, dtype={'PARCEL_ID': str})
        
        # Standardize column names
        if 'PARCEL_ID' in df.columns:
            df['parcel_id_nal'] = df['PARCEL_ID'].astype(str).str.strip()
        
        # Handle redacted records
        if self.config.redaction_compliance:
            df = self.apply_redaction_compliance(df)
        
        return df
    
    def apply_redaction_compliance(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply Chapter 119 Florida Statutes redaction requirements
        Removes or masks sensitive information
        """
        logger.info("Applying redaction compliance")
        
        # Flag redacted records
        df['is_redacted'] = False
        
        # Common redaction scenarios
        redaction_indicators = [
            'CONFIDENTIAL',
            'EXEMPT',
            'REDACTED',
            'WITHHELD'
        ]
        
        for indicator in redaction_indicators:
            mask = df.apply(lambda row: any(
                indicator in str(val).upper() if pd.notna(val) else False 
                for val in row
            ), axis=1)
            df.loc[mask, 'is_redacted'] = True
        
        # Mask sensitive fields for redacted records
        sensitive_fields = ['OWNER_NAME', 'OWNER_ADDR', 'OWNER_PHONE']
        for field in sensitive_fields:
            if field in df.columns:
                df.loc[df['is_redacted'], field] = 'REDACTED'
        
        return df
    
    def join_spatial_with_attributes(
        self, 
        gdf: gpd.GeoDataFrame, 
        nal_df: pd.DataFrame
    ) -> gpd.GeoDataFrame:
        """
        Join spatial data with NAL attributes
        Handles record count discrepancies gracefully
        """
        logger.info("Joining spatial and attribute data")
        
        # Prepare join keys
        gdf['join_key'] = gdf['parcel_id_geo'].astype(str).str.strip().str.upper()
        nal_df['join_key'] = nal_df['parcel_id_nal'].astype(str).str.strip().str.upper()
        
        # Track join statistics
        stats = {
            'total_polygons': len(gdf),
            'total_nal_records': len(nal_df),
            'matched': 0,
            'unmatched_polygons': [],
            'unmatched_nal': []
        }
        
        # Perform left join (keep all polygons)
        result = gdf.merge(
            nal_df, 
            on='join_key', 
            how='left', 
            indicator=True,
            suffixes=('_geo', '_nal')
        )
        
        # Analyze join results
        stats['matched'] = len(result[result['_merge'] == 'both'])
        stats['unmatched_polygons'] = result[result['_merge'] == 'left_only']['join_key'].tolist()
        
        # Find NAL records without polygons
        nal_keys = set(nal_df['join_key'])
        geo_keys = set(gdf['join_key'])
        stats['unmatched_nal'] = list(nal_keys - geo_keys)
        
        # Flag unmatched records for investigation
        result['match_status'] = result['_merge'].map({
            'both': 'matched',
            'left_only': 'polygon_only',
            'right_only': 'nal_only'
        })
        
        # Handle known discrepancy reasons
        result = self.handle_discrepancy_reasons(result)
        
        logger.info(f"Join statistics: {stats}")
        
        return result
    
    def handle_discrepancy_reasons(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Handle known reasons for record count discrepancies
        """
        logger.info("Handling known discrepancy reasons")
        
        # Flag public rights-of-way
        row_indicators = ['ROW', 'RIGHT OF WAY', 'ROAD', 'STREET']
        for indicator in row_indicators:
            mask = gdf['parcel_id_geo'].str.contains(indicator, case=False, na=False)
            gdf.loc[mask, 'discrepancy_reason'] = 'public_right_of_way'
        
        # Flag potential phantom polygons (stacked condos)
        duplicate_geoms = gdf[gdf.geometry.duplicated(keep=False)]
        if len(duplicate_geoms) > 0:
            gdf.loc[duplicate_geoms.index, 'discrepancy_reason'] = 'stacked_polygon'
        
        # Flag multi-parcel polygons
        # (Would need additional logic based on ownership data)
        
        # Flag redacted parcels
        if 'is_redacted' in gdf.columns:
            gdf.loc[gdf['is_redacted'] == True, 'discrepancy_reason'] = 'redacted_record'
        
        return gdf
    
    def process_condo_data(self, condo_path: Path, county: str) -> pd.DataFrame:
        """
        Process separate condominium data for Miami-Dade and St. Johns counties
        """
        logger.info(f"Processing condo data for {county}")
        
        if condo_path.suffix == '.zip':
            extract_dir = Path(self.config.base_path) / "staging" / "condos"
            with zipfile.ZipFile(condo_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Process extracted files
            # Implementation depends on specific format
            pass
        
        # Return processed condo DataFrame
        return pd.DataFrame()
    
    def validate_data_quality(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Validate data quality and generate quality report
        """
        logger.info("Validating data quality")
        
        report = {
            'timestamp': datetime.now(),
            'total_records': len(gdf),
            'geometry_valid': gdf.geometry.is_valid.sum(),
            'geometry_invalid': (~gdf.geometry.is_valid).sum(),
            'matched_records': len(gdf[gdf['match_status'] == 'matched']),
            'unmatched_polygons': len(gdf[gdf['match_status'] == 'polygon_only']),
            'redacted_records': len(gdf[gdf.get('is_redacted', False) == True]),
            'discrepancy_breakdown': gdf.get('discrepancy_reason', pd.Series()).value_counts().to_dict()
        }
        
        # Check for geometry issues
        if report['geometry_invalid'] > 0:
            logger.warning(f"Found {report['geometry_invalid']} invalid geometries")
            # Attempt to fix
            gdf.geometry = gdf.geometry.buffer(0)
        
        # Check for duplicate parcel IDs
        duplicates = gdf[gdf['parcel_id_geo'].duplicated(keep=False)]
        report['duplicate_parcels'] = len(duplicates)
        
        return report
    
    def load_to_database(self, gdf: gpd.GeoDataFrame, table_name: str):
        """
        Load processed data to PostgreSQL/PostGIS database
        """
        logger.info(f"Loading data to database table: {table_name}")
        
        # Ensure PostGIS extension
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
        
        # Write to PostGIS
        gdf.to_postgis(
            name=table_name,
            con=self.engine,
            if_exists='append',
            index=True,
            index_label='id'
        )
        
        # Create spatial index
        with self.engine.connect() as conn:
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS {table_name}_geom_idx 
                ON {table_name} USING GIST(geometry);
            """))
            conn.commit()
        
        logger.info(f"Successfully loaded {len(gdf)} records to {table_name}")
    
    def process_county_pipeline(self, county: str, year: int = 2024):
        """
        Complete pipeline for processing a single county's data
        """
        logger.info(f"Starting pipeline for {county} County")
        
        try:
            # Download data
            files = self.download_county_data(county, year)
            
            # Process PAR shapefile (includes geometry and attributes)
            gdf = self.process_shapefile(files['par'], file_type='PAR')
            
            # Process NAL file if additional attributes needed
            nal_df = self.process_nal_file(files['nal'])
            
            # Join spatial with attributes
            result_gdf = self.join_spatial_with_attributes(gdf, nal_df)
            
            # Handle condos for special counties
            if county.upper() in self.config.special_counties and 'condo' in files:
                condo_df = self.process_condo_data(files['condo'], county)
                # Merge condo data logic here
            
            # Validate data quality
            quality_report = self.validate_data_quality(result_gdf)
            logger.info(f"Quality report: {quality_report}")
            
            # Load to database
            table_name = f"parcels_{county.lower()}_{year}"
            self.load_to_database(result_gdf, table_name)
            
            # Save quality report
            report_path = Path(self.config.base_path) / "processed" / f"{county}_{year}_report.json"
            pd.Series(quality_report).to_json(report_path)
            
            logger.info(f"Successfully processed {county} County")
            return True
            
        except Exception as e:
            logger.error(f"Error processing {county}: {str(e)}")
            return False
    
    def process_all_counties(self, counties: List[str], year: int = 2024):
        """
        Process multiple counties in sequence
        """
        results = {}
        for county in counties:
            success = self.process_county_pipeline(county, year)
            results[county] = success
        
        # Generate summary report
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Processed {success_count}/{len(counties)} counties successfully")
        return results


# Usage example
if __name__ == "__main__":
    # Configure pipeline
    config = ParcelDataConfig(
        base_path="./data/florida_parcels",
        database_url="postgresql://user:password@localhost/concord_broker",
        redaction_compliance=True,
        handle_condos_separately=True
    )
    
    # Initialize pipeline
    pipeline = FloridaParcelPipeline(config)
    
    # Process specific counties
    counties = ["BROWARD", "MIAMI-DADE", "PALM BEACH"]
    results = pipeline.process_all_counties(counties, year=2024)
    
    print(f"Processing complete: {results}")