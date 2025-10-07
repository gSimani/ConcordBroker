"""
Comprehensive Data Integration Analysis for ConcordBroker
Analyzes Supabase database connections and creates integration plan for MiniPropertyCard
"""

import os
import json
import pandas as pd
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.orm import sessionmaker
import requests
from typing import Dict, List, Any
from datetime import datetime

# Environment configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"
POSTGRES_URL = "postgresql://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

class SupabaseDataAnalyzer:
    """Analyzes Supabase database structure and data relationships"""

    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        self.engine = None
        self.metadata = MetaData()

    def connect_database(self):
        """Establish database connection using SQLAlchemy"""
        try:
            # Fix the URL format
            postgres_url = POSTGRES_URL.replace("%40", "@")
            self.engine = create_engine(postgres_url)
            self.metadata.reflect(self.engine)
            print(" Database connection established")
            return True
        except Exception as e:
            print(f" Database connection failed: {e}")
            # Fallback to REST API
            return False

    def analyze_tables(self) -> Dict[str, Any]:
        """Analyze all tables in the database"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "tables": {},
            "relationships": [],
            "minicard_mappings": {}
        }

        # Tables expected for MiniPropertyCard
        property_tables = [
            "florida_parcels",
            "sales_history",
            "property_characteristics",
            "property_values",
            "property_owners",
            "tax_assessments",
            "exemptions",
            "property_use_codes",
            "dor_use_codes"
        ]

        for table_name in property_tables:
            try:
                # Try REST API first
                response = requests.get(
                    f"{self.supabase_url}/rest/v1/{table_name}",
                    headers=self.headers,
                    params={"limit": 1}
                )

                if response.status_code == 200:
                    data = response.json()
                    if data:
                        columns = list(data[0].keys())
                        analysis["tables"][table_name] = {
                            "exists": True,
                            "columns": columns,
                            "sample_row": data[0]
                        }
                        print(f" Found table: {table_name} with {len(columns)} columns")
                    else:
                        analysis["tables"][table_name] = {
                            "exists": True,
                            "columns": [],
                            "empty": True
                        }
                        print(f" Table {table_name} exists but is empty")
                else:
                    analysis["tables"][table_name] = {
                        "exists": False,
                        "error": f"Status {response.status_code}"
                    }
                    print(f" Table {table_name} not accessible: {response.status_code}")

            except Exception as e:
                analysis["tables"][table_name] = {
                    "exists": False,
                    "error": str(e)
                }
                print(f" Error accessing {table_name}: {e}")

        # Map database fields to MiniPropertyCard requirements
        analysis["minicard_mappings"] = self.create_minicard_mappings(analysis["tables"])

        return analysis

    def create_minicard_mappings(self, tables: Dict) -> Dict[str, Any]:
        """Map database fields to MiniPropertyCard component requirements"""

        # MiniPropertyCard expects these fields
        minicard_fields = {
            "phy_addr1": "Physical address line 1",
            "phy_city": "City name",
            "phy_zipcode": "Zip code",
            "owner_name": "Property owner name",
            "jv": "Just/Appraised value",
            "tv_sd": "Taxable value",
            "property_use": "Property use code",
            "sale_price": "Recent sale price",
            "sale_date": "Recent sale date",
            "land_sqft": "Land square footage",
            "building_sqft": "Building square footage",
            "year_built": "Year property built",
            "bedrooms": "Number of bedrooms",
            "bathrooms": "Number of bathrooms",
            "parcel_id": "Parcel identifier",
            "county": "County name"
        }

        mappings = {}

        # Check florida_parcels table for primary data
        if "florida_parcels" in tables and tables["florida_parcels"].get("exists"):
            columns = tables["florida_parcels"].get("columns", [])
            for field, description in minicard_fields.items():
                if field in columns:
                    mappings[field] = {
                        "source_table": "florida_parcels",
                        "source_column": field,
                        "available": True,
                        "description": description
                    }
                else:
                    # Try to find alternative column names
                    alternatives = self.find_alternative_columns(field, columns)
                    if alternatives:
                        mappings[field] = {
                            "source_table": "florida_parcels",
                            "source_column": alternatives[0],
                            "available": True,
                            "alternatives": alternatives,
                            "description": description
                        }
                    else:
                        mappings[field] = {
                            "available": False,
                            "description": description,
                            "needs_join": True
                        }

        return mappings

    def find_alternative_columns(self, target_field: str, columns: List[str]) -> List[str]:
        """Find alternative column names that might match the target field"""
        alternatives = []

        # Common mappings
        field_mappings = {
            "jv": ["just_value", "appraised_value", "market_value"],
            "tv_sd": ["taxable_value", "assessed_value", "tax_value"],
            "owner_name": ["owner", "owner1", "own_name"],
            "phy_addr1": ["property_address", "address1", "site_addr1"],
            "phy_city": ["city", "property_city", "site_city"],
            "phy_zipcode": ["zip", "zipcode", "zip_code", "postal_code"],
            "land_sqft": ["land_square_feet", "lot_size", "land_area"],
            "building_sqft": ["building_square_feet", "living_area", "total_sqft"]
        }

        if target_field in field_mappings:
            for alt in field_mappings[target_field]:
                if alt in columns:
                    alternatives.append(alt)

        return alternatives

    def analyze_filters(self) -> Dict[str, Any]:
        """Analyze filtering requirements for MiniPropertyCard"""

        filters = {
            "property_type": {
                "description": "Filter by property category",
                "values": [
                    "Single Family",
                    "Condo",
                    "Multi-family",
                    "Commercial",
                    "Vacant Land",
                    "Other"
                ],
                "implementation": "Use property_use codes and categorization logic"
            },
            "price_range": {
                "description": "Filter by just value (jv)",
                "ranges": [
                    {"min": 0, "max": 100000, "label": "Under $100K"},
                    {"min": 100000, "max": 250000, "label": "$100K - $250K"},
                    {"min": 250000, "max": 500000, "label": "$250K - $500K"},
                    {"min": 500000, "max": 1000000, "label": "$500K - $1M"},
                    {"min": 1000000, "max": None, "label": "Over $1M"}
                ]
            },
            "location": {
                "description": "Filter by city or zip code",
                "fields": ["phy_city", "phy_zipcode"],
                "type": "text_search"
            },
            "size": {
                "description": "Filter by property size",
                "fields": ["land_sqft", "building_sqft"],
                "type": "range"
            },
            "year_built": {
                "description": "Filter by construction year",
                "type": "range",
                "field": "year_built"
            },
            "sale_date": {
                "description": "Filter by recent sales",
                "type": "date_range",
                "field": "sale_date"
            }
        }

        return filters

    def generate_sqlalchemy_models(self) -> str:
        """Generate SQLAlchemy models for database access"""

        models_code = '''"""
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
'''

        return models_code

    def generate_report(self, analysis: Dict) -> str:
        """Generate comprehensive analysis report"""

        report = f"""
# ConcordBroker Data Integration Analysis Report
Generated: {analysis['timestamp']}

## Database Structure Analysis

### Available Tables:
"""
        for table_name, info in analysis['tables'].items():
            if info.get('exists'):
                columns_count = len(info.get('columns', []))
                report += f" **{table_name}** - {columns_count} columns\n"
            else:
                report += f" **{table_name}** - Not found or inaccessible\n"

        report += """

## MiniPropertyCard Field Mappings

### Required Fields and Data Sources:
"""
        for field, mapping in analysis.get('minicard_mappings', {}).items():
            if mapping.get('available'):
                source = f"{mapping['source_table']}.{mapping['source_column']}"
                report += f" **{field}**  {source}\n"
            else:
                report += f" **{field}**  Needs additional data source\n"

        report += """

## Filter Implementation Strategy

### 1. Property Type Filter
- Use `property_use` field with DOR code categorization
- Categories: Single Family, Condo, Multi-family, Commercial, Vacant Land

### 2. Price Range Filter
- Use `jv` (just value) field
- Implement ranges: <$100K, $100K-$250K, $250K-$500K, $500K-$1M, >$1M

### 3. Location Filter
- Index on `phy_city` and `phy_zipcode`
- Implement autocomplete search

### 4. Size Filter
- Use `land_sqft` and `building_sqft` fields
- Allow min/max range selection

### 5. Year Built Filter
- Use `year_built` field
- Decade-based grouping

## Implementation Recommendations

1. **Database Optimization**
   - Create composite indexes for common filter combinations
   - Implement materialized views for complex queries
   - Use connection pooling for better performance

2. **API Layer**
   - Create RESTful endpoints for filtered property searches
   - Implement pagination with cursor-based navigation
   - Add response caching for frequently accessed data

3. **Frontend Integration**
   - Use React Query for data fetching and caching
   - Implement virtual scrolling for large result sets
   - Add progressive loading for better UX

4. **Data Pipeline**
   - Set up ETL process for regular data updates
   - Implement data validation and cleaning
   - Create backup and recovery procedures
"""

        return report

# Main execution
if __name__ == "__main__":
    print("Starting ConcordBroker Data Integration Analysis...")

    analyzer = SupabaseDataAnalyzer()

    # Analyze database structure
    analysis = analyzer.analyze_tables()

    # Analyze filter requirements
    filters = analyzer.analyze_filters()
    analysis["filters"] = filters

    # Generate SQLAlchemy models
    models_code = analyzer.generate_sqlalchemy_models()

    # Save models to file
    with open("database_models.py", "w") as f:
        f.write(models_code)
    print(" SQLAlchemy models saved to database_models.py")

    # Generate and save analysis report
    report = analyzer.generate_report(analysis)
    with open("data_integration_report.md", "w") as f:
        f.write(report)
    print(" Analysis report saved to data_integration_report.md")

    # Save raw analysis as JSON
    with open("data_analysis_results.json", "w") as f:
        json.dump(analysis, f, indent=2, default=str)
    print(" Raw analysis saved to data_analysis_results.json")

    print("\n Analysis Complete!")
    print(f"Tables analyzed: {len(analysis['tables'])}")
    print(f"Field mappings created: {len(analysis['minicard_mappings'])}")
    print(f"Filters defined: {len(filters)}")