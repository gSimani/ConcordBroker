#!/usr/bin/env python3
"""
SQLAlchemy Models and Database Operations for ConcordBroker
Comprehensive ORM models for all data tables with optimized relationships
"""

import os
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union
from decimal import Decimal

# SQLAlchemy imports
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, Date, DateTime,
    Text, Numeric, ForeignKey, Index, UniqueConstraint, CheckConstraint,
    text, func, and_, or_, desc, asc, distinct, case, cast
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session, Query
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import select, insert, update, delete
from sqlalchemy.pool import QueuePool

# Pydantic for data validation
from pydantic import BaseModel, Field, validator
from pydantic.dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()

class FloridaParcels(Base):
    """Florida property parcels table - main property data"""
    __tablename__ = 'florida_parcels'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50), nullable=False, index=True)
    county = Column(String(20), nullable=False, index=True)
    year = Column(Integer, nullable=False, default=2025)

    # Owner information
    owner_name = Column(String(200), index=True)
    owner_addr1 = Column(String(100))
    owner_addr2 = Column(String(100))
    owner_city = Column(String(50))
    owner_state = Column(String(2))
    owner_zip = Column(String(10))

    # Property address
    phy_addr1 = Column(String(100), index=True)
    phy_addr2 = Column(String(100))
    phy_city = Column(String(50))
    phy_zip = Column(String(10))

    # Property characteristics
    land_use_code = Column(String(10))
    land_use_desc = Column(String(100))
    total_living_area = Column(Integer)
    land_sqft = Column(Integer)
    year_built = Column(Integer)
    beds = Column(Integer)
    baths = Column(Float)
    pool = Column(String(1))  # Y/N

    # Values
    just_value = Column(Numeric(12, 2))
    land_value = Column(Numeric(12, 2))
    building_value = Column(Numeric(12, 2))
    assessed_value = Column(Numeric(12, 2))
    exemption_amount = Column(Numeric(12, 2))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sales_history = relationship("PropertySalesHistory", back_populates="property")
    tax_certificates = relationship("TaxCertificates", back_populates="property")

    # Indexes for performance
    __table_args__ = (
        Index('idx_parcel_county_year', 'parcel_id', 'county', 'year'),
        Index('idx_owner_name', 'owner_name'),
        Index('idx_property_address', 'phy_addr1'),
        Index('idx_just_value', 'just_value'),
        Index('idx_year_built', 'year_built'),
        UniqueConstraint('parcel_id', 'county', 'year', name='uq_parcel_county_year')
    )

    def __repr__(self):
        return f"<FloridaParcels(parcel_id='{self.parcel_id}', county='{self.county}', owner='{self.owner_name}')>"

class PropertySalesHistory(Base):
    """Property sales transaction history"""
    __tablename__ = 'property_sales_history'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50), ForeignKey('florida_parcels.parcel_id'), nullable=False, index=True)

    # Sale details
    sale_date = Column(Date, index=True)
    sale_price = Column(Numeric(12, 2), index=True)
    sale_type = Column(String(50))
    deed_type = Column(String(50))

    # Parties
    grantor = Column(String(200))
    grantee = Column(String(200))

    # Document information
    document_number = Column(String(50))
    book_page = Column(String(20))
    legal_description = Column(Text)

    # Data source
    data_source = Column(String(50), default='property_sales_history')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    property = relationship("FloridaParcels", back_populates="sales_history")

    # Indexes
    __table_args__ = (
        Index('idx_sale_date_price', 'sale_date', 'sale_price'),
        Index('idx_grantor', 'grantor'),
        Index('idx_grantee', 'grantee'),
        Index('idx_document_number', 'document_number')
    )

    def __repr__(self):
        return f"<PropertySalesHistory(parcel_id='{self.parcel_id}', sale_date='{self.sale_date}', price='{self.sale_price}')>"

