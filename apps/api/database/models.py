"""
SQLAlchemy Models for Property Appraiser and Sunbiz Databases
Optimized for performance with indexes and relationships
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text,
    Index, ForeignKey, UniqueConstraint, CheckConstraint,
    func, text, Date, DECIMAL, BigInteger
)
from sqlalchemy.orm import relationship, backref, deferred
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

Base = declarative_base()


class FloridaParcel(Base):
    """Property Appraiser main parcel table - optimized"""
    __tablename__ = 'florida_parcels'

    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Core identifiers - indexed
    parcel_id = Column(String(50), nullable=False, index=True)
    county = Column(String(50), nullable=False, index=True)
    year = Column(Integer, nullable=False, default=2025)

    # Physical address - indexed for search
    phy_addr1 = Column(String(255), index=True)
    phy_addr2 = Column(String(255))
    phy_city = Column(String(100), index=True)
    phy_state = Column(String(2), default='FL')
    phy_zipcd = Column(String(10), index=True)

    # Owner information - indexed
    owner_name = Column(String(255), index=True)
    owner_addr1 = Column(String(255))
    owner_addr2 = Column(String(255))
    owner_city = Column(String(100))
    owner_state = Column(String(2))
    owner_zip = Column(String(10))

    # Property characteristics
    dor_uc = Column(String(10), index=True)  # Property use code
    property_use = Column(String(50))
    yr_blt = Column(Integer, index=True)
    act_yr_blt = Column(Integer)
    eff_yr_blt = Column(Integer)
    bedroom_cnt = Column(Integer)
    bathroom_cnt = Column(Float)
    tot_lvg_area = Column(Float, index=True)
    lnd_sqfoot = Column(Float)
    no_res_unts = Column(Integer, default=1)

    # Values - indexed for filtering
    jv = Column(DECIMAL(15, 2), index=True)  # Just value
    av_sd = Column(DECIMAL(15, 2))  # Assessed value
    tv_sd = Column(DECIMAL(15, 2))  # Taxable value
    lnd_val = Column(DECIMAL(15, 2))  # Land value
    bldg_val = Column(DECIMAL(15, 2))  # Building value
    just_value = Column(DECIMAL(15, 2))
    assessed_value = Column(DECIMAL(15, 2))
    taxable_value = Column(DECIMAL(15, 2))
    land_value = Column(DECIMAL(15, 2))

    # Sales information
    sale_prc1 = Column(DECIMAL(15, 2))
    sale_yr1 = Column(Integer)
    sale_mo1 = Column(Integer)
    qual_cd1 = Column(String(2))
    vi_cd = Column(String(10))
    or_book_page = Column(String(50))
    sale_date = Column(DateTime)

    # Tax information
    tax_amount = Column(DECIMAL(12, 2))
    millage_rate = Column(Float)
    exempt_val = Column(DECIMAL(12, 2))
    homestead_exemption = Column(Boolean, default=False)

    # Geographic
    latitude = Column(Float)
    longitude = Column(Float)
    subdivision = Column(String(255))
    nbhd_cd = Column(String(20))

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    sales_history = relationship("SalesHistory", back_populates="parcel", lazy="dynamic")
    tax_certificates = relationship("TaxCertificate", back_populates="parcel", lazy="dynamic")
    tax_deeds = relationship("TaxDeed", back_populates="parcel", lazy="dynamic")
    sunbiz_matches = relationship("SunbizPropertyMatch", back_populates="parcel", lazy="dynamic")

    # Composite indexes for common queries
    __table_args__ = (
        UniqueConstraint('parcel_id', 'county', 'year', name='uq_parcel_county_year'),
        Index('idx_address_search', 'phy_addr1', 'phy_city', 'phy_zipcd'),
        Index('idx_value_range', 'jv', 'av_sd', 'tv_sd'),
        Index('idx_property_type', 'dor_uc', 'yr_blt', 'tot_lvg_area'),
        Index('idx_owner_search', 'owner_name', 'owner_city'),
        Index('idx_geo_location', 'latitude', 'longitude'),
        Index('idx_sales_data', 'sale_yr1', 'sale_prc1', 'qual_cd1'),
    )

    @hybrid_property
    def full_address(self):
        """Full property address"""
        return f"{self.phy_addr1}, {self.phy_city}, {self.phy_state} {self.phy_zipcd}"

    @hybrid_property
    def market_to_assessed_ratio(self):
        """Ratio of market value to assessed value"""
        if self.av_sd and self.av_sd > 0:
            return float(self.jv or 0) / float(self.av_sd)
        return 0

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'parcel_id': self.parcel_id,
            'address': self.phy_addr1,
            'city': self.phy_city,
            'state': self.phy_state,
            'zip_code': self.phy_zipcd,
            'owner': self.owner_name,
            'market_value': float(self.jv or 0),
            'assessed_value': float(self.av_sd or 0),
            'year_built': self.yr_blt,
            'square_feet': self.tot_lvg_area,
            'bedrooms': self.bedroom_cnt,
            'bathrooms': self.bathroom_cnt
        }


class SalesHistory(Base):
    """Property sales history"""
    __tablename__ = 'sales_history'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50), ForeignKey('florida_parcels.parcel_id'), nullable=False, index=True)
    sale_date = Column(Date, nullable=False, index=True)
    sale_price = Column(DECIMAL(15, 2))
    seller_name = Column(String(255))
    buyer_name = Column(String(255))
    deed_type = Column(String(50))
    qualified_sale = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())

    # Relationship
    parcel = relationship("FloridaParcel", back_populates="sales_history")

    __table_args__ = (
        Index('idx_sales_parcel_date', 'parcel_id', 'sale_date'),
    )


class TaxCertificate(Base):
    """Tax certificate data"""
    __tablename__ = 'tax_certificates'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50), ForeignKey('florida_parcels.parcel_id'), nullable=False, index=True)
    certificate_number = Column(String(50), unique=True)
    tax_year = Column(Integer)
    certificate_date = Column(Date)
    face_amount = Column(DECIMAL(12, 2))
    interest_rate = Column(Float)
    redemption_date = Column(Date)
    status = Column(String(50), default='Active')

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    parcel = relationship("FloridaParcel", back_populates="tax_certificates")

    __table_args__ = (
        Index('idx_cert_status', 'status', 'certificate_date'),
    )


class TaxDeed(Base):
    """Tax deed auction data"""
    __tablename__ = 'tax_deeds'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50), ForeignKey('florida_parcels.parcel_id'), nullable=False, index=True)
    td_number = Column(String(50), unique=True, index=True)
    auction_date = Column(Date, index=True)
    auction_status = Column(String(50), default='Upcoming', index=True)
    opening_bid = Column(DECIMAL(12, 2))
    winning_bid = Column(DECIMAL(12, 2))
    assessed_value = Column(DECIMAL(12, 2))
    market_value = Column(DECIMAL(12, 2))
    certificate_amount = Column(DECIMAL(12, 2))

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    parcel = relationship("FloridaParcel", back_populates="tax_deeds")

    __table_args__ = (
        Index('idx_auction_status_date', 'auction_status', 'auction_date'),
        Index('idx_bid_range', 'opening_bid', 'winning_bid'),
    )


class SunbizEntity(Base):
    """Sunbiz business entity data"""
    __tablename__ = 'sunbiz_entities'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    doc_number = Column(String(50), unique=True, nullable=False, index=True)
    entity_name = Column(String(500), nullable=False, index=True)
    entity_type = Column(String(100))
    status = Column(String(50), index=True)
    filing_date = Column(Date)
    state = Column(String(2), default='FL')

    # Principal address
    principal_addr1 = Column(String(255))
    principal_addr2 = Column(String(255))
    principal_city = Column(String(100))
    principal_state = Column(String(2))
    principal_zip = Column(String(10))

    # Mailing address
    mailing_addr1 = Column(String(255))
    mailing_addr2 = Column(String(255))
    mailing_city = Column(String(100))
    mailing_state = Column(String(2))
    mailing_zip = Column(String(10))

    # Registered agent
    registered_agent = Column(String(255))
    agent_addr1 = Column(String(255))
    agent_city = Column(String(100))
    agent_state = Column(String(2))
    agent_zip = Column(String(10))

    # Additional info
    ein = Column(String(20))
    annual_report_date = Column(Date)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    officers = relationship("SunbizOfficer", back_populates="entity", lazy="dynamic")
    property_matches = relationship("SunbizPropertyMatch", back_populates="entity", lazy="dynamic")

    __table_args__ = (
        Index('idx_entity_search', 'entity_name', 'status'),
        Index('idx_entity_location', 'principal_city', 'principal_state'),
    )


class SunbizOfficer(Base):
    """Sunbiz officer/director data"""
    __tablename__ = 'sunbiz_officers'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    doc_number = Column(String(50), ForeignKey('sunbiz_entities.doc_number'), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    title = Column(String(100))
    address1 = Column(String(255))
    address2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))

    created_at = Column(DateTime, default=func.now())

    # Relationship
    entity = relationship("SunbizEntity", back_populates="officers")

    __table_args__ = (
        Index('idx_officer_name', 'name'),
        Index('idx_officer_entity', 'doc_number', 'name'),
    )


class SunbizPropertyMatch(Base):
    """Matches between Sunbiz entities and properties"""
    __tablename__ = 'sunbiz_property_matches'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50), ForeignKey('florida_parcels.parcel_id'), nullable=False, index=True)
    doc_number = Column(String(50), ForeignKey('sunbiz_entities.doc_number'), nullable=False, index=True)
    match_type = Column(String(50))  # 'owner', 'address', 'officer'
    confidence_score = Column(Float)

    created_at = Column(DateTime, default=func.now())

    # Relationships
    parcel = relationship("FloridaParcel", back_populates="sunbiz_matches")
    entity = relationship("SunbizEntity", back_populates="property_matches")

    __table_args__ = (
        UniqueConstraint('parcel_id', 'doc_number', name='uq_parcel_entity'),
        Index('idx_match_type', 'match_type', 'confidence_score'),
    )


class QueryCache(Base):
    """Cache for expensive queries"""
    __tablename__ = 'query_cache'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    query_hash = Column(String(64), index=True)
    result_data = Column(Text)
    result_count = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, index=True)
    hit_count = Column(Integer, default=0)

    __table_args__ = (
        Index('idx_cache_expiry', 'expires_at', 'cache_key'),
    )