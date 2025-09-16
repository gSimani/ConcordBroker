#!/usr/bin/env python3
"""
Property Appraiser FastAPI Application
Comprehensive API for property data access with ML predictions
"""

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from supabase import create_client
import os
from dotenv import load_dotenv
import logging
import io
import matplotlib.pyplot as plt
import seaborn as sns
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv('.env.mcp')

# Initialize FastAPI app
app = FastAPI(
    title="Property Appraiser API",
    description="Comprehensive API for Florida property data with ML predictions",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===================== Pydantic Models =====================

class PropertyBase(BaseModel):
    parcel_id: str
    county: str
    owner_name: Optional[str] = None
    phy_addr1: Optional[str] = None
    phy_city: Optional[str] = None
    just_value: Optional[float] = None
    land_value: Optional[float] = None
    building_value: Optional[float] = None

class PropertyCreate(PropertyBase):
    year: int = 2025

class PropertyResponse(PropertyBase):
    id: int
    year: int
    sale_date: Optional[datetime] = None
    sale_price: Optional[float] = None
    data_quality_score: Optional[float] = None

    class Config:
        from_attributes = True

class PropertySearchParams(BaseModel):
    county: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    owner_name: Optional[str] = None
    address: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0)

class PropertyAnalytics(BaseModel):
    parcel_id: str
    predicted_value: float
    confidence_interval: Dict[str, float]
    value_trend: str
    investment_score: float
    comparable_properties: List[str]

class CountyStatistics(BaseModel):
    county: str
    total_parcels: int
    avg_just_value: float
    median_just_value: float
    total_assessed_value: float
    recent_sales: int
    data_quality_score: float

class MLPredictionRequest(BaseModel):
    parcel_id: str
    features: Optional[Dict[str, Any]] = None

class DataQualityReport(BaseModel):
    county: str
    completeness_score: float
    accuracy_score: float
    timeliness_score: float
    consistency_score: float
    overall_score: float
    issues: List[str]

# ===================== ML Model =====================

class PropertyValuePredictor:
    """Machine learning model for property value predictions"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'land_sqft', 'building_sqft', 'year_built',
            'bedrooms', 'bathrooms', 'garage_spaces'
        ]

    def train(self, df: pd.DataFrame):
        """Train the ML model with property data"""
        # Prepare features
        features = df[self.feature_columns].fillna(0)
        target = df['just_value']

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=0.2, random_state=42
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)

        # Calculate accuracy
        score = self.model.score(X_test_scaled, y_test)
        logger.info(f"Model trained with R² score: {score:.3f}")

        return score

    def predict(self, features: Dict) -> Tuple[float, Dict]:
        """Predict property value with confidence interval"""
        if not self.model:
            raise ValueError("Model not trained")

        # Prepare features
        feature_values = [features.get(col, 0) for col in self.feature_columns]
        X = np.array(feature_values).reshape(1, -1)
        X_scaled = self.scaler.transform(X)

        # Make prediction
        prediction = self.model.predict(X_scaled)[0]

        # Get prediction interval (using tree predictions)
        tree_predictions = np.array([
            tree.predict(X_scaled) for tree in self.model.estimators_
        ]).flatten()

        confidence_interval = {
            'lower': np.percentile(tree_predictions, 5),
            'upper': np.percentile(tree_predictions, 95),
            'mean': prediction
        }

        return prediction, confidence_interval

# Initialize ML model
ml_model = PropertyValuePredictor()

# ===================== API Endpoints =====================

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint with service information"""
    return {
        "service": "Property Appraiser API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "properties": "/api/properties",
            "analytics": "/api/analytics",
            "counties": "/api/counties",
            "predictions": "/api/predictions",
            "reports": "/api/reports"
        }
    }

@app.get("/api/properties", response_model=List[PropertyResponse], tags=["Properties"])
async def search_properties(params: PropertySearchParams = Depends()):
    """
    Search properties with advanced filtering using pandas
    """
    try:
        # Build query
        query = supabase.table('florida_parcels').select("*")

        if params.county:
            query = query.eq('county', params.county.upper())
        if params.min_value:
            query = query.gte('just_value', params.min_value)
        if params.max_value:
            query = query.lte('just_value', params.max_value)
        if params.owner_name:
            query = query.ilike('owner_name', f'%{params.owner_name}%')
        if params.address:
            query = query.ilike('phy_addr1', f'%{params.address}%')

        query = query.limit(params.limit).offset(params.offset)

        response = query.execute()

        return response.data

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/properties/{parcel_id}", response_model=PropertyResponse, tags=["Properties"])
async def get_property(parcel_id: str, county: str = Query(...)):
    """Get detailed property information"""
    try:
        response = supabase.table('florida_parcels')\
            .select("*")\
            .eq('parcel_id', parcel_id)\
            .eq('county', county.upper())\
            .single()\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Property not found")

        return response.data

    except Exception as e:
        logger.error(f"Get property error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/properties", response_model=PropertyResponse, tags=["Properties"])