class TaxCertificates(Base):
    """Tax lien certificates"""
    __tablename__ = 'tax_certificates'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String(50), ForeignKey('florida_parcels.parcel_id'), nullable=False, index=True)

    # Certificate details
    certificate_number = Column(String(50), unique=True, nullable=False)
    certificate_year = Column(Integer, nullable=False, index=True)
    certificate_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, index=True)  # Active, Redeemed, etc.

    # Sale information
    sale_date = Column(Date)
    county = Column(String(20), nullable=False, index=True)

    # Property owner at time of certificate
    owner_name = Column(String(200))
    property_address = Column(String(200))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    property = relationship("FloridaParcels", back_populates="tax_certificates")

    # Indexes
    __table_args__ = (
        Index('idx_cert_year_status', 'certificate_year', 'status'),
        Index('idx_cert_amount', 'certificate_amount'),
        Index('idx_sale_date', 'sale_date'),
        Index('idx_county_year', 'county', 'certificate_year')
    )

    def __repr__(self):
        return f"<TaxCertificates(cert_number='{self.certificate_number}', parcel_id='{self.parcel_id}', amount='{self.certificate_amount}')>"

class FloridaEntities(Base):
    """Florida business entities"""
    __tablename__ = 'florida_entities'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String(50), unique=True, nullable=False)

    # Entity details
    entity_name = Column(String(200), nullable=False, index=True)
    entity_type = Column(String(50))
    status = Column(String(20), index=True)
    registration_date = Column(Date)

    # Agent information
    agent_name = Column(String(200))
    agent_address = Column(String(300))

    # Address
    principal_address = Column(String(300))
    mailing_address = Column(String(300))

    # Additional data
    additional_info = Column(JSONB)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_entity_name', 'entity_name'),
        Index('idx_entity_type', 'entity_type'),
        Index('idx_status', 'status'),
        Index('idx_registration_date', 'registration_date')
    )

    def __repr__(self):
        return f"<FloridaEntities(entity_id='{self.entity_id}', name='{self.entity_name}', type='{self.entity_type}')>"

class SunbizCorporate(Base):
    """Sunbiz corporate registrations"""
    __tablename__ = 'sunbiz_corporate'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_number = Column(String(50), unique=True, nullable=False)

    # Corporation details
    corporation_name = Column(String(200), nullable=False, index=True)
    corp_type = Column(String(50))
    status = Column(String(20), index=True)
    file_date = Column(Date)

    # Agent information
    agent_name = Column(String(200))
    agent_address = Column(String(300))

    # Address information
    principal_address = Column(String(300))
    mailing_address = Column(String(300))

    # Additional details
    state_of_incorporation = Column(String(20))
    annual_report_date = Column(Date)
    additional_data = Column(JSONB)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_corporation_name', 'corporation_name'),
        Index('idx_corp_type', 'corp_type'),
        Index('idx_corp_status', 'status'),
        Index('idx_file_date', 'file_date')
    )

    def __repr__(self):
        return f"<SunbizCorporate(doc_number='{self.document_number}', name='{self.corporation_name}', type='{self.corp_type}')>"

class DataFlowMetrics(Base):
    """Table for storing data flow monitoring metrics"""
    __tablename__ = 'data_flow_metrics'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Metric details
    table_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # record_count, query_time, data_freshness, etc.
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))  # count, ms, hours, etc.

    # Additional context
    county_filter = Column(String(20))
    additional_context = Column(JSONB)

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Indexes
    __table_args__ = (
        Index('idx_table_metric_timestamp', 'table_name', 'metric_type', 'timestamp'),
        Index('idx_timestamp', 'timestamp')
    )

    def __repr__(self):
        return f"<DataFlowMetrics(table='{self.table_name}', metric='{self.metric_type}', value='{self.metric_value}')>"

