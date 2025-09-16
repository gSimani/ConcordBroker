"""
Florida Parcel Data Models
Database schema for storing Florida PTO parcel shapefiles and NAL data
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from datetime import datetime

Base = declarative_base()

class FloridaParcel(Base):
    """
    Main table for Florida parcel data
    Combines spatial geometry with NAL attributes
    """
    __tablename__ = 'florida_parcels'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Parcel identification
    parcel_id = Column(String(50), nullable=False, index=True)  # PARCELNO from shapefile
    parcel_id_alt = Column(String(50))  # Alternative ID if exists
    county = Column(String(50), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    
    # Geometry
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=False)
    centroid = Column(Geometry('POINT', srid=4326))
    area_sqft = Column(Float)
    perimeter_ft = Column(Float)
    
    # NAL attributes - Property Information
    owner_name = Column(String(255))
    owner_addr1 = Column(String(255))
    owner_addr2 = Column(String(255))
    owner_city = Column(String(100))
    owner_state = Column(String(2))
    owner_zip = Column(String(10))
    
    # Physical address
    phy_addr1 = Column(String(255))
    phy_addr2 = Column(String(255))
    phy_city = Column(String(100))
    phy_state = Column(String(2), default='FL')
    phy_zipcd = Column(String(10))
    
    # Legal description
    legal_desc = Column(Text)
    subdivision = Column(String(255))
    lot = Column(String(50))
    block = Column(String(50))
    plat_book = Column(String(50))
    plat_page = Column(String(50))
    
    # Property characteristics
    property_use = Column(String(10))
    property_use_desc = Column(String(255))
    land_use_code = Column(String(10))
    zoning = Column(String(50))
    
    # Valuations
    just_value = Column(Float)  # Market value
    assessed_value = Column(Float)
    taxable_value = Column(Float)
    land_value = Column(Float)
    building_value = Column(Float)
    
    # Property details
    year_built = Column(Integer)
    effective_year = Column(Integer)
    total_living_area = Column(Float)
    adjusted_area = Column(Float)
    gross_area = Column(Float)
    heated_area = Column(Float)
    
    # Building characteristics
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    half_bathrooms = Column(Integer)
    stories = Column(Float)
    units = Column(Integer)
    
    # Land measurements
    land_sqft = Column(Float)
    land_acres = Column(Float)
    frontage = Column(Float)
    depth = Column(Float)
    
    # Sales information
    sale_date = Column(DateTime)
    sale_price = Column(Float)
    sale_qualification = Column(String(10))
    deed_type = Column(String(50))
    grantor = Column(String(255))
    grantee = Column(String(255))
    
    # Tax information
    millage_code = Column(String(10))
    tax_district = Column(String(50))
    exemptions = Column(String(255))
    homestead_exempt = Column(Boolean, default=False)
    
    # Data quality flags
    match_status = Column(String(20))  # matched, polygon_only, nal_only
    discrepancy_reason = Column(String(100))
    is_redacted = Column(Boolean, default=False)
    data_source = Column(String(20))  # PIN, PAR, NAL
    
    # Metadata
    import_date = Column(DateTime, default=datetime.utcnow)
    update_date = Column(DateTime, onupdate=datetime.utcnow)
    source_file = Column(String(255))
    
    # Indexes
    __table_args__ = (
        Index('idx_parcel_county_year', 'county', 'year'),
        Index('idx_owner_name', 'owner_name'),
        Index('idx_phy_address', 'phy_addr1', 'phy_city'),
        Index('idx_property_use', 'property_use'),
        Index('idx_sale_date', 'sale_date'),
        Index('idx_taxable_value', 'taxable_value'),
    )


class FloridaCondoUnit(Base):
    """
    Separate table for condominium units
    Used for Miami-Dade and St. Johns counties
    """
    __tablename__ = 'florida_condo_units'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50), ForeignKey('florida_parcels.parcel_id'))
    unit_number = Column(String(50))
    floor = Column(Integer)
    building = Column(String(50))
    
    # Unit-specific details
    unit_sqft = Column(Float)
    unit_bedrooms = Column(Integer)
    unit_bathrooms = Column(Float)
    
    # Ownership
    unit_owner = Column(String(255))
    unit_assessed_value = Column(Float)
    unit_taxable_value = Column(Float)
    
    # Metadata
    county = Column(String(50))
    import_date = Column(DateTime, default=datetime.utcnow)


class ParcelHistory(Base):
    """
    Historical changes to parcel data
    """
    __tablename__ = 'parcel_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50), ForeignKey('florida_parcels.parcel_id'))
    
    # What changed
    change_type = Column(String(50))  # ownership, value, geometry, etc.
    change_date = Column(DateTime)
    old_value = Column(Text)
    new_value = Column(Text)
    
    # Source of change
    source = Column(String(100))
    import_date = Column(DateTime, default=datetime.utcnow)


class DataQualityReport(Base):
    """
    Data quality metrics for each import batch
    """
    __tablename__ = 'data_quality_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    county = Column(String(50))
    year = Column(Integer)
    import_date = Column(DateTime, default=datetime.utcnow)
    
    # Counts
    total_polygons = Column(Integer)
    total_nal_records = Column(Integer)
    matched_records = Column(Integer)
    unmatched_polygons = Column(Integer)
    unmatched_nal = Column(Integer)
    
    # Quality metrics
    valid_geometries = Column(Integer)
    invalid_geometries = Column(Integer)
    duplicate_parcels = Column(Integer)
    redacted_records = Column(Integer)
    
    # Discrepancy breakdown
    public_row_count = Column(Integer)
    stacked_polygon_count = Column(Integer)
    multi_parcel_count = Column(Integer)
    unknown_owner_count = Column(Integer)
    
    # Processing metadata
    processing_time_seconds = Column(Float)
    source_files = Column(Text)
    notes = Column(Text)


class CountyBoundary(Base):
    """
    County boundaries for spatial queries
    """
    __tablename__ = 'county_boundaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    county_name = Column(String(50), unique=True)
    county_fips = Column(String(5))
    geometry = Column(Geometry('MULTIPOLYGON', srid=4326))
    
    # Statistics
    total_parcels = Column(Integer)
    total_area_sqmi = Column(Float)
    population = Column(Integer)
    
    update_date = Column(DateTime, default=datetime.utcnow)


class RedactionLog(Base):
    """
    Track redacted records for compliance
    """
    __tablename__ = 'redaction_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50))
    redaction_type = Column(String(50))  # Chapter 119, owner request, etc.
    redaction_date = Column(DateTime, default=datetime.utcnow)
    reason = Column(Text)
    authorized_by = Column(String(100))
    
    # Original data hash for audit purposes
    data_hash = Column(String(64))


# Create views for common queries
VIEWS_SQL = """
-- Active parcels view (most recent year for each county)
CREATE OR REPLACE VIEW active_parcels AS
SELECT DISTINCT ON (parcel_id, county) *
FROM florida_parcels
ORDER BY parcel_id, county, year DESC;

