#!/usr/bin/env python3
"""
Comprehensive Supabase Database Analyzer
=========================================
This script performs a complete analysis of the Supabase PostgreSQL database
to discover all tables, analyze data completeness, and identify missing data.

Features:
- SQLAlchemy-based database inspection
- Full schema documentation
- Data completeness analysis
- Sales data discovery
- Property analysis
- Performance insights
"""

import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database imports
import sqlalchemy as sa
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import psycopg2
from psycopg2 import sql

# Pyspark for large data analysis
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, count, when, isnan, isnull
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    print("PySpark not available - will use pandas for analysis")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('supabase_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SupabaseAnalyzer:
    """Comprehensive Supabase database analyzer"""

    def __init__(self, db_url: str = None):
        """Initialize the analyzer with database connection"""
        self.db_url = db_url or self._get_db_url()
        self.engine = None
        self.session = None
        self.inspector = None
        self.metadata = None
        self.spark = None

        # Analysis results storage
        self.schema_data = {}
        self.completeness_data = {}
        self.analysis_results = {}

        self._connect()

    def _get_db_url(self) -> str:
        """Get database URL from environment variables"""
        # Try different environment variable patterns
        db_url_vars = [
            'DATABASE_URL',
            'POSTGRES_URL_NON_POOLING',
            'POSTGRES_URL',
            'SUPABASE_DB_URL'
        ]

        for var in db_url_vars:
            url = os.getenv(var)
            if url:
                logger.info(f"Using database URL from {var}")
                # Convert postgres:// to postgresql+psycopg2:// if needed
                if url.startswith('postgres://'):
                    url = url.replace('postgres://', 'postgresql+psycopg2://', 1)

                # Clean up invalid connection options for psycopg2
                if '&supa=' in url:
                    url = url.split('&supa=')[0]
                if '&pgbouncer=' in url:
                    url = url.split('&pgbouncer=')[0]

                return url

        # Construct from individual components
        host = os.getenv('POSTGRES_HOST', 'db.pmispwtdngkcmsrsjwbp.supabase.co')
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD')
        database = os.getenv('POSTGRES_DATABASE', 'postgres')
        port = os.getenv('POSTGRES_PORT', '5432')

        if password:
            url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
            logger.info("Constructed database URL from components")
            return url

        raise ValueError("No database URL found in environment variables")

    def _connect(self):
        """Establish database connections"""
        try:
            # SQLAlchemy connection
            self.engine = create_engine(
                self.db_url,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                echo=False
            )

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            Session = sessionmaker(bind=self.engine)
            self.session = Session()

            # Database inspector
            self.inspector = inspect(self.engine)
            self.metadata = MetaData()

            logger.info("Successfully connected to Supabase database")

            # Initialize Spark if available and dealing with large datasets
            if PYSPARK_AVAILABLE:
                self._init_spark()

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _init_spark(self):
        """Initialize Spark session for large data analysis"""
        try:
            self.spark = SparkSession.builder \
                .appName("SupabaseAnalyzer") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.driver.memory", "4g") \
                .config("spark.executor.memory", "4g") \
                .getOrCreate()

            logger.info("Spark session initialized for large data analysis")
        except Exception as e:
            logger.warning(f"Failed to initialize Spark: {e}")
            self.spark = None

    def discover_all_tables(self) -> Dict[str, Any]:
        """Discover all tables in the database"""
        logger.info("Discovering all tables in database...")

        try:
            # Get all table names
            table_names = self.inspector.get_table_names()

            # Get all views
            view_names = self.inspector.get_view_names()

            tables_info = {}

            for table_name in table_names:
                logger.info(f"Analyzing table: {table_name}")

                # Get table columns
                columns = self.inspector.get_columns(table_name)

                # Get primary keys
                pk_constraint = self.inspector.get_pk_constraint(table_name)
                primary_keys = pk_constraint.get('constrained_columns', [])

                # Get foreign keys
                foreign_keys = self.inspector.get_foreign_keys(table_name)

                # Get indexes
                indexes = self.inspector.get_indexes(table_name)

                # Get table size and row count
                row_count, table_size = self._get_table_stats(table_name)

                # Column analysis
                column_info = []
                for col in columns:
                    col_stats = self._analyze_column(table_name, col['name'])
                    column_info.append({
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'default': col.get('default'),
                        'stats': col_stats
                    })

                tables_info[table_name] = {
                    'type': 'table',
                    'columns': column_info,
                    'primary_keys': primary_keys,
                    'foreign_keys': foreign_keys,
                    'indexes': indexes,
                    'row_count': row_count,
                    'table_size': table_size,
                    'analysis_timestamp': datetime.now().isoformat()
                }

            # Analyze views separately
            for view_name in view_names:
                logger.info(f"Analyzing view: {view_name}")

                try:
                    columns = self.inspector.get_columns(view_name)
                    column_info = [{
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable']
                    } for col in columns]

                    tables_info[view_name] = {
                        'type': 'view',
                        'columns': column_info,
                        'analysis_timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.warning(f"Failed to analyze view {view_name}: {e}")

            self.schema_data = tables_info
            logger.info(f"Discovered {len(table_names)} tables and {len(view_names)} views")

            return tables_info

        except Exception as e:
            logger.error(f"Failed to discover tables: {e}")
            raise

    def _get_table_stats(self, table_name: str) -> Tuple[int, str]:
        """Get table statistics (row count and size)"""
        try:
            # Get row count
            query = text(f"SELECT COUNT(*) FROM {table_name}")
            result = self.session.execute(query)
            row_count = result.scalar()

            # Get table size
            size_query = text("""
                SELECT pg_size_pretty(pg_total_relation_size(%s))
            """)
            result = self.session.execute(size_query, (table_name,))
            table_size = result.scalar()

            return row_count, table_size

        except Exception as e:
            logger.warning(f"Failed to get stats for table {table_name}: {e}")
            return 0, "Unknown"

    def _analyze_column(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """Analyze individual column statistics"""
        try:
            # Basic statistics query
            query = text(f"""
                SELECT
                    COUNT(*) as total_count,
                    COUNT({column_name}) as non_null_count,
                    COUNT(DISTINCT {column_name}) as distinct_count
                FROM {table_name}
            """)

            result = self.session.execute(query).fetchone()

            total_count = result[0]
            non_null_count = result[1]
            distinct_count = result[2]

            null_count = total_count - non_null_count
            null_percentage = (null_count / total_count * 100) if total_count > 0 else 0

            return {
                'total_rows': total_count,
                'non_null_count': non_null_count,
                'null_count': null_count,
                'null_percentage': round(null_percentage, 2),
                'distinct_count': distinct_count,
                'completeness': round((non_null_count / total_count * 100) if total_count > 0 else 0, 2)
            }

        except Exception as e:
            logger.warning(f"Failed to analyze column {table_name}.{column_name}: {e}")
            return {
                'total_rows': 0,
                'non_null_count': 0,
                'null_count': 0,
                'null_percentage': 0,
                'distinct_count': 0,
                'completeness': 0,
                'error': str(e)
            }

    def analyze_florida_parcels(self) -> Dict[str, Any]:
        """Comprehensive analysis of florida_parcels table"""
        logger.info("Analyzing florida_parcels table...")

        try:
            # Check if table exists
            if 'florida_parcels' not in self.schema_data:
                logger.warning("florida_parcels table not found")
                return {'error': 'florida_parcels table not found'}

            # Get basic stats
            total_count_query = text("SELECT COUNT(*) FROM florida_parcels")
            total_count = self.session.execute(total_count_query).scalar()

            # County distribution
            county_query = text("""
                SELECT county, COUNT(*) as count
                FROM florida_parcels
                WHERE county IS NOT NULL
                GROUP BY county
                ORDER BY count DESC
            """)
            county_results = self.session.execute(county_query).fetchall()
            county_distribution = {row[0]: row[1] for row in county_results}

            # Year distribution
            year_query = text("""
                SELECT year, COUNT(*) as count
                FROM florida_parcels
                WHERE year IS NOT NULL
                GROUP BY year
                ORDER BY year DESC
            """)
            year_results = self.session.execute(year_query).fetchall()
            year_distribution = {row[0]: row[1] for row in year_results}

            # Data completeness by key fields
            completeness_fields = [
                'parcel_id', 'county', 'year', 'phy_addr1', 'owner_name1',
                'just_value', 'land_value', 'building_value', 'land_sqft',
                'living_units', 'property_use_code', 'deed_book', 'deed_page'
            ]

            field_completeness = {}
            for field in completeness_fields:
                try:
                    query = text(f"""
                        SELECT
                            COUNT(*) as total,
                            COUNT({field}) as non_null,
                            ROUND(COUNT({field}) * 100.0 / COUNT(*), 2) as percentage
                        FROM florida_parcels
                    """)
                    result = self.session.execute(query).fetchone()
                    field_completeness[field] = {
                        'total': result[0],
                        'non_null': result[1],
                        'percentage': result[2]
                    }
                except Exception as e:
                    logger.warning(f"Failed to analyze field {field}: {e}")
                    field_completeness[field] = {'error': str(e)}

            # Geographic distribution
            geographic_query = text("""
                SELECT
                    county,
                    COUNT(*) as total_properties,
                    COUNT(CASE WHEN just_value > 0 THEN 1 END) as valued_properties,
                    AVG(CASE WHEN just_value > 0 THEN just_value END) as avg_value,
                    MIN(year) as earliest_year,
                    MAX(year) as latest_year
                FROM florida_parcels
                WHERE county IS NOT NULL
                GROUP BY county
                ORDER BY total_properties DESC
            """)

            geographic_results = self.session.execute(geographic_query).fetchall()
            geographic_analysis = {}
            for row in geographic_results:
                geographic_analysis[row[0]] = {
                    'total_properties': row[1],
                    'valued_properties': row[2],
                    'avg_value': float(row[3]) if row[3] else 0,
                    'earliest_year': row[4],
                    'latest_year': row[5]
                }

            analysis_result = {
                'table_name': 'florida_parcels',
                'total_records': total_count,
                'county_distribution': county_distribution,
                'year_distribution': year_distribution,
                'field_completeness': field_completeness,
                'geographic_analysis': geographic_analysis,
                'analysis_timestamp': datetime.now().isoformat()
            }

            self.completeness_data['florida_parcels'] = analysis_result
            return analysis_result

        except Exception as e:
            logger.error(f"Failed to analyze florida_parcels: {e}")
            return {'error': str(e)}

    def find_sales_tables(self) -> Dict[str, Any]:
        """Find and analyze all sales-related tables"""
        logger.info("Searching for sales-related tables...")

        sales_keywords = [
            'sale', 'sales', 'sdf', 'transaction', 'transfer', 'deed',
            'florida_sales', 'property_sales', 'real_estate_sales'
        ]

        sales_tables = {}

        # Search in discovered tables
        for table_name in self.schema_data.keys():
            table_name_lower = table_name.lower()

            # Check if table name contains sales keywords
            for keyword in sales_keywords:
                if keyword in table_name_lower:
                    logger.info(f"Found potential sales table: {table_name}")

                    # Analyze the table structure
                    table_info = self.schema_data[table_name]

                    # Look for sales-specific columns
                    sales_columns = []
                    for col in table_info.get('columns', []):
                        col_name_lower = col['name'].lower()
                        if any(sales_word in col_name_lower for sales_word in [
                            'sale', 'price', 'amount', 'value', 'date', 'year', 'month'
                        ]):
                            sales_columns.append(col)

                    # Get sample data if table has rows
                    sample_data = None
                    if table_info.get('row_count', 0) > 0:
                        sample_data = self._get_sample_data(table_name, limit=5)

                    sales_tables[table_name] = {
                        'table_info': table_info,
                        'sales_columns': sales_columns,
                        'sample_data': sample_data,
                        'potential_sales_indicators': [keyword for keyword in sales_keywords if keyword in table_name_lower]
                    }
                    break

        # Also check if sales data is embedded in florida_parcels
        if 'florida_parcels' in self.schema_data:
            parcels_info = self.schema_data['florida_parcels']
            sales_columns_in_parcels = []

            for col in parcels_info.get('columns', []):
                col_name_lower = col['name'].lower()
                if any(sales_word in col_name_lower for sales_word in [
                    'sale', 'deed', 'transfer', 'price'
                ]):
                    sales_columns_in_parcels.append(col)

            if sales_columns_in_parcels:
                sales_tables['florida_parcels_sales_data'] = {
                    'table_info': parcels_info,
                    'sales_columns': sales_columns_in_parcels,
                    'note': 'Sales data embedded in florida_parcels table'
                }

        return sales_tables

    def _get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict]:
        """Get sample data from a table"""
        try:
            query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
            result = self.session.execute(query)
            columns = result.keys()
            rows = result.fetchall()

            sample_data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Convert non-serializable types
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    elif isinstance(value, (bytes, memoryview)):
                        value = str(value)
                    row_dict[col] = value
                sample_data.append(row_dict)

            return sample_data

        except Exception as e:
            logger.warning(f"Failed to get sample data from {table_name}: {e}")
            return []

    def analyze_specific_properties(self, parcel_ids: List[str]) -> Dict[str, Any]:
        """Analyze specific properties across all tables"""
        logger.info(f"Analyzing specific properties: {parcel_ids}")

        results = {}

        for parcel_id in parcel_ids:
            logger.info(f"Searching for property: {parcel_id}")
            property_data = {}

            # Search in all tables for this parcel ID
            for table_name in self.schema_data.keys():
                if self.schema_data[table_name]['type'] != 'table':
                    continue

                # Check if table has parcel_id column
                columns = [col['name'] for col in self.schema_data[table_name]['columns']]
                parcel_columns = [col for col in columns if 'parcel' in col.lower()]

                if parcel_columns:
                    for parcel_col in parcel_columns:
                        try:
                            query = text(f"SELECT * FROM {table_name} WHERE {parcel_col} = :parcel_id")
                            result = self.session.execute(query, {'parcel_id': parcel_id})
                            rows = result.fetchall()

                            if rows:
                                columns = result.keys()
                                property_records = []

                                for row in rows:
                                    row_dict = {}
                                    for i, col in enumerate(columns):
                                        value = row[i]
                                        # Convert non-serializable types
                                        if hasattr(value, 'isoformat'):
                                            value = value.isoformat()
                                        elif isinstance(value, (bytes, memoryview)):
                                            value = str(value)
                                        row_dict[col] = value
                                    property_records.append(row_dict)

                                property_data[f"{table_name}_{parcel_col}"] = {
                                    'table': table_name,
                                    'column': parcel_col,
                                    'records_found': len(property_records),
                                    'data': property_records
                                }

                                logger.info(f"Found {len(property_records)} records for {parcel_id} in {table_name}.{parcel_col}")

                        except Exception as e:
                            logger.warning(f"Failed to search {table_name}.{parcel_col} for {parcel_id}: {e}")

            results[parcel_id] = property_data

        return results

    def generate_completeness_report(self) -> Dict[str, Any]:
        """Generate comprehensive data completeness report"""
        logger.info("Generating data completeness report...")

        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'database_overview': {
                'total_tables': len([t for t in self.schema_data.values() if t['type'] == 'table']),
                'total_views': len([t for t in self.schema_data.values() if t['type'] == 'view']),
                'total_columns': sum(len(t['columns']) for t in self.schema_data.values())
            },
            'table_analysis': {},
            'missing_data_summary': {},
            'recommendations': []
        }

        # Analyze each table
        for table_name, table_info in self.schema_data.items():
            if table_info['type'] != 'table':
                continue

            table_analysis = {
                'row_count': table_info.get('row_count', 0),
                'column_count': len(table_info['columns']),
                'primary_keys': table_info.get('primary_keys', []),
                'foreign_keys': len(table_info.get('foreign_keys', [])),
                'indexes': len(table_info.get('indexes', [])),
                'columns_with_high_nulls': [],
                'columns_with_low_cardinality': [],
                'completeness_score': 0
            }

            total_completeness = 0
            column_count = 0

            for col in table_info['columns']:
                stats = col.get('stats', {})
                completeness = stats.get('completeness', 0)
                total_completeness += completeness
                column_count += 1

                # Flag columns with high null percentage
                if stats.get('null_percentage', 0) > 50:
                    table_analysis['columns_with_high_nulls'].append({
                        'column': col['name'],
                        'null_percentage': stats.get('null_percentage', 0)
                    })

                # Flag columns with low cardinality (potential enum/category fields)
                total_rows = stats.get('total_rows', 0)
                distinct_count = stats.get('distinct_count', 0)
                if total_rows > 100 and distinct_count < 10:
                    table_analysis['columns_with_low_cardinality'].append({
                        'column': col['name'],
                        'distinct_count': distinct_count,
                        'total_rows': total_rows
                    })

            table_analysis['completeness_score'] = round(total_completeness / column_count if column_count > 0 else 0, 2)
            report['table_analysis'][table_name] = table_analysis

        # Generate recommendations
        for table_name, analysis in report['table_analysis'].items():
            if analysis['completeness_score'] < 80:
                report['recommendations'].append(f"Table {table_name} has low completeness score ({analysis['completeness_score']}%)")

            if len(analysis['columns_with_high_nulls']) > 0:
                report['recommendations'].append(f"Table {table_name} has {len(analysis['columns_with_high_nulls'])} columns with >50% null values")

            if not analysis['primary_keys']:
                report['recommendations'].append(f"Table {table_name} lacks primary key constraints")

        return report

    def export_results(self, output_dir: str = "."):
        """Export all analysis results to files"""
        logger.info(f"Exporting analysis results to {output_dir}...")

        os.makedirs(output_dir, exist_ok=True)

        # Export schema documentation
        schema_file = os.path.join(output_dir, "database_schema_complete.json")
        with open(schema_file, 'w') as f:
            json.dump(self.schema_data, f, indent=2, default=str)
        logger.info(f"Schema exported to {schema_file}")

        # Export completeness report
        completeness_report = self.generate_completeness_report()
        completeness_file = os.path.join(output_dir, "data_completeness_report.json")
        with open(completeness_file, 'w') as f:
            json.dump(completeness_report, f, indent=2, default=str)
        logger.info(f"Completeness report exported to {completeness_file}")

        # Export analysis results
        if self.analysis_results:
            results_file = os.path.join(output_dir, "analysis_results.json")
            with open(results_file, 'w') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            logger.info(f"Analysis results exported to {results_file}")

        # Generate markdown summary
        self._generate_markdown_report(output_dir, completeness_report)

    def _generate_markdown_report(self, output_dir: str, completeness_report: Dict):
        """Generate markdown summary report"""
        report_file = os.path.join(output_dir, "data_completeness_report.md")

        with open(report_file, 'w') as f:
            f.write("# Supabase Database Analysis Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Overview
            overview = completeness_report['database_overview']
            f.write("## Database Overview\n\n")
            f.write(f"- **Total Tables**: {overview['total_tables']}\n")
            f.write(f"- **Total Views**: {overview['total_views']}\n")
            f.write(f"- **Total Columns**: {overview['total_columns']}\n\n")

            # Table Analysis
            f.write("## Table Analysis\n\n")
            f.write("| Table | Rows | Columns | Completeness | Primary Keys | Indexes |\n")
            f.write("|-------|------|---------|--------------|--------------|----------|\n")

            for table_name, analysis in completeness_report['table_analysis'].items():
                f.write(f"| {table_name} | {analysis['row_count']:,} | {analysis['column_count']} | {analysis['completeness_score']}% | {len(analysis['primary_keys'])} | {analysis['indexes']} |\n")

            # Recommendations
            f.write("\n## Recommendations\n\n")
            for i, rec in enumerate(completeness_report['recommendations'], 1):
                f.write(f"{i}. {rec}\n")

            # Data Quality Issues
            f.write("\n## Data Quality Issues\n\n")
            for table_name, analysis in completeness_report['table_analysis'].items():
                if analysis['columns_with_high_nulls']:
                    f.write(f"### {table_name} - High Null Columns\n\n")
                    for col_info in analysis['columns_with_high_nulls']:
                        f.write(f"- **{col_info['column']}**: {col_info['null_percentage']}% null\n")
                    f.write("\n")

        logger.info(f"Markdown report exported to {report_file}")

    def run_complete_analysis(self):
        """Run the complete database analysis"""
        logger.info("Starting complete database analysis...")

        try:
            # 1. Discover all tables
            logger.info("Step 1: Discovering all tables...")
            self.discover_all_tables()

            # 2. Analyze florida_parcels specifically
            logger.info("Step 2: Analyzing florida_parcels table...")
            florida_analysis = self.analyze_florida_parcels()
            self.analysis_results['florida_parcels_analysis'] = florida_analysis

            # 3. Find and analyze sales tables
            logger.info("Step 3: Finding sales-related tables...")
            sales_analysis = self.find_sales_tables()
            self.analysis_results['sales_tables_analysis'] = sales_analysis

            # 4. Analyze specific properties
            logger.info("Step 4: Analyzing specific properties...")
            specific_properties = ['1078130000370', '504231242730']
            property_analysis = self.analyze_specific_properties(specific_properties)
            self.analysis_results['specific_properties_analysis'] = property_analysis

            # 5. Export all results
            logger.info("Step 5: Exporting results...")
            self.export_results()

            logger.info("Complete analysis finished successfully!")

            # Print summary
            self._print_summary()

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    def _print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*60)
        print("SUPABASE DATABASE ANALYSIS SUMMARY")
        print("="*60)

        total_tables = len([t for t in self.schema_data.values() if t['type'] == 'table'])
        total_views = len([t for t in self.schema_data.values() if t['type'] == 'view'])

        print(f"Total Tables Discovered: {total_tables}")
        print(f"Total Views Discovered: {total_views}")

        # Show largest tables
        table_sizes = []
        for name, info in self.schema_data.items():
            if info['type'] == 'table' and 'row_count' in info:
                table_sizes.append((name, info['row_count']))

        table_sizes.sort(key=lambda x: x[1], reverse=True)

        print(f"\nLargest Tables:")
        for i, (name, count) in enumerate(table_sizes[:5], 1):
            print(f"{i}. {name}: {count:,} rows")

        # Show sales tables found
        sales_tables = self.analysis_results.get('sales_tables_analysis', {})
        print(f"\nSales-related tables found: {len(sales_tables)}")
        for table_name in sales_tables.keys():
            print(f"- {table_name}")

        print(f"\nAnalysis complete! Check the generated files for detailed results.")
        print("="*60)

    def close(self):
        """Clean up connections"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
        if self.spark:
            self.spark.stop()

def main():
    """Main execution function"""
    try:
        # Initialize analyzer
        analyzer = SupabaseAnalyzer()

        # Run complete analysis
        analyzer.run_complete_analysis()

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)
    finally:
        if 'analyzer' in locals():
            analyzer.close()

if __name__ == "__main__":
    main()