class ValidationResults(Base):
    """Table for storing validation results"""
    __tablename__ = 'validation_results'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Validation details
    table_name = Column(String(100), nullable=False, index=True)
    validation_type = Column(String(50), nullable=False)  # table_integrity, referential_integrity, etc.
    passed = Column(Boolean, nullable=False, index=True)
    message = Column(Text)
    details = Column(JSONB)

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Indexes
    __table_args__ = (
        Index('idx_table_validation_timestamp', 'table_name', 'validation_type', 'timestamp'),
        Index('idx_passed_timestamp', 'passed', 'timestamp')
    )

    def __repr__(self):
        return f"<ValidationResults(table='{self.table_name}', type='{self.validation_type}', passed='{self.passed}')>"

# Database connection and session management
class DatabaseManager:
    """Centralized database management"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_maker = None
        self.async_engine = None
        self.async_session_maker = None

    def initialize_sync(self):
        """Initialize synchronous database connections"""
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=30,
                pool_timeout=30,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )

            self.session_maker = sessionmaker(bind=self.engine)
            logger.info("✅ Synchronous database connection initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize sync database connection: {e}")
            raise

    def initialize_async(self):
        """Initialize asynchronous database connections"""
        try:
            async_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://')

            self.async_engine = create_async_engine(
                async_url,
                pool_size=20,
                max_overflow=30,
                pool_timeout=30,
                pool_recycle=3600,
                echo=False
            )

            self.async_session_maker = async_sessionmaker(
                self.async_engine,
                expire_on_commit=False
            )

            logger.info("✅ Asynchronous database connection initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize async database connection: {e}")
            raise

    def get_session(self) -> Session:
        """Get a synchronous database session"""
        if not self.session_maker:
            raise RuntimeError("Synchronous database not initialized")
        return self.session_maker()

    def get_async_session(self) -> AsyncSession:
        """Get an asynchronous database session"""
        if not self.async_session_maker:
            raise RuntimeError("Asynchronous database not initialized")
        return self.async_session_maker()

    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("✅ All tables created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise

    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
        if self.async_engine:
            self.async_engine.dispose()

# High-level database operations
class PropertyDataOperations:
    """High-level operations for property data"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def search_properties(
        self,
        county: Optional[str] = None,
        owner_name: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        has_tax_certificates: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FloridaParcels]:
        """Search properties with multiple filters"""

        with self.db_manager.get_session() as session:
            query = session.query(FloridaParcels)

            if county:
                query = query.filter(FloridaParcels.county.ilike(f'%{county}%'))

            if owner_name:
                query = query.filter(FloridaParcels.owner_name.ilike(f'%{owner_name}%'))

            if min_value is not None:
                query = query.filter(FloridaParcels.just_value >= min_value)

            if max_value is not None:
                query = query.filter(FloridaParcels.just_value <= max_value)

            if has_tax_certificates is not None:
                if has_tax_certificates:
                    query = query.join(TaxCertificates).filter(
                        TaxCertificates.status != 'Redeemed'
                    )
                else:
                    # Properties without active tax certificates
                    subquery = session.query(TaxCertificates.parcel_id).filter(
                        TaxCertificates.status != 'Redeemed'
                    ).distinct()
                    query = query.filter(~FloridaParcels.parcel_id.in_(subquery))

            return query.offset(offset).limit(limit).all()

    def get_property_with_details(self, parcel_id: str) -> Optional[Dict[str, Any]]:
        """Get property with all related data"""

        with self.db_manager.get_session() as session:
            property_data = session.query(FloridaParcels).filter(
                FloridaParcels.parcel_id == parcel_id
            ).first()

            if not property_data:
                return None

            # Get sales history
            sales = session.query(PropertySalesHistory).filter(
                PropertySalesHistory.parcel_id == parcel_id
            ).order_by(desc(PropertySalesHistory.sale_date)).all()

            # Get tax certificates
            tax_certs = session.query(TaxCertificates).filter(
                TaxCertificates.parcel_id == parcel_id
            ).order_by(desc(TaxCertificates.certificate_year)).all()

            return {
                'property': property_data,
                'sales_history': sales,
                'tax_certificates': tax_certs
            }

    def get_sales_comparables(
        self,
        parcel_id: str,
        radius_sqft: int = 500,
        time_period_months: int = 24
    ) -> List[PropertySalesHistory]:
        """Get comparable sales for a property"""

        with self.db_manager.get_session() as session:
            # Get the subject property
            subject = session.query(FloridaParcels).filter(
                FloridaParcels.parcel_id == parcel_id
            ).first()

            if not subject:
                return []

            # Find comparable sales
            cutoff_date = datetime.now() - timedelta(days=time_period_months * 30)

            comparables = session.query(PropertySalesHistory).join(FloridaParcels).filter(
                FloridaParcels.county == subject.county,
                PropertySalesHistory.sale_date >= cutoff_date,
                PropertySalesHistory.sale_price > 0,
                FloridaParcels.total_living_area.between(
                    subject.total_living_area * 0.7,
                    subject.total_living_area * 1.3
                ) if subject.total_living_area else True,
                PropertySalesHistory.parcel_id != parcel_id
            ).order_by(desc(PropertySalesHistory.sale_date)).limit(20).all()

            return comparables