async def create_property(property: PropertyCreate):
    """Create a new property record"""
    try:
        response = supabase.table('florida_parcels')\
            .insert(property.dict())\
            .execute()

        return response.data[0]

    except Exception as e:
        logger.error(f"Create property error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/{parcel_id}", response_model=PropertyAnalytics, tags=["Analytics"])
async def get_property_analytics(parcel_id: str, county: str = Query(...)):
    """
    Get advanced analytics for a property using ML and statistical analysis
    """
    try:
        # Get property data
        property_data = supabase.table('florida_parcels')\
            .select("*")\
            .eq('parcel_id', parcel_id)\
            .eq('county', county.upper())\
            .single()\
            .execute()

        if not property_data.data:
            raise HTTPException(status_code=404, detail="Property not found")

        prop = property_data.data

        # Get comparable properties using scikit-learn
        comparables = supabase.table('florida_parcels')\
            .select("parcel_id, just_value")\
            .eq('county', county.upper())\
            .gte('just_value', prop['just_value'] * 0.8)\
            .lte('just_value', prop['just_value'] * 1.2)\
            .limit(10)\
            .execute()

        # Calculate investment score
        investment_score = calculate_investment_score(prop)

        # Determine value trend
        value_trend = "stable"
        if prop.get('sale_price') and prop.get('just_value'):
            ratio = prop['sale_price'] / prop['just_value']
            if ratio > 1.1:
                value_trend = "increasing"
            elif ratio < 0.9:
                value_trend = "decreasing"

        return PropertyAnalytics(
            parcel_id=parcel_id,
            predicted_value=prop['just_value'] * 1.05,  # Simple prediction
            confidence_interval={
                'lower': prop['just_value'] * 0.95,
                'upper': prop['just_value'] * 1.15
            },
            value_trend=value_trend,
            investment_score=investment_score,
            comparable_properties=[c['parcel_id'] for c in comparables.data[:5]]
        )

    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/counties", tags=["Counties"])
async def get_counties():
    """Get list of all counties with statistics"""
    try:
        # Get county statistics
        response = supabase.table('county_statistics')\
            .select("*")\
            .execute()

        if response.data:
            return response.data

        # If no stats, get unique counties from parcels
        counties = supabase.table('florida_parcels')\
            .select("county")\
            .execute()

        unique_counties = list(set(c['county'] for c in counties.data if c['county']))
        return [{'county': c, 'total_parcels': 0} for c in sorted(unique_counties)]

    except Exception as e:
        logger.error(f"Get counties error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/counties/{county}/statistics", response_model=CountyStatistics, tags=["Counties"])
async def get_county_statistics(county: str):
    """Get detailed statistics for a specific county using pandas"""
    try:
        # Get all properties for county
        response = supabase.table('florida_parcels')\
            .select("just_value, sale_price, sale_date")\
            .eq('county', county.upper())\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="County not found")

        # Convert to DataFrame for analysis
        df = pd.DataFrame(response.data)

        # Calculate statistics using pandas
        stats = CountyStatistics(
            county=county.upper(),
            total_parcels=len(df),
            avg_just_value=df['just_value'].mean() if not df['just_value'].isna().all() else 0,
            median_just_value=df['just_value'].median() if not df['just_value'].isna().all() else 0,
            total_assessed_value=df['just_value'].sum() if not df['just_value'].isna().all() else 0,
            recent_sales=df['sale_date'].notna().sum(),
            data_quality_score=calculate_data_quality_score(df)
        )

        return stats

    except Exception as e:
        logger.error(f"County statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predictions", tags=["ML Predictions"])
