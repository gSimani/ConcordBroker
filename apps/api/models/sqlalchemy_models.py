"""
SQLAlchemy Models for ConcordBroker Database Integration
Comprehensive ORM models for all database tables using SQLAlchemy
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Index, JSON, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from datetime import datetime
import uuid
import os
from typing import Optional

Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv('POSTGRES_URL', os.getenv('DATABASE_URL'))

class FloridaParcel(Base):
    """Main property/parcel table with comprehensive property data"""
    __tablename__ = 'florida_parcels'

    # Primary keys
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(String(50), nullable=False, index=True)
    county = Column(String(50), nullable=False, index=True)
    year = Column(Integer, nullable=False, default=2025)

    # Property identifiers
    property_id = Column(String(100), unique=True, index=True)
    folio = Column(String(50))

    # Physical address
    phy_addr1 = Column(String(255))
    phy_addr2 = Column(String(255))
    phy_city = Column(String(100))
    phy_zipcode = Column(String(20))

    # Owner information
    owner_name = Column(String(255), index=True)
    owner_addr1 = Column(String(255))
    owner_addr2 = Column(String(255))
    owner_city = Column(String(100))
    owner_state = Column(String(2))
    owner_zipcode = Column(String(20))
    owner_country = Column(String(100))

    # Property characteristics
    property_type = Column(String(50))
    property_use_code = Column(String(20))
    land_sqft = Column(Integer)
    building_sqft = Column(Integer)
    total_sqft = Column(Integer)
    year_built = Column(Integer)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    stories = Column(Integer)

    # Values
    land_value = Column(DECIMAL(15, 2))
    building_value = Column(DECIMAL(15, 2))
    just_value = Column(DECIMAL(15, 2))
    assessed_value = Column(DECIMAL(15, 2))
    taxable_value = Column(DECIMAL(15, 2))
    market_value = Column(DECIMAL(15, 2))

    # Sales information
    sale_date = Column(DateTime)
    sale_price = Column(DECIMAL(15, 2))
    sale_type = Column(String(50))
    previous_sale_date = Column(DateTime)
    previous_sale_price = Column(DECIMAL(15, 2))

    # Geographic data
    latitude = Column(Float)
    longitude = Column(Float)
    census_tract = Column(String(20))
    subdivision = Column(String(255))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = Column(String(50))

    # Relationships
    tax_deeds = relationship("TaxDeed", back_populates="property")
    sales_history = relationship("SalesHistory", back_populates="property")
    permits = relationship("BuildingPermit", back_populates="property")
    sunbiz_entities = relationship("PropertySunbizLink", back_populates="property")
    images = relationship("PropertyImage", back_populates="property")

    # Indexes
    __table_args__ = (
        Index('idx_florida_parcels_location', 'county', 'phy_city'),
        Index('idx_florida_parcels_owner', 'owner_name'),
        Index('idx_florida_parcels_value', 'just_value'),
        Index('idx_florida_parcels_unique', 'parcel_id', 'county', 'year', unique=True),
    )

class TaxDeed(Base):
    """Tax deed auction and certificate information"""
    __tablename__ = 'tax_deeds'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey('florida_parcels.id'))

    # Certificate information
    certificate_number = Column(String(50), unique=True, index=True)
    certificate_year = Column(Integer)
    certificate_face_value = Column(DECIMAL(15, 2))

    # Auction information
    auction_date = Column(DateTime, index=True)
    auction_status = Column(String(50))  # upcoming, completed, cancelled
    auction_type = Column(String(50))

    # Bidding information
    minimum_bid = Column(DECIMAL(15, 2))
    winning_bid = Column(DECIMAL(15, 2))
    bidder_number = Column(String(50))
    total_bidders = Column(Integer)

    # Property details at auction
    assessed_value_at_auction = Column(DECIMAL(15, 2))
    opening_bid = Column(DECIMAL(15, 2))

    # URLs and references
    auction_url = Column(Text)
    case_number = Column(String(100))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    property = relationship("FloridaParcel", back_populates="tax_deeds")

class SalesHistory(Base):
    """Historical sales records for properties"""
    __tablename__ = 'sales_history'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey('florida_parcels.id'))

    # Sale details
    sale_date = Column(DateTime, nullable=False, index=True)
    sale_price = Column(DECIMAL(15, 2))
    sale_type = Column(String(50))

    # Parties involved
    grantor = Column(String(255))
    grantee = Column(String(255))

    # Document information
    deed_type = Column(String(50))
    document_number = Column(String(100))
    book_page = Column(String(50))

    # Validation
    qualified_sale = Column(Boolean)
    vacant_at_sale = Column(Boolean)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    property = relationship("FloridaParcel", back_populates="sales_history")

class BuildingPermit(Base):
    """Building permits and construction information"""
    __tablename__ = 'building_permits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey('florida_parcels.id'))

    # Permit details
    permit_number = Column(String(100), unique=True, index=True)
    permit_type = Column(String(100))
    permit_status = Column(String(50))

    # Dates
    application_date = Column(DateTime)
    issue_date = Column(DateTime)
    finalize_date = Column(DateTime)
    expiration_date = Column(DateTime)

    # Work details
    work_description = Column(Text)
    contractor_name = Column(String(255))
    contractor_license = Column(String(100))

    # Values
    estimated_value = Column(DECIMAL(15, 2))
    permit_fee = Column(DECIMAL(10, 2))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    property = relationship("FloridaParcel", back_populates="permits")

class SunbizEntity(Base):
    """Florida business entities from Sunbiz"""
    __tablename__ = 'sunbiz_entities'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Entity identification
    entity_id = Column(String(50), unique=True, index=True)
    entity_name = Column(String(500), index=True)
    entity_type = Column(String(100))

    # Registration details
    filing_date = Column(DateTime)
    status = Column(String(50))
    status_date = Column(DateTime)

    # Address
    principal_address = Column(Text)
    mailing_address = Column(Text)
    registered_agent_name = Column(String(255))
    registered_agent_address = Column(Text)

    # Officers/Members
    officers = Column(JSONB)  # Store as JSON array

    # Documents
    document_number = Column(String(100))
    ein_number = Column(String(50))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_annual_report = Column(DateTime)

    # Relationships
    property_links = relationship("PropertySunbizLink", back_populates="entity")

class PropertySunbizLink(Base):
    """Links between properties and business entities"""
    __tablename__ = 'property_sunbiz_links'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey('florida_parcels.id'))
    entity_id = Column(UUID(as_uuid=True), ForeignKey('sunbiz_entities.id'))

    # Link details
    link_type = Column(String(50))  # owner, agent, officer, etc.
    confidence_score = Column(Float)
    match_method = Column(String(100))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    verified = Column(Boolean, default=False)

    # Relationships
    property = relationship("FloridaParcel", back_populates="sunbiz_entities")
    entity = relationship("SunbizEntity", back_populates="property_links")

class PropertyImage(Base):
    """Property images for OpenCV analysis"""
    __tablename__ = 'property_images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey('florida_parcels.id'))

    # Image details
    image_url = Column(Text)
    image_type = Column(String(50))  # aerial, street, interior, etc.
    source = Column(String(100))

    # OpenCV analysis results
    cv_analysis = Column(JSONB)  # Store analysis results as JSON
    features_detected = Column(ARRAY(String))
    quality_score = Column(Float)

    # Image characteristics
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)

    # Metadata
    captured_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime)

    # Relationships
    property = relationship("FloridaParcel", back_populates="images")

class MarketAnalysis(Base):
    """Market analysis data for properties"""
    __tablename__ = 'market_analysis'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey('florida_parcels.id'))

    # Analysis metrics
    estimated_rent = Column(DECIMAL(10, 2))
    rental_yield = Column(Float)
    cap_rate = Column(Float)
    price_per_sqft = Column(DECIMAL(10, 2))

    # Comparables
    comp_properties = Column(JSONB)  # Store comparable properties
    avg_area_price = Column(DECIMAL(15, 2))
    avg_area_rent = Column(DECIMAL(10, 2))

    # Market trends
    appreciation_rate = Column(Float)
    days_on_market = Column(Integer)
    inventory_level = Column(String(50))

    # Scores and ratings
    investment_score = Column(Float)
    location_score = Column(Float)
    condition_score = Column(Float)

    # Analysis date
    analysis_date = Column(DateTime, default=datetime.utcnow)

    # PySpark analysis results
    spark_analysis = Column(JSONB)

# Database session management
class DatabaseManager:
    """Database connection and session management"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(
            self.database_url,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()

    def bulk_insert(self, model, data):
        """Bulk insert data using SQLAlchemy"""
        session = self.get_session()
        try:
            session.bulk_insert_mappings(model, data)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Bulk insert error: {e}")
            return False
        finally:
            session.close()

# Example usage
if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.create_tables()
    print("SQLAlchemy models created successfully!")