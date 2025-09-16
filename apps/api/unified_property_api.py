"""
Unified Property Data API
Combines all data sources into comprehensive property investment analysis
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio
import json

# Load environment variables
load_dotenv()

app = FastAPI(title="ConcordBroker Unified Property API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host='aws-1-us-east-1.pooler.supabase.com',
        database='postgres',
        user='postgres.pmispwtdngkcmsrsjwbp',
        password='West@Boca613!',
        port=6543,
        cursor_factory=RealDictCursor
    )

class InvestmentScorer:
    """Calculate investment score for properties"""
    
    @staticmethod
    def calculate_score(property_data: dict, tax_certificates: list = None, 
                       sales_history: list = None) -> dict:
        """
        Calculate comprehensive investment score based on multiple factors
        Returns score (0-100) and detailed breakdown
        """
        score = 50  # Base score
        breakdown = {}
        
        # 1. Value Analysis (max 25 points)
        value_score = 0
        if property_data.get('market_value') and property_data.get('assessed_value'):
            market_value = float(property_data['market_value'])
            assessed_value = float(property_data['assessed_value'])
            
            if market_value > 0 and assessed_value > 0:
                value_ratio = market_value / assessed_value
                if value_ratio < 0.9:  # Potentially undervalued
                    value_score += 15
                    breakdown['undervalued'] = True
                elif value_ratio < 1.1:  # Fair value
                    value_score += 10
                else:
                    value_score += 5
                    
                # Check for recent assessment changes
                if property_data.get('last_assessment_change'):
                    if property_data['last_assessment_change'] < -0.1:  # Assessment dropped
                        value_score += 10
                        breakdown['assessment_dropped'] = True
        
        score += min(25, value_score)
        breakdown['value_score'] = value_score
        
        # 2. Distress Indicators (max 25 points)
        distress_score = 0
        distress_indicators = []
        
        # Tax certificates
        if tax_certificates:
            active_certs = [c for c in tax_certificates if c.get('status') == 'active']
            if active_certs:
                distress_score += min(15, len(active_certs) * 5)
                distress_indicators.append(f"{len(active_certs)} tax certificates")
                
                # Calculate total lien amount
                total_liens = sum(float(c.get('redemption_amount', 0)) for c in active_certs)
                if market_value > 0:
                    lien_ratio = total_liens / market_value
                    if lien_ratio > 0.1:  # Significant liens
                        distress_score += 10
                        distress_indicators.append(f"High lien ratio: {lien_ratio:.2%}")
        
        # Code violations (if available)
        if property_data.get('code_violations'):
            violations = property_data['code_violations']
            if violations > 0:
                distress_score += min(5, violations * 2)
                distress_indicators.append(f"{violations} code violations")
        
        # Vacancy indicator
        if property_data.get('occupancy_status') == 'VACANT':
            distress_score += 5
            distress_indicators.append("Vacant property")
            
        score += min(25, distress_score)
        breakdown['distress_score'] = distress_score
        breakdown['distress_indicators'] = distress_indicators
        
        # 3. Ownership Duration (max 15 points)
        ownership_score = 0
        if sales_history and len(sales_history) > 0:
            last_sale = sales_history[0]  # Assuming sorted by date desc
            if last_sale.get('sale_date'):
                sale_date = datetime.fromisoformat(str(last_sale['sale_date']))
                years_owned = (datetime.now() - sale_date).days / 365
                
                if years_owned > 20:  # Very long-term owner
                    ownership_score = 15
                    breakdown['long_term_owner'] = True
                elif years_owned > 10:
                    ownership_score = 10
                elif years_owned > 5:
                    ownership_score = 5
                    
                breakdown['years_owned'] = round(years_owned, 1)
        
        score += ownership_score
        breakdown['ownership_score'] = ownership_score
        
        # 4. Property Characteristics (max 20 points)
        property_score = 0
        
        # Building age and condition
        if property_data.get('year_built'):
            age = datetime.now().year - int(property_data['year_built'])
            if age < 10:
                property_score += 5
            elif age < 30:
                property_score += 3
            elif age > 50:
                property_score -= 2
            breakdown['property_age'] = age
        
        # Size and lot
        if property_data.get('building_sqft'):
            sqft = float(property_data['building_sqft'])
            if sqft > 2000:
                property_score += 5
            elif sqft > 1500:
                property_score += 3
        
        if property_data.get('lot_sqft'):
            lot_sqft = float(property_data['lot_sqft'])
            if lot_sqft > 10000:  # Large lot
                property_score += 5
                breakdown['large_lot'] = True
        
        # Pool or extra features
        if property_data.get('pool') == 'Y':
            property_score += 3
            breakdown['has_pool'] = True
            
        score += max(0, min(20, property_score))
        breakdown['property_score'] = property_score
        
        # 5. Location and Market Factors (max 15 points)
        location_score = 0
        
        # School ratings (if available)
        if property_data.get('school_rating'):
            if property_data['school_rating'] >= 8:
                location_score += 5
            elif property_data['school_rating'] >= 6:
                location_score += 3
        
        # Crime rate (if available)
        if property_data.get('crime_index'):
            if property_data['crime_index'] < 100:  # Below national average
                location_score += 5
        
        # Flood zone
        if property_data.get('flood_zone'):
            if property_data['flood_zone'] in ['X', 'B', 'C']:  # Minimal flood risk
                location_score += 5
            else:
                location_score -= 3
                breakdown['flood_risk'] = property_data['flood_zone']
        
        score += max(0, min(15, location_score))
        breakdown['location_score'] = location_score
        
        # Final score adjustment
        final_score = max(0, min(100, score))
        
        # Categorize investment opportunity
        if final_score >= 85:
            category = "🔥 Hot Deal"
            recommendation = "Immediate action recommended"
        elif final_score >= 70:
            category = "💎 Hidden Gem"
            recommendation = "Strong investment potential"
        elif final_score >= 55:
            category = "🏗️ Fixer-Upper"
            recommendation = "Good for renovation/flip"
        elif final_score >= 40:
            category = "📊 Cash Flow"
            recommendation = "Potential rental income"
        else:
            category = "⚠️ High Risk"
            recommendation = "Proceed with caution"
        
        return {
            'score': final_score,
            'category': category,
            'recommendation': recommendation,
            'breakdown': breakdown,
            'distress_indicators': distress_indicators,
            'calculated_at': datetime.now().isoformat()
        }

@app.get("/api/properties/{parcel_id}/complete")
async def get_complete_property_data(parcel_id: str):
    """Get all available data for a property including investment analysis"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Get basic property data
        cur.execute("""
            SELECT * FROM florida_parcels 
            WHERE parcel_id = %s
            LIMIT 1
        """, (parcel_id,))
        property_data = cur.fetchone()
        
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # 2. Get tax certificates
        cur.execute("""
            SELECT * FROM tax_certificates 
            WHERE parcel_id = %s OR real_estate_account = %s
            ORDER BY tax_year DESC
        """, (parcel_id, parcel_id))
        tax_certificates = cur.fetchall()
        
        # 3. Get sales history (if table exists)
        sales_history = []
        try:
            cur.execute("""
                SELECT * FROM property_sales_history 
                WHERE parcel_id = %s
                ORDER BY sale_date DESC
                LIMIT 10
            """, (parcel_id,))
            sales_history = cur.fetchall()
        except:
            pass
        
        # 4. Get NAV assessments (if table exists)
        nav_assessments = []
        try:
            cur.execute("""
                SELECT * FROM nav_assessments 
                WHERE parcel_id = %s
            """, (parcel_id,))
            nav_assessments = cur.fetchall()
        except:
            pass
        
        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, Decimal):
                        obj[key] = float(value)
                    elif isinstance(value, datetime):
                        obj[key] = value.isoformat()
            return obj
        
        property_data = convert_decimals(property_data)
        tax_certificates = [convert_decimals(cert) for cert in tax_certificates]
        sales_history = [convert_decimals(sale) for sale in sales_history]
        nav_assessments = [convert_decimals(nav) for nav in nav_assessments]
        
        # 5. Calculate investment score
        scorer = InvestmentScorer()
        investment_analysis = scorer.calculate_score(
            property_data, 
            tax_certificates, 
            sales_history
        )
        
        # 6. Calculate financial metrics
        financial_metrics = calculate_financial_metrics(property_data, tax_certificates)
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "parcel_id": parcel_id,
            "property": property_data,
            "tax_certificates": {
                "count": len(tax_certificates),
                "total_amount": sum(float(c.get('redemption_amount', 0)) for c in tax_certificates if c.get('status') == 'active'),
                "certificates": tax_certificates
            },
            "sales_history": {
                "count": len(sales_history),
                "transactions": sales_history
            },
            "nav_assessments": nav_assessments,
            "investment_analysis": investment_analysis,
            "financial_metrics": financial_metrics,
            "data_completeness": {
                "has_basic_info": True,
                "has_tax_certificates": len(tax_certificates) > 0,
                "has_sales_history": len(sales_history) > 0,
                "has_nav_assessments": len(nav_assessments) > 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_financial_metrics(property_data: dict, tax_certificates: list) -> dict:
    """Calculate key financial metrics for investment analysis"""
    metrics = {}
    
    # Get key values
    market_value = float(property_data.get('market_value', 0))
    assessed_value = float(property_data.get('assessed_value', 0))
    taxable_value = float(property_data.get('taxable_value', 0))
    
    # Calculate tax burden
    annual_tax = taxable_value * 0.02  # Approximate 2% tax rate
    metrics['annual_tax'] = round(annual_tax, 2)
    metrics['monthly_tax'] = round(annual_tax / 12, 2)
    
    # Calculate lien amounts
    active_liens = [c for c in tax_certificates if c.get('status') == 'active']
    total_liens = sum(float(c.get('redemption_amount', 0)) for c in active_liens)
    metrics['total_liens'] = round(total_liens, 2)
    metrics['lien_count'] = len(active_liens)
    
    # Estimate rental income (rough calculation - 0.8-1% of market value per month)
    if market_value > 0:
        estimated_rent_low = market_value * 0.008
        estimated_rent_high = market_value * 0.01
        metrics['estimated_rent_range'] = {
            'low': round(estimated_rent_low, 2),
            'high': round(estimated_rent_high, 2),
            'average': round((estimated_rent_low + estimated_rent_high) / 2, 2)
        }
        
        # Calculate cap rate (using average rent estimate)
        avg_rent = (estimated_rent_low + estimated_rent_high) / 2
        annual_income = avg_rent * 12
        annual_expenses = annual_tax + (market_value * 0.01)  # Tax + 1% maintenance
        net_income = annual_income - annual_expenses
        
        metrics['cap_rate'] = round((net_income / market_value) * 100, 2) if market_value > 0 else 0
        metrics['monthly_cash_flow'] = round(net_income / 12, 2)
        metrics['annual_roi'] = round((net_income / (market_value * 0.25)) * 100, 2)  # Assuming 25% down
    
    # Price per square foot
    if property_data.get('building_sqft'):
        sqft = float(property_data['building_sqft'])
        if sqft > 0:
            metrics['price_per_sqft'] = round(market_value / sqft, 2)
    
    # Value ratios
    if assessed_value > 0:
        metrics['market_to_assessed_ratio'] = round(market_value / assessed_value, 3)
    
    return metrics

@app.post("/api/properties/search/investment")
async def search_investment_properties(
    min_score: int = Query(50, description="Minimum investment score"),
    max_price: float = Query(None, description="Maximum property price"),
    min_cap_rate: float = Query(None, description="Minimum cap rate"),
    has_liens: bool = Query(None, description="Has tax liens"),
    city: str = Query(None, description="City filter"),
    limit: int = Query(100, description="Maximum results")
):
    """Search for properties with investment scoring"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build query
        query = """
            SELECT 
                p.*,
                COUNT(DISTINCT tc.id) as lien_count,
                SUM(CASE WHEN tc.status = 'active' THEN tc.redemption_amount ELSE 0 END) as total_liens
            FROM florida_parcels p
            LEFT JOIN tax_certificates tc ON p.parcel_id = tc.parcel_id
            WHERE 1=1
        """
        params = []
        
        if max_price:
            query += " AND p.market_value <= %s"
            params.append(max_price)
        
        if city:
            query += " AND p.city ILIKE %s"
            params.append(f"%{city}%")
        
        if has_liens is not None:
            if has_liens:
                query += " AND EXISTS (SELECT 1 FROM tax_certificates WHERE parcel_id = p.parcel_id AND status = 'active')"
            else:
                query += " AND NOT EXISTS (SELECT 1 FROM tax_certificates WHERE parcel_id = p.parcel_id AND status = 'active')"
        
        query += """
            GROUP BY p.parcel_id
            ORDER BY total_liens DESC NULLS LAST
            LIMIT %s
        """
        params.append(limit)
        
        cur.execute(query, params)
        properties = cur.fetchall()
        
        # Calculate scores for each property
        scorer = InvestmentScorer()
        scored_properties = []
        
        for prop in properties:
            # Get additional data for scoring
            cur.execute("""
                SELECT * FROM tax_certificates 
                WHERE parcel_id = %s AND status = 'active'
            """, (prop['parcel_id'],))
            tax_certs = cur.fetchall()
            
            # Convert decimals
            for key, value in prop.items():
                if isinstance(value, Decimal):
                    prop[key] = float(value)
            
            # Calculate score
            investment_score = scorer.calculate_score(prop, tax_certs)
            
            if investment_score['score'] >= min_score:
                # Calculate financial metrics
                financial_metrics = calculate_financial_metrics(prop, tax_certs)
                
                # Apply cap rate filter if specified
                if min_cap_rate and financial_metrics.get('cap_rate', 0) < min_cap_rate:
                    continue
                
                scored_properties.append({
                    'property': prop,
                    'investment_score': investment_score,
                    'financial_metrics': financial_metrics
                })
        
        # Sort by investment score
        scored_properties.sort(key=lambda x: x['investment_score']['score'], reverse=True)
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "count": len(scored_properties),
            "properties": scored_properties[:limit],
            "filters_applied": {
                "min_score": min_score,
                "max_price": max_price,
                "min_cap_rate": min_cap_rate,
                "has_liens": has_liens,
                "city": city
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/properties/opportunities/distressed")
async def find_distressed_properties(limit: int = 50):
    """Find properties with strong distress indicators"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Find properties with multiple distress indicators
        cur.execute("""
            WITH distressed AS (
                SELECT 
                    p.*,
                    COUNT(DISTINCT tc.id) as lien_count,
                    SUM(tc.redemption_amount) as total_liens,
                    MAX(tc.tax_year) as latest_lien_year
                FROM florida_parcels p
                INNER JOIN tax_certificates tc ON p.parcel_id = tc.parcel_id
                WHERE tc.status = 'active'
                GROUP BY p.parcel_id
                HAVING COUNT(DISTINCT tc.id) > 0
            )
            SELECT * FROM distressed
            ORDER BY total_liens DESC
            LIMIT %s
        """, (limit,))
        
        properties = cur.fetchall()
        
        # Convert and enhance data
        distressed_properties = []
        for prop in properties:
            # Convert decimals
            for key, value in prop.items():
                if isinstance(value, Decimal):
                    prop[key] = float(value)
            
            # Add distress analysis
            market_value = prop.get('market_value', 0)
            total_liens = prop.get('total_liens', 0)
            
            distress_analysis = {
                'lien_to_value_ratio': round(total_liens / market_value * 100, 2) if market_value > 0 else 0,
                'years_delinquent': datetime.now().year - prop.get('latest_lien_year', datetime.now().year),
                'opportunity_type': 'Tax Deed Candidate' if prop.get('lien_count', 0) > 2 else 'Negotiation Opportunity'
            }
            
            distressed_properties.append({
                'property': prop,
                'distress_analysis': distress_analysis
            })
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "count": len(distressed_properties),
            "opportunities": distressed_properties
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/market-summary")
async def get_market_summary(city: str = None):
    """Get market analytics summary"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build query
        base_query = "FROM florida_parcels p"
        where_clause = ""
        params = []
        
        if city:
            where_clause = " WHERE p.city ILIKE %s"
            params.append(f"%{city}%")
        
        # Get summary statistics
        cur.execute(f"""
            SELECT 
                COUNT(*) as total_properties,
                AVG(market_value) as avg_market_value,
                MEDIAN(market_value) as median_market_value,
                AVG(building_sqft) as avg_sqft,
                AVG(EXTRACT(YEAR FROM CURRENT_DATE) - year_built) as avg_age
            {base_query}
            {where_clause}
        """, params)
        
        summary = cur.fetchone()
        
        # Get properties with liens
        cur.execute(f"""
            SELECT COUNT(DISTINCT p.parcel_id) as properties_with_liens
            {base_query}
            INNER JOIN tax_certificates tc ON p.parcel_id = tc.parcel_id
            {where_clause.replace('WHERE', 'WHERE tc.status = \'active\' AND' if where_clause else 'WHERE tc.status = \'active\'')}
        """, params)
        
        lien_count = cur.fetchone()
        
        # Convert decimals
        for key, value in summary.items():
            if isinstance(value, Decimal):
                summary[key] = float(value)
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "market": city or "All Florida",
            "statistics": summary,
            "distress_indicators": {
                "properties_with_liens": lien_count['properties_with_liens'] if lien_count else 0,
                "lien_percentage": round((lien_count['properties_with_liens'] / summary['total_properties'] * 100), 2) if summary['total_properties'] > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting Unified Property API Server...")
    print("=" * 50)
    print("Endpoints available:")
    print("  - GET  /api/properties/{parcel_id}/complete")
    print("  - POST /api/properties/search/investment")
    print("  - GET  /api/properties/opportunities/distressed")
    print("  - GET  /api/analytics/market-summary")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8002)