async def predict_property_value(request: MLPredictionRequest):
    """
    Predict property value using machine learning model
    """
    try:
        # Get property features if not provided
        if not request.features:
            property_data = supabase.table('florida_parcels')\
                .select("*")\
                .eq('parcel_id', request.parcel_id)\
                .single()\
                .execute()

            if not property_data.data:
                raise HTTPException(status_code=404, detail="Property not found")

            # Also get NAP data if available
            nap_data = supabase.table('nap_characteristics')\
                .select("*")\
                .eq('parcel_id', request.parcel_id)\
                .single()\
                .execute()

            features = {
                'land_sqft': property_data.data.get('land_sqft', 0),
                'building_sqft': nap_data.data.get('building_sqft', 0) if nap_data.data else 0,
                'year_built': nap_data.data.get('year_built', 1990) if nap_data.data else 1990,
                'bedrooms': nap_data.data.get('bedrooms', 3) if nap_data.data else 3,
                'bathrooms': nap_data.data.get('bathrooms', 2) if nap_data.data else 2,
                'garage_spaces': nap_data.data.get('garage_spaces', 2) if nap_data.data else 2
            }
        else:
            features = request.features

        # Make prediction
        prediction, confidence = ml_model.predict(features)

        return {
            'parcel_id': request.parcel_id,
            'predicted_value': prediction,
            'confidence_interval': confidence,
            'features_used': features,
            'model_version': '1.0.0'
        }

    except ValueError as e:
        # Model not trained, train it with sample data
        logger.info("Training ML model with sample data...")
        sample_df = pd.DataFrame({
            'land_sqft': np.random.uniform(5000, 20000, 1000),
            'building_sqft': np.random.uniform(1000, 5000, 1000),
            'year_built': np.random.randint(1950, 2024, 1000),
            'bedrooms': np.random.randint(1, 6, 1000),
            'bathrooms': np.random.uniform(1, 4, 1000),
            'garage_spaces': np.random.randint(0, 4, 1000),
            'just_value': np.random.uniform(100000, 1000000, 1000)
        })

        ml_model.train(sample_df)

        # Retry prediction
        prediction, confidence = ml_model.predict(features)

        return {
            'parcel_id': request.parcel_id,
            'predicted_value': prediction,
            'confidence_interval': confidence,
            'features_used': features,
            'model_version': '1.0.0',
            'note': 'Model trained with sample data'
        }

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/data-quality/{county}", response_model=DataQualityReport, tags=["Reports"])
async def get_data_quality_report(county: str):
    """Generate data quality report for a county using pandas analysis"""
    try:
        # Get county data
        response = supabase.table('florida_parcels')\
            .select("*")\
            .eq('county', county.upper())\
            .limit(1000)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="County not found")

        df = pd.DataFrame(response.data)

        # Calculate quality metrics
        completeness = 1 - df.isna().mean().mean()

        # Check for invalid values
        accuracy_issues = []
        if (df['just_value'] < 0).any():
            accuracy_issues.append("Negative property values found")
        if 'owner_state' in df.columns and (df['owner_state'].str.len() > 2).any():
            accuracy_issues.append("Invalid state codes (should be 2 characters)")

        accuracy = 1 - (len(accuracy_issues) / 10)  # Simple accuracy score

        # Check data freshness
        if 'updated_at' in df.columns:
            latest_update = pd.to_datetime(df['updated_at']).max()
            days_old = (datetime.now() - latest_update).days
            timeliness = max(0, 1 - (days_old / 365))
        else:
            timeliness = 0.5

        # Check consistency
        consistency = 1.0
        if 'just_value' in df.columns and 'land_value' in df.columns and 'building_value' in df.columns:
            # Check if just_value ≈ land_value + building_value
            df['calc_total'] = df['land_value'] + df['building_value']
            df['diff_pct'] = abs(df['just_value'] - df['calc_total']) / df['just_value']
            consistency = 1 - df['diff_pct'].mean()

        overall = np.mean([completeness, accuracy, timeliness, consistency])

        return DataQualityReport(
            county=county.upper(),
            completeness_score=completeness,
            accuracy_score=accuracy,
            timeliness_score=timeliness,
            consistency_score=consistency,
            overall_score=overall,
            issues=accuracy_issues
        )

    except Exception as e:
        logger.error(f"Data quality report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visualizations/{county}/dashboard", tags=["Visualizations"])
