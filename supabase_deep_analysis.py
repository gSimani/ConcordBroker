#!/usr/bin/env python3
"""
Supabase Database Deep Analysis
Uses advanced data science tools to analyze the database comprehensively
"""

import os
import sys
import json
import warnings
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, inspect, text
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import IsolationForest
from scipy import stats
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class SupabaseAnalyzer:
    def __init__(self):
        """Initialize connection to Supabase"""
        # Get connection details from environment - use correct host
        # Using the pooler URL from env file
        self.db_url = "postgresql://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613%21@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
        self.engine = None
        self.conn = None
        self.inspector = None
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'database_info': {},
            'schema_analysis': {},
            'data_statistics': {},
            'data_quality': {},
            'patterns': {},
            'anomalies': {},
            'recommendations': []
        }

    def connect(self):
        """Establish database connection"""
        try:
            # Create SQLAlchemy engine
            self.engine = create_engine(self.db_url)
            self.inspector = inspect(self.engine)

            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"[SUCCESS] Connected to PostgreSQL: {version}")
                self.analysis_results['database_info']['version'] = version

            # Get psycopg2 connection for advanced queries
            # Use a direct connection string for psycopg2
            self.conn = psycopg2.connect(
                host="aws-1-us-east-1.pooler.supabase.com",
                port=6543,
                database="postgres",
                user="postgres.pmispwtdngkcmsrsjwbp",
                password="West@Boca613!"
            )

            return True

        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False

    def analyze_schema(self):
        """Analyze database schema and structure"""
        print("\n" + "="*80)
        print("SCHEMA ANALYSIS")
        print("="*80)

        schemas = self.inspector.get_schema_names()
        self.analysis_results['schema_analysis']['schemas'] = schemas

        schema_details = {}
        total_tables = 0
        total_columns = 0
        total_indexes = 0

        for schema in schemas:
            if schema in ['pg_catalog', 'information_schema', 'pg_toast']:
                continue

            tables = self.inspector.get_table_names(schema=schema)
            schema_details[schema] = {
                'tables': {},
                'table_count': len(tables)
            }
            total_tables += len(tables)

            for table in tables:
                columns = self.inspector.get_columns(table, schema=schema)
                indexes = self.inspector.get_indexes(table, schema=schema)
                pk = self.inspector.get_pk_constraint(table, schema=schema)
                fks = self.inspector.get_foreign_keys(table, schema=schema)

                total_columns += len(columns)
                total_indexes += len(indexes)

                schema_details[schema]['tables'][table] = {
                    'columns': len(columns),
                    'indexes': len(indexes),
                    'primary_key': pk['constrained_columns'] if pk else [],
                    'foreign_keys': len(fks),
                    'column_types': {col['name']: str(col['type']) for col in columns}
                }

        self.analysis_results['schema_analysis']['details'] = schema_details
        self.analysis_results['schema_analysis']['summary'] = {
            'total_schemas': len([s for s in schemas if s not in ['pg_catalog', 'information_schema', 'pg_toast']]),
            'total_tables': total_tables,
            'total_columns': total_columns,
            'total_indexes': total_indexes
        }

        print(f"Schemas analyzed: {len(schemas)}")
        print(f"Total tables: {total_tables}")
        print(f"Total columns: {total_columns}")
        print(f"Total indexes: {total_indexes}")

        return schema_details

    def analyze_data_statistics(self):
        """Perform statistical analysis on all tables"""
        print("\n" + "="*80)
        print("DATA STATISTICS ANALYSIS")
        print("="*80)

        stats_results = {}

        # Get all tables from public schema
        tables = self.inspector.get_table_names(schema='public')

        for table in tables[:10]:  # Analyze first 10 tables for demo
            try:
                # Get row count
                query = f"SELECT COUNT(*) as count FROM public.{table}"
                df = pd.read_sql(query, self.engine)
                row_count = df['count'].iloc[0]

                if row_count == 0:
                    continue

                # Get sample data for analysis
                sample_query = f"SELECT * FROM public.{table} LIMIT 10000"
                df_sample = pd.read_sql(sample_query, self.engine)

                table_stats = {
                    'row_count': int(row_count),
                    'columns': len(df_sample.columns),
                    'memory_usage': df_sample.memory_usage(deep=True).sum() / 1024 / 1024,  # MB
                    'column_stats': {}
                }

                # Analyze each column
                for col in df_sample.columns:
                    col_stats = {
                        'dtype': str(df_sample[col].dtype),
                        'null_count': int(df_sample[col].isna().sum()),
                        'null_percentage': float(df_sample[col].isna().mean() * 100),
                        'unique_values': int(df_sample[col].nunique()),
                        'unique_ratio': float(df_sample[col].nunique() / len(df_sample) * 100)
                    }

                    # Additional stats for numeric columns
                    if pd.api.types.is_numeric_dtype(df_sample[col]):
                        col_stats.update({
                            'mean': float(df_sample[col].mean()) if not df_sample[col].isna().all() else None,
                            'median': float(df_sample[col].median()) if not df_sample[col].isna().all() else None,
                            'std': float(df_sample[col].std()) if not df_sample[col].isna().all() else None,
                            'min': float(df_sample[col].min()) if not df_sample[col].isna().all() else None,
                            'max': float(df_sample[col].max()) if not df_sample[col].isna().all() else None
                        })

                    table_stats['column_stats'][col] = col_stats

                stats_results[table] = table_stats
                print(f"  Analyzed table: {table} ({row_count:,} rows)")

            except Exception as e:
                print(f"  [WARNING] Could not analyze table {table}: {e}")
                continue

        self.analysis_results['data_statistics'] = stats_results
        return stats_results

    def analyze_data_quality(self):
        """Analyze data quality issues"""
        print("\n" + "="*80)
        print("DATA QUALITY ANALYSIS")
        print("="*80)

        quality_issues = {
            'tables_with_no_primary_key': [],
            'tables_with_no_indexes': [],
            'columns_with_high_nulls': [],
            'potential_duplicates': [],
            'data_type_mismatches': [],
            'orphaned_records': []
        }

        tables = self.inspector.get_table_names(schema='public')

        for table in tables:
            # Check for primary key
            pk = self.inspector.get_pk_constraint(table, schema='public')
            if not pk or not pk['constrained_columns']:
                quality_issues['tables_with_no_primary_key'].append(table)

            # Check for indexes
            indexes = self.inspector.get_indexes(table, schema='public')
            if not indexes:
                quality_issues['tables_with_no_indexes'].append(table)

            # Check for high null percentages
            try:
                query = f"SELECT * FROM public.{table} LIMIT 1000"
                df = pd.read_sql(query, self.engine)

                for col in df.columns:
                    null_pct = df[col].isna().mean() * 100
                    if null_pct > 50:
                        quality_issues['columns_with_high_nulls'].append({
                            'table': table,
                            'column': col,
                            'null_percentage': round(null_pct, 2)
                        })

            except Exception as e:
                continue

        self.analysis_results['data_quality'] = quality_issues

        print(f"Tables without primary key: {len(quality_issues['tables_with_no_primary_key'])}")
        print(f"Tables without indexes: {len(quality_issues['tables_with_no_indexes'])}")
        print(f"Columns with >50% nulls: {len(quality_issues['columns_with_high_nulls'])}")

        return quality_issues

    def detect_patterns_ml(self):
        """Use machine learning to detect patterns in data"""
        print("\n" + "="*80)
        print("PATTERN DETECTION (Machine Learning)")
        print("="*80)

        patterns = {}

        # Analyze florida_parcels if it exists
        try:
            query = """
            SELECT
                just_value,
                land_value,
                building_value,
                living_area,
                land_sqft,
                year_built,
                bedrooms,
                bathrooms
            FROM public.florida_parcels
            WHERE just_value > 0
                AND land_value > 0
                AND living_area > 0
            LIMIT 10000
            """

            df = pd.read_sql(query, self.engine)

            if len(df) > 100:
                # Remove nulls and prepare data
                df_clean = df.dropna()

                # Standardize features
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(df_clean)

                # PCA for dimensionality reduction
                pca = PCA(n_components=2)
                X_pca = pca.fit_transform(X_scaled)

                # KMeans clustering
                kmeans = KMeans(n_clusters=4, random_state=42)
                clusters = kmeans.fit_predict(X_scaled)

                # Anomaly detection with Isolation Forest
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                anomalies = iso_forest.fit_predict(X_scaled)

                patterns['property_clusters'] = {
                    'n_clusters': 4,
                    'cluster_sizes': pd.Series(clusters).value_counts().to_dict(),
                    'pca_variance_explained': pca.explained_variance_ratio_.tolist(),
                    'anomaly_count': int((anomalies == -1).sum()),
                    'anomaly_percentage': float((anomalies == -1).mean() * 100)
                }

                # Find correlations
                correlation_matrix = df_clean.corr()
                high_correlations = []

                for i in range(len(correlation_matrix.columns)):
                    for j in range(i+1, len(correlation_matrix.columns)):
                        if abs(correlation_matrix.iloc[i, j]) > 0.7:
                            high_correlations.append({
                                'var1': correlation_matrix.columns[i],
                                'var2': correlation_matrix.columns[j],
                                'correlation': round(correlation_matrix.iloc[i, j], 3)
                            })

                patterns['high_correlations'] = high_correlations

                print(f"  Found {len(high_correlations)} high correlations")
                print(f"  Detected {patterns['property_clusters']['anomaly_count']} anomalies")
                print(f"  Created {patterns['property_clusters']['n_clusters']} property clusters")

        except Exception as e:
            print(f"  [WARNING] Could not perform ML analysis: {e}")

        self.analysis_results['patterns'] = patterns
        return patterns

    def generate_visualizations(self):
        """Generate data visualizations"""
        print("\n" + "="*80)
        print("GENERATING VISUALIZATIONS")
        print("="*80)

        # Create output directory
        os.makedirs('supabase_analysis_output', exist_ok=True)

        # 1. Schema complexity visualization
        if self.analysis_results['schema_analysis']['details']:
            fig = go.Figure()

            for schema, details in self.analysis_results['schema_analysis']['details'].items():
                if schema == 'public' and details['tables']:
                    table_names = list(details['tables'].keys())[:20]
                    column_counts = [details['tables'][t]['columns'] for t in table_names]

                    fig.add_trace(go.Bar(
                        x=table_names,
                        y=column_counts,
                        name='Columns per Table'
                    ))

            fig.update_layout(
                title='Database Table Complexity',
                xaxis_title='Table Name',
                yaxis_title='Number of Columns',
                xaxis_tickangle=-45
            )

            fig.write_html('supabase_analysis_output/table_complexity.html')
            print("  Created: table_complexity.html")

        # 2. Data quality heatmap
        try:
            query = """
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            LIMIT 500
            """

            df_schema = pd.read_sql(query, self.engine)

            if len(df_schema) > 0:
                # Create pivot table for visualization
                pivot = df_schema.pivot_table(
                    index='table_name',
                    columns='data_type',
                    values='column_name',
                    aggfunc='count',
                    fill_value=0
                )

                plt.figure(figsize=(12, 8))
                sns.heatmap(pivot.head(20), annot=True, fmt='d', cmap='YlOrRd')
                plt.title('Data Types Distribution Across Tables')
                plt.tight_layout()
                plt.savefig('supabase_analysis_output/data_types_heatmap.png', dpi=100)
                plt.close()
                print("  Created: data_types_heatmap.png")

        except Exception as e:
            print(f"  [WARNING] Could not create heatmap: {e}")

        return True

    def generate_recommendations(self):
        """Generate actionable recommendations based on analysis"""
        print("\n" + "="*80)
        print("GENERATING RECOMMENDATIONS")
        print("="*80)

        recommendations = []

        # Schema recommendations
        if self.analysis_results['data_quality'].get('tables_with_no_primary_key'):
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Schema',
                'issue': f"{len(self.analysis_results['data_quality']['tables_with_no_primary_key'])} tables lack primary keys",
                'recommendation': 'Add primary keys to ensure data integrity and improve query performance',
                'affected_tables': self.analysis_results['data_quality']['tables_with_no_primary_key'][:5]
            })

        if self.analysis_results['data_quality'].get('tables_with_no_indexes'):
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Performance',
                'issue': f"{len(self.analysis_results['data_quality']['tables_with_no_indexes'])} tables have no indexes",
                'recommendation': 'Create indexes on frequently queried columns to improve performance',
                'affected_tables': self.analysis_results['data_quality']['tables_with_no_indexes'][:5]
            })

        if self.analysis_results['data_quality'].get('columns_with_high_nulls'):
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Data Quality',
                'issue': f"{len(self.analysis_results['data_quality']['columns_with_high_nulls'])} columns have >50% null values",
                'recommendation': 'Review nullable columns and consider removing or populating sparse columns',
                'examples': self.analysis_results['data_quality']['columns_with_high_nulls'][:3]
            })

        # ML-based recommendations
        if self.analysis_results['patterns'].get('property_clusters'):
            if self.analysis_results['patterns']['property_clusters']['anomaly_percentage'] > 5:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Data Integrity',
                    'issue': f"{self.analysis_results['patterns']['property_clusters']['anomaly_percentage']:.1f}% of property records are anomalous",
                    'recommendation': 'Review anomalous records for data entry errors or unusual patterns',
                    'action': 'Run data validation scripts on identified anomalies'
                })

        self.analysis_results['recommendations'] = recommendations

        for rec in recommendations:
            print(f"  [{rec['priority']}] {rec['category']}: {rec['issue']}")

        return recommendations

    def save_report(self):
        """Save comprehensive analysis report"""

        # Save JSON report
        with open('supabase_analysis_output/analysis_report.json', 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)

        # Create markdown report
        with open('supabase_analysis_output/analysis_report.md', 'w') as f:
            f.write("# Supabase Database Deep Analysis Report\n\n")
            f.write(f"Generated: {self.analysis_results['timestamp']}\n\n")

            f.write("## Database Overview\n\n")
            f.write(f"- **Version**: {self.analysis_results['database_info'].get('version', 'N/A')}\n")
            f.write(f"- **Total Schemas**: {self.analysis_results['schema_analysis']['summary']['total_schemas']}\n")
            f.write(f"- **Total Tables**: {self.analysis_results['schema_analysis']['summary']['total_tables']}\n")
            f.write(f"- **Total Columns**: {self.analysis_results['schema_analysis']['summary']['total_columns']}\n")
            f.write(f"- **Total Indexes**: {self.analysis_results['schema_analysis']['summary']['total_indexes']}\n\n")

            f.write("## Key Findings\n\n")

            if self.analysis_results['data_quality']:
                f.write("### Data Quality Issues\n\n")
                for issue_type, issues in self.analysis_results['data_quality'].items():
                    if issues:
                        f.write(f"- **{issue_type.replace('_', ' ').title()}**: {len(issues)} found\n")
                f.write("\n")

            if self.analysis_results['patterns'].get('high_correlations'):
                f.write("### Discovered Patterns\n\n")
                f.write("**High Correlations Found:**\n")
                for corr in self.analysis_results['patterns']['high_correlations'][:5]:
                    f.write(f"- {corr['var1']} ↔ {corr['var2']}: {corr['correlation']}\n")
                f.write("\n")

            f.write("## Recommendations\n\n")
            for rec in self.analysis_results['recommendations']:
                f.write(f"### {rec['priority']} Priority: {rec['category']}\n")
                f.write(f"**Issue**: {rec['issue']}\n\n")
                f.write(f"**Recommendation**: {rec['recommendation']}\n\n")

        print(f"\n[SAVED] Reports saved to supabase_analysis_output/")

    def run_full_analysis(self):
        """Run complete database analysis"""
        print("="*80)
        print("STARTING SUPABASE DATABASE DEEP ANALYSIS")
        print("="*80)

        if not self.connect():
            return False

        self.analyze_schema()
        self.analyze_data_statistics()
        self.analyze_data_quality()
        self.detect_patterns_ml()
        self.generate_visualizations()
        self.generate_recommendations()
        self.save_report()

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print("\nCheck 'supabase_analysis_output' folder for detailed reports and visualizations")

        return True

if __name__ == "__main__":
    analyzer = SupabaseAnalyzer()
    analyzer.run_full_analysis()