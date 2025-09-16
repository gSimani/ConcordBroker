#!/usr/bin/env python3
"""
Advanced ML-Based Anomaly Detection System for Real Estate Data
Uses multiple algorithms to identify outliers and suspicious patterns
"""

import numpy as np
import pandas as pd
import psycopg2
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import LocalOutlierFactor
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import joblib
import json
import logging
from datetime import datetime
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)

class AnomalyDetectionSystem:
    def __init__(self):
        self.conn = None
        self.models = {}
        self.scalers = {}
        self.anomalies = {
            'property_value': [],
            'transaction': [],
            'geographic': [],
            'temporal': [],
            'combined': []
        }

    def connect(self):
        """Connect to database"""
        self.conn = psycopg2.connect(
            host="aws-1-us-east-1.pooler.supabase.com",
            port=6543,
            database="postgres",
            user="postgres.pmispwtdngkcmsrsjwbp",
            password="West@Boca613!",
            connect_timeout=10
        )
        logging.info("Connected to database")

    def load_property_data(self, limit: int = 50000) -> pd.DataFrame:
        """Load property data for analysis"""
        query = f"""
        SELECT
            id,
            parcel_id,
            county,
            just_value,
            land_value,
            building_value,
            total_living_area,
            year_built,
            bedrooms,
            bathrooms,
            land_sqft,
            sale_price,
            sale_date,
            EXTRACT(YEAR FROM sale_date) as sale_year,
            EXTRACT(MONTH FROM sale_date) as sale_month
        FROM public.florida_parcels
        WHERE just_value > 1000
            AND just_value < 100000000
            AND total_living_area > 100
            AND year_built > 1800
            AND year_built <= EXTRACT(YEAR FROM CURRENT_DATE)
        ORDER BY RANDOM()
        LIMIT {limit}
        """

        df = pd.read_sql(query, self.conn)
        logging.info(f"Loaded {len(df)} property records")
        return df

    def detect_value_anomalies(self, df: pd.DataFrame) -> np.ndarray:
        """Detect anomalies in property values using Isolation Forest"""
        logging.info("Detecting value anomalies...")

        # Features for value anomaly detection
        value_features = ['just_value', 'land_value', 'building_value', 'total_living_area']
        X = df[value_features].fillna(df[value_features].median())

        # Use RobustScaler for better handling of outliers
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['value'] = scaler

        # Isolation Forest
        iso_forest = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )
        anomalies = iso_forest.fit_predict(X_scaled)
        self.models['value_isolation'] = iso_forest

        # Local Outlier Factor
        lof = LocalOutlierFactor(n_neighbors=20, contamination=0.05)
        lof_anomalies = lof.fit_predict(X_scaled)

        # Combine both methods (anomaly if both agree)
        combined_anomalies = ((anomalies == -1) & (lof_anomalies == -1)).astype(int)

        # Store anomalous records
        anomaly_indices = df[combined_anomalies == 1].index
        self.anomalies['property_value'] = df.iloc[anomaly_indices]['id'].tolist()

        logging.info(f"Found {len(anomaly_indices)} value anomalies")
        return combined_anomalies

    def detect_transaction_anomalies(self, df: pd.DataFrame) -> np.ndarray:
        """Detect anomalies in sales transactions"""
        logging.info("Detecting transaction anomalies...")

        # Filter for properties with sales
        sales_df = df[df['sale_price'] > 0].copy()

        if len(sales_df) == 0:
            return np.zeros(len(df))

        # Calculate price ratios
        sales_df['price_to_value_ratio'] = sales_df['sale_price'] / sales_df['just_value']
        sales_df['price_per_sqft'] = sales_df['sale_price'] / sales_df['total_living_area']

        # Features for transaction analysis
        trans_features = ['sale_price', 'price_to_value_ratio', 'price_per_sqft', 'sale_year']
        X = sales_df[trans_features].fillna(sales_df[trans_features].median())

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # DBSCAN for density-based anomaly detection
        dbscan = DBSCAN(eps=0.5, min_samples=10)
        clusters = dbscan.fit_predict(X_scaled)

        # Outliers are labeled as -1
        anomalies = (clusters == -1).astype(int)

        # Map back to original dataframe
        result = np.zeros(len(df))
        result[sales_df.index] = anomalies

        anomaly_indices = sales_df[anomalies == 1].index
        self.anomalies['transaction'] = df.iloc[anomaly_indices]['id'].tolist()

        logging.info(f"Found {anomalies.sum()} transaction anomalies")
        return result

    def build_autoencoder(self, input_dim: int) -> keras.Model:
        """Build autoencoder for deep anomaly detection"""
        # Encoder
        encoder_input = layers.Input(shape=(input_dim,))
        x = layers.Dense(32, activation='relu')(encoder_input)
        x = layers.Dense(16, activation='relu')(x)
        encoder_output = layers.Dense(8, activation='relu')(x)

        # Decoder
        x = layers.Dense(16, activation='relu')(encoder_output)
        x = layers.Dense(32, activation='relu')(x)
        decoder_output = layers.Dense(input_dim, activation='linear')(x)

        # Model
        autoencoder = keras.Model(encoder_input, decoder_output)
        autoencoder.compile(optimizer='adam', loss='mse')

        return autoencoder

    def detect_deep_anomalies(self, df: pd.DataFrame) -> np.ndarray:
        """Use deep learning autoencoder for anomaly detection"""
        logging.info("Running deep anomaly detection...")

        # Prepare features
        features = ['just_value', 'land_value', 'building_value',
                   'total_living_area', 'year_built', 'bedrooms',
                   'bathrooms', 'land_sqft']

        X = df[features].fillna(df[features].median())

        # Scale data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Build and train autoencoder
        autoencoder = self.build_autoencoder(len(features))

        # Split data for training (use normal data)
        train_size = int(0.8 * len(X_scaled))
        X_train = X_scaled[:train_size]

        # Train autoencoder
        autoencoder.fit(
            X_train, X_train,
            epochs=50,
            batch_size=32,
            validation_split=0.1,
            verbose=0
        )

        # Predict and calculate reconstruction error
        predictions = autoencoder.predict(X_scaled, verbose=0)
        mse = np.mean(np.power(X_scaled - predictions, 2), axis=1)

        # Threshold for anomalies (95th percentile)
        threshold = np.percentile(mse, 95)
        anomalies = (mse > threshold).astype(int)

        self.models['autoencoder'] = autoencoder
        self.scalers['deep'] = scaler

        logging.info(f"Found {anomalies.sum()} deep anomalies")
        return anomalies

    def detect_geographic_clusters(self, df: pd.DataFrame) -> np.ndarray:
        """Detect geographic anomalies based on county patterns"""
        logging.info("Detecting geographic anomalies...")

        anomalies = np.zeros(len(df))

        # Analyze patterns by county
        for county in df['county'].unique():
            county_df = df[df['county'] == county]

            if len(county_df) < 10:
                continue

            # Calculate county statistics
            county_stats = {
                'median_value': county_df['just_value'].median(),
                'std_value': county_df['just_value'].std(),
                'median_size': county_df['total_living_area'].median()
            }

            # Flag properties that deviate significantly from county norms
            z_scores = np.abs((county_df['just_value'] - county_stats['median_value']) / county_stats['std_value'])
            county_anomalies = (z_scores > 3).values

            anomalies[county_df.index] = county_anomalies

        self.anomalies['geographic'] = df[anomalies == 1]['id'].tolist()
        logging.info(f"Found {anomalies.sum()} geographic anomalies")
        return anomalies

    def combine_anomaly_scores(self, *anomaly_arrays) -> Dict:
        """Combine multiple anomaly detection results"""
        logging.info("Combining anomaly scores...")

        # Stack all anomaly arrays
        combined = np.stack(anomaly_arrays, axis=1)

        # Calculate consensus score (how many methods agree)
        consensus_score = np.sum(combined, axis=1)

        # Classification based on consensus
        anomaly_classification = {
            'normal': (consensus_score == 0).sum(),
            'suspicious': (consensus_score == 1).sum(),
            'likely_anomaly': (consensus_score == 2).sum(),
            'definite_anomaly': (consensus_score >= 3).sum()
        }

        # Get indices of definite anomalies
        definite_anomalies = np.where(consensus_score >= 3)[0]

        return {
            'consensus_scores': consensus_score,
            'classification': anomaly_classification,
            'anomaly_indices': definite_anomalies.tolist()
        }

    def generate_anomaly_report(self, df: pd.DataFrame, results: Dict) -> Dict:
        """Generate detailed anomaly report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(df),
            'anomaly_summary': results['classification'],
            'anomaly_rate': round(results['classification']['definite_anomaly'] / len(df) * 100, 2),
            'anomaly_categories': {
                'property_value': len(self.anomalies['property_value']),
                'transaction': len(self.anomalies['transaction']),
                'geographic': len(self.anomalies['geographic'])
            }
        }

        # Get sample anomalies for investigation
        anomaly_indices = results['anomaly_indices'][:10]
        if anomaly_indices:
            sample_anomalies = df.iloc[anomaly_indices][
                ['id', 'parcel_id', 'county', 'just_value', 'sale_price']
            ].to_dict('records')
            report['sample_anomalies'] = sample_anomalies

        # Generate recommendations
        report['recommendations'] = self.generate_recommendations(results)

        return report

    def generate_recommendations(self, results: Dict) -> List[str]:
        """Generate actionable recommendations based on anomalies"""
        recommendations = []

        anomaly_rate = results['classification']['definite_anomaly'] / sum(results['classification'].values()) * 100

        if anomaly_rate > 10:
            recommendations.append("HIGH ALERT: Anomaly rate exceeds 10%. Immediate data review required.")
        elif anomaly_rate > 5:
            recommendations.append("MEDIUM ALERT: Elevated anomaly rate. Schedule data quality review.")
        else:
            recommendations.append("Low anomaly rate. Continue regular monitoring.")

        if len(self.anomalies['transaction']) > 100:
            recommendations.append("Review transaction anomalies for potential data entry errors or fraud.")

        if len(self.anomalies['geographic']) > 50:
            recommendations.append("Geographic clustering detected. Verify county-specific data accuracy.")

        return recommendations

    def save_models(self):
        """Save trained models for future use"""
        logging.info("Saving models...")

        # Save sklearn models
        for name, model in self.models.items():
            if name != 'autoencoder':
                joblib.dump(model, f'supabase_optimization/models/{name}_model.pkl')

        # Save scalers
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, f'supabase_optimization/models/{name}_scaler.pkl')

        # Save Keras model
        if 'autoencoder' in self.models:
            self.models['autoencoder'].save('supabase_optimization/models/autoencoder.h5')

        logging.info("Models saved successfully")

    def run_full_detection(self) -> Dict:
        """Run complete anomaly detection pipeline"""
        self.connect()

        try:
            # Load data
            df = self.load_property_data()

            # Run different anomaly detection methods
            value_anomalies = self.detect_value_anomalies(df)
            transaction_anomalies = self.detect_transaction_anomalies(df)
            geographic_anomalies = self.detect_geographic_clusters(df)
            deep_anomalies = self.detect_deep_anomalies(df)

            # Combine results
            combined_results = self.combine_anomaly_scores(
                value_anomalies,
                transaction_anomalies,
                geographic_anomalies,
                deep_anomalies
            )

            # Add combined anomalies to tracking
            self.anomalies['combined'] = df.iloc[combined_results['anomaly_indices']]['id'].tolist()

            # Generate report
            report = self.generate_anomaly_report(df, combined_results)

            # Save report
            with open('supabase_optimization/anomaly_report.json', 'w') as f:
                json.dump(report, f, indent=2, default=str)

            # Create visualization
            self.visualize_anomalies(df, combined_results)

            logging.info(f"Anomaly detection complete. Rate: {report['anomaly_rate']}%")
            return report

        finally:
            if self.conn:
                self.conn.close()

    def visualize_anomalies(self, df: pd.DataFrame, results: Dict):
        """Create visualizations of anomalies"""
        import matplotlib.pyplot as plt
        import seaborn as sns

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # 1. Anomaly distribution by consensus score
        ax1 = axes[0, 0]
        consensus_counts = pd.Series(results['consensus_scores']).value_counts().sort_index()
        ax1.bar(consensus_counts.index, consensus_counts.values, color='skyblue', edgecolor='navy')
        ax1.set_xlabel('Consensus Score')
        ax1.set_ylabel('Count')
        ax1.set_title('Anomaly Consensus Distribution')

        # 2. Property values: normal vs anomalous
        ax2 = axes[0, 1]
        anomaly_mask = results['consensus_scores'] >= 3
        normal_values = df[~anomaly_mask]['just_value']
        anomaly_values = df[anomaly_mask]['just_value']

        ax2.hist([normal_values, anomaly_values], label=['Normal', 'Anomaly'],
                bins=30, alpha=0.7, color=['green', 'red'])
        ax2.set_xlabel('Property Value')
        ax2.set_ylabel('Count')
        ax2.set_title('Value Distribution: Normal vs Anomalous')
        ax2.legend()
        ax2.set_xlim(0, 2000000)

        # 3. Geographic distribution of anomalies
        ax3 = axes[1, 0]
        county_anomalies = df[anomaly_mask]['county'].value_counts().head(10)
        ax3.barh(county_anomalies.index, county_anomalies.values, color='coral')
        ax3.set_xlabel('Number of Anomalies')
        ax3.set_ylabel('County')
        ax3.set_title('Top 10 Counties with Anomalies')

        # 4. Anomaly rate over time
        ax4 = axes[1, 1]
        if 'sale_year' in df.columns:
            yearly_data = df.groupby('sale_year').agg({
                'id': 'count'
            }).rename(columns={'id': 'total'})

            anomaly_df = df[anomaly_mask]
            if len(anomaly_df) > 0:
                yearly_anomalies = anomaly_df.groupby('sale_year').size()
                yearly_data['anomalies'] = yearly_anomalies
                yearly_data['anomaly_rate'] = (yearly_data['anomalies'] / yearly_data['total'] * 100).fillna(0)

                ax4.plot(yearly_data.index, yearly_data['anomaly_rate'], marker='o', color='purple')
                ax4.set_xlabel('Year')
                ax4.set_ylabel('Anomaly Rate (%)')
                ax4.set_title('Anomaly Rate Over Time')
                ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('supabase_optimization/anomaly_visualization.png', dpi=100, bbox_inches='tight')
        plt.close()

        logging.info("Anomaly visualizations saved")

if __name__ == "__main__":
    # Create necessary directories
    import os
    os.makedirs('supabase_optimization/models', exist_ok=True)

    # Run anomaly detection
    detector = AnomalyDetectionSystem()
    report = detector.run_full_detection()

    print("\n" + "="*60)
    print("ANOMALY DETECTION COMPLETE")
    print("="*60)
    print(f"Anomaly Rate: {report['anomaly_rate']}%")
    print(f"Total Anomalies: {report['anomaly_summary']['definite_anomaly']}")
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")