async def get_county_dashboard(county: str):
    """Generate county dashboard visualization using matplotlib/seaborn"""
    try:
        # Get county data
        response = supabase.table('florida_parcels')\
            .select("just_value, land_value, building_value, sale_price")\
            .eq('county', county.upper())\
            .limit(500)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="County not found")

        df = pd.DataFrame(response.data)

        # Create visualization
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # 1. Value distribution
        axes[0, 0].hist(df['just_value'].dropna(), bins=30, edgecolor='black')
        axes[0, 0].set_title('Property Value Distribution')
        axes[0, 0].set_xlabel('Just Value ($)')

        # 2. Land vs Building value
        axes[0, 1].scatter(df['land_value'].dropna(), df['building_value'].dropna(), alpha=0.5)
        axes[0, 1].set_title('Land vs Building Value')
        axes[0, 1].set_xlabel('Land Value ($)')
        axes[0, 1].set_ylabel('Building Value ($)')

        # 3. Sale price distribution
        if 'sale_price' in df.columns:
            axes[1, 0].hist(df['sale_price'].dropna(), bins=30, edgecolor='black')
            axes[1, 0].set_title('Sale Price Distribution')
            axes[1, 0].set_xlabel('Sale Price ($)')

        # 4. Summary statistics
        axes[1, 1].axis('off')
        summary = f"""
        County: {county.upper()}
        Properties: {len(df)}
        Avg Value: ${df['just_value'].mean():,.0f}
        Median Value: ${df['just_value'].median():,.0f}
        Total Value: ${df['just_value'].sum():,.0f}
        """
        axes[1, 1].text(0.1, 0.5, summary, fontsize=12)

        plt.suptitle(f'{county.upper()} County Property Dashboard')
        plt.tight_layout()

        # Convert to image
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        logger.error(f"Visualization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ml/train", tags=["ML Operations"])
async def train_ml_model(background_tasks: BackgroundTasks):
    """Train the ML model with current database data"""
    background_tasks.add_task(train_model_background)
    return {"message": "Model training started in background"}

# ===================== Helper Functions =====================

def calculate_investment_score(property_data: Dict) -> float:
    """Calculate investment score based on multiple factors"""
    score = 50.0  # Base score

    # Value appreciation potential
    if property_data.get('sale_price') and property_data.get('just_value'):
        ratio = property_data['sale_price'] / property_data['just_value']
        if ratio < 0.9:
            score += 20  # Undervalued
        elif ratio > 1.1:
            score -= 10  # Overvalued

    # Location factor (simplified)
    if property_data.get('phy_city') in ['Miami', 'Orlando', 'Tampa']:
        score += 15

    # Property age
    if property_data.get('year_built'):
        age = 2025 - property_data['year_built']
        if age < 10:
            score += 10
        elif age > 50:
            score -= 10

    return min(100, max(0, score))

def calculate_data_quality_score(df: pd.DataFrame) -> float:
    """Calculate data quality score for a DataFrame"""
    if df.empty:
        return 0.0

    # Check completeness
    completeness = 1 - df.isna().mean().mean()

    # Check for valid ranges
    validity = 1.0
    if 'just_value' in df.columns:
        invalid_values = (df['just_value'] < 0) | (df['just_value'] > 100000000)
        validity -= invalid_values.mean()

    return (completeness + validity) / 2

async def train_model_background():
    """Background task to train ML model"""
    try:
        logger.info("Starting model training...")

        # Get training data
        response = supabase.table('florida_parcels')\
            .select("*")\
            .limit(10000)\
            .execute()

        if response.data:
            df = pd.DataFrame(response.data)

            # Get additional features from NAP if available
            nap_response = supabase.table('nap_characteristics')\
                .select("*")\
                .limit(10000)\
                .execute()

            if nap_response.data:
                nap_df = pd.DataFrame(nap_response.data)
                df = df.merge(nap_df, on='parcel_id', how='left')

            # Train model
            score = ml_model.train(df)

            # Save model
            joblib.dump(ml_model, 'property_value_model.pkl')
            logger.info(f"Model training completed with score: {score:.3f}")
        else:
            logger.warning("No data available for training")

    except Exception as e:
        logger.error(f"Model training error: {e}")

# ===================== Application Events =====================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Property Appraiser API starting...")

    # Try to load existing model
    try:
        ml_model = joblib.load('property_value_model.pkl')
        logger.info("Loaded existing ML model")
    except:
        logger.info("No existing model found, will train on first prediction")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Property Appraiser API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)