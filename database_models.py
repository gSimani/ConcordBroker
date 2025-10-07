"""
SQLAlchemy Models for ConcordBroker Data Integration
Auto-generated models for database access
"""

from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class FloridaParcel(Base):
    """Main property/parcel data table"""
    __tablename__ = 'florida_parcels'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, nullable=False, index=True)
    county = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=False)

    # Address fields
    phy_addr1 = Column(String)
    phy_addr2 = Column(String)
    phy_city = Column(String, index=True)
    phy_zipcode = Column(String, index=True)

    # Owner information
    owner_name = Column(String)
    owner_addr1 = Column(String)
    owner_addr2 = Column(String)
    owner_city = Column(String)
    owner_state = Column(String(2))
    owner_zip = Column(String)

    # Property values
    jv = Column(Float)  # Just/Appraised Value
    av = Column(Float)  # Assessed Value
    tv_sd = Column(Float)  # Taxable Value
    land_value = Column(Float)
    building_value = Column(Float)

    # Property characteristics
    property_use = Column(String, index=True)
    land_sqft = Column(Float)
    building_sqft = Column(Float)
    year_built = Column(Integer)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)

    # Sales information
    sale_price = Column(Float)
    sale_date = Column(Date)

    # Indexes for performance
    __table_args__ = (
        Index('idx_location', 'phy_city', 'phy_zipcode'),
        Index('idx_property_type', 'property_use'),
        Index('idx_value_range', 'jv'),
        Index('idx_parcel_county_year', 'parcel_id', 'county', 'year', unique=True)
    )

    # Relationships
    sales_history = relationship("SalesHistory", back_populates="parcel")
    exemptions = relationship("PropertyExemption", back_populates="parcel")

class SalesHistory(Base):
    """Historical sales data"""
    __tablename__ = 'sales_history'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'))
    sale_date = Column(Date, nullable=False)
    sale_price = Column(Float, nullable=False)
    sale_type = Column(String)
    buyer_name = Column(String)
    seller_name = Column(String)

    # Relationship
    parcel = relationship("FloridaParcel", back_populates="sales_history")

class PropertyExemption(Base):
    """Property tax exemptions"""
    __tablename__ = 'exemptions'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'))
    exemption_type = Column(String)
    exemption_amount = Column(Float)
    year = Column(Integer)

    # Relationship
    parcel = relationship("FloridaParcel", back_populates="exemptions")

class DORUseCode(Base):
    """Department of Revenue use codes for property categorization"""
    __tablename__ = 'dor_use_codes'

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String)
    category = Column(String)
    subcategory = Column(String)
