#!/usr/bin/env python3
"""
Automated Data Quality Manager for Supabase
Identifies and fixes data quality issues using ML and statistical methods
"""

import psycopg2
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.impute import KNNImputer
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DataQualityManager:
    def __init__(self):
        self.conn = None
        self.issues_found = []
        self.fixes_applied = []
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'issues': [],
            'fixes': [],
            'statistics': {}
        }

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host="aws-1-us-east-1.pooler.supabase.com",
                port=6543,
                database="postgres",
                user="postgres.pmispwtdngkcmsrsjwbp",
                password="West@Boca613!",
                connect_timeout=10
            )
            logging.info("Connected to Supabase database")
            return True
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            return False

    def analyze_null_patterns(self, table_name: str = 'florida_parcels'):
        """Analyze null value patterns in the table"""
        logging.info(f"Analyzing null patterns in {table_name}...")

        query = f"""
        SELECT
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
            AND table_name = '{table_name}'
        ORDER BY ordinal_position
        """

        df_columns = pd.read_sql(query, self.conn)

        null_analysis = []

        for _, col in df_columns.iterrows():
            col_name = col['column_name']

            # Skip system columns
            if col_name in ['id', 'created_at', 'updated_at']:
                continue

            try:
                null_query = f"""
                SELECT
                    COUNT(*) as total,
                    COUNT({col_name}) as non_null,
                    COUNT(*) - COUNT({col_name}) as null_count,
                    (COUNT(*) - COUNT({col_name}))::float / COUNT(*) * 100 as null_percentage
                FROM public.{table_name}
                """

                df_nulls = pd.read_sql(null_query, self.conn)
                null_pct = df_nulls['null_percentage'].iloc[0]

                if null_pct > 20:  # Flag columns with >20% nulls
                    null_analysis.append({
                        'column': col_name,
                        'null_percentage': round(null_pct, 2),
                        'total_nulls': int(df_nulls['null_count'].iloc[0]),
                        'severity': 'HIGH' if null_pct > 50 else 'MEDIUM'
                    })

            except:
                continue

        self.report['issues'].append({
            'type': 'NULL_VALUES',
            'table': table_name,
            'columns_affected': len(null_analysis),
            'details': null_analysis[:10]  # Top 10 worst columns
        })

        logging.info(f"Found {len(null_analysis)} columns with significant null values")
        return null_analysis

    def detect_anomalies(self, table_name: str = 'florida_parcels'):
        """Detect anomalous records using Isolation Forest"""
        logging.info("Detecting anomalies in property data...")

        query = """
        SELECT
            id,
            just_value,
            land_value,
            building_value,
            total_living_area,
            year_built,
            bedrooms,
            bathrooms
        FROM public.florida_parcels
        WHERE just_value > 0
            AND just_value < 100000000
            AND total_living_area > 0
            AND year_built > 1800
            AND year_built < 2030
        LIMIT 10000
        """

        df = pd.read_sql(query, self.conn)

        # Prepare features
        features = ['just_value', 'land_value', 'building_value',
                   'total_living_area', 'year_built', 'bedrooms', 'bathrooms']

        X = df[features].fillna(df[features].median())

        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Detect anomalies
        iso_forest = IsolationForest(
            contamination=0.05,  # Expect 5% anomalies
            random_state=42
        )
        anomalies = iso_forest.fit_predict(X_scaled)

        # Identify anomalous records
        df['is_anomaly'] = anomalies == -1
        anomaly_ids = df[df['is_anomaly']]['id'].tolist()

        # Analyze anomaly patterns
        anomaly_stats = {
            'total_anomalies': len(anomaly_ids),
            'percentage': round(len(anomaly_ids) / len(df) * 100, 2),
            'anomaly_ids': anomaly_ids[:100]  # First 100 for review
        }

        # Find common characteristics of anomalies
        if len(anomaly_ids) > 0:
            anomaly_df = df[df['is_anomaly']]
            normal_df = df[~df['is_anomaly']]

            anomaly_patterns = {
                'avg_just_value_anomaly': float(anomaly_df['just_value'].mean()),
                'avg_just_value_normal': float(normal_df['just_value'].mean()),
                'avg_year_built_anomaly': float(anomaly_df['year_built'].mean()),
                'avg_year_built_normal': float(normal_df['year_built'].mean())
            }

            anomaly_stats['patterns'] = anomaly_patterns

        self.report['issues'].append({
            'type': 'ANOMALIES',
            'table': table_name,
            'statistics': anomaly_stats
        })

        logging.info(f"Detected {anomaly_stats['total_anomalies']} anomalous records")
        return anomaly_ids

    def check_data_consistency(self):
        """Check for data consistency issues"""
        logging.info("Checking data consistency...")

        consistency_issues = []

        # Check 1: Properties where building_value + land_value != just_value
        query = """
        SELECT COUNT(*) as count
        FROM public.florida_parcels
        WHERE just_value > 0
            AND land_value > 0
            AND building_value > 0
            AND ABS(just_value - (land_value + building_value)) > 1000
        """

        df = pd.read_sql(query, self.conn)
        inconsistent_values = df['count'].iloc[0]

        if inconsistent_values > 0:
            consistency_issues.append({
                'issue': 'Value calculations inconsistent',
                'description': 'just_value != land_value + building_value',
                'affected_records': int(inconsistent_values),
                'severity': 'MEDIUM'
            })

        # Check 2: Future dates
        query = """
        SELECT COUNT(*) as count
        FROM public.florida_parcels
        WHERE sale_date > CURRENT_DATE
            OR year_built > EXTRACT(YEAR FROM CURRENT_DATE)
        """

        df = pd.read_sql(query, self.conn)
        future_dates = df['count'].iloc[0]

        if future_dates > 0:
            consistency_issues.append({
                'issue': 'Future dates detected',
                'description': 'Sale dates or year built in the future',
                'affected_records': int(future_dates),
                'severity': 'HIGH'
            })

        # Check 3: Negative values
        query = """
        SELECT COUNT(*) as count
        FROM public.florida_parcels
        WHERE just_value < 0
            OR land_value < 0
            OR building_value < 0
            OR total_living_area < 0
        """

        df = pd.read_sql(query, self.conn)
        negative_values = df['count'].iloc[0]

        if negative_values > 0:
            consistency_issues.append({
                'issue': 'Negative values detected',
                'description': 'Property values or areas are negative',
                'affected_records': int(negative_values),
                'severity': 'HIGH'
            })

        self.report['issues'].append({
            'type': 'CONSISTENCY',
            'issues_found': len(consistency_issues),
            'details': consistency_issues
        })

        logging.info(f"Found {len(consistency_issues)} consistency issues")
        return consistency_issues

    def auto_fix_issues(self, dry_run: bool = True):
        """Automatically fix identified issues"""
        logging.info(f"Auto-fixing issues (dry_run={dry_run})...")

        fixes = []

        # Fix 1: Correct value calculations
        fix_query_1 = """
        UPDATE public.florida_parcels
        SET building_value = just_value - land_value
        WHERE just_value > 0
            AND land_value > 0
            AND building_value = 0
            AND just_value > land_value
        """

        if not dry_run:
            cursor = self.conn.cursor()
            cursor.execute(fix_query_1)
            affected = cursor.rowcount
            cursor.close()
            self.conn.commit()
        else:
            affected = "DRY RUN - Not executed"

        fixes.append({
            'fix': 'Calculate missing building values',
            'query': fix_query_1,
            'affected_rows': affected
        })

        # Fix 2: Standardize NULL addresses
        fix_query_2 = """
        UPDATE public.florida_parcels
        SET owner_addr1 = 'ADDRESS UNKNOWN'
        WHERE owner_addr1 IS NULL
            AND owner_name IS NOT NULL
        """

        if not dry_run:
            cursor = self.conn.cursor()
            cursor.execute(fix_query_2)
            affected = cursor.rowcount
            cursor.close()
            self.conn.commit()
        else:
            affected = "DRY RUN - Not executed"

        fixes.append({
            'fix': 'Standardize NULL addresses',
            'query': fix_query_2,
            'affected_rows': affected
        })

        # Fix 3: Remove future dates
        fix_query_3 = """
        UPDATE public.florida_parcels
        SET sale_date = NULL
        WHERE sale_date > CURRENT_DATE
        """

        if not dry_run:
            cursor = self.conn.cursor()
            cursor.execute(fix_query_3)
            affected = cursor.rowcount
            cursor.close()
            self.conn.commit()
        else:
            affected = "DRY RUN - Not executed"

        fixes.append({
            'fix': 'Remove future sale dates',
            'query': fix_query_3,
            'affected_rows': affected
        })

        self.report['fixes'] = fixes
        logging.info(f"Applied {len(fixes)} fixes")
        return fixes

    def generate_quality_score(self):
        """Generate overall data quality score"""
        logging.info("Calculating data quality score...")

        scores = []

        # Score 1: Completeness
        query = """
        SELECT
            AVG(CASE WHEN owner_name IS NOT NULL THEN 1 ELSE 0 END) * 100 as owner_completeness,
            AVG(CASE WHEN property_address IS NOT NULL THEN 1 ELSE 0 END) * 100 as address_completeness,
            AVG(CASE WHEN year_built IS NOT NULL THEN 1 ELSE 0 END) * 100 as year_completeness
        FROM public.florida_parcels
        """

        df = pd.read_sql(query, self.conn)
        completeness_score = df.mean().mean()
        scores.append(('Completeness', completeness_score))

        # Score 2: Consistency
        consistency_issues = len(self.check_data_consistency())
        consistency_score = max(0, 100 - (consistency_issues * 10))
        scores.append(('Consistency', consistency_score))

        # Score 3: Validity (based on anomaly rate)
        anomaly_rate = len(self.detect_anomalies()) / 10000 * 100  # Sample of 10000
        validity_score = max(0, 100 - (anomaly_rate * 10))
        scores.append(('Validity', validity_score))

        # Calculate overall score
        overall_score = np.mean([score for _, score in scores])

        quality_report = {
            'overall_score': round(overall_score, 2),
            'category_scores': {name: round(score, 2) for name, score in scores},
            'grade': self._get_grade(overall_score),
            'recommendation': self._get_recommendation(overall_score)
        }

        self.report['statistics'] = quality_report
        logging.info(f"Data Quality Score: {quality_report['overall_score']}% ({quality_report['grade']})")

        return quality_report

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on score"""
        if score >= 90:
            return "Excellent data quality. Minor improvements possible."
        elif score >= 80:
            return "Good data quality. Focus on completeness improvements."
        elif score >= 70:
            return "Acceptable data quality. Address consistency issues."
        elif score >= 60:
            return "Poor data quality. Significant cleanup required."
        else:
            return "Critical data quality issues. Immediate action required."

    def save_report(self):
        """Save quality report to file"""
        with open('supabase_optimization/data_quality_report.json', 'w') as f:
            json.dump(self.report, f, indent=2, default=str)

        # Create markdown summary
        with open('supabase_optimization/data_quality_summary.md', 'w') as f:
            f.write("# Data Quality Report\n\n")
            f.write(f"**Generated:** {self.report['timestamp']}\n\n")

            if 'statistics' in self.report:
                stats = self.report['statistics']
                f.write(f"## Overall Score: {stats['overall_score']}% ({stats['grade']})\n\n")
                f.write(f"**Recommendation:** {stats['recommendation']}\n\n")

                f.write("### Category Scores\n")
                for category, score in stats['category_scores'].items():
                    f.write(f"- {category}: {score}%\n")

            f.write("\n## Issues Found\n")
            for issue in self.report['issues']:
                f.write(f"- **{issue['type']}**: {issue.get('columns_affected', 'N/A')} affected\n")

            if self.report.get('fixes'):
                f.write("\n## Fixes Applied\n")
                for fix in self.report['fixes']:
                    f.write(f"- {fix['fix']}: {fix['affected_rows']} rows\n")

        logging.info("Report saved to data_quality_report.json and data_quality_summary.md")

    def run_full_analysis(self, apply_fixes: bool = False):
        """Run complete data quality analysis"""
        if not self.connect():
            return False

        try:
            # Run analyses
            self.analyze_null_patterns()
            self.detect_anomalies()
            self.check_data_consistency()

            # Apply fixes if requested
            if apply_fixes:
                self.auto_fix_issues(dry_run=False)
            else:
                self.auto_fix_issues(dry_run=True)

            # Generate quality score
            self.generate_quality_score()

            # Save report
            self.save_report()

            return True

        except Exception as e:
            logging.error(f"Analysis failed: {e}")
            return False

        finally:
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    manager = DataQualityManager()
    manager.run_full_analysis(apply_fixes=False)  # Set to True to apply fixes