class EntityOperations:
    """Operations for business entity data"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def search_entities(
        self,
        name: str,
        fuzzy_match: bool = True,
        include_florida: bool = True,
        include_sunbiz: bool = True
    ) -> Dict[str, List]:
        """Search for business entities across multiple sources"""

        results = {"florida_entities": [], "sunbiz_corporate": []}

        with self.db_manager.get_session() as session:
            if include_florida:
                florida_query = session.query(FloridaEntities)
                if fuzzy_match:
                    florida_query = florida_query.filter(
                        FloridaEntities.entity_name.ilike(f'%{name}%')
                    )
                else:
                    florida_query = florida_query.filter(
                        FloridaEntities.entity_name == name
                    )
                results["florida_entities"] = florida_query.limit(50).all()

            if include_sunbiz:
                sunbiz_query = session.query(SunbizCorporate)
                if fuzzy_match:
                    sunbiz_query = sunbiz_query.filter(
                        SunbizCorporate.corporation_name.ilike(f'%{name}%')
                    )
                else:
                    sunbiz_query = sunbiz_query.filter(
                        SunbizCorporate.corporation_name == name
                    )
                results["sunbiz_corporate"] = sunbiz_query.limit(50).all()

        return results

    def find_potential_duplicates(self, similarity_threshold: float = 0.8) -> List[Dict]:
        """Find potential duplicate entities using SQL similarity functions"""

        with self.db_manager.get_session() as session:
            # This would use PostgreSQL's similarity() function if available
            # For now, we'll use simpler string matching
            duplicates_query = text("""
                SELECT
                    fe1.entity_name as name1,
                    fe1.entity_id as id1,
                    fe2.entity_name as name2,
                    fe2.entity_id as id2,
                    similarity(fe1.entity_name, fe2.entity_name) as sim_score
                FROM florida_entities fe1
                JOIN florida_entities fe2 ON fe1.id < fe2.id
                WHERE similarity(fe1.entity_name, fe2.entity_name) > :threshold
                ORDER BY sim_score DESC
                LIMIT 100
            """)

            result = session.execute(duplicates_query, {"threshold": similarity_threshold})
            return [dict(row) for row in result]

class MonitoringOperations:
    """Operations for data flow monitoring"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def log_metric(
        self,
        table_name: str,
        metric_type: str,
        metric_value: float,
        metric_unit: str = None,
        county_filter: str = None,
        additional_context: Dict = None
    ):
        """Log a monitoring metric"""

        with self.db_manager.get_session() as session:
            metric = DataFlowMetrics(
                table_name=table_name,
                metric_type=metric_type,
                metric_value=metric_value,
                metric_unit=metric_unit,
                county_filter=county_filter,
                additional_context=additional_context
            )
            session.add(metric)
            session.commit()

    def log_validation_result(
        self,
        table_name: str,
        validation_type: str,
        passed: bool,
        message: str,
        details: Dict = None
    ):
        """Log a validation result"""

        with self.db_manager.get_session() as session:
            validation = ValidationResults(
                table_name=table_name,
                validation_type=validation_type,
                passed=passed,
                message=message,
                details=details
            )
            session.add(validation)
            session.commit()

    def get_recent_metrics(
        self,
        table_name: str = None,
        hours: int = 24
    ) -> List[DataFlowMetrics]:
        """Get recent metrics"""

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        with self.db_manager.get_session() as session:
            query = session.query(DataFlowMetrics).filter(
                DataFlowMetrics.timestamp >= cutoff_time
            )

            if table_name:
                query = query.filter(DataFlowMetrics.table_name == table_name)

            return query.order_by(desc(DataFlowMetrics.timestamp)).all()

    def get_validation_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get validation summary for the specified time period"""

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        with self.db_manager.get_session() as session:
            # Get total validations
            total_validations = session.query(ValidationResults).filter(
                ValidationResults.timestamp >= cutoff_time
            ).count()

            # Get passed validations
            passed_validations = session.query(ValidationResults).filter(
                ValidationResults.timestamp >= cutoff_time,
                ValidationResults.passed == True
            ).count()

            # Get validation breakdown by table
            table_breakdown = session.query(
                ValidationResults.table_name,
                func.count(ValidationResults.id).label('total'),
                func.sum(case([(ValidationResults.passed == True, 1)], else_=0)).label('passed')
            ).filter(
                ValidationResults.timestamp >= cutoff_time
            ).group_by(ValidationResults.table_name).all()

            return {
                "summary": {
                    "total_validations": total_validations,
                    "passed_validations": passed_validations,
                    "success_rate": (passed_validations / total_validations * 100) if total_validations > 0 else 0
                },
                "table_breakdown": [
                    {
                        "table_name": row.table_name,
                        "total": row.total,
                        "passed": row.passed,
                        "success_rate": (row.passed / row.total * 100) if row.total > 0 else 0
                    }
                    for row in table_breakdown
                ]
            }

# Initialization function
def initialize_database(database_url: str = None) -> DatabaseManager:
    """Initialize database with all components"""
    try:
        if not database_url:
            # Get from environment
            database_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_URL', '').replace('https://', 'postgresql://postgres:')

        if not database_url:
            raise ValueError("Database URL not provided")

        db_manager = DatabaseManager(database_url)
        db_manager.initialize_sync()
        db_manager.initialize_async()

        # Create tables if they don't exist
        db_manager.create_tables()

        logger.info("✅ Database initialized successfully with all models")
        return db_manager

    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

# Example usage
def main():
    """Example usage of the SQLAlchemy models"""
    try:
        # Initialize database
        db_manager = initialize_database()

        # Create operations instances
        property_ops = PropertyDataOperations(db_manager)
        entity_ops = EntityOperations(db_manager)
        monitoring_ops = MonitoringOperations(db_manager)

        # Example: Search properties
        properties = property_ops.search_properties(
            county="BROWARD",
            min_value=100000,
            max_value=500000,
            limit=10
        )
        print(f"Found {len(properties)} properties in BROWARD county")

        # Example: Log a metric
        monitoring_ops.log_metric(
            table_name="florida_parcels",
            metric_type="record_count",
            metric_value=1500000,
            metric_unit="count"
        )

        # Example: Get validation summary
        validation_summary = monitoring_ops.get_validation_summary()
        print(f"Validation summary: {validation_summary}")

        print("✅ SQLAlchemy operations test completed successfully")

    except Exception as e:
        print(f"❌ SQLAlchemy test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    main()