-- Properties with recent sales
CREATE OR REPLACE VIEW recent_sales AS
SELECT *
FROM florida_parcels
WHERE sale_date >= CURRENT_DATE - INTERVAL '1 year'
  AND sale_price > 0
  AND sale_qualification IN ('Q', 'U');  -- Qualified and Unqualified sales

-- High value properties
CREATE OR REPLACE VIEW high_value_properties AS
SELECT *
FROM florida_parcels
WHERE taxable_value > 1000000
  AND is_redacted = FALSE;

-- Residential properties
CREATE OR REPLACE VIEW residential_properties AS
SELECT *
FROM florida_parcels
WHERE property_use IN ('01', '02', '03', '04', '05', '06', '07', '08', '09')
  AND is_redacted = FALSE;

-- Commercial properties
CREATE OR REPLACE VIEW commercial_properties AS
SELECT *
FROM florida_parcels
WHERE property_use IN ('10', '11', '12', '13', '14', '15', '16', '17', '18', '19')
  AND is_redacted = FALSE;

-- Data quality overview
CREATE OR REPLACE VIEW data_quality_overview AS
SELECT 
    county,
    year,
    COUNT(*) as total_parcels,
    SUM(CASE WHEN match_status = 'matched' THEN 1 ELSE 0 END) as matched,
    SUM(CASE WHEN match_status = 'polygon_only' THEN 1 ELSE 0 END) as polygon_only,
    SUM(CASE WHEN is_redacted THEN 1 ELSE 0 END) as redacted,
    AVG(taxable_value) as avg_taxable_value
FROM florida_parcels
GROUP BY county, year
ORDER BY county, year DESC;
"""