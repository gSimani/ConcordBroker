#!/usr/bin/env python3
"""
Advanced Property Valuation Prediction Model
Uses ensemble machine learning to predict property values with high accuracy
"""

import numpy as np
import pandas as pd
import psycopg2
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import (RandomForestRegressor, GradientBoostingRegressor,
                            ExtraTreesRegressor, VotingRegressor)
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.feature_selection import SelectKBest, f_regression
import xgboost as xgb
import lightgbm as lgb
import joblib
import json
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)

class PropertyValuationModel:
    def __init__(self):
        self.conn = None
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.best_model = None
        self.performance_metrics = {}

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

    def load_training_data(self, sample_size: int = 100000) -> pd.DataFrame:
        """Load and prepare training data"""
        logging.info(f"Loading {sample_size} property records for training...")

        query = f"""
        SELECT
            just_value as target,
            county,
            year,
            land_value,
            building_value,
            total_living_area,
            year_built,
            bedrooms,
            bathrooms,
            stories,
            units,
            land_sqft,
            property_use,
            phy_city,
            sale_price,
            EXTRACT(YEAR FROM sale_date) as sale_year,
            EXTRACT(MONTH FROM sale_date) as sale_month,
            CASE
                WHEN year_built > 0 THEN {datetime.now().year} - year_built
                ELSE NULL
            END as property_age,
            CASE
                WHEN total_living_area > 0 AND land_sqft > 0
                THEN total_living_area / land_sqft
                ELSE NULL
            END as coverage_ratio,
            CASE
                WHEN total_living_area > 0 AND bedrooms > 0
                THEN total_living_area / bedrooms
                ELSE NULL
            END as sqft_per_bedroom,
            CASE
                WHEN just_value > 0 AND total_living_area > 0
                THEN just_value / total_living_area
                ELSE NULL
            END as value_per_sqft
        FROM public.florida_parcels
        WHERE just_value > 10000
            AND just_value < 10000000
            AND total_living_area > 100
            AND total_living_area < 20000
            AND year_built > 1900
            AND year_built <= {datetime.now().year}
            AND bedrooms > 0
            AND bedrooms < 20
            AND bathrooms > 0
            AND bathrooms < 10
        ORDER BY RANDOM()
        LIMIT {sample_size}
        """

        df = pd.read_sql(query, self.conn)
        logging.info(f"Loaded {len(df)} valid property records")

        return df

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create additional features for better prediction"""
        logging.info("Engineering features...")

        # Location quality score (based on average values per city)
        city_avg = df.groupby('phy_city')['target'].mean()
        df['location_score'] = df['phy_city'].map(city_avg)

        # Property type features
        df['is_residential'] = df['property_use'].str.contains('RESIDENTIAL', na=False).astype(int)
        df['is_condo'] = df['property_use'].str.contains('CONDO', na=False).astype(int)
        df['is_single_family'] = df['property_use'].str.contains('SINGLE', na=False).astype(int)

        # Luxury indicators
        df['is_luxury'] = ((df['bedrooms'] >= 4) &
                          (df['bathrooms'] >= 3) &
                          (df['total_living_area'] > 3000)).astype(int)

        # Market timing features
        df['years_since_sale'] = df['year'] - df['sale_year']
        df['market_activity'] = df.groupby(['county', 'sale_year'])['target'].transform('count')

        # Quality indicators
        df['bathroom_ratio'] = df['bathrooms'] / df['bedrooms']
        df['land_to_building_ratio'] = df['land_value'] / (df['building_value'] + 1)

        # Age categories
        df['age_category'] = pd.cut(df['property_age'],
                                   bins=[0, 10, 25, 50, 100],
                                   labels=['New', 'Recent', 'Established', 'Old'])

        # Size categories
        df['size_category'] = pd.cut(df['total_living_area'],
                                    bins=[0, 1500, 2500, 4000, 20000],
                                    labels=['Small', 'Medium', 'Large', 'Mansion'])

        return df

    def prepare_features(self, df: pd.DataFrame) -> tuple:
        """Prepare features for training"""
        logging.info("Preparing features...")

        # Separate target
        y = df['target']

        # Select features
        feature_columns = [
            'land_value', 'building_value', 'total_living_area',
            'year_built', 'bedrooms', 'bathrooms', 'stories', 'units',
            'land_sqft', 'property_age', 'coverage_ratio',
            'sqft_per_bedroom', 'value_per_sqft', 'location_score',
            'is_residential', 'is_condo', 'is_single_family',
            'is_luxury', 'bathroom_ratio', 'land_to_building_ratio'
        ]

        # Handle categorical variables
        categorical_columns = ['county', 'age_category', 'size_category']

        # Encode categorical variables
        for col in categorical_columns:
            if col in df.columns:
                le = LabelEncoder()
                df[col + '_encoded'] = le.fit_transform(df[col].fillna('Unknown'))
                self.encoders[col] = le
                feature_columns.append(col + '_encoded')

        # Select final features
        X = df[feature_columns]

        # Fill missing values
        X = X.fillna(X.median())

        # Remove infinite values
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(X.median())

        logging.info(f"Prepared {X.shape[1]} features for {X.shape[0]} samples")

        return X, y

    def train_ensemble_model(self, X_train, y_train, X_val, y_val):
        """Train multiple models and create ensemble"""
        logging.info("Training ensemble models...")

        # 1. Random Forest
        logging.info("  Training Random Forest...")
        rf = RandomForestRegressor(
            n_estimators=100,
            max_depth=20,
            min_samples_split=10,
            min_samples_leaf=4,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        self.models['random_forest'] = rf

        # 2. Gradient Boosting
        logging.info("  Training Gradient Boosting...")
        gb = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=10,
            random_state=42
        )
        gb.fit(X_train, y_train)
        self.models['gradient_boosting'] = gb

        # 3. XGBoost
        logging.info("  Training XGBoost...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        xgb_model.fit(X_train, y_train)
        self.models['xgboost'] = xgb_model

        # 4. LightGBM
        logging.info("  Training LightGBM...")
        lgb_model = lgb.LGBMRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        lgb_model.fit(X_train, y_train)
        self.models['lightgbm'] = lgb_model

        # 5. Extra Trees
        logging.info("  Training Extra Trees...")
        et = ExtraTreesRegressor(
            n_estimators=100,
            max_depth=20,
            random_state=42,
            n_jobs=-1
        )
        et.fit(X_train, y_train)
        self.models['extra_trees'] = et

        # Create voting ensemble
        logging.info("  Creating ensemble model...")
        ensemble = VotingRegressor([
            ('rf', rf),
            ('gb', gb),
            ('xgb', xgb_model),
            ('lgb', lgb_model),
            ('et', et)
        ])
        ensemble.fit(X_train, y_train)
        self.models['ensemble'] = ensemble

        # Evaluate all models
        for name, model in self.models.items():
            y_pred = model.predict(X_val)
            mae = mean_absolute_error(y_val, y_pred)
            rmse = np.sqrt(mean_squared_error(y_val, y_pred))
            r2 = r2_score(y_val, y_pred)
            mape = np.mean(np.abs((y_val - y_pred) / y_val)) * 100

            self.performance_metrics[name] = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'mape': mape
            }

            logging.info(f"  {name}: MAE=${mae:,.0f}, R²={r2:.3f}, MAPE={mape:.1f}%")

        # Select best model
        best_model_name = min(self.performance_metrics,
                            key=lambda x: self.performance_metrics[x]['mae'])
        self.best_model = self.models[best_model_name]
        logging.info(f"Best model: {best_model_name}")

    def analyze_feature_importance(self, X_train):
        """Analyze and rank feature importance"""
        logging.info("Analyzing feature importance...")

        # Get feature names
        feature_names = X_train.columns.tolist()

        # Get importance from tree-based models
        for model_name in ['random_forest', 'gradient_boosting', 'extra_trees', 'xgboost', 'lightgbm']:
            if model_name in self.models:
                model = self.models[model_name]
                if hasattr(model, 'feature_importances_'):
                    importance = model.feature_importances_
                    self.feature_importance[model_name] = dict(zip(feature_names, importance))

        # Calculate average importance
        avg_importance = {}
        for feature in feature_names:
            importances = [self.feature_importance[m].get(feature, 0)
                         for m in self.feature_importance]
            avg_importance[feature] = np.mean(importances)

        # Sort by importance
        sorted_features = sorted(avg_importance.items(), key=lambda x: x[1], reverse=True)

        logging.info("Top 10 most important features:")
        for feature, importance in sorted_features[:10]:
            logging.info(f"  {feature}: {importance:.4f}")

        return sorted_features

    def predict_property_value(self, property_features: dict) -> dict:
        """Predict value for a single property"""
        # Prepare features
        df = pd.DataFrame([property_features])
        df = self.engineer_features(df)
        X, _ = self.prepare_features(df)

        # Scale features
        if 'features' in self.scalers:
            X = self.scalers['features'].transform(X)

        # Predict with all models
        predictions = {}
        for name, model in self.models.items():
            pred = model.predict(X)[0]
            predictions[name] = float(pred)

        # Get confidence interval (using std of predictions)
        pred_values = list(predictions.values())
        mean_prediction = np.mean(pred_values)
        std_prediction = np.std(pred_values)

        return {
            'predicted_value': float(mean_prediction),
            'confidence_interval': {
                'lower': float(mean_prediction - 2 * std_prediction),
                'upper': float(mean_prediction + 2 * std_prediction)
            },
            'model_predictions': predictions,
            'confidence': float(1 - (std_prediction / mean_prediction))
        }

    def generate_valuation_report(self, X_test, y_test):
        """Generate comprehensive valuation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'model_performance': self.performance_metrics,
            'best_model': min(self.performance_metrics,
                            key=lambda x: self.performance_metrics[x]['mae']),
            'feature_importance': {},
            'valuation_insights': {}
        }

        # Add feature importance
        sorted_features = self.analyze_feature_importance(X_test)
        report['feature_importance'] = dict(sorted_features[:20])

        # Generate insights
        best_metrics = self.performance_metrics[report['best_model']]
        report['valuation_insights'] = {
            'accuracy_rate': round(100 - best_metrics['mape'], 2),
            'average_error': round(best_metrics['mae']),
            'r_squared': round(best_metrics['r2'], 3),
            'key_factors': [f[0] for f in sorted_features[:5]],
            'confidence_level': 'High' if best_metrics['r2'] > 0.8 else 'Medium'
        }

        return report

    def save_models(self):
        """Save trained models and preprocessors"""
        logging.info("Saving models...")

        # Save models
        for name, model in self.models.items():
            joblib.dump(model, f'supabase_optimization/models/valuation_{name}.pkl')

        # Save scalers and encoders
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, f'supabase_optimization/models/scaler_{name}.pkl')

        for name, encoder in self.encoders.items():
            joblib.dump(encoder, f'supabase_optimization/models/encoder_{name}.pkl')

        # Save performance metrics
        with open('supabase_optimization/models/valuation_metrics.json', 'w') as f:
            json.dump(self.performance_metrics, f, indent=2)

        logging.info("Models saved successfully")

    def run_training_pipeline(self):
        """Run complete training pipeline"""
        self.connect()

        try:
            # Load data
            df = self.load_training_data()

            # Engineer features
            df = self.engineer_features(df)

            # Prepare features
            X, y = self.prepare_features(df)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            self.scalers['features'] = scaler

            # Train models
            self.train_ensemble_model(X_train_scaled, y_train,
                                    X_test_scaled, y_test)

            # Generate report
            report = self.generate_valuation_report(X_test, y_test)

            # Save report
            with open('supabase_optimization/valuation_report.json', 'w') as f:
                json.dump(report, f, indent=2, default=str)

            # Create summary
            self.create_summary_report(report)

            # Save models
            self.save_models()

            return report

        finally:
            if self.conn:
                self.conn.close()

    def create_summary_report(self, report):
        """Create markdown summary report"""
        with open('supabase_optimization/valuation_summary.md', 'w') as f:
            f.write("# Property Valuation Model Report\n\n")
            f.write(f"**Generated:** {report['timestamp']}\n\n")

            f.write("## Model Performance\n\n")
            best = report['best_model']
            metrics = report['model_performance'][best]
            f.write(f"**Best Model:** {best}\n\n")
            f.write(f"- **Accuracy Rate:** {report['valuation_insights']['accuracy_rate']}%\n")
            f.write(f"- **Average Error:** ${metrics['mae']:,.0f}\n")
            f.write(f"- **R² Score:** {metrics['r2']:.3f}\n")
            f.write(f"- **MAPE:** {metrics['mape']:.1f}%\n\n")

            f.write("## All Models Performance\n\n")
            f.write("| Model | MAE | R² | MAPE |\n")
            f.write("|-------|-----|-------|------|\n")
            for name, m in report['model_performance'].items():
                f.write(f"| {name} | ${m['mae']:,.0f} | {m['r2']:.3f} | {m['mape']:.1f}% |\n")

            f.write("\n## Key Value Drivers\n\n")
            f.write("Top factors influencing property values:\n\n")
            for i, (feature, importance) in enumerate(list(report['feature_importance'].items())[:10], 1):
                f.write(f"{i}. **{feature.replace('_', ' ').title()}** - {importance:.3f}\n")

            f.write("\n## Valuation Insights\n\n")
            f.write(f"- The model achieves **{report['valuation_insights']['accuracy_rate']}% accuracy**\n")
            f.write(f"- Average prediction error: **${report['valuation_insights']['average_error']:,.0f}**\n")
            f.write(f"- Confidence Level: **{report['valuation_insights']['confidence_level']}**\n")
            f.write(f"- Key factors: {', '.join(report['valuation_insights']['key_factors'])}\n")

        logging.info("Summary report saved")

if __name__ == "__main__":
    import os
    os.makedirs('supabase_optimization/models', exist_ok=True)

    # Train model
    model = PropertyValuationModel()
    report = model.run_training_pipeline()

    print("\n" + "="*60)
    print("PROPERTY VALUATION MODEL TRAINING COMPLETE")
    print("="*60)
    print(f"Best Model: {report['best_model']}")
    print(f"Accuracy: {report['valuation_insights']['accuracy_rate']}%")
    print(f"Average Error: ${report['valuation_insights']['average_error']:,.0f}")
    print(f"R² Score: {report['valuation_insights']['r_squared']}")
    print("\nModel saved and ready for predictions!")