#!/usr/bin/env python3
"""
Complete Supabase Database Deep Analysis
Uses Python data science tools to comprehensively analyze the database
"""

import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class SupabaseDeepAnalyzer:
    def __init__(self):
        self.conn = None
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'database_info': {},
            'schema_analysis': {},
            'table_statistics': {},
            'data_quality': {},
            'ml_insights': {},
            'recommendations': []
        }

    def connect(self):
        """Establish database connection"""
        print("\n" + "="*80)
        print("CONNECTING TO SUPABASE DATABASE")
        print("="*80)

        try:
            self.conn = psycopg2.connect(
                host="aws-1-us-east-1.pooler.supabase.com",
                port=6543,
                database="postgres",
                user="postgres.pmispwtdngkcmsrsjwbp",
                password="West@Boca613!",
                connect_timeout=10
            )

            cursor = self.conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.close()

            self.results['database_info']['version'] = version
            print(f"[SUCCESS] Connected to PostgreSQL")
            print(f"  Version: {version[:60]}...")

            return True

        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False

    def analyze_schema(self):
        """Analyze database schema and structure"""
        print("\n" + "="*80)
        print("SCHEMA ANALYSIS")
        print("="*80)

        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get all schemas
        cursor.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """)
        schemas = [row['schema_name'] for row in cursor.fetchall()]
        print(f"  Active Schemas: {', '.join(schemas)}")

        # Analyze tables per schema
        table_analysis = {}
        total_tables = 0
        total_columns = 0

        for schema in schemas:
            cursor.execute("""
                SELECT
                    t.table_name,
                    COUNT(c.column_name) as column_count,
                    pg_relation_size(quote_ident(t.table_schema)||'.'||quote_ident(t.table_name)) as size_bytes
                FROM information_schema.tables t
                JOIN information_schema.columns c
                    ON t.table_schema = c.table_schema
                    AND t.table_name = c.table_name
                WHERE t.table_schema = %s
                    AND t.table_type = 'BASE TABLE'
                GROUP BY t.table_schema, t.table_name
                ORDER BY size_bytes DESC
                LIMIT 20
            """, (schema,))

            tables = cursor.fetchall()
            table_analysis[schema] = tables
            total_tables += len(tables)
            total_columns += sum(t['column_count'] for t in tables)

        self.results['schema_analysis'] = {
            'schemas': schemas,
            'total_tables': total_tables,
            'total_columns': total_columns,
            'table_details': table_analysis
        }

        print(f"  Total Tables: {total_tables}")
        print(f"  Total Columns: {total_columns}")

        # Find largest tables
        cursor.execute("""
            SELECT
                schemaname || '.' || tablename as full_table_name,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY pg_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 5
        """)

        largest_tables = cursor.fetchall()
        print("\n  Top 5 Largest Tables:")
        for table in largest_tables:
            print(f"    - {table['full_table_name']}: {table['size']}")

        cursor.close()

    def analyze_data_statistics(self):
        """Perform statistical analysis on key tables"""
        print("\n" + "="*80)
        print("DATA STATISTICS ANALYSIS")
        print("="*80)

        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Analyze florida_parcels if exists
        try:
            print("\n  Analyzing florida_parcels table...")

            cursor.execute("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT county) as unique_counties,
                    COUNT(DISTINCT year) as unique_years,
                    AVG(just_value) as avg_property_value,
                    STDDEV(just_value) as stddev_property_value,
                    MIN(just_value) as min_property_value,
                    MAX(just_value) as max_property_value,
                    AVG(total_living_area) as avg_living_area,
                    AVG(year_built) as avg_year_built,
                    SUM(CASE WHEN just_value IS NULL THEN 1 ELSE 0 END) as null_values,
                    SUM(CASE WHEN land_value > 0 THEN 1 ELSE 0 END) as properties_with_land_value
                FROM public.florida_parcels
                WHERE just_value > 0 AND just_value < 100000000
            """)

            stats = cursor.fetchone()

            if stats:
                self.results['table_statistics']['florida_parcels'] = dict(stats)

                print(f"    Total Records: {stats['total_records']:,}")
                print(f"    Unique Counties: {stats['unique_counties']}")
                print(f"    Average Property Value: ${stats['avg_property_value']:,.0f}" if stats['avg_property_value'] else "N/A")
                print(f"    Std Dev Property Value: ${stats['stddev_property_value']:,.0f}" if stats['stddev_property_value'] else "N/A")
                print(f"    Value Range: ${stats['min_property_value']:,.0f} - ${stats['max_property_value']:,.0f}")

        except Exception as e:
            print(f"    [WARNING] Could not analyze florida_parcels: {str(e)[:50]}")

        # Analyze other important tables
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
                AND tablename IN ('sunbiz_entities', 'tax_deed_sales', 'building_permits')
        """)

        for row in cursor.fetchall():
            table = row['tablename']
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM public.{table}")
                count = cursor.fetchone()['count']
                print(f"    {table}: {count:,} records")
                self.results['table_statistics'][table] = {'record_count': count}
            except:
                continue

        cursor.close()

    def analyze_data_quality(self):
        """Analyze data quality issues"""
        print("\n" + "="*80)
        print("DATA QUALITY ANALYSIS")
        print("="*80)

        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        quality_issues = []

        # Check for tables without primary keys
        cursor.execute("""
            SELECT t.table_name
            FROM information_schema.tables t
            LEFT JOIN information_schema.table_constraints tc
                ON t.table_name = tc.table_name
                AND t.table_schema = tc.table_schema
                AND tc.constraint_type = 'PRIMARY KEY'
            WHERE t.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
                AND tc.constraint_name IS NULL
        """)

        tables_no_pk = [row['table_name'] for row in cursor.fetchall()]
        if tables_no_pk:
            quality_issues.append({
                'type': 'MISSING_PRIMARY_KEY',
                'severity': 'HIGH',
                'tables': tables_no_pk[:10],
                'count': len(tables_no_pk)
            })
            print(f"  [HIGH] {len(tables_no_pk)} tables without primary keys")

        # Check for tables without indexes
        cursor.execute("""
            SELECT DISTINCT t.tablename
            FROM pg_tables t
            LEFT JOIN pg_indexes i ON t.tablename = i.tablename AND t.schemaname = i.schemaname
            WHERE t.schemaname = 'public'
                AND i.indexname IS NULL
        """)

        tables_no_index = [row['tablename'] for row in cursor.fetchall()]
        if tables_no_index:
            quality_issues.append({
                'type': 'NO_INDEXES',
                'severity': 'MEDIUM',
                'tables': tables_no_index[:10],
                'count': len(tables_no_index)
            })
            print(f"  [MEDIUM] {len(tables_no_index)} tables without any indexes")

        # Check for columns with high null percentage in florida_parcels
        try:
            cursor.execute("""
                SELECT
                    'owner_name' as column_name,
                    COUNT(*) - COUNT(owner_name) as null_count,
                    (COUNT(*) - COUNT(owner_name))::float / COUNT(*) * 100 as null_percentage
                FROM public.florida_parcels
                UNION ALL
                SELECT
                    'property_address',
                    COUNT(*) - COUNT(property_address),
                    (COUNT(*) - COUNT(property_address))::float / COUNT(*) * 100
                FROM public.florida_parcels
                UNION ALL
                SELECT
                    'year_built',
                    COUNT(*) - COUNT(year_built),
                    (COUNT(*) - COUNT(year_built))::float / COUNT(*) * 100
                FROM public.florida_parcels
            """)

            high_null_columns = []
            for row in cursor.fetchall():
                if row['null_percentage'] > 50:
                    high_null_columns.append({
                        'column': row['column_name'],
                        'null_percentage': round(row['null_percentage'], 2)
                    })

            if high_null_columns:
                quality_issues.append({
                    'type': 'HIGH_NULL_COLUMNS',
                    'severity': 'MEDIUM',
                    'columns': high_null_columns
                })
                print(f"  [MEDIUM] {len(high_null_columns)} columns with >50% null values")

        except:
            pass

        self.results['data_quality'] = quality_issues
        cursor.close()

    def perform_ml_analysis(self):
        """Use machine learning to find patterns and anomalies"""
        print("\n" + "="*80)
        print("MACHINE LEARNING ANALYSIS")
        print("="*80)

        cursor = self.conn.cursor()

        try:
            print("  Loading property data for ML analysis...")

            # Load sample data
            query = """
                SELECT
                    just_value,
                    land_value,
                    building_value,
                    total_living_area,
                    year_built,
                    bedrooms,
                    bathrooms
                FROM public.florida_parcels
                WHERE just_value > 10000
                    AND just_value < 10000000
                    AND total_living_area > 0
                    AND year_built > 1900
                    AND bedrooms > 0
                LIMIT 5000
            """

            df = pd.read_sql(query, self.conn)
            print(f"    Loaded {len(df)} property records")

            # Prepare data
            df = df.dropna()
            X = df.values

            # Standardize
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # PCA Analysis
            print("  Performing PCA...")
            pca = PCA(n_components=3)
            X_pca = pca.fit_transform(X_scaled)
            variance_explained = pca.explained_variance_ratio_

            print(f"    Variance explained by first 3 components: {variance_explained.sum():.2%}")

            # KMeans Clustering
            print("  Performing clustering...")
            kmeans = KMeans(n_clusters=4, random_state=42)
            clusters = kmeans.fit_predict(X_scaled)

            cluster_sizes = pd.Series(clusters).value_counts().sort_index()
            print(f"    Found {len(cluster_sizes)} property clusters")
            for i, size in cluster_sizes.items():
                print(f"      Cluster {i}: {size} properties")

            # Anomaly Detection
            print("  Detecting anomalies...")
            iso_forest = IsolationForest(contamination=0.05, random_state=42)
            anomalies = iso_forest.fit_predict(X_scaled)

            n_anomalies = (anomalies == -1).sum()
            print(f"    Detected {n_anomalies} anomalous properties ({n_anomalies/len(df)*100:.1f}%)")

            # Find correlations
            correlations = df.corr()
            high_corr = []
            for i in range(len(correlations.columns)):
                for j in range(i+1, len(correlations.columns)):
                    if abs(correlations.iloc[i, j]) > 0.7:
                        high_corr.append({
                            'var1': correlations.columns[i],
                            'var2': correlations.columns[j],
                            'correlation': round(correlations.iloc[i, j], 3)
                        })

            if high_corr:
                print(f"    Found {len(high_corr)} high correlations (>0.7)")
                for corr in high_corr[:3]:
                    print(f"      {corr['var1']} <-> {corr['var2']}: {corr['correlation']}")

            self.results['ml_insights'] = {
                'pca_variance': variance_explained.tolist(),
                'cluster_sizes': cluster_sizes.to_dict(),
                'anomaly_percentage': round(n_anomalies/len(df)*100, 2),
                'high_correlations': high_corr
            }

        except Exception as e:
            print(f"  [WARNING] ML analysis failed: {str(e)[:100]}")

        cursor.close()

    def generate_visualizations(self):
        """Create data visualizations"""
        print("\n" + "="*80)
        print("GENERATING VISUALIZATIONS")
        print("="*80)

        os.makedirs('supabase_analysis_output', exist_ok=True)

        # 1. Table size distribution
        if self.results['schema_analysis'].get('table_details'):
            plt.figure(figsize=(12, 6))

            public_tables = self.results['schema_analysis']['table_details'].get('public', [])
            if public_tables:
                table_names = [t['table_name'] for t in public_tables[:10]]
                column_counts = [t['column_count'] for t in public_tables[:10]]

                plt.bar(table_names, column_counts, color='skyblue', edgecolor='navy')
                plt.xlabel('Table Name')
                plt.ylabel('Number of Columns')
                plt.title('Database Table Complexity (Top 10 Tables)')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig('supabase_analysis_output/table_complexity.png', dpi=100)
                plt.close()
                print("  Created: table_complexity.png")

        # 2. Data quality summary
        if self.results['data_quality']:
            quality_counts = {}
            for issue in self.results['data_quality']:
                quality_counts[issue['severity']] = quality_counts.get(issue['severity'], 0) + issue.get('count', 1)

            if quality_counts:
                plt.figure(figsize=(8, 6))
                colors = {'HIGH': 'red', 'MEDIUM': 'orange', 'LOW': 'yellow'}
                bars = plt.bar(quality_counts.keys(), quality_counts.values(),
                             color=[colors.get(k, 'gray') for k in quality_counts.keys()])
                plt.xlabel('Severity')
                plt.ylabel('Number of Issues')
                plt.title('Data Quality Issues by Severity')

                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom')

                plt.tight_layout()
                plt.savefig('supabase_analysis_output/data_quality.png', dpi=100)
                plt.close()
                print("  Created: data_quality.png")

        # 3. ML insights visualization
        if self.results['ml_insights'].get('cluster_sizes'):
            plt.figure(figsize=(10, 6))

            clusters = self.results['ml_insights']['cluster_sizes']
            plt.pie(clusters.values(), labels=[f'Cluster {k}' for k in clusters.keys()],
                   autopct='%1.1f%%', startangle=90)
            plt.title('Property Clustering Distribution')
            plt.axis('equal')
            plt.savefig('supabase_analysis_output/clustering.png', dpi=100)
            plt.close()
            print("  Created: clustering.png")

    def generate_recommendations(self):
        """Generate actionable recommendations"""
        print("\n" + "="*80)
        print("GENERATING RECOMMENDATIONS")
        print("="*80)

        recommendations = []

        # Schema recommendations
        for issue in self.results.get('data_quality', []):
            if issue['type'] == 'MISSING_PRIMARY_KEY':
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Database Integrity',
                    'issue': f"{issue['count']} tables lack primary keys",
                    'recommendation': 'Add primary keys to ensure data integrity and improve query performance',
                    'impact': 'Critical for data consistency and performance',
                    'example_tables': issue['tables'][:3]
                })

            elif issue['type'] == 'NO_INDEXES':
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Performance',
                    'issue': f"{issue['count']} tables have no indexes",
                    'recommendation': 'Create indexes on frequently queried columns',
                    'impact': 'Can improve query performance by 10-100x',
                    'example_tables': issue['tables'][:3]
                })

        # ML-based recommendations
        if self.results.get('ml_insights'):
            if self.results['ml_insights'].get('anomaly_percentage', 0) > 3:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Data Quality',
                    'issue': f"{self.results['ml_insights']['anomaly_percentage']}% of properties are anomalous",
                    'recommendation': 'Review anomalous records for data entry errors',
                    'impact': 'Improves data reliability for analytics'
                })

        self.results['recommendations'] = recommendations

        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. [{rec['priority']}] {rec['category']}: {rec['issue']}")

    def save_report(self):
        """Save comprehensive analysis report"""
        print("\n" + "="*80)
        print("SAVING REPORTS")
        print("="*80)

        os.makedirs('supabase_analysis_output', exist_ok=True)

        # Save JSON report
        with open('supabase_analysis_output/deep_analysis.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        # Create markdown report
        with open('supabase_analysis_output/analysis_report.md', 'w') as f:
            f.write("# Supabase Database Deep Analysis Report\n\n")
            f.write(f"**Generated:** {self.results['timestamp']}\n\n")

            f.write("## Executive Summary\n\n")
            f.write(f"- **Database:** PostgreSQL {self.results['database_info'].get('version', 'N/A')[:30]}...\n")
            f.write(f"- **Total Schemas:** {len(self.results['schema_analysis'].get('schemas', []))}\n")
            f.write(f"- **Total Tables:** {self.results['schema_analysis'].get('total_tables', 0)}\n")
            f.write(f"- **Total Columns:** {self.results['schema_analysis'].get('total_columns', 0)}\n\n")

            if self.results.get('table_statistics', {}).get('florida_parcels'):
                stats = self.results['table_statistics']['florida_parcels']
                f.write("## Property Data Overview\n\n")
                f.write(f"- **Total Properties:** {stats.get('total_records', 0):,}\n")
                f.write(f"- **Counties Covered:** {stats.get('unique_counties', 0)}\n")
                f.write(f"- **Average Property Value:** ${stats.get('avg_property_value', 0):,.0f}\n\n")

            f.write("## Data Quality Issues\n\n")
            for issue in self.results.get('data_quality', []):
                f.write(f"- **{issue['severity']}:** {issue['type'].replace('_', ' ').title()}")
                if 'count' in issue:
                    f.write(f" ({issue['count']} instances)")
                f.write("\n")

            if self.results.get('ml_insights'):
                f.write("\n## Machine Learning Insights\n\n")
                insights = self.results['ml_insights']
                if 'cluster_sizes' in insights:
                    f.write(f"- **Property Clusters:** {len(insights['cluster_sizes'])} distinct groups identified\n")
                if 'anomaly_percentage' in insights:
                    f.write(f"- **Anomaly Rate:** {insights['anomaly_percentage']}% of properties are outliers\n")
                if 'high_correlations' in insights and insights['high_correlations']:
                    f.write("- **Key Correlations:**\n")
                    for corr in insights['high_correlations'][:3]:
                        f.write(f"  - {corr['var1']} ↔ {corr['var2']}: {corr['correlation']}\n")

            f.write("\n## Recommendations\n\n")
            for i, rec in enumerate(self.results.get('recommendations', []), 1):
                f.write(f"### {i}. {rec['category']}\n")
                f.write(f"**Priority:** {rec['priority']}\n\n")
                f.write(f"**Issue:** {rec['issue']}\n\n")
                f.write(f"**Recommendation:** {rec['recommendation']}\n\n")
                f.write(f"**Impact:** {rec.get('impact', 'N/A')}\n\n")

        print("  Saved: deep_analysis.json")
        print("  Saved: analysis_report.md")

    def run_complete_analysis(self):
        """Run complete database analysis"""
        print("="*80)
        print("SUPABASE DATABASE DEEP ANALYSIS")
        print("="*80)

        if not self.connect():
            return False

        try:
            self.analyze_schema()
            self.analyze_data_statistics()
            self.analyze_data_quality()
            self.perform_ml_analysis()
            self.generate_visualizations()
            self.generate_recommendations()
            self.save_report()

            print("\n" + "="*80)
            print("ANALYSIS COMPLETE")
            print("="*80)
            print("\nReports saved to: supabase_analysis_output/")
            print("  - deep_analysis.json (detailed data)")
            print("  - analysis_report.md (summary report)")
            print("  - *.png (visualizations)")

            return True

        except Exception as e:
            print(f"\n[ERROR] Analysis failed: {e}")
            return False

        finally:
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    analyzer = SupabaseDeepAnalyzer()
    analyzer.run_complete